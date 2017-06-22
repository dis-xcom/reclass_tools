
import copy
import hashlib
import os
import re
import tarfile

import urllib2
import yaml


def walkfiles(topdir, verbose=False):
    walker = os.walk(topdir)
    opener = open
    prefix = ''
    isdir = os.path.isdir(topdir)

    if isdir:
        for dirName, subdirList, fileList in walker:
            for filename in fileList:
                filepath = os.path.join(dirName,filename)
                if verbose:
                    print (prefix + filepath)
                with OpenFile(filepath, opener) as log:
                    yield (log)
    else:
        if verbose:
            print (topdir)
        with OpenFile(topdir, opener) as log:
            yield (log)


def yaml_read(yaml_file):
    if os.path.isfile(yaml_file):
        with open(yaml_file, 'r') as f:
            return yaml.load(f)
    else:
        print("\'{}\' is not a file!".format(yaml_file))


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
            self.fobj =  None
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


def get_nested_key(data, path=None):
    if type(path) is not list:
        raise("Use 'list' object with key names for 'path'")
    for key in path:
        value = data.get(key, None)
        if value:
            data = value
        else:
            return None
    return data


def remove_nested_key(data, path=None):
    if type(path) is not list:
        raise("Use 'list' object with key names for 'path'")

    # Remove the value from the specified key
    val = get_nested_key(data, path[:-1])
    val[path[-1]] = None

    # Clear parent keys if empty
    while path:
        val = get_nested_key(data, path)
        if val:
            # Non-empty value, nothing to do
            return
        else:
            get_nested_key(data, path[:-1]).pop(path[-1])
            path = path[:-1]


def get_all_reclass_params(paths, verbose=False):
    """Return dict with all used values for each param"""
    _params = dict()
    for path in paths:
        for log in walkfiles(path, verbose):
            if log.fname.endswith('.yml'):
                model = yaml_read(log.fname)
                if model is not None:
                    # Collect all params from the models
                    _param = get_nested_key(model, ['parameters', '_param'])
                    if _param:
                        for key, val in _param.items():
                            if key in _params:
                                # Keep list values sorted
                                _params[key].append(val)
                                _params[key] = sorted(_params[key])
                            else:
                                _params[key] = [val]
    return _params


def remove_reclass_parameter(paths, key,
                             verbose=False,
                             pretend=False):
    """Removes specified key from parameters from all reclass models

    :param key: string with point-separated nested objects, for
                example: parameters.linux.network.interface
    :rtype dict: { 'file path': {nested_key}, ...}
    """
    remove_key = key.split('.')
    found_keys = {}

    for path in paths:
        for fyml in walkfiles(path, verbose=verbose):
            if fyml.fname.endswith('.yml'):
                model = yaml_read(fyml.fname)
                if model is not None:

                    # Clear linux.network.interfaces
                    nested_key = get_nested_key(model, remove_key)
                    if nested_key:
                        found_keys[fyml.fname] = copy.deepcopy(nested_key)
                        if pretend:
                            print("\nFound {0} in {1}".format('.'.join(remove_key),
                                                                   fyml.fname))
                            print(yaml.dump(nested_key, default_flow_style=False))
                        else:
                            print("\nRemoving {0} from {1}".format('.'.join(remove_key),
                                                                   fyml.fname))
                            print(yaml.dump(nested_key, default_flow_style=False))

                            remove_nested_key(model, remove_key)

                            with open(fyml.fname, 'w') as f:
                                f.write(
                                    yaml.dump(
                                        model, default_flow_style=False
                                    )
                                )
    return found_keys
