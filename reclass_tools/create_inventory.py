#    Copyright 2013 - 2017 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import sys

from reclass_tools import helpers
from reclass_tools import reclass_models


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
    reclass_storage = reclass_models.reclass_storage(domain=domain,
                                                     inventory=inventory)

    if domain is None:
        sys.exit("Error: please specify a domain name from: \n{}"
                 .format('\n'.join(reclass_storage.keys())))

    for storage_domain, storage_nodes in reclass_storage.items():
        if storage_domain != domain:
            continue

        current_cluster_nodes = {}
        for storage_node_name, storage_node in storage_nodes.items():
            inventory_node_name = "{0}.{1}".format(storage_node['name'],
                                                   storage_node['domain'])
            current_cluster_nodes[inventory_node_name] = {
                'name': storage_node['name'],
                'reclass_storage_name': storage_node_name,
                'roles': list(),
                'parameters': dict(),
            }

            if (storage_node['name'], storage_node['domain']) in vcp_list:
                # Add role 'vcp' to mark the VM nodes.
                current_cluster_nodes[
                    inventory_node_name]['roles'].append('vcp')

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
                        helpers.create_nested_key(
                            current_cluster_nodes[inventory_node_name],
                            path=key_path,
                            value=reclass_key)

        current_underlay_context = {
            'cookiecutter': {
                'cluster_name': storage_domain,
                'nodes': current_cluster_nodes,
            }
        }

    return current_underlay_context
