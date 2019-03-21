# -*- coding: utf-8 -*-
import unittest

from copy import copy
from mock import Mock, MagicMock

from openprocurement.api.migration import (
    AliasesInfoDTO,
    BaseMigrationsRunner,
    MigrationResourcesDTO,
    get_db_schema_version,
    migrate_data,
)
from openprocurement.api.constants import (
    SCHEMA_VERSION
)
from openprocurement.api.tests.base import BaseWebTest


class MigrateTest(BaseWebTest):

    def setUp(self):
        super(MigrateTest, self).setUp()
        migrate_data(self.app.app.registry)

    def test_migrate(self):
        self.assertEqual(get_db_schema_version(self.db), SCHEMA_VERSION)
        migrate_data(self.app.app.registry, 1)
        self.assertEqual(get_db_schema_version(self.db), SCHEMA_VERSION)


class BaseMigrationRunnerTestCase(unittest.TestCase):

    default_db_version = 0
    DB_DOCS_COUNT = 2

    class TestMigrationRunner(BaseMigrationsRunner):

        SCHEMA_VERSION = 1
        SCHEMA_DOC = 'test_scema'

    def get_db_schema_version_mock(self, db_version=None):
        m = Mock()
        m.return_value = db_version if db_version else self.default_db_version

        return m

    def set_db_schema_version_mock(self):
        m = Mock()

        return m

    def db_mock(self, iterview_generator):
        db = Mock()
        db.iterview = iterview_generator

        return db

    def iterview_results_generator(self, count_to_procuce=1):

        def iterview(*args, **kwargs):
            produced = 0

            doc_data = {
                '_id': 'test_id_{0}',
                'name': 'Harry',
                'surname': 'Na Ferrarri'
            }
            while produced < count_to_procuce:
                data = copy(doc_data)
                data['_id'] = data['_id'].format(str(produced))
                db_row = Mock(doc=data)
                yield db_row
                produced += 1

        return iterview

    def step_mock(self):
        # A quite sophisticated mock, bcs there's a need
        # to access class and it's inctance as well

        s_class = Mock(__name__='test_step_class_name')

        s_instance = Mock()
        s_instance.setUp = Mock()
        s_instance.migrate_document = MagicMock()
        s_instance.tearDown = Mock()

        s_class.return_value = s_instance

        return (s_class, s_instance)

    def aliases_info_dto_mock(self, aliases_info=None):
        aliases_info_default = {'pack': ['al1', 'al2']}
        ai = AliasesInfoDTO(aliases_info if aliases_info else aliases_info_default)

        return ai

    def migration_resources_dto_mock(self):
        ai = self.aliases_info_dto_mock()
        db = self.db_mock(self.iterview_results_generator(self.DB_DOCS_COUNT))

        mr = MigrationResourcesDTO(db, ai)

        return mr

    def setUp(self):
        migration_resources = self.migration_resources_dto_mock()
        self.runner = self.TestMigrationRunner(migration_resources)
        self.runner._get_db_schema_version = self.get_db_schema_version_mock()
        self.runner._set_db_schema_version = self.set_db_schema_version_mock()

    def test_run_single_migration_step(self):
        step_class, step = self.step_mock()
        steps = (step_class,)
        self.runner.migrate(steps)

        self.assertEqual(step.setUp.call_count, 1)
        self.assertEqual(step.tearDown.call_count, 1)
        self.assertEqual(step.migrate_document.call_count, self.DB_DOCS_COUNT)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MigrateTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
