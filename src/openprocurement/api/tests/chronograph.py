# -*- coding: utf-8 -*-
import unittest

from openprocurement.api.tests.base import BaseTenderWebTest, test_lots, test_bids


class TenderSwitchTenderingResourceTest(BaseTenderWebTest):

    def test_switch_to_tendering_by_enquiryPeriod_endDate(self):
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {'id': self.tender_id}})
        self.assertEqual(response.status, '200 OK')
        self.assertNotEqual(response.json['data']["status"], "active.tendering")
        self.set_status('active.tendering', {'status': 'active.enquiries'})
        response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {'id': self.tender_id}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']["status"], "active.tendering")

    def test_switch_to_tendering_by_tenderPeriod_startDate(self):
        self.set_status('active.tendering', {'status': 'active.enquiries', "tenderPeriod": {}})
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {'id': self.tender_id}})
        self.assertEqual(response.status, '200 OK')
        self.assertNotEqual(response.json['data']["status"], "active.tendering")
        self.set_status('active.tendering', {'status': self.initial_status, "enquiryPeriod": {}})
        response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {'id': self.tender_id}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']["status"], "active.tendering")


class TenderSwitchQualificationResourceTest(BaseTenderWebTest):
    initial_status = 'active.tendering'
    initial_bids = test_bids[:1]

    def test_switch_to_qualification(self):
        response = self.set_status('active.auction', {'status': self.initial_status})
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {'id': self.tender_id}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "active.qualification")
        self.assertEqual(len(response.json['data']["awards"]), 1)


class TenderSwitchAuctionResourceTest(BaseTenderWebTest):
    initial_status = 'active.tendering'
    initial_bids = test_bids

    def test_switch_to_auction(self):
        response = self.set_status('active.auction', {'status': self.initial_status})
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {'id': self.tender_id}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "active.auction")


class TenderSwitchUnsuccessfulResourceTest(BaseTenderWebTest):
    initial_status = 'active.tendering'

    def test_switch_to_unsuccessful(self):
        response = self.set_status('active.auction', {'status': self.initial_status})
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {'id': self.tender_id}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "unsuccessful")


class TenderLotSwitchQualificationResourceTest(BaseTenderWebTest):
    initial_status = 'active.tendering'
    initial_lots = test_lots
    initial_bids = test_bids[:1]

    def test_switch_to_qualification(self):
        response = self.set_status('active.auction', {'status': self.initial_status})
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {'id': self.tender_id}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "active.qualification")
        self.assertEqual(len(response.json['data']["awards"]), 1)


class TenderLotSwitchAuctionResourceTest(BaseTenderWebTest):
    initial_status = 'active.tendering'
    initial_lots = test_lots
    initial_bids = test_bids

    def test_switch_to_auction(self):
        response = self.set_status('active.auction', {'status': self.initial_status})
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {'id': self.tender_id}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "active.auction")


class TenderLotSwitchUnsuccessfulResourceTest(BaseTenderWebTest):
    initial_status = 'active.tendering'
    initial_lots = test_lots

    def test_switch_to_unsuccessful(self):
        response = self.set_status('active.auction', {'status': self.initial_status})
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {'id': self.tender_id}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "unsuccessful")
        self.assertEqual(set([i['status'] for i in response.json['data']["lots"]]), set(["unsuccessful"]))


class TenderAuctionPeriodResourceTest(BaseTenderWebTest):
    initial_status = 'active.tendering'

    def test_set_auction_period(self):
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {"auctionPeriod": {"startDate": "9999-01-01T00:00:00+00:00"}}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['auctionPeriod']['startDate'], '9999-01-01T00:00:00+00:00')

        response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {"auctionPeriod": {"startDate": None}}})
        self.assertEqual(response.status, '200 OK')
        self.assertNotIn('auctionPeriod', response.json['data'])


class TenderLotAuctionPeriodResourceTest(BaseTenderWebTest):
    initial_status = 'active.tendering'
    initial_lots = test_lots

    def test_set_auction_period(self):
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {"lots": [{"auctionPeriod": {"startDate": "9999-01-01T00:00:00+00:00"}}]}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']["lots"][0]['auctionPeriod']['startDate'], '9999-01-01T00:00:00+00:00')

        response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {"lots": [{"auctionPeriod": {"startDate": None}}]}})
        self.assertEqual(response.status, '200 OK')
        self.assertNotIn('auctionPeriod', response.json['data']["lots"][0])


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
