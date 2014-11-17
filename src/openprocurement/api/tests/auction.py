# -*- coding: utf-8 -*-
import unittest

from openprocurement.api.tests.base import test_tender_data, BaseWebTest
from iso8601 import parse_date
from tzlocal import get_localzone


class TenderAuctionResourceTest(BaseWebTest):

    def setUp(self):
        super(TenderAuctionResourceTest, self).setUp()
        # Create tender with bids
        self.tender_data = test_tender_data.copy()
        self.tender_data['bids'] = [
            {
                "id": "4879d3f8ee2443169b5fbbc9f89fa606",
                "status": "registration",
                "date": "2014-10-28T11:44:17.946",
                "bidders": [
                    test_tender_data["procuringEntity"]
                ],
                "totalValue": {
                    "amount": 469,
                    "currency": "UAH",
                    "valueAddedTaxIncluded": True
                }
            },
            {
                "id": "4879d3f8ee2443169b5fbbc9f89fa607",
                "status": "registration",
                "date": "2014-10-28T11:44:17.947",
                "bidders": [
                    test_tender_data["procuringEntity"]
                ],
                "totalValue": {
                    "amount": 479,
                    "currency": "UAH",
                    "valueAddedTaxIncluded": True
                }
            }
        ]
        response = self.app.post_json('/tenders', {'data': self.tender_data})
        tender = response.json['data']
        self.tender_id = tender['id']

    def tearDown(self):
        del self.db[self.tender_id]
        super(TenderAuctionResourceTest, self).tearDown()

    def test_get_tender_auction_not_found(self):
        response = self.app.get('/tenders/some_id/auction', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])
        response = self.app.patch_json('/tenders/some_id/auction', {'data': {}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

    def test_get_tender_auction(self):
        response = self.app.get('/tenders/{}/auction'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        auction = response.json['data']
        self.assertNotEqual(auction, self.tender_data)
        self.assertTrue('modified' in auction)
        self.assertTrue('minimalStep' in auction)
        self.assertFalse("procuringEntity" in auction)
        self.assertFalse("bidders" in auction["bids"][0])
        self.assertEqual(auction["bids"][0]['totalValue']['amount'], self.tender_data["bids"][0]['totalValue']['amount'])
        self.assertEqual(auction["bids"][1]['totalValue']['amount'], self.tender_data["bids"][1]['totalValue']['amount'])
        self.assertEqual(parse_date(self.tender_data["tenderPeriod"]['endDate'], get_localzone()), parse_date(auction["tenderPeriod"]['endDate']))

        response = self.app.get('/tenders/{}/auction?opt_jsonp=callback'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/javascript')
        self.assertTrue('callback({"data": {"' in response.body)

        response = self.app.get('/tenders/{}/auction?opt_pretty=1'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertTrue('{\n    "data": {\n        "' in response.body)

    def test_patch_tender(self):
        patch_data = {
            'bids': [
                {
                    "totalValue": {
                        "amount": 409,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": True
                    }
                },
                {
                    "totalValue": {
                        "amount": 419,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": True
                    }
                }
            ]
        }
        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        auction = response.json['data']
        self.assertNotEqual(auction["bids"][0]['totalValue']['amount'], self.tender_data["bids"][0]['totalValue']['amount'])
        self.assertNotEqual(auction["bids"][1]['totalValue']['amount'], self.tender_data["bids"][1]['totalValue']['amount'])
        self.assertEqual(auction["bids"][0]['totalValue']['amount'], patch_data["bids"][0]['totalValue']['amount'])
        self.assertEqual(auction["bids"][1]['totalValue']['amount'], patch_data["bids"][1]['totalValue']['amount'])


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TenderAuctionResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
