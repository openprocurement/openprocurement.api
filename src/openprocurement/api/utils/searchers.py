# -*- coding: utf-8 -*-
from copy import copy


def search_list_with_dicts(container, key, value):
    """Search for dict in list with dicts

    :param container: an iterable to search in
    :param key: key of dict to check
    :param value: value of key to search

    :returns: first acceptable dict
    """
    for item in container:
        found_value = item.get(key, False)
        if found_value and found_value == value:
            return item


def dict_traverser(d, trigger_func):
    found_paths = []  # buffer for the results
    current_path = []

    def search(curr_dict, curr_path):
        for key, value in curr_dict.iteritems():
            if trigger_func(key, value):
                curr_path.append(key)
                found_paths.append(tuple(curr_path))
            elif isinstance(value, dict):
                new_path = copy(curr_path)
                new_path.append(key)
                search(value, new_path)

    search(d, current_path)

    if found_paths:
        return tuple(found_paths)

    return None


def path_to_kv(kv, d):
    """Traverse nested dict recursively & search for a given k/v

    :param kv: key/value to seek, tuple
    :param d: dict to search in

    :returns: path(s) to a target k/v
    """
    def trigger(k, v):
        if k == kv[0] and v == kv[1]:
            return True

    return dict_traverser(d, trigger)


def traverse_nested_dicts(d, path):
    """Traverses nested dicts using path of keys"""
    position = None

    for index, step in enumerate(path):
        if index == 0:
            position = d[step]
            continue
        position = position[step]

    return position


def paths_to_key(key, d):
    """Traverse nested dict recursively & search for a given key

    :param key: key to seek
    :param d: dict to search in

    :returns: path(s) to a target key
    """
    def trigger(k, v):
        if k == key:
            return True

    return dict_traverser(d, trigger)
