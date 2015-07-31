# -*- coding: utf-8 -*-
import unittest
from datetime import timedelta

from openprocurement.api import ROUTE_PREFIX
from openprocurement.api.models import Tender, get_now
from openprocurement.api.tests.base import test_tender_data, BaseWebTest, BaseTenderWebTest


class TenderTest(BaseWebTest):

    def test_simple_add_tender(self):
        u = Tender(test_tender_data)
        u.tenderID = "UA-X"

        assert u.id is None
        assert u.rev is None

        u.store(self.db)

        assert u.id is not None
        assert u.rev is not None

        fromdb = self.db.get(u.id)

        assert u.tenderID == fromdb['tenderID']
        assert u.doc_type == "Tender"

        u.delete_instance(self.db)


class TenderResourceTest(BaseWebTest):

    def test_empty_listing(self):
        response = self.app.get('/tenders')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'], [])
        self.assertFalse('{\n    "' in response.body)
        self.assertFalse('callback({' in response.body)
        self.assertEqual(response.json['next_page']['offset'], '')

        response = self.app.get('/tenders?opt_jsonp=callback')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/javascript')
        self.assertFalse('{\n    "' in response.body)
        self.assertIn('callback({', response.body)

        response = self.app.get('/tenders?opt_pretty=1')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('{\n    "', response.body)
        self.assertFalse('callback({' in response.body)

        response = self.app.get('/tenders?opt_jsonp=callback&opt_pretty=1')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/javascript')
        self.assertIn('{\n    "', response.body)
        self.assertIn('callback({', response.body)

        response = self.app.get('/tenders?offset=2015-01-01T00:00:00+02:00&descending=1&limit=10')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'], [])
        self.assertIn('descending=1', response.json['next_page']['uri'])
        self.assertIn('limit=10', response.json['next_page']['uri'])

    def test_listing(self):
        response = self.app.get('/tenders')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json['data']), 0)

        tenders = []

        for i in range(3):
            response = self.app.post_json('/tenders', {'data': test_tender_data})
            self.assertEqual(response.status, '201 Created')
            self.assertEqual(response.content_type, 'application/json')
            tenders.append(response.json['data'])

        response = self.app.get('/tenders')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json['data']), 3)
        self.assertEqual(set(response.json['data'][0]), set([u'id', u'dateModified']))
        self.assertEqual(set([i['id'] for i in response.json['data']]), set([i['id'] for i in tenders]))
        self.assertEqual(set([i['dateModified'] for i in response.json['data']]), set([i['dateModified'] for i in tenders]))
        self.assertEqual([i['dateModified'] for i in response.json['data']], sorted([i['dateModified'] for i in tenders]))

        response = self.app.get('/tenders?limit=2')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json['data']), 2)

        response = self.app.get(response.json['next_page']['path'].replace(ROUTE_PREFIX, ''))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json['data']), 1)

        response = self.app.get(response.json['next_page']['path'].replace(ROUTE_PREFIX, ''))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json['data']), 0)

        response = self.app.get('/tenders', params=[('opt_fields', 'status,enquiryPeriod')])
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json['data']), 3)
        self.assertEqual(set(response.json['data'][0]), set([u'id', u'dateModified', u'status', u'enquiryPeriod']))
        self.assertIn('opt_fields=status%2CenquiryPeriod', response.json['next_page']['uri'])

        response = self.app.get('/tenders?descending=1')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(len(response.json['data']), 3)
        self.assertEqual(set(response.json['data'][0]), set([u'id', u'dateModified']))
        self.assertEqual(set([i['id'] for i in response.json['data']]), set([i['id'] for i in tenders]))
        self.assertEqual([i['dateModified'] for i in response.json['data']], sorted([i['dateModified'] for i in tenders], reverse=True))

        response = self.app.get('/tenders?descending=1&limit=2')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(len(response.json['data']), 2)

        response = self.app.get(response.json['next_page']['path'].replace(ROUTE_PREFIX, ''))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json['data']), 1)

        response = self.app.get(response.json['next_page']['path'].replace(ROUTE_PREFIX, ''))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json['data']), 0)

        test_tender_data2 = test_tender_data.copy()
        test_tender_data2['mode'] = 'test'
        response = self.app.post_json('/tenders', {'data': test_tender_data2})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.get('/tenders?mode=test')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json['data']), 1)

        response = self.app.get('/tenders?mode=_all_')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json['data']), 4)

    def test_create_tender_invalid(self):
        request_path = '/tenders'
        response = self.app.post(request_path, 'data', status=415)
        self.assertEqual(response.status, '415 Unsupported Media Type')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description':
                u"Content-Type header should be one of ['application/json']", u'location': u'header', u'name': u'Content-Type'}
        ])

        response = self.app.post(
            request_path, 'data', content_type='application/json', status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'No JSON object could be decoded',
                u'location': u'body', u'name': u'data'}
        ])

        response = self.app.post_json(request_path, 'data', status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Data not available',
                u'location': u'body', u'name': u'data'}
        ])

        response = self.app.post_json(request_path, {'not_data': {}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Data not available',
                u'location': u'body', u'name': u'data'}
        ])

        response = self.app.post_json(request_path, {'data': []}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Data not available',
                u'location': u'body', u'name': u'data'}
        ])

        response = self.app.post_json(request_path, {'data': {
                                      'invalid_field': 'invalid_value'}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Rogue field', u'location':
                u'body', u'name': u'invalid_field'}
        ])

        response = self.app.post_json(request_path, {'data': {'value': 'invalid_value'}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [
                u'Please use a mapping for this field or Value instance instead of unicode.'], u'location': u'body', u'name': u'value'}
        ])

        response = self.app.post_json(request_path, {'data': {'procurementMethod': 'invalid_value'}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertIn({u'description': [u"Value must be one of ['open', 'selective', 'limited']."], u'location': u'body', u'name': u'procurementMethod'}, response.json['errors'])
        self.assertIn({u'description': [u'This field is required.'], u'location': u'body', u'name': u'tenderPeriod'}, response.json['errors'])
        self.assertIn({u'description': [u'This field is required.'], u'location': u'body', u'name': u'minimalStep'}, response.json['errors'])
        self.assertIn({u'description': [u'This field is required.'], u'location': u'body', u'name': u'items'}, response.json['errors'])
        self.assertIn({u'description': [u'This field is required.'], u'location': u'body', u'name': u'enquiryPeriod'}, response.json['errors'])
        self.assertIn({u'description': [u'This field is required.'], u'location': u'body', u'name': u'value'}, response.json['errors'])
        self.assertIn({u'description': [u'This field is required.'], u'location': u'body', u'name': u'items'}, response.json['errors'])

        response = self.app.post_json(request_path, {'data': {'enquiryPeriod': {'endDate': 'invalid_value'}}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': {u'endDate': [u"Could not parse invalid_value. Should be ISO8601."]}, u'location': u'body', u'name': u'enquiryPeriod'}
        ])

        data = test_tender_data['tenderPeriod']
        test_tender_data['tenderPeriod'] = {'startDate': '2014-10-31T00:00:00', 'endDate': '2014-10-01T00:00:00'}
        response = self.app.post_json(request_path, {'data': test_tender_data}, status=422)
        test_tender_data['tenderPeriod'] = data
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': {u'startDate': [u'period should begin before its end']}, u'location': u'body', u'name': u'tenderPeriod'}
        ])

        data = test_tender_data['tenderPeriod']
        test_tender_data['tenderPeriod'] = {'startDate': '2014-10-31T00:00:00', 'endDate': '2015-10-01T00:00:00'}
        response = self.app.post_json(request_path, {'data': test_tender_data}, status=422)
        test_tender_data['tenderPeriod'] = data
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'period should begin after enquiryPeriod'], u'location': u'body', u'name': u'tenderPeriod'}
        ])

        test_tender_data['auctionPeriod'] = {'startDate': '2014-10-31T00:00:00', 'endDate': '2015-10-01T00:00:00'}
        response = self.app.post_json(request_path, {'data': test_tender_data}, status=422)
        del test_tender_data['auctionPeriod']
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'period should begin after tenderPeriod'], u'location': u'body', u'name': u'auctionPeriod'}
        ])

        test_tender_data['auctionPeriod'] = {'startDate': '2015-10-31T00:00:00', 'endDate': '2016-10-01T00:00:00'}
        test_tender_data['awardPeriod'] = {'startDate': '2014-10-31T00:00:00', 'endDate': '2015-10-01T00:00:00'}
        response = self.app.post_json(request_path, {'data': test_tender_data}, status=422)
        del test_tender_data['auctionPeriod']
        del test_tender_data['awardPeriod']
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'period should begin after auctionPeriod'], u'location': u'body', u'name': u'awardPeriod'}
        ])

        data = test_tender_data['minimalStep']
        test_tender_data['minimalStep'] = {'amount': '1000.0'}
        response = self.app.post_json(request_path, {'data': test_tender_data}, status=422)
        test_tender_data['minimalStep'] = data
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'value should be less than value of tender'], u'location': u'body', u'name': u'minimalStep'}
        ])

        data = test_tender_data['minimalStep']
        test_tender_data['minimalStep'] = {'amount': '100.0', 'valueAddedTaxIncluded': False}
        response = self.app.post_json(request_path, {'data': test_tender_data}, status=422)
        test_tender_data['minimalStep'] = data
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'valueAddedTaxIncluded should be identical to valueAddedTaxIncluded of value of tender'], u'location': u'body', u'name': u'minimalStep'}
        ])

        data = test_tender_data['minimalStep']
        test_tender_data['minimalStep'] = {'amount': '100.0', 'currency': "USD"}
        response = self.app.post_json(request_path, {'data': test_tender_data}, status=422)
        test_tender_data['minimalStep'] = data
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'currency should be identical to currency of value of tender'], u'location': u'body', u'name': u'minimalStep'}
        ])

        data = test_tender_data["items"][0]["additionalClassifications"][0]["scheme"]
        test_tender_data["items"][0]["additionalClassifications"][0]["scheme"] = 'Не ДКПП'
        response = self.app.post_json(request_path, {'data': test_tender_data}, status=422)
        test_tender_data["items"][0]["additionalClassifications"][0]["scheme"] = data
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'additionalClassifications'], u'location': u'body', u'name': u'items'}
        ])

        data = test_tender_data["procuringEntity"]["contactPoint"]["telephone"]
        del test_tender_data["procuringEntity"]["contactPoint"]["telephone"]
        response = self.app.post_json(request_path, {'data': test_tender_data}, status=422)
        test_tender_data["procuringEntity"]["contactPoint"]["telephone"] = data
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': {u'contactPoint': {u'email': [u'telephone or email should be present']}}, u'location': u'body', u'name': u'procuringEntity'}
        ])

        data = test_tender_data["items"][0].copy()
        classification = data['classification'].copy()
        classification["id"] = u'19212310-1'
        data['classification'] = classification
        test_tender_data["items"] = [test_tender_data["items"][0], data]
        response = self.app.post_json(request_path, {'data': test_tender_data}, status=422)
        test_tender_data["items"] = test_tender_data["items"][:1]
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'CPV group of items be identical'], u'location': u'body', u'name': u'items'}
        ])

    def test_create_tender_generated(self):
        data = test_tender_data.copy()
        #del data['awardPeriod']
        data.update({'id': 'hash', 'doc_id': 'hash2', 'tenderID': 'hash3'})
        response = self.app.post_json('/tenders', {'data': data})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        tender = response.json['data']
        self.assertEqual(set(tender), set([u'id', u'dateModified', u'tenderID', u'status', u'enquiryPeriod',
                                           u'tenderPeriod', u'minimalStep', u'items', u'value', u'procuringEntity',
                                           u'procurementMethod', u'awardCriteria', u'submissionMethod', u'title']))
        self.assertNotEqual(data['id'], tender['id'])
        self.assertNotEqual(data['doc_id'], tender['id'])
        self.assertNotEqual(data['tenderID'], tender['tenderID'])

    def test_create_tender(self):
        response = self.app.get('/tenders')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json['data']), 0)

        response = self.app.post_json('/tenders', {"data": test_tender_data})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        tender = response.json['data']
        self.assertEqual(set(tender) - set(test_tender_data), set(
            [u'id', u'dateModified', u'tenderID', u'status', u'procurementMethod', u'awardCriteria', u'submissionMethod']))
        self.assertIn(tender['id'], response.headers['Location'])

        response = self.app.get('/tenders/{}'.format(tender['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(set(response.json['data']), set(tender))
        self.assertEqual(response.json['data'], tender)

        response = self.app.post_json('/tenders?opt_jsonp=callback', {"data": test_tender_data})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/javascript')
        self.assertIn('callback({"', response.body)

        response = self.app.post_json('/tenders?opt_pretty=1', {"data": test_tender_data})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('{\n    "', response.body)

        response = self.app.post_json('/tenders', {"data": test_tender_data, "options": {"pretty": True}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('{\n    "', response.body)

    def test_get_tender(self):
        response = self.app.get('/tenders')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json['data']), 0)

        response = self.app.post_json('/tenders', {'data': test_tender_data})
        self.assertEqual(response.status, '201 Created')
        tender = response.json['data']

        response = self.app.get('/tenders/{}'.format(tender['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'], tender)

        response = self.app.get('/tenders/{}?opt_jsonp=callback'.format(tender['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/javascript')
        self.assertIn('callback({"data": {"', response.body)

        response = self.app.get('/tenders/{}?opt_pretty=1'.format(tender['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('{\n    "data": {\n        "', response.body)

    #def test_put_tender(self):
        #response = self.app.get('/tenders')
        #self.assertEqual(response.status, '200 OK')
        #self.assertEqual(len(response.json['data']), 0)

        #response = self.app.post_json('/tenders', {'data': test_tender_data})
        #self.assertEqual(response.status, '201 Created')
        #tender = response.json['data']
        #tender['procurementMethod'] = 'Open'
        #dateModified = tender.pop('dateModified')

        #response = self.app.put_json('/tenders/{}'.format(
            #tender['id']), {'data': tender})
        #self.assertEqual(response.status, '200 OK')
        #self.assertEqual(response.content_type, 'application/json')
        #new_tender = response.json['data']
        #new_dateModified = new_tender.pop('dateModified')
        #self.assertEqual(tender, new_tender)
        #self.assertNotEqual(dateModified, new_dateModified)

        #response = self.app.patch_json('/tenders/{}'.format(tender['id']), {'data': {'status': 'complete'}})
        #self.assertEqual(response.status, '200 OK')
        #self.assertEqual(response.content_type, 'application/json')

        #response = self.app.put_json('/tenders/{}'.format(
            #tender['id']), {'data': tender}, status=403)
        #self.assertEqual(response.status, '403 Forbidden')
        #self.assertEqual(response.content_type, 'application/json')
        #self.assertEqual(response.json['errors'][0]["description"], "Can't update tender in current (complete) status")

    def test_patch_tender(self):
        response = self.app.get('/tenders')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json['data']), 0)

        response = self.app.post_json('/tenders', {'data': test_tender_data})
        self.assertEqual(response.status, '201 Created')
        tender = response.json['data']
        owner_token = response.json['access']['token']
        dateModified = tender.pop('dateModified')

        response = self.app.patch_json('/tenders/{}'.format(
            tender['id']), {'data': {'procuringEntity': {'contactPoint': {'faxNumber': None}}}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertNotIn('faxNumber', response.json['data']['procuringEntity']['contactPoint'])

        response = self.app.patch_json('/tenders/{}'.format(
            tender['id']), {'data': {'procuringEntity': {'contactPoint': {'faxNumber': u"0440000000"}}}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('faxNumber', response.json['data']['procuringEntity']['contactPoint'])

        response = self.app.patch_json('/tenders/{}'.format(
            tender['id']), {'data': {'procurementMethodRationale': 'Open'}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        new_tender = response.json['data']
        new_dateModified = new_tender.pop('dateModified')
        tender['procurementMethodRationale'] = 'Open'
        self.assertEqual(tender, new_tender)
        self.assertNotEqual(dateModified, new_dateModified)

        response = self.app.patch_json('/tenders/{}'.format(
            tender['id']), {'data': {'dateModified': new_dateModified}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        new_tender2 = response.json['data']
        new_dateModified2 = new_tender2.pop('dateModified')
        self.assertEqual(new_tender, new_tender2)
        self.assertEqual(new_dateModified, new_dateModified2)

        revisions = self.db.get(tender['id']).get('revisions')
        self.assertEqual(revisions[-1][u'changes'][0]['op'], u'remove')
        self.assertEqual(revisions[-1][u'changes'][0]['path'], u'/procurementMethodRationale')

        response = self.app.patch_json('/tenders/{}'.format(
            tender['id']), {'data': {'items': [test_tender_data['items'][0]]}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.patch_json('/tenders/{}'.format(
            tender['id']), {'data': {'items': [{}, test_tender_data['items'][0]]}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['items'][0], response.json['data']['items'][1])

        response = self.app.patch_json('/tenders/{}'.format(
            tender['id']), {'data': {'items': [{}]}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(len(response.json['data']['items']), 1)

        response = self.app.patch_json('/tenders/{}'.format(tender['id']), {'data': {'items': [{"classification": {
            "scheme": "CPV",
            "id": "55523100-3",
            "description": "Послуги з харчування у школах"
        }}]}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.patch_json('/tenders/{}'.format(tender['id']), {'data': {'items': [{"additionalClassifications": [
            tender['items'][0]["additionalClassifications"][0] for i in range(3)
        ]}]}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.patch_json('/tenders/{}'.format(tender['id']), {'data': {'items': [{"additionalClassifications": tender['items'][0]["additionalClassifications"]}]}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.patch_json('/tenders/{}'.format(
            tender['id']), {'data': {'enquiryPeriod': {'endDate': new_dateModified2}}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        new_tender = response.json['data']
        self.assertIn('startDate', new_tender['enquiryPeriod'])

        #response = self.app.patch_json('/tenders/{}'.format(tender['id']), {'data': {'status': 'active.auction'}})
        #self.assertEqual(response.status, '200 OK')

        #response = self.app.get('/tenders/{}'.format(tender['id']))
        #self.assertEqual(response.status, '200 OK')
        #self.assertEqual(response.content_type, 'application/json')
        #self.assertIn('auctionUrl', response.json['data'])

        response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender['id'], owner_token), {'data': {'status': 'active.auction'}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update tender status")

        response = self.app.patch_json('/tenders/{}'.format(tender['id']), {'data': {'status': 'complete'}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.patch_json('/tenders/{}'.format(tender['id']), {'data': {'status': 'active.auction'}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update tender in current (complete) status")

    def test_dateModified_tender(self):
        response = self.app.get('/tenders')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json['data']), 0)

        response = self.app.post_json('/tenders', {'data': test_tender_data})
        self.assertEqual(response.status, '201 Created')
        tender = response.json['data']
        dateModified = tender['dateModified']

        response = self.app.get('/tenders/{}'.format(tender['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['dateModified'], dateModified)

        response = self.app.patch_json('/tenders/{}'.format(
            tender['id']), {'data': {'procurementMethodRationale': 'Open'}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertNotEqual(response.json['data']['dateModified'], dateModified)
        tender = response.json['data']
        dateModified = tender['dateModified']

        response = self.app.get('/tenders/{}'.format(tender['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'], tender)
        self.assertEqual(response.json['data']['dateModified'], dateModified)

    def test_tender_not_found(self):
        response = self.app.get('/tenders')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json['data']), 0)

        response = self.app.get('/tenders/some_id', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'tender_id'}
        ])

        #response = self.app.put_json(
            #'/tenders/some_id', {'data': test_tender_data}, status=404)
        #self.assertEqual(response.status, '404 Not Found')
        #self.assertEqual(response.content_type, 'application/json')
        #self.assertEqual(response.json['status'], 'error')
        #self.assertEqual(response.json['errors'], [
            #{u'description': u'Not Found', u'location': u'url', u'name': u'tender_id'}
        #])

        response = self.app.patch_json(
            '/tenders/some_id', {'data': {}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'tender_id'}
        ])

    def test_tender_Administrator_change(self):
        response = self.app.post_json('/tenders', {'data': test_tender_data})
        self.assertEqual(response.status, '201 Created')
        tender = response.json['data']

        response = self.app.post_json('/tenders/{}/questions'.format(tender['id']), {'data': {'title': 'question title', 'description': 'question description', 'author': test_tender_data["procuringEntity"]}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        question = response.json['data']

        authorization = self.app.authorization
        self.app.authorization = ('Basic', ('administrator', ''))
        response = self.app.patch_json('/tenders/{}'.format(tender['id']), {'data': {'mode': u'test'}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['mode'], u'test')

        response = self.app.patch_json('/tenders/{}/questions/{}'.format(tender['id'], question['id']), {"data": {"answer": "answer"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'], [
            {"location": "url", "name": "role", "description": "Forbidden"}
        ])
        self.app.authorization = authorization

        response = self.app.post_json('/tenders', {'data': test_tender_data})
        self.assertEqual(response.status, '201 Created')
        tender = response.json['data']

        response = self.app.post_json('/tenders/{}/cancellations'.format(tender['id']), {'data': {'reason': 'cancellation reason', 'status': 'active'}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')

        self.app.authorization = ('Basic', ('administrator', ''))
        response = self.app.patch_json('/tenders/{}'.format(tender['id']), {'data': {'mode': u'test'}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['mode'], u'test')

    def test_required_field_deletion(self):
        response = self.app.post_json('/tenders', {'data': test_tender_data})
        self.assertEqual(response.status, '201 Created')
        tender = response.json['data']

        # TODO: Test all the required fields

        response = self.app.patch_json('/tenders/{}'.format(
            tender['id']), {'data': {'enquiryPeriod': {'startDate': None}}})
        self.assertNotEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('startDate', response.json['data']['enquiryPeriod'])

class TenderProcessTest(BaseTenderWebTest):
    setUp = BaseWebTest.setUp

    def test_invalid_tender_conditions(self):
        self.app.authorization = ('Basic', ('broker', ''))
        # empty tenders listing
        response = self.app.get('/tenders')
        self.assertEqual(response.json['data'], [])
        # create tender
        response = self.app.post_json('/tenders',
                                      {"data": test_tender_data})
        tender_id = self.tender_id = response.json['data']['id']
        owner_token = response.json['access']['token']
        # create compaint
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.post_json('/tenders/{}/complaints'.format(tender_id),
                                      {'data': {'title': 'invalid conditions', 'description': 'description', 'author': test_tender_data["procuringEntity"]}})
        complaint_id = response.json['data']['id']
        # create second compaint
        response = self.app.post_json('/tenders/{}/complaints'.format(tender_id),
                                      {'data': {'title': 'invalid conditions', 'description': 'description', 'author': test_tender_data["procuringEntity"]}})
        # switch to active.tendering
        self.set_status('active.tendering')
        # satisfying tender conditions complaint
        # XXX correct auth
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(tender_id, complaint_id, owner_token),
                                       {"data": {"status": "resolved", "resolution": "resolution text"}})
        # check status
        response = self.app.get('/tenders/{}'.format(tender_id))
        self.assertEqual(response.json['data']['status'], 'cancelled')

    def test_one_valid_bid_tender(self):
        self.app.authorization = ('Basic', ('broker', ''))
        # empty tenders listing
        response = self.app.get('/tenders')
        self.assertEqual(response.json['data'], [])
        # create tender
        response = self.app.post_json('/tenders',
                                      {"data": test_tender_data})
        tender_id = self.tender_id = response.json['data']['id']
        owner_token = response.json['access']['token']
        # switch to active.tendering
        response = self.set_status('active.tendering', {"auctionPeriod": {"startDate": (get_now() + timedelta(days=10)).isoformat()}})
        self.assertIn("auctionPeriod", response.json['data'])
        # create bid
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.post_json('/tenders/{}/bids'.format(tender_id),
                                      {'data': {'tenderers': [test_tender_data["procuringEntity"]], "value": {"amount": 500}}})
        # switch to active.qualification
        response = self.set_status('active.qualification', {"auctionPeriod": {"startDate": None}})
        self.assertNotIn("auctionPeriod", response.json['data'])
        # get awards
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.get('/tenders/{}/awards?acc_token={}'.format(tender_id, owner_token))
        # get pending award
        award_id = [i['id'] for i in response.json['data'] if i['status'] == 'pending'][0]
        # set award as active
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(tender_id, award_id, owner_token),
                                       {"data": {"status": "active"}})
        contract_id = response.json['data']['contracts'][0]['id']
        # after stand slill period
        self.app.authorization = ('Basic', ('chronograph', ''))
        self.set_status('complete', {'status': 'active.awarded'})
        # time travel
        tender = self.db.get(tender_id)
        for i in tender.get('awards', []):
            i['complaintPeriod']['endDate'] = i['complaintPeriod']['startDate']
        self.db.save(tender)
        # sign contract
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.patch_json('/tenders/{}/awards/{}/contracts/{}?acc_token={}'.format(tender_id, award_id, contract_id, owner_token), {"data": {"status": "active"}})
        # check status
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.get('/tenders/{}'.format(tender_id))
        self.assertEqual(response.json['data']['status'], 'complete')

    def test_one_invalid_bid_tender(self):
        self.app.authorization = ('Basic', ('broker', ''))
        # empty tenders listing
        response = self.app.get('/tenders')
        self.assertEqual(response.json['data'], [])
        # create tender
        response = self.app.post_json('/tenders',
                                      {"data": test_tender_data})
        tender_id = self.tender_id = response.json['data']['id']
        owner_token = response.json['access']['token']
        # switch to active.tendering
        self.set_status('active.tendering')
        # create bid
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.post_json('/tenders/{}/bids'.format(tender_id),
                                      {'data': {'tenderers': [test_tender_data["procuringEntity"]], "value": {"amount": 500}}})
        # switch to active.qualification
        self.set_status('active.qualification')
        # get awards
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.get('/tenders/{}/awards?acc_token={}'.format(tender_id, owner_token))
        # get pending award
        award_id = [i['id'] for i in response.json['data'] if i['status'] == 'pending'][0]
        # set award as unsuccessful
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(tender_id, award_id, owner_token),
                                       {"data": {"status": "unsuccessful"}})
        # set tender status after stand slill period
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json('/tenders/{}'.format(tender_id),
                                       {'data': {'status': 'unsuccessful'}})
        # check status
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.get('/tenders/{}'.format(tender_id))
        self.assertEqual(response.json['data']['status'], 'unsuccessful')

    def test_first_bid_tender(self):
        self.app.authorization = ('Basic', ('broker', ''))
        # empty tenders listing
        response = self.app.get('/tenders')
        self.assertEqual(response.json['data'], [])
        # create tender
        response = self.app.post_json('/tenders',
                                      {"data": test_tender_data})
        tender_id = self.tender_id = response.json['data']['id']
        owner_token = response.json['access']['token']
        # switch to active.tendering
        self.set_status('active.tendering')
        # create bid
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.post_json('/tenders/{}/bids'.format(tender_id),
                                      {'data': {'tenderers': [test_tender_data["procuringEntity"]], "value": {"amount": 450}}})
        bid_id = response.json['data']['id']
        bid_token = response.json['access']['token']
        # create second bid
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.post_json('/tenders/{}/bids'.format(tender_id),
                                      {'data': {'tenderers': [test_tender_data["procuringEntity"]], "value": {"amount": 475}}})
        # switch to active.auction
        self.set_status('active.auction')

        # get auction info
        self.app.authorization = ('Basic', ('auction', ''))
        response = self.app.get('/tenders/{}/auction'.format(tender_id))
        auction_bids_data = response.json['data']['bids']
        # posting auction urls
        response = self.app.patch_json('/tenders/{}/auction'.format(tender_id),
                                       {
                                           'data': {
                                               'auctionUrl': 'https://tender.auction.url',
                                               'bids': [
                                                   {
                                                       'id': i['id'],
                                                       'participationUrl': 'https://tender.auction.url/for_bid/{}'.format(i['id'])
                                                   }
                                                   for i in auction_bids_data
                                               ]
                                           }
        })
        # view bid participationUrl
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.get('/tenders/{}/bids/{}?acc_token={}'.format(tender_id, bid_id, bid_token))
        self.assertEqual(response.json['data']['participationUrl'], 'https://tender.auction.url/for_bid/{}'.format(bid_id))

        # posting auction results
        self.app.authorization = ('Basic', ('auction', ''))
        response = self.app.post_json('/tenders/{}/auction'.format(tender_id),
                                      {'data': {'bids': auction_bids_data}})
        # get awards
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.get('/tenders/{}/awards?acc_token={}'.format(tender_id, owner_token))
        # get pending award
        award_id = [i['id'] for i in response.json['data'] if i['status'] == 'pending'][0]
        # set award as unsuccessful
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(tender_id, award_id, owner_token),
                                       {"data": {"status": "unsuccessful"}})
        # get awards
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.get('/tenders/{}/awards?acc_token={}'.format(tender_id, owner_token))
        # get pending award
        award2_id = [i['id'] for i in response.json['data'] if i['status'] == 'pending'][0]
        self.assertNotEqual(award_id, award2_id)
        # create first award complaint
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.post_json('/tenders/{}/awards/{}/complaints?acc_token={}'.format(tender_id, award_id, bid_token),
                                      {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_tender_data["procuringEntity"]}})
        complaint_id = response.json['data']['id']
        # create first award complaint #2
        response = self.app.post_json('/tenders/{}/awards/{}/complaints?acc_token={}'.format(tender_id, award_id, bid_token),
                                      {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_tender_data["procuringEntity"]}})
        # satisfying award complaint
        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(tender_id, award_id, complaint_id, owner_token),
                                       {"data": {"status": "resolved", "resolution": "resolution text"}})
        # get awards
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.get('/tenders/{}/awards?acc_token={}'.format(tender_id, owner_token))
        # get pending award
        award_id = [i['id'] for i in response.json['data'] if i['status'] == 'pending'][0]
        # set award as active
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(tender_id, award_id, owner_token),
                                       {"data": {"status": "active"}})
        contract_id = response.json['data']['contracts'][0]['id']
        # after stand slill period
        self.app.authorization = ('Basic', ('chronograph', ''))
        self.set_status('complete', {'status': 'active.awarded'})
        # time travel
        tender = self.db.get(tender_id)
        for i in tender.get('awards', []):
            i['complaintPeriod']['endDate'] = i['complaintPeriod']['startDate']
        self.db.save(tender)
        # sign contract
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.patch_json('/tenders/{}/awards/{}/contracts/{}?acc_token={}'.format(tender_id, award_id, contract_id, owner_token), {"data": {"status": "active"}})
        # check status
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.get('/tenders/{}'.format(tender_id))
        self.assertEqual(response.json['data']['status'], 'complete')


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TenderProcessTest))
    suite.addTest(unittest.makeSuite(TenderResourceTest))
    suite.addTest(unittest.makeSuite(TenderTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
