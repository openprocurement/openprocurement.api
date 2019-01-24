# -*- coding: utf-8 -*-
import mock
import unittest

from copy import deepcopy

from openprocurement.api.utils.migration import (
    collect_packages_for_migration,
    run_migrations_console_entrypoint,
)
from openprocurement.api.tests.fixtures.config import RANDOM_PLUGINS


class CollectPackagesForMigrationTestCase(unittest.TestCase):

    def setUp(self):
        self.plugins = deepcopy(RANDOM_PLUGINS)

    def test_ok(self):
        result = collect_packages_for_migration(self.plugins)

        target_result = ('auctions.rubble.other',)
        self.assertEqual(result, target_result)

    def test_none_find(self):
        self.plugins['api']['plugins']['auctions.core']['plugins']['auctions.rubble.other']['migration'] = False

        result = collect_packages_for_migration(self.plugins)

        target_result = None
        self.assertEqual(result, target_result)


class RunMigrationsConsoleEntrypointTestCase(unittest.TestCase):

    @mock.patch('openprocurement.api.utils.migration.run_migrations')
    @mock.patch('openprocurement.api.utils.migration.create_app_meta')
    @mock.patch('openprocurement.api.utils.migration.sys')
    def test_ok(self, argv_mock, create_app_meta, run_migrations):
        argv_mock.configure_mock(**{'argv': ('1', '2')})
        create_app_meta.return_value = 'test_app_meta'

        run_migrations_console_entrypoint()
        self.assertEqual(
            run_migrations.call_args[0][0], 'test_app_meta', 'run_migrations did not received proper argument'
        )
