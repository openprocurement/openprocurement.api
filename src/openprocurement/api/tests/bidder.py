# -*- coding: utf-8 -*-
import unittest

from openprocurement.api.tests.base import BaseTenderWebTest, test_tender_data, test_features_tender_data, test_organization


class TenderBidderResourceTest(BaseTenderWebTest):
    initial_status = 'active.tendering'

    def test_create_tender_bidder_invalid(self):
        response = self.app.post_json('/tenders/some_id/bids', {
                                      'data': {'tenderers': [test_organization], "value": {"amount": 500}}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        request_path = '/tenders/{}/bids'.format(self.tender_id)
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
                                      'data': {'tenderers': [{'identifier': 'invalid_value'}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': {u'identifier': [
                u'Please use a mapping for this field or Identifier instance instead of unicode.']}, u'location': u'body', u'name': u'tenderers'}
        ])

        response = self.app.post_json(request_path, {
                                      'data': {'tenderers': [{'identifier': {}}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [{u'contactPoint': [u'This field is required.'], u'identifier': {u'scheme': [u'This field is required.'], u'id': [u'This field is required.']}, u'name': [u'This field is required.'], u'address': [u'This field is required.']}], u'location': u'body', u'name': u'tenderers'}
        ])

        response = self.app.post_json(request_path, {'data': {'tenderers': [{
            'name': 'name', 'identifier': {'uri': 'invalid_value'}}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [{u'contactPoint': [u'This field is required.'], u'identifier': {u'scheme': [u'This field is required.'], u'id': [u'This field is required.'], u'uri': [u'Not a well formed URL.']}, u'address': [u'This field is required.']}], u'location': u'body', u'name': u'tenderers'}
        ])

        response = self.app.post_json(request_path, {'data': {'tenderers': [test_organization]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'This field is required.'], u'location': u'body', u'name': u'value'}
        ])

        response = self.app.post_json(request_path, {'data': {'tenderers': [test_organization], "value": {"amount": 500, 'valueAddedTaxPayer': False}}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'valueAddedTaxPayer of bid should be identical to valueAddedTaxIncluded of value of tender'], u'location': u'body', u'name': u'value'}
        ])

        response = self.app.post_json(request_path, {'data': {'tenderers': [test_organization], "value": {"amount": 500, 'currency': "USD"}}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'currency of bid should be identical to currency of value of tender'], u'location': u'body', u'name': u'value'},
        ])

        response = self.app.post_json(request_path, {'data': {'tenderers': test_organization, "value": {"amount": 500}}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u"invalid literal for int() with base 10: 'contactPoint'", u'location': u'body', u'name': u'data'},
        ])

    def test_create_tender_bidder(self):
        dateModified = self.db.get(self.tender_id).get('dateModified')

        response = self.app.post_json('/tenders/{}/bids'.format(
            self.tender_id), {'data': {'tenderers': [test_organization], "value": {"amount": 500}}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        bidder = response.json['data']
        self.assertEqual(bidder['tenderers'][0]['name'], test_organization['name'])
        self.assertIn('id', bidder)
        self.assertIn(bidder['id'], response.headers['Location'])

        self.assertEqual(self.db.get(self.tender_id).get('dateModified'), dateModified)

        self.set_status('complete')

        response = self.app.post_json('/tenders/{}/bids'.format(
            self.tender_id), {'data': {'tenderers': [test_organization], "value": {"amount": 500}}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add bid in current (complete) tender status")

    def test_patch_tender_bidder(self):
        response = self.app.post_json('/tenders/{}/bids'.format(
            self.tender_id), {'data': {'tenderers': [test_organization], "status": "draft", "value": {"amount": 500}}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        bidder = response.json['data']

        response = self.app.patch_json('/tenders/{}/bids/{}'.format(self.tender_id, bidder['id']), {"data": {"value": {"amount": 600}}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'value of bid should be less than value of tender'], u'location': u'body', u'name': u'value'}
        ])

        response = self.app.patch_json('/tenders/{}/bids/{}'.format(self.tender_id, bidder['id']), {"data": {'tenderers': [{"name": u"Державне управління управлінням справами"}]}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['date'], bidder['date'])
        self.assertNotEqual(response.json['data']['tenderers'][0]['name'], bidder['tenderers'][0]['name'])

        response = self.app.patch_json('/tenders/{}/bids/{}'.format(self.tender_id, bidder['id']), {"data": {"value": {"amount": 500}, 'tenderers': [test_organization]}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['date'], bidder['date'])
        self.assertEqual(response.json['data']['tenderers'][0]['name'], bidder['tenderers'][0]['name'])

        response = self.app.patch_json('/tenders/{}/bids/{}'.format(self.tender_id, bidder['id']), {"data": {"value": {"amount": 400}}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["value"]["amount"], 400)
        self.assertNotEqual(response.json['data']['date'], bidder['date'])

        response = self.app.patch_json('/tenders/{}/bids/{}'.format(self.tender_id, bidder['id']), {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "active")
        self.assertNotEqual(response.json['data']['date'], bidder['date'])

        response = self.app.patch_json('/tenders/{}/bids/{}'.format(self.tender_id, bidder['id']), {"data": {"status": "draft"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can\'t update bid to (draft) status")

        response = self.app.patch_json('/tenders/{}/bids/some_id'.format(self.tender_id), {"data": {"value": {"amount": 400}}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'bid_id'}
        ])

        response = self.app.patch_json('/tenders/some_id/bids/some_id', {"data": {"value": {"amount": 400}}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        self.set_status('complete')

        response = self.app.get('/tenders/{}/bids/{}'.format(self.tender_id, bidder['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["value"]["amount"], 400)

        response = self.app.patch_json('/tenders/{}/bids/{}'.format(self.tender_id, bidder['id']), {"data": {"value": {"amount": 400}}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update bid in current (complete) tender status")

    def test_get_tender_bidder(self):
        response = self.app.post_json('/tenders/{}/bids'.format(
            self.tender_id), {'data': {'tenderers': [test_organization], "value": {"amount": 500}}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        bidder = response.json['data']
        bid_token = response.json['access']['token']

        response = self.app.get('/tenders/{}/bids/{}'.format(self.tender_id, bidder['id']), status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't view bid in current (active.tendering) tender status")

        response = self.app.get('/tenders/{}/bids/{}?acc_token={}'.format(self.tender_id, bidder['id'], bid_token))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'], bidder)

        self.set_status('active.qualification')

        response = self.app.get('/tenders/{}/bids/{}'.format(self.tender_id, bidder['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        bidder_data = response.json['data']
        #self.assertIn(u'participationUrl', bidder_data)
        #bidder_data.pop(u'participationUrl')
        self.assertEqual(bidder_data, bidder)

        response = self.app.get('/tenders/{}/bids/some_id'.format(self.tender_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'bid_id'}
        ])

        response = self.app.get('/tenders/some_id/bids/some_id', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.delete('/tenders/{}/bids/{}'.format(self.tender_id, bidder['id']), status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't delete bid in current (active.qualification) tender status")

    def test_delete_tender_bidder(self):
        response = self.app.post_json('/tenders/{}/bids'.format(
            self.tender_id), {'data': {'tenderers': [test_organization], "value": {"amount": 500}}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        bidder = response.json['data']

        response = self.app.delete('/tenders/{}/bids/{}'.format(self.tender_id, bidder['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'], bidder)

        revisions = self.db.get(self.tender_id).get('revisions')
        self.assertTrue(any([i for i in revisions[-2][u'changes'] if i['op'] == u'remove' and i['path'] == u'/bids']))
        self.assertTrue(any([i for i in revisions[-1][u'changes'] if i['op'] == u'add' and i['path'] == u'/bids']))

        response = self.app.delete('/tenders/{}/bids/some_id'.format(self.tender_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'bid_id'}
        ])

        response = self.app.delete('/tenders/some_id/bids/some_id', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

    def test_get_tender_tenderers(self):
        response = self.app.post_json('/tenders/{}/bids'.format(
            self.tender_id), {'data': {'tenderers': [test_organization], "value": {"amount": 500}}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        bidder = response.json['data']

        response = self.app.get('/tenders/{}/bids'.format(self.tender_id), status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't view bids in current (active.tendering) tender status")

        self.set_status('active.qualification')

        response = self.app.get('/tenders/{}/bids'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'][0], bidder)

        response = self.app.get('/tenders/some_id/bids', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

    def test_bid_Administrator_change(self):
        response = self.app.post_json('/tenders/{}/bids'.format(
            self.tender_id), {'data': {'tenderers': [test_organization], "value": {"amount": 500}}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        bidder = response.json['data']

        self.app.authorization = ('Basic', ('administrator', ''))
        response = self.app.patch_json('/tenders/{}/bids/{}'.format(self.tender_id, bidder['id']), {"data": {
            'tenderers': [{"identifier": {"id": "00000000"}}],
            "value": {"amount": 400}
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertNotEqual(response.json['data']["value"]["amount"], 400)
        self.assertEqual(response.json['data']["tenderers"][0]["identifier"]["id"], "00000000")


class TenderBidderFeaturesResourceTest(BaseTenderWebTest):
    initial_data = test_features_tender_data
    initial_status = 'active.tendering'

    def test_features_bidder(self):
        test_features_bids = [
            {
                "parameters": [
                    {
                        "code": i["code"],
                        "value": 0.1,
                    }
                    for i in self.initial_data['features']
                ],
                "status": "active",
                "tenderers": [
                    test_organization
                ],
                "value": {
                    "amount": 469,
                    "currency": "UAH",
                    "valueAddedTaxPayer": True,
                    "valueAddedTax": 20
                }
            },
            {
                "parameters": [
                    {
                        "code": i["code"],
                        "value": 0.15,
                    }
                    for i in self.initial_data['features']
                ],
                "tenderers": [
                    test_organization
                ],
                "status": "draft",
                "value": {
                    "amount": 479,
                    "currency": "UAH",
                    "valueAddedTaxPayer": True,
                    "valueAddedTax": 20
                }
            }
        ]
        for i in test_features_bids:
            response = self.app.post_json('/tenders/{}/bids'.format(self.tender_id), {'data': i})
            self.assertEqual(response.status, '201 Created')
            self.assertEqual(response.content_type, 'application/json')
            bid = response.json['data']
            bid.pop(u'date')
            bid.pop(u'id')
            self.assertEqual(bid, i)

    def test_features_bidder_invalid(self):
        data = {
            "tenderers": [
                test_organization
            ],
            "value": {
                "amount": 469,
                "currency": "UAH",
                "valueAddedTaxPayer": True
            }
        }
        response = self.app.post_json('/tenders/{}/bids'.format(self.tender_id), {'data': data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'This field is required.'], u'location': u'body', u'name': u'parameters'}
        ])
        data["parameters"] = [
            {
                "code": "OCDS-123454-AIR-INTAKE",
                "value": 0.1,
            }
        ]
        response = self.app.post_json('/tenders/{}/bids'.format(self.tender_id), {'data': data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'All features parameters is required.'], u'location': u'body', u'name': u'parameters'}
        ])
        data["parameters"].append({
            "code": "OCDS-123454-AIR-INTAKE",
            "value": 0.1,
        })
        response = self.app.post_json('/tenders/{}/bids'.format(self.tender_id), {'data': data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'Parameter code should be uniq for all parameters'], u'location': u'body', u'name': u'parameters'}
        ])
        data["parameters"][1]["code"] = "OCDS-123454-YEARS"
        data["parameters"][1]["value"] = 0.2
        response = self.app.post_json('/tenders/{}/bids'.format(self.tender_id), {'data': data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [{u'value': [u'value should be one of feature value.']}], u'location': u'body', u'name': u'parameters'}
        ])


class TenderBidderDocumentResourceTest(BaseTenderWebTest):
    initial_status = 'active.tendering'

    def setUp(self):
        super(TenderBidderDocumentResourceTest, self).setUp()
        # Create bid
        response = self.app.post_json('/tenders/{}/bids'.format(
            self.tender_id), {'data': {'tenderers': [test_organization], "value": {"amount": 500}}})
        bid = response.json['data']
        self.bid_id = bid['id']
        self.bid_token = response.json['access']['token']

    def test_not_found(self):
        response = self.app.post('/tenders/some_id/bids/some_id/documents', status=404, upload_files=[
                                 ('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.post('/tenders/{}/bids/some_id/documents'.format(self.tender_id), status=404, upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'bid_id'}
        ])

        response = self.app.post('/tenders/{}/bids/{}/documents'.format(self.tender_id, self.bid_id), status=404, upload_files=[
                                 ('invalid_value', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'body', u'name': u'file'}
        ])

        response = self.app.get('/tenders/some_id/bids/some_id/documents', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.get('/tenders/{}/bids/some_id/documents'.format(self.tender_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'bid_id'}
        ])

        response = self.app.get('/tenders/some_id/bids/some_id/documents/some_id', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.get('/tenders/{}/bids/some_id/documents/some_id'.format(self.tender_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'bid_id'}
        ])

        response = self.app.get('/tenders/{}/bids/{}/documents/some_id'.format(self.tender_id, self.bid_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'document_id'}
        ])

        response = self.app.put('/tenders/some_id/bids/some_id/documents/some_id', status=404,
                                upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.put('/tenders/{}/bids/some_id/documents/some_id'.format(self.tender_id), status=404, upload_files=[
                                ('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'bid_id'}
        ])

        response = self.app.put('/tenders/{}/bids/{}/documents/some_id'.format(
            self.tender_id, self.bid_id), status=404, upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'document_id'}
        ])

        self.app.authorization = ('Basic', ('invalid', ''))
        response = self.app.put('/tenders/{}/bids/{}/documents/some_id'.format(
            self.tender_id, self.bid_id), status=404, upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'document_id'}
        ])

    def test_create_tender_bidder_document(self):
        response = self.app.post('/tenders/{}/bids/{}/documents'.format(
            self.tender_id, self.bid_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])
        self.assertEqual('name.doc', response.json["data"]["title"])
        key = response.json["data"]["url"].split('?')[-1].split('=')[-1]

        response = self.app.get('/tenders/{}/bids/{}/documents'.format(self.tender_id, self.bid_id), status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't view bid documents in current (active.tendering) tender status")

        response = self.app.get('/tenders/{}/bids/{}/documents?acc_token={}'.format(self.tender_id, self.bid_id, self.bid_token))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/tenders/{}/bids/{}/documents?all=true&acc_token={}'.format(self.tender_id, self.bid_id, self.bid_token))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/tenders/{}/bids/{}/documents/{}?download=some_id&acc_token={}'.format(
            self.tender_id, self.bid_id, doc_id, self.bid_token), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'download'}
        ])

        response = self.app.get('/tenders/{}/bids/{}/documents/{}?download={}'.format(
            self.tender_id, self.bid_id, doc_id, key), status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't view bid document in current (active.tendering) tender status")

        if self.docservice:
            response = self.app.get('/tenders/{}/bids/{}/documents/{}?download={}&acc_token={}'.format(
                self.tender_id, self.bid_id, doc_id, key, self.bid_token))
            self.assertEqual(response.status, '302 Moved Temporarily')
            self.assertIn('http://localhost/get/', response.location)
            self.assertIn('Signature=', response.location)
            self.assertIn('KeyID=', response.location)
            self.assertIn('Expires=', response.location)
        else:
            response = self.app.get('/tenders/{}/bids/{}/documents/{}?download={}&acc_token={}'.format(
                self.tender_id, self.bid_id, doc_id, key, self.bid_token))
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/msword')
            self.assertEqual(response.content_length, 7)
            self.assertEqual(response.body, 'content')

        response = self.app.get('/tenders/{}/bids/{}/documents/{}'.format(
            self.tender_id, self.bid_id, doc_id), status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't view bid document in current (active.tendering) tender status")

        response = self.app.get('/tenders/{}/bids/{}/documents/{}?acc_token={}'.format(
            self.tender_id, self.bid_id, doc_id, self.bid_token))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])

        self.set_status('active.awarded')

        response = self.app.post('/tenders/{}/bids/{}/documents'.format(
            self.tender_id, self.bid_id), upload_files=[('file', 'name.doc', 'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add document in current (active.awarded) tender status")

        response = self.app.get('/tenders/{}/bids/{}/documents/{}'.format(self.tender_id, self.bid_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        if self.docservice:
            self.assertIn('http://localhost/get/', response.json['data']['url'])
            self.assertIn('Signature=', response.json['data']['url'])
            self.assertIn('KeyID=', response.json['data']['url'])
            self.assertNotIn('Expires=', response.json['data']['url'])
        else:
            self.assertIn('download=', response.json['data']['url'])

        response = self.app.get('/tenders/{}/bids/{}/documents/{}?download={}&acc_token={}'.format(
            self.tender_id, self.bid_id, doc_id, key, self.bid_token))
        if self.docservice:
            self.assertIn('http://localhost/get/', response.location)
            self.assertIn('Signature=', response.location)
            self.assertIn('KeyID=', response.location)
            self.assertIn('Expires=', response.location)
        else:
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/msword')
            self.assertEqual(response.content_length, 7)
            self.assertEqual(response.body, 'content')

    def test_put_tender_bidder_document(self):
        response = self.app.post('/tenders/{}/bids/{}/documents'.format(
            self.tender_id, self.bid_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.put('/tenders/{}/bids/{}/documents/{}'.format(self.tender_id, self.bid_id, doc_id),
                                status=404,
                                upload_files=[('invalid_name', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'body', u'name': u'file'}
        ])

        response = self.app.put('/tenders/{}/bids/{}/documents/{}'.format(
            self.tender_id, self.bid_id, doc_id), upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/tenders/{}/bids/{}/documents/{}?{}&acc_token={}'.format(
            self.tender_id, self.bid_id, doc_id, key, self.bid_token))
        if self.docservice:
            self.assertEqual(response.status, '302 Moved Temporarily')
            self.assertIn('http://localhost/get/', response.location)
            self.assertIn('Signature=', response.location)
            self.assertIn('KeyID=', response.location)
            self.assertIn('Expires=', response.location)
        else:
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/msword')
            self.assertEqual(response.content_length, 8)
            self.assertEqual(response.body, 'content2')

        response = self.app.get('/tenders/{}/bids/{}/documents/{}?acc_token={}'.format(
            self.tender_id, self.bid_id, doc_id, self.bid_token))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])

        response = self.app.put('/tenders/{}/bids/{}/documents/{}'.format(
            self.tender_id, self.bid_id, doc_id), 'content3', content_type='application/msword')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/tenders/{}/bids/{}/documents/{}?{}&acc_token={}'.format(
            self.tender_id, self.bid_id, doc_id, key, self.bid_token))
        if self.docservice:
            self.assertEqual(response.status, '302 Moved Temporarily')
            self.assertIn('http://localhost/get/', response.location)
            self.assertIn('Signature=', response.location)
            self.assertIn('KeyID=', response.location)
            self.assertIn('Expires=', response.location)
        else:
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/msword')
            self.assertEqual(response.content_length, 8)
            self.assertEqual(response.body, 'content3')

        self.set_status('active.awarded')

        response = self.app.put('/tenders/{}/bids/{}/documents/{}'.format(
            self.tender_id, self.bid_id, doc_id), upload_files=[('file', 'name.doc', 'content3')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current (active.awarded) tender status")

    def test_patch_tender_bidder_document(self):
        response = self.app.post('/tenders/{}/bids/{}/documents'.format(
            self.tender_id, self.bid_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.patch_json('/tenders/{}/bids/{}/documents/{}'.format(self.tender_id, self.bid_id, doc_id), {"data": {
            "documentOf": "lot"
        }}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'This field is required.'], u'location': u'body', u'name': u'relatedItem'},
        ])

        response = self.app.patch_json('/tenders/{}/bids/{}/documents/{}'.format(self.tender_id, self.bid_id, doc_id), {"data": {
            "documentOf": "lot",
            "relatedItem": '0' * 32
        }}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'relatedItem should be one of lots'], u'location': u'body', u'name': u'relatedItem'}
        ])

        response = self.app.patch_json('/tenders/{}/bids/{}/documents/{}'.format(self.tender_id, self.bid_id, doc_id), {"data": {"description": "document description"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])

        response = self.app.get('/tenders/{}/bids/{}/documents/{}?acc_token={}'.format(
            self.tender_id, self.bid_id, doc_id, self.bid_token))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('document description', response.json["data"]["description"])

        self.set_status('active.awarded')

        response = self.app.patch_json('/tenders/{}/bids/{}/documents/{}'.format(self.tender_id, self.bid_id, doc_id), {"data": {"description": "document description"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current (active.awarded) tender status")

    def test_create_tender_bidder_document_nopending(self):
        response = self.app.post_json('/tenders/{}/bids'.format(
            self.tender_id), {'data': {'tenderers': [test_organization], "value": {"amount": 500}}})
        bid = response.json['data']
        bid_id = bid['id']

        response = self.app.post('/tenders/{}/bids/{}/documents'.format(
            self.tender_id, bid_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        self.set_status('active.qualification')

        response = self.app.patch_json('/tenders/{}/bids/{}/documents/{}'.format(
            self.tender_id, bid_id, doc_id), {"data": {"description": "document description"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update document because award of bid is not in pending state")

        response = self.app.put('/tenders/{}/bids/{}/documents/{}'.format(
            self.tender_id, bid_id, doc_id), 'content3', content_type='application/msword', status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update document because award of bid is not in pending state")

        response = self.app.post('/tenders/{}/bids/{}/documents'.format(
            self.tender_id, bid_id), upload_files=[('file', 'name.doc', 'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add document because award of bid is not in pending state")


class TenderBidderDocumentWithDSResourceTest(TenderBidderDocumentResourceTest):
    docservice = True

    def test_create_tender_bidder_document_json(self):
        response = self.app.post_json('/tenders/{}/bids/{}/documents'.format(self.tender_id, self.bid_id),
            {'data': {
                'title': 'name.doc',
                'url': self.generate_docservice_url(),
                'hash': 'md5:' + '0' * 32,
                'format': 'application/msword',
            }})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])
        self.assertEqual('name.doc', response.json["data"]["title"])
        key = response.json["data"]["url"].split('?')[-1].split('=')[-1]

        response = self.app.get('/tenders/{}/bids/{}/documents'.format(self.tender_id, self.bid_id), status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't view bid documents in current (active.tendering) tender status")

        response = self.app.get('/tenders/{}/bids/{}/documents?acc_token={}'.format(self.tender_id, self.bid_id, self.bid_token))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/tenders/{}/bids/{}/documents?all=true&acc_token={}'.format(self.tender_id, self.bid_id, self.bid_token))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/tenders/{}/bids/{}/documents/{}?download=some_id&acc_token={}'.format(
            self.tender_id, self.bid_id, doc_id, self.bid_token), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'download'}
        ])

        response = self.app.get('/tenders/{}/bids/{}/documents/{}?download={}'.format(
            self.tender_id, self.bid_id, doc_id, key), status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't view bid document in current (active.tendering) tender status")

        response = self.app.get('/tenders/{}/bids/{}/documents/{}?download={}&acc_token={}'.format(
            self.tender_id, self.bid_id, doc_id, key, self.bid_token))
        self.assertEqual(response.status, '302 Moved Temporarily')
        self.assertIn('http://localhost/get/', response.location)
        self.assertIn('Signature=', response.location)
        self.assertIn('KeyID=', response.location)
        self.assertIn('Expires=', response.location)

        response = self.app.get('/tenders/{}/bids/{}/documents/{}'.format(
            self.tender_id, self.bid_id, doc_id), status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't view bid document in current (active.tendering) tender status")

        response = self.app.get('/tenders/{}/bids/{}/documents/{}?acc_token={}'.format(
            self.tender_id, self.bid_id, doc_id, self.bid_token))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])

        response = self.app.post_json('/tenders/{}/bids/{}/documents'.format(self.tender_id, self.bid_id),
            {'data': {
                'title': 'name.doc',
                'url': self.generate_docservice_url(),
                'hash': 'md5:' + '0' * 32,
                'format': 'application/msword',
            }})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn(response.json["data"]['id'], response.headers['Location'])
        self.assertEqual('name.doc', response.json["data"]["title"])

        self.set_status('active.awarded')

        response = self.app.post_json('/tenders/{}/bids/{}/documents'.format(self.tender_id, self.bid_id),
            {'data': {
                'title': 'name.doc',
                'url': self.generate_docservice_url(),
                'hash': 'md5:' + '0' * 32,
                'format': 'application/msword',
            }}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add document in current (active.awarded) tender status")

        response = self.app.get('/tenders/{}/bids/{}/documents/{}'.format(self.tender_id, self.bid_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertIn('http://localhost/get/', response.json['data']['url'])
        self.assertIn('Signature=', response.json['data']['url'])
        self.assertIn('KeyID=', response.json['data']['url'])
        self.assertNotIn('Expires=', response.json['data']['url'])

        response = self.app.get('/tenders/{}/bids/{}/documents/{}?download={}&acc_token={}'.format(
            self.tender_id, self.bid_id, doc_id, key, self.bid_token))
        self.assertIn('http://localhost/get/', response.location)
        self.assertIn('Signature=', response.location)
        self.assertIn('KeyID=', response.location)
        self.assertIn('Expires=', response.location)

    def test_put_tender_bidder_document_json(self):
        response = self.app.post_json('/tenders/{}/bids/{}/documents'.format(self.tender_id, self.bid_id),
            {'data': {
                'title': 'name.doc',
                'url': self.generate_docservice_url(),
                'hash': 'md5:' + '0' * 32,
                'format': 'application/msword',
            }})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.put_json('/tenders/{}/bids/{}/documents/{}'.format(self.tender_id, self.bid_id, doc_id),
            {'data': {
                'title': 'name.doc',
                'url': self.generate_docservice_url(),
                'hash': 'md5:' + '0' * 32,
                'format': 'application/msword',
                'description': 'test description',
            }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual('test description', response.json["data"]["description"])
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertIn(self.bid_id + '/documents/' + doc_id, response.json["data"]["url"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/tenders/{}/bids/{}/documents/{}?{}&acc_token={}'.format(
            self.tender_id, self.bid_id, doc_id, key, self.bid_token))
        self.assertEqual(response.status, '302 Moved Temporarily')
        self.assertIn('http://localhost/get/', response.location)
        self.assertIn('Signature=', response.location)
        self.assertIn('KeyID=', response.location)
        self.assertIn('Expires=', response.location)

        response = self.app.get('/tenders/{}/bids/{}/documents/{}?acc_token={}'.format(
            self.tender_id, self.bid_id, doc_id, self.bid_token))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])

        response = self.app.put_json('/tenders/{}/bids/{}/documents/{}'.format(self.tender_id, self.bid_id, doc_id),
            {'data': {
                'title': 'name.doc',
                'url': self.generate_docservice_url(),
                'hash': 'md5:' + '0' * 32,
                'format': 'application/msword',
            }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual('test description', response.json["data"]["description"])
        self.assertEqual(doc_id, response.json["data"]["id"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/tenders/{}/bids/{}/documents/{}?{}&acc_token={}'.format(
            self.tender_id, self.bid_id, doc_id, key, self.bid_token))
        self.assertEqual(response.status, '302 Moved Temporarily')
        self.assertIn('http://localhost/get/', response.location)
        self.assertIn('Signature=', response.location)
        self.assertIn('KeyID=', response.location)
        self.assertIn('Expires=', response.location)

        self.set_status('active.awarded')

        response = self.app.put_json('/tenders/{}/bids/{}/documents/{}'.format(self.tender_id, self.bid_id, doc_id),
            {'data': {
                'title': 'name.doc',
                'url': self.generate_docservice_url(),
                'hash': 'md5:' + '0' * 32,
                'format': 'application/msword',
            }}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current (active.awarded) tender status")


class TenderBidderBatchDocumentWithDSResourceTest(BaseTenderWebTest):
    docservice = True
    initial_status = 'active.tendering'

    def test_create_tender_bidder_with_document_invalid(self):
        response = self.app.post_json('/tenders/{}/bids'.format( self.tender_id),
            {'data': {
                 'tenderers': [test_organization],
                 "value": {"amount": 500},
                 'documents': [{
                        'title': 'name.doc',
                        'url': 'http://invalid.docservice.url/get/uuid',
                        'hash': 'md5:' + '0' * 32,
                        'format': 'application/msword'
                    }]
            }}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can add document only from document service.")

        response = self.app.post_json('/tenders/{}/bids'.format( self.tender_id),
            {'data': {
                 'tenderers': [test_organization],
                 "value": {"amount": 500},
                 'documents': [{
                        'title': 'name.doc',
                        'url': '/'.join(self.generate_docservice_url().split('/')[:4]),
                        'hash': 'md5:' + '0' * 32,
                        'format': 'application/msword'
                    }]
            }}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can add document only from document service.")

        response = self.app.post_json('/tenders/{}/bids'.format( self.tender_id),
            {'data': {
                 'tenderers': [test_organization],
                 "value": {"amount": 500},
                 'documents': [{
                        'title': 'name.doc',
                        'url': self.generate_docservice_url().split('?')[0],
                        'hash': 'md5:' + '0' * 32,
                        'format': 'application/msword'
                    }]
            }}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can add document only from document service.")

        response = self.app.post_json('/tenders/{}/bids'.format( self.tender_id),
            {'data': {
                 'tenderers': [test_organization],
                 "value": {"amount": 500},
                 'documents': [{
                        'title': 'name.doc',
                        'url': self.generate_docservice_url(),
                        'format': 'application/msword'
                    }]
            }}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["location"], "documents")
        self.assertEqual(response.json['errors'][0]["name"], "hash")
        self.assertEqual(response.json['errors'][0]["description"], "This field is required.")

        response = self.app.post_json('/tenders/{}/bids'.format( self.tender_id),
            {'data': {
                 'tenderers': [test_organization],
                 "value": {"amount": 500},
                 'documents': [{
                        'title': 'name.doc',
                        'url': self.generate_docservice_url().replace(self.app.app.registry.keyring.keys()[-1], '0' * 8),
                        'hash': 'md5:' + '0' * 32,
                        'format': 'application/msword'
                    }]
            }}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Document url expired.")

        response = self.app.post_json('/tenders/{}/bids'.format( self.tender_id),
            {'data': {
                 'tenderers': [test_organization],
                 "value": {"amount": 500},
                 'documents': [{
                        'title': 'name.doc',
                        'url': self.generate_docservice_url().replace("Signature=", "Signature=ABC"),
                        'hash': 'md5:' + '0' * 32,
                        'format': 'application/msword'
                    }]
            }}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Document url signature invalid.")

        response = self.app.post_json('/tenders/{}/bids'.format( self.tender_id),
            {'data': {
                 'tenderers': [test_organization],
                 "value": {"amount": 500},
                 'documents': [{
                        'title': 'name.doc',
                        'url': self.generate_docservice_url().replace("Signature=", "Signature=bw%3D%3D"),
                        'hash': 'md5:' + '0' * 32,
                        'format': 'application/msword'
                    }]
            }}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Document url invalid.")


    def test_create_tender_bidder_with_document(self):
        response = self.app.post_json('/tenders/{}/bids'.format( self.tender_id),
            {'data': {
                 'tenderers': [test_organization],
                 "value": {"amount": 500},
                 'documents': [{
                        'title': 'name.doc',
                        'url': self.generate_docservice_url(),
                        'hash': 'md5:' + '0' * 32,
                        'format': 'application/msword'
                    }]
            }})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        bidder = response.json['data']
        self.assertEqual(bidder['tenderers'][0]['name'], test_organization['name'])
        self.assertIn('id', bidder)
        self.bid_id = bidder['id']
        self.bid_token = response.json['access']['token']
        self.assertIn(bidder['id'], response.headers['Location'])
        document = bidder['documents'][0]
        self.assertEqual('name.doc', document["title"])
        key = document["url"].split('?')[-1].split('=')[-1]

        response = self.app.get('/tenders/{}/bids/{}/documents'.format(self.tender_id, self.bid_id), status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't view bid documents in current (active.tendering) tender status")

        response = self.app.get('/tenders/{}/bids/{}/documents?acc_token={}'.format(self.tender_id, self.bid_id, self.bid_token))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(document['id'], response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/tenders/{}/bids/{}/documents?all=true&acc_token={}'.format(self.tender_id, self.bid_id, self.bid_token))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(document['id'], response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/tenders/{}/bids/{}/documents/{}?download=some_id&acc_token={}'.format(
            self.tender_id, self.bid_id, document['id'], self.bid_token), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'download'}
        ])

        response = self.app.get('/tenders/{}/bids/{}/documents/{}?download={}'.format(
            self.tender_id, self.bid_id, document['id'], key), status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't view bid document in current (active.tendering) tender status")

        response = self.app.get('/tenders/{}/bids/{}/documents/{}?download={}&acc_token={}'.format(
            self.tender_id, self.bid_id, document['id'], key, self.bid_token))
        self.assertEqual(response.status, '302 Moved Temporarily')
        self.assertIn('http://localhost/get/', response.location)
        self.assertIn('Signature=', response.location)
        self.assertIn('KeyID=', response.location)
        self.assertIn('Expires=', response.location)

        response = self.app.get('/tenders/{}/bids/{}/documents/{}'.format(
            self.tender_id, self.bid_id, document['id']), status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't view bid document in current (active.tendering) tender status")

        response = self.app.get('/tenders/{}/bids/{}/documents/{}?acc_token={}'.format(
            self.tender_id, self.bid_id, document['id'], self.bid_token))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(document['id'], response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])


    def test_create_tender_bidder_with_documents(self):
        dateModified = self.db.get(self.tender_id).get('dateModified')

        response = self.app.post_json('/tenders/{}/bids'.format( self.tender_id),
            {'data': {
                 'tenderers': [test_organization],
                 "value": {"amount": 500},
                 'documents': [{
                        'title': 'first.doc',
                        'url': self.generate_docservice_url(),
                        'hash': 'md5:' + '0' * 32,
                        'format': 'application/msword'
                    },
                    {
                        'title': 'second.doc',
                        'url': self.generate_docservice_url(),
                        'hash': 'md5:' + '0' * 32,
                        'format': 'application/msword'
                    },
                    {
                        'title': 'third.doc',
                        'url': self.generate_docservice_url(),
                        'hash': 'md5:' + '0' * 32,
                        'format': 'application/msword'
                    }]
            }})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        bidder = response.json['data']
        self.assertEqual(bidder['tenderers'][0]['name'], test_organization['name'])
        self.assertIn('id', bidder)
        self.bid_id = bidder['id']
        self.bid_token = response.json['access']['token']
        self.assertIn(bidder['id'], response.headers['Location'])
        documents = bidder['documents']
        ids = [doc['id'] for doc in documents]
        self.assertEqual(['first.doc', 'second.doc', 'third.doc'], [document["title"] for document in documents])

        response = self.app.get('/tenders/{}/bids/{}/documents'.format(self.tender_id, self.bid_id), status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't view bid documents in current (active.tendering) tender status")

        response = self.app.get('/tenders/{}/bids/{}/documents?acc_token={}'.format(self.tender_id, self.bid_id, self.bid_token))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(len(response.json["data"]), 3)
        self.assertEqual(ids, [doc['id'] for doc in response.json["data"]])

        response = self.app.get('/tenders/{}/bids/{}/documents?all=true&acc_token={}'.format(self.tender_id, self.bid_id, self.bid_token))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(len(response.json["data"]), 3)
        self.assertEqual(ids, [doc['id'] for doc in response.json["data"]])

        for index, document in enumerate(documents):
            key = document["url"].split('?')[-1].split('=')[-1]

            response = self.app.get('/tenders/{}/bids/{}/documents/{}?download=some_id&acc_token={}'.format(
                self.tender_id, self.bid_id, document['id'], self.bid_token), status=404)
            self.assertEqual(response.status, '404 Not Found')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.json['status'], 'error')
            self.assertEqual(response.json['errors'], [
                {u'description': u'Not Found', u'location': u'url', u'name': u'download'}
            ])

            response = self.app.get('/tenders/{}/bids/{}/documents/{}?download={}'.format(
                self.tender_id, self.bid_id, document['id'], key), status=403)
            self.assertEqual(response.status, '403 Forbidden')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.json['errors'][0]["description"], "Can't view bid document in current (active.tendering) tender status")

            response = self.app.get('/tenders/{}/bids/{}/documents/{}?download={}&acc_token={}'.format(
                self.tender_id, self.bid_id, document['id'], key, self.bid_token))
            self.assertEqual(response.status, '302 Moved Temporarily')
            self.assertIn('http://localhost/get/', response.location)
            self.assertIn('Signature=', response.location)
            self.assertIn('KeyID=', response.location)
            self.assertIn('Expires=', response.location)

            response = self.app.get('/tenders/{}/bids/{}/documents/{}'.format(
                self.tender_id, self.bid_id, document['id']), status=403)
            self.assertEqual(response.status, '403 Forbidden')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.json['errors'][0]["description"], "Can't view bid document in current (active.tendering) tender status")

            response = self.app.get('/tenders/{}/bids/{}/documents/{}?acc_token={}'.format(
                self.tender_id, self.bid_id, document['id'], self.bid_token))
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(document['id'], response.json["data"]["id"])


class TenderBidderValueAddedTaxPayer(BaseTenderWebTest):
    initial_data = test_features_tender_data
    initial_status = 'active.tendering'
    
    RESPONSE_CODE = {
        '200': '200 OK',
        '201': '201 Created',
        '403': '403 Forbidden',
        '422': '422 Unprocessable Entity'
    }
    
    def test_create_tender_with_invalid_value_added_tax_bidder(self):
        request_path = '/tenders/{}/bids'.format(self.tender_id)

        # Try update tender VAT
        response = self.app.patch_json(
            '/tenders/{}?acc_token={}'.format(self.tender_id, self.tender_token),
            {'data': {
                'value': {'valueAddedTaxIncluded': False},
                'minimalStep': {'valueAddedTaxIncluded': False}
            }}
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])

        response = self.app.get('/tenders/{}?acc_token={}'.format(self.tender_id, self.tender_token))
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        tender = response.json['data']
        self.assertTrue(tender['value']['valueAddedTaxIncluded'])

        response = self.app.post_json(
            request_path,
            {'data': {
                'tenderers': [test_organization],
                'value': {'amount': 500, 'valueAddedTaxPayer': False},
                'parameters': [
                    {
                        'code': i['code'],
                        'value': 0.15,
                    }
                    for i in self.initial_data['features']
                ]
            }}, status=422
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['422'])
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'][0]['description'], [
            u'valueAddedTaxPayer of bid should be identical to valueAddedTaxIncluded of value of tender'
        ])

        # Create bidder without valueAddedTax
        response = self.app.post_json(
            request_path,
            {'data': {
                'tenderers': [test_organization],
                'value': {'amount': 500},
                'parameters': [
                    {
                        'code': i['code'],
                        'value': 0.15,
                    }
                    for i in self.initial_data['features']
                ]}}
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['201'])
        self.assertEqual(response.content_type, 'application/json')

        bid = response.json['data']

        self.assertTrue(bid['value']['valueAddedTaxPayer'])
        self.assertEqual(bid['value']['valueAddedTax'], 20)

        # Create two bidder with invalid valueAddedTax
        response = self.app.post_json(
            request_path,
            {'data': {
                'tenderers': [test_organization],
                'value': {'amount': 500, 'valueAddedTax': 10},
                'parameters': [
                    {
                        'code': i['code'],
                        'value': 0.15,
                    }
                    for i in self.initial_data['features']
                ]}}, status=422
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['422'])
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['errors'][0]['description'], ['valueAddedTax should be 0, 7 or 20 percent']
        )

        response = self.app.post_json(
            request_path,
            {'data': {
                'tenderers': [test_organization],
                'value': {'amount': 500, 'valueAddedTax': 21},
                'parameters': [
                    {
                        'code': i['code'],
                        'value': 0.15,
                    }
                    for i in self.initial_data['features']]
            }}, status=422
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['422'])
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['errors'][0]['description'], ['valueAddedTax should be 0, 7 or 20 percent']
        )

    def test_create_tender_with_valid_value_added_tax_bidder(self):
        request_path = '/tenders/{}/bids'.format(self.tender_id)

        # Create bidder with valueAddedTax = 7
        response = self.app.post_json(
            request_path,
            {'data': {
                'tenderers': [test_organization],
                'value': {'amount': 500, 'valueAddedTax': 7},
                'parameters': [
                    {
                        'code': i['code'],
                        'value': 0.15,
                    }
                    for i in self.initial_data['features']]
            }}
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['201'])
        self.assertEqual(response.content_type, 'application/json')

        bid = response.json['data']

        self.assertTrue(bid['value']['valueAddedTaxPayer'])
        self.assertEqual(bid['value']['valueAddedTax'], 7)

        # Create bidder with valueAddedTax = 20
        response = self.app.post_json(
            request_path,
            {'data': {
                'tenderers': [test_organization],
                'value': {'amount': 500, 'valueAddedTax': 20},
                'parameters': [
                    {
                        'code': i['code'],
                        'value': 0.15,
                    }
                    for i in self.initial_data['features']]
            }}
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['201'])
        self.assertEqual(response.content_type, 'application/json')

        bid = response.json['data']

        self.assertTrue(bid['value']['valueAddedTaxPayer'])
        self.assertEqual(bid['value']['valueAddedTax'], 20)

        # Create bidder with valueAddedTax = 0
        response = self.app.post_json(
            request_path,
            {'data': {
                'tenderers': [test_organization],
                'value': {'amount': 500, 'valueAddedTax': 0},
                'parameters': [
                    {
                        'code': i['code'],
                        'value': 0.15,
                    }
                    for i in self.initial_data['features']]
            }}
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['201'])
        self.assertEqual(response.content_type, 'application/json')

        bid = response.json['data']

        self.assertTrue(bid['value']['valueAddedTaxPayer'])
        self.assertEqual(bid['value']['valueAddedTax'], 0)

        response = self.app.get('/tenders/{}/bids'.format(self.tender_id), status=403)
        self.assertEqual(response.status, self.RESPONSE_CODE['403'])
        self.assertEqual(
            response.json['errors'][0]['description'],
            u'Can\'t view bids in current (active.tendering) tender status'
        )

        self.set_status('active.awarded')

        response = self.app.get('/tenders/{}/bids'.format(self.tender_id))
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        bids = response.json['data']

        self.assertEqual(bids[0]['value']['valueAddedTax'], 7)
        self.assertEqual(bids[1]['value']['valueAddedTax'], 20)
        self.assertEqual(bids[2]['value']['valueAddedTax'], 0)

    def test_invalid_editing_tender_bidders(self):
        request_path = '/tenders/{}/bids'.format(self.tender_id)

        # Create two bidders
        response_bidder_1 = self.app.post_json(
            request_path,
            {'data': {
                'tenderers': [test_organization],
                'value': {'amount': 500, 'valueAddedTax': 7},
                'parameters': [
                    {
                        'code': i['code'],
                        'value': 0.15,
                    }
                    for i in self.initial_data['features']]
            }}
        )

        self.assertEqual(response_bidder_1.status, self.RESPONSE_CODE['201'])

        response_bidder_2 = self.app.post_json(
            request_path,
            {'data': {
                'tenderers': [test_organization],
                'value': {'amount': 500, 'valueAddedTax': 20},
                'parameters': [
                    {
                        'code': i['code'],
                        'value': 0.15,
                    }
                    for i in self.initial_data['features']]
            }}
        )

        self.assertEqual(response_bidder_2.status, self.RESPONSE_CODE['201'])

        # Get bids
        response = self.app.get('/tenders/{}/bids'.format(self.tender_id), status=403)
        self.assertEqual(response.status, self.RESPONSE_CODE['403'])
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(
            response.json['errors'],
            [{
                u'description': u"Can't view bids in current (active.tendering) tender status",
                u'location': u'body',
                u'name': u'data'
            }]
        )

        self.set_status('active.qualification')

        response = self.app.get('/tenders/{}/bids'.format(self.tender_id))
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        bids = response.json['data']

        # Editing bidder with invalid valueAddedTax
        response = self.app.patch_json(
            '/tenders/{}/bids/{}?acc_token={}'.format(self.tender_id, bids[0]['id'], self.tender_token),
            {'data': {'value': {'valueAddedTax': 10}}}, status=422
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['422'])
        self.assertEqual(
            response.json['errors'][0]['description'],
            [u'valueAddedTax should be 0, 7 or 20 percent']
        )

        response = self.app.patch_json(
            '/tenders/{}/bids/{}?acc_token={}'.format(self.tender_id, bids[1]['id'], self.tender_token),
            {'data': {'value': {'valueAddedTax': 10}}}, status=422
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['422'])
        self.assertEqual(
            response.json['errors'][0]['description'],
            [u'valueAddedTax should be 0, 7 or 20 percent']
        )

        response = self.app.patch_json(
            '/tenders/{}/bids/{}?acc_token={}'.format(self.tender_id, bids[0]['id'], self.tender_token),
            {'data': {'value': {'valueAddedTax': 20}}}, status=403
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['403'])
        self.assertEqual(
            response.json['errors'][0]['description'],
            'Can\'t update bid in current (active.qualification) tender status'
        )

        # Change valueAddedTaxPayer to False
        response = self.app.patch_json(
            '/tenders/{}/bids/{}?acc_token={}'.format(self.tender_id, bids[0]['id'], self.tender_token),
            {'data': {'value': {'valueAddedTaxPayer': False}}}, status=422
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['422'])
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(
            response.json['errors'],
            [{
                u'description': [
                    u'valueAddedTaxPayer of bid should be identical to valueAddedTaxIncluded of value of tender'
                ],
                u'location': u'body',
                u'name': u'value'
            }]
        )

        # Create bidder with valueAddedTax = 0
        self.set_status('active.tendering')
        response = self.app.post_json(
            request_path,
            {'data': {
                'tenderers': [test_organization],
                'value': {'amount': 500, 'valueAddedTax': 0},
                'parameters': [
                    {
                        'code': i['code'],
                        'value': 0.15,
                    }
                    for i in self.initial_data['features']]
            }}, status=422
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['422'])
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(
            response.json['errors'][0], 
            {
                u'description': [u'period should begin after tenderPeriod'], 
                u'location': u'body', 
                u'name': u'awardPeriod'
            }
        )

    def test_valid_editing_tender_bidders(self):
        request_path = '/tenders/{}/bids'.format(self.tender_id)

        # Create first bidder
        response = self.app.post_json(
            request_path,
            {'data': {
                'tenderers': [test_organization],
                'value': {'amount': 500, 'valueAddedTax': 7},
                'parameters': [
                    {
                        'code': i['code'],
                        'value': 0.15,
                    }
                    for i in self.initial_data['features']]
            }}
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['201'])
        self.assertEqual(response.content_type, 'application/json')

        bids = response.json['data']

        self.assertTrue(bids['value']['valueAddedTaxPayer'])
        self.assertEqual(bids['value']['valueAddedTax'], 7)

        response = self.app.patch_json(
            '/tenders/{}/bids/{}?acc_token={}'.format(self.tender_id, bids['id'], self.tender_token),
            {'data': {'value': {'valueAddedTax': 20}}}
        )

        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        first_bidder = response.json['data']

        self.assertTrue(first_bidder['value']['valueAddedTaxPayer'])
        self.assertEqual(first_bidder['value']['valueAddedTax'], 20)

        # Create second bidder
        self.set_status('active.tendering')
        response = self.app.post_json(
            request_path,
            {'data': {
                'tenderers': [test_organization],
                'value': {'amount': 500, 'valueAddedTax': 20},
                'parameters': [
                    {
                        'code': i['code'],
                        'value': 0.15,
                    }
                    for i in self.initial_data['features']]
            }}
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['201'])
        self.assertEqual(response.content_type, 'application/json')

        bids = response.json['data']

        self.assertTrue(bids['value']['valueAddedTaxPayer'])
        self.assertEqual(bids['value']['valueAddedTax'], 20)

        response = self.app.patch_json(
            '/tenders/{}/bids/{}?acc_token={}'.format(self.tender_id, bids['id'], self.tender_token),
            {'data': {'value': {'valueAddedTax': 7}}}
        )

        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        second_bidder = response.json['data']

        self.assertTrue(second_bidder['value']['valueAddedTaxPayer'])
        self.assertEqual(second_bidder['value']['valueAddedTax'], 7)

        # Create and edit bidder with with valueAddedTax = 0
        response = self.app.post_json(
            request_path,
            {'data': {
                'tenderers': [test_organization],
                'value': {'amount': 500, 'valueAddedTax': 0},
                'parameters': [
                    {
                        'code': i['code'],
                        'value': 0.15,
                    }
                    for i in self.initial_data['features']]
            }}
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['201'])
        self.assertEqual(response.content_type, 'application/json')

        bids = response.json['data']

        self.assertTrue(bids['value']['valueAddedTaxPayer'])
        self.assertEqual(bids['value']['valueAddedTax'], 0)

        response = self.app.patch_json(
            '/tenders/{}/bids/{}?acc_token={}'.format(self.tender_id, bids['id'], self.tender_token),
            {'data': {'value': {'valueAddedTax': 7}}}
        )

        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')
        self.assertTrue(response.json['data']['value']['valueAddedTaxPayer'])
        self.assertEqual(response.json['data']['value']['valueAddedTax'], 7)

        # Change bidder sumValueAddedTax
        response = self.app.patch_json(
            '/tenders/{}/bids/{}?acc_token={}'.format(self.tender_id, bids['id'], self.tender_token),
            {'data': {'value': {'sumValueAddedTax': 10}}}, status=422
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['422'])
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(
            response.json['errors'],
            [{u'description': {u'sumValueAddedTax': [u'Rogue field']}, u'location': u'body', u'name': u'value'}]
        )

        # Change bidder amountWithValueAddedTax
        response = self.app.patch_json(
            '/tenders/{}/bids/{}?acc_token={}'.format(self.tender_id, bids['id'], self.tender_token),
            {'data': {'value': {'amountWithValueAddedTax': 10}}}, status=422
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['422'])
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'],  'error')
        self.assertEqual(
            response.json['errors'],
            [{u'description': {u'amountWithValueAddedTax': [u'Rogue field']}, u'location': u'body', u'name': u'value'}]
        )

        # Change bidder amountWithoutValueAddedTax
        response = self.app.patch_json(
            '/tenders/{}/bids/{}?acc_token={}'.format(self.tender_id, bids['id'], self.tender_token),
            {'data': {'value': {'amountWithoutValueAddedTax': 10}}}, status=422
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['422'])
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(
            response.json['errors'],
            [{
                u'description': {u'amountWithoutValueAddedTax': [u'Rogue field']},
                u'location': u'body',
                u'name': u'value'
            }]
        )

        # Change bidder value:valueAddedTaxPayer to False
        response = self.app.patch_json(
            '/tenders/{}/bids/{}?acc_token={}'.format(self.tender_id, bids['id'], self.tender_token),
            {'data': {'value': {'valueAddedTaxPayer': False}}}, status=422
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['422'])
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(
            response.json['errors'][0],
            {u'description': [
                u'valueAddedTaxPayer of bid should be identical to valueAddedTaxIncluded of value of tender'],
             u'location': u'body', u'name': u'value'}
        )

        # View some modified bidder
        response = self.app.get('/tenders/{}/bids/{}'.format(self.tender_id, first_bidder['id']), status=403)
        self.assertEqual(response.status, self.RESPONSE_CODE['403'])
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['errors'][0]['description'],
            u'Can\'t view bid in current (active.tendering) tender status'
        )

        self.set_status('active.qualification')

        # Get first bidder
        response = self.app.get('/tenders/{}/bids/{}'.format(self.tender_id, first_bidder['id']))
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        first_bidder = response.json['data']

        self.assertEqual(first_bidder['value']['valueAddedTax'], 20)

        # Get second bidder
        response = self.app.get('/tenders/{}/bids/{}'.format(self.tender_id, second_bidder['id']))
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        second_bidder = response.json['data']

        self.assertEqual(second_bidder['value']['valueAddedTax'], 7)

        # Edition attempt after change tender status with active.qualification to active.tendering
        self.set_status('active.tendering')

        response = self.app.patch_json(
            '/tenders/{}/bids/{}?acc_token={}'.format(self.tender_id, second_bidder['id'], self.tender_token),
            {'data': {'value': {'valueAddedTax': 20}}}, status=422
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['422'])
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]['description'], [u'period should begin after tenderPeriod'])


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TenderBidderDocumentResourceTest))
    suite.addTest(unittest.makeSuite(TenderBidderDocumentWithDSResourceTest))
    suite.addTest(unittest.makeSuite(TenderBidderFeaturesResourceTest))
    suite.addTest(unittest.makeSuite(TenderBidderResourceTest))
    suite.addTest(unittest.makeSuite(TenderBidderValueAddedTaxPayer))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
