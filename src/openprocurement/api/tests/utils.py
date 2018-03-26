# -*- coding: utf-8 -*-
import unittest

from openprocurement.api.models import (
    Tender,
    Bid
)
from openprocurement.api.traversal import Root
from openprocurement.api.utils import (
    get_request_from_root
)
from openprocurement.api.tests.base import (
    BaseWebTest,
    test_tender_data,
    RequestWithRegistry,
    test_bids
)


class TestCoreUtils(BaseWebTest):

    def test_get_request_from_root_with_request(self):
        # Create tender with Tender model
        test_tender = Tender(test_tender_data)

        # Init root and add tender parent
        root = Root(RequestWithRegistry(self.app.app.registry))
        test_tender.__parent__ = root

        # get_request_from_root should return RequestWithRegistry instance
        self.assertIsInstance(get_request_from_root(test_tender),
                              RequestWithRegistry)

        # Add Tender to bid as parent
        test_bid = Bid(test_bids[0])
        test_bid.__parent__ = test_tender

        # get_request_from_root should returb ReqeustWithRegistry instance
        self.assertIsInstance(get_request_from_root(test_bid),
                              RequestWithRegistry)

    def test_get_request_from_root_without_request(self):
        # create tender without reqeust
        test_tender = Tender(test_tender_data)
        test_tender.tenderid = "ua-x"
        test_tender.store(self.db)

        # get_request_from_root should return None
        self.assertIsNone(get_request_from_root(test_tender))


def suite():
    tests = unittest.TestSuite()
    tests.addTest(unittest.makeSuite(TestCoreUtils))
    return tests
