import unittest
from couchdb.tests import testutil

from openprocurement.api.models import TenderDocument


class TestTenderDocument(testutil.TempDatabaseMixin, unittest.TestCase):

    def test_simpleAddTender(self):
        u = TenderDocument()
        u.tenderID = "UA-X"

        assert u.id is None
        assert u.rev is None

        u.store(self.db)

        assert u.id is not None
        assert u.rev is not None

        fromdb = self.db.get(u.id)

        assert u.tenderID == fromdb['tenderID']
        assert u.doc_type == "TenderDocument"

        u.delete_instance(self.db)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestTenderDocument))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
