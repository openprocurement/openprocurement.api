# -*- coding: utf-8 -*-
import unittest

from openprocurement.api.migration import migrate_data, get_db_schema_version, set_db_schema_version, SCHEMA_VERSION
from openprocurement.api.tests.base import BaseWebTest


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
        data = {u'doc_type': u'Tender', u'status': u'active.qualification', u'awardPeriod': {u'startDate': u'2014-12-12T14:46:00.067102+02:00'}, u'tenderPeriod': {u'startDate': u'2014-11-03T00:00:00+02:02', u'endDate': u'2015-06-07T10:00:00+02:02'}, u'minimalStep': {u'currency': u'UAH', u'amount': 35000.0, u'valueAddedTaxIncluded': True}, u'auctionPeriod': {u'startDate': u'2014-12-12T14:21:00+02:02', u'endDate': u'2014-12-12T14:46:00.067102+02:00'}, u'bids': [{u'date': u'2014-12-12T13:20:44.137146+02:00', u'documents': [{u'title': u'Proposal.pdf', u'url': u'http://api-sandbox.openprocurement.org/api/0/tenders/23e86c9d820c4e66b887980c856b3507/bids/12a7a1a462e64521babe69d8c68fed4c/documents/358ed76c29774aa78b059d8d2686aca4?download=b3145a5b03dd4e4aab5f07cf941863e7', u'format': u'text/plain', u'datePublished': u'2014-12-12T13:20:54.102857+02:00', u'dateModified': u'2014-12-12T13:20:54.102913+02:00', u'id': u'358ed76c29774aa78b059d8d2686aca4'}], u'id': u'12a7a1a462e64521babe69d8c68fed4c',
                u'value': {u'currency': u'UAH', u'amount': 475000.0, u'valueAddedTaxIncluded': True}, u'tenderers': [{u'contactPoint': {u'email': u'soleksuk@gmail.com', u'telephone': u'+380 (432) 21-69-30', u'name': u'\u0421\u0435\u0440\u0433\u0456\u0439 \u041e\u043b\u0435\u043a\u0441\u044e\u043a'}, u'identifier': {u'scheme': u'https://ns.openprocurement.org/ua/edrpou', u'legalName': u'\u0414\u0435\u0440\u0436\u0430\u0432\u043d\u0435 \u043a\u043e\u043c\u0443\u043d\u0430\u043b\u044c\u043d\u0435 \u043f\u0456\u0434\u043f\u0440\u0438\u0454\u043c\u0441\u0442\u0432\u043e \u0433\u0440\u043e\u043c\u0430\u0434\u0441\u044c\u043a\u043e\u0433\u043e \u0445\u0430\u0440\u0447\u0443\u0432\u0430\u043d\u043d\u044f \xab\u0428\u043a\u043e\u043b\u044f\u0440\xbb', u'id': u'13313462', u'uri': u'http://sch10.edu.vn.ua/'}, u'name': u'\u0414\u041a\u041f \xab\u0428\u043a\u043e\u043b\u044f\u0440\xbb', u'address': {u'postalCode': u'21100',
                u'countryName': u'\u0423\u043a\u0440\u0430\u0457\u043d\u0430', u'streetAddress': u'\u0432\u0443\u043b. \u041e\u0441\u0442\u0440\u043e\u0432\u0441\u044c\u043a\u043e\u0433\u043e, 33', u'region': u'\u043c. \u0412\u0456\u043d\u043d\u0438\u0446\u044f', u'locality': u'\u043c. \u0412\u0456\u043d\u043d\u0438\u0446\u044f'}}]}, {u'date': u'2014-12-12T13:21:11.731371+02:00', u'id': u'11cb51f466a14c91a95c46614f9b5eea', u'value': {u'currency': u'UAH', u'amount': 480000.0, u'valueAddedTaxIncluded': True}, u'tenderers': [{u'contactPoint': {u'email': u'alla.myhailova@i.ua', u'telephone': u'+380 (432) 460-665', u'name': u'\u0410\u043b\u043b\u0430 \u041c\u0438\u0445\u0430\u0439\u043b\u043e\u0432\u0430'}, u'identifier': {u'scheme': u'https://ns.openprocurement.org/ua/edrpou',
                u'legalName': u'\u0414\u0435\u0440\u0436\u0430\u0432\u043d\u0435 \u043a\u043e\u043c\u0443\u043d\u0430\u043b\u044c\u043d\u0435 \u043f\u0456\u0434\u043f\u0440\u0438\u0454\u043c\u0441\u0442\u0432\u043e \u0433\u0440\u043e\u043c\u0430\u0434\u0441\u044c\u043a\u043e\u0433\u043e \u0445\u0430\u0440\u0447\u0443\u0432\u0430\u043d\u043d\u044f \xab\u041c\u0435\u0440\u0438\u0434\u0456\u0430\u043d\xbb', u'id': u'13306232', u'uri': u'http://sch10.edu.vn.ua/'}, u'name': u'\u0414\u041a\u041f \xab\u041c\u0435\u0440\u0438\u0434\u0456\u0430\u043d\xbb', u'address': {u'postalCode': u'21018', u'countryName': u'\u0423\u043a\u0440\u0430\u0457\u043d\u0430', u'streetAddress': u'\u0432\u0443\u043b. \u042e\u043d\u043e\u0441\u0442\u0456, 30', u'region': u'\u043c. \u0412\u0456\u043d\u043d\u0438\u0446\u044f', u'locality': u'\u043c. \u0412\u0456\u043d\u043d\u0438\u0446\u044f'}}]}, {u'date': u'2014-12-12T13:21:19.642159+02:00', u'id': u'5b584be340c144a3ad1d963799108b2e',
                u'value': {u'currency': u'UAH', u'amount': 482000.0, u'valueAddedTaxIncluded': True}, u'tenderers': [{u'contactPoint': {u'email': u'alla.myhailova@i.ua', u'telephone': u'+380 (432) 460-665', u'name': u'\u0410\u043b\u043b\u0430 \u041c\u0438\u0445\u0430\u0439\u043b\u043e\u0432\u0430'}, u'identifier': {u'scheme': u'https://ns.openprocurement.org/ua/edrpou', u'legalName': u'\u0414\u0435\u0440\u0436\u0430\u0432\u043d\u0435 \u043a\u043e\u043c\u0443\u043d\u0430\u043b\u044c\u043d\u0435 \u043f\u0456\u0434\u043f\u0440\u0438\u0454\u043c\u0441\u0442\u0432\u043e \u0433\u0440\u043e\u043c\u0430\u0434\u0441\u044c\u043a\u043e\u0433\u043e \u0445\u0430\u0440\u0447\u0443\u0432\u0430\u043d\u043d\u044f \xab\u041c\u0435\u0440\u0438\u0434\u0456\u0430\u043d\xbb', u'id': u'13306232', u'uri': u'http://sch10.edu.vn.ua/'}, u'name': u'\u0414\u041a\u041f \xab\u041c\u0435\u0440\u0438\u0434\u0456\u0430\u043d2\xbb', u'address': {u'postalCode': u'21018', u'countryName': u'\u0423\u043a\u0440\u0430\u0457\u043d\u0430',
                u'streetAddress': u'\u0432\u0443\u043b. \u042e\u043d\u043e\u0441\u0442\u0456, 30', u'region': u'\u043c. \u0412\u0456\u043d\u043d\u0438\u0446\u044f', u'locality': u'\u043c. \u0412\u0456\u043d\u043d\u0438\u0446\u044f'}}]}], u'value': {u'currency': u'UAH', u'amount': 500000.0, u'valueAddedTaxIncluded': True}, u'dateModified': u'2014-12-12T14:46:00.086732+02:00', u'auctionUrl': u'http://auction-sandbox.openprocurement.org/tenders/23e86c9d820c4e66b887980c856b3507', u'documents': [{u'title': u'Notice.pdf', u'url': u'http://api-sandbox.openprocurement.org/api/0/tenders/23e86c9d820c4e66b887980c856b3507/documents/99eef7b8a5b74ef1a97ff358424fbf3b?download=ac399b4442564d5e918e9e08b3f4a871', u'format': u'text/plain', u'datePublished': u'2014-12-12T13:19:22.906045+02:00', u'dateModified': u'2014-12-12T13:19:22.906099+02:00', u'id': u'99eef7b8a5b74ef1a97ff358424fbf3b'}, {u'title': u'AwardCriteria.pdf',
                u'url': u'http://api-sandbox.openprocurement.org/api/0/tenders/23e86c9d820c4e66b887980c856b3507/documents/832090c645d34b97b0d99be36dfb9fab?download=0687f2be0e7149118a992d16e1e155a5', u'format': u'text/plain', u'datePublished': u'2014-12-12T13:19:34.176354+02:00', u'dateModified': u'2014-12-12T13:19:34.178444+02:00', u'id': u'832090c645d34b97b0d99be36dfb9fab'}, {u'title': u'AwardCriteria-v2.pdf', u'url': u'http://api-sandbox.openprocurement.org/api/0/tenders/23e86c9d820c4e66b887980c856b3507/documents/832090c645d34b97b0d99be36dfb9fab?download=2810d488da3e43a18f8ef3fe573e5442', u'format': u'text/plain', u'datePublished': u'2014-12-12T13:19:34.176354+02:00', u'dateModified': u'2014-12-12T13:19:46.238336+02:00', u'id': u'832090c645d34b97b0d99be36dfb9fab'}], u'awards': [{u'status': u'pending', u'suppliers': [{u'contactPoint': {u'email': u'soleksuk@gmail.com', u'telephone': u'+380 (432) 21-69-30', u'name': u'\u0421\u0435\u0440\u0433\u0456\u0439 \u041e\u043b\u0435\u043a\u0441\u044e\u043a'},
                u'identifier': {u'scheme': u'https://ns.openprocurement.org/ua/edrpou', u'legalName': u'\u0414\u0435\u0440\u0436\u0430\u0432\u043d\u0435 \u043a\u043e\u043c\u0443\u043d\u0430\u043b\u044c\u043d\u0435 \u043f\u0456\u0434\u043f\u0440\u0438\u0454\u043c\u0441\u0442\u0432\u043e \u0433\u0440\u043e\u043c\u0430\u0434\u0441\u044c\u043a\u043e\u0433\u043e \u0445\u0430\u0440\u0447\u0443\u0432\u0430\u043d\u043d\u044f \xab\u0428\u043a\u043e\u043b\u044f\u0440\xbb', u'id': u'13313462', u'uri': u'http://sch10.edu.vn.ua/'}, u'name': u'\u0414\u041a\u041f \xab\u0428\u043a\u043e\u043b\u044f\u0440\xbb', u'address': {u'postalCode': u'21100', u'countryName': u'\u0423\u043a\u0440\u0430\u0457\u043d\u0430', u'streetAddress': u'\u0432\u0443\u043b. \u041e\u0441\u0442\u0440\u043e\u0432\u0441\u044c\u043a\u043e\u0433\u043e, 33', u'region': u'\u043c. \u0412\u0456\u043d\u043d\u0438\u0446\u044f', u'locality': u'\u043c. \u0412\u0456\u043d\u043d\u0438\u0446\u044f'}}], u'bid_id': u'12a7a1a462e64521babe69d8c68fed4c',
                u'value': {u'currency': u'UAH', u'amount': 475000.0, u'valueAddedTaxIncluded': True}, u'date': u'2014-12-12T14:46:00.087654+02:00', u'id': u'6939af5cc8144edcbac0d536df7a3082'}], u'tenderID': u'UA-23e86c9d820c4e66b887980c856b3507', u'questions': [{u'description': u'\u041f\u0440\u043e\u0441\u0438\u043c\u043e \u0434\u043e\u0434\u0430\u0442\u0438 \u0442\u0430\u0431\u043b\u0438\u0446\u044e \u043f\u043e\u0442\u0440\u0456\u0431\u043d\u043e\u0457 \u043a\u0430\u043b\u043e\u0440\u0456\u0439\u043d\u043e\u0441\u0442\u0456 \u0445\u0430\u0440\u0447\u0443\u0432\u0430\u043d\u043d\u044f \u043f\u043e \u043c\u0456\u0441\u044f\u0446\u044f\u0445', u'author': {u'contactPoint': {u'email': u'soleksuk@gmail.com', u'telephone': u'+380 (432) 21-69-30', u'name': u'\u0421\u0435\u0440\u0433\u0456\u0439 \u041e\u043b\u0435\u043a\u0441\u044e\u043a'}, u'identifier': {u'scheme': u'https://ns.openprocurement.org/ua/edrpou',
                u'legalName': u'\u0414\u0435\u0440\u0436\u0430\u0432\u043d\u0435 \u043a\u043e\u043c\u0443\u043d\u0430\u043b\u044c\u043d\u0435 \u043f\u0456\u0434\u043f\u0440\u0438\u0454\u043c\u0441\u0442\u0432\u043e \u0433\u0440\u043e\u043c\u0430\u0434\u0441\u044c\u043a\u043e\u0433\u043e \u0445\u0430\u0440\u0447\u0443\u0432\u0430\u043d\u043d\u044f \xab\u0428\u043a\u043e\u043b\u044f\u0440\xbb', u'id': u'13313462', u'uri': u'http://sch10.edu.vn.ua/'}, u'name': u'\u0414\u041a\u041f \xab\u0428\u043a\u043e\u043b\u044f\u0440\xbb', u'address': {u'postalCode': u'21100', u'countryName': u'\u0423\u043a\u0440\u0430\u0457\u043d\u0430', u'streetAddress': u'\u0432\u0443\u043b. \u041e\u0441\u0442\u0440\u043e\u0432\u0441\u044c\u043a\u043e\u0433\u043e, 33', u'region': u'\u043c. \u0412\u0456\u043d\u043d\u0438\u0446\u044f', u'locality': u'\u043c. \u0412\u0456\u043d\u043d\u0438\u0446\u044f'}},
                u'title': u'\u041a\u0430\u043b\u043e\u0440\u0456\u0439\u043d\u0456\u0441\u0442\u044c \u043f\u043e \u043c\u0456\u0441\u044f\u0446\u044f\u0445', u'date': u'2014-12-12T13:19:57.647711+02:00', u'answer': u'\u0422\u0430\u0431\u043b\u0438\u0446\u044e \u0434\u043e\u0434\u0430\u043d\u043e \u0432 \u0444\u0430\u0439\u043b\u0456 "Kalorijnist.xslx"', u'id': u'68b7dc5c7b1241aa9a88713b5142042f'}], u'enquiryPeriod': {u'startDate': u'2014-12-12T13:18:27.993046+02:00', u'endDate': u'2015-05-29T00:00:00+02:02'}, u'complaints': [{u'status': u'invalid', u'documents': [{u'title': u'ComplaintResolution.pdf', u'url': u'http://api-sandbox.openprocurement.org/api/0/tenders/23e86c9d820c4e66b887980c856b3507/complaints/40114ce22115477faa77bd6824ebadd1/documents/844728f0b41d4f46b4ef721f6c4497cb?download=f14f31961744449684869f1f270bc6f3', u'format': u'text/plain', u'datePublished': u'2014-12-12T13:19:02.985969+02:00', u'dateModified': u'2014-12-12T13:19:02.986016+02:00', u'id': u'844728f0b41d4f46b4ef721f6c4497cb'}],
                u'description': u'\u0423\u043c\u043e\u0432\u0438 \u0432\u0438\u0441\u0442\u0430\u0432\u043b\u0435\u043d\u0456 \u0437\u0430\u043c\u043e\u0432\u043d\u0438\u043a\u043e\u043c \u043d\u0435 \u043c\u0456\u0441\u0442\u044f\u0442\u044c \u0434\u043e\u0441\u0442\u0430\u0442\u043d\u044c\u043e \u0456\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0456\u0457, \u0449\u043e\u0431 \u0437\u0430\u044f\u0432\u043a\u0430 \u043c\u0430\u043b\u0430 \u0441\u0435\u043d\u0441.', u'author': {u'contactPoint': {u'email': u'soleksuk@gmail.com', u'telephone': u'+380 (432) 21-69-30', u'name': u'\u0421\u0435\u0440\u0433\u0456\u0439 \u041e\u043b\u0435\u043a\u0441\u044e\u043a'}, u'identifier': {u'scheme': u'https://ns.openprocurement.org/ua/edrpou',
                u'legalName': u'\u0414\u0435\u0440\u0436\u0430\u0432\u043d\u0435 \u043a\u043e\u043c\u0443\u043d\u0430\u043b\u044c\u043d\u0435 \u043f\u0456\u0434\u043f\u0440\u0438\u0454\u043c\u0441\u0442\u0432\u043e \u0433\u0440\u043e\u043c\u0430\u0434\u0441\u044c\u043a\u043e\u0433\u043e \u0445\u0430\u0440\u0447\u0443\u0432\u0430\u043d\u043d\u044f \xab\u0428\u043a\u043e\u043b\u044f\u0440\xbb', u'id': u'13313462', u'uri': u'http://sch10.edu.vn.ua/'}, u'name': u'\u0414\u041a\u041f \xab\u0428\u043a\u043e\u043b\u044f\u0440\xbb', u'address': {u'postalCode': u'21100', u'countryName': u'\u0423\u043a\u0440\u0430\u0457\u043d\u0430', u'streetAddress': u'\u0432\u0443\u043b. \u041e\u0441\u0442\u0440\u043e\u0432\u0441\u044c\u043a\u043e\u0433\u043e, 33', u'region': u'\u043c. \u0412\u0456\u043d\u043d\u0438\u0446\u044f', u'locality': u'\u043c. \u0412\u0456\u043d\u043d\u0438\u0446\u044f'}},
                u'title': u'\u041d\u0435\u0434\u043e\u0441\u0442\u0430\u0442\u043d\u044c\u043e \u0456\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0456\u0457', u'date': u'2014-12-12T13:18:46.250102+02:00', u'id': u'40114ce22115477faa77bd6824ebadd1'}], u'items': [{u'classification': {u'scheme': u'CPV', u'id': u'55523100-3', u'description': u'\u041f\u043e\u0441\u043b\u0443\u0433\u0438 \u0437 \u0445\u0430\u0440\u0447\u0443\u0432\u0430\u043d\u043d\u044f \u0443 \u0448\u043a\u043e\u043b\u0430\u0445'}, u'additionalClassifications': [{u'scheme': u'\u0414\u041a\u041f\u041f', u'id': u'55.51.10.300', u'description': u'\u041f\u043e\u0441\u043b\u0443\u0433\u0438 \u0448\u043a\u0456\u043b\u044c\u043d\u0438\u0445 \u0457\u0434\u0430\u043b\u0435\u043d\u044c'}], u'description': u'\u041f\u043e\u0441\u043b\u0443\u0433\u0438 \u0448\u043a\u0456\u043b\u044c\u043d\u0438\u0445 \u0457\u0434\u0430\u043b\u0435\u043d\u044c', u'unit': {u'name': u'item'}, u'quantity': 5}], u'id': u'23e86c9d820c4e66b887980c856b3507',
                u'procuringEntity': {u'identifier': {u'scheme': u'https://ns.openprocurement.org/ua/edrpou', u'legalName': u'\u0417\u0430\u043a\u043b\u0430\u0434 "\u0417\u0430\u0433\u0430\u043b\u044c\u043d\u043e\u043e\u0441\u0432\u0456\u0442\u043d\u044f \u0448\u043a\u043e\u043b\u0430 \u0406-\u0406\u0406\u0406 \u0441\u0442\u0443\u043f\u0435\u043d\u0456\u0432 \u2116 10 \u0412\u0456\u043d\u043d\u0438\u0446\u044c\u043a\u043e\u0457 \u043c\u0456\u0441\u044c\u043a\u043e\u0457 \u0440\u0430\u0434\u0438"', u'id': u'21725150', u'uri': u'http://sch10.edu.vn.ua/'}, u'name': u'\u0417\u041e\u0421\u0428 #10 \u043c.\u0412\u0456\u043d\u043d\u0438\u0446\u0456', u'address': {u'postalCode': u'21027', u'countryName': u'\u0423\u043a\u0440\u0430\u0457\u043d\u0430', u'streetAddress': u'\u0432\u0443\u043b. \u0421\u0442\u0430\u0445\u0443\u0440\u0441\u044c\u043a\u043e\u0433\u043e. 22', u'region': u'\u043c. \u0412\u0456\u043d\u043d\u0438\u0446\u044f', u'locality': u'\u043c. \u0412\u0456\u043d\u043d\u0438\u0446\u044f'}}}
        _id, _rev = self.db.save(data)
        item = self.db.get(_id)
        migrate_data(self.db, 12)
        migrated_item = self.db.get(_id)
        self.assertNotEqual(item, migrated_item)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MigrateTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
