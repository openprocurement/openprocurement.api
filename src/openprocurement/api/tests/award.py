# -*- coding: utf-8 -*-
import unittest

from openprocurement.api.tests.base import BaseAuctionWebTest, test_auction_data, test_bids, test_lots


class AuctionAwardResourceTest(BaseAuctionWebTest):
    #initial_data = auction_data
    initial_status = 'active.qualification'
    initial_bids = test_bids

    def test_create_auction_award_invalid(self):
        request_path = '/auctions/{}/awards'.format(self.auction_id)
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
            'suppliers': [test_auction_data["procuringEntity"]],
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

        response = self.app.post_json('/auctions/some_id/awards', {'data': {
                                      'suppliers': [test_auction_data["procuringEntity"]], 'bid_id': self.initial_bids[0]['id']}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'auction_id'}
        ])

        response = self.app.get('/auctions/some_id/awards', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'auction_id'}
        ])

        self.set_status('complete')

        response = self.app.post_json('/auctions/{}/awards'.format(
            self.auction_id), {'data': {'suppliers': [test_auction_data["procuringEntity"]], 'status': 'pending', 'bid_id': self.initial_bids[0]['id']}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't create award in current (complete) auction status")

    def test_create_auction_award(self):
        request_path = '/auctions/{}/awards'.format(self.auction_id)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_auction_data["procuringEntity"]], 'status': 'pending', 'bid_id': self.initial_bids[0]['id']}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']
        self.assertEqual(award['suppliers'][0]['name'], test_auction_data["procuringEntity"]['name'])
        self.assertIn('id', award)
        self.assertIn(award['id'], response.headers['Location'])

        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'][-1], award)

        response = self.app.patch_json('/auctions/{}/awards/{}'.format(self.auction_id, award['id']), {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['status'], u'active')

        response = self.app.get('/auctions/{}'.format(self.auction_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['status'], u'active.awarded')

        response = self.app.patch_json('/auctions/{}/awards/{}'.format(self.auction_id, award['id']), {"data": {"status": "cancelled"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['status'], u'cancelled')
        self.assertIn('Location', response.headers)

    def test_patch_auction_award(self):
        request_path = '/auctions/{}/awards'.format(self.auction_id)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_auction_data["procuringEntity"]], 'status': u'pending', 'bid_id': self.initial_bids[0]['id'], "value": {"amount": 500}}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']

        #response = self.app.patch_json('/auctions/{}/awards/{}'.format(self.auction_id, award['id']), {"data": {"value": {"amount": 600}}})
        #self.assertEqual(response.status, '200 OK')
        #self.assertEqual(response.content_type, 'application/json')
        #self.assertEqual(response.json['data']["value"]["amount"], 600)

        response = self.app.patch_json('/auctions/{}/awards/some_id'.format(self.auction_id), {"data": {"status": "unsuccessful"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.patch_json('/auctions/some_id/awards/some_id', {"data": {"status": "unsuccessful"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'auction_id'}
        ])

        response = self.app.patch_json('/auctions/{}/awards/{}'.format(self.auction_id, award['id']), {"data": {"awardStatus": "unsuccessful"}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'], [
            {"location": "body", "name": "awardStatus", "description": "Rogue field"}
        ])

        response = self.app.patch_json('/auctions/{}/awards/{}'.format(self.auction_id, award['id']), {"data": {"status": "unsuccessful"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('Location', response.headers)
        new_award_location = response.headers['Location']

        response = self.app.patch_json('/auctions/{}/awards/{}'.format(self.auction_id, award['id']), {"data": {"status": "pending"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update award in current (unsuccessful) status")

        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(len(response.json['data']), 2)
        self.assertIn(response.json['data'][1]['id'], new_award_location)
        new_award = response.json['data'][-1]

        response = self.app.patch_json('/auctions/{}/awards/{}'.format(self.auction_id, new_award['id']), {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(len(response.json['data']), 2)

        response = self.app.patch_json('/auctions/{}/awards/{}'.format(self.auction_id, new_award['id']), {"data": {"status": "cancelled"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('Location', response.headers)

        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(len(response.json['data']), 3)

        self.set_status('complete')

        response = self.app.get('/auctions/{}/awards/{}'.format(self.auction_id, award['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["value"]["amount"], 500)

        response = self.app.patch_json('/auctions/{}/awards/{}'.format(self.auction_id, award['id']), {"data": {"status": "unsuccessful"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update award in current (complete) auction status")

    def test_patch_auction_award_unsuccessful(self):
        request_path = '/auctions/{}/awards'.format(self.auction_id)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_auction_data["procuringEntity"]], 'status': u'pending', 'bid_id': self.initial_bids[0]['id'], "value": {"amount": 500}}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']

        response = self.app.patch_json('/auctions/{}/awards/{}'.format(self.auction_id, award['id']), {"data": {"status": "unsuccessful"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('Location', response.headers)
        new_award_location = response.headers['Location']

        response = self.app.patch_json(new_award_location[-82:], {"data": {"status": "unsuccessful"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertNotIn('Location', response.headers)

        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(len(response.json['data']), 2)

    def test_get_auction_award(self):
        response = self.app.post_json('/auctions/{}/awards'.format(
            self.auction_id), {'data': {'suppliers': [test_auction_data["procuringEntity"]], 'status': 'pending', 'bid_id': self.initial_bids[0]['id']}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']

        response = self.app.get('/auctions/{}/awards/{}'.format(self.auction_id, award['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        award_data = response.json['data']
        self.assertEqual(award_data, award)

        response = self.app.get('/auctions/{}/awards/some_id'.format(self.auction_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.get('/auctions/some_id/awards/some_id', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'auction_id'}
        ])


class AuctionLotAwardResourceTest(BaseAuctionWebTest):
    initial_status = 'active.qualification'
    initial_lots = test_lots
    initial_bids = test_bids

    def test_create_auction_award(self):
        request_path = '/auctions/{}/awards'.format(self.auction_id)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_auction_data["procuringEntity"]], 'status': 'pending', 'bid_id': self.initial_bids[0]['id']}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'], [
            {"location": "body", "name": "lotID", "description": ["This field is required."]}
        ])

        response = self.app.post_json(request_path, {'data': {'suppliers': [test_auction_data["procuringEntity"]], 'status': 'pending', 'bid_id': self.initial_bids[0]['id'], 'lotID': self.initial_lots[0]['id']}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']
        self.assertEqual(award['suppliers'][0]['name'], test_auction_data["procuringEntity"]['name'])
        self.assertEqual(award['lotID'], self.initial_lots[0]['id'])
        self.assertIn('id', award)
        self.assertIn(award['id'], response.headers['Location'])

        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'][-1], award)

        response = self.app.patch_json('/auctions/{}/awards/{}'.format(self.auction_id, award['id']), {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['status'], u'active')

        response = self.app.get('/auctions/{}'.format(self.auction_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['status'], u'active.awarded')

        response = self.app.patch_json('/auctions/{}/awards/{}'.format(self.auction_id, award['id']), {"data": {"status": "cancelled"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['status'], u'cancelled')
        self.assertIn('Location', response.headers)

    def test_patch_auction_award(self):
        request_path = '/auctions/{}/awards'.format(self.auction_id)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_auction_data["procuringEntity"]], 'status': u'pending', 'bid_id': self.initial_bids[0]['id'], 'lotID': self.initial_lots[0]['id'], "value": {"amount": 500}}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']

        response = self.app.patch_json('/auctions/{}/awards/some_id'.format(self.auction_id), {"data": {"status": "unsuccessful"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.patch_json('/auctions/some_id/awards/some_id', {"data": {"status": "unsuccessful"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'auction_id'}
        ])

        response = self.app.patch_json('/auctions/{}/awards/{}'.format(self.auction_id, award['id']), {"data": {"awardStatus": "unsuccessful"}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'], [
            {"location": "body", "name": "awardStatus", "description": "Rogue field"}
        ])

        response = self.app.patch_json('/auctions/{}/awards/{}'.format(self.auction_id, award['id']), {"data": {"status": "unsuccessful"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('Location', response.headers)
        new_award_location = response.headers['Location']

        response = self.app.patch_json('/auctions/{}/awards/{}'.format(self.auction_id, award['id']), {"data": {"status": "pending"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update award in current (unsuccessful) status")

        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(len(response.json['data']), 2)
        self.assertIn(response.json['data'][-1]['id'], new_award_location)
        new_award = response.json['data'][-1]

        response = self.app.patch_json('/auctions/{}/awards/{}'.format(self.auction_id, new_award['id']), {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(len(response.json['data']), 2)

        response = self.app.patch_json('/auctions/{}/awards/{}'.format(self.auction_id, new_award['id']), {"data": {"status": "cancelled"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('Location', response.headers)

        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(len(response.json['data']), 3)

        self.set_status('complete')

        response = self.app.get('/auctions/{}/awards/{}'.format(self.auction_id, award['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["value"]["amount"], 500)

        response = self.app.patch_json('/auctions/{}/awards/{}'.format(self.auction_id, award['id']), {"data": {"status": "unsuccessful"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update award in current (complete) auction status")

    def test_patch_auction_award_unsuccessful(self):
        request_path = '/auctions/{}/awards'.format(self.auction_id)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_auction_data["procuringEntity"]], 'status': u'pending', 'bid_id': self.initial_bids[0]['id'], 'lotID': self.initial_lots[0]['id'], "value": {"amount": 500}}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']

        response = self.app.patch_json('/auctions/{}/awards/{}'.format(self.auction_id, award['id']), {"data": {"status": "unsuccessful"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('Location', response.headers)
        new_award_location = response.headers['Location']

        response = self.app.patch_json(new_award_location[-82:], {"data": {"status": "unsuccessful"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertNotIn('Location', response.headers)

        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(len(response.json['data']), 2)


class Auction2LotAwardResourceTest(BaseAuctionWebTest):
    initial_status = 'active.qualification'
    initial_lots = 2 * test_lots
    initial_bids = test_bids

    def test_create_auction_award(self):
        request_path = '/auctions/{}/awards'.format(self.auction_id)
        response = self.app.post_json('/auctions/{}/cancellations'.format(self.auction_id), {'data': {
            'reason': 'cancellation reason',
            'status': 'active',
            "cancellationOf": "lot",
            "relatedLot": self.initial_lots[0]['id']
        }})
        self.assertEqual(response.status, '201 Created')

        response = self.app.post_json(request_path, {'data': {
            'suppliers': [test_auction_data["procuringEntity"]],
            'status': 'pending',
            'bid_id': self.initial_bids[0]['id'],
            'lotID': self.initial_lots[0]['id']
        }}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can create award only in active lot status")

        response = self.app.post_json(request_path, {'data': {
            'suppliers': [test_auction_data["procuringEntity"]],
            'status': 'pending',
            'bid_id': self.initial_bids[0]['id'],
            'lotID': self.initial_lots[1]['id']
        }})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']
        self.assertEqual(award['suppliers'][0]['name'], test_auction_data["procuringEntity"]['name'])
        self.assertEqual(award['lotID'], self.initial_lots[1]['id'])
        self.assertIn('id', award)
        self.assertIn(award['id'], response.headers['Location'])

        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'][-1], award)

        response = self.app.patch_json('/auctions/{}/awards/{}'.format(self.auction_id, award['id']), {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['status'], u'active')

        response = self.app.get('/auctions/{}'.format(self.auction_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['status'], u'active.awarded')

        response = self.app.patch_json('/auctions/{}/awards/{}'.format(self.auction_id, award['id']), {"data": {"status": "cancelled"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['status'], u'cancelled')
        self.assertIn('Location', response.headers)

    def test_patch_auction_award(self):
        request_path = '/auctions/{}/awards'.format(self.auction_id)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_auction_data["procuringEntity"]], 'status': u'pending', 'bid_id': self.initial_bids[0]['id'], 'lotID': self.initial_lots[0]['id'], "value": {"amount": 500}}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']

        response = self.app.patch_json('/auctions/{}/awards/{}'.format(self.auction_id, award['id']), {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(len(response.json['data']), 2)
        new_award = response.json['data'][-1]

        response = self.app.post_json('/auctions/{}/cancellations'.format(self.auction_id), {'data': {
            'reason': 'cancellation reason',
            'status': 'active',
            "cancellationOf": "lot",
            "relatedLot": self.initial_lots[1]['id']
        }})
        self.assertEqual(response.status, '201 Created')

        response = self.app.patch_json('/auctions/{}/awards/{}'.format(self.auction_id, new_award['id']), {"data": {"status": "unsuccessful"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can update award only in active lot status")


class AuctionAwardComplaintResourceTest(BaseAuctionWebTest):
    #initial_data = auction_data
    initial_status = 'active.qualification'
    initial_bids = test_bids

    def setUp(self):
        super(AuctionAwardComplaintResourceTest, self).setUp()
        # Create award
        response = self.app.post_json('/auctions/{}/awards'.format(
            self.auction_id), {'data': {'suppliers': [test_auction_data["procuringEntity"]], 'status': 'pending', 'bid_id': self.initial_bids[0]['id']}})
        award = response.json['data']
        self.award_id = award['id']

    def test_create_auction_award_complaint_invalid(self):
        response = self.app.post_json('/auctions/some_id/awards/some_id/complaints', {
                                      'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_auction_data["procuringEntity"]}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'auction_id'}
        ])

        request_path = '/auctions/{}/awards/{}/complaints'.format(self.auction_id, self.award_id)

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

    def test_create_auction_award_complaint(self):
        response = self.app.post_json('/auctions/{}/awards/{}/complaints'.format(
            self.auction_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_auction_data["procuringEntity"]}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']
        self.assertEqual(complaint['author']['name'], test_auction_data["procuringEntity"]['name'])
        self.assertIn('id', complaint)
        self.assertIn(complaint['id'], response.headers['Location'])

        self.set_status('active.awarded')

        response = self.app.patch_json('/auctions/{}/awards/{}/complaints/{}'.format(self.auction_id, self.award_id, complaint['id']), {"data": {"status": "invalid", "resolution": "spam"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "invalid")
        self.assertEqual(response.json['data']["resolution"], "spam")

        response = self.app.get('/auctions/{}'.format(self.auction_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], 'active.awarded')

        self.set_status('unsuccessful')

        response = self.app.post_json('/auctions/{}/awards/{}/complaints'.format(
            self.auction_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_auction_data["procuringEntity"]}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add complaint in current (unsuccessful) auction status")

    def test_patch_auction_award_complaint(self):
        response = self.app.post_json('/auctions/{}/awards/{}/complaints'.format(
            self.auction_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_auction_data["procuringEntity"]}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']

        response = self.app.patch_json('/auctions/{}/awards/{}'.format(self.auction_id, self.award_id, complaint['id']), {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "active")

        response = self.app.patch_json('/auctions/{}/awards/{}/complaints/{}'.format(self.auction_id, self.award_id, complaint['id']), {"data": {"status": "cancelled"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't cancel complaint")

        response = self.app.patch_json('/auctions/{}/awards/{}/complaints/{}'.format(self.auction_id, self.award_id, complaint['id']), {"data": {"status": "resolved", "resolution": "resolution text"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "resolved")
        self.assertEqual(response.json['data']["resolution"], "resolution text")

        response = self.app.patch_json('/auctions/{}/awards/{}/complaints/some_id'.format(self.auction_id, self.award_id), {"data": {"status": "resolved", "resolution": "resolution text"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.patch_json('/auctions/some_id/awards/some_id/complaints/some_id', {"data": {"status": "resolved", "resolution": "resolution text"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'auction_id'}
        ])

        response = self.app.patch_json('/auctions/{}/awards/{}/complaints/{}'.format(self.auction_id, self.award_id, complaint['id']), {"data": {"status": "resolved", "resolution": "resolution text"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update complaint in current (resolved) status")

        response = self.app.patch_json('/auctions/{}/awards/some_id/complaints/some_id'.format(self.auction_id), {"data": {"status": "resolved", "resolution": "resolution text"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.get('/auctions/{}/awards/{}/complaints/{}'.format(self.auction_id, self.award_id, complaint['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "resolved")
        self.assertEqual(response.json['data']["resolution"], "resolution text")

        self.set_status('complete')

        response = self.app.patch_json('/auctions/{}/awards/{}/complaints/{}'.format(self.auction_id, self.award_id, complaint['id']), {"data": {"status": "resolved", "resolution": "resolution text"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update complaint in current (complete) auction status")

    def test_get_auction_award_complaint(self):
        response = self.app.post_json('/auctions/{}/awards/{}/complaints'.format(
            self.auction_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_auction_data["procuringEntity"]}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']

        response = self.app.get('/auctions/{}/awards/{}/complaints/{}'.format(self.auction_id, self.award_id, complaint['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'], complaint)

        response = self.app.get('/auctions/{}/awards/{}/complaints/some_id'.format(self.auction_id, self.award_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.get('/auctions/some_id/awards/some_id/complaints/some_id', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'auction_id'}
        ])

    def test_get_auction_award_complaints(self):
        response = self.app.post_json('/auctions/{}/awards/{}/complaints'.format(
            self.auction_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_auction_data["procuringEntity"]}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']

        response = self.app.get('/auctions/{}/awards/{}/complaints'.format(self.auction_id, self.award_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'][0], complaint)

        response = self.app.get('/auctions/some_id/awards/some_id/complaints', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'auction_id'}
        ])

        auction = self.db.get(self.auction_id)
        for i in auction.get('awards', []):
            i['complaintPeriod']['endDate'] = i['complaintPeriod']['startDate']
        self.db.save(auction)

        response = self.app.post_json('/auctions/{}/awards/{}/complaints'.format(
            self.auction_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_auction_data["procuringEntity"]}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can add complaint only in complaintPeriod")


class AuctionLotAwardComplaintResourceTest(BaseAuctionWebTest):
    #initial_data = auction_data
    initial_status = 'active.qualification'
    initial_lots = test_lots
    initial_bids = test_bids

    def setUp(self):
        super(AuctionLotAwardComplaintResourceTest, self).setUp()
        # Create award
        bid = self.initial_bids[0]
        response = self.app.post_json('/auctions/{}/awards'.format(
            self.auction_id), {'data': {'suppliers': [test_auction_data["procuringEntity"]], 'status': 'pending', 'bid_id': bid['id'], 'lotID': bid['lotValues'][0]['relatedLot']}})
        award = response.json['data']
        self.award_id = award['id']

    def test_create_auction_award_complaint(self):
        response = self.app.post_json('/auctions/{}/awards/{}/complaints'.format(
            self.auction_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_auction_data["procuringEntity"]}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']
        self.assertEqual(complaint['author']['name'], test_auction_data["procuringEntity"]['name'])
        self.assertIn('id', complaint)
        self.assertIn(complaint['id'], response.headers['Location'])

        self.set_status('active.awarded')

        response = self.app.patch_json('/auctions/{}/awards/{}/complaints/{}'.format(self.auction_id, self.award_id, complaint['id']), {"data": {"status": "invalid", "resolution": "spam"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "invalid")
        self.assertEqual(response.json['data']["resolution"], "spam")

        response = self.app.get('/auctions/{}'.format(self.auction_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], 'active.awarded')

        self.set_status('unsuccessful')

        response = self.app.post_json('/auctions/{}/awards/{}/complaints'.format(
            self.auction_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_auction_data["procuringEntity"]}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add complaint in current (unsuccessful) auction status")

    def test_patch_auction_award_complaint(self):
        response = self.app.post_json('/auctions/{}/awards/{}/complaints'.format(
            self.auction_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_auction_data["procuringEntity"]}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']

        response = self.app.patch_json('/auctions/{}/awards/{}'.format(self.auction_id, self.award_id, complaint['id']), {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "active")

        response = self.app.patch_json('/auctions/{}/awards/{}/complaints/{}'.format(self.auction_id, self.award_id, complaint['id']), {"data": {"status": "cancelled"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't cancel complaint")

        response = self.app.patch_json('/auctions/{}/awards/{}/complaints/{}'.format(self.auction_id, self.award_id, complaint['id']), {"data": {"status": "resolved", "resolution": "resolution text"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "resolved")
        self.assertEqual(response.json['data']["resolution"], "resolution text")

        response = self.app.patch_json('/auctions/{}/awards/{}/complaints/some_id'.format(self.auction_id, self.award_id), {"data": {"status": "resolved", "resolution": "resolution text"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.patch_json('/auctions/some_id/awards/some_id/complaints/some_id', {"data": {"status": "resolved", "resolution": "resolution text"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'auction_id'}
        ])

        response = self.app.patch_json('/auctions/{}/awards/{}/complaints/{}'.format(self.auction_id, self.award_id, complaint['id']), {"data": {"status": "resolved", "resolution": "resolution text"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update complaint in current (resolved) status")

        response = self.app.patch_json('/auctions/{}/awards/some_id/complaints/some_id'.format(self.auction_id), {"data": {"status": "resolved", "resolution": "resolution text"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.get('/auctions/{}/awards/{}/complaints/{}'.format(self.auction_id, self.award_id, complaint['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "resolved")
        self.assertEqual(response.json['data']["resolution"], "resolution text")

        self.set_status('complete')

        response = self.app.patch_json('/auctions/{}/awards/{}/complaints/{}'.format(self.auction_id, self.award_id, complaint['id']), {"data": {"status": "resolved", "resolution": "resolution text"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update complaint in current (complete) auction status")

    def test_get_auction_award_complaint(self):
        response = self.app.post_json('/auctions/{}/awards/{}/complaints'.format(
            self.auction_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_auction_data["procuringEntity"]}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']

        response = self.app.get('/auctions/{}/awards/{}/complaints/{}'.format(self.auction_id, self.award_id, complaint['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'], complaint)

        response = self.app.get('/auctions/{}/awards/{}/complaints/some_id'.format(self.auction_id, self.award_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.get('/auctions/some_id/awards/some_id/complaints/some_id', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'auction_id'}
        ])

    def test_get_auction_award_complaints(self):
        response = self.app.post_json('/auctions/{}/awards/{}/complaints'.format(
            self.auction_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_auction_data["procuringEntity"]}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']

        response = self.app.get('/auctions/{}/awards/{}/complaints'.format(self.auction_id, self.award_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'][0], complaint)

        response = self.app.get('/auctions/some_id/awards/some_id/complaints', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'auction_id'}
        ])

        auction = self.db.get(self.auction_id)
        for i in auction.get('awards', []):
            i['complaintPeriod']['endDate'] = i['complaintPeriod']['startDate']
        self.db.save(auction)

        response = self.app.post_json('/auctions/{}/awards/{}/complaints'.format(
            self.auction_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_auction_data["procuringEntity"]}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can add complaint only in complaintPeriod")


class Auction2LotAwardComplaintResourceTest(AuctionLotAwardComplaintResourceTest):
    initial_lots = 2 * test_lots

    def test_create_auction_award_complaint(self):
        response = self.app.post_json('/auctions/{}/awards/{}/complaints'.format(
            self.auction_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_auction_data["procuringEntity"]}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']
        self.assertEqual(complaint['author']['name'], test_auction_data["procuringEntity"]['name'])
        self.assertIn('id', complaint)
        self.assertIn(complaint['id'], response.headers['Location'])

        self.set_status('active.awarded')

        response = self.app.patch_json('/auctions/{}/awards/{}/complaints/{}'.format(self.auction_id, self.award_id, complaint['id']), {"data": {"status": "invalid", "resolution": "spam"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "invalid")
        self.assertEqual(response.json['data']["resolution"], "spam")

        response = self.app.get('/auctions/{}'.format(self.auction_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], 'active.awarded')

        response = self.app.post_json('/auctions/{}/cancellations'.format(self.auction_id), {'data': {
            'reason': 'cancellation reason',
            'status': 'active',
            "cancellationOf": "lot",
            "relatedLot": self.initial_lots[0]['id']
        }})
        self.assertEqual(response.status, '201 Created')

        response = self.app.post_json('/auctions/{}/awards/{}/complaints'.format(
            self.auction_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_auction_data["procuringEntity"]}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can add complaint only in active lot status")

    def test_patch_auction_award_complaint(self):
        response = self.app.patch_json('/auctions/{}/awards/{}'.format(self.auction_id, self.award_id), {"data": {"status": "unsuccessful"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "unsuccessful")

        response = self.app.post_json('/auctions/{}/awards/{}/complaints'.format(
            self.auction_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_auction_data["procuringEntity"]}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']

        response = self.app.patch_json('/auctions/{}/awards/{}/complaints/{}'.format(self.auction_id, self.award_id, complaint['id']), {"data": {"status": "resolved", "resolution": "resolution text"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "resolved")
        self.assertEqual(response.json['data']["resolution"], "resolution text")

        response = self.app.post_json('/auctions/{}/awards/{}/complaints'.format(
            self.auction_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_auction_data["procuringEntity"]}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']

        response = self.app.post_json('/auctions/{}/cancellations'.format(self.auction_id), {'data': {
            'reason': 'cancellation reason',
            'status': 'active',
            "cancellationOf": "lot",
            "relatedLot": self.initial_lots[0]['id']
        }})
        self.assertEqual(response.status, '201 Created')

        response = self.app.patch_json('/auctions/{}/awards/{}/complaints/{}'.format(self.auction_id, self.award_id, complaint['id']), {"data": {"status": "resolved", "resolution": "resolution text"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can update complaint only in active lot status")


class AuctionAwardComplaintDocumentResourceTest(BaseAuctionWebTest):
    initial_status = 'active.qualification'
    initial_bids = test_bids

    def setUp(self):
        super(AuctionAwardComplaintDocumentResourceTest, self).setUp()
        # Create award
        response = self.app.post_json('/auctions/{}/awards'.format(
            self.auction_id), {'data': {'suppliers': [test_auction_data["procuringEntity"]], 'status': 'pending', 'bid_id': self.initial_bids[0]['id']}})
        award = response.json['data']
        self.award_id = award['id']
        # Create complaint for award
        response = self.app.post_json('/auctions/{}/awards/{}/complaints'.format(
            self.auction_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_auction_data["procuringEntity"]}})
        complaint = response.json['data']
        self.complaint_id = complaint['id']

    def test_not_found(self):
        response = self.app.post('/auctions/some_id/awards/some_id/complaints/some_id/documents', status=404, upload_files=[
                                 ('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'auction_id'}
        ])

        response = self.app.post('/auctions/{}/awards/some_id/complaints/some_id/documents'.format(self.auction_id), status=404, upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.post('/auctions/{}/awards/{}/complaints/some_id/documents'.format(self.auction_id, self.award_id), status=404, upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.post('/auctions/{}/awards/{}/complaints/{}/documents'.format(self.auction_id, self.award_id, self.complaint_id), status=404, upload_files=[
                                 ('invalid_value', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'body', u'name': u'file'}
        ])

        response = self.app.get('/auctions/some_id/awards/some_id/complaints/some_id/documents', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'auction_id'}
        ])

        response = self.app.get('/auctions/{}/awards/some_id/complaints/some_id/documents'.format(self.auction_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.get('/auctions/{}/awards/{}/complaints/some_id/documents'.format(self.auction_id, self.award_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.get('/auctions/some_id/awards/some_id/complaints/some_id/documents/some_id', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'auction_id'}
        ])

        response = self.app.get('/auctions/{}/awards/some_id/complaints/some_id/documents/some_id'.format(self.auction_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.get('/auctions/{}/awards/{}/complaints/some_id/documents/some_id'.format(self.auction_id, self.award_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.get('/auctions/{}/awards/{}/complaints/{}/documents/some_id'.format(self.auction_id, self.award_id, self.complaint_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'document_id'}
        ])

        response = self.app.put('/auctions/some_id/awards/some_id/complaints/some_id/documents/some_id', status=404,
                                upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'auction_id'}
        ])

        response = self.app.put('/auctions/{}/awards/some_id/complaints/some_id/documents/some_id'.format(self.auction_id), status=404,
                                upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.put('/auctions/{}/awards/{}/complaints/some_id/documents/some_id'.format(self.auction_id, self.award_id), status=404, upload_files=[
                                ('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.put('/auctions/{}/awards/{}/complaints/{}/documents/some_id'.format(
            self.auction_id, self.award_id, self.complaint_id), status=404, upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'document_id'}
        ])

    def test_create_auction_award_complaint_document(self):
        response = self.app.post('/auctions/{}/awards/{}/complaints/{}/documents'.format(
            self.auction_id, self.award_id, self.complaint_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])
        self.assertEqual('name.doc', response.json["data"]["title"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/auctions/{}/awards/{}/complaints/{}/documents'.format(self.auction_id, self.award_id, self.complaint_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/auctions/{}/awards/{}/complaints/{}/documents?all=true'.format(self.auction_id, self.award_id, self.complaint_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/auctions/{}/awards/{}/complaints/{}/documents/{}?download=some_id'.format(
            self.auction_id, self.award_id, self.complaint_id, doc_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'download'}
        ])

        response = self.app.get('/auctions/{}/awards/{}/complaints/{}/documents/{}?{}'.format(
            self.auction_id, self.award_id, self.complaint_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 7)
        self.assertEqual(response.body, 'content')

        response = self.app.get('/auctions/{}/awards/{}/complaints/{}/documents/{}'.format(
            self.auction_id, self.award_id, self.complaint_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])

        self.set_status('complete')

        response = self.app.post('/auctions/{}/awards/{}/complaints/{}/documents'.format(
            self.auction_id, self.award_id, self.complaint_id), upload_files=[('file', 'name.doc', 'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add document in current (complete) auction status")

    def test_put_auction_award_complaint_document(self):
        response = self.app.post('/auctions/{}/awards/{}/complaints/{}/documents'.format(
            self.auction_id, self.award_id, self.complaint_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.put('/auctions/{}/awards/{}/complaints/{}/documents/{}'.format(self.auction_id, self.award_id, self.complaint_id, doc_id),
                                status=404,
                                upload_files=[('invalid_name', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'body', u'name': u'file'}
        ])

        response = self.app.put('/auctions/{}/awards/{}/complaints/{}/documents/{}'.format(
            self.auction_id, self.award_id, self.complaint_id, doc_id), upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/auctions/{}/awards/{}/complaints/{}/documents/{}?{}'.format(
            self.auction_id, self.award_id, self.complaint_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 8)
        self.assertEqual(response.body, 'content2')

        response = self.app.get('/auctions/{}/awards/{}/complaints/{}/documents/{}'.format(
            self.auction_id, self.award_id, self.complaint_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])

        response = self.app.put('/auctions/{}/awards/{}/complaints/{}/documents/{}'.format(
            self.auction_id, self.award_id, self.complaint_id, doc_id), 'content3', content_type='application/msword')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/auctions/{}/awards/{}/complaints/{}/documents/{}?{}'.format(
            self.auction_id, self.award_id, self.complaint_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 8)
        self.assertEqual(response.body, 'content3')

        self.set_status('complete')

        response = self.app.put('/auctions/{}/awards/{}/complaints/{}/documents/{}'.format(
            self.auction_id, self.award_id, self.complaint_id, doc_id), upload_files=[('file', 'name.doc', 'content3')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current (complete) auction status")

    def test_patch_auction_award_complaint_document(self):
        response = self.app.post('/auctions/{}/awards/{}/complaints/{}/documents'.format(
            self.auction_id, self.award_id, self.complaint_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.patch_json('/auctions/{}/awards/{}/complaints/{}/documents/{}'.format(self.auction_id, self.award_id, self.complaint_id, doc_id), {"data": {"description": "document description"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])

        response = self.app.get('/auctions/{}/awards/{}/complaints/{}/documents/{}'.format(
            self.auction_id, self.award_id, self.complaint_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('document description', response.json["data"]["description"])

        self.set_status('complete')

        response = self.app.patch_json('/auctions/{}/awards/{}/complaints/{}/documents/{}'.format(self.auction_id, self.award_id, self.complaint_id, doc_id), {"data": {"description": "document description"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current (complete) auction status")


class Auction2LotAwardComplaintDocumentResourceTest(BaseAuctionWebTest):
    initial_status = 'active.qualification'
    initial_bids = test_bids
    initial_lots = 2 * test_lots

    def setUp(self):
        super(Auction2LotAwardComplaintDocumentResourceTest, self).setUp()
        # Create award
        bid = self.initial_bids[0]
        response = self.app.post_json('/auctions/{}/awards'.format(
            self.auction_id), {'data': {'suppliers': [test_auction_data["procuringEntity"]], 'status': 'pending', 'bid_id': bid['id'], 'lotID': bid['lotValues'][0]['relatedLot']}})
        award = response.json['data']
        self.award_id = award['id']
        # Create complaint for award
        response = self.app.post_json('/auctions/{}/awards/{}/complaints'.format(
            self.auction_id, self.award_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_auction_data["procuringEntity"]}})
        complaint = response.json['data']
        self.complaint_id = complaint['id']

    def test_create_auction_award_complaint_document(self):
        response = self.app.post('/auctions/{}/awards/{}/complaints/{}/documents'.format(
            self.auction_id, self.award_id, self.complaint_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])
        self.assertEqual('name.doc', response.json["data"]["title"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/auctions/{}/awards/{}/complaints/{}/documents'.format(self.auction_id, self.award_id, self.complaint_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/auctions/{}/awards/{}/complaints/{}/documents?all=true'.format(self.auction_id, self.award_id, self.complaint_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/auctions/{}/awards/{}/complaints/{}/documents/{}?download=some_id'.format(
            self.auction_id, self.award_id, self.complaint_id, doc_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'download'}
        ])

        response = self.app.get('/auctions/{}/awards/{}/complaints/{}/documents/{}?{}'.format(
            self.auction_id, self.award_id, self.complaint_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 7)
        self.assertEqual(response.body, 'content')

        response = self.app.get('/auctions/{}/awards/{}/complaints/{}/documents/{}'.format(
            self.auction_id, self.award_id, self.complaint_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])

        response = self.app.post_json('/auctions/{}/cancellations'.format(self.auction_id), {'data': {
            'reason': 'cancellation reason',
            'status': 'active',
            "cancellationOf": "lot",
            "relatedLot": self.initial_lots[0]['id']
        }})
        self.assertEqual(response.status, '201 Created')

        response = self.app.post('/auctions/{}/awards/{}/complaints/{}/documents'.format(
            self.auction_id, self.award_id, self.complaint_id), upload_files=[('file', 'name.doc', 'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can add document only in active lot status")

    def test_put_auction_award_complaint_document(self):
        response = self.app.post('/auctions/{}/awards/{}/complaints/{}/documents'.format(
            self.auction_id, self.award_id, self.complaint_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.put('/auctions/{}/awards/{}/complaints/{}/documents/{}'.format(self.auction_id, self.award_id, self.complaint_id, doc_id),
                                status=404,
                                upload_files=[('invalid_name', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'body', u'name': u'file'}
        ])

        response = self.app.put('/auctions/{}/awards/{}/complaints/{}/documents/{}'.format(
            self.auction_id, self.award_id, self.complaint_id, doc_id), upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/auctions/{}/awards/{}/complaints/{}/documents/{}?{}'.format(
            self.auction_id, self.award_id, self.complaint_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 8)
        self.assertEqual(response.body, 'content2')

        response = self.app.get('/auctions/{}/awards/{}/complaints/{}/documents/{}'.format(
            self.auction_id, self.award_id, self.complaint_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])

        response = self.app.put('/auctions/{}/awards/{}/complaints/{}/documents/{}'.format(
            self.auction_id, self.award_id, self.complaint_id, doc_id), 'content3', content_type='application/msword')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/auctions/{}/awards/{}/complaints/{}/documents/{}?{}'.format(
            self.auction_id, self.award_id, self.complaint_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 8)
        self.assertEqual(response.body, 'content3')

        response = self.app.post_json('/auctions/{}/cancellations'.format(self.auction_id), {'data': {
            'reason': 'cancellation reason',
            'status': 'active',
            "cancellationOf": "lot",
            "relatedLot": self.initial_lots[0]['id']
        }})
        self.assertEqual(response.status, '201 Created')

        response = self.app.put('/auctions/{}/awards/{}/complaints/{}/documents/{}'.format(
            self.auction_id, self.award_id, self.complaint_id, doc_id), upload_files=[('file', 'name.doc', 'content3')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can update document only in active lot status")

    def test_patch_auction_award_complaint_document(self):
        response = self.app.post('/auctions/{}/awards/{}/complaints/{}/documents'.format(
            self.auction_id, self.award_id, self.complaint_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.patch_json('/auctions/{}/awards/{}/complaints/{}/documents/{}'.format(self.auction_id, self.award_id, self.complaint_id, doc_id), {"data": {"description": "document description"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])

        response = self.app.get('/auctions/{}/awards/{}/complaints/{}/documents/{}'.format(
            self.auction_id, self.award_id, self.complaint_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('document description', response.json["data"]["description"])

        response = self.app.post_json('/auctions/{}/cancellations'.format(self.auction_id), {'data': {
            'reason': 'cancellation reason',
            'status': 'active',
            "cancellationOf": "lot",
            "relatedLot": self.initial_lots[0]['id']
        }})
        self.assertEqual(response.status, '201 Created')

        response = self.app.patch_json('/auctions/{}/awards/{}/complaints/{}/documents/{}'.format(self.auction_id, self.award_id, self.complaint_id, doc_id), {"data": {"description": "document description"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can update document only in active lot status")


class AuctionAwardDocumentResourceTest(BaseAuctionWebTest):
    initial_status = 'active.qualification'
    initial_bids = test_bids

    def setUp(self):
        super(AuctionAwardDocumentResourceTest, self).setUp()
        # Create award
        response = self.app.post_json('/auctions/{}/awards'.format(
            self.auction_id), {'data': {'suppliers': [test_auction_data["procuringEntity"]], 'status': 'pending', 'bid_id': self.initial_bids[0]['id']}})
        award = response.json['data']
        self.award_id = award['id']

    def test_not_found(self):
        response = self.app.post('/auctions/some_id/awards/some_id/documents', status=404, upload_files=[
                                 ('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'auction_id'}
        ])

        response = self.app.post('/auctions/{}/awards/some_id/documents'.format(self.auction_id), status=404, upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.post('/auctions/{}/awards/{}/documents'.format(self.auction_id, self.award_id), status=404, upload_files=[
                                 ('invalid_value', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'body', u'name': u'file'}
        ])

        response = self.app.get('/auctions/some_id/awards/some_id/documents', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'auction_id'}
        ])

        response = self.app.get('/auctions/{}/awards/some_id/documents'.format(self.auction_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.get('/auctions/some_id/awards/some_id/documents/some_id', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'auction_id'}
        ])

        response = self.app.get('/auctions/{}/awards/some_id/documents/some_id'.format(self.auction_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.get('/auctions/{}/awards/{}/documents/some_id'.format(self.auction_id, self.award_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'document_id'}
        ])

        response = self.app.put('/auctions/some_id/awards/some_id/documents/some_id', status=404,
                                upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'auction_id'}
        ])

        response = self.app.put('/auctions/{}/awards/some_id/documents/some_id'.format(self.auction_id), status=404,
                                upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.put('/auctions/{}/awards/{}/documents/some_id'.format(
            self.auction_id, self.award_id), status=404, upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'document_id'}
        ])

    def test_create_auction_award_document(self):
        response = self.app.post('/auctions/{}/awards/{}/documents'.format(
            self.auction_id, self.award_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])
        self.assertEqual('name.doc', response.json["data"]["title"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/auctions/{}/awards/{}/documents'.format(self.auction_id, self.award_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/auctions/{}/awards/{}/documents?all=true'.format(self.auction_id, self.award_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/auctions/{}/awards/{}/documents/{}?download=some_id'.format(
            self.auction_id, self.award_id, doc_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'download'}
        ])

        response = self.app.get('/auctions/{}/awards/{}/documents/{}?{}'.format(
            self.auction_id, self.award_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 7)
        self.assertEqual(response.body, 'content')

        response = self.app.get('/auctions/{}/awards/{}/documents/{}'.format(
            self.auction_id, self.award_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])

        self.set_status('complete')

        response = self.app.post('/auctions/{}/awards/{}/documents'.format(
            self.auction_id, self.award_id), upload_files=[('file', 'name.doc', 'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add document in current (complete) auction status")

    def test_put_auction_award_document(self):
        response = self.app.post('/auctions/{}/awards/{}/documents'.format(
            self.auction_id, self.award_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.put('/auctions/{}/awards/{}/documents/{}'.format(self.auction_id, self.award_id, doc_id),
                                status=404,
                                upload_files=[('invalid_name', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'body', u'name': u'file'}
        ])

        response = self.app.put('/auctions/{}/awards/{}/documents/{}'.format(
            self.auction_id, self.award_id, doc_id), upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/auctions/{}/awards/{}/documents/{}?{}'.format(
            self.auction_id, self.award_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 8)
        self.assertEqual(response.body, 'content2')

        response = self.app.get('/auctions/{}/awards/{}/documents/{}'.format(
            self.auction_id, self.award_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])

        response = self.app.put('/auctions/{}/awards/{}/documents/{}'.format(
            self.auction_id, self.award_id, doc_id), 'content3', content_type='application/msword')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/auctions/{}/awards/{}/documents/{}?{}'.format(
            self.auction_id, self.award_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 8)
        self.assertEqual(response.body, 'content3')

        self.set_status('complete')

        response = self.app.put('/auctions/{}/awards/{}/documents/{}'.format(
            self.auction_id, self.award_id, doc_id), upload_files=[('file', 'name.doc', 'content3')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current (complete) auction status")

    def test_patch_auction_award_document(self):
        response = self.app.post('/auctions/{}/awards/{}/documents'.format(
            self.auction_id, self.award_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.patch_json('/auctions/{}/awards/{}/documents/{}'.format(self.auction_id, self.award_id, doc_id), {"data": {"description": "document description"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])

        response = self.app.get('/auctions/{}/awards/{}/documents/{}'.format(
            self.auction_id, self.award_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('document description', response.json["data"]["description"])

        self.set_status('complete')

        response = self.app.patch_json('/auctions/{}/awards/{}/documents/{}'.format(self.auction_id, self.award_id, doc_id), {"data": {"description": "document description"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current (complete) auction status")


class Auction2LotAwardDocumentResourceTest(BaseAuctionWebTest):
    initial_status = 'active.qualification'
    initial_bids = test_bids
    initial_lots = 2 * test_lots

    def setUp(self):
        super(Auction2LotAwardDocumentResourceTest, self).setUp()
        # Create award
        bid = self.initial_bids[0]
        response = self.app.post_json('/auctions/{}/awards'.format(
            self.auction_id), {'data': {'suppliers': [test_auction_data["procuringEntity"]], 'status': 'pending', 'bid_id': bid['id'], 'lotID': bid['lotValues'][0]['relatedLot']}})
        award = response.json['data']
        self.award_id = award['id']

    def test_create_auction_award_document(self):
        response = self.app.post('/auctions/{}/awards/{}/documents'.format(
            self.auction_id, self.award_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])
        self.assertEqual('name.doc', response.json["data"]["title"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/auctions/{}/awards/{}/documents'.format(self.auction_id, self.award_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/auctions/{}/awards/{}/documents?all=true'.format(self.auction_id, self.award_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/auctions/{}/awards/{}/documents/{}?download=some_id'.format(
            self.auction_id, self.award_id, doc_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'download'}
        ])

        response = self.app.get('/auctions/{}/awards/{}/documents/{}?{}'.format(
            self.auction_id, self.award_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 7)
        self.assertEqual(response.body, 'content')

        response = self.app.get('/auctions/{}/awards/{}/documents/{}'.format(
            self.auction_id, self.award_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])

        response = self.app.post_json('/auctions/{}/cancellations'.format(self.auction_id), {'data': {
            'reason': 'cancellation reason',
            'status': 'active',
            "cancellationOf": "lot",
            "relatedLot": self.initial_lots[0]['id']
        }})
        self.assertEqual(response.status, '201 Created')

        response = self.app.post('/auctions/{}/awards/{}/documents'.format(
            self.auction_id, self.award_id), upload_files=[('file', 'name.doc', 'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can add document only in active lot status")

    def test_put_auction_award_document(self):
        response = self.app.post('/auctions/{}/awards/{}/documents'.format(
            self.auction_id, self.award_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.put('/auctions/{}/awards/{}/documents/{}'.format(self.auction_id, self.award_id, doc_id),
                                status=404,
                                upload_files=[('invalid_name', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'body', u'name': u'file'}
        ])

        response = self.app.put('/auctions/{}/awards/{}/documents/{}'.format(
            self.auction_id, self.award_id, doc_id), upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/auctions/{}/awards/{}/documents/{}?{}'.format(
            self.auction_id, self.award_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 8)
        self.assertEqual(response.body, 'content2')

        response = self.app.get('/auctions/{}/awards/{}/documents/{}'.format(
            self.auction_id, self.award_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])

        response = self.app.put('/auctions/{}/awards/{}/documents/{}'.format(
            self.auction_id, self.award_id, doc_id), 'content3', content_type='application/msword')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/auctions/{}/awards/{}/documents/{}?{}'.format(
            self.auction_id, self.award_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 8)
        self.assertEqual(response.body, 'content3')

        response = self.app.post_json('/auctions/{}/cancellations'.format(self.auction_id), {'data': {
            'reason': 'cancellation reason',
            'status': 'active',
            "cancellationOf": "lot",
            "relatedLot": self.initial_lots[0]['id']
        }})
        self.assertEqual(response.status, '201 Created')

        response = self.app.put('/auctions/{}/awards/{}/documents/{}'.format(
            self.auction_id, self.award_id, doc_id), upload_files=[('file', 'name.doc', 'content3')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can update document only in active lot status")

    def test_patch_auction_award_document(self):
        response = self.app.post('/auctions/{}/awards/{}/documents'.format(
            self.auction_id, self.award_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.patch_json('/auctions/{}/awards/{}/documents/{}'.format(self.auction_id, self.award_id, doc_id), {"data": {"description": "document description"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])

        response = self.app.get('/auctions/{}/awards/{}/documents/{}'.format(
            self.auction_id, self.award_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('document description', response.json["data"]["description"])

        response = self.app.post_json('/auctions/{}/cancellations'.format(self.auction_id), {'data': {
            'reason': 'cancellation reason',
            'status': 'active',
            "cancellationOf": "lot",
            "relatedLot": self.initial_lots[0]['id']
        }})
        self.assertEqual(response.status, '201 Created')

        response = self.app.patch_json('/auctions/{}/awards/{}/documents/{}'.format(self.auction_id, self.award_id, doc_id), {"data": {"description": "document description"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can update document only in active lot status")


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(Auction2LotAwardComplaintDocumentResourceTest))
    suite.addTest(unittest.makeSuite(Auction2LotAwardComplaintResourceTest))
    suite.addTest(unittest.makeSuite(Auction2LotAwardDocumentResourceTest))
    suite.addTest(unittest.makeSuite(Auction2LotAwardResourceTest))
    suite.addTest(unittest.makeSuite(AuctionAwardComplaintDocumentResourceTest))
    suite.addTest(unittest.makeSuite(AuctionAwardComplaintResourceTest))
    suite.addTest(unittest.makeSuite(AuctionAwardDocumentResourceTest))
    suite.addTest(unittest.makeSuite(AuctionAwardResourceTest))
    suite.addTest(unittest.makeSuite(AuctionLotAwardResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
