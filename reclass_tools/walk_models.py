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

# import copy
import os
import sys

import yaml

from reclass_tools import helpers


def walkfiles(topdir, verbose=False):
    walker = os.walk(topdir)
    opener = open
    prefix = ''
    isdir = os.path.isdir(topdir)

    if isdir:
        for dirName, subdirList, fileList in walker:
            for filename in fileList:
                filepath = os.path.join(dirName, filename)
                if verbose:
                    print (prefix + filepath)
                with OpenFile(filepath, opener) as log:
                    yield (log)
    else:
        if verbose:
            print (topdir)
        with OpenFile(topdir, opener) as log:
            yield (log)


# def yaml_read(yaml_file):
#     if os.path.isfile(yaml_file):
#         with open(yaml_file, 'r') as f:
#             return yaml.load(f)
#     else:
#         print("\'{}\' is not a file!".format(yaml_file))


class OpenFile(object):

    fname = None
    opener = None
    readlines = None
    fobj = None

    def __init__(self, fname, opener):
        self.fname = fname
        self.opener = opener

    def get_parser(self):
        parsers = {'/lastlog': self.fake_parser,
                   '/wtmp': self.fake_parser,
                   '/btmp': self.fake_parser,
                   '/atop.log': self.fake_parser,
                   '/atop_': self.fake_parser,
                   '/atop_current': self.fake_parser,
                   '/supervisord.log': self.docker_parser,
                   '.gz': self.gz_parser,
                   '.bz2': self.gz_parser,
                   }
        for w in parsers.keys():
            if w in self.fname:
                self.readlines = parsers[w]
                return
        try:
            self.fobj = self.opener(self.fname, 'r')
            self.readlines = self.plaintext_parser
        except IOError as e:
            print("Error opening file {0}: {1}".format(self.fname, e))
            if self.fobj:
                self.fobj.close()
            self.fobj = None
            self.readlines = self.fake_parser

    def plaintext_parser(self):
        try:
            for s in self.fobj.readlines():
                yield s
        except IOError as e:
            print("Error reading file {0}: {1}".format(self.fname, e))

    def fake_parser(self):
        yield ''

    def docker_parser(self):
        yield ''

    def gz_parser(self):
        yield ''

    def bz2_parser(self):
        yield ''

    def __enter__(self):
        self.get_parser()
        return self

    def __exit__(self, x, y, z):
        if self.fobj:
            self.fobj.close()


def get_all_reclass_params(paths, verbose=False):
    """Return dict with all used values for each param"""
    _params = dict()
    for path in paths:
        for log in walkfiles(path, verbose):
            if log.fname.endswith('.yml'):
                model = helpers.yaml_read(log.fname)
                if model is not None:
                    # Collect all params from the models
                    _param = helpers.get_nested_key(
                        model,
                        ['parameters', '_param'])
                    if _param:
                        for key, val in _param.items():
                            if key in _params:
                                # Keep list values sorted
                                _params[key].append(val)
                                _params[key] = sorted(_params[key])
                            else:
                                _params[key] = [val]
    return _params


def add_reclass_parameter(paths, key, value, verbose=False, merge=False):
    """Add a value to the specified key to all the files in the paths

    if merge=False (default):
      - new value replaces previous key content completely.

    if merge=True:
      - if the specified key type is list, then value will be appended
        to the list. Value examples:
          '1000'
          'new_lab_name'
          'cluster.virtual_cluster_name.infra'
          'http://archive.ubuntu.com'
          '[a, b, c]'   # a list in the list
          '{a:1, b:2, c:3}' # a dict in the list
      - if the specified key type is an existing dict, then the dict
        will be extended with the dict in the value. Value example:
          '{address: 192.168.1.1, netmask: 255.255.255.0}'

    - If the specified key type is string/int/bool - it will replace previous
      value
    """
    add_key = key.split('.')

    for path in paths:
        for fyml in walkfiles(path, verbose=verbose):
            if fyml.fname.endswith('.yml'):
                model = helpers.yaml_read(fyml.fname)
                if model is not None:

                    nested_key = helpers.get_nested_key(model, add_key)

                    if nested_key is not None:
                        if merge is False:
                            nested_key = value
                        else:
                            if type(nested_key) is list:
                                nested_key.append(value)
                            elif type(nested_key) is dict:
                                nested_key.update(value)
                            else:
                                nested_key = value
                    else:
                        nested_key = value

                    helpers.create_nested_key(model, path=add_key,
                                              value=nested_key)

                    with open(fyml.fname, 'w') as f:
                        f.write(
                            yaml.dump(
                                model, default_flow_style=False
                            )
                        )


def remove_reclass_parameter(paths, key,
                             verbose=False,
                             pretend=False):
    """Removes specified key from parameters from all reclass models

    :param key: string with point-separated nested objects, for
                example: parameters.linux.network.interface
    :rtype dict: { 'file path': {nested_key}, ...}
    """
    remove_key = key.split('.')
    # found_keys = {}

    for path in paths:
        for fyml in walkfiles(path, verbose=verbose):
            if fyml.fname.endswith('.yml'):

                try:
                    model = helpers.yaml_read(fyml.fname)
                except yaml.scanner.ScannerError as e:
                    print(e, file=sys.stderr)
                    continue

                if model is not None:
                    # Clear linux.network.interfaces
                    nested_key = helpers.get_nested_key(model, remove_key)
                    if nested_key is not None:
                        # found_keys[fyml.fname] = copy.deepcopy(nested_key)
                        if pretend:
                            print("\n---\n# Found {0} in {1}"
                                  .format('.'.join(remove_key), fyml.fname))
                            print(yaml.dump(nested_key,
                                            default_flow_style=False))
                        else:
                            print("\n---\n# Removing {0} from {1}"
                                  .format('.'.join(remove_key), fyml.fname))
                            print(yaml.dump(nested_key,
                                            default_flow_style=False))

                            helpers.remove_nested_key(model, remove_key)

                            with open(fyml.fname, 'w') as f:
                                f.write(
                                    yaml.dump(
                                        model, default_flow_style=False
                                    )
                                )
    # return found_keys
