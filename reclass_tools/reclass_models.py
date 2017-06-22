import reclass
from reclass.adapters import salt as reclass_salt
from reclass import config as reclass_config
from reclass import core as reclass_core
import salt.cli.call
import salt.cli.caller


def get_core():
    """Initializes reclass Core() using /etc/reclass settings"""

    defaults = reclass_config.find_and_read_configfile()
    inventory_base_uri = defaults['inventory_base_uri']
    storage_type = defaults['storage_type']

    nodes_uri, classes_uri = reclass_config.path_mangler(inventory_base_uri,
                                                         None, None)
    storage = reclass.get_storage(storage_type, nodes_uri, classes_uri,
                                  default_environment='base')

    return reclass_core.Core(storage, None, None)


def get_minion_domain():
    """Try to get domain from the local salt minion"""
    client = salt.cli.call.SaltCall()
    client.parse_args(args=['pillar.items'])
    caller = salt.cli.caller.Caller.factory(client.config)
    result = caller.call()
    # Warning! There is a model-related parameter
    # TODO: move the path to the parameter to a settings/defaults
    domain = result['return']['_param']['cluster_domain']
    return domain


def inventory_list(all_nodes=False):
    core = get_core()
    inventory = core.inventory()
    nodes_list = inventory['nodes'].keys()
    if not all_nodes:
        domain = get_minion_domain()
        nodes_list = [node for node in nodes_list if domain in node]
    print('\n'.join(sorted(nodes_list)))
