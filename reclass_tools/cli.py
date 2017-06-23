#    Copyright 2013 - 2016 Mirantis, Inc.
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


def execute(params):

    results = walk_models.get_all_reclass_params(
        params.paths,
        verbose=params.verbose)

    print(yaml.dump(results))


def dump_params(args=None):
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description="")
    parser.add_argument('--verbose', dest='verbose', action='store_const', const=True,
                        help='Show verbosed output.', default=False)
    parser.add_argument('paths', help='Paths to search for *.yml files.', nargs='+')

    if len(args) == 0:
        args = ['-h']

    params = parser.parse_args(args)
    results = walk_models.get_all_reclass_params(
        params.paths,
        verbose=params.verbose)

    print(yaml.dump(results))


def show_key(args=None):
    remove_key(args=args, pretend=True)


def remove_key(args=None, pretend=False):
    if args is None:
        args = sys.argv[1:]

    key_parser = argparse.ArgumentParser(add_help=False)
    if pretend:
        key_parser_help = (
            'Key name to find in reclass model files, for example:'
            ' reclass-show-key parameters.linux.network.interface'
            ' /path/to/model/')
    else:
        key_parser_help = (
            'Key name to remove from reclass model files, for example:'
            ' reclass-remove-key parameters.linux.network.interface'
            ' /path/to/model/')
    key_parser.add_argument('key_name', help=key_parser_help)

    parser = argparse.ArgumentParser(parents=[key_parser],
        formatter_class=argparse.RawTextHelpFormatter,
        description="")
    parser.add_argument('--verbose', dest='verbose', action='store_const', const=True,
                        help='Show verbosed output.', default=False)
    parser.add_argument('paths', help='Paths to search for *.yml files.', nargs='+')

    if len(args) == 0:
        args = ['-h']

    params = parser.parse_args(args)
    results = walk_models.remove_reclass_parameter(
        params.paths,
        params.key_name,
        verbose=params.verbose,
        pretend=pretend)

def inventory_list(args=None):
    try:
        from reclass_tools import reclass_models
    except ImportError:
        print("Please run this tool on the salt-master node with installed 'reclass'")
        return

    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                     description="")
    parser.add_argument('--domain', '-d', dest='domain',
                        help=('Show only the nodes which names are ended with the specified domain, for example:'
                              ' reclass-inventory-list -d example.local'))

    params = parser.parse_args(args)

    reclass_models.inventory_list(domain=params.domain)
