# -*- coding: utf-8 -*-
import unittest

from openprocurement.api.models import Tender
from openprocurement.api.migration import migrate_data, get_db_schema_version, set_db_schema_version, SCHEMA_VERSION
from openprocurement.api.tests.base import BaseWebTest, test_tender_data
from email.header import Header


class MigrateTest(BaseWebTest):

    def setUp(self):
        super(MigrateTest, self).setUp()
        migrate_data(self.app.app.registry)

    def test_migrate(self):
        self.assertEqual(get_db_schema_version(self.db), SCHEMA_VERSION)
        migrate_data(self.app.app.registry, 1)
        self.assertEqual(get_db_schema_version(self.db), SCHEMA_VERSION)

    def test_migrate_from0to1(self):
        set_db_schema_version(self.db, 0)
        data = {'doc_type': 'Tender',
                'modifiedAt': '2014-10-15T00:00:00.000000'}
        _id, _rev = self.db.save(data)
        item = self.db.get(_id)
        migrate_data(self.app.app.registry, 1)
        migrated_item = self.db.get(_id)
        self.assertNotIn('modified', item)
        self.assertIn('modifiedAt', item)
        self.assertIn('modified', migrated_item)
        self.assertNotIn('modifiedAt', migrated_item)
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
        migrate_data(self.app.app.registry, 2)
        migrated_item = self.db.get(_id)
        self.assertIn('country-name', item["procuringEntity"]["address"])
        self.assertNotIn('countryName', item["procuringEntity"]["address"])
        self.assertIn('country-name', item["bidders"][0]["address"])
        self.assertNotIn('countryName', item["bidders"][0]["address"])
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
        migrate_data(self.app.app.registry, 3)
        migrated_item = self.db.get(_id)
        self.assertIn('bidders', item)
        self.assertNotIn('bids', item)
        self.assertNotIn('bidders', migrated_item)
        self.assertIn('bids', migrated_item)
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
        migrate_data(self.app.app.registry, 4)
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
        migrate_data(self.app.app.registry, 5)
        migrated_item = self.db.get(_id)
        self.assertNotIn('clarificationPeriod', migrated_item)
        self.assertIn('enquiryPeriod', migrated_item)
        self.assertNotIn('clarifications', migrated_item)
        self.assertIn('hasEnquiries', migrated_item)
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
        migrate_data(self.app.app.registry, 6)
        migrated_item = self.db.get(_id)
        self.assertNotIn('attachments', migrated_item)
        self.assertIn('documents', migrated_item)
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
        migrate_data(self.app.app.registry, 11)
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
        migrate_data(self.app.app.registry, 12)
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
        migrate_data(self.app.app.registry, 13)
        migrated_item = self.db.get(_id)
        self.assertEqual('open', migrated_item['procurementMethod'])
        self.assertEqual('lowestCost', migrated_item['awardCriteria'])
        self.assertEqual('electronicAuction', migrated_item['submissionMethod'])

    def test_migrate_from13to14(self):
        set_db_schema_version(self.db, 13)
        filename = u'файл.doc'
        data = {
            'doc_type': 'Tender',
            "awards": [{
                "documents": [{'title': str(Header(filename))}],
                "contracts": [{
                    "documents": [{'title': str(Header(filename))}],
                }],
                "complaints": [{
                    "documents": [{'title': str(Header(filename))}],
                }],
            }],
            "documents": [{'title': str(Header(filename))}],
            "complaints": [{
                "documents": [{'title': str(Header(filename))}],
            }],
            "bids": [{
                "documents": [{'title': str(Header(filename))}],
            }],
        }
        _id, _rev = self.db.save(data)
        migrate_data(self.app.app.registry, 14)
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
        migrate_data(self.app.app.registry, 15)
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
        migrate_data(self.app.app.registry, 16)
        migrated_item = self.db.get(_id)
        self.assertEqual(item["items"][0]["deliveryLocation"]["longitudee"], migrated_item["items"][0]["deliveryLocation"]["longitude"])

    def test_migrate_from16to17(self):
        set_db_schema_version(self.db, 16)
        data = {
            'doc_type': 'Tender',
            "awards": [
                {"date": '2015-03-01T00:00:00+02:00', "status": 'pending', 'complaintPeriod': {'startDate': '2015-03-01T00:00:00+02:00'}},
                {"date": '2015-03-01T00:00:00+02:00', "status": 'pending'},
                {"date": '2015-03-01T00:00:00+02:00', "status": 'unsuccessful'},
                {"date": '2015-03-01T00:00:00+02:00', "status": 'active'},
                {"date": '2015-03-01T00:00:00+02:00', "status": 'cancelled'},
            ]
        }
        _id, _rev = self.db.save(data)
        migrate_data(self.app.app.registry, 17)
        migrated_item = self.db.get(_id)
        for i in migrated_item['awards']:
            self.assertIn('complaintPeriod', i)

    def test_migrate_from17to18(self):
        set_db_schema_version(self.db, 17)
        data = {
            'doc_type': 'Tender',
            "awards": [
                {
                    "id": "award_id",
                    "contracts": [
                        {
                            "awardID": "award_id",
                            "id": "contract_id"
                        }
                    ]
                }
            ]
        }
        _id, _rev = self.db.save(data)
        migrate_data(self.app.app.registry, 18)
        migrated_item = self.db.get(_id)
        for i in migrated_item['awards']:
            self.assertNotIn('contracts', i)
        self.assertIn('contracts', migrated_item)

    def test_migrate_from18to19(self):
        set_db_schema_version(self.db, 18)
        data = {
            'doc_type': 'Tender',
            "documents": [
                {"title": "title1.doc",
                    "id": "tender_document1_id",
                    "documentType": "contractAnnexes"},
                {"title": "title2.doc",
                    "id": "tender_document2_id",
                    "documentType": "tenderNotice"},
                {"title": "title3.doc",
                    "id": "tender_document3_id",
                    "documentType": "contractAnnexes"},
            ],
            "bids": [
                {
                    "id": "bid1_id",
                    "documents": [
                        {"title": "title1.doc",
                         "id": "bid_document1_id",
                         "documentType": "contractAnnexes"},
                    ]
                }
            ],
            "complaints": [
                {
                    "id": "complaint1_id",
                    "documents": [
                        {"title": "title1.doc",
                         "id": "complaint_document1_id",
                         "documentType": "contractAnnexes"},
                    ]
                }
            ],
            "cancellations": [
                {
                    "id": "cancellation1_id",
                    "documents": [
                        {"title": "title1.doc",
                         "id": "cancellation_document1_id",
                         "documentType": "contractAnnexes"},
                    ]
                }
            ],
            "contracts": [
                {
                    "id": "contract1_id",
                    "documents": [
                        {"title": "title1.doc",
                         "id": "contract_document1_id",
                         "documentType": "contractAnnexes"},
                    ]
                }
            ],
            "awards": [
                {
                    "id": "award_id",
                    "documents": [
                        {"title": "title1.doc",
                         "id": "award_document1_id",
                         "documentType": "contractAnnexes"},
                    ],
                    "complaints": [
                        {"id": "complaint_id",
                         "documents": [
                             {"title": "title1.doc",
                              "id": "award_complaint_document1_id",
                              "documentType": "contractAnnexes"},
                             {"title": "title2.doc",
                              "id": "award_complaint_document2_id",
                              "documentType": "contractGuarantees"},
                             {"title": "title3.doc",
                              "id": "award_complaint_document3_id",
                              "documentType": "contractAnnexes"},
                         ]
                         }
                    ]
                }
            ]
        }
        _id, _rev = self.db.save(data)
        migrate_data(self.app.app.registry, 19)
        migrated_item = self.db.get(_id)
        tender_docs = migrated_item['documents']
        self.assertEqual('contractAnnexe', tender_docs[0]['documentType'])
        self.assertEqual('tenderNotice', tender_docs[1]['documentType'])
        self.assertEqual('contractAnnexe', tender_docs[2]['documentType'])
        for e in ('bids', 'complaints', 'cancellations', 'contracts', 'awards'):
            for i in migrated_item[e]:
                document = i['documents'][0]
                self.assertEqual('contractAnnexe', document['documentType'])
        award_compl_docs = migrated_item['awards'][0]['complaints'][0]['documents']
        self.assertEqual('contractAnnexe', award_compl_docs[0]['documentType'])
        self.assertEqual('contractGuarantees', award_compl_docs[1]['documentType'])
        self.assertEqual('contractAnnexe', award_compl_docs[2]['documentType'])

    def test_migrate_from19to20(self):
        set_db_schema_version(self.db, 19)
        data = {
            'doc_type': 'Tender',
            "contracts": [
                {
                    "documents": [
                        {
                            "url": "/tenders/13fcd78ee62e40dda3a89dc930e5bac9/awards/76ab137ced6e47268d0cdd33448ff22c/contracts/3e9b292b2a7540a89797de335bf053ce/documents/ebcb5dd7f7384b0fbfbed2dc4252fa6e?download=10367238a2964ee18513f209d9b6d1d3"
                        }
                    ]
                }
            ]
        }
        _id, _rev = self.db.save(data)
        migrate_data(self.app.app.registry, 20)
        migrated_item = self.db.get(_id)
        self.assertEqual('/tenders/13fcd78ee62e40dda3a89dc930e5bac9/contracts/3e9b292b2a7540a89797de335bf053ce/documents/ebcb5dd7f7384b0fbfbed2dc4252fa6e?download=10367238a2964ee18513f209d9b6d1d3', migrated_item['contracts'][0]['documents'][0]['url'])

    def test_migrate_from21to22(self):
        set_db_schema_version(self.db, 21)
        data = {
            'doc_type': 'Tender',
            "awards": [
                {
                    "id": "award_id",
                    "complaints": [
                        {
                            "id": "complaint_id",
                            "type": "claim",
                            "dateEscalated": "2016-05-11T15:09:53.751926+03:00"
                        }
                    ]
                }
            ]
        }
        _id, _rev = self.db.save(data)
        migrate_data(self.app.app.registry, 22)
        migrated_item = self.db.get(_id)
        self.assertEqual(migrated_item['awards'][0]['complaints'][0]['type'], 'complaint')

    def test_migrate_from22to23(self):
        set_db_schema_version(self.db, 22)
        u = Tender(test_tender_data)
        u.tenderID = "UA-X"
        u.store(self.db)
        data = self.db.get(u.id)
        data["documents"] = [
            {
                "id": "ebcb5dd7f7384b0fbfbed2dc4252fa6e",
                "title": "name.txt",
                "documentOf": "tender",
                "url": "/tenders/{}/documents/ebcb5dd7f7384b0fbfbed2dc4252fa6e?download=10367238a2964ee18513f209d9b6d1d3".format(u.id),
                "datePublished": "2016-06-01T00:00:00+03:00",
                "dateModified": "2016-06-01T00:00:00+03:00",
                "format": "text/plain",
            }
        ]
        _id, _rev = self.db.save(data)
        self.app.app.registry.docservice_url = 'http://localhost'
        migrate_data(self.app.app.registry, 23)
        migrated_item = self.db.get(u.id)
        self.assertIn('http://localhost/get/10367238a2964ee18513f209d9b6d1d3?', migrated_item['documents'][0]['url'])
        self.assertIn('Prefix={}%2Febcb5dd7f7384b0fbfbed2dc4252fa6e'.format(u.id), migrated_item['documents'][0]['url'])
        self.assertIn('KeyID=', migrated_item['documents'][0]['url'])
        self.assertIn('Signature=', migrated_item['documents'][0]['url'])

    def test_migrate_from23to24(self):
        set_db_schema_version(self.db, 23)
        self.app.app.registry.docservice_url = 'http://localhost.ds'
        u = Tender(test_tender_data)
        u.tenderID = "UA-X"
        u.store(self.db)
        tender_raw = self.db.get(u.id)
        tender_raw['procurementMethodType'] = 'aboveThresholdEU'  # dirty eu simulation
        bid = {"id": "1b4da15470e84c4d948a5d1660d29776"}
        bid["documents"] = [
            {
                # non-ds url. should be fixed (correct id in url) by migrator
                "id": "1801ca2749bd40b0944e58adc3e09c46",
                "title": "name.txt",
                "documentOf": "tender",
                "url": "/tenders/{}/bids/{}/documents/63073ea0da17414db9f13e1a8c347e11?download=a65ef5c688884931aed1a472620d3a00".format(u.id, bid['id']),
                "datePublished": "2016-06-01T00:00:00+03:00",
                "dateModified": "2016-06-01T00:00:00+03:00",
                "format": "text/plain",
                "language": "uk",
                "confidentiality": "buyerOnly"  # documents for which url is not rewrited to ds url
            },
            {
                # non-ds url. should NOT be rewrited by migrator
                "id": "f3e5470b76f84c66a89fd52ed871f645",
                "title": "name.txt",
                "documentOf": "tender",
                "url": "/tenders/{}/bids/{}/documents/512bd84155b145b99e0ac80894fe2b8f?download=d48723d7b4014599ac8d94fb0ac958b4".format(u.id, bid['id']),
                "datePublished": "2016-06-01T00:00:00+03:00",
                "dateModified": "2016-06-01T00:00:00+03:00",
                "format": "text/plain",
            },
            {
                # ds url. should NOT be rewrited by migrator
                "id": "352d774608d749c996fc0e798ffef433",
                "title": "name.txt",
                "documentOf": "tender",
                "url": "http://localhost.ds/get/b893bf5d2fb44a26bd6896178afe5953?KeyID=i_am_ds_url_lalalalala",  # DS url
                "datePublished": "2016-06-01T00:00:00+03:00",
                "dateModified": "2016-06-01T00:00:00+03:00",
                "format": "text/plain",
            }
        ]

        bid["eligibilityDocuments"] = [
            {
                # non-ds url. should be fixed (correct id in url) by migrator
                "id": "73e728784f924518b07f16e34750df1b",
                "title": "name.txt",
                "documentOf": "tender",
                "url": "/tenders/{}/bids/{}/eligibility_documents/a109ca6b04d24bd5bccf57917a65e835?download=5443af5e910f46debe412fc36e69f1ad".format(u.id, bid['id']),
                "datePublished": "2016-06-01T00:00:00+03:00",
                "dateModified": "2016-06-01T00:00:00+03:00",
                "format": "text/plain",
                "language": "uk",
                "confidentiality": "buyerOnly"  # documents for which url is not rewrited to ds url
            }
        ]

        tender_raw['bids'] = [bid,]

        _id, _rev = self.db.save(tender_raw)

        migrate_data(self.app.app.registry, 24)
        migrated= self.db.get(u.id)
        migrated_bid = migrated['bids'][0]

        # url should be corrected
        self.assertIn("/tenders/{}/bids/1b4da15470e84c4d948a5d1660d29776/documents/1801ca2749bd40b0944e58adc3e09c46?download=a65ef5c688884931aed1a472620d3a00".format(u.id), migrated_bid['documents'][0]['url'])
        self.assertIn("/tenders/{}/bids/1b4da15470e84c4d948a5d1660d29776/eligibility_documents/73e728784f924518b07f16e34750df1b?download=5443af5e910f46debe412fc36e69f1ad".format(u.id), migrated_bid['eligibilityDocuments'][0]['url'])

        # url remained the same as before migration
        self.assertIn("/tenders/{}/bids/1b4da15470e84c4d948a5d1660d29776/documents/512bd84155b145b99e0ac80894fe2b8f?download=d48723d7b4014599ac8d94fb0ac958b4".format(u.id), migrated_bid['documents'][1]['url'])
        self.assertIn("http://localhost.ds/get/b893bf5d2fb44a26bd6896178afe5953?KeyID=i_am_ds_url_lalalalala", migrated_bid['documents'][2]['url'])



def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MigrateTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
