import os
import json
import yaml


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


def create_nested_key(data, path=None, value=None):
    if type(data) is not dict:
        raise("Use 'dict' object for 'data'")
    if type(path) is not list:
        raise("Use 'list' object with key names for 'path'")
    for key in path[:-1]:
        if key not in data:
            data[key] = {}
        data = data[key]
    data[path[-1]] = value


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


def yaml_read(yaml_file):
    if os.path.isfile(yaml_file):
        with open(yaml_file, 'r') as f:
            return yaml.load(f)
    else:
        print("\'{}\' is not a file!".format(yaml_file))


def json_read(yaml_file):
    if os.path.isfile(yaml_file):
        with open(yaml_file, 'r') as f:
            return json.load(f)
    else:
        print("\'{}\' is not a file!".format(yaml_file))


def merge_nested_objects(obj_1, obj_2):
    """Merge two objects with optional key overwrites

    Original : https://stackoverflow.com/a/17860173
    - Merges dicts and lists
    - If a dict key has the suffix '__overwrite__' and boolean value,
      then the key is assumed as a special keyword for merging:
      <key>__overwrite__: True   #  Overwrite the existing <key> content with <key> from obj_2
      <key>__overwrite__: False  #  Keep the existing <key> content from obj_1


      Case #1: Merge dicts and lists, overwrite other types with latest value

        dict_a = {
          'host': '1.1.1.1',
          'ssh': {
            'login': 'user'
          }
        }

        dict_b = {
          'host': '2.2.2.2',
          'ssh': {
            'password': 'pass'
          }
        }

        print(merge_nested_objects(dict_a, dict_b))
        {
          'host': '2.2.2.2',
          'ssh': {
            'login': 'user',
            'password': 'pass',
          }
        }

      Case #2: Use <key>__overwrite__: True to remove previous key content

        dict_a = {
          'host': '1.1.1.1'
          'ssh': {
            'login': 'user'
          }
        }

        dict_b = {
          'ssh__overwrite__': True
          'ssh': {
            'password': 'pass'
          }
        }

        print(merge_nested_objects(dict_a, dict_b))
        {
          'host': '1.1.1.1',
          'ssh': {
            'password': 'pass',
          }
        }

      Case #3: Use <key>__overwrite__: False to skip merging key if already exists

        dict_a = {
          'host': '1.1.1.1'
          'ssh': {
            'login': 'user'
          }
        }

        dict_b = {
          'host__overwrite__': False
          'host': '2.2.2.2'
          'ssh': {
            'login__overwrite__': False
            'login': 'new_user'
            'password': 'pass'
          }
        }

        print(merge_nested_objects(dict_a, dict_b))
        {
          'host': '1.1.1.1',
          'ssh': {
            'login': 'user',
            'password': 'pass'
          }
        }


    """
    # Merge two dicts
    if isinstance(obj_1, dict) and isinstance(obj_2, dict):
        result = {}
        for key, value in obj_1.iteritems():
            if key not in obj_2:
                result[key] = value
            else:
                overwrite_key = key + '__overwrite__'
                if overwrite_key in obj_2 and obj_2[overwrite_key] == True:
                    result[key] = obj_2[key]
                elif overwrite_key in obj_2 and obj_2[overwrite_key] == False:
                    result[key] = value
                else:
                    result[key] = merge_nested_objects(value, obj_2[key])
        for key, value in obj_2.iteritems():
            if key not in obj_1:
                result[key] = value
        return result

    # Add two lists
    if isinstance(obj_1, list) and isinstance(obj_2, list):
        return obj_1 + obj_2

    # Overwrite a value with new one
    return obj_2
