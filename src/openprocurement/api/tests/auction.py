# -*- coding: utf-8 -*-
import unittest
from datetime import timedelta

from openprocurement.api.models import get_now
from openprocurement.api.tests.base import BaseTenderWebTest, test_tender_data, test_features_tender_data, test_bids, test_lots


class TenderAuctionResourceTest(BaseTenderWebTest):
    #initial_data = tender_data
    initial_status = 'active.tendering'
    initial_bids = test_bids

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

        response = self.app.post_json('/tenders/some_id/auction', {'data': {}}, status=404)
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
        self.assertEqual(response.json['errors'][0]["description"], "Can't get auction info in current (active.tendering) tender status")

        self.set_status('active.auction')

        response = self.app.get('/tenders/{}/auction'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        auction = response.json['data']
        self.assertNotEqual(auction, self.initial_data)
        self.assertIn('dateModified', auction)
        self.assertIn('minimalStep', auction)
        self.assertNotIn("procuringEntity", auction)
        self.assertNotIn("tenderers", auction["bids"][0])
        self.assertEqual(auction["bids"][0]['value']['amount'], self.initial_bids[0]['value']['amount'])
        self.assertEqual(auction["bids"][1]['value']['amount'], self.initial_bids[1]['value']['amount'])
        #self.assertEqual(self.initial_data["auctionPeriod"]['startDate'], auction["auctionPeriod"]['startDate'])

        response = self.app.get('/tenders/{}/auction?opt_jsonp=callback'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/javascript')
        self.assertIn('callback({"data": {"', response.body)

        response = self.app.get('/tenders/{}/auction?opt_pretty=1'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('{\n    "data": {\n        "', response.body)

        self.set_status('active.qualification')

        response = self.app.get('/tenders/{}/auction'.format(self.tender_id), status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't get auction info in current (active.qualification) tender status")

    def test_post_tender_auction(self):
        self.app.authorization = ('Basic', ('auction', ''))
        response = self.app.post_json('/tenders/{}/auction'.format(self.tender_id), {'data': {}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't report auction results in current (active.tendering) tender status")

        self.set_status('active.auction')

        response = self.app.post_json('/tenders/{}/auction'.format(self.tender_id), {'data': {'bids': [{'invalid_field': 'invalid_value'}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'], [
            {u'description': {u'invalid_field': u'Rogue field'}, u'location': u'body', u'name': u'bids'}
        ])

        patch_data = {
            'bids': [
                {
                    "id": self.initial_bids[1]['id'],
                    "value": {
                        "amount": 409,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": True
                    }
                }
            ]
        }

        response = self.app.post_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=422)
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

        patch_data['bids'][1]['id'] = "some_id"

        response = self.app.post_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], {u'id': [u'Hash value is wrong length.']})

        patch_data['bids'][1]['id'] = "00000000000000000000000000000000"

        response = self.app.post_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Auction bids should be identical to the tender bids")

        patch_data['bids'][1]['id'] = self.initial_bids[0]['id']

        response = self.app.post_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        tender = response.json['data']
        self.assertNotEqual(tender["bids"][0]['value']['amount'], self.initial_bids[0]['value']['amount'])
        self.assertNotEqual(tender["bids"][1]['value']['amount'], self.initial_bids[1]['value']['amount'])
        self.assertEqual(tender["bids"][0]['value']['amount'], patch_data["bids"][1]['value']['amount'])
        self.assertEqual(tender["bids"][1]['value']['amount'], patch_data["bids"][0]['value']['amount'])
        self.assertEqual('active.qualification', tender["status"])
        self.assertIn("tenderers", tender["bids"][0])
        self.assertIn("name", tender["bids"][0]["tenderers"][0])
        # self.assertIn(tender["awards"][0]["id"], response.headers['Location'])
        self.assertEqual(tender["awards"][0]['bid_id'], patch_data["bids"][0]['id'])
        self.assertEqual(tender["awards"][0]['value']['amount'], patch_data["bids"][0]['value']['amount'])
        self.assertEqual(tender["awards"][0]['suppliers'], self.initial_bids[0]['tenderers'])

        response = self.app.post_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't report auction results in current (active.qualification) tender status")

    def test_patch_tender_auction(self):
        self.app.authorization = ('Basic', ('auction', ''))
        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': {}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update auction urls in current (active.tendering) tender status")

        self.set_status('active.auction')

        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': {'bids': [{'invalid_field': 'invalid_value'}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'], [
            {u'description': {u'invalid_field': u'Rogue field'}, u'location': u'body', u'name': u'bids'}
        ])

        patch_data = {
            'auctionUrl': u'http://auction-sandbox.openprocurement.org/tenders/{}'.format(self.tender_id),
            'bids': [
                {
                    "id": self.initial_bids[1]['id'],
                    "participationUrl": u'http://auction-sandbox.openprocurement.org/tenders/{}?key_for_bid={}'.format(self.tender_id, self.initial_bids[1]['id'])
                }
            ]
        }

        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Number of auction results did not match the number of tender bids")

        patch_data['bids'].append({
            "participationUrl": u'http://auction-sandbox.openprocurement.org/tenders/{}?key_for_bid={}'.format(self.tender_id, self.initial_bids[0]['id'])
        })

        patch_data['bids'][1]['id'] = "some_id"

        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], {u'id': [u'Hash value is wrong length.']})

        patch_data['bids'][1]['id'] = "00000000000000000000000000000000"

        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Auction bids should be identical to the tender bids")

        patch_data['bids'][1]['id'] = self.initial_bids[0]['id']

        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        tender = response.json['data']
        self.assertEqual(tender["bids"][0]['participationUrl'], patch_data["bids"][1]['participationUrl'])
        self.assertEqual(tender["bids"][1]['participationUrl'], patch_data["bids"][0]['participationUrl'])

        self.set_status('complete')

        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update auction urls in current (complete) tender status")

    def test_post_tender_auction_document(self):
        self.app.authorization = ('Basic', ('auction', ''))
        response = self.app.post('/tenders/{}/documents'.format(self.tender_id), upload_files=[('file', 'name.doc', 'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add document in current (active.tendering) tender status")

        self.set_status('active.auction')

        response = self.app.post('/tenders/{}/documents'.format(self.tender_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        key = response.json["data"]["url"].split('?')[-1].split('=')[-1]

        patch_data = {
            'bids': [
                {
                    "id": self.initial_bids[1]['id'],
                    "value": {
                        "amount": 409,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": True
                    }
                },
                {
                    'id': self.initial_bids[0]['id'],
                    "value": {
                        "amount": 419,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": True
                    }
                }
            ]
        }

        response = self.app.post_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.put('/tenders/{}/documents/{}'.format(self.tender_id, doc_id), upload_files=[('file', 'name.doc', 'content_with_names')])
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key2 = response.json["data"]["url"].split('?')[-1].split('=')[-1]
        self.assertNotEqual(key, key2)

        self.set_status('complete')
        response = self.app.post('/tenders/{}/documents'.format(self.tender_id), upload_files=[('file', 'name.doc', 'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add document in current (complete) tender status")


class TenderSameValueAuctionResourceTest(BaseTenderWebTest):
    initial_status = 'active.auction'
    initial_bids = [
        {
            "tenderers": [
                test_tender_data["procuringEntity"]
            ],
            "value": {
                "amount": 469,
                "currency": "UAH",
                "valueAddedTaxIncluded": True
            }
        }
        for i in range(3)
    ]

    def test_post_tender_auction_not_changed(self):
        self.app.authorization = ('Basic', ('auction', ''))
        response = self.app.post_json('/tenders/{}/auction'.format(self.tender_id), {'data': {'bids': self.initial_bids}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        tender = response.json['data']
        self.assertEqual('active.qualification', tender["status"])
        self.assertEqual(tender["awards"][0]['bid_id'], self.initial_bids[0]['id'])
        self.assertEqual(tender["awards"][0]['value']['amount'], self.initial_bids[0]['value']['amount'])
        self.assertEqual(tender["awards"][0]['suppliers'], self.initial_bids[0]['tenderers'])

    def test_post_tender_auction_reversed(self):
        self.app.authorization = ('Basic', ('auction', ''))
        now = get_now()
        patch_data = {
            'bids': [
                {
                    "id": b['id'],
                    "date": (now - timedelta(seconds=i)).isoformat(),
                    "value": b['value']
                }
                for i, b in enumerate(self.initial_bids)
            ]
        }

        response = self.app.post_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        tender = response.json['data']
        self.assertEqual('active.qualification', tender["status"])
        self.assertEqual(tender["awards"][0]['bid_id'], self.initial_bids[2]['id'])
        self.assertEqual(tender["awards"][0]['value']['amount'], self.initial_bids[2]['value']['amount'])
        self.assertEqual(tender["awards"][0]['suppliers'], self.initial_bids[2]['tenderers'])


class TenderLotAuctionResourceTest(TenderAuctionResourceTest):
    initial_lots = test_lots

    def test_get_tender_auction(self):
        response = self.app.get('/tenders/{}/auction'.format(self.tender_id), status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't get auction info in current (active.tendering) tender status")

        self.set_status('active.auction')

        response = self.app.get('/tenders/{}/auction'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        auction = response.json['data']
        self.assertNotEqual(auction, self.initial_data)
        self.assertIn('dateModified', auction)
        self.assertIn('minimalStep', auction)
        self.assertIn('lots', auction)
        self.assertNotIn("procuringEntity", auction)
        self.assertNotIn("tenderers", auction["bids"][0])
        self.assertEqual(auction["bids"][0]['lotValues'][0]['value']['amount'], self.initial_bids[0]['lotValues'][0]['value']['amount'])
        self.assertEqual(auction["bids"][1]['lotValues'][0]['value']['amount'], self.initial_bids[1]['lotValues'][0]['value']['amount'])

        self.set_status('active.qualification')

        response = self.app.get('/tenders/{}/auction'.format(self.tender_id), status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't get auction info in current (active.qualification) tender status")

    def test_post_tender_auction(self):
        self.app.authorization = ('Basic', ('auction', ''))
        response = self.app.post_json('/tenders/{}/auction'.format(self.tender_id), {'data': {}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't report auction results in current (active.tendering) tender status")

        self.set_status('active.auction')

        response = self.app.post_json('/tenders/{}/auction'.format(self.tender_id), {'data': {'bids': [{'invalid_field': 'invalid_value'}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'], [
            {u'description': {u'invalid_field': u'Rogue field'}, u'location': u'body', u'name': u'bids'}
        ])

        patch_data = {
            'bids': [
                {
                    "id": self.initial_bids[1]['id'],
                    'lotValues': [
                        {
                            "value": {
                                "amount": 409,
                                "currency": "UAH",
                                "valueAddedTaxIncluded": True
                            }
                        }
                    ]
                }
            ]
        }

        response = self.app.post_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Number of auction results did not match the number of tender bids")

        patch_data['bids'].append({
            'lotValues': [
                {
                    "value": {
                        "amount": 419,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": True
                    }
                }
            ]
        })

        patch_data['bids'][1]['id'] = "some_id"

        response = self.app.post_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], {u'id': [u'Hash value is wrong length.']})

        patch_data['bids'][1]['id'] = "00000000000000000000000000000000"

        response = self.app.post_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Auction bids should be identical to the tender bids")

        patch_data['bids'][1]['id'] = self.initial_bids[0]['id']

        for lot in self.initial_lots:
            response = self.app.post_json('/tenders/{}/auction/{}'.format(self.tender_id, lot['id']), {'data': patch_data})
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            tender = response.json['data']

        self.assertNotEqual(tender["bids"][0]['lotValues'][0]['value']['amount'], self.initial_bids[0]['lotValues'][0]['value']['amount'])
        self.assertNotEqual(tender["bids"][1]['lotValues'][0]['value']['amount'], self.initial_bids[1]['lotValues'][0]['value']['amount'])
        self.assertEqual(tender["bids"][0]['lotValues'][0]['value']['amount'], patch_data["bids"][1]['lotValues'][0]['value']['amount'])
        self.assertEqual(tender["bids"][1]['lotValues'][0]['value']['amount'], patch_data["bids"][0]['lotValues'][0]['value']['amount'])
        self.assertEqual('active.qualification', tender["status"])
        self.assertIn("tenderers", tender["bids"][0])
        self.assertIn("name", tender["bids"][0]["tenderers"][0])
        # self.assertIn(tender["awards"][0]["id"], response.headers['Location'])
        self.assertEqual(tender["awards"][0]['bid_id'], patch_data["bids"][0]['id'])
        self.assertEqual(tender["awards"][0]['value']['amount'], patch_data["bids"][0]['lotValues'][0]['value']['amount'])
        self.assertEqual(tender["awards"][0]['suppliers'], self.initial_bids[0]['tenderers'])

        response = self.app.post_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't report auction results in current (active.qualification) tender status")

    def test_patch_tender_auction(self):
        self.app.authorization = ('Basic', ('auction', ''))
        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': {}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update auction urls in current (active.tendering) tender status")

        self.set_status('active.auction')

        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': {'bids': [{'invalid_field': 'invalid_value'}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'], [
            {u'description': {u'invalid_field': u'Rogue field'}, u'location': u'body', u'name': u'bids'}
        ])

        patch_data = {
            'auctionUrl': u'http://auction-sandbox.openprocurement.org/tenders/{}'.format(self.tender_id),
            'bids': [
                {
                    "id": self.initial_bids[1]['id'],
                    "participationUrl": u'http://auction-sandbox.openprocurement.org/tenders/{}?key_for_bid={}'.format(self.tender_id, self.initial_bids[1]['id'])
                }
            ]
        }

        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'], [
            {u'description': [{u'participationUrl': [u'url should be posted for each lot of bid']}], u'location': u'body', u'name': u'bids'}
        ])

        del patch_data['bids'][0]["participationUrl"]
        patch_data['bids'][0]['lotValues'] = [
            {
                "participationUrl": u'http://auction-sandbox.openprocurement.org/tenders/{}?key_for_bid={}'.format(self.tender_id, self.initial_bids[0]['id'])
            }
        ]

        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'], [
            {u'description': ["url should be posted for each lot"], u'location': u'body', u'name': u'auctionUrl'}
        ])

        patch_data['lots'] = [
            {
                "auctionUrl": patch_data.pop('auctionUrl')
            }
        ]

        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Number of auction results did not match the number of tender bids")

        patch_data['bids'].append({
            'lotValues': [
                {
                    "participationUrl": u'http://auction-sandbox.openprocurement.org/tenders/{}?key_for_bid={}'.format(self.tender_id, self.initial_bids[0]['id'])
                }
            ]
        })

        patch_data['bids'][1]['id'] = "some_id"

        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], {u'id': [u'Hash value is wrong length.']})

        patch_data['bids'][1]['id'] = "00000000000000000000000000000000"

        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Auction bids should be identical to the tender bids")

        patch_data['bids'][1]['id'] = self.initial_bids[0]['id']

        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIsNone(response.json)

        for lot in self.initial_lots:
            response = self.app.patch_json('/tenders/{}/auction/{}'.format(self.tender_id, lot['id']), {'data': patch_data})
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            tender = response.json['data']

        self.assertEqual(tender["bids"][0]['lotValues'][0]['participationUrl'], patch_data["bids"][1]['lotValues'][0]['participationUrl'])
        self.assertEqual(tender["bids"][1]['lotValues'][0]['participationUrl'], patch_data["bids"][0]['lotValues'][0]['participationUrl'])
        self.assertEqual(tender["lots"][0]['auctionUrl'], patch_data["lots"][0]['auctionUrl'])

        self.set_status('complete')

        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update auction urls in current (complete) tender status")

    def test_post_tender_auction_document(self):
        self.app.authorization = ('Basic', ('auction', ''))
        response = self.app.post('/tenders/{}/documents'.format(self.tender_id), upload_files=[('file', 'name.doc', 'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add document in current (active.tendering) tender status")

        self.set_status('active.auction')

        response = self.app.post('/tenders/{}/documents'.format(self.tender_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        key = response.json["data"]["url"].split('?')[-1].split('=')[-1]

        response = self.app.patch_json('/tenders/{}/documents/{}'.format(self.tender_id, doc_id), {'data': {"documentOf": "lot", 'relatedItem': self.initial_lots[0]['id']}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json["data"]["documentOf"], "lot")
        self.assertEqual(response.json["data"]["relatedItem"], self.initial_lots[0]['id'])

        patch_data = {
            'bids': [
                {
                    "id": self.initial_bids[1]['id'],
                    'lotValues': [
                        {
                            "value": {
                                "amount": 409,
                                "currency": "UAH",
                                "valueAddedTaxIncluded": True
                            }
                        }
                    ]
                },
                {
                    'id': self.initial_bids[0]['id'],
                    'lotValues': [
                        {
                            "value": {
                                "amount": 419,
                                "currency": "UAH",
                                "valueAddedTaxIncluded": True
                            }
                        }
                    ]
                }
            ]
        }

        response = self.app.post_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.put('/tenders/{}/documents/{}'.format(self.tender_id, doc_id), upload_files=[('file', 'name.doc', 'content_with_names')])
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key2 = response.json["data"]["url"].split('?')[-1].split('=')[-1]
        self.assertNotEqual(key, key2)

        self.set_status('complete')
        response = self.app.post('/tenders/{}/documents'.format(self.tender_id), upload_files=[('file', 'name.doc', 'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add document in current (complete) tender status")


class TenderMultipleLotAuctionResourceTest(TenderAuctionResourceTest):
    initial_lots = 2 * test_lots

    def test_get_tender_auction(self):
        response = self.app.get('/tenders/{}/auction'.format(self.tender_id), status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't get auction info in current (active.tendering) tender status")

        self.set_status('active.auction')

        response = self.app.get('/tenders/{}/auction'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        auction = response.json['data']
        self.assertNotEqual(auction, self.initial_data)
        self.assertIn('dateModified', auction)
        self.assertIn('minimalStep', auction)
        self.assertIn('lots', auction)
        self.assertNotIn("procuringEntity", auction)
        self.assertNotIn("tenderers", auction["bids"][0])
        self.assertEqual(auction["bids"][0]['lotValues'][0]['value']['amount'], self.initial_bids[0]['lotValues'][0]['value']['amount'])
        self.assertEqual(auction["bids"][1]['lotValues'][0]['value']['amount'], self.initial_bids[1]['lotValues'][0]['value']['amount'])
        self.assertEqual(auction["bids"][0]['lotValues'][1]['value']['amount'], self.initial_bids[0]['lotValues'][1]['value']['amount'])
        self.assertEqual(auction["bids"][1]['lotValues'][1]['value']['amount'], self.initial_bids[1]['lotValues'][1]['value']['amount'])

        self.set_status('active.qualification')

        response = self.app.get('/tenders/{}/auction'.format(self.tender_id), status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't get auction info in current (active.qualification) tender status")

    def test_post_tender_auction(self):
        self.app.authorization = ('Basic', ('auction', ''))
        response = self.app.post_json('/tenders/{}/auction'.format(self.tender_id), {'data': {}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't report auction results in current (active.tendering) tender status")

        self.set_status('active.auction')

        response = self.app.post_json('/tenders/{}/auction'.format(self.tender_id), {'data': {'bids': [{'invalid_field': 'invalid_value'}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'], [
            {u'description': {u'invalid_field': u'Rogue field'}, u'location': u'body', u'name': u'bids'}
        ])

        patch_data = {
            'bids': [
                {
                    "id": self.initial_bids[1]['id'],
                    'lotValues': [
                        {
                            "value": {
                                "amount": 409,
                                "currency": "UAH",
                                "valueAddedTaxIncluded": True
                            }
                        }
                    ]
                }
            ]
        }

        response = self.app.post_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Number of auction results did not match the number of tender bids")

        patch_data['bids'].append({
            'lotValues': [
                {
                    "value": {
                        "amount": 419,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": True
                    }
                }
            ]
        })

        patch_data['bids'][1]['id'] = "some_id"

        response = self.app.post_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], {u'id': [u'Hash value is wrong length.']})

        patch_data['bids'][1]['id'] = "00000000000000000000000000000000"

        response = self.app.post_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Auction bids should be identical to the tender bids")

        patch_data['bids'][1]['id'] = self.initial_bids[0]['id']

        response = self.app.post_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], [{"lotValues": ["Number of lots of auction results did not match the number of tender lots"]}])

        for bid in patch_data['bids']:
            bid['lotValues'] = [bid['lotValues'][0].copy() for i in self.initial_lots]

        patch_data['bids'][0]['lotValues'][1]['relatedLot'] = self.initial_bids[0]['lotValues'][0]['relatedLot']

        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], [{u'lotValues': [{u'relatedLot': [u'relatedLot should be one of lots of bid']}]}])

        patch_data['bids'][0]['lotValues'][1]['relatedLot'] = self.initial_bids[0]['lotValues'][1]['relatedLot']

        for lot in self.initial_lots:
            response = self.app.post_json('/tenders/{}/auction/{}'.format(self.tender_id, lot['id']), {'data': patch_data})
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            tender = response.json['data']

        self.assertNotEqual(tender["bids"][0]['lotValues'][0]['value']['amount'], self.initial_bids[0]['lotValues'][0]['value']['amount'])
        self.assertNotEqual(tender["bids"][1]['lotValues'][0]['value']['amount'], self.initial_bids[1]['lotValues'][0]['value']['amount'])
        self.assertEqual(tender["bids"][0]['lotValues'][0]['value']['amount'], patch_data["bids"][1]['lotValues'][0]['value']['amount'])
        self.assertEqual(tender["bids"][1]['lotValues'][0]['value']['amount'], patch_data["bids"][0]['lotValues'][0]['value']['amount'])
        self.assertEqual('active.qualification', tender["status"])
        self.assertIn("tenderers", tender["bids"][0])
        self.assertIn("name", tender["bids"][0]["tenderers"][0])
        # self.assertIn(tender["awards"][0]["id"], response.headers['Location'])
        self.assertEqual(tender["awards"][0]['bid_id'], patch_data["bids"][0]['id'])
        self.assertEqual(tender["awards"][0]['value']['amount'], patch_data["bids"][0]['lotValues'][0]['value']['amount'])
        self.assertEqual(tender["awards"][0]['suppliers'], self.initial_bids[0]['tenderers'])

        response = self.app.post_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't report auction results in current (active.qualification) tender status")

    def test_patch_tender_auction(self):
        self.app.authorization = ('Basic', ('auction', ''))
        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': {}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update auction urls in current (active.tendering) tender status")

        self.set_status('active.auction')

        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': {'bids': [{'invalid_field': 'invalid_value'}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'], [
            {u'description': {u'invalid_field': u'Rogue field'}, u'location': u'body', u'name': u'bids'}
        ])

        patch_data = {
            'auctionUrl': u'http://auction-sandbox.openprocurement.org/tenders/{}'.format(self.tender_id),
            'bids': [
                {
                    "id": self.initial_bids[1]['id'],
                    "participationUrl": u'http://auction-sandbox.openprocurement.org/tenders/{}?key_for_bid={}'.format(self.tender_id, self.initial_bids[1]['id'])
                }
            ]
        }

        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'], [
            {u'description': [{u'participationUrl': [u'url should be posted for each lot of bid']}], u'location': u'body', u'name': u'bids'}
        ])

        del patch_data['bids'][0]["participationUrl"]
        patch_data['bids'][0]['lotValues'] = [
            {
                "participationUrl": u'http://auction-sandbox.openprocurement.org/tenders/{}?key_for_bid={}'.format(self.tender_id, self.initial_bids[0]['id'])
            }
        ]

        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'], [
            {u'description': ["url should be posted for each lot"], u'location': u'body', u'name': u'auctionUrl'}
        ])

        patch_data['lots'] = [
            {
                "auctionUrl": patch_data.pop('auctionUrl')
            }
        ]

        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Number of auction results did not match the number of tender bids")

        patch_data['bids'].append({
            'lotValues': [
                {
                    "participationUrl": u'http://auction-sandbox.openprocurement.org/tenders/{}?key_for_bid={}'.format(self.tender_id, self.initial_bids[0]['id'])
                }
            ]
        })

        patch_data['bids'][1]['id'] = "some_id"

        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], {u'id': [u'Hash value is wrong length.']})

        patch_data['bids'][1]['id'] = "00000000000000000000000000000000"

        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Auction bids should be identical to the tender bids")

        patch_data['bids'][1]['id'] = self.initial_bids[0]['id']

        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], u'Number of lots did not match the number of tender lots')

        patch_data['lots'] = [patch_data['lots'][0].copy() for i in self.initial_lots]
        patch_data['lots'][1]['id'] = self.initial_lots[0]['id']

        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], u'Auction lots should be identical to the tender lots')

        patch_data['lots'][1]['id'] = self.initial_lots[1]['id']

        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], [{"lotValues": ["Number of lots of auction results did not match the number of tender lots"]}])

        for bid in patch_data['bids']:
            bid['lotValues'] = [bid['lotValues'][0].copy() for i in self.initial_lots]

        patch_data['bids'][0]['lotValues'][1]['relatedLot'] = self.initial_bids[0]['lotValues'][0]['relatedLot']

        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], [{u'lotValues': [{u'relatedLot': [u'relatedLot should be one of lots of bid']}]}])

        patch_data['bids'][0]['lotValues'][1]['relatedLot'] = self.initial_bids[0]['lotValues'][1]['relatedLot']

        response = self.app.patch_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIsNone(response.json)

        for lot in self.initial_lots:
            response = self.app.patch_json('/tenders/{}/auction/{}'.format(self.tender_id, lot['id']), {'data': patch_data})
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            tender = response.json['data']

        self.assertEqual(tender["bids"][0]['lotValues'][0]['participationUrl'], patch_data["bids"][1]['lotValues'][0]['participationUrl'])
        self.assertEqual(tender["bids"][1]['lotValues'][0]['participationUrl'], patch_data["bids"][0]['lotValues'][0]['participationUrl'])
        self.assertEqual(tender["lots"][0]['auctionUrl'], patch_data["lots"][0]['auctionUrl'])

        self.app.authorization = ('Basic', ('token', ''))
        response = self.app.post_json('/tenders/{}/cancellations'.format(self.tender_id), {'data': {
            'reason': 'cancellation reason',
            'status': 'active',
            "cancellationOf": "lot",
            "relatedLot": self.initial_lots[0]['id']
        }})
        self.assertEqual(response.status, '201 Created')

        self.app.authorization = ('Basic', ('auction', ''))
        response = self.app.patch_json('/tenders/{}/auction/{}'.format(self.tender_id, self.initial_lots[0]['id']), {'data': patch_data}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can update auction urls only in active lot status")

    def test_post_tender_auction_document(self):
        self.app.authorization = ('Basic', ('auction', ''))
        response = self.app.post('/tenders/{}/documents'.format(self.tender_id), upload_files=[('file', 'name.doc', 'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add document in current (active.tendering) tender status")

        self.set_status('active.auction')

        response = self.app.post('/tenders/{}/documents'.format(self.tender_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        key = response.json["data"]["url"].split('?')[-1].split('=')[-1]

        response = self.app.patch_json('/tenders/{}/documents/{}'.format(self.tender_id, doc_id), {'data': {"documentOf": "lot", 'relatedItem': self.initial_lots[0]['id']}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json["data"]["documentOf"], "lot")
        self.assertEqual(response.json["data"]["relatedItem"], self.initial_lots[0]['id'])

        patch_data = {
            'bids': [
                {
                    "id": self.initial_bids[1]['id'],
                    'lotValues': [
                        {
                            "value": {
                                "amount": 409,
                                "currency": "UAH",
                                "valueAddedTaxIncluded": True
                            }
                        }
                        for i in self.initial_lots
                    ]
                },
                {
                    'id': self.initial_bids[0]['id'],
                    'lotValues': [
                        {
                            "value": {
                                "amount": 419,
                                "currency": "UAH",
                                "valueAddedTaxIncluded": True
                            }
                        }
                        for i in self.initial_lots
                    ]
                }
            ]
        }

        response = self.app.post_json('/tenders/{}/auction'.format(self.tender_id), {'data': patch_data})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.put('/tenders/{}/documents/{}'.format(self.tender_id, doc_id), upload_files=[('file', 'name.doc', 'content_with_names')])
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key2 = response.json["data"]["url"].split('?')[-1].split('=')[-1]
        self.assertNotEqual(key, key2)

        self.set_status('complete')
        response = self.app.post('/tenders/{}/documents'.format(self.tender_id), upload_files=[('file', 'name.doc', 'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add document in current (complete) tender status")


class TenderFeaturesAuctionResourceTest(BaseTenderWebTest):
    initial_data = test_features_tender_data
    initial_status = 'active.auction'
    initial_bids = [
        {
            "parameters": [
                {
                    "code": i["code"],
                    "value": 0.1,
                }
                for i in test_features_tender_data['features']
            ],
            "tenderers": [
                test_tender_data["procuringEntity"]
            ],
            "value": {
                "amount": 469,
                "currency": "UAH",
                "valueAddedTaxIncluded": True
            }
        },
        {
            "parameters": [
                {
                    "code": i["code"],
                    "value": 0.15,
                }
                for i in test_features_tender_data['features']
            ],
            "tenderers": [
                test_tender_data["procuringEntity"]
            ],
            "value": {
                "amount": 479,
                "currency": "UAH",
                "valueAddedTaxIncluded": True
            }
        }
    ]

    def test_get_tender_auction(self):
        response = self.app.get('/tenders/{}/auction'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        auction = response.json['data']
        self.assertNotEqual(auction, self.initial_data)
        self.assertIn('dateModified', auction)
        self.assertIn('minimalStep', auction)
        self.assertNotIn("procuringEntity", auction)
        self.assertNotIn("tenderers", auction["bids"][0])
        self.assertEqual(auction["bids"][0]['value']['amount'], self.initial_bids[0]['value']['amount'])
        self.assertEqual(auction["bids"][1]['value']['amount'], self.initial_bids[1]['value']['amount'])
        self.assertIn('features', auction)
        self.assertIn('parameters', auction["bids"][0])


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TenderAuctionResourceTest))
    suite.addTest(unittest.makeSuite(TenderSameValueAuctionResourceTest))
    suite.addTest(unittest.makeSuite(TenderFeaturesAuctionResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
