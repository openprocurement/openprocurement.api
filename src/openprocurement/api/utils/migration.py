# -*- coding: utf-8 -*-
import sys
import logging

from openprocurement.api.database import set_api_security
from openprocurement.api.utils.common import (
    create_app_meta,
)
from openprocurement.api.utils.plugins import search_entrypoints
from openprocurement.api.utils.searchers import (
    paths_to_key,
    traverse_nested_dicts,
)
from openprocurement.api.migration import (
    AliasesInfoDTO,
    MigrationResourcesDTO,
)

MIGRATION_LOG_FORMAT = '%(asctime)s %(levelname)-5.5s [%(name)s][%(threadName)s] %(message)s'


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
    launcher = PackageMigrationLauncher()
    launcher.launch()
