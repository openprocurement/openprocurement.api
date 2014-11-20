# -*- coding: utf-8 -*-
import unittest

from openprocurement.api.tests.base import test_tender_data, BaseTenderWebTest
from iso8601 import parse_date
from tzlocal import get_localzone


tender_data = test_tender_data.copy()
tender_data['auctionPeriod'] = test_tender_data["tenderPeriod"]
tender_data['bids'] = [
    {
        "id": "4879d3f8ee2443169b5fbbc9f89fa606",
        "status": "registration",
        "date": "2014-10-28T11:44:17.946",
        "bidders": [
            test_tender_data["procuringEntity"]
        ],
        "value": {
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
        "value": {
            "amount": 479,
            "currency": "UAH",
            "valueAddedTaxIncluded": True
        }
    }
]


class TenderAuctionResourceTest(BaseTenderWebTest):
    initial_data = tender_data

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
        response = self.app.get('/tenders/{}/auction'.format(self.tender_id), status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't get auction info in current tender status")

        self.set_status('auction')

        response = self.app.get('/tenders/{}/auction'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        auction = response.json['data']
        self.assertNotEqual(auction, self.initial_data)
        self.assertTrue('dateModified' in auction)
        self.assertTrue('minimalStep' in auction)
        self.assertFalse("procuringEntity" in auction)
        self.assertFalse("bidders" in auction["bids"][0])
        self.assertEqual(auction["bids"][0]['value']['amount'], self.initial_data["bids"][0]['value']['amount'])
        self.assertEqual(auction["bids"][1]['value']['amount'], self.initial_data["bids"][1]['value']['amount'])
        self.assertEqual(parse_date(self.initial_data["auctionPeriod"]['endDate'], get_localzone()), parse_date(auction["auctionPeriod"]['endDate']))

        response = self.app.get('/tenders/{}/auction?opt_jsonp=callback'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/javascript')
        self.assertTrue('callback({"data": {"' in response.body)

        response = self.app.get('/tenders/{}/auction?opt_pretty=1'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertTrue('{\n    "data": {\n        "' in response.body)

        self.set_status('qualification')

        response = self.app.get('/tenders/{}/auction'.format(self.tender_id), status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't get auction info in current tender status")

    def test_post_tender_auction(self):
        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': {}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't report auction results in current tender status")

        self.set_status('auction')

        patch_data = {
            'bids': [
                {
                    "id": "4879d3f8ee2443169b5fbbc9f89fa607",
                    "value": {
                        "amount": 409,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": True
                    }
                }
            ]
        }

        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Number of auction results did not match the number of tender bids")

        patch_data['bids'].append({
            "value": {
                "amount": 419,
                "currency": "UAH",
                "valueAddedTaxIncluded": True
            }
        })

        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Results of auction bids should contains id of bid")

        patch_data['bids'][1]['id'] = "some_id"

        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Auction bids should be identical to the tender bids")

        patch_data['bids'][1]['id'] = "4879d3f8ee2443169b5fbbc9f89fa606"

        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        auction = response.json['data']
        self.assertNotEqual(auction["bids"][0]['value']['amount'], self.initial_data["bids"][0]['value']['amount'])
        self.assertNotEqual(auction["bids"][1]['value']['amount'], self.initial_data["bids"][1]['value']['amount'])
        self.assertEqual(auction["bids"][0]['value']['amount'], patch_data["bids"][1]['value']['amount'])
        self.assertEqual(auction["bids"][1]['value']['amount'], patch_data["bids"][0]['value']['amount'])

        self.set_status('qualification')

        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't report auction results in current tender status")


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TenderAuctionResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
