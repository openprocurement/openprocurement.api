# -*- coding: utf-8 -*-
from uuid import uuid4
from copy import deepcopy

from openprocurement.api.plugins.transferring.models import Transfer
from openprocurement.api.tests.base import BaseWebTest

test_transfer_data = {}


class TestTransfer(BaseWebTest):

    def test_simple_add_transfer(self):

        data = {"access_token": "1234",
                "transfer_token": "5678",
                "owner": "Chuck Norris"}

        transfer = Transfer(data)

        self.assertIsNone(transfer.id)

        transfer.store(self.db)

        self.assertIsNotNone(transfer.id)

        fromdb = self.db.get(transfer.id)

        self.assertEqual(transfer.transfer_token, fromdb['transfer_token'])
        self.assertEqual(transfer.access_token, fromdb['access_token'])
        self.assertEqual(transfer.owner, fromdb['owner'])
        self.assertEqual(transfer.doc_type, "Transfer")

        transfer.delete_instance(self.db)


class TestTransferResource(BaseWebTest):
    """ /transfers resource test """

    def test_get_transfer(self):
        response = self.app.get('/transfers', status=405)
        self.assertEqual(response.status, '405 Method Not Allowed')

        response = self.app.post_json('/transfers', {'data': test_transfer_data})
        transfer = response.json['data']
        self.assertIn('id', transfer)

        response = self.app.get('/transfers/{}'.format(transfer['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'], transfer)

        response = self.app.get('/transfers/{}?opt_jsonp=callback'.format(transfer['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/javascript')
        self.assertIn('callback({"data": {"', response.body)

        response = self.app.get('/transfers/{}?opt_pretty=1'.format(transfer['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('{\n    "data": {\n        "', response.body)

    def test_not_found(self):
        response = self.app.post_json('/transfers', {'data': test_transfer_data})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.get('/transfers/{}'.format("1234" * 8), status=404)
        self.assertEqual(response.status, '404 Not Found')

        data = deepcopy(test_transfer_data)
        data['id'] = uuid4().hex
        response = self.app.post_json('/transfers', {'data': data})
        transfer = response.json['data']
        self.assertNotEqual(transfer['id'], data['id'])

        response = self.app.get('/transfers/{}'.format(data['id']), status=404)
        self.assertEqual(response.status, '404 Not Found')

        response = self.app.get('/transfers/some_id', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'transfer_id'}
        ])

        response = self.app.patch_json(
            '/transfers/some_id', {'data': {}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'transfer_id'}
        ])

    def test_create_transfer(self):
        response = self.app.post_json('/transfers', status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')

        response = self.app.post_json('/transfers', {"data": test_transfer_data})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        transfer = response.json['data']
        self.assertNotIn('usedFor', transfer)
        self.assertIn('token', response.json['access'])
        self.assertIn('transfer', response.json['access'])

        response = self.app.get('/transfers/{}'.format(transfer['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(set(response.json['data']), set(transfer))
        self.assertEqual(response.json['data'], transfer)

        data = test_transfer_data
        response = self.app.post_json('/transfers?opt_jsonp=callback', {"data": data})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/javascript')
        self.assertIn('callback({"', response.body)

        response = self.app.post_json('/transfers?opt_pretty=1', {"data": data})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('{\n    "', response.body)

        response = self.app.post_json('/transfers', {"data": data, "options": {"pretty": True}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('{\n    "', response.body)
