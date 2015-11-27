# -*- coding: utf-8 -*-
import unittest

from openprocurement.api.tests.base import BaseAuctionWebTest, test_lots


class AuctionCancellationResourceTest(BaseAuctionWebTest):

    def test_create_auction_cancellation_invalid(self):
        response = self.app.post_json('/auctions/some_id/cancellations', {
                                      'data': {'reason': 'cancellation reason'}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'auction_id'}
        ])

        request_path = '/auctions/{}/cancellations'.format(self.auction_id)

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
            {u'description': [u'This field is required.'], u'location': u'body', u'name': u'reason'},
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

        response = self.app.post_json('/auctions/{}/cancellations'.format(self.auction_id), {'data': {
            'reason': 'cancellation reason',
            "cancellationOf": "lot"
        }}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'This field is required.'], u'location': u'body', u'name': u'relatedLot'}
        ])

        response = self.app.post_json('/auctions/{}/cancellations'.format(self.auction_id), {'data': {
            'reason': 'cancellation reason',
            "cancellationOf": "lot",
            "relatedLot": '0' * 32
        }}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'relatedLot should be one of lots'], u'location': u'body', u'name': u'relatedLot'}
        ])

    def test_create_auction_cancellation(self):
        response = self.app.post_json('/auctions/{}/cancellations'.format(
            self.auction_id), {'data': {'reason': 'cancellation reason'}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        cancellation = response.json['data']
        self.assertEqual(cancellation['reason'], 'cancellation reason')
        self.assertIn('id', cancellation)
        self.assertIn(cancellation['id'], response.headers['Location'])

        response = self.app.get('/auctions/{}'.format(self.auction_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], 'active.enquiries')

        response = self.app.post_json('/auctions/{}/cancellations'.format(
            self.auction_id), {'data': {'reason': 'cancellation reason', 'status': 'active'}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        cancellation = response.json['data']
        self.assertEqual(cancellation['reason'], 'cancellation reason')
        self.assertEqual(cancellation['status'], 'active')
        self.assertIn('id', cancellation)
        self.assertIn(cancellation['id'], response.headers['Location'])

        response = self.app.get('/auctions/{}'.format(self.auction_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], 'cancelled')

        response = self.app.post_json('/auctions/{}/cancellations'.format(
            self.auction_id), {'data': {'reason': 'cancellation reason'}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add cancellation in current (cancelled) auction status")

    def test_patch_auction_cancellation(self):
        response = self.app.post_json('/auctions/{}/cancellations'.format(
            self.auction_id), {'data': {'reason': 'cancellation reason'}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        cancellation = response.json['data']

        response = self.app.patch_json('/auctions/{}/cancellations/{}'.format(self.auction_id, cancellation['id']), {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "active")

        response = self.app.get('/auctions/{}'.format(self.auction_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], 'cancelled')

        response = self.app.patch_json('/auctions/{}/cancellations/{}'.format(self.auction_id, cancellation['id']), {"data": {"status": "pending"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update cancellation in current (cancelled) auction status")

        response = self.app.patch_json('/auctions/{}/cancellations/some_id'.format(self.auction_id), {"data": {"status": "active"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'cancellation_id'}
        ])

        response = self.app.patch_json('/auctions/some_id/cancellations/some_id', {"data": {"status": "active"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'auction_id'}
        ])

        response = self.app.get('/auctions/{}/cancellations/{}'.format(self.auction_id, cancellation['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "active")
        self.assertEqual(response.json['data']["reason"], "cancellation reason")

    def test_get_auction_cancellation(self):
        response = self.app.post_json('/auctions/{}/cancellations'.format(
            self.auction_id), {'data': {'reason': 'cancellation reason'}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        cancellation = response.json['data']

        response = self.app.get('/auctions/{}/cancellations/{}'.format(self.auction_id, cancellation['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'], cancellation)

        response = self.app.get('/auctions/{}/cancellations/some_id'.format(self.auction_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'cancellation_id'}
        ])

        response = self.app.get('/auctions/some_id/cancellations/some_id', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'auction_id'}
        ])

    def test_get_auction_cancellations(self):
        response = self.app.post_json('/auctions/{}/cancellations'.format(
            self.auction_id), {'data': {'reason': 'cancellation reason'}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        cancellation = response.json['data']

        response = self.app.get('/auctions/{}/cancellations'.format(self.auction_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'][0], cancellation)

        response = self.app.get('/auctions/some_id/cancellations', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'auction_id'}
        ])


class AuctionLotCancellationResourceTest(BaseAuctionWebTest):
    initial_lots = test_lots

    def test_create_auction_cancellation(self):
        lot_id = self.initial_lots[0]['id']
        response = self.app.post_json('/auctions/{}/cancellations'.format(self.auction_id), {'data': {
            'reason': 'cancellation reason',
            "cancellationOf": "lot",
            "relatedLot": lot_id
        }})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        cancellation = response.json['data']
        self.assertEqual(cancellation['reason'], 'cancellation reason')
        self.assertIn('id', cancellation)
        self.assertIn(cancellation['id'], response.headers['Location'])

        response = self.app.get('/auctions/{}'.format(self.auction_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['lots'][0]["status"], 'active')
        self.assertEqual(response.json['data']["status"], 'active.enquiries')

        response = self.app.post_json('/auctions/{}/cancellations'.format(self.auction_id), {'data': {
            'reason': 'cancellation reason',
            'status': 'active',
            "cancellationOf": "lot",
            "relatedLot": lot_id
        }})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        cancellation = response.json['data']
        self.assertEqual(cancellation['reason'], 'cancellation reason')
        self.assertEqual(cancellation['status'], 'active')
        self.assertIn('id', cancellation)
        self.assertIn(cancellation['id'], response.headers['Location'])

        response = self.app.get('/auctions/{}'.format(self.auction_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['lots'][0]["status"], 'cancelled')
        self.assertEqual(response.json['data']["status"], 'cancelled')

        response = self.app.post_json('/auctions/{}/cancellations'.format(
            self.auction_id), {'data': {'reason': 'cancellation reason'}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add cancellation in current (cancelled) auction status")

    def test_patch_auction_cancellation(self):
        lot_id = self.initial_lots[0]['id']
        response = self.app.post_json('/auctions/{}/cancellations'.format(self.auction_id), {'data': {
            'reason': 'cancellation reason',
            "cancellationOf": "lot",
            "relatedLot": lot_id
        }})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        cancellation = response.json['data']

        response = self.app.patch_json('/auctions/{}/cancellations/{}'.format(self.auction_id, cancellation['id']), {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "active")

        response = self.app.get('/auctions/{}'.format(self.auction_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['lots'][0]["status"], 'cancelled')
        self.assertEqual(response.json['data']["status"], 'cancelled')

        response = self.app.patch_json('/auctions/{}/cancellations/{}'.format(self.auction_id, cancellation['id']), {"data": {"status": "pending"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update cancellation in current (cancelled) auction status")

        response = self.app.get('/auctions/{}/cancellations/{}'.format(self.auction_id, cancellation['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "active")
        self.assertEqual(response.json['data']["reason"], "cancellation reason")


class AuctionLotsCancellationResourceTest(BaseAuctionWebTest):
    initial_lots = 2 * test_lots

    def test_create_auction_cancellation(self):
        lot_id = self.initial_lots[0]['id']
        response = self.app.post_json('/auctions/{}/cancellations'.format(self.auction_id), {'data': {
            'reason': 'cancellation reason',
            "cancellationOf": "lot",
            "relatedLot": lot_id
        }})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        cancellation = response.json['data']
        self.assertEqual(cancellation['reason'], 'cancellation reason')
        self.assertIn('id', cancellation)
        self.assertIn(cancellation['id'], response.headers['Location'])

        response = self.app.get('/auctions/{}'.format(self.auction_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['lots'][0]["status"], 'active')
        self.assertEqual(response.json['data']["status"], 'active.enquiries')

        response = self.app.post_json('/auctions/{}/cancellations'.format(self.auction_id), {'data': {
            'reason': 'cancellation reason',
            'status': 'active',
            "cancellationOf": "lot",
            "relatedLot": lot_id
        }})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        cancellation = response.json['data']
        self.assertEqual(cancellation['reason'], 'cancellation reason')
        self.assertEqual(cancellation['status'], 'active')
        self.assertIn('id', cancellation)
        self.assertIn(cancellation['id'], response.headers['Location'])

        response = self.app.get('/auctions/{}'.format(self.auction_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['lots'][0]["status"], 'cancelled')
        self.assertNotEqual(response.json['data']["status"], 'cancelled')

        response = self.app.post_json('/auctions/{}/cancellations'.format(self.auction_id), {'data': {
            'reason': 'cancellation reason',
            'status': 'active',
            "cancellationOf": "lot",
            "relatedLot": lot_id
        }}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can add cancellation only in active lot status")

    def test_patch_auction_cancellation(self):
        lot_id = self.initial_lots[0]['id']
        response = self.app.post_json('/auctions/{}/cancellations'.format(self.auction_id), {'data': {
            'reason': 'cancellation reason',
            "cancellationOf": "lot",
            "relatedLot": lot_id
        }})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        cancellation = response.json['data']

        response = self.app.patch_json('/auctions/{}/cancellations/{}'.format(self.auction_id, cancellation['id']), {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "active")

        response = self.app.get('/auctions/{}'.format(self.auction_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['lots'][0]["status"], 'cancelled')
        self.assertNotEqual(response.json['data']["status"], 'cancelled')

        response = self.app.patch_json('/auctions/{}/cancellations/{}'.format(self.auction_id, cancellation['id']), {"data": {"status": "pending"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can update cancellation only in active lot status")

        response = self.app.get('/auctions/{}/cancellations/{}'.format(self.auction_id, cancellation['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "active")
        self.assertEqual(response.json['data']["reason"], "cancellation reason")


class AuctionCancellationDocumentResourceTest(BaseAuctionWebTest):

    def setUp(self):
        super(AuctionCancellationDocumentResourceTest, self).setUp()
        # Create cancellation
        response = self.app.post_json('/auctions/{}/cancellations'.format(
            self.auction_id), {'data': {'reason': 'cancellation reason'}})
        cancellation = response.json['data']
        self.cancellation_id = cancellation['id']

    def test_not_found(self):
        response = self.app.post('/auctions/some_id/cancellations/some_id/documents', status=404, upload_files=[
                                 ('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'auction_id'}
        ])

        response = self.app.post('/auctions/{}/cancellations/some_id/documents'.format(self.auction_id), status=404, upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'cancellation_id'}
        ])

        response = self.app.post('/auctions/{}/cancellations/{}/documents'.format(self.auction_id, self.cancellation_id), status=404, upload_files=[
                                 ('invalid_value', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'body', u'name': u'file'}
        ])

        response = self.app.get('/auctions/some_id/cancellations/some_id/documents', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'auction_id'}
        ])

        response = self.app.get('/auctions/{}/cancellations/some_id/documents'.format(self.auction_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'cancellation_id'}
        ])

        response = self.app.get('/auctions/some_id/cancellations/some_id/documents/some_id', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'auction_id'}
        ])

        response = self.app.get('/auctions/{}/cancellations/some_id/documents/some_id'.format(self.auction_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'cancellation_id'}
        ])

        response = self.app.get('/auctions/{}/cancellations/{}/documents/some_id'.format(self.auction_id, self.cancellation_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'document_id'}
        ])

        response = self.app.put('/auctions/some_id/cancellations/some_id/documents/some_id', status=404,
                                upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'auction_id'}
        ])

        response = self.app.put('/auctions/{}/cancellations/some_id/documents/some_id'.format(self.auction_id), status=404, upload_files=[
                                ('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'cancellation_id'}
        ])

        response = self.app.put('/auctions/{}/cancellations/{}/documents/some_id'.format(
            self.auction_id, self.cancellation_id), status=404, upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'document_id'}
        ])

    def test_create_auction_cancellation_document(self):
        response = self.app.post('/auctions/{}/cancellations/{}/documents'.format(
            self.auction_id, self.cancellation_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])
        self.assertEqual('name.doc', response.json["data"]["title"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/auctions/{}/cancellations/{}/documents'.format(self.auction_id, self.cancellation_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/auctions/{}/cancellations/{}/documents?all=true'.format(self.auction_id, self.cancellation_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/auctions/{}/cancellations/{}/documents/{}?download=some_id'.format(
            self.auction_id, self.cancellation_id, doc_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'download'}
        ])

        response = self.app.get('/auctions/{}/cancellations/{}/documents/{}?{}'.format(
            self.auction_id, self.cancellation_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 7)
        self.assertEqual(response.body, 'content')

        response = self.app.get('/auctions/{}/cancellations/{}/documents/{}'.format(
            self.auction_id, self.cancellation_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])

        self.set_status('complete')

        response = self.app.post('/auctions/{}/cancellations/{}/documents'.format(
            self.auction_id, self.cancellation_id), upload_files=[('file', 'name.doc', 'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add document in current (complete) auction status")

    def test_put_auction_cancellation_document(self):
        response = self.app.post('/auctions/{}/cancellations/{}/documents'.format(
            self.auction_id, self.cancellation_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.put('/auctions/{}/cancellations/{}/documents/{}'.format(self.auction_id, self.cancellation_id, doc_id),
                                status=404,
                                upload_files=[('invalid_name', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'body', u'name': u'file'}
        ])

        response = self.app.put('/auctions/{}/cancellations/{}/documents/{}'.format(
            self.auction_id, self.cancellation_id, doc_id), upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/auctions/{}/cancellations/{}/documents/{}?{}'.format(
            self.auction_id, self.cancellation_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 8)
        self.assertEqual(response.body, 'content2')

        response = self.app.get('/auctions/{}/cancellations/{}/documents/{}'.format(
            self.auction_id, self.cancellation_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])

        response = self.app.put('/auctions/{}/cancellations/{}/documents/{}'.format(
            self.auction_id, self.cancellation_id, doc_id), 'content3', content_type='application/msword')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/auctions/{}/cancellations/{}/documents/{}?{}'.format(
            self.auction_id, self.cancellation_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 8)
        self.assertEqual(response.body, 'content3')

        self.set_status('complete')

        response = self.app.put('/auctions/{}/cancellations/{}/documents/{}'.format(
            self.auction_id, self.cancellation_id, doc_id), upload_files=[('file', 'name.doc', 'content3')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current (complete) auction status")

    def test_patch_auction_cancellation_document(self):
        response = self.app.post('/auctions/{}/cancellations/{}/documents'.format(
            self.auction_id, self.cancellation_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.patch_json('/auctions/{}/cancellations/{}/documents/{}'.format(self.auction_id, self.cancellation_id, doc_id), {"data": {"description": "document description"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])

        response = self.app.get('/auctions/{}/cancellations/{}/documents/{}'.format(
            self.auction_id, self.cancellation_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('document description', response.json["data"]["description"])

        self.set_status('complete')

        response = self.app.patch_json('/auctions/{}/cancellations/{}/documents/{}'.format(self.auction_id, self.cancellation_id, doc_id), {"data": {"description": "document description"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current (complete) auction status")


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AuctionCancellationDocumentResourceTest))
    suite.addTest(unittest.makeSuite(AuctionCancellationResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
