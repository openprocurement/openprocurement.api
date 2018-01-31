# -*- coding: utf-8 -*-
import unittest

from openprocurement.api.tests.base import BaseTenderWebTest, test_tender_data, test_bids, test_lots, test_organization


class TenderAwardResourceTest(BaseTenderWebTest):
    #initial_data = tender_data
    initial_status = 'active.qualification'
    initial_bids = test_bids

    def test_create_tender_award_invalid(self):
        request_path = '/tenders/{}/awards'.format(self.tender_id)
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
            {u'description': u'Expecting value: line 1 column 1 (char 0)',
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

        response = self.app.post_json(
            request_path, {'not_data': {}}, status=422)
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

        response = self.app.post_json(request_path, {
                                      'data': {'suppliers': [{'identifier': 'invalid_value'}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': {u'identifier': [
                u'Please use a mapping for this field or Identifier instance instead of unicode.']}, u'location': u'body', u'name': u'suppliers'}
        ])

        response = self.app.post_json(request_path, {
                                      'data': {'suppliers': [{'identifier': {'id': 0}}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [{u'contactPoint': [u'This field is required.'], u'identifier': {u'scheme': [u'This field is required.']}, u'name': [u'This field is required.'], u'address': [u'This field is required.']}], u'location': u'body', u'name': u'suppliers'},
            {u'description': [u'This field is required.'], u'location': u'body', u'name': u'bid_id'}
        ])

        response = self.app.post_json(request_path, {'data': {'suppliers': [
                                      {'name': 'name', 'identifier': {'uri': 'invalid_value'}}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [{u'contactPoint': [u'This field is required.'], u'identifier': {u'scheme': [u'This field is required.'], u'id': [u'This field is required.'], u'uri': [u'Not a well formed URL.']}, u'address': [u'This field is required.']}], u'location': u'body', u'name': u'suppliers'},
            {u'description': [u'This field is required.'], u'location': u'body', u'name': u'bid_id'}
        ])

        response = self.app.post_json(request_path, {'data': {
            'suppliers': [test_organization],
            'status': 'pending',
            'bid_id': self.initial_bids[0]['id'],
            'lotID': '0' * 32
        }}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'lotID should be one of lots'], u'location': u'body', u'name': u'lotID'}
        ])

        response = self.app.post_json('/tenders/some_id/awards', {'data': {
                                      'suppliers': [test_organization], 'bid_id': self.initial_bids[0]['id']}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.get('/tenders/some_id/awards', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        self.set_status('complete')

        response = self.app.post_json('/tenders/{}/awards'.format(
            self.tender_id), {'data': {'suppliers': [test_organization], 'status': 'pending', 'bid_id': self.initial_bids[0]['id']}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't create award in current (complete) tender status")

    def test_create_tender_award(self):
        request_path = '/tenders/{}/awards'.format(self.tender_id)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization], 'status': 'pending', 'bid_id': self.initial_bids[0]['id']}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']
        self.assertEqual(award['suppliers'][0]['name'], test_organization['name'])
        self.assertIn('id', award)
        self.assertIn(award['id'], response.headers['Location'])

        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'][-1], award)

        response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, award['id']), {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['status'], u'active')

        response = self.app.get('/tenders/{}'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['status'], u'active.awarded')

        response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, award['id']), {"data": {"status": "cancelled"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['status'], u'cancelled')
        self.assertIn('Location', response.headers)

    def test_patch_tender_award(self):
        request_path = '/tenders/{}/awards'.format(self.tender_id)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization], 'status': u'pending', 'bid_id': self.initial_bids[0]['id'], "value": {"amount": 500}}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']

        #response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, award['id']), {"data": {"value": {"amount": 600}}})
        #self.assertEqual(response.status, '200 OK')
        #self.assertEqual(response.content_type, 'application/json')
        #self.assertEqual(response.json['data']["value"]["amount"], 600)

        response = self.app.patch_json('/tenders/{}/awards/some_id'.format(self.tender_id), {"data": {"status": "unsuccessful"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.patch_json('/tenders/some_id/awards/some_id', {"data": {"status": "unsuccessful"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, award['id']), {"data": {"awardStatus": "unsuccessful"}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'], [
            {"location": "body", "name": "awardStatus", "description": "Rogue field"}
        ])

        response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, award['id']), {"data": {"status": "unsuccessful"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('Location', response.headers)
        new_award_location = response.headers['Location']

        response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, award['id']), {"data": {"status": "pending"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update award in current (unsuccessful) status")

        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(len(response.json['data']), 2)
        self.assertIn(response.json['data'][1]['id'], new_award_location)
        new_award = response.json['data'][-1]

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(self.tender_id, new_award['id'], self.tender_token),
                                       {"data": {"title": "title", "description": "description"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['title'], 'title')
        self.assertEqual(response.json['data']['description'], 'description')

        response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, new_award['id']), {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(len(response.json['data']), 2)

        response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, new_award['id']), {"data": {"status": "cancelled"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('Location', response.headers)

        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(len(response.json['data']), 3)

        self.set_status('complete')

        response = self.app.get('/tenders/{}/awards/{}'.format(self.tender_id, award['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["value"]["amount"], 500)

        response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, award['id']), {"data": {"status": "unsuccessful"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update award in current (complete) tender status")

    def test_patch_tender_award_unsuccessful(self):
        request_path = '/tenders/{}/awards'.format(self.tender_id)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization], 'status': u'pending', 'bid_id': self.initial_bids[0]['id'], "value": {"amount": 500}}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']

        response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, award['id']), {"data": {"status": "unsuccessful"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('Location', response.headers)
        new_award_location = response.headers['Location']


        response = self.app.patch_json(new_award_location[-81:], {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertNotIn('Location', response.headers)

        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(len(response.json['data']), 2)

        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(self.tender_id, award['id']), {'data': {
            'title': 'complaint title',
            'description': 'complaint description',
            'author': test_organization,
            'status': 'claim'
        }})
        self.assertEqual(response.status, '201 Created')

        response = self.app.post_json('{}/complaints'.format(new_award_location[-81:]), {'data': {
            'title': 'complaint title',
            'description': 'complaint description',
            'author': test_organization
        }})
        self.assertEqual(response.status, '201 Created')

        response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, award['id']), {"data": {"status": "cancelled"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('Location', response.headers)
        new_award_location = response.headers['Location']

        response = self.app.patch_json(new_award_location[-81:], {"data": {"status": "unsuccessful"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('Location', response.headers)
        new_award_location = response.headers['Location']

        response = self.app.patch_json(new_award_location[-81:], {"data": {"status": "unsuccessful"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertNotIn('Location', response.headers)

        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(len(response.json['data']), 4)

    def test_get_tender_award(self):
        response = self.app.post_json('/tenders/{}/awards'.format(
            self.tender_id), {'data': {'suppliers': [test_organization], 'status': 'pending', 'bid_id': self.initial_bids[0]['id']}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']

        response = self.app.get('/tenders/{}/awards/{}'.format(self.tender_id, award['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        award_data = response.json['data']
        self.assertEqual(award_data, award)

        response = self.app.get('/tenders/{}/awards/some_id'.format(self.tender_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.get('/tenders/some_id/awards/some_id', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

    def test_patch_tender_award_Administrator_change(self):
        response = self.app.post_json('/tenders/{}/awards'.format(
            self.tender_id), {'data': {'suppliers': [test_organization], 'status': 'pending', 'bid_id': self.initial_bids[0]['id']}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']
        complaintPeriod = award['complaintPeriod'][u'startDate']

        authorization = self.app.authorization
        self.app.authorization = ('Basic', ('administrator', ''))
        response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, award['id']), {"data": {"complaintPeriod": {"endDate": award['complaintPeriod'][u'startDate']}}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn("endDate", response.json['data']['complaintPeriod'])
        self.assertEqual(response.json['data']['complaintPeriod']["endDate"], complaintPeriod)


class TenderLotAwardResourceTest(BaseTenderWebTest):
    initial_status = 'active.qualification'
    initial_lots = test_lots
    initial_bids = test_bids

    def test_create_tender_award(self):
        request_path = '/tenders/{}/awards'.format(self.tender_id)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization], 'status': 'pending', 'bid_id': self.initial_bids[0]['id']}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'], [
            {"location": "body", "name": "lotID", "description": ["This field is required."]}
        ])

        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization], 'status': 'pending', 'bid_id': self.initial_bids[0]['id'], 'lotID': self.initial_lots[0]['id']}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']
        self.assertEqual(award['suppliers'][0]['name'], test_organization['name'])
        self.assertEqual(award['lotID'], self.initial_lots[0]['id'])
        self.assertIn('id', award)
        self.assertIn(award['id'], response.headers['Location'])

        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'][-1], award)

        response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, award['id']), {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['status'], u'active')

        response = self.app.get('/tenders/{}'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['status'], u'active.awarded')

        response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, award['id']), {"data": {"status": "cancelled"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['status'], u'cancelled')
        self.assertIn('Location', response.headers)

    def test_patch_tender_award(self):
        request_path = '/tenders/{}/awards'.format(self.tender_id)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization], 'status': u'pending', 'bid_id': self.initial_bids[0]['id'], 'lotID': self.initial_lots[0]['id'], "value": {"amount": 500}}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']

        response = self.app.patch_json('/tenders/{}/awards/some_id'.format(self.tender_id), {"data": {"status": "unsuccessful"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.patch_json('/tenders/some_id/awards/some_id', {"data": {"status": "unsuccessful"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, award['id']), {"data": {"awardStatus": "unsuccessful"}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'], [
            {"location": "body", "name": "awardStatus", "description": "Rogue field"}
        ])

        response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, award['id']), {"data": {"status": "unsuccessful"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('Location', response.headers)
        new_award_location = response.headers['Location']

        response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, award['id']), {"data": {"status": "pending"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update award in current (unsuccessful) status")

        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(len(response.json['data']), 2)
        self.assertIn(response.json['data'][-1]['id'], new_award_location)
        new_award = response.json['data'][-1]

        response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, new_award['id']), {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(len(response.json['data']), 2)

        response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, new_award['id']), {"data": {"status": "cancelled"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('Location', response.headers)

        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(len(response.json['data']), 3)

        self.set_status('complete')

        response = self.app.get('/tenders/{}/awards/{}'.format(self.tender_id, award['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["value"]["amount"], 500)

        response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, award['id']), {"data": {"status": "unsuccessful"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update award in current (complete) tender status")

    def test_patch_tender_award_unsuccessful(self):
        request_path = '/tenders/{}/awards'.format(self.tender_id)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization], 'status': u'pending', 'bid_id': self.initial_bids[0]['id'], 'lotID': self.initial_lots[0]['id'], "value": {"amount": 500}}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']

        response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, award['id']), {"data": {"status": "unsuccessful"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('Location', response.headers)
        new_award_location = response.headers['Location']

        response = self.app.patch_json(new_award_location[-81:], {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertNotIn('Location', response.headers)

        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(len(response.json['data']), 2)

        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(self.tender_id, award['id']), {'data': {
            'title': 'complaint title',
            'description': 'complaint description',
            'author': test_organization,
            'status': 'claim'
        }})
        self.assertEqual(response.status, '201 Created')

        response = self.app.post_json('{}/complaints'.format(new_award_location[-81:]), {'data': {
            'title': 'complaint title',
            'description': 'complaint description',
            'author': test_organization
        }})
        self.assertEqual(response.status, '201 Created')

        response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, award['id']), {"data": {"status": "cancelled"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('Location', response.headers)
        new_award_location = response.headers['Location']

        response = self.app.patch_json(new_award_location[-81:], {"data": {"status": "unsuccessful"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('Location', response.headers)
        new_award_location = response.headers['Location']

        response = self.app.patch_json(new_award_location[-81:], {"data": {"status": "unsuccessful"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertNotIn('Location', response.headers)

        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(len(response.json['data']), 4)


class Tender2LotAwardResourceTest(BaseTenderWebTest):
    initial_status = 'active.qualification'
    initial_lots = 2 * test_lots
    initial_bids = test_bids

    def test_create_tender_award(self):
        request_path = '/tenders/{}/awards'.format(self.tender_id)
        response = self.app.post_json('/tenders/{}/cancellations'.format(self.tender_id), {'data': {
            'reason': 'cancellation reason',
            'status': 'active',
            "cancellationOf": "lot",
            "relatedLot": self.initial_lots[0]['id']
        }})
        self.assertEqual(response.status, '201 Created')

        response = self.app.post_json(request_path, {'data': {
            'suppliers': [test_organization],
            'status': 'pending',
            'bid_id': self.initial_bids[0]['id'],
            'lotID': self.initial_lots[0]['id']
        }}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can create award only in active lot status")

        response = self.app.post_json(request_path, {'data': {
            'suppliers': [test_organization],
            'status': 'pending',
            'bid_id': self.initial_bids[0]['id'],
            'lotID': self.initial_lots[1]['id']
        }})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']
        self.assertEqual(award['suppliers'][0]['name'], test_organization['name'])
        self.assertEqual(award['lotID'], self.initial_lots[1]['id'])
        self.assertIn('id', award)
        self.assertIn(award['id'], response.headers['Location'])

        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'][-1], award)

        response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, award['id']), {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['status'], u'active')

        response = self.app.get('/tenders/{}'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['status'], u'active.awarded')

        response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, award['id']), {"data": {"status": "cancelled"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['status'], u'cancelled')
        self.assertIn('Location', response.headers)

    def test_patch_tender_award(self):
        request_path = '/tenders/{}/awards'.format(self.tender_id)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization], 'status': u'pending', 'bid_id': self.initial_bids[0]['id'], 'lotID': self.initial_lots[0]['id'], "value": {"amount": 500}}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']

        response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, award['id']), {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(len(response.json['data']), 2)
        new_award = response.json['data'][-1]

        response = self.app.post_json('/tenders/{}/cancellations'.format(self.tender_id), {'data': {
            'reason': 'cancellation reason',
            'status': 'active',
            "cancellationOf": "lot",
            "relatedLot": self.initial_lots[1]['id']
        }})
        self.assertEqual(response.status, '201 Created')

        response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, new_award['id']), {"data": {"status": "unsuccessful"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can update award only in active lot status")


class TenderAwardComplaintResourceTest(BaseTenderWebTest):
    #initial_data = tender_data
    initial_status = 'active.qualification'
    initial_bids = test_bids

    def setUp(self):
        super(TenderAwardComplaintResourceTest, self).setUp()
        # Create award
        response = self.app.post_json('/tenders/{}/awards'.format(
            self.tender_id), {'data': {'suppliers': [test_organization], 'status': 'pending', 'bid_id': self.initial_bids[0]['id']}})
        award = response.json['data']
        self.award_id = award['id']

    def test_create_tender_award_complaint_invalid(self):
        response = self.app.post_json('/tenders/some_id/awards/some_id/complaints', {
                                      'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_organization}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'tender_id'}
        ])

        request_path = '/tenders/{}/awards/{}/complaints'.format(self.tender_id, self.award_id)

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
            {u'description': u'Expecting value: line 1 column 1 (char 0)',
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

        response = self.app.post_json(
            request_path, {'not_data': {}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Data not available',
                u'location': u'body', u'name': u'data'}
        ])

        response = self.app.post_json(request_path, {'data': {}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'This field is required.'], u'location': u'body', u'name': u'author'},
            {u'description': [u'This field is required.'], u'location': u'body', u'name': u'title'},
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

        response = self.app.post_json(request_path, {
                                      'data': {'author': {'identifier': 'invalid_value'}}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': {u'identifier': [
                u'Please use a mapping for this field or Identifier instance instead of unicode.']}, u'location': u'body', u'name': u'author'}
        ])

        response = self.app.post_json(request_path, {
                                      'data': {'title': 'complaint title', 'description': 'complaint description', 'author': {'identifier': {'id': 0}}}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': {u'contactPoint': [u'This field is required.'], u'identifier': {u'scheme': [u'This field is required.']}, u'name': [u'This field is required.'], u'address': [u'This field is required.']}, u'location': u'body', u'name': u'author'}
        ])

        response = self.app.post_json(request_path, {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': {
            'name': 'name', 'identifier': {'uri': 'invalid_value'}}}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': {u'contactPoint': [u'This field is required.'], u'identifier': {u'scheme': [u'This field is required.'], u'id': [u'This field is required.'], u'uri': [u'Not a well formed URL.']}, u'address': [u'This field is required.']}, u'location': u'body', u'name': u'author'}
        ])

    def test_create_tender_award_complaint(self):
        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(
            self.tender_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_organization, 'status': 'claim'}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']
        self.assertEqual(complaint['author']['name'], test_organization['name'])
        self.assertIn('id', complaint)
        self.assertIn(complaint['id'], response.headers['Location'])

        self.set_status('active.awarded')

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.award_id, complaint['id'], self.tender_token), {"data": {
            "status": "answered",
            "resolutionType": "invalid",
            "resolution": "spam 100% " * 3
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "answered")
        self.assertEqual(response.json['data']["resolutionType"], "invalid")
        self.assertEqual(response.json['data']["resolution"], "spam 100% " * 3)

        response = self.app.get('/tenders/{}'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], 'active.awarded')

        self.set_status('unsuccessful')

        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(
            self.tender_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_organization}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add complaint in current (unsuccessful) tender status")

    def test_patch_tender_award_complaint(self):
        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(
            self.tender_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_organization}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']
        owner_token = response.json['access']['token']

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.award_id, complaint['id'], self.tender_token), {"data": {
            "status": "cancelled",
            "cancellationReason": "reason"
        }}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Forbidden")

        response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, self.award_id, complaint['id']), {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "active")

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.award_id, complaint['id'], owner_token), {"data": {
            "title": "claim title",
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']["title"], "claim title")

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.award_id, complaint['id'], owner_token), {"data": {
            "status": "claim",
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']["status"], "claim")

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.award_id, complaint['id'], self.tender_token), {"data": {
            "resolution": "changing rules"
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["resolution"], "changing rules")

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.award_id, complaint['id'], self.tender_token), {"data": {
            "status": "answered",
            "resolutionType": "resolved",
            "resolution": "resolution text " * 2
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "answered")
        self.assertEqual(response.json['data']["resolutionType"], "resolved")
        self.assertEqual(response.json['data']["resolution"], "resolution text " * 2)

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.award_id, complaint['id'], owner_token), {"data": {
            "satisfied": False
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["satisfied"], False)

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.award_id, complaint['id'], owner_token), {"data": {
            "status": "resolved"
        }}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update complaint")

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.award_id, complaint['id'], owner_token), {"data": {
            "status": "pending"
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "pending")

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.award_id, complaint['id'], owner_token), {"data": {
            "status": "cancelled",
            "cancellationReason": "reason"
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "cancelled")
        self.assertEqual(response.json['data']["cancellationReason"], "reason")

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/some_id'.format(self.tender_id, self.award_id), {"data": {"status": "resolved", "resolution": "resolution text"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.patch_json('/tenders/some_id/awards/some_id/complaints/some_id', {"data": {"status": "resolved", "resolution": "resolution text"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.award_id, complaint['id'], owner_token), {"data": {
            "status": "cancelled",
            "cancellationReason": "reason"
        }}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update complaint in current (cancelled) status")

        response = self.app.patch_json('/tenders/{}/awards/some_id/complaints/some_id'.format(self.tender_id), {"data": {"status": "resolved", "resolution": "resolution text"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}'.format(self.tender_id, self.award_id, complaint['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "cancelled")
        self.assertEqual(response.json['data']["cancellationReason"], "reason")
        self.assertEqual(response.json['data']["resolutionType"], "resolved")
        self.assertEqual(response.json['data']["resolution"], "resolution text " * 2)

        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(
            self.tender_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_organization}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']
        owner_token = response.json['access']['token']

        self.set_status('complete')

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.award_id, complaint['id'], owner_token), {"data": {
            "status": "claim",
        }}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update complaint in current (complete) tender status")

    def test_review_tender_award_complaint(self):
        complaints = []
        for i in range(3):
            response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(self.tender_id, self.award_id), {'data': {
                'title': 'complaint title',
                'description': 'complaint description',
                'author': test_organization,
                'status': 'claim'
            }})
            self.assertEqual(response.status, '201 Created')
            self.assertEqual(response.content_type, 'application/json')
            complaint = response.json['data']
            owner_token = response.json['access']['token']
            complaints.append(complaint)

            response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.award_id, complaint['id'], self.tender_token), {"data": {
                "status": "answered",
                "resolutionType": "resolved",
                "resolution": "resolution text " * 2
            }})
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.json['data']["status"], "answered")
            self.assertEqual(response.json['data']["resolutionType"], "resolved")
            self.assertEqual(response.json['data']["resolution"], "resolution text " * 2)

            response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.award_id, complaint['id'], owner_token), {"data": {
                "satisfied": False,
                "status": "pending"
            }})
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.json['data']["status"], "pending")

        self.app.authorization = ('Basic', ('reviewer', ''))
        for complaint, status in zip(complaints, ['invalid', 'resolved', 'declined']):
            response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}'.format(self.tender_id, self.award_id, complaint['id']), {"data": {
                "decision": '{} complaint'.format(status)
            }})
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.json['data']["decision"], '{} complaint'.format(status))

            response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}'.format(self.tender_id, self.award_id, complaint['id']), {"data": {
                "status": status
            }})
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.json['data']["status"], status)

    def test_get_tender_award_complaint(self):
        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(
            self.tender_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_organization}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}'.format(self.tender_id, self.award_id, complaint['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'], complaint)

        response = self.app.get('/tenders/{}/awards/{}/complaints/some_id'.format(self.tender_id, self.award_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.get('/tenders/some_id/awards/some_id/complaints/some_id', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

    def test_get_tender_award_complaints(self):
        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(
            self.tender_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_organization}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']

        response = self.app.get('/tenders/{}/awards/{}/complaints'.format(self.tender_id, self.award_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'][0], complaint)

        response = self.app.get('/tenders/some_id/awards/some_id/complaints', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        tender = self.db.get(self.tender_id)
        for i in tender.get('awards', []):
            i['complaintPeriod']['endDate'] = i['complaintPeriod']['startDate']
        self.db.save(tender)

        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(
            self.tender_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_organization}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can add complaint only in complaintPeriod")


class TenderLotAwardComplaintResourceTest(BaseTenderWebTest):
    #initial_data = tender_data
    initial_status = 'active.qualification'
    initial_lots = test_lots
    initial_bids = test_bids

    def setUp(self):
        super(TenderLotAwardComplaintResourceTest, self).setUp()
        # Create award
        bid = self.initial_bids[0]
        response = self.app.post_json('/tenders/{}/awards'.format(
            self.tender_id), {'data': {'suppliers': [test_organization], 'status': 'pending', 'bid_id': bid['id'], 'lotID': bid['lotValues'][0]['relatedLot']}})
        award = response.json['data']
        self.award_id = award['id']

    def test_create_tender_award_complaint(self):
        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(
            self.tender_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_organization, 'status': 'claim'}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']
        self.assertEqual(complaint['author']['name'], test_organization['name'])
        self.assertIn('id', complaint)
        self.assertIn(complaint['id'], response.headers['Location'])

        self.set_status('active.awarded')

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.award_id, complaint['id'], self.tender_token), {"data": {
            "status": "answered",
            "resolutionType": "invalid",
            "resolution": "spam 100% " * 3
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "answered")
        self.assertEqual(response.json['data']["resolutionType"], "invalid")
        self.assertEqual(response.json['data']["resolution"], "spam 100% " * 3)

        response = self.app.get('/tenders/{}'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], 'active.awarded')

        self.set_status('unsuccessful')

        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(
            self.tender_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_organization}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add complaint in current (unsuccessful) tender status")

    def test_patch_tender_award_complaint(self):
        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(
            self.tender_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_organization}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']
        owner_token = response.json['access']['token']

        response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, self.award_id, complaint['id']), {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "active")

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.award_id, complaint['id'], owner_token), {"data": {
            "status": "claim"
        }})

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.award_id, complaint['id'], self.tender_token), {"data": {
            "status": "answered",
            "resolutionType": "resolved",
            "resolution": "resolution text " * 2
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "answered")
        self.assertEqual(response.json['data']["resolutionType"], "resolved")
        self.assertEqual(response.json['data']["resolution"], "resolution text " * 2)

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.award_id, complaint['id'], owner_token), {"data": {
            "satisfied": False,
            "status": "pending",
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "pending")

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.award_id, complaint['id'], owner_token), {"data": {"status": "cancelled", "cancellationReason": "reason"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "cancelled")
        self.assertEqual(response.json['data']["cancellationReason"], "reason")

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/some_id'.format(self.tender_id, self.award_id), {"data": {"status": "resolved", "resolution": "resolution text"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.patch_json('/tenders/some_id/awards/some_id/complaints/some_id', {"data": {"status": "resolved", "resolution": "resolution text"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.award_id, complaint['id'], owner_token), {"data": {
            "status": "cancelled",
            "cancellationReason": "reason"
        }}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update complaint in current (cancelled) status")

        response = self.app.patch_json('/tenders/{}/awards/some_id/complaints/some_id'.format(self.tender_id), {"data": {"status": "resolved", "resolution": "resolution text"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}'.format(self.tender_id, self.award_id, complaint['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "cancelled")
        self.assertEqual(response.json['data']["cancellationReason"], "reason")
        self.assertEqual(response.json['data']["resolutionType"], "resolved")
        self.assertEqual(response.json['data']["resolution"], "resolution text " * 2)

        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(
            self.tender_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_organization}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']
        owner_token = response.json['access']['token']

        self.set_status('complete')

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.award_id, complaint['id'], owner_token), {"data": {
            "status": "claim",
        }}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update complaint in current (complete) tender status")

    def test_get_tender_award_complaint(self):
        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(
            self.tender_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_organization}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}'.format(self.tender_id, self.award_id, complaint['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'], complaint)

        response = self.app.get('/tenders/{}/awards/{}/complaints/some_id'.format(self.tender_id, self.award_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.get('/tenders/some_id/awards/some_id/complaints/some_id', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

    def test_get_tender_award_complaints(self):
        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(
            self.tender_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_organization}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']

        response = self.app.get('/tenders/{}/awards/{}/complaints'.format(self.tender_id, self.award_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'][0], complaint)

        response = self.app.get('/tenders/some_id/awards/some_id/complaints', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        tender = self.db.get(self.tender_id)
        for i in tender.get('awards', []):
            i['complaintPeriod']['endDate'] = i['complaintPeriod']['startDate']
        self.db.save(tender)

        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(
            self.tender_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_organization}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can add complaint only in complaintPeriod")


class Tender2LotAwardComplaintResourceTest(TenderLotAwardComplaintResourceTest):
    initial_lots = 2 * test_lots

    def test_create_tender_award_complaint(self):
        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(
            self.tender_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_organization, 'status': 'claim'}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']
        self.assertEqual(complaint['author']['name'], test_organization['name'])
        self.assertIn('id', complaint)
        self.assertIn(complaint['id'], response.headers['Location'])

        self.set_status('active.awarded')

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.award_id, complaint['id'], self.tender_token), {"data": {
            "status": "answered",
            "resolutionType": "invalid",
            "resolution": "spam 100% " * 3
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "answered")
        self.assertEqual(response.json['data']["resolutionType"], "invalid")
        self.assertEqual(response.json['data']["resolution"], "spam 100% " * 3)

        response = self.app.get('/tenders/{}'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], 'active.awarded')

        response = self.app.post_json('/tenders/{}/cancellations'.format(self.tender_id), {'data': {
            'reason': 'cancellation reason',
            'status': 'active',
            "cancellationOf": "lot",
            "relatedLot": self.initial_lots[0]['id']
        }})
        self.assertEqual(response.status, '201 Created')

        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(
            self.tender_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_organization}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can add complaint only in active lot status")

    def test_patch_tender_award_complaint(self):
        response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, self.award_id), {"data": {"status": "unsuccessful"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "unsuccessful")

        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(
            self.tender_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_organization}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']
        owner_token = response.json['access']['token']

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.award_id, complaint['id'], owner_token), {"data": {
            "status": "claim"
        }})

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.award_id, complaint['id'], self.tender_token), {"data": {
            "status": "answered",
            "resolutionType": "resolved",
            "resolution": "resolution text " * 2
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "answered")
        self.assertEqual(response.json['data']["resolutionType"], "resolved")
        self.assertEqual(response.json['data']["resolution"], "resolution text " * 2)

        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(self.tender_id, self.award_id), {'data': {
            'title': 'complaint title',
            'description': 'complaint description',
            'author': test_organization,
            'status': 'claim'
        }})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']

        response = self.app.post_json('/tenders/{}/cancellations'.format(self.tender_id), {'data': {
            'reason': 'cancellation reason',
            'status': 'active',
            "cancellationOf": "lot",
            "relatedLot": self.initial_lots[0]['id']
        }})
        self.assertEqual(response.status, '201 Created')

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.award_id, complaint['id'], self.tender_token), {"data": {
            "status": "answered",
            "resolutionType": "resolved",
            "resolution": "resolution text"
        }}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can update complaint only in active lot status")


class TenderAwardComplaintDocumentResourceTest(BaseTenderWebTest):
    initial_status = 'active.qualification'
    initial_bids = test_bids

    def setUp(self):
        super(TenderAwardComplaintDocumentResourceTest, self).setUp()
        # Create award
        response = self.app.post_json('/tenders/{}/awards'.format(
            self.tender_id), {'data': {'suppliers': [test_organization], 'status': 'pending', 'bid_id': self.initial_bids[0]['id']}})
        award = response.json['data']
        self.award_id = award['id']
        # Create complaint for award
        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(
            self.tender_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_organization}})
        complaint = response.json['data']
        self.complaint_id = complaint['id']
        self.complaint_owner_token = response.json['access']['token']

    def test_not_found(self):
        response = self.app.post('/tenders/some_id/awards/some_id/complaints/some_id/documents', status=404, upload_files=[
                                 ('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.post('/tenders/{}/awards/some_id/complaints/some_id/documents'.format(self.tender_id), status=404, upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.post('/tenders/{}/awards/{}/complaints/some_id/documents'.format(self.tender_id, self.award_id), status=404, upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.post('/tenders/{}/awards/{}/complaints/{}/documents'.format(self.tender_id, self.award_id, self.complaint_id), status=404, upload_files=[
                                 ('invalid_value', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'body', u'name': u'file'}
        ])

        response = self.app.get('/tenders/some_id/awards/some_id/complaints/some_id/documents', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.get('/tenders/{}/awards/some_id/complaints/some_id/documents'.format(self.tender_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.get('/tenders/{}/awards/{}/complaints/some_id/documents'.format(self.tender_id, self.award_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.get('/tenders/some_id/awards/some_id/complaints/some_id/documents/some_id', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.get('/tenders/{}/awards/some_id/complaints/some_id/documents/some_id'.format(self.tender_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.get('/tenders/{}/awards/{}/complaints/some_id/documents/some_id'.format(self.tender_id, self.award_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}/documents/some_id'.format(self.tender_id, self.award_id, self.complaint_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'document_id'}
        ])

        response = self.app.put('/tenders/some_id/awards/some_id/complaints/some_id/documents/some_id', status=404,
                                upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.put('/tenders/{}/awards/some_id/complaints/some_id/documents/some_id'.format(self.tender_id), status=404,
                                upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.put('/tenders/{}/awards/{}/complaints/some_id/documents/some_id'.format(self.tender_id, self.award_id), status=404, upload_files=[
                                ('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.put('/tenders/{}/awards/{}/complaints/{}/documents/some_id'.format(
            self.tender_id, self.award_id, self.complaint_id), status=404, upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'document_id'}
        ])

    def test_create_tender_award_complaint_document(self):
        response = self.app.post('/tenders/{}/awards/{}/complaints/{}/documents'.format(
            self.tender_id, self.award_id, self.complaint_id), upload_files=[('file', 'name.doc', 'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add document in current (draft) complaint status")

        response = self.app.post('/tenders/{}/awards/{}/complaints/{}/documents?acc_token={}'.format(
            self.tender_id, self.award_id, self.complaint_id, self.complaint_owner_token), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])
        self.assertEqual('name.doc', response.json["data"]["title"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}/documents'.format(self.tender_id, self.award_id, self.complaint_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}/documents?all=true'.format(self.tender_id, self.award_id, self.complaint_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}/documents/{}?download=some_id'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'download'}
        ])

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}/documents/{}?{}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 7)
        self.assertEqual(response.body, 'content')

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}/documents/{}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])

        self.set_status('complete')

        response = self.app.post('/tenders/{}/awards/{}/complaints/{}/documents'.format(
            self.tender_id, self.award_id, self.complaint_id), upload_files=[('file', 'name.doc', 'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add document in current (complete) tender status")

    def test_put_tender_award_complaint_document(self):
        response = self.app.post('/tenders/{}/awards/{}/complaints/{}/documents?acc_token={}'.format(
            self.tender_id, self.award_id, self.complaint_id, self.complaint_owner_token), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.put('/tenders/{}/awards/{}/complaints/{}/documents/{}'.format(self.tender_id, self.award_id, self.complaint_id, doc_id),
                                status=404,
                                upload_files=[('invalid_name', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'body', u'name': u'file'}
        ])

        response = self.app.put('/tenders/{}/awards/{}/complaints/{}/documents/{}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id), upload_files=[('file', 'name.doc', 'content2')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can update document only author")

        response = self.app.put('/tenders/{}/awards/{}/complaints/{}/documents/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id, self.complaint_owner_token), upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}/documents/{}?{}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 8)
        self.assertEqual(response.body, 'content2')

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}/documents/{}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])

        response = self.app.put('/tenders/{}/awards/{}/complaints/{}/documents/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id, self.complaint_owner_token), 'content3', content_type='application/msword')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}/documents/{}?{}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 8)
        self.assertEqual(response.body, 'content3')

        self.set_status('complete')

        response = self.app.put('/tenders/{}/awards/{}/complaints/{}/documents/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id, self.complaint_owner_token), upload_files=[('file', 'name.doc', 'content3')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current (complete) tender status")

    def test_patch_tender_award_complaint_document(self):
        response = self.app.post('/tenders/{}/awards/{}/complaints/{}/documents?acc_token={}'.format(
            self.tender_id, self.award_id, self.complaint_id, self.complaint_owner_token), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}/documents/{}'.format(self.tender_id, self.award_id, self.complaint_id, doc_id), {"data": {"description": "document description"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can update document only author")

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}/documents/{}?acc_token={}'.format(self.tender_id, self.award_id, self.complaint_id, doc_id, self.complaint_owner_token), {"data": {"description": "document description"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}/documents/{}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('document description', response.json["data"]["description"])

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.award_id, self.complaint_id, self.complaint_owner_token), {"data": {
            "status": "claim",
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']["status"], "claim")

        response = self.app.put('/tenders/{}/awards/{}/complaints/{}/documents/{}?acc_token={}'.format(self.tender_id, self.award_id, self.complaint_id, doc_id, self.complaint_owner_token), 'content', content_type='application/msword', status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current (claim) complaint status")

        self.set_status('complete')

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}/documents/{}?acc_token={}'.format(self.tender_id, self.award_id, self.complaint_id, doc_id, self.complaint_owner_token), {"data": {"description": "document description"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current (complete) tender status")


class Tender2LotAwardComplaintDocumentResourceTest(BaseTenderWebTest):
    initial_status = 'active.qualification'
    initial_bids = test_bids
    initial_lots = 2 * test_lots

    def setUp(self):
        super(Tender2LotAwardComplaintDocumentResourceTest, self).setUp()
        # Create award
        bid = self.initial_bids[0]
        response = self.app.post_json('/tenders/{}/awards'.format(
            self.tender_id), {'data': {'suppliers': [test_organization], 'status': 'pending', 'bid_id': bid['id'], 'lotID': bid['lotValues'][0]['relatedLot']}})
        award = response.json['data']
        self.award_id = award['id']
        # Create complaint for award
        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(
            self.tender_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_organization}})
        complaint = response.json['data']
        self.complaint_id = complaint['id']
        self.complaint_owner_token = response.json['access']['token']

    def test_create_tender_award_complaint_document(self):
        response = self.app.post('/tenders/{}/awards/{}/complaints/{}/documents'.format(
            self.tender_id, self.award_id, self.complaint_id), upload_files=[('file', 'name.doc', 'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add document in current (draft) complaint status")

        response = self.app.post('/tenders/{}/awards/{}/complaints/{}/documents?acc_token={}'.format(
            self.tender_id, self.award_id, self.complaint_id, self.complaint_owner_token), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])
        self.assertEqual('name.doc', response.json["data"]["title"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}/documents'.format(self.tender_id, self.award_id, self.complaint_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}/documents?all=true'.format(self.tender_id, self.award_id, self.complaint_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}/documents/{}?download=some_id'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'download'}
        ])

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}/documents/{}?{}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 7)
        self.assertEqual(response.body, 'content')

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}/documents/{}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])

        response = self.app.post_json('/tenders/{}/cancellations'.format(self.tender_id), {'data': {
            'reason': 'cancellation reason',
            'status': 'active',
            "cancellationOf": "lot",
            "relatedLot": self.initial_lots[0]['id']
        }})
        self.assertEqual(response.status, '201 Created')

        response = self.app.post('/tenders/{}/awards/{}/complaints/{}/documents'.format(
            self.tender_id, self.award_id, self.complaint_id), upload_files=[('file', 'name.doc', 'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can add document only in active lot status")

    def test_put_tender_award_complaint_document(self):
        response = self.app.post('/tenders/{}/awards/{}/complaints/{}/documents?acc_token={}'.format(
            self.tender_id, self.award_id, self.complaint_id, self.complaint_owner_token), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.put('/tenders/{}/awards/{}/complaints/{}/documents/{}'.format(self.tender_id, self.award_id, self.complaint_id, doc_id),
                                status=404,
                                upload_files=[('invalid_name', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'body', u'name': u'file'}
        ])

        response = self.app.put('/tenders/{}/awards/{}/complaints/{}/documents/{}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id), upload_files=[('file', 'name.doc', 'content2')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can update document only author")

        response = self.app.put('/tenders/{}/awards/{}/complaints/{}/documents/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id, self.complaint_owner_token), upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}/documents/{}?{}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 8)
        self.assertEqual(response.body, 'content2')

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}/documents/{}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])

        response = self.app.put('/tenders/{}/awards/{}/complaints/{}/documents/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id, self.complaint_owner_token), 'content3', content_type='application/msword')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}/documents/{}?{}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 8)
        self.assertEqual(response.body, 'content3')

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.award_id, self.complaint_id, self.complaint_owner_token), {"data": {
            "status": "claim",
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']["status"], "claim")

        response = self.app.put('/tenders/{}/awards/{}/complaints/{}/documents/{}?acc_token={}'.format(self.tender_id, self.award_id, self.complaint_id, doc_id, self.complaint_owner_token), 'content', content_type='application/msword', status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current (claim) complaint status")

        response = self.app.post_json('/tenders/{}/cancellations'.format(self.tender_id), {'data': {
            'reason': 'cancellation reason',
            'status': 'active',
            "cancellationOf": "lot",
            "relatedLot": self.initial_lots[0]['id']
        }})
        self.assertEqual(response.status, '201 Created')

        response = self.app.put('/tenders/{}/awards/{}/complaints/{}/documents/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id, self.complaint_owner_token), upload_files=[('file', 'name.doc', 'content3')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can update document only in active lot status")

    def test_patch_tender_award_complaint_document(self):
        response = self.app.post('/tenders/{}/awards/{}/complaints/{}/documents?acc_token={}'.format(
            self.tender_id, self.award_id, self.complaint_id, self.complaint_owner_token), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}/documents/{}'.format(self.tender_id, self.award_id, self.complaint_id, doc_id), {"data": {"description": "document description"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can update document only author")

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}/documents/{}?acc_token={}'.format(self.tender_id, self.award_id, self.complaint_id, doc_id, self.complaint_owner_token), {"data": {"description": "document description"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}/documents/{}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('document description', response.json["data"]["description"])

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.award_id, self.complaint_id, self.complaint_owner_token), {"data": {
            "status": "claim",
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']["status"], "claim")

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}/documents/{}?acc_token={}'.format(self.tender_id, self.award_id, self.complaint_id, doc_id, self.complaint_owner_token), {"data": {"description": "document description"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current (claim) complaint status")

        response = self.app.post_json('/tenders/{}/cancellations'.format(self.tender_id), {'data': {
            'reason': 'cancellation reason',
            'status': 'active',
            "cancellationOf": "lot",
            "relatedLot": self.initial_lots[0]['id']
        }})
        self.assertEqual(response.status, '201 Created')

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}/documents/{}?acc_token={}'.format(self.tender_id, self.award_id, self.complaint_id, doc_id, self.complaint_owner_token), {"data": {"description": "document description"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can update document only in active lot status")


class TenderAwardDocumentResourceTest(BaseTenderWebTest):
    initial_status = 'active.qualification'
    initial_bids = test_bids

    def setUp(self):
        super(TenderAwardDocumentResourceTest, self).setUp()
        # Create award
        response = self.app.post_json('/tenders/{}/awards'.format(
            self.tender_id), {'data': {'suppliers': [test_organization], 'status': 'pending', 'bid_id': self.initial_bids[0]['id']}})
        award = response.json['data']
        self.award_id = award['id']

    def test_not_found(self):
        response = self.app.post('/tenders/some_id/awards/some_id/documents', status=404, upload_files=[
                                 ('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.post('/tenders/{}/awards/some_id/documents'.format(self.tender_id), status=404, upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.post('/tenders/{}/awards/{}/documents'.format(self.tender_id, self.award_id), status=404, upload_files=[
                                 ('invalid_value', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'body', u'name': u'file'}
        ])

        response = self.app.get('/tenders/some_id/awards/some_id/documents', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.get('/tenders/{}/awards/some_id/documents'.format(self.tender_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.get('/tenders/some_id/awards/some_id/documents/some_id', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.get('/tenders/{}/awards/some_id/documents/some_id'.format(self.tender_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.get('/tenders/{}/awards/{}/documents/some_id'.format(self.tender_id, self.award_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'document_id'}
        ])

        response = self.app.put('/tenders/some_id/awards/some_id/documents/some_id', status=404,
                                upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.put('/tenders/{}/awards/some_id/documents/some_id'.format(self.tender_id), status=404,
                                upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.put('/tenders/{}/awards/{}/documents/some_id'.format(
            self.tender_id, self.award_id), status=404, upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'document_id'}
        ])

    def test_create_tender_award_document(self):
        response = self.app.post('/tenders/{}/awards/{}/documents'.format(
            self.tender_id, self.award_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])
        self.assertEqual('name.doc', response.json["data"]["title"])
        if self.docservice:
            self.assertIn('Signature=', response.json["data"]["url"])
            self.assertIn('KeyID=', response.json["data"]["url"])
            self.assertNotIn('Expires=', response.json["data"]["url"])
            key = response.json["data"]["url"].split('/')[-1].split('?')[0]
            tender = self.db.get(self.tender_id)
            self.assertIn(key, tender['awards'][-1]['documents'][-1]["url"])
            self.assertIn('Signature=', tender['awards'][-1]['documents'][-1]["url"])
            self.assertIn('KeyID=', tender['awards'][-1]['documents'][-1]["url"])
            self.assertNotIn('Expires=', tender['awards'][-1]['documents'][-1]["url"])
        else:
            key = response.json["data"]["url"].split('?')[-1].split('=')[-1]

        response = self.app.get('/tenders/{}/awards/{}/documents'.format(self.tender_id, self.award_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/tenders/{}/awards/{}/documents?all=true'.format(self.tender_id, self.award_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/tenders/{}/awards/{}/documents/{}?download=some_id'.format(
            self.tender_id, self.award_id, doc_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'download'}
        ])

        if self.docservice:
            response = self.app.get('/tenders/{}/awards/{}/documents/{}?download={}'.format(
                self.tender_id, self.award_id, doc_id, key))
            self.assertEqual(response.status, '302 Moved Temporarily')
            self.assertIn('http://localhost/get/', response.location)
            self.assertIn('Signature=', response.location)
            self.assertIn('KeyID=', response.location)
            self.assertNotIn('Expires=', response.location)
        else:
            response = self.app.get('/tenders/{}/awards/{}/documents/{}?download={}'.format(
                self.tender_id, self.award_id, doc_id, key))
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/msword')
            self.assertEqual(response.content_length, 7)
            self.assertEqual(response.body, 'content')

        response = self.app.get('/tenders/{}/awards/{}/documents/{}'.format(
            self.tender_id, self.award_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])

        self.set_status('complete')

        response = self.app.post('/tenders/{}/awards/{}/documents'.format(
            self.tender_id, self.award_id), upload_files=[('file', 'name.doc', 'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add document in current (complete) tender status")

    def test_put_tender_award_document(self):
        response = self.app.post('/tenders/{}/awards/{}/documents'.format(
            self.tender_id, self.award_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.put('/tenders/{}/awards/{}/documents/{}'.format(self.tender_id, self.award_id, doc_id),
                                status=404,
                                upload_files=[('invalid_name', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'body', u'name': u'file'}
        ])

        response = self.app.put('/tenders/{}/awards/{}/documents/{}'.format(
            self.tender_id, self.award_id, doc_id), upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        if self.docservice:
            self.assertIn('Signature=', response.json["data"]["url"])
            self.assertIn('KeyID=', response.json["data"]["url"])
            self.assertNotIn('Expires=', response.json["data"]["url"])
            key = response.json["data"]["url"].split('/')[-1].split('?')[0]
            tender = self.db.get(self.tender_id)
            self.assertIn(key, tender['awards'][-1]['documents'][-1]["url"])
            self.assertIn('Signature=', tender['awards'][-1]['documents'][-1]["url"])
            self.assertIn('KeyID=', tender['awards'][-1]['documents'][-1]["url"])
            self.assertNotIn('Expires=', tender['awards'][-1]['documents'][-1]["url"])
        else:
            key = response.json["data"]["url"].split('?')[-1].split('=')[-1]

        response = self.app.get('/tenders/{}/awards/{}/documents/{}?download={}'.format(
            self.tender_id, self.award_id, doc_id, key))
        if self.docservice:
            self.assertEqual(response.status, '302 Moved Temporarily')
            self.assertIn('http://localhost/get/', response.location)
            self.assertIn('Signature=', response.location)
            self.assertIn('KeyID=', response.location)
            self.assertNotIn('Expires=', response.location)
        else:
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/msword')
            self.assertEqual(response.content_length, 8)
            self.assertEqual(response.body, 'content2')

        response = self.app.get('/tenders/{}/awards/{}/documents/{}'.format(
            self.tender_id, self.award_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])

        response = self.app.put('/tenders/{}/awards/{}/documents/{}'.format(
            self.tender_id, self.award_id, doc_id), 'content3', content_type='application/msword')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        if self.docservice:
            self.assertIn('Signature=', response.json["data"]["url"])
            self.assertIn('KeyID=', response.json["data"]["url"])
            self.assertNotIn('Expires=', response.json["data"]["url"])
            key = response.json["data"]["url"].split('/')[-1].split('?')[0]
            tender = self.db.get(self.tender_id)
            self.assertIn(key, tender['awards'][-1]['documents'][-1]["url"])
            self.assertIn('Signature=', tender['awards'][-1]['documents'][-1]["url"])
            self.assertIn('KeyID=', tender['awards'][-1]['documents'][-1]["url"])
            self.assertNotIn('Expires=', tender['awards'][-1]['documents'][-1]["url"])
        else:
            key = response.json["data"]["url"].split('?')[-1].split('=')[-1]

        response = self.app.get('/tenders/{}/awards/{}/documents/{}?download={}'.format(
            self.tender_id, self.award_id, doc_id, key))
        if self.docservice:
            self.assertEqual(response.status, '302 Moved Temporarily')
            self.assertIn('http://localhost/get/', response.location)
            self.assertIn('Signature=', response.location)
            self.assertIn('KeyID=', response.location)
            self.assertNotIn('Expires=', response.location)
        else:
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/msword')
            self.assertEqual(response.content_length, 8)
            self.assertEqual(response.body, 'content3')

        self.set_status('complete')

        response = self.app.put('/tenders/{}/awards/{}/documents/{}'.format(
            self.tender_id, self.award_id, doc_id), upload_files=[('file', 'name.doc', 'content3')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current (complete) tender status")

    def test_patch_tender_award_document(self):
        response = self.app.post('/tenders/{}/awards/{}/documents'.format(
            self.tender_id, self.award_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.patch_json('/tenders/{}/awards/{}/documents/{}'.format(self.tender_id, self.award_id, doc_id), {"data": {"description": "document description"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])

        response = self.app.get('/tenders/{}/awards/{}/documents/{}'.format(
            self.tender_id, self.award_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('document description', response.json["data"]["description"])

        self.set_status('complete')

        response = self.app.patch_json('/tenders/{}/awards/{}/documents/{}'.format(self.tender_id, self.award_id, doc_id), {"data": {"description": "document description"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current (complete) tender status")


class TenderAwardDocumentWithDSResourceTest(TenderAwardDocumentResourceTest):
    docservice = True


class Tender2LotAwardDocumentResourceTest(BaseTenderWebTest):
    initial_status = 'active.qualification'
    initial_bids = test_bids
    initial_lots = 2 * test_lots

    def setUp(self):
        super(Tender2LotAwardDocumentResourceTest, self).setUp()
        # Create award
        bid = self.initial_bids[0]
        response = self.app.post_json('/tenders/{}/awards'.format(
            self.tender_id), {'data': {'suppliers': [test_organization], 'status': 'pending', 'bid_id': bid['id'], 'lotID': bid['lotValues'][0]['relatedLot']}})
        award = response.json['data']
        self.award_id = award['id']

    def test_create_tender_award_document(self):
        response = self.app.post('/tenders/{}/awards/{}/documents'.format(
            self.tender_id, self.award_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])
        self.assertEqual('name.doc', response.json["data"]["title"])
        if self.docservice:
            self.assertIn('Signature=', response.json["data"]["url"])
            self.assertIn('KeyID=', response.json["data"]["url"])
            self.assertNotIn('Expires=', response.json["data"]["url"])
            key = response.json["data"]["url"].split('/')[-1].split('?')[0]
            tender = self.db.get(self.tender_id)
            self.assertIn(key, tender['awards'][-1]['documents'][-1]["url"])
            self.assertIn('Signature=', tender['awards'][-1]['documents'][-1]["url"])
            self.assertIn('KeyID=', tender['awards'][-1]['documents'][-1]["url"])
            self.assertNotIn('Expires=', tender['awards'][-1]['documents'][-1]["url"])
        else:
            key = response.json["data"]["url"].split('?')[-1].split('=')[-1]

        response = self.app.get('/tenders/{}/awards/{}/documents'.format(self.tender_id, self.award_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/tenders/{}/awards/{}/documents?all=true'.format(self.tender_id, self.award_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/tenders/{}/awards/{}/documents/{}?download=some_id'.format(
            self.tender_id, self.award_id, doc_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'download'}
        ])

        response = self.app.get('/tenders/{}/awards/{}/documents/{}?download={}'.format(
            self.tender_id, self.award_id, doc_id, key))
        if self.docservice:
            self.assertEqual(response.status, '302 Moved Temporarily')
            self.assertIn('http://localhost/get/', response.location)
            self.assertIn('Signature=', response.location)
            self.assertIn('KeyID=', response.location)
            self.assertNotIn('Expires=', response.location)
        else:
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/msword')
            self.assertEqual(response.content_length, 7)
            self.assertEqual(response.body, 'content')

        response = self.app.get('/tenders/{}/awards/{}/documents/{}'.format(
            self.tender_id, self.award_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])

        response = self.app.post_json('/tenders/{}/cancellations'.format(self.tender_id), {'data': {
            'reason': 'cancellation reason',
            'status': 'active',
            "cancellationOf": "lot",
            "relatedLot": self.initial_lots[0]['id']
        }})
        self.assertEqual(response.status, '201 Created')

        response = self.app.post('/tenders/{}/awards/{}/documents'.format(
            self.tender_id, self.award_id), upload_files=[('file', 'name.doc', 'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can add document only in active lot status")

    def test_put_tender_award_document(self):
        response = self.app.post('/tenders/{}/awards/{}/documents'.format(
            self.tender_id, self.award_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.put('/tenders/{}/awards/{}/documents/{}'.format(self.tender_id, self.award_id, doc_id),
                                status=404,
                                upload_files=[('invalid_name', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'body', u'name': u'file'}
        ])

        response = self.app.put('/tenders/{}/awards/{}/documents/{}'.format(
            self.tender_id, self.award_id, doc_id), upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        if self.docservice:
            self.assertIn('Signature=', response.json["data"]["url"])
            self.assertIn('KeyID=', response.json["data"]["url"])
            self.assertNotIn('Expires=', response.json["data"]["url"])
            key = response.json["data"]["url"].split('/')[-1].split('?')[0]
            tender = self.db.get(self.tender_id)
            self.assertIn(key, tender['awards'][-1]['documents'][-1]["url"])
            self.assertIn('Signature=', tender['awards'][-1]['documents'][-1]["url"])
            self.assertIn('KeyID=', tender['awards'][-1]['documents'][-1]["url"])
            self.assertNotIn('Expires=', tender['awards'][-1]['documents'][-1]["url"])
        else:
            key = response.json["data"]["url"].split('?')[-1].split('=')[-1]

        response = self.app.get('/tenders/{}/awards/{}/documents/{}?download={}'.format(
            self.tender_id, self.award_id, doc_id, key))
        if self.docservice:
            self.assertEqual(response.status, '302 Moved Temporarily')
            self.assertIn('http://localhost/get/', response.location)
            self.assertIn('Signature=', response.location)
            self.assertIn('KeyID=', response.location)
            self.assertNotIn('Expires=', response.location)
        else:
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/msword')
            self.assertEqual(response.content_length, 8)
            self.assertEqual(response.body, 'content2')

        response = self.app.get('/tenders/{}/awards/{}/documents/{}'.format(
            self.tender_id, self.award_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])

        response = self.app.put('/tenders/{}/awards/{}/documents/{}'.format(
            self.tender_id, self.award_id, doc_id), 'content3', content_type='application/msword')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        if self.docservice:
            self.assertIn('Signature=', response.json["data"]["url"])
            self.assertIn('KeyID=', response.json["data"]["url"])
            self.assertNotIn('Expires=', response.json["data"]["url"])
            key = response.json["data"]["url"].split('/')[-1].split('?')[0]
            tender = self.db.get(self.tender_id)
            self.assertIn(key, tender['awards'][-1]['documents'][-1]["url"])
            self.assertIn('Signature=', tender['awards'][-1]['documents'][-1]["url"])
            self.assertIn('KeyID=', tender['awards'][-1]['documents'][-1]["url"])
            self.assertNotIn('Expires=', tender['awards'][-1]['documents'][-1]["url"])
        else:
            key = response.json["data"]["url"].split('?')[-1].split('=')[-1]

        response = self.app.get('/tenders/{}/awards/{}/documents/{}?download={}'.format(
            self.tender_id, self.award_id, doc_id, key))
        if self.docservice:
            self.assertEqual(response.status, '302 Moved Temporarily')
            self.assertIn('http://localhost/get/', response.location)
            self.assertIn('Signature=', response.location)
            self.assertIn('KeyID=', response.location)
            self.assertNotIn('Expires=', response.location)
        else:
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/msword')
            self.assertEqual(response.content_length, 8)
            self.assertEqual(response.body, 'content3')

        response = self.app.post_json('/tenders/{}/cancellations'.format(self.tender_id), {'data': {
            'reason': 'cancellation reason',
            'status': 'active',
            "cancellationOf": "lot",
            "relatedLot": self.initial_lots[0]['id']
        }})
        self.assertEqual(response.status, '201 Created')

        response = self.app.put('/tenders/{}/awards/{}/documents/{}'.format(
            self.tender_id, self.award_id, doc_id), upload_files=[('file', 'name.doc', 'content3')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can update document only in active lot status")

    def test_patch_tender_award_document(self):
        response = self.app.post('/tenders/{}/awards/{}/documents'.format(
            self.tender_id, self.award_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.patch_json('/tenders/{}/awards/{}/documents/{}'.format(self.tender_id, self.award_id, doc_id), {"data": {"description": "document description"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])

        response = self.app.get('/tenders/{}/awards/{}/documents/{}'.format(
            self.tender_id, self.award_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('document description', response.json["data"]["description"])

        response = self.app.post_json('/tenders/{}/cancellations'.format(self.tender_id), {'data': {
            'reason': 'cancellation reason',
            'status': 'active',
            "cancellationOf": "lot",
            "relatedLot": self.initial_lots[0]['id']
        }})
        self.assertEqual(response.status, '201 Created')

        response = self.app.patch_json('/tenders/{}/awards/{}/documents/{}'.format(self.tender_id, self.award_id, doc_id), {"data": {"description": "document description"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can update document only in active lot status")


class Tender2LotAwardDocumentWithDSResourceTest(Tender2LotAwardDocumentResourceTest):
    docservice = True


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(Tender2LotAwardComplaintDocumentResourceTest))
    suite.addTest(unittest.makeSuite(Tender2LotAwardComplaintResourceTest))
    suite.addTest(unittest.makeSuite(Tender2LotAwardDocumentResourceTest))
    suite.addTest(unittest.makeSuite(Tender2LotAwardResourceTest))
    suite.addTest(unittest.makeSuite(TenderAwardComplaintDocumentResourceTest))
    suite.addTest(unittest.makeSuite(TenderAwardComplaintResourceTest))
    suite.addTest(unittest.makeSuite(TenderAwardDocumentResourceTest))
    suite.addTest(unittest.makeSuite(TenderAwardResourceTest))
    suite.addTest(unittest.makeSuite(TenderLotAwardResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
