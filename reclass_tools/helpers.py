
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


