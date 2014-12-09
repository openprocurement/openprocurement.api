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


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MigrateTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
