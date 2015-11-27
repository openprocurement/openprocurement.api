# -*- coding: utf-8 -*-
import unittest

from openprocurement.api.tests.base import BaseAuctionWebTest, test_auction_data


class AuctionComplaintResourceTest(BaseAuctionWebTest):

    def test_create_auction_complaint_invalid(self):
        response = self.app.post_json('/auctions/some_id/complaints', {
                                      'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_auction_data["procuringEntity"]}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'auction_id'}
        ])

        request_path = '/auctions/{}/complaints'.format(self.auction_id)

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
                                      'data': {'title': 'complaint title', 'description': 'complaint description', 'author': {'identifier': {}}}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': {u'contactPoint': [u'This field is required.'], u'identifier': {u'scheme': [u'This field is required.'], u'id': [u'This field is required.']}, u'name': [u'This field is required.'], u'address': [u'This field is required.']}, u'location': u'body', u'name': u'author'}
        ])

        response = self.app.post_json(request_path, {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': {
            'name': 'name', 'identifier': {'uri': 'invalid_value'}}}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': {u'contactPoint': [u'This field is required.'], u'identifier': {u'scheme': [u'This field is required.'], u'id': [u'This field is required.'], u'uri': [u'Not a well formed URL.']}, u'address': [u'This field is required.']}, u'location': u'body', u'name': u'author'}
        ])

    def test_create_auction_complaint(self):
        response = self.app.post_json('/auctions/{}/complaints'.format(
            self.auction_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_auction_data["procuringEntity"]}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']
        self.assertEqual(complaint['author']['name'], test_auction_data["procuringEntity"]['name'])
        self.assertIn('id', complaint)
        self.assertIn(complaint['id'], response.headers['Location'])

        authorization = self.app.authorization
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json('/auctions/{}'.format(self.auction_id), {'data': {'status': 'active.awarded', 'awardPeriod': {'endDate': '2014-01-01'}}})
        self.app.authorization = authorization
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.patch_json('/auctions/{}/complaints/{}'.format(self.auction_id, complaint['id']), {"data": {"status": "cancelled"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't cancel complaint")

        response = self.app.patch_json('/auctions/{}/complaints/{}'.format(self.auction_id, complaint['id']), {"data": {"status": "invalid", "resolution": "resolution text"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "invalid")
        self.assertEqual(response.json['data']["resolution"], "resolution text")

        response = self.app.get('/auctions/{}'.format(self.auction_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], 'active.awarded')

        self.set_status('unsuccessful')

        response = self.app.post_json('/auctions/{}/complaints'.format(
            self.auction_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_auction_data["procuringEntity"]}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add complaint in current (unsuccessful) auction status")

    def test_patch_auction_complaint(self):
        response = self.app.post_json('/auctions/{}/complaints'.format(
            self.auction_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_auction_data["procuringEntity"]}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']

        response = self.app.patch_json('/auctions/{}/complaints/{}'.format(self.auction_id, complaint['id']), {"data": {"status": "resolved", "resolution": "resolution text"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "resolved")
        self.assertEqual(response.json['data']["resolution"], "resolution text")

        response = self.app.patch_json('/auctions/{}/complaints/{}'.format(self.auction_id, complaint['id']), {"data": {"status": "pending"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update complaint in current (resolved) status")

        response = self.app.patch_json('/auctions/{}/complaints/some_id'.format(self.auction_id), {"data": {"status": "resolved", "resolution": "resolution text"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.patch_json('/auctions/some_id/complaints/some_id', {"data": {"status": "resolved", "resolution": "resolution text"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'auction_id'}
        ])

        response = self.app.get('/auctions/{}/complaints/{}'.format(self.auction_id, complaint['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "resolved")
        self.assertEqual(response.json['data']["resolution"], "resolution text")

        self.set_status('complete')

        response = self.app.patch_json('/auctions/{}/complaints/{}'.format(self.auction_id, complaint['id']), {"data": {"status": "resolved", "resolution": "resolution text"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update complaint in current (complete) auction status")

    def test_get_auction_complaint(self):
        response = self.app.post_json('/auctions/{}/complaints'.format(
            self.auction_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_auction_data["procuringEntity"]}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']

        response = self.app.get('/auctions/{}/complaints/{}'.format(self.auction_id, complaint['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'], complaint)

        response = self.app.get('/auctions/{}/complaints/some_id'.format(self.auction_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.get('/auctions/some_id/complaints/some_id', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'auction_id'}
        ])

    def test_get_auction_complaints(self):
        response = self.app.post_json('/auctions/{}/complaints'.format(
            self.auction_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_auction_data["procuringEntity"]}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']

        response = self.app.get('/auctions/{}/complaints'.format(self.auction_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'][0], complaint)

        response = self.app.get('/auctions/some_id/complaints', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'auction_id'}
        ])


class AuctionComplaintDocumentResourceTest(BaseAuctionWebTest):

    def setUp(self):
        super(AuctionComplaintDocumentResourceTest, self).setUp()
        # Create complaint
        response = self.app.post_json('/auctions/{}/complaints'.format(
            self.auction_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_auction_data["procuringEntity"]}})
        complaint = response.json['data']
        self.complaint_id = complaint['id']

    def test_not_found(self):
        response = self.app.post('/auctions/some_id/complaints/some_id/documents', status=404, upload_files=[
                                 ('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'auction_id'}
        ])

        response = self.app.post('/auctions/{}/complaints/some_id/documents'.format(self.auction_id), status=404, upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.post('/auctions/{}/complaints/{}/documents'.format(self.auction_id, self.complaint_id), status=404, upload_files=[
                                 ('invalid_value', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'body', u'name': u'file'}
        ])

        response = self.app.get('/auctions/some_id/complaints/some_id/documents', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'auction_id'}
        ])

        response = self.app.get('/auctions/{}/complaints/some_id/documents'.format(self.auction_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.get('/auctions/some_id/complaints/some_id/documents/some_id', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'auction_id'}
        ])

        response = self.app.get('/auctions/{}/complaints/some_id/documents/some_id'.format(self.auction_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.get('/auctions/{}/complaints/{}/documents/some_id'.format(self.auction_id, self.complaint_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'document_id'}
        ])

        response = self.app.put('/auctions/some_id/complaints/some_id/documents/some_id', status=404,
                                upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'auction_id'}
        ])

        response = self.app.put('/auctions/{}/complaints/some_id/documents/some_id'.format(self.auction_id), status=404, upload_files=[
                                ('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.put('/auctions/{}/complaints/{}/documents/some_id'.format(
            self.auction_id, self.complaint_id), status=404, upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'document_id'}
        ])

    def test_create_auction_complaint_document(self):
        response = self.app.post('/auctions/{}/complaints/{}/documents'.format(
            self.auction_id, self.complaint_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])
        self.assertEqual('name.doc', response.json["data"]["title"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/auctions/{}/complaints/{}/documents'.format(self.auction_id, self.complaint_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/auctions/{}/complaints/{}/documents?all=true'.format(self.auction_id, self.complaint_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/auctions/{}/complaints/{}/documents/{}?download=some_id'.format(
            self.auction_id, self.complaint_id, doc_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'download'}
        ])

        response = self.app.get('/auctions/{}/complaints/{}/documents/{}?{}'.format(
            self.auction_id, self.complaint_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 7)
        self.assertEqual(response.body, 'content')

        response = self.app.get('/auctions/{}/complaints/{}/documents/{}'.format(
            self.auction_id, self.complaint_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])

        self.set_status('complete')

        response = self.app.post('/auctions/{}/complaints/{}/documents'.format(
            self.auction_id, self.complaint_id), upload_files=[('file', 'name.doc', 'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add document in current (complete) auction status")

    def test_put_auction_complaint_document(self):
        response = self.app.post('/auctions/{}/complaints/{}/documents'.format(
            self.auction_id, self.complaint_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.put('/auctions/{}/complaints/{}/documents/{}'.format(self.auction_id, self.complaint_id, doc_id),
                                status=404,
                                upload_files=[('invalid_name', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'body', u'name': u'file'}
        ])

        response = self.app.put('/auctions/{}/complaints/{}/documents/{}'.format(
            self.auction_id, self.complaint_id, doc_id), upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/auctions/{}/complaints/{}/documents/{}?{}'.format(
            self.auction_id, self.complaint_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 8)
        self.assertEqual(response.body, 'content2')

        response = self.app.get('/auctions/{}/complaints/{}/documents/{}'.format(
            self.auction_id, self.complaint_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])

        response = self.app.put('/auctions/{}/complaints/{}/documents/{}'.format(
            self.auction_id, self.complaint_id, doc_id), 'content3', content_type='application/msword')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/auctions/{}/complaints/{}/documents/{}?{}'.format(
            self.auction_id, self.complaint_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 8)
        self.assertEqual(response.body, 'content3')

        self.set_status('complete')

        response = self.app.put('/auctions/{}/complaints/{}/documents/{}'.format(
            self.auction_id, self.complaint_id, doc_id), upload_files=[('file', 'name.doc', 'content3')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current (complete) auction status")

    def test_patch_auction_complaint_document(self):
        response = self.app.post('/auctions/{}/complaints/{}/documents'.format(
            self.auction_id, self.complaint_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.patch_json('/auctions/{}/complaints/{}/documents/{}'.format(self.auction_id, self.complaint_id, doc_id), {"data": {"description": "document description"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])

        response = self.app.get('/auctions/{}/complaints/{}/documents/{}'.format(
            self.auction_id, self.complaint_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('document description', response.json["data"]["description"])

        self.set_status('complete')

        response = self.app.patch_json('/auctions/{}/complaints/{}/documents/{}'.format(self.auction_id, self.complaint_id, doc_id), {"data": {"description": "document description"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current (complete) auction status")


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AuctionComplaintDocumentResourceTest))
    suite.addTest(unittest.makeSuite(AuctionComplaintResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
