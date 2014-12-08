# -*- coding: utf-8 -*-

import unittest

from openprocurement.api.tests import auction, auth, award, bidder, document, migration, spore, tender, question, complaint


def suite():
    suite = unittest.TestSuite()
    suite.addTest(auction.suite())
    suite.addTest(auth.suite())
    suite.addTest(award.suite())
    suite.addTest(bidder.suite())
    suite.addTest(complaint.suite())
    suite.addTest(document.suite())
    suite.addTest(migration.suite())
    suite.addTest(question.suite())
    suite.addTest(spore.suite())
    suite.addTest(tender.suite())
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
