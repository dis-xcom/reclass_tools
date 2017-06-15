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
        identity_files=params.identity_files,
        verbose=params.verbose)

    print(yaml.dump(results))


def dump_params(args=None):
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description="")
    parser.add_argument('-i', dest='identity_files',
                        help=('For SSH connections, selects a file from which \n'
                              'the identity (private key) for public key \n'
                              'authentication is read. It is possible to have \n'
                              'multiple -i options.'),
                        action='append')
    parser.add_argument('--verbose', dest='verbose', action='store_const', const=True,
                        help='Show verbosed output.', default=False)
    parser.add_argument('paths', help='Paths to search for *.yml files.', nargs='+')

    if len(args) == 0:
        args = ['-h']

    params = parser.parse_args(args)
    execute(params)
