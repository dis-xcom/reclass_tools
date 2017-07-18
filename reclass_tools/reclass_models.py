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

import reclass
# from reclass.adapters import salt as reclass_salt
from reclass import config as reclass_config
from reclass import core as reclass_core

from reclass_tools import helpers
# import salt.cli.call
# import salt.cli.caller


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


# def get_minion_domain():
#     """Try to get domain from the local salt minion"""
#     client = salt.cli.call.SaltCall()
#     client.parse_args(args=['pillar.items'])
#     caller = salt.cli.caller.Caller.factory(client.config)
#     result = caller.call()
#     # Warning! There is a model-related parameter
#     # TODO(ddmitriev): move the path to the parameter to a settings/defaults
#     domain = result['return']['_param']['cluster_domain']
#     return domain


def inventory_list(domain=None):
    core = get_core()
    inventory = core.inventory()['nodes']
    if domain is not None:
        inventory = {key: val for (key, val) in inventory.items()
                     if key.endswith(domain)}
    return inventory


def get_nodeinfo(minion_id):
    core = get_core()
    return core.nodeinfo(minion_id)


def vcp_list(domain=None, inventory=None):
    """List VCP node names

    Scan all nodes for the object salt.control.cluster.internal.node.XXX.name
    Return set of tuples ((nodename1, domain), (nodename2, domain), ...)
    """

    inventory = inventory or inventory_list(domain=domain)
    vcp_path = 'parameters.salt.control.cluster.internal.node'.split('.')
    domain_path = 'parameters._param.cluster_domain'.split('.')

    vcp_node_names = set()

    for node_name, node in inventory.items():
        vcp_nodes = helpers.get_nested_key(node, path=vcp_path)
        if vcp_nodes is not None:
            for vcp_node_name, vcp_node in vcp_nodes.items():
                vcp_node_names.add((
                    vcp_node['name'],
                    helpers.get_nested_key(node, path=domain_path)))
    return vcp_node_names


def reclass_storage(domain=None, inventory=None):
    """List VCP node names

    Scan all nodes for the object salt.control.cluster.internal.node.XXX.name
    """

    inventory = inventory or inventory_list(domain=domain)
    storage_path = 'parameters.reclass.storage.node'.split('.')

    res = dict()
    for node_name, node in inventory.items():
        storage_nodes = helpers.get_nested_key(node, path=storage_path)
        if storage_nodes is not None:
            for storage_node_name, storage_node in storage_nodes.items():
                if storage_node['domain'] not in res:
                    res[storage_node['domain']] = dict()
                res[storage_node['domain']][storage_node_name] = storage_node
    return res
