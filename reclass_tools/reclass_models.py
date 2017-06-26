import reclass
from reclass.adapters import salt as reclass_salt
from reclass import config as reclass_config
from reclass import core as reclass_core

from reclass_tools import helpers
#import salt.cli.call
#import salt.cli.caller


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


#def get_minion_domain():
#    """Try to get domain from the local salt minion"""
#    client = salt.cli.call.SaltCall()
#    client.parse_args(args=['pillar.items'])
#    caller = salt.cli.caller.Caller.factory(client.config)
#    result = caller.call()
#    # Warning! There is a model-related parameter
#    # TODO: move the path to the parameter to a settings/defaults
#    domain = result['return']['_param']['cluster_domain']
#    return domain


def inventory_list(domain=None):
    core = get_core()
    inventory = core.inventory()['nodes']
    if domain is not None:
        inventory = {key:val for (key, val) in inventory.items() if key.endswith(domain)}
    return inventory


def vcp_list(domain=None):
    """List VCP node names

    Scan all nodes for the object salt.control.cluster.internal.node.XXX.name
    """

    inventory = inventory_list(domain=domain)
    vcp_path = 'parameters.salt.control.cluster.internal.node'.split('.')

    vcp_node_names = set()

    for node_name, node in inventory.items():
        vcp_nodes = helpers.get_nested_key(node, path=vcp_path)
        if vcp_nodes is not None:
            for vcp_node_name, vcp_node in vcp_nodes.items():
                vcp_node_names.add(vcp_node['name'])
    return vcp_node_names


