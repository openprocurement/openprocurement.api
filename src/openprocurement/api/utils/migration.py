# -*- coding: utf-8 -*-
import sys
import logging

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

MIGRATION_LOG_FORMAT = '%(asctime)s %(levelname)-5.5s [%(name)s][%(threadName)s] %(message)s'


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
    elif len(sys.argv) < 3:
        sys.exit('Provide package name as second argument')
    am_filepath = sys.argv[1]
    package_name = sys.argv[2]
    app_meta = create_app_meta(am_filepath)
    logging.basicConfig(level=logging.DEBUG, format=MIGRATION_LOG_FORMAT)
    run_migrations(app_meta, package_name)


class PackageMigrationLauncher(object):
    """Provides pipeline of migration launching process from user input till very launch"""

    _migration_entrypoint_postfix = '.migration'

    def __init__(self):
        logging.basicConfig(level=logging.DEBUG, format=MIGRATION_LOG_FORMAT)

    def launch(self):
        filepath, package_name = self._read_args()
        self._check_package_name(package_name)
        m_package_name = self._build_migration_entrypoint_name(package_name)

        app_meta = create_app_meta(filepath)
        aliases_info = self._build_aliases_info(app_meta, package_name)
        db = self._get_db_connection(app_meta)

        migration_resources = self._build_migration_resources(aliases_info, db)

        ep_funcs = search_entrypoints(m_package_name, None)
        self._check_ep_functions(ep_funcs)
        self._run_migration_entrypoins(ep_funcs, migration_resources)

    def _read_args(self):
        if len(sys.argv) < 2:
            sys.exit('Provide app_meta location as first argument')
        elif len(sys.argv) < 3:
            sys.exit('Provide package name as second argument')
        am_filepath = sys.argv[1]
        package_name = sys.argv[2]

        return am_filepath, package_name

    def _check_package_name(self, p_name):
        package_name_parts = p_name.split('.')
        if len(package_name_parts) < 2:
            raise RuntimeError('Provide full package name. ex: openprocurement.auctions.tessel')

    def _build_migration_entrypoint_name(self, p_name):
        return p_name + self._migration_entrypoint_postfix

    def _build_aliases_info(self, app_meta, p_name):
        paths_to_package = paths_to_key(p_name, app_meta.plugins)
        package_info = traverse_nested_dicts(app_meta.plugins, paths_to_package[0])
        aliases = package_info['aliases']

        return AliasesInfoDTO({p_name: aliases})

    def _get_db_connection(self, app_meta):
        _, _, _, db = set_api_security(app_meta.config.db)
        return db

    def _build_migration_resources(self, aliases_info, db):
        return MigrationResourcesDTO(db, aliases_info)

    def _run_migration_entrypoins(self, ep_funcs, migration_resources):
        for migration_func in ep_funcs:
            migration_func(migration_resources)

    def _check_ep_functions(self, ep_funcs):
        if not ep_funcs:
            raise RuntimeError("No entrypoints was found")


def launch_migration():
    l = PackageMigrationLauncher()
    l.launch()
