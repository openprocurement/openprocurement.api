# -*- coding: utf-8 -*-
import sys

from pkg_resources import iter_entry_points
from openprocurement.api.database import set_api_security
from openprocurement.api.utils.common import (
    create_app_meta,
)
from openprocurement.api.utils.searchers import (
    path_to_kv,
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
        for ep in iter_entry_points(group, name):
            ep_func = ep.load()
            ep_funcs.append(ep_func)

    return ep_funcs


def run_migrations(app_meta):
    packages_for_migrations_names = collect_packages_for_migration(app_meta.plugins)
    ep_funcs = collect_migration_entrypoints(packages_for_migrations_names)
    _, _, _, db = set_api_security(app_meta.config.db)

    for migration_func in ep_funcs:
        migration_func(db)


def run_migrations_console_entrypoint():
    """Search for migrations in the app_meta and run them if enabled

    This is an entrypoint for console script.
    """
    # due to indirect calling of this function, namely through the script,
    # generated from the package's entrypionts, argparse lib usage is troublesome
    if len(sys.argv) < 2:
        sys.exit('Provide app_meta location as first argument')
    am_filepath = sys.argv[1]
    app_meta = create_app_meta(am_filepath)
    run_migrations(app_meta)
