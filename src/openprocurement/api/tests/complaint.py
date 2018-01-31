# -*- coding: utf-8 -*-
import unittest

from openprocurement.api.tests.base import BaseTenderWebTest, test_tender_data, test_lots, test_organization


class TenderComplaintResourceTest(BaseTenderWebTest):

    def test_create_tender_complaint_invalid(self):
        response = self.app.post_json('/tenders/some_id/complaints', {
                                      'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_organization}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'tender_id'}
        ])

        request_path = '/tenders/{}/complaints'.format(self.tender_id)

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

        response = self.app.post_json(request_path, {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_organization, 'relatedLot': '0' * 32}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'relatedLot should be one of lots'], u'location': u'body', u'name': u'relatedLot'}
        ])

    def test_create_tender_complaint(self):
        response = self.app.post_json('/tenders/{}/complaints'.format(
            self.tender_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_organization, 'status': 'claim'}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']
        status_date = response.json['data']['date']
        owner_token = response.json['access']['token']
        self.assertEqual(complaint['author']['name'], test_organization['name'])
        self.assertIn('id', complaint)
        self.assertIn(complaint['id'], response.headers['Location'])

        tender = self.db.get(self.tender_id)
        tender['status'] = 'active.awarded'
        tender['awardPeriod'] = {'endDate': '2014-01-01'}
        self.db.save(tender)

        response = self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(self.tender_id, complaint['id'], self.tender_token), {"data": {
            "status": "answered"
        }}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'This field is required.'], u'location': u'body', u'name': u'resolutionType'},
        ])

        response = self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(self.tender_id, complaint['id'], self.tender_token), {"data": {
            "status": "answered",
            "resolutionType": "invalid",
            "resolution": "spam 100% " * 3
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "answered")
        self.assertNotEqual(response.json['data']['date'], status_date)
        status_date = response.json['data']['date']
        self.assertEqual(response.json['data']["resolutionType"], "invalid")
        self.assertEqual(response.json['data']["resolution"], "spam 100% " * 3)

        response = self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(self.tender_id, complaint['id'], owner_token), {"data": {
            "satisfied": True,
            "status": "resolved"
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "resolved")
        self.assertNotEqual(response.json['data']['date'], status_date)

        response = self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(self.tender_id, complaint['id'], owner_token), {"data": {"status": "cancelled", "cancellationReason": "reason"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update complaint in current (resolved) status")

        response = self.app.get('/tenders/{}'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], 'active.awarded')

        self.set_status('unsuccessful')

        response = self.app.post_json('/tenders/{}/complaints'.format(
            self.tender_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_organization}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add complaint in current (unsuccessful) tender status")

    def test_patch_tender_complaint(self):
        response = self.app.post_json('/tenders/{}/complaints'.format(
            self.tender_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_organization}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']
        owner_token = response.json['access']['token']

        response = self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(self.tender_id, complaint['id'], self.tender_token), {"data": {
            "status": "cancelled",
            "cancellationReason": "reason"
        }}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Forbidden")

        response = self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(self.tender_id, complaint['id'], owner_token), {"data": {
            "title": "claim title",
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']["title"], "claim title")

        response = self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(self.tender_id, complaint['id'], owner_token), {"data": {
            "status": "claim",
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']["status"], "claim")

        response = self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(self.tender_id, complaint['id'], self.tender_token), {"data": {
            "resolution": "changing rules " * 2
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["resolution"], "changing rules " * 2)

        response = self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(self.tender_id, complaint['id'], self.tender_token), {"data": {
            "status": "answered",
            "resolutionType": "resolved",
            "resolution": "resolution text " * 2
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "answered")
        self.assertEqual(response.json['data']["resolutionType"], "resolved")
        self.assertEqual(response.json['data']["resolution"], "resolution text " * 2)

        response = self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(self.tender_id, complaint['id'], owner_token), {"data": {
            "satisfied": False
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["satisfied"], False)

        response = self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(self.tender_id, complaint['id'], owner_token), {"data": {
            "status": "resolved"
        }}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update complaint")

        response = self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(self.tender_id, complaint['id'], owner_token), {"data": {
            "status": "pending"
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "pending")

        response = self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(self.tender_id, complaint['id'], owner_token), {"data": {
            "status": "cancelled"
        }}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'This field is required.'], u'location': u'body', u'name': u'cancellationReason'},
        ])

        response = self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(self.tender_id, complaint['id'], owner_token), {"data": {
            "status": "cancelled",
            "cancellationReason": "reason"
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "cancelled")
        self.assertEqual(response.json['data']["cancellationReason"], "reason")

        response = self.app.patch_json('/tenders/{}/complaints/some_id'.format(self.tender_id), {"data": {"status": "resolved", "resolution": "resolution text"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.patch_json('/tenders/some_id/complaints/some_id', {"data": {"status": "resolved", "resolution": "resolution text"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.get('/tenders/{}/complaints/{}'.format(self.tender_id, complaint['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "cancelled")
        self.assertEqual(response.json['data']["cancellationReason"], "reason")
        self.assertEqual(response.json['data']["resolutionType"], "resolved")
        self.assertEqual(response.json['data']["resolution"], "resolution text " * 2)

        response = self.app.post_json('/tenders/{}/complaints'.format(
            self.tender_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_organization}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']
        owner_token = response.json['access']['token']

        self.set_status('complete')

        response = self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(self.tender_id, complaint['id'], owner_token), {"data": {
            "status": "claim",
        }}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update complaint in current (complete) tender status")

    def test_review_tender_complaint(self):
        complaints = []
        for i in range(3):
            response = self.app.post_json('/tenders/{}/complaints'.format(self.tender_id), {'data': {
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

            response = self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(self.tender_id, complaint['id'], self.tender_token), {"data": {
                "status": "answered",
                "resolutionType": "resolved",
                "resolution": "resolution text " * 2
            }})
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.json['data']["status"], "answered")
            self.assertEqual(response.json['data']["resolutionType"], "resolved")
            self.assertEqual(response.json['data']["resolution"], "resolution text " * 2)

            response = self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(self.tender_id, complaint['id'], owner_token), {"data": {
                "satisfied": False,
                "status": "pending"
            }})
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.json['data']["status"], "pending")

        self.app.authorization = ('Basic', ('reviewer', ''))
        for complaint, status in zip(complaints, ['invalid', 'resolved', 'declined']):
            response = self.app.patch_json('/tenders/{}/complaints/{}'.format(self.tender_id, complaint['id']), {"data": {
                "decision": '{} complaint'.format(status)
            }})
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.json['data']["decision"], '{} complaint'.format(status))

            response = self.app.patch_json('/tenders/{}/complaints/{}'.format(self.tender_id, complaint['id']), {"data": {
                "status": status
            }})
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.json['data']["status"], status)

    def test_get_tender_complaint(self):
        response = self.app.post_json('/tenders/{}/complaints'.format(
            self.tender_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_organization}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']
        del complaint['author']

        response = self.app.get('/tenders/{}/complaints/{}'.format(self.tender_id, complaint['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'], complaint)

        response = self.app.get('/tenders/{}/complaints/some_id'.format(self.tender_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.get('/tenders/some_id/complaints/some_id', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

    def test_get_tender_complaints(self):
        response = self.app.post_json('/tenders/{}/complaints'.format(
            self.tender_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_organization}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']
        del complaint['author']

        response = self.app.get('/tenders/{}/complaints'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'][0], complaint)

        response = self.app.get('/tenders/some_id/complaints', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])


class TenderLotAwardComplaintResourceTest(BaseTenderWebTest):
    initial_lots = test_lots

    def test_create_tender_complaint(self):
        response = self.app.post_json('/tenders/{}/complaints'.format(self.tender_id), {'data': {
            'title': 'complaint title',
            'description': 'complaint description',
            'author': test_organization,
            'relatedLot': self.initial_lots[0]['id'],
            'status': 'claim'
        }})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']
        owner_token = response.json['access']['token']
        self.assertEqual(complaint['author']['name'], test_organization['name'])
        self.assertIn('id', complaint)
        self.assertIn(complaint['id'], response.headers['Location'])

        tender = self.db.get(self.tender_id)
        tender['status'] = 'active.awarded'
        tender['awardPeriod'] = {'endDate': '2014-01-01'}
        self.db.save(tender)

        response = self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(self.tender_id, complaint['id'], self.tender_token), {"data": {
            "status": "answered"
        }}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'This field is required.'], u'location': u'body', u'name': u'resolutionType'},
        ])

        response = self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(self.tender_id, complaint['id'], self.tender_token), {"data": {
            "status": "answered",
            "resolutionType": "invalid",
            "resolution": "spam 100% " * 3
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "answered")
        self.assertEqual(response.json['data']["resolutionType"], "invalid")
        self.assertEqual(response.json['data']["resolution"], "spam 100% " * 3)

        response = self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(self.tender_id, complaint['id'], owner_token), {"data": {
            "satisfied": True,
            "status": "resolved"
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "resolved")

        response = self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(self.tender_id, complaint['id'], owner_token), {"data": {"status": "cancelled", "cancellationReason": "reason"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update complaint in current (resolved) status")

        response = self.app.get('/tenders/{}'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], 'active.awarded')

        self.set_status('unsuccessful')

        response = self.app.post_json('/tenders/{}/complaints'.format(
            self.tender_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_organization}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add complaint in current (unsuccessful) tender status")


class TenderComplaintDocumentResourceTest(BaseTenderWebTest):

    def setUp(self):
        super(TenderComplaintDocumentResourceTest, self).setUp()
        # Create complaint
        response = self.app.post_json('/tenders/{}/complaints'.format(
            self.tender_id), {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': test_organization}})
        complaint = response.json['data']
        self.complaint_id = complaint['id']
        self.complaint_owner_token = response.json['access']['token']

    def test_not_found(self):
        response = self.app.post('/tenders/some_id/complaints/some_id/documents', status=404, upload_files=[
                                 ('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.post('/tenders/{}/complaints/some_id/documents'.format(self.tender_id), status=404, upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.post('/tenders/{}/complaints/{}/documents'.format(self.tender_id, self.complaint_id), status=404, upload_files=[
                                 ('invalid_value', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'body', u'name': u'file'}
        ])

        response = self.app.get('/tenders/some_id/complaints/some_id/documents', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.get('/tenders/{}/complaints/some_id/documents'.format(self.tender_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.get('/tenders/some_id/complaints/some_id/documents/some_id', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.get('/tenders/{}/complaints/some_id/documents/some_id'.format(self.tender_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.get('/tenders/{}/complaints/{}/documents/some_id'.format(self.tender_id, self.complaint_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'document_id'}
        ])

        response = self.app.put('/tenders/some_id/complaints/some_id/documents/some_id', status=404,
                                upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.put('/tenders/{}/complaints/some_id/documents/some_id'.format(self.tender_id), status=404, upload_files=[
                                ('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.put('/tenders/{}/complaints/{}/documents/some_id'.format(
            self.tender_id, self.complaint_id), status=404, upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'document_id'}
        ])

    def test_create_tender_complaint_document(self):
        response = self.app.post('/tenders/{}/complaints/{}/documents'.format(
            self.tender_id, self.complaint_id), upload_files=[('file', 'name.doc', 'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add document in current (draft) complaint status")

        response = self.app.post('/tenders/{}/complaints/{}/documents?acc_token={}'.format(
            self.tender_id, self.complaint_id, self.complaint_owner_token), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])
        self.assertEqual('name.doc', response.json["data"]["title"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/tenders/{}/complaints/{}/documents'.format(self.tender_id, self.complaint_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/tenders/{}/complaints/{}/documents?all=true'.format(self.tender_id, self.complaint_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/tenders/{}/complaints/{}/documents/{}?download=some_id'.format(
            self.tender_id, self.complaint_id, doc_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'download'}
        ])

        response = self.app.get('/tenders/{}/complaints/{}/documents/{}?{}'.format(
            self.tender_id, self.complaint_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 7)
        self.assertEqual(response.body, 'content')

        response = self.app.get('/tenders/{}/complaints/{}/documents/{}'.format(
            self.tender_id, self.complaint_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])

        self.set_status('complete')

        response = self.app.post('/tenders/{}/complaints/{}/documents'.format(
            self.tender_id, self.complaint_id), upload_files=[('file', 'name.doc', 'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add document in current (complete) tender status")

    def test_put_tender_complaint_document(self):
        response = self.app.post('/tenders/{}/complaints/{}/documents?acc_token={}'.format(
            self.tender_id, self.complaint_id, self.complaint_owner_token), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.put('/tenders/{}/complaints/{}/documents/{}'.format(self.tender_id, self.complaint_id, doc_id),
                                status=404,
                                upload_files=[('invalid_name', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'body', u'name': u'file'}
        ])

        response = self.app.put('/tenders/{}/complaints/{}/documents/{}'.format(
            self.tender_id, self.complaint_id, doc_id), upload_files=[('file', 'name.doc', 'content2')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can update document only author")

        response = self.app.put('/tenders/{}/complaints/{}/documents/{}?acc_token={}'.format(
            self.tender_id, self.complaint_id, doc_id, self.complaint_owner_token), upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/tenders/{}/complaints/{}/documents/{}?{}'.format(
            self.tender_id, self.complaint_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 8)
        self.assertEqual(response.body, 'content2')

        response = self.app.get('/tenders/{}/complaints/{}/documents/{}'.format(
            self.tender_id, self.complaint_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])

        response = self.app.put('/tenders/{}/complaints/{}/documents/{}?acc_token={}'.format(
            self.tender_id, self.complaint_id, doc_id, self.complaint_owner_token), 'content3', content_type='application/msword')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/tenders/{}/complaints/{}/documents/{}?{}'.format(
            self.tender_id, self.complaint_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 8)
        self.assertEqual(response.body, 'content3')

        response = self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.complaint_id, self.complaint_owner_token), {"data": {
            "status": "claim",
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']["status"], "claim")

        response = self.app.put('/tenders/{}/complaints/{}/documents/{}?acc_token={}'.format(self.tender_id, self.complaint_id, doc_id, self.complaint_owner_token), 'content', content_type='application/msword', status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current (claim) complaint status")

        self.set_status('complete')

        response = self.app.put('/tenders/{}/complaints/{}/documents/{}?acc_token={}'.format(
            self.tender_id, self.complaint_id, doc_id, self.complaint_owner_token), upload_files=[('file', 'name.doc', 'content3')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current (complete) tender status")

    def test_patch_tender_complaint_document(self):
        response = self.app.post('/tenders/{}/complaints/{}/documents?acc_token={}'.format(
            self.tender_id, self.complaint_id, self.complaint_owner_token), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.patch_json('/tenders/{}/complaints/{}/documents/{}'.format(self.tender_id, self.complaint_id, doc_id), {"data": {"description": "document description"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can update document only author")

        response = self.app.patch_json('/tenders/{}/complaints/{}/documents/{}?acc_token={}'.format(self.tender_id, self.complaint_id, doc_id, self.complaint_owner_token), {"data": {"description": "document description"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])

        response = self.app.get('/tenders/{}/complaints/{}/documents/{}'.format(
            self.tender_id, self.complaint_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('document description', response.json["data"]["description"])

        response = self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.complaint_id, self.complaint_owner_token), {"data": {
            "status": "claim",
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']["status"], "claim")

        response = self.app.patch_json('/tenders/{}/complaints/{}/documents/{}?acc_token={}'.format(self.tender_id, self.complaint_id, doc_id, self.complaint_owner_token), {"data": {"description": "document description"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current (claim) complaint status")

        self.set_status('complete')

        response = self.app.patch_json('/tenders/{}/complaints/{}/documents/{}?acc_token={}'.format(self.tender_id, self.complaint_id, doc_id, self.complaint_owner_token), {"data": {"description": "document description"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current (complete) tender status")


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TenderComplaintDocumentResourceTest))
    suite.addTest(unittest.makeSuite(TenderComplaintResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
