# -*- coding: utf-8 -*-

import unittest

from openprocurement.api.tests import (
    auction,
    auth,
    award,
    bidder,
    cancellation,
    chronograph,
    complaint,
    contract,
    document,
    health,
    lot,
    migration,
    question,
    spore,
    tender,
    utils,
)


def suite():
    tests = unittest.TestSuite()
    tests.addTest(auction.suite())
    tests.addTest(auth.suite())
    tests.addTest(award.suite())
    tests.addTest(bidder.suite())
    tests.addTest(cancellation.suite())
    tests.addTest(chronograph.suite())
    tests.addTest(complaint.suite())
    tests.addTest(contract.suite())
    tests.addTest(document.suite())
    tests.addTest(health.suite())
    tests.addTest(lot.suite())
    tests.addTest(migration.suite())
    tests.addTest(question.suite())
    tests.addTest(spore.suite())
    tests.addTest(tender.suite())
    tests.addTest(utils.suite())
    return tests


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

