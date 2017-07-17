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

from __future__ import print_function

import argparse
import os
import sys
import yaml

from reclass_tools import walk_models


class Shell(object):
    def __init__(self, args):
        self.args = args
        self.params = self.get_params()

    def execute(self):
        command_name = 'do_{}'.format(self.params.command.replace('-', '_'))
        command_method = getattr(self, command_name)
        command_method()

    def do_get_key(self):
        results = walk_models.remove_reclass_parameter(
            self.params.path,
            self.params.key_name,
            verbose=self.params.verbose,
            pretend=True)

    def do_del_key(self):
        results = walk_models.remove_reclass_parameter(
            self.params.path,
            self.params.key_name,
            verbose=self.params.verbose,
            pretend=False)

    def do_list_params(self):
        results = walk_models.get_all_reclass_params(
            self.params.path,
            verbose=self.params.verbose)
        print(yaml.dump(results))

    def do_list_domains(self):
        try:
            from reclass_tools import reclass_models
        except ImportError:
            sys.exit("Please run this tool on the salt-master node "
                     "with installed 'reclass'")
        inventory = reclass_models.inventory_list()
        reclass_storage = reclass_models.reclass_storage(inventory=inventory)
        print('\n'.join(sorted(reclass_storage.keys())))


    def do_list_nodes(self):
        try:
            from reclass_tools import reclass_models
        except ImportError:
            sys.exit("Please run this tool on the salt-master node "
                     "with installed 'reclass'")

        inventory = reclass_models.inventory_list(domain=self.params.domain)
        vcp_nodes = reclass_models.vcp_list(domain=self.params.domain,
                                            inventory=inventory)
        vcp_node_names = ['{0}.{1}'.format(name, domain)
                          for name, domain in vcp_nodes]

        if self.params.vcp_only:
            print('\n'.join(sorted(vcp_node_names)))
        elif self.params.non_vcp_only:
            print('\n'.join(sorted((node_name for node_name in inventory.keys()
                                    if node_name not in vcp_node_names))))
        else:
            print('\n'.join(sorted(inventory.keys())))

    def do_show_context(self):
        try:
            from reclass_tools import create_inventory
        except ImportError:
            sys.exit("Please run this tool on the salt-master node "
                     "with installed 'reclass'")

        current_underlay_context = create_inventory.create_inventory_context(
            domain=self.params.domain, keys=self.params.keys)

        print(yaml.dump(current_underlay_context, default_flow_style=False))

    def do_render(self):
        try:
            from reclass_tools import create_inventory
        except ImportError:
            sys.exit("Please run this tool on the salt-master node "
                     "with installed 'reclass'")

        if not self.params.template_dir or not self.params.output_dir \
                or not self.params.contexts:
            sys.exit("Missing parameters, see: reclass-tools render -h")

        create_inventory.render_dir(template_dir=self.params.template_dir,
                                    output_dir=self.params.output_dir,
                                    contexts=self.params.contexts,
                                    env_name=self.params.env_name)

    def get_params(self):

        verbose_parser = argparse.ArgumentParser(add_help=False)
        verbose_parser.add_argument('--verbose', dest='verbose',
                                    action='store_const', const=True,
                                    help='Show verbosed output', default=False)

        key_parser = argparse.ArgumentParser(add_help=False)
        key_parser_help = (
                'Key name to find in reclass model files, for example:'
                ' parameters.linux.network.interface')
        key_parser.add_argument('key_name', help=key_parser_help, default=None)

        keys_parser = argparse.ArgumentParser(add_help=False)
        keys_parser.add_argument(
            'keys',
            help='Key names to find in reclass model files', nargs='*')

        path_parser = argparse.ArgumentParser(add_help=False)
        path_parser.add_argument(
            'path',
            help='Path to search for *.yml files.', nargs='+')

        domain_parser = argparse.ArgumentParser(add_help=False)
        domain_parser.add_argument(
            '--domain', '-d', dest='domain',
            help=('Show only the nodes which names are ended with the '
                  'specified domain, for example: example.local'))

        env_name_parser = argparse.ArgumentParser(add_help=False)
        env_name_parser.add_argument(
            '--env-name', '-e', dest='env_name',
            help=("Name of the 'environment' to create or use"),
            default=None)

        vcp_only_parser = argparse.ArgumentParser(add_help=False)
        vcp_only_parser.add_argument(
            '--vcp-only', dest='vcp_only',
            action='store_const', const=True,
            help=('Show only VCP nodes (present in '
                  'parameters.salt.control.cluster.internal.node)'),
            default=False)

        non_vcp_only_parser = argparse.ArgumentParser(add_help=False)
        non_vcp_only_parser.add_argument(
            '--non-vcp-only', dest='non_vcp_only',
            action='store_const', const=True,  default=False,
            help=('Show only non-VCP nodes (absent in '
                  'parameters.salt.control.cluster.internal.node)'))

        render_parser = argparse.ArgumentParser(add_help=False)
        render_parser.add_argument(
            '--template-dir', '-t', dest='template_dir',
            help=('Coockiecutter-based template directory'))
        render_parser.add_argument(
            '--output-dir', '-o', dest='output_dir',
            help=('Path to the directory where the rendered '
                  'template will be placed'))
        render_parser.add_argument(
            '--context', '-c', dest='contexts', nargs='+',
            help=('YAML/JSON files with context data to render '
                  'the template'))



        parser = argparse.ArgumentParser(
            description="Manage virtual environments. "
                        "For additional help, use with -h/--help option")
        subparsers = parser.add_subparsers(title="Operation commands",
                                           help='available commands',
                                           dest='command')

        # TODO: add-class NNN [to] MMM.yml # can be used with 'render'
        subparsers.add_parser('get-key',
                              parents=[key_parser, path_parser,
                                       verbose_parser],
                              help="Find a key in YAMLs found in <path>",
                              description=("Get a key collected from "
                                           "different YAMLs"))
        subparsers.add_parser('del-key',
                              parents=[key_parser, path_parser,
                                       verbose_parser],
                              help="Delete a key from YAMLs found in <path>",
                              description="Delete a key from different YAMLs")
        subparsers.add_parser('list-params',
                              parents=[path_parser, verbose_parser],
                              help=("Collect all options for "
                                    "'parameters._params' keys from YAMLs "
                                    "found in <path>"))
        subparsers.add_parser('list-nodes',
                              parents=[domain_parser, vcp_only_parser,
                                       non_vcp_only_parser],
                              help=("List nodes that are available for "
                                    "reclass. Use on salt-master node only!"))
        subparsers.add_parser('list-domains',
                              help=("List domains that are available from "
                                    "reclass models. Use on salt-master "
                                    "node only!"))
        subparsers.add_parser('show-context',
                              parents=[domain_parser, keys_parser],
                              help=("Show domain nodes with rendered content "
                                    "for specified keys. Use on salt-master "
                                    "node for already generated inventory "
                                    "only!"))
        subparsers.add_parser('render',
                              parents=[render_parser, env_name_parser],
                              help=("Render cookiecutter template using "
                                    "multiple metadata sources"))

        if len(self.args) == 0:
            self.args = ['-h']
        return parser.parse_args(self.args)


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    shell = Shell(args)
    shell.execute()
