# -*- coding: utf-8 -*-
import sys

from pkg_resources import iter_entry_points
from openprocurement.api.database import set_api_security
from openprocurement.api.utils.common import (
    create_app_meta,
)
from openprocurement.api.utils.plugins import search_entrypoints
from openprocurement.api.utils.searchers import (
    path_to_kv,
    paths_to_key,
    traverse_nested_dicts,
)
from openprocurement.api.migration import (
    AliasesInfoDTO,
    MigrationResourcesDTO,
)


def collect_packages_for_migration(plugins):
    migration_kv = ('migration', True)
    results_buffer = []

    paths = path_to_kv(migration_kv, plugins)
    if not paths:
        return None

    for path in paths:
        package_name = path[-2]
        results_buffer.append(package_name)

    if results_buffer:
        return tuple(results_buffer)

    return None


def collect_migration_entrypoints(package_names, name='main'):
    """Collect migration functions from specified entrypoint groups"""
    # form entrypoint groups names
    ep_group_names = []
    for g in package_names:
        ep_group_name = '{0}.migration'.format(g)
        ep_group_names.append(ep_group_name)

    ep_funcs = []
    for group in ep_group_names:
        ep_funcs.append(search_entrypoints(group, name))

    return ep_funcs


def run_migrations(app_meta, package_name):
    # provide package name in format like this: lots.loki
    package_name_parts = package_name.split('.')
    if len(package_name_parts) != 3:
        raise RuntimeError('Provide fill package name. ex: openprocurement.auctions.tessel')
    last_parts = (package_name_parts[-2], package_name_parts[-1])
    package_name_in_app_meta_format = '.'.join(last_parts)

    paths_to_package = paths_to_key(package_name_in_app_meta_format, app_meta.plugins)
    package_info = traverse_nested_dicts(app_meta.plugins, paths_to_package[0])
    aliases = package_info['aliases']

    aliases_info = AliasesInfoDTO({package_name: aliases})
    _, _, _, db = set_api_security(app_meta.config.db)
    migration_resources = MigrationResourcesDTO(db, aliases_info)

    group_name = '{0}.migration'.format(package_name_in_app_meta_format)
    ep_funcs = search_entrypoints(group_name, None)

    for migration_func in ep_funcs:
        migration_func(migration_resources)


def run_migrations_console_entrypoint():
    """Search for migrations in the app_meta and run them if enabled

    This is an entrypoint for console script.
    """
    # due to indirect calling of this function, namely through the script,
    # generated from the package's entrypionts, argparse lib usage is troublesome
    if len(sys.argv) < 2:
        sys.exit('Provide app_meta location as first argument')
    am_filepath = sys.argv[1]
    package_name = sys.argv[2]
    app_meta = create_app_meta(am_filepath)
    run_migrations(app_meta, package_name)
