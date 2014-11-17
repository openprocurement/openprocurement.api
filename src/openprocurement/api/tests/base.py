# -*- coding: utf-8 -*-
import unittest
import webtest
import os

from openprocurement.api import VERSION


test_tender_data = {
    "procuringEntity": {
        "name": "Державне управління справами",
        "identifier": {
            "scheme": "https://ns.openprocurement.org/ua/edrpou",
            "id": "00037256",
            "uri": "http://www.dus.gov.ua/"
        },
        "address": {
            "countryName": "Україна",
            "postalCode": "01220",
            "region": "м. Київ",
            "locality": "м. Київ",
            "streetAddress": "вул. Банкова, 11, корпус 1"
        },
    },
    "value": {
        "amount": 500,
        "currency": "UAH"
    },
    "minimalStep": {
        "amount": 35,
        "currency": "UAH"
    },
    "items": [
        {
            "description": "футляри до державних нагород",
            "classification": {
                "scheme": "CPV",
                "id": "44617100-9",
                "description": "Cartons"
            },
            "additionalClassifications": [
                {
                    "scheme": "ДКПП",
                    "id": "17.21.1",
                    "description": "папір і картон гофровані, паперова й картонна тара"
                }
            ],
            "unit": {
                "name": "item"
            },
            "quantity": 5
        }
    ],
    "enquiryPeriod": {
        "endDate": "2014-10-31T00:00:00"
    },
    "tenderPeriod": {
        "endDate": "2014-11-06T10:00:00"
    },
    "awardPeriod": {
        "endDate": "2014-11-13T00:00:00"
    }
}


class PrefixedRequestClass(webtest.app.TestRequest):

    @classmethod
    def blank(cls, path, *args, **kwargs):
        path = '/api/%s%s' % (VERSION, path)
        return webtest.app.TestRequest.blank(path, *args, **kwargs)


class BaseWebTest(unittest.TestCase):

    """Base Web Test to test openprocurement.api.

    It setups the database before each test and delete it after.
    """

    def setUp(self):
        self.app = webtest.TestApp(
            "config:tests.ini", relative_to=os.path.dirname(__file__))
        self.app.RequestClass = PrefixedRequestClass
        self.couchdb_server = self.app.app.registry.couchdb_server
        self.db = self.app.app.registry.db

    def tearDown(self):
        del self.couchdb_server[self.db.name]


class BaseTenderWebTest(BaseWebTest):
    initial_data = {}

    def set_status(self, status):
        response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {'status': status}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')

    def setUp(self):
        super(BaseTenderWebTest, self).setUp()
        # Create tender
        response = self.app.post_json('/tenders', {'data': self.initial_data})
        tender = response.json['data']
        self.tender_id = tender['id']

    def tearDown(self):
        del self.db[self.tender_id]
        super(BaseTenderWebTest, self).tearDown()
