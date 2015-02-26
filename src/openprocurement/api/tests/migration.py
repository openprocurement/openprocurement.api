# -*- coding: utf-8 -*-
import unittest

from openprocurement.api.migration import migrate_data, get_db_schema_version, set_db_schema_version, SCHEMA_VERSION
from openprocurement.api.tests.base import BaseWebTest, test_tender_data
from email.header import Header


class MigrateTest(BaseWebTest):

    def test_migrate(self):
        self.assertEqual(get_db_schema_version(self.db), SCHEMA_VERSION)
        migrate_data(self.db, 1)
        self.assertEqual(get_db_schema_version(self.db), SCHEMA_VERSION)

    def test_migrate_from0to1(self):
        set_db_schema_version(self.db, 0)
        data = {'doc_type': 'Tender',
                'modifiedAt': '2014-10-15T00:00:00.000000'}
        _id, _rev = self.db.save(data)
        item = self.db.get(_id)
        migrate_data(self.db, 1)
        migrated_item = self.db.get(_id)
        self.assertFalse('modified' in item)
        self.assertTrue('modifiedAt' in item)
        self.assertTrue('modified' in migrated_item)
        self.assertFalse('modifiedAt' in migrated_item)
        self.assertEqual(item['modifiedAt'], migrated_item['modified'])

    def test_migrate_from1to2(self):
        set_db_schema_version(self.db, 1)
        data = {
            "procuringEntity": {
                "address": {
                    "country-name": "Україна",
                    "postal-code": "01220",
                    "street-address": "вул. Банкова, 11, корпус 1"
                },
            },
            'doc_type': 'Tender',
            'bidders': [{
                "address": {
                    "country-name": "Україна",
                    "postal-code": "01220",
                    "street-address": "вул. Банкова, 11, корпус 1"
                },
            }]
        }
        _id, _rev = self.db.save(data)
        item = self.db.get(_id)
        migrate_data(self.db, 2)
        migrated_item = self.db.get(_id)
        self.assertTrue('country-name' in item["procuringEntity"]["address"])
        self.assertFalse('countryName' in item["procuringEntity"]["address"])
        self.assertTrue('country-name' in item["bidders"][0]["address"])
        self.assertFalse('countryName' in item["bidders"][0]["address"])
        self.assertFalse(
            'country-name' in migrated_item["procuringEntity"]["address"])
        self.assertTrue(
            'countryName' in migrated_item["procuringEntity"]["address"])
        self.assertFalse(
            'country-name' in migrated_item["bidders"][0]["address"])
        self.assertTrue(
            'countryName' in migrated_item["bidders"][0]["address"])

    def test_migrate_from2to3(self):
        set_db_schema_version(self.db, 2)
        data = {
            'doc_type': 'Tender',
            'bidders': [{
                "_id": "UUID",
                "id": {
                    "name": "Державне управління справами"
                },
            }]
        }
        _id, _rev = self.db.save(data)
        item = self.db.get(_id)
        migrate_data(self.db, 3)
        migrated_item = self.db.get(_id)
        self.assertTrue('bidders' in item)
        self.assertFalse('bids' in item)
        self.assertFalse('bidders' in migrated_item)
        self.assertTrue('bids' in migrated_item)
        self.assertEqual(
            item["bidders"][0]["_id"], migrated_item["bids"][0]["id"])
        self.assertEqual(item["bidders"][0]["id"]["name"], migrated_item[
                         "bids"][0]["bidders"][0]["id"]["name"])

    def test_migrate_from3to4(self):
        set_db_schema_version(self.db, 3)
        data = {
            'doc_type': 'Tender',
            "itemsToBeProcured": [{
                "description": "футляри до державних нагород",
                "classificationScheme": "Other",
                "otherClassificationScheme": "ДКПП",
                "classificationID": "17.21.1",
                "classificationDescription": "папір і картон гофровані, паперова й картонна тара",
                "unitOfMeasure": "item",
                "quantity": 5
            }]
        }
        _id, _rev = self.db.save(data)
        item = self.db.get(_id)
        migrate_data(self.db, 4)
        migrated_item = self.db.get(_id)
        self.assertEqual(item["itemsToBeProcured"][0]["otherClassificationScheme"], migrated_item["itemsToBeProcured"][0]["primaryClassification"]["scheme"])
        self.assertEqual(item["itemsToBeProcured"][0]["classificationID"], migrated_item["itemsToBeProcured"][0]["primaryClassification"]["id"])
        self.assertEqual(item["itemsToBeProcured"][0]["classificationDescription"], migrated_item["itemsToBeProcured"][0]["primaryClassification"]["description"])

    def test_migrate_from4to5(self):
        set_db_schema_version(self.db, 4)
        data = {
            'doc_type': 'Tender',
            "clarificationPeriod": {
                "endDate": "2014-10-31T00:00:00"
            },
            "clarifications": True
        }
        _id, _rev = self.db.save(data)
        item = self.db.get(_id)
        migrate_data(self.db, 5)
        migrated_item = self.db.get(_id)
        self.assertFalse('clarificationPeriod' in migrated_item)
        self.assertTrue('enquiryPeriod' in migrated_item)
        self.assertFalse('clarifications' in migrated_item)
        self.assertTrue('hasEnquiries' in migrated_item)
        self.assertEqual(item["clarificationPeriod"], migrated_item["enquiryPeriod"])
        self.assertEqual(item["clarifications"], migrated_item["hasEnquiries"])

    def test_migrate_from5to6(self):
        set_db_schema_version(self.db, 5)
        data = {
            'doc_type': 'Tender',
            "attachments": [
                {
                    'id': 'id',
                    'description': 'description',
                    'lastModified': "2014-10-31T00:00:00",
                    'uri': 'uri',
                    'revisions': [1, 1]
                }
            ],
            "bids": [
                {
                    "attachments": [
                        {
                            'id': 'id',
                            'description': 'description',
                            'lastModified': "2014-10-31T00:00:00",
                            'uri': 'uri'
                        }
                    ]
                }
            ]
        }
        _id, _rev = self.db.save(data)
        item = self.db.get(_id)
        migrate_data(self.db, 6)
        migrated_item = self.db.get(_id)
        self.assertFalse('attachments' in migrated_item)
        self.assertTrue('documents' in migrated_item)
        self.assertEqual(item["attachments"][0]["id"], migrated_item["documents"][0]["id"])
        self.assertEqual(item["attachments"][0]["description"], migrated_item["documents"][0]["title"])
        self.assertEqual(item["attachments"][0]["lastModified"], migrated_item["documents"][0]["modified"])
        self.assertEqual(item["attachments"][0]["uri"] + "?download=2_description", migrated_item["documents"][0]["url"])
        self.assertEqual(item["bids"][0]["attachments"][0]["id"], migrated_item["bids"][0]["documents"][0]["id"])
        self.assertEqual(item["bids"][0]["attachments"][0]["description"], migrated_item["bids"][0]["documents"][0]["title"])
        self.assertEqual(item["bids"][0]["attachments"][0]["lastModified"], migrated_item["bids"][0]["documents"][0]["modified"])
        self.assertEqual(item["bids"][0]["attachments"][0]["uri"] + "?download=0_description", migrated_item["bids"][0]["documents"][0]["url"])

    def test_migrate_from10to11(self):
        set_db_schema_version(self.db, 10)
        data = {
            'doc_type': 'Tender',
            "procuringEntity": {
                "identifier": {
                    "scheme": "scheme"
                }
            },
            "bids": [
                {
                    "tenderers": [
                        {
                            "identifier": {
                                "scheme": "scheme"
                            }
                        }
                    ]
                }
            ],
            "awards": [
                {
                    "suppliers": [
                        {
                            "identifier": {
                                "scheme": "scheme"
                            }
                        }
                    ],
                    "complaints": [
                        {
                            "author": {
                                "identifier": {
                                    "scheme": "scheme"
                                }
                            }
                        }
                    ]
                }
            ],
            "complaints": [
                {
                    "author": {
                        "identifier": {
                            "scheme": "scheme"
                        }
                    }
                }
            ],
            "questions": [
                {
                    "author": {
                        "identifier": {
                            "scheme": "scheme"
                        }
                    }
                }
            ],
        }
        _id, _rev = self.db.save(data)
        migrate_data(self.db, 11)
        migrated_item = self.db.get(_id)
        self.assertTrue(all([
            i["identifier"]["scheme"] == 'UA-EDR'
            for i in [
                migrated_item["procuringEntity"]
            ] + [
                x["author"] for x in migrated_item["questions"]
            ] + [
                x["author"] for x in migrated_item["complaints"]
            ] + [
                x for b in migrated_item["bids"] for x in b["tenderers"]
            ] + [
                x for a in migrated_item["awards"] for x in a["suppliers"]
            ] + [
                x["author"] for a in migrated_item["awards"] for x in a["complaints"]
            ]
        ]))

    def test_migrate_from11to12(self):
        set_db_schema_version(self.db, 11)
        data = [
            {
                "status": "active.enquiries",
                "doc_type": "Tender",
                "enquiryPeriod": {
                    "startDate": "2014-11-30T21:51:28.008729+02:00"
                },
                "value": {
                    "amount": -10.0,
                    "currency": u"USD",
                    "valueAddedTaxIncluded": False
                },
                "minimalStep": {
                    "amount": 10.0
                },
                "items": [
                    {
                        "classification": {},
                        "additionalClassifications": [{"scheme": "scheme"}]
                    }
                ],
                "awards": [{}],
                "owner_token": "d9d24edba7bd4eaead5d68f47d7f288e",
                "tenderID": "UA-0d0d5850b0aa4ef5988f4a20925672d2",
                "dateModified": "2014-11-30T21:51:28.008729+02:00",
                "owner": "test"
            },
            {
                "status": "active.tendering",
                "doc_type": "Tender",
                "enquiryPeriod": {
                    "startDate": "2014-11-30T21:51:28.008729+02:00"
                },
                "complaints": [{}],
                "questions": [{}],
                "value": {
                    "amount": 10.0,
                    "currency": u"UAH",
                    "valueAddedTaxIncluded": True
                },
                "minimalStep": {
                    "amount": 20.0,
                    "currency": u"USD",
                    "valueAddedTaxIncluded": False
                },
                "items": [
                    {
                        "classification": {
                            "id": "id",
                            "scheme": "scheme"
                        },
                        "unit": {}
                    }
                ],
                "bids": [
                    {
                        "id": "id1",
                        "tenderers": [{"name": "name"}, {"name": "name"}]
                    },
                    {
                        "id": "id2",
                    },
                ],
                u'procuringEntity': {
                    u'identifier': {
                        u'scheme': u'https://ns.openprocurement.org/ua/edrpou',
                        u'legalName': u'Name'
                    },
                    u'name': u'Name',
                    u'address': {},
                },
                "owner_token": "d9d24edba7bd4eaead5d68f47d7f288e",
                "tenderID": "UA-0d0d5850b0aa4ef5988f4a20925672d2",
                "dateModified": "2014-11-30T21:51:28.008729+02:00",
                "owner": "test"
            },
            {
                "status": "active.auction",
                "doc_type": "Tender",
                "enquiryPeriod": {
                    "startDate": "2014-11-30T21:51:28.008729+02:00"
                },
                "value": {
                    "amount": 10.0,
                    "currency": u"UAH",
                    "valueAddedTaxIncluded": True
                },
                "minimalStep": {
                    "amount": 20.0,
                    "currency": u"USD",
                    "valueAddedTaxIncluded": False
                },
                u'procuringEntity': {
                    u'name': u'Name',
                    u'contactPoint': {},
                },
                "tenderID": "UA-0d0d5850b0aa4ef5988f4a20925672d2",
                "dateModified": "2014-11-30T21:51:28.008729+02:00",
            },
            {
                "status": "active.qualification",
                "doc_type": "Tender",
                "enquiryPeriod": {
                    "startDate": "2014-11-30T21:51:28.008729+02:00"
                },
                "complaints": [{}],
                "questions": [{}],
                "value": {
                    "amount": 10.0,
                    "currency": u"UAH",
                    "valueAddedTaxIncluded": True
                },
                "minimalStep": {
                    "amount": 20.0,
                    "currency": u"USD",
                    "valueAddedTaxIncluded": False
                },
                "bids": [
                    {
                        "id": "id1",
                        "tenderers": [{"name": "name"}, {"name": "name"}]
                    },
                ],
                u'procuringEntity': {
                    u'identifier': {
                        u'scheme': u'https://ns.openprocurement.org/ua/edrpou',
                        u'legalName': u'Name'
                    },
                    u'name': u'Name',
                    u'address': {},
                },
                "awards": [
                    {
                        "suppliers": [{"name": "name"}, {"name": "name"}]
                    }
                ],
                "tenderID": "UA-0d0d5850b0aa4ef5988f4a20925672d2",
                "dateModified": "2014-11-30T21:51:28.008729+02:00",
            },
            {
                "status": "active.awarded",
                "doc_type": "Tender",
                "enquiryPeriod": {
                    "startDate": "2014-11-30T21:51:28.008729+02:00"
                },
                "complaints": [{"author": {"name": "name"}}],
                "questions": [{"author": {"name": "name"}}],
                "value": {
                    "amount": 10.0,
                    "currency": u"UAH",
                    "valueAddedTaxIncluded": True
                },
                "minimalStep": {
                    "amount": 20.0,
                    "currency": u"USD",
                    "valueAddedTaxIncluded": False
                },
                "bids": [
                    {
                        "id": "id1",
                        "tenderers": [{"name": "name"}, {"name": "name"}]
                    },
                ],
                u'procuringEntity': {
                    u'identifier': {
                        u'scheme': u'https://ns.openprocurement.org/ua/edrpou',
                        u'legalName': u'Name'
                    },
                    u'name': u'Name',
                    u'address': {},
                },
                "awards": [
                    {
                        "suppliers": [{"name": "name"}, {"name": "name"}]
                    }
                ],
                "tenderID": "UA-0d0d5850b0aa4ef5988f4a20925672d2",
                "dateModified": "2014-11-30T21:51:28.008729+02:00",
            },
            {
                "status": "complete",
                "doc_type": "Tender",
                "enquiryPeriod": {
                    "startDate": "2014-11-30T21:51:28.008729+02:00"
                },
                "bids": [
                    {
                        "id": "id1",
                        "value": {},
                        "tenderers": [{"name": "name"}, {"name": "name"}]
                    },
                ],
                u'procuringEntity': {
                    u'identifier': {
                        u'scheme': u'https://ns.openprocurement.org/ua/edrpou',
                        u'legalName': u'Name'
                    },
                    u'name': u'Name',
                    u'address': {},
                },
                "awards": [
                    {
                        "value": {},
                    }
                ],
                "tenderID": "UA-0d0d5850b0aa4ef5988f4a20925672d2",
                "dateModified": "2014-11-30T21:51:28.008729+02:00",
            },
        ]
        items = []
        for i in data:
            _id, _rev = self.db.save(i)
            items.append(self.db.get(_id))
        migrate_data(self.db, 12)
        for item in items:
            migrated_item = self.db.get(item['_id'])
            self.assertNotEqual(item, migrated_item)
        self.app.authorization = ('Basic', ('broker05', ''))
        self.app.post_json('/tenders', {'data': test_tender_data}, status=403)

    def test_migrate_from12to13(self):
        set_db_schema_version(self.db, 12)
        data = {
            'doc_type': 'Tender',
            'procurementMethod': 'Open',
            'awardCriteria': 'Lowest Cost',
            'submissionMethod': 'Electronic Auction',
        }
        _id, _rev = self.db.save(data)
        migrate_data(self.db, 13)
        migrated_item = self.db.get(_id)
        self.assertEqual('open', migrated_item['procurementMethod'])
        self.assertEqual('lowestCost', migrated_item['awardCriteria'])
        self.assertEqual('electronicAuction', migrated_item['submissionMethod'])

    def test_migrate_from13to14(self):
        set_db_schema_version(self.db, 13)
        filename = u'файл.doc'
        data = {
            'doc_type': 'Tender',
            "documents": [{'title': str(Header(filename))}],
            "complaints": [{
                "documents": [{'title': str(Header(filename))}],
            }],
            "bids": [{
                "documents": [{'title': str(Header(filename))}],
            }],
        }
        _id, _rev = self.db.save(data)
        migrate_data(self.db, 14)
        migrated_item = self.db.get(_id)
        self.assertEqual(migrated_item["documents"][0]["title"], filename)

    def test_migrate_from14to15(self):
        set_db_schema_version(self.db, 14)
        data = {
            'doc_type': 'Tender',
            'items': [
                {
                    "description": u"футляри до державних нагород",
                    "unit": {
                        "name": u"item",
                        "code": u"44617100-9"
                    },
                    "quantity": 5
                }
            ]
        }
        _id, _rev = self.db.save(data)
        migrate_data(self.db, 15)
        migrated_item = self.db.get(_id)
        self.assertIn('title', migrated_item)
        self.assertEqual(data['items'][0]["description"], migrated_item['title'])
        self.assertEqual(u"CPV", migrated_item['items'][0]['classification']["scheme"])
        self.assertEqual(u"ДКПП", migrated_item['items'][0]['additionalClassifications'][0]["scheme"])

    def test_migrate_from15to16(self):
        set_db_schema_version(self.db, 15)
        data = {
            'doc_type': 'Tender',
            "items": [{
                "deliveryLocation": {
                    'latitude': 49,
                    'longitudee': 24
                }
            }]
        }
        _id, _rev = self.db.save(data)
        item = self.db.get(_id)
        migrate_data(self.db, 16)
        migrated_item = self.db.get(_id)
        self.assertEqual(item["items"][0]["deliveryLocation"]["longitudee"], migrated_item["items"][0]["deliveryLocation"]["longitude"])


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MigrateTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
