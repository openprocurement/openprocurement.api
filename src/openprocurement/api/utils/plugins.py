# -*- coding: utf-8 -*-
import collections

from pkg_resources import iter_entry_points
from openprocurement.api.exceptions import ConfigAliasError
from openprocurement.api.constants import (
    LOGGER,
)


def get_evenly_plugins(config, plugin_map, group):
    """
    Load plugin which fall into the group
    :param config: app config
    :param plugin_map: mapping of plugins names
    :param group: group of entry point

    :type config: Configurator
    :type plugin_map: abs.Mapping
    :type group: string

    :rtype: None
    """

    if not hasattr(plugin_map, '__iter__'):
        return
    for name in plugin_map:
        for entry_point in iter_entry_points(group, name):
            plugin = entry_point.load()
            value = plugin_map.get(name) if plugin_map.get(name) else {}
            plugin(config, collections.defaultdict(lambda: None, value))
            break
        else:
            LOGGER.warning("Could not find plugin for "
                           "entry_point '{}' in '{}' group".format(name, group))


def get_plugins(plugins_map):
    plugins = []
    for item in plugins_map:
        plugins.append(item)
        if isinstance(plugins_map[item], collections.Mapping) and plugins_map[item].get('plugins'):
            plugins.extend(get_plugins(plugins_map[item]['plugins']))
    return plugins


def format_aliases(alias):
    """Converts an dictionary where key is 'plugin name'
    and value is 'a list with aliases'

    Args:
        alias An dictionary object

    Returns:
        A string representation of plugin and object
    """
    for k, v in alias.items():
        info = '{} aliases: {}'.format(k, v)
    return info


def check_alias(alias):
    """Checks whether a plugin contains an repeated aliases

    Note:
        If a plugin contains an repeated aliases
        we raise ConfigAliasError

    Args:
        alias a dictionary with alias info,
    where key is a name of a package, and value
    of which contains his aliases
    """
    for _, value in alias.items():
        duplicated = collections.Counter(value)
        for d_key, d_value in duplicated.items():
            if d_value >= 2:
                raise ConfigAliasError(
                    'Alias {} repeating {} times'.format(d_key, d_value)
                )


def make_aliases(plugin):
    """Makes a dictionary with aliases information

    Args:
        plugin A dictionary with an plugins information

    Returns:
        aliases A list with dictionary objects, where key
    is a name of a plugin, and value is a list of an aliases
    Otherwise an empty list
    """
    if plugin:
        aliases = []
        for key, val in plugin.items():
            if plugin[key] is None:
                continue
            alias = {key: val['aliases']}
            aliases.append(alias)
        return aliases
    LOGGER.warning('Aliases not provided, check your app_meta file')
    return []


def get_plugin_aliases(plugin):
    """Returns an array with plugin aliases information
       If an aliases were repeated more than one time
       we raise AttributeError

    Example:
        data = {'auctions.rubble.financial': {'aliases': []}}
        get_plugin_aliases(data)
    ['auctions.rubble.financial aliases: []']

    Args:
        plugin an configurations dictionary
    """
    aliases = make_aliases(plugin)
    for alias in aliases:
        LOGGER.info(format_aliases(alias))

    for alias in aliases:
        check_alias(alias)
