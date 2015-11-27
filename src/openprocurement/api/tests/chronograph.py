# -*- coding: utf-8 -*-
import unittest

from openprocurement.api.tests.base import BaseAuctionWebTest, test_lots, test_bids


class AuctionSwitchQualificationResourceTest(BaseAuctionWebTest):
    initial_status = 'active.tendering'
    initial_bids = test_bids[:1]

    def test_switch_to_qualification(self):
        response = self.set_status('active.auction')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "active.qualification")
        self.assertEqual(len(response.json['data']["awards"]), 1)


class AuctionSwitchAuctionResourceTest(BaseAuctionWebTest):
    initial_status = 'active.tendering'
    initial_bids = test_bids

    def test_switch_to_auction(self):
        response = self.set_status('active.auction')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "active.auction")


class AuctionSwitchUnsuccessfulResourceTest(BaseAuctionWebTest):
    initial_status = 'active.tendering'

    def test_switch_to_unsuccessful(self):
        response = self.set_status('active.auction')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "unsuccessful")


class AuctionLotSwitchQualificationResourceTest(BaseAuctionWebTest):
    initial_status = 'active.tendering'
    initial_lots = test_lots
    initial_bids = test_bids[:1]

    def test_switch_to_qualification(self):
        response = self.set_status('active.auction')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "active.qualification")
        self.assertEqual(len(response.json['data']["awards"]), 1)


class AuctionLotSwitchAuctionResourceTest(BaseAuctionWebTest):
    initial_status = 'active.tendering'
    initial_lots = test_lots
    initial_bids = test_bids

    def test_switch_to_auction(self):
        response = self.set_status('active.auction')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "active.auction")


class AuctionLotSwitchUnsuccessfulResourceTest(BaseAuctionWebTest):
    initial_status = 'active.tendering'
    initial_lots = test_lots

    def test_switch_to_unsuccessful(self):
        response = self.set_status('active.auction')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "unsuccessful")
        self.assertEqual(set([i['status'] for i in response.json['data']["lots"]]), set(["unsuccessful"]))


class AuctionAuctionPeriodResourceTest(BaseAuctionWebTest):
    initial_status = 'active.tendering'

    def test_set_auction_period(self):
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json('/auctions/{}'.format(self.auction_id), {'data': {"auctionPeriod": {"startDate": "9999-01-01T00:00:00+00:00"}}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['auctionPeriod']['startDate'], '9999-01-01T00:00:00+00:00')

        response = self.app.patch_json('/auctions/{}'.format(self.auction_id), {'data': {"auctionPeriod": {"startDate": None}}})
        self.assertEqual(response.status, '200 OK')
        self.assertNotIn('auctionPeriod', response.json['data'])


class AuctionLotAuctionPeriodResourceTest(BaseAuctionWebTest):
    initial_status = 'active.tendering'
    initial_lots = test_lots

    def test_set_auction_period(self):
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json('/auctions/{}'.format(self.auction_id), {'data': {"lots": [{"auctionPeriod": {"startDate": "9999-01-01T00:00:00+00:00"}}]}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']["lots"][0]['auctionPeriod']['startDate'], '9999-01-01T00:00:00+00:00')

        response = self.app.patch_json('/auctions/{}'.format(self.auction_id), {'data': {"lots": [{"auctionPeriod": {"startDate": None}}]}})
        self.assertEqual(response.status, '200 OK')
        self.assertNotIn('auctionPeriod', response.json['data']["lots"][0])


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AuctionSwitchQualificationResourceTest))
    suite.addTest(unittest.makeSuite(AuctionSwitchAuctionResourceTest))
    suite.addTest(unittest.makeSuite(AuctionSwitchUnsuccessfulResourceTest))
    suite.addTest(unittest.makeSuite(AuctionLotSwitchQualificationResourceTest))
    suite.addTest(unittest.makeSuite(AuctionLotSwitchAuctionResourceTest))
    suite.addTest(unittest.makeSuite(AuctionLotSwitchUnsuccessfulResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
