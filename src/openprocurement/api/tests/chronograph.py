# -*- coding: utf-8 -*-
import unittest

from openprocurement.api.tests.base import BaseTenderWebTest, test_lots, test_bids


class TenderSwitchQualificationResourceTest(BaseTenderWebTest):
    initial_status = 'active.tendering'
    initial_bids = test_bids[:1]

    def test_switch_to_qualification(self):
        response = self.set_status('active.auction')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "active.qualification")
        self.assertEqual(len(response.json['data']["awards"]), 1)


class TenderSwitchAuctionResourceTest(BaseTenderWebTest):
    initial_status = 'active.tendering'
    initial_bids = test_bids

    def test_switch_to_auction(self):
        response = self.set_status('active.auction')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "active.auction")


class TenderSwitchUnsuccessfulResourceTest(BaseTenderWebTest):
    initial_status = 'active.tendering'

    def test_switch_to_unsuccessful(self):
        response = self.set_status('active.auction')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "unsuccessful")


class TenderLotSwitchQualificationResourceTest(BaseTenderWebTest):
    initial_status = 'active.tendering'
    initial_lots = test_lots
    initial_bids = test_bids[:1]

    def test_switch_to_qualification(self):
        response = self.set_status('active.auction')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "active.qualification")
        self.assertEqual(len(response.json['data']["awards"]), 1)


class TenderLotSwitchAuctionResourceTest(BaseTenderWebTest):
    initial_status = 'active.tendering'
    initial_lots = test_lots
    initial_bids = test_bids

    def test_switch_to_auction(self):
        response = self.set_status('active.auction')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "active.auction")


class TenderLotSwitchUnsuccessfulResourceTest(BaseTenderWebTest):
    initial_status = 'active.tendering'
    initial_lots = test_lots

    def test_switch_to_unsuccessful(self):
        response = self.set_status('active.auction')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "unsuccessful")
        self.assertEqual(set([i['status'] for i in response.json['data']["lots"]]), set(["unsuccessful"]))


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TenderSwitchQualificationResourceTest))
    suite.addTest(unittest.makeSuite(TenderSwitchAuctionResourceTest))
    suite.addTest(unittest.makeSuite(TenderSwitchUnsuccessfulResourceTest))
    suite.addTest(unittest.makeSuite(TenderLotSwitchQualificationResourceTest))
    suite.addTest(unittest.makeSuite(TenderLotSwitchAuctionResourceTest))
    suite.addTest(unittest.makeSuite(TenderLotSwitchUnsuccessfulResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
