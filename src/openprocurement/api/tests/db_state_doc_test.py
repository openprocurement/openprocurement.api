# -*- coding: utf-8 -*-
import unittest

from datetime import datetime
from openprocurement.api.tests.base import BaseWebTest
from openprocurement.api.utils.db_state_doc import DBStateDocManager


class DBStateDocManagerTestCase(BaseWebTest):

    def setUp(self):
        super(DBStateDocManagerTestCase, self).setUp()
        self.docname = 'test_dbstate_doc'
        self.manager = DBStateDocManager(self.db, doc_name=self.docname)

    def test_create_doc(self):
        """Create db_state_doc"""
        self.manager._create_doc()

        db_doc = self.db.get(self.docname)
        self.assertNotEqual(db_doc, None, 'db_state_doc must be created')
        created_time = db_doc['db_created']
        # iso8601 timestring with time value always contains 'T'
        self.assertIn('T', created_time, 'Invalid timestring')
        self.assertIn('+00:00', created_time, 'timestamp must be in UTC')

    def test_assure_doc_while_doc_present(self):
        doc = self.manager._create_doc()

        tstamp_old = doc['db_created']

        self.manager.assure_doc()

        doc_updated = doc.load(self.db, self.docname)

        tstamp_new = doc_updated['db_created']
        self.assertEqual(
            tstamp_new.microsecond, tstamp_old.microsecond, 'document should not be changed'
        )

    def test_write_migration_info(self):
        target_params = {
            'name': 'test_name',
            'description': 'test_descr',
            'applied': datetime.now().isoformat()
        }
        self.manager.write_migration_info(**target_params)

        upd_doc = self.db[self.docname]
        self.assertTrue(len(upd_doc['migrations']), 1)

    def tearDown(self):
        dbs_doc = self.db.get(self.docname)
        if dbs_doc:
            self.db.delete(dbs_doc)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DBStateDocManagerTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
