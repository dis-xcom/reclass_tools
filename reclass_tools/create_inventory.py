import yaml
import json

from cookiecutter import __version__
#from cookiecutter.log import configure_logger
#from cookiecutter.main import cookiecutter

from cookiecutter import generate
from cookiecutter.exceptions import UndefinedVariableInTemplate

from reclass_tools import helpers
from reclass_tools import reclass_models
from reclass_tools import walk_models


def create_inventory_context(domain=None, keys=None):
    """Dumps the current inventory per domain

    Example of context:

    <global_settings>: # only if required
      ...
    current_clusters:
      <cluster_names>:
        # here are cluster settings if required
        nodes:
          <node_names>:
            name: ctl01
            reclass_storage_name: openstack_control_node01
            roles:
            - vcp        # 'vcp' or None
            parameters:  # specified keys to dump, for example
                         # parameters.linux.network.interface below:
              linux:
                network:
                  interfaces:
                    ..
    """
    inventory = reclass_models.inventory_list(domain=domain)
    vcp_list = reclass_models.vcp_list(domain=domain, inventory=inventory)
    reclass_storage = reclass_models.reclass_storage(domain=domain, inventory=inventory)

    current_underlay_context = {
        'current_clusters': {
        }
    }

    for domain, storage_nodes in reclass_storage.items():

        current_cluster_nodes = {}
        for storage_node_name, storage_node in storage_nodes.items():
            inventory_node_name = "{0}.{1}".format(storage_node['name'], storage_node['domain'])
            current_cluster_nodes[inventory_node_name] = {
                'name': storage_node['name'],
                'reclass_storage_name': storage_node_name,
                'roles': list(),
                'parameters': dict(),
            }

            if (storage_node['name'], storage_node['domain']) in vcp_list:
                # Add role 'vcp' to mark the VM nodes.
                current_cluster_nodes[inventory_node_name]['roles'].append('vcp')

            if keys:
                # Dump specified parameters for the node
                # Will fail with KeyError if 'inventory_node_name' doesn't
                # exists in reclass inventory
                # (wasn't generated with reclass.storage yet, for example)
                node = inventory[inventory_node_name]
                for key in keys:
                    key_path = key.split('.')
                    reclass_key = helpers.get_nested_key(node, path=key_path)
                    if reclass_key:
                        helpers.create_nested_key(current_cluster_nodes[inventory_node_name], path=key_path, value=reclass_key)

        current_underlay_context['current_clusters'][domain] = {
            'nodes': current_cluster_nodes
        }

    return current_underlay_context


    #1. Generate jinga interfaces / hw details based on node information provided to jinja

    #2. Generate appropriate includes to reclass.storate model in config node
    #configure_logger(
    #    stream_level='DEBUG' if verbose else 'INFO',
    #    debug_file=debug_file,
    #)

#current_clusters:
#  <cluster_names>:
#    nodes:
#      <node_names>:
#        name: ctl01
#        reclass_storage_name: openstack_control_node01
#        # if classes - then classes
#        roles:
#        - vcp  # to select wich interface type to use
#        #- openstack_controller  # Don't forget to map the roles to corresponded classes if needed
#        parameters: # there is just a DUMP of the existing model,
#                    # which could be re-used complete or particulary for rendering new model
#          linux:
#            network:
#              interfaces:
#                ..


def render_environment_class():
    """Coockiecutter echancement to use several source JSON files

    :param template_dir: directory with templates to render
    :param output_dir: directory that should be created from templates
    :param context_files: list of strings, paths to YAML or JSON files
                          that provide the context variables for rendering.
                          Merge of the files usind update() into a single
                          dict is in the same order as files in the list.
    """

#ipdb> repo_dir
#u'/root/cookiecutter-templates/cluster_product/openstack'
#ipdb> context
#{u'cookiecutter': {u'openstack_telemetry_node02_hostname': u'mdb02', ... }}
#ipdb> overwrite_if_exists
#False
#ipdb> output_dir
#'/root/my_new_deployment/'

    repo_dir = '/root/cookiecutter-templates/cluster_product/openstack'
    overwrite_if_exists = True
    output_dir = '/root/my_new_deployment/'
    context = {'cookiecutter': {'openstack_telemetry_node02_hostname': 'mdb02' }}

    try:
        generate.generate_files(
            repo_dir=repo_dir,
            context=context,
            overwrite_if_exists=overwrite_if_exists,
            output_dir=output_dir
        )


    except UndefinedVariableInTemplate as undefined_err:
        print('>>> {}'.format(undefined_err.message))
        print('>>> Error message: {}'.format(undefined_err.error.message))

        context_str = yaml.dump(
            undefined_err.context,
            indent=4,
            default_flow_style=False
        )
        print('='*15 + ' Context: '+ '='*15 + '\n{}'.format(context_str) + '='*40)
        return
