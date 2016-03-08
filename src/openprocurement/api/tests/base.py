# -*- coding: utf-8 -*-
import unittest
import webtest
import os
from copy import deepcopy
from datetime import datetime, timedelta
from uuid import uuid4

from openprocurement.api.utils import VERSION, apply_data_patch


now = datetime.now()
test_tender_data = {
    "title": u"футляри до державних нагород",
    "procuringEntity": {
        "name": u"Державне управління справами",
        "identifier": {
            "scheme": u"UA-EDR",
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
        "contactPoint": {
            "name": u"Державне управління справами",
            "telephone": u"0440000000"
        }
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
        "endDate": (now + timedelta(days=7)).isoformat()
    },
    "tenderPeriod": {
        "endDate": (now + timedelta(days=14)).isoformat()
    },
    "procurementMethodType": "belowThreshold",
}

test_features_tender_data = test_tender_data.copy()
test_features_item = test_features_tender_data['items'][0].copy()
test_features_item['id'] = "1"
test_features_tender_data['items'] = [test_features_item]
test_features_tender_data["features"] = [
    {
        "code": "OCDS-123454-AIR-INTAKE",
        "featureOf": "item",
        "relatedItem": "1",
        "title": u"Потужність всмоктування",
        "title_en": "Air Intake",
        "description": u"Ефективна потужність всмоктування пилососа, в ватах (аероватах)",
        "enum": [
            {
                "value": 0.1,
                "title": u"До 1000 Вт"
            },
            {
                "value": 0.15,
                "title": u"Більше 1000 Вт"
            }
        ]
    },
    {
        "code": "OCDS-123454-YEARS",
        "featureOf": "tenderer",
        "title": u"Років на ринку",
        "title_en": "Years trading",
        "description": u"Кількість років, які організація учасник працює на ринку",
        "enum": [
            {
                "value": 0.05,
                "title": u"До 3 років"
            },
            {
                "value": 0.1,
                "title": u"Більше 3 років, менше 5 років"
            },
            {
                "value": 0.15,
                "title": u"Більше 5 років"
            }
        ]
    }
]
test_bids = [
    {
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
test_lots = [
    {
        'title': 'lot title',
        'description': 'lot description',
        'value': test_tender_data['value'],
        'minimalStep': test_tender_data['minimalStep'],
    }
]
test_features = [
    {
        "code": "code_item",
        "featureOf": "item",
        "relatedItem": "1",
        "title": u"item feature",
        "enum": [
            {
                "value": 0.01,
                "title": u"good"
            },
            {
                "value": 0.02,
                "title": u"best"
            }
        ]
    },
    {
        "code": "code_tenderer",
        "featureOf": "tenderer",
        "title": u"tenderer feature",
        "enum": [
            {
                "value": 0.01,
                "title": u"good"
            },
            {
                "value": 0.02,
                "title": u"best"
            }
        ]
    }
]


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
        #self.app.authorization = ('Basic', ('broker', ''))
        self.couchdb_server = self.app.app.application.registry.couchdb_server
        self.db = self.app.app.application.registry.db

    def tearDown(self):
        del self.couchdb_server[self.db.name]


class BaseTenderWebTest(BaseWebTest):
    initial_data = test_tender_data
    initial_status = None
    initial_bids = None
    initial_lots = None

    def set_status(self, status, extra=None):
        data = {'status': status}
        if status == 'active.enquiries':
            data.update({
                "enquiryPeriod": {
                    "startDate": (now).isoformat(),
                    "endDate": (now + timedelta(days=7)).isoformat()
                },
                "tenderPeriod": {
                    "startDate": (now + timedelta(days=7)).isoformat(),
                    "endDate": (now + timedelta(days=14)).isoformat()
                }
            })
        elif status == 'active.tendering':
            data.update({
                "enquiryPeriod": {
                    "startDate": (now - timedelta(days=10)).isoformat(),
                    "endDate": (now).isoformat()
                },
                "tenderPeriod": {
                    "startDate": (now).isoformat(),
                    "endDate": (now + timedelta(days=7)).isoformat()
                }
            })
        elif status == 'active.auction':
            data.update({
                "enquiryPeriod": {
                    "startDate": (now - timedelta(days=14)).isoformat(),
                    "endDate": (now - timedelta(days=7)).isoformat()
                },
                "tenderPeriod": {
                    "startDate": (now - timedelta(days=7)).isoformat(),
                    "endDate": (now).isoformat()
                },
                "auctionPeriod": {
                    "startDate": (now).isoformat()
                }
            })
            if self.initial_lots:
                data.update({
                    'lots': [
                        {
                            "auctionPeriod": {
                                "startDate": (now).isoformat()
                            }
                        }
                        for i in self.initial_lots
                    ]
                })
        elif status == 'active.qualification':
            data.update({
                "enquiryPeriod": {
                    "startDate": (now - timedelta(days=15)).isoformat(),
                    "endDate": (now - timedelta(days=8)).isoformat()
                },
                "tenderPeriod": {
                    "startDate": (now - timedelta(days=8)).isoformat(),
                    "endDate": (now - timedelta(days=1)).isoformat()
                },
                "auctionPeriod": {
                    "startDate": (now - timedelta(days=1)).isoformat(),
                    "endDate": (now).isoformat()
                },
                "awardPeriod": {
                    "startDate": (now).isoformat()
                }
            })
            if self.initial_lots:
                data.update({
                    'lots': [
                        {
                            "auctionPeriod": {
                                "startDate": (now - timedelta(days=1)).isoformat(),
                                "endDate": (now).isoformat()
                            }
                        }
                        for i in self.initial_lots
                    ]
                })
        elif status == 'active.awarded':
            data.update({
                "enquiryPeriod": {
                    "startDate": (now - timedelta(days=15)).isoformat(),
                    "endDate": (now - timedelta(days=8)).isoformat()
                },
                "tenderPeriod": {
                    "startDate": (now - timedelta(days=8)).isoformat(),
                    "endDate": (now - timedelta(days=1)).isoformat()
                },
                "auctionPeriod": {
                    "startDate": (now - timedelta(days=1)).isoformat(),
                    "endDate": (now).isoformat()
                },
                "awardPeriod": {
                    "startDate": (now).isoformat(),
                    "endDate": (now).isoformat()
                }
            })
            if self.initial_lots:
                data.update({
                    'lots': [
                        {
                            "auctionPeriod": {
                                "startDate": (now - timedelta(days=1)).isoformat(),
                                "endDate": (now).isoformat()
                            }
                        }
                        for i in self.initial_lots
                    ]
                })
        elif status == 'complete':
            data.update({
                "enquiryPeriod": {
                    "startDate": (now - timedelta(days=25)).isoformat(),
                    "endDate": (now - timedelta(days=18)).isoformat()
                },
                "tenderPeriod": {
                    "startDate": (now - timedelta(days=18)).isoformat(),
                    "endDate": (now - timedelta(days=11)).isoformat()
                },
                "auctionPeriod": {
                    "startDate": (now - timedelta(days=11)).isoformat(),
                    "endDate": (now - timedelta(days=10)).isoformat()
                },
                "awardPeriod": {
                    "startDate": (now - timedelta(days=10)).isoformat(),
                    "endDate": (now - timedelta(days=10)).isoformat()
                }
            })
            if self.initial_lots:
                data.update({
                    'lots': [
                        {
                            "auctionPeriod": {
                                "startDate": (now - timedelta(days=11)).isoformat(),
                                "endDate": (now - timedelta(days=10)).isoformat()
                            }
                        }
                        for i in self.initial_lots
                    ]
                })
        if extra:
            data.update(extra)

        tender = self.db.get(self.tender_id)
        tender.update(apply_data_patch(tender, data))
        self.db.save(tender)

        authorization = self.app.authorization
        self.app.authorization = ('Basic', ('chronograph', ''))
        #response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {'id': self.tender_id}})
        response = self.app.get('/tenders/{}'.format(self.tender_id))
        self.app.authorization = authorization
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        return response

    def setUp(self):
        super(BaseTenderWebTest, self).setUp()
        self.create_tender()

    def create_tender(self):
        data = deepcopy(self.initial_data)
        if self.initial_lots:
            lots = []
            for i in self.initial_lots:
                lot = deepcopy(i)
                lot['id'] = uuid4().hex
                lots.append(lot)
            data['lots'] = self.initial_lots = lots
            for i, item in enumerate(data['items']):
                item['relatedLot'] = lots[i % len(lots)]['id']
        response = self.app.post_json('/tenders', {'data': data})
        tender = response.json['data']
        self.tender_token = response.json['access']['token']
        self.tender_id = tender['id']
        status = tender['status']
        if self.initial_bids:
            self.initial_bids_tokens = {}
            response = self.set_status('active.tendering')
            status = response.json['data']['status']
            bids = []
            for i in self.initial_bids:
                if self.initial_lots:
                    i = i.copy()
                    value = i.pop('value')
                    i['lotValues'] = [
                        {
                            'value': value,
                            'relatedLot': l['id'],
                        }
                        for l in self.initial_lots
                    ]
                response = self.app.post_json('/tenders/{}/bids'.format(self.tender_id), {'data': i})
                self.assertEqual(response.status, '201 Created')
                bids.append(response.json['data'])
                self.initial_bids_tokens[response.json['data']['id']] = response.json['access']['token']
            self.initial_bids = bids
        if self.initial_status != status:
            self.set_status(self.initial_status)

    def tearDown(self):
        del self.db[self.tender_id]
        super(BaseTenderWebTest, self).tearDown()
