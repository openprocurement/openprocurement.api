# -*- coding: utf-8 -*-
import unittest
import webtest
import os

from openprocurement.api import VERSION
from pyramid.security import (
    Everyone,
    Allow,
    ALL_PERMISSIONS,
)


test_tender_data = {
    "procuringEntity": {
        "name": u"Державне управління справами",
        "identifier": {
            "scheme": u"https://ns.openprocurement.org/ua/edrpou",
            "id": u"00037256",
            "uri": u"http://www.dus.gov.ua/"
        },
        "address": {
            "countryName": u"Україна",
            "postalCode": u"01220",
            "region": u"м. Київ",
            "locality": u"м. Київ",
            "streetAddress": u"вул. Банкова, 11, корпус 1"
        },
    },
    "value": {
        "amount": 500,
        "currency": u"UAH"
    },
    "minimalStep": {
        "amount": 35,
        "currency": u"UAH"
    },
    "items": [
        {
            "description": u"футляри до державних нагород",
            "classification": {
                "scheme": u"CPV",
                "id": u"44617100-9",
                "description": u"Cartons"
            },
            "additionalClassifications": [
                {
                    "scheme": u"ДКПП",
                    "id": u"17.21.1",
                    "description": u"папір і картон гофровані, паперова й картонна тара"
                }
            ],
            "unit": {
                "name": u"item",
                "code": u"44617100-9"
            },
            "quantity": 5
        }
    ],
    "enquiryPeriod": {
        "endDate": u"2014-10-31T00:00:00"
    },
    "tenderPeriod": {
        "endDate": u"2014-11-06T10:00:00"
    },
    "awardPeriod": {
        "endDate": u"2014-11-13T00:00:00"
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
        self.app.authorization = ('Basic', ('token', ''))
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
