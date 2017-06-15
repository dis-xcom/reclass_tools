#!/usr/bin/python
# -*- coding: utf-8 -*-

import hashlib
import os
import re
import tarfile

import urllib2
import yaml

from reclass_tools.helpers import ssh_client


def walkfiles(topdir, identity_files=None, verbose=False):
    if ":" in topdir:
        host, path = topdir.split(":")
        private_keys = ssh_client.get_private_keys(os.environ.get("HOME"), identity_files)
        if "@" in host:
            username, host = host.split("@")
        else:
            username = os.environ.get("USER")
        remote = ssh_client.SSHClient(
            host, username=username, private_keys=private_keys)

        walker = remote.walk(path)
        opener = remote.open
        prefix = remote.host + ":"
        isdir = remote.isdir(path, follow_symlink=True)
    else:
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
    #path = '/srv/salt/reclass/classes'
    _params = dict()
    for path in paths:
        for log in walkfiles(path, verbose=verbose):
            if log.fname.endswith('.yml'):
                model = yaml_read(log.fname)
                if model is not None:
                    # Collect all params from the models
                    _param = get_nested_key(model, ['parameters', '_param'])
                    if _param:
                        for key, val in _param.items():
                            if key in _params:
                                _params[key].append(val)
                            else:
                                _params[key] = [val]

    return _params
    #print(yaml.dump(_params))


def remove_reclass_parameter(path, parameter, verbose=False):
    """Removes specified key from parameters from all reclass models"""
    #path = '/srv/salt/reclass/classes'
    _params = dict()
    for log in walkfiles(path, verbose=verbose):
        if log.fname.endswith('.yml'):
            model = yaml_read(log.fname)
            if model is not None:

                # Clear linux.network.interfaces
                interfaces = get_nested_key(model, ['parameters', 'linux', 'network', 'interface'])
                if interfaces:
                    print(log.fname)
                    print(interfaces.keys())

                    remove_nested_key(model, ['parameters', 'linux', 'network', 'interface'])

                    print(model)
                    with open(log.fname, 'w') as f:
                        f.write(
                            yaml.dump(
                                model, default_flow_style=False
                            )
                        )

#                #print(yaml.dump(interfaces, default_flow_style=False))

#                lvm = get_nested_key(model, ['parameters', 'linux', 'storage', 'lvm'])
#                if lvm:
#                    print(log.fname)
#                    print(lvm.keys())
#                    #print(yaml.dump(lvm, default_flow_style=False))

#                mount = get_nested_key(model, ['parameters', 'linux', 'storage', 'mount'])
#                if mount:
#                    print(log.fname)
#                    print(mount.keys())
#                    #print(yaml.dump(mount, default_flow_style=False))

#                swap = get_nested_key(model, ['parameters', 'linux', 'storage', 'swap'])
#                if swap:
#                    print(log.fname)
#                    print(swap.keys())
#                        #print(yaml.dump(swap, default_flow_style=False))
