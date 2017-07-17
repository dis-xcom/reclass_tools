import yaml
import json
import sys

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

    if domain is None:
        sys.exit("Error: please specify a domain name from: \n{}".format('\n'.join(reclass_storage.keys())))

    for storage_domain, storage_nodes in reclass_storage.items():
        if storage_domain != domain:
            continue

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

        current_underlay_context = {
            'cookiecutter': {
                'cluster_name': storage_domain,
                'nodes': current_cluster_nodes,
            }
        }

    return current_underlay_context


def render_dir(template_dir, output_dir, contexts, env_name=None):
    """Coockiecutter echancement to use several source JSON files

    :param template_dir: directory with templates to render
    :param output_dir: directory that should be created from templates
    :param context_files: list of strings, paths to YAML or JSON files
                          that provide the context variables for rendering.
                          Merge of the files usind update() into a single
                          dict is in the same order as files in the list.
    :param env_name: name for new environment that will be created
    """
    def toyaml(value, width=0, indentfirst=False):
        string = yaml.dump(value, default_flow_style=False)
        if string.splitlines():
            return (
                ' ' * width * indentfirst +
                ('\n' + ' ' * width).join(string.splitlines()) + '\n')
        else:
            return ''

    overwrite_if_exists = True

    merged_context = {}

    for fcon in contexts:
        if fcon.endswith('.yaml'):
            context = helpers.yaml_read(fcon)
        elif fcon.endswith('.json'):
            context = helpers.json_read(fcon)
        else:
            sys.exit("Error: Please use YAML or JSON files for contexts")

        merged_context = helpers.merge_nested_objects(merged_context, context)

    merged_context['toyaml'] = toyaml
    if env_name:
        merged_context['cookiecutter']['_environment_name'] = env_name

    try:
        generate.generate_files(
            repo_dir=template_dir,
            context=merged_context,
            overwrite_if_exists=overwrite_if_exists,
            output_dir=output_dir
        )

    except UndefinedVariableInTemplate as undefined_err:
        context_str = yaml.dump(
            undefined_err.context,
            default_flow_style=False
        )
        print('='*15 + ' Context: '+ '='*15 + '\n{}'.format(context_str) + '='*40)
        print('>>> {}'.format(undefined_err.message))
        sys.exit('>>> Error message: {}'.format(undefined_err.error.message))
