# -*- coding: utf-8 -*-
import unittest

from openprocurement.api.tests.base import BaseTenderWebTest, test_lots, test_bids


class TenderSwitchTenderingResourceTest(BaseTenderWebTest):

    def test_switch_to_tendering_by_enquiryPeriod_endDate(self):
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {'id': self.tender_id}})
        self.assertEqual(response.status, '200 OK')
        self.assertNotEqual(response.json['data']["status"], "active.tendering")
        self.set_status('active.tendering', {'status': 'active.enquiries', "tenderPeriod": {"startDate": None}})
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

    def test_switch_to_tendering_auctionPeriod(self):
        self.set_status('active.tendering', {'status': 'active.enquiries', "tenderPeriod": {"startDate": None}})
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {'id': self.tender_id}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']["status"], "active.tendering")
        self.assertIn('auctionPeriod', response.json['data'])


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
        if self.initial_lots:
            self.assertEqual(set([i['status'] for i in response.json['data']["lots"]]), set(["unsuccessful"]))


class TenderLotSwitchQualificationResourceTest(TenderSwitchQualificationResourceTest):
    initial_lots = test_lots


class TenderLotSwitchAuctionResourceTest(TenderSwitchAuctionResourceTest):
    initial_lots = test_lots


class TenderLotSwitchUnsuccessfulResourceTest(TenderSwitchUnsuccessfulResourceTest):
    initial_lots = test_lots


class TenderAuctionPeriodResourceTest(BaseTenderWebTest):
    initial_bids = test_bids

    def test_set_auction_period(self):
        self.set_status('active.tendering', {'status': 'active.enquiries'})
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {'id': self.tender_id}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], 'active.tendering')
        if self.initial_lots:
            item = response.json['data']["lots"][0]
        else:
            item = response.json['data']
        self.assertIn('auctionPeriod', item)
        self.assertIn('shouldStartAfter', item['auctionPeriod'])
        self.assertEqual(item['auctionPeriod']['shouldStartAfter'], response.json['data']['tenderPeriod']['endDate'])
        self.assertEqual(response.json['data']['next_check'], response.json['data']['tenderPeriod']['endDate'])

        if self.initial_lots:
            response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {"lots": [{"auctionPeriod": {"startDate": "9999-01-01T00:00:00+00:00"}}]}})
            item = response.json['data']["lots"][0]
        else:
            response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {"auctionPeriod": {"startDate": "9999-01-01T00:00:00+00:00"}}})
            item = response.json['data']
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(item['auctionPeriod']['startDate'], '9999-01-01T00:00:00+00:00')

        if self.initial_lots:
            response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {"lots": [{"auctionPeriod": {"startDate": None}}]}})
            item = response.json['data']["lots"][0]
        else:
            response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {"auctionPeriod": {"startDate": None}}})
            item = response.json['data']
        self.assertEqual(response.status, '200 OK')
        self.assertNotIn('startDate', item['auctionPeriod'])

    def test_reset_auction_period(self):
        self.set_status('active.tendering', {'status': 'active.enquiries'})
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {'id': self.tender_id}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], 'active.tendering')
        if self.initial_lots:
            item = response.json['data']["lots"][0]
        else:
            item = response.json['data']
        self.assertIn('auctionPeriod', item)
        self.assertIn('shouldStartAfter', item['auctionPeriod'])
        self.assertEqual(item['auctionPeriod']['shouldStartAfter'], response.json['data']['tenderPeriod']['endDate'])
        self.assertEqual(response.json['data']['next_check'], response.json['data']['tenderPeriod']['endDate'])

        if self.initial_lots:
            response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {"lots": [{"auctionPeriod": {"startDate": "9999-01-01T00:00:00"}}]}})
            item = response.json['data']["lots"][0]
        else:
            response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {"auctionPeriod": {"startDate": "9999-01-01T00:00:00"}}})
            item = response.json['data']
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(item['auctionPeriod']['shouldStartAfter'], response.json['data']['tenderPeriod']['endDate'])
        self.assertIn('9999-01-01T00:00:00', item['auctionPeriod']['startDate'])

        self.set_status('active.auction', {'status': 'active.tendering'})
        if self.initial_lots:
            response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {"lots": [{"auctionPeriod": {"startDate": "9999-01-01T00:00:00"}}]}})
            item = response.json['data']["lots"][0]
        else:
            response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {"auctionPeriod": {"startDate": "9999-01-01T00:00:00"}}})
            item = response.json['data']
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']["status"], 'active.auction')
        self.assertEqual(item['auctionPeriod']['shouldStartAfter'], response.json['data']['tenderPeriod']['endDate'])
        self.assertIn('9999-01-01T00:00:00', item['auctionPeriod']['startDate'])
        self.assertIn('9999-01-01T00:00:00', response.json['data']['next_check'])

        if self.initial_lots:
            response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {"lots": [{"auctionPeriod": {"startDate": response.json['data']['tenderPeriod']['endDate']}}]}})
            item = response.json['data']["lots"][0]
        else:
            response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {"auctionPeriod": {"startDate": response.json['data']['tenderPeriod']['endDate']}}})
            item = response.json['data']
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']["status"], 'active.auction')
        self.assertEqual(item['auctionPeriod']['shouldStartAfter'], response.json['data']['tenderPeriod']['endDate'])
        self.assertNotIn('9999-01-01T00:00:00', item['auctionPeriod']['startDate'])
        self.assertGreater(response.json['data']['next_check'], response.json['data']['tenderPeriod']['endDate'])

        tender = self.db.get(self.tender_id)
        tender['tenderPeriod']['endDate'] = tender['tenderPeriod']['startDate']
        if self.initial_lots:
            tender['lots'][0]['auctionPeriod']['startDate'] = tender['tenderPeriod']['startDate']
        else:
            tender['auctionPeriod']['startDate'] = tender['tenderPeriod']['startDate']
        self.db.save(tender)

        response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {'id': self.tender_id}})
        if self.initial_lots:
            item = response.json['data']["lots"][0]
        else:
            item = response.json['data']
        self.assertGreater(item['auctionPeriod']['shouldStartAfter'], response.json['data']['tenderPeriod']['endDate'])
        self.assertNotIn('next_check', response.json['data'])
        shouldStartAfter = item['auctionPeriod']['shouldStartAfter']

        response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {'id': self.tender_id}})
        if self.initial_lots:
            item = response.json['data']["lots"][0]
        else:
            item = response.json['data']
        self.assertEqual(item['auctionPeriod']['shouldStartAfter'], shouldStartAfter)
        self.assertNotIn('next_check', response.json['data'])

        if self.initial_lots:
            response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {"lots": [{"auctionPeriod": {"startDate": "9999-01-01T00:00:00"}}]}})
            item = response.json['data']["lots"][0]
        else:
            response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {"auctionPeriod": {"startDate": "9999-01-01T00:00:00"}}})
            item = response.json['data']
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']["status"], 'active.auction')
        self.assertEqual(item['auctionPeriod']['shouldStartAfter'], response.json['data']['tenderPeriod']['endDate'])
        self.assertIn('9999-01-01T00:00:00', item['auctionPeriod']['startDate'])
        self.assertIn('9999-01-01T00:00:00', response.json['data']['next_check'])


class TenderLotAuctionPeriodResourceTest(TenderAuctionPeriodResourceTest):
    initial_lots = test_lots


class TenderComplaintSwitchResourceTest(BaseTenderWebTest):

    def test_switch_to_pending(self):
        response = self.app.post_json('/tenders/{}/complaints'.format(self.tender_id), {'data': {
            'title': 'complaint title',
            'description': 'complaint description',
            'author': self.initial_data["procuringEntity"],
            'status': 'claim'
        }})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.json['data']['status'], 'claim')

        tender = self.db.get(self.tender_id)
        tender['complaints'][0]['dateSubmitted'] = '2014-01-01'
        self.db.save(tender)

        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {'id': self.tender_id}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']["complaints"][0]['status'], 'pending')

    def test_switch_to_complaint(self):
        for status in ['invalid', 'resolved', 'declined']:
            self.app.authorization = ('Basic', ('token', ''))
            response = self.app.post_json('/tenders/{}/complaints'.format(self.tender_id), {'data': {
                'title': 'complaint title',
                'description': 'complaint description',
                'author': self.initial_data["procuringEntity"],
                'status': 'claim'
            }})
            self.assertEqual(response.status, '201 Created')
            self.assertEqual(response.json['data']['status'], 'claim')
            complaint = response.json['data']

            response = self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(self.tender_id, complaint['id'], self.tender_token), {"data": {
                "status": "answered",
                "resolutionType": status
            }})
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.json['data']["status"], "answered")
            self.assertEqual(response.json['data']["resolutionType"], status)

            tender = self.db.get(self.tender_id)
            tender['complaints'][-1]['dateAnswered'] = '2014-01-01'
            self.db.save(tender)

            self.app.authorization = ('Basic', ('chronograph', ''))
            response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {'id': self.tender_id}})
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.json['data']["complaints"][-1]['status'], status)


class TenderLotComplaintSwitchResourceTest(TenderComplaintSwitchResourceTest):
    initial_lots = test_lots


class TenderAwardComplaintSwitchResourceTest(BaseTenderWebTest):
    initial_status = 'active.qualification'
    initial_bids = test_bids

    def setUp(self):
        super(TenderAwardComplaintSwitchResourceTest, self).setUp()
        # Create award
        response = self.app.post_json('/tenders/{}/awards'.format(
            self.tender_id), {'data': {'suppliers': [self.initial_data["procuringEntity"]], 'status': 'pending', 'bid_id': self.initial_bids[0]['id']}})
        award = response.json['data']
        self.award_id = award['id']

    def test_switch_to_pending(self):
        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(self.tender_id, self.award_id), {'data': {
            'title': 'complaint title',
            'description': 'complaint description',
            'author': self.initial_data["procuringEntity"],
            'status': 'claim'
        }})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.json['data']['status'], 'claim')

        response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, self.award_id), {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "active")

        tender = self.db.get(self.tender_id)
        tender['awards'][0]['complaints'][0]['dateSubmitted'] = '2014-01-01'
        self.db.save(tender)

        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {'id': self.tender_id}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['awards'][0]["complaints"][0]['status'], 'pending')

    def test_switch_to_complaint(self):
        response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, self.award_id), {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "active")

        for status in ['invalid', 'resolved', 'declined']:
            self.app.authorization = ('Basic', ('token', ''))
            response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(self.tender_id, self.award_id), {'data': {
                'title': 'complaint title',
                'description': 'complaint description',
                'author': self.initial_data["procuringEntity"],
                'status': 'claim'
            }})
            self.assertEqual(response.status, '201 Created')
            self.assertEqual(response.json['data']['status'], 'claim')
            complaint = response.json['data']

            response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.award_id, complaint['id'], self.tender_token), {"data": {
                "status": "answered",
                "resolutionType": status
            }})
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.json['data']["status"], "answered")
            self.assertEqual(response.json['data']["resolutionType"], status)

            tender = self.db.get(self.tender_id)
            tender['awards'][0]['complaints'][-1]['dateAnswered'] = '2014-01-01'
            self.db.save(tender)

            self.app.authorization = ('Basic', ('chronograph', ''))
            response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {'id': self.tender_id}})
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.json['data']['awards'][0]["complaints"][-1]['status'], status)


class TenderLotAwardComplaintSwitchResourceTest(TenderAwardComplaintSwitchResourceTest):
    initial_lots = test_lots

    def setUp(self):
        super(TenderAwardComplaintSwitchResourceTest, self).setUp()
        # Create award
        response = self.app.post_json('/tenders/{}/awards'.format(self.tender_id), {'data': {
            'suppliers': [self.initial_data["procuringEntity"]],
            'status': 'pending',
            'bid_id': self.initial_bids[0]['id'],
            'lotID': self.initial_bids[0]['lotValues'][0]['relatedLot']
        }})
        award = response.json['data']
        self.award_id = award['id']


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TenderAwardComplaintSwitchResourceTest))
    suite.addTest(unittest.makeSuite(TenderComplaintSwitchResourceTest))
    suite.addTest(unittest.makeSuite(TenderLotAwardComplaintSwitchResourceTest))
    suite.addTest(unittest.makeSuite(TenderLotComplaintSwitchResourceTest))
    suite.addTest(unittest.makeSuite(TenderLotSwitchAuctionResourceTest))
    suite.addTest(unittest.makeSuite(TenderLotSwitchQualificationResourceTest))
    suite.addTest(unittest.makeSuite(TenderLotSwitchUnsuccessfulResourceTest))
    suite.addTest(unittest.makeSuite(TenderSwitchAuctionResourceTest))
    suite.addTest(unittest.makeSuite(TenderSwitchQualificationResourceTest))
    suite.addTest(unittest.makeSuite(TenderSwitchUnsuccessfulResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
