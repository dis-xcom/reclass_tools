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

import copy

import reclass
# from reclass.adapters import salt as reclass_salt
from reclass import config as reclass_config
from reclass import core as reclass_core
from reclass import defaults as reclass_defaults
from reclass.datatypes import parameters as reclass_parameters
from reclass.utils.refvalue import RefValue
import yaml
import mock

from reclass_tools import helpers
# import salt.cli.call
# import salt.cli.caller


def refvalue_representer(dumper, data):
    return dumper.represent_str(
        data._assemble(
            lambda s: s.join(reclass_defaults.PARAMETER_INTERPOLATION_SENTINELS)))
yaml.add_representer(RefValue, refvalue_representer)

class ReclassCore(reclass_core.Core):
    """Track the specific key

    :param key: string with dot-separated keys
    """
    track_key_path = None

    def __init__(self, storage, class_mappings, input_data=None,
                 key=None):
        if key:
            if ':' in key:
                # Linux pillar notation:  linux:network:interface
                self.track_key_path = key.split(':')
            else:
                # Python notation: linux.network.interface
                self.track_key_path = key.split('.')

            if self.track_key_path[0] == 'parameters':
                # Remove the first 'parameters' element because the model entities
                # keep parameters in different object format.
                self.track_key_path = self.track_key_path[1:]

        super(ReclassCore, self).__init__(storage, class_mappings, input_data)


    def _recurse_entity(self, entity, merge_base=None, seen=None, nodename=None):

        def _new_merge_dict(self, cur, new, path):
            try:
                return orig_merge_dict(self, cur, new, path)
            except TypeError as e:
                if "Current value:" not in e.message:
                    e.message +="\nValue path: {}\nCurrent value: {}\nNew value: {}\n".format(path, cur, new)
                raise TypeError(e.message)

        if seen is None:
            seen = {}
        if '__visited' not in seen:
            seen['__visited'] = []

        orig_visited = copy.deepcopy(seen['__visited'])
        seen['__visited'].append(entity.name)

        orig_merge_dict = reclass_parameters.Parameters._merge_dict
        with mock.patch.object(reclass_parameters.Parameters, '_merge_dict', new=_new_merge_dict):
            try:
                result =  super(ReclassCore, self)._recurse_entity(entity,
                                                                   merge_base,
                                                                   seen,
                                                                   nodename)
            except Exception:
                print("### Interpolation failed in the class: " + ' < '.join(seen['__visited']))
                raise
        if self.track_key_path:
            key = helpers.get_nested_key(entity.parameters.as_dict(),
                                         path=self.track_key_path)
            if key is not None:
                print("# " + ' < '.join(seen['__visited']))
                out_dict = {}
                helpers.create_nested_key(out_dict, ['parameters'] + self.track_key_path, key)
                print(yaml.dump(out_dict,
                                default_flow_style=False,
                                width=255))

        # Reset the data collected by child entries
        seen['__visited'] = orig_visited

        return result

    def _nodeinfo(self, nodename):
        if self.track_key_path:
            print("\n" + nodename)
            print("-" * len(nodename))

        result =  super(ReclassCore, self)._nodeinfo(nodename)

        if self.track_key_path:
            key = helpers.get_nested_key(result.parameters.as_dict(),
                                         path=self.track_key_path)
            if key is not None:
                print("### Final result after interpolation: ###")
                out_dict = {}
                helpers.create_nested_key(out_dict, ['parameters'] + self.track_key_path, key)
                print(yaml.dump(out_dict,
                                default_flow_style=False,
                                width=255))
        return result


def get_core(key=None):
    """Initializes reclass Core() using /etc/reclass settings"""

    defaults = reclass_config.find_and_read_configfile()
    inventory_base_uri = defaults['inventory_base_uri']
    storage_type = defaults['storage_type']

    nodes_uri, classes_uri = reclass_config.path_mangler(inventory_base_uri,
                                                         None, None)
    storage = reclass.get_storage(storage_type, nodes_uri, classes_uri,
                                  default_environment='base')

    #key = '_param.keepalived_vip_interface'
    return ReclassCore(storage, None, None, key=key)


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


def nodes_list(domain=None):
    core = get_core()
    nodes = core._storage.enumerate_nodes()
    if domain is not None:
        nodes = [node for node in nodes
                 if node.endswith(domain)]
    return nodes


def get_nodeinfo(minion_id):
    core = get_core()
    return core.nodeinfo(minion_id)


def trace_key(key, domain=None, node=None):
    if node:
        nodes = [node]
    else:
        nodes = nodes_list(domain=domain)

    core = get_core(key=key)
    for node in nodes:
        core.nodeinfo(node)


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
