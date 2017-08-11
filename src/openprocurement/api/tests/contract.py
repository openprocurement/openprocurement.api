# -*- coding: utf-8 -*-
import unittest
from datetime import timedelta

from openprocurement.api.models import get_now
from openprocurement.api.tests.base import BaseTenderWebTest, test_tender_data, test_bids, test_lots, \
    test_organization, test_features_tender_data


class TenderContractResourceTest(BaseTenderWebTest):
    #initial_data = tender_data
    initial_status = 'active.qualification'
    initial_bids = test_bids

    def setUp(self):
        super(TenderContractResourceTest, self).setUp()
        # Create award
        response = self.app.post_json('/tenders/{}/awards'.format(
            self.tender_id), {'data': {'suppliers': [test_organization], 'status': 'pending', 'bid_id': self.initial_bids[0]['id'], 'value': test_tender_data["value"], 'items': test_tender_data["items"]}})
        award = response.json['data']
        self.award_id = award['id']
        self.award_value = award['value']
        self.award_suppliers = award['suppliers']
        self.award_items = award['items']
        response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, self.award_id), {"data": {"status": "active"}})

    def test_create_tender_contract_invalid(self):
        response = self.app.post_json('/tenders/some_id/contracts', {
                                      'data': {'title': 'contract title', 'description': 'contract description', 'awardID': self.award_id}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'tender_id'}
        ])

        request_path = '/tenders/{}/contracts'.format(self.tender_id)

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

        response = self.app.post_json(request_path, {'data': {'awardID': 'invalid_value'}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'awardID should be one of awards'], u'location': u'body', u'name': u'awardID'}
        ])

    def test_create_tender_contract(self):
        response = self.app.post_json('/tenders/{}/contracts'.format(
            self.tender_id), {'data': {'title': 'contract title', 'description': 'contract description', 'awardID': self.award_id, 'value': self.award_value, 'suppliers': self.award_suppliers}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        contract = response.json['data']
        self.assertIn('id', contract)
        self.assertIn('value', contract)
        self.assertIn('suppliers', contract)
        self.assertIn(contract['id'], response.headers['Location'])

        tender = self.db.get(self.tender_id)
        tender['contracts'][-1]["status"] = "terminated"
        self.db.save(tender)

        self.set_status('unsuccessful')

        response = self.app.post_json('/tenders/{}/contracts'.format(
            self.tender_id), {'data': {'title': 'contract title', 'description': 'contract description', 'awardID': self.award_id}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add contract in current (unsuccessful) tender status")

        response = self.app.patch_json('/tenders/{}/contracts/{}'.format(self.tender_id, contract['id']), {"data": {"status": "active"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update contract in current (unsuccessful) tender status")

    def test_create_tender_contract_in_complete_status(self):
        response = self.app.post_json('/tenders/{}/contracts'.format(
            self.tender_id), {'data': {'title': 'contract title', 'description': 'contract description', 'awardID': self.award_id}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        contract = response.json['data']
        self.assertIn('id', contract)
        self.assertIn(contract['id'], response.headers['Location'])

        tender = self.db.get(self.tender_id)
        tender['contracts'][-1]["status"] = "terminated"
        self.db.save(tender)

        self.set_status('complete')

        response = self.app.post_json('/tenders/{}/contracts'.format(
        self.tender_id), {'data': {'title': 'contract title', 'description': 'contract description', 'awardID': self.award_id}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add contract in current (complete) tender status")

        response = self.app.patch_json('/tenders/{}/contracts/{}'.format(self.tender_id, contract['id']), {"data": {"status": "active"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update contract in current (complete) tender status")

    def test_patch_tender_contract(self):
        response = self.app.get('/tenders/{}/contracts'.format( self.tender_id))
        contract = response.json['data'][0]

        response = self.app.patch_json('/tenders/{}/contracts/{}'.format(self.tender_id, contract['id']), {"data": {"status": "active"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn("Can't sign contract before stand-still period end (", response.json['errors'][0]["description"])

        self.set_status('complete', {'status': 'active.awarded'})

        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(self.tender_id, self.award_id), {'data': {
            'title': 'complaint title',
            'description': 'complaint description',
            'author': test_organization,
            'status': 'claim'
        }})
        self.assertEqual(response.status, '201 Created')
        complaint = response.json['data']
        owner_token = response.json['access']['token']

        tender = self.db.get(self.tender_id)
        for i in tender.get('awards', []):
            i['complaintPeriod']['endDate'] = i['complaintPeriod']['startDate']
        self.db.save(tender)

        response = self.app.patch_json('/tenders/{}/contracts/{}'.format(self.tender_id, contract['id']), {"data": {"contractID": "myselfID", "items": [{"description": "New Description"}], "suppliers": [{"name": "New Name"}]}})

        response = self.app.get('/tenders/{}/contracts/{}'.format(self.tender_id, contract['id']))
        self.assertEqual(response.json['data']['contractID'], contract['contractID'])
        self.assertEqual(response.json['data']['items'], contract['items'])
        self.assertEqual(response.json['data']['suppliers'], contract['suppliers'])

        response = self.app.patch_json('/tenders/{}/contracts/{}'.format(self.tender_id, contract['id']), {"data": {"value": {"currency": "USD"}}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]["description"], "Can\'t update currency for contract value")

        response = self.app.patch_json('/tenders/{}/contracts/{}'.format(self.tender_id, contract['id']), {"data": {"value": {"valueAddedTaxPayer": False}}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]["description"], "Can\'t update valueAddedTaxPayer for contract value")

        response = self.app.patch_json('/tenders/{}/contracts/{}'.format(self.tender_id, contract['id']), {"data": {"value": {"amount": 501}}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]["description"], "Value amount should be less or equal to awarded amount (500.0)")

        response = self.app.patch_json('/tenders/{}/contracts/{}'.format(self.tender_id, contract['id']), {"data": {"value": {"amount": 238}}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['value']['amount'], 238)

        response = self.app.patch_json('/tenders/{}/contracts/{}'.format(self.tender_id, contract['id']), {"data": {"dateSigned": i['complaintPeriod']['endDate']}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.json['errors'], [{u'description': [u'Contract signature date should be after award complaint period end date ({})'.format(i['complaintPeriod']['endDate'])], u'location': u'body', u'name': u'dateSigned'}])

        one_hour_in_furure = (get_now() + timedelta(hours=1)).isoformat()
        response = self.app.patch_json('/tenders/{}/contracts/{}'.format(self.tender_id, contract['id']), {"data": {"dateSigned": one_hour_in_furure}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.json['errors'], [{u'description': [u"Contract signature date can't be in the future"], u'location': u'body', u'name': u'dateSigned'}])

        custom_signature_date = get_now().isoformat()
        response = self.app.patch_json('/tenders/{}/contracts/{}'.format(self.tender_id, contract['id']), {"data": {"dateSigned": custom_signature_date}})
        self.assertEqual(response.status, '200 OK')

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

        response = self.app.patch_json('/tenders/{}/contracts/{}'.format(self.tender_id, contract['id']), {"data": {"status": "active"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't sign contract before reviewing all complaints")

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.award_id, complaint['id'], owner_token), {"data": {
            "satisfied": True,
            "status": "resolved"
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "resolved")

        response = self.app.patch_json('/tenders/{}/contracts/{}'.format(self.tender_id, contract['id']), {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "active")

        response = self.app.patch_json('/tenders/{}/contracts/{}'.format(self.tender_id, contract['id']), {"data": {"value": {"amount": 232}}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update contract in current (complete) tender status")

        response = self.app.patch_json('/tenders/{}/contracts/{}'.format(self.tender_id, contract['id']), {"data": {"contractID": "myselfID"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update contract in current (complete) tender status")

        response = self.app.patch_json('/tenders/{}/contracts/{}'.format(self.tender_id, contract['id']), {"data": {"items": [{"description": "New Description"}]}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update contract in current (complete) tender status")

        response = self.app.patch_json('/tenders/{}/contracts/{}'.format(self.tender_id, contract['id']), {"data": {"suppliers": [{"name": "New Name"}]}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update contract in current (complete) tender status")

        response = self.app.patch_json('/tenders/{}/contracts/{}'.format(self.tender_id, contract['id']), {"data": {"status": "active"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update contract in current (complete) tender status")

        response = self.app.patch_json('/tenders/{}/contracts/some_id'.format(self.tender_id), {"data": {"status": "active"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'contract_id'}
        ])

        response = self.app.patch_json('/tenders/some_id/contracts/some_id', {"data": {"status": "active"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.get('/tenders/{}/contracts/{}'.format(self.tender_id, contract['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "active")
        self.assertEqual(response.json['data']["value"]['amount'], 238)
        self.assertEqual(response.json['data']['contractID'], contract['contractID'])
        self.assertEqual(response.json['data']['items'], contract['items'])
        self.assertEqual(response.json['data']['suppliers'], contract['suppliers'])
        self.assertEqual(response.json['data']['dateSigned'], custom_signature_date)

    def test_get_tender_contract(self):
        response = self.app.post_json('/tenders/{}/contracts'.format(
            self.tender_id), {'data': {'title': 'contract title', 'description': 'contract description', 'awardID': self.award_id}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        contract = response.json['data']

        response = self.app.get('/tenders/{}/contracts/{}'.format(self.tender_id, contract['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'], contract)

        response = self.app.get('/tenders/{}/contracts/some_id'.format(self.tender_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'contract_id'}
        ])

        response = self.app.get('/tenders/some_id/contracts/some_id', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

    def test_get_tender_contracts(self):
        response = self.app.post_json('/tenders/{}/contracts'.format(
            self.tender_id), {'data': {'title': 'contract title', 'description': 'contract description', 'awardID': self.award_id}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        contract = response.json['data']

        response = self.app.get('/tenders/{}/contracts'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'][-1], contract)

        response = self.app.get('/tenders/some_id/contracts', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])


class Tender2LotContractResourceTest(BaseTenderWebTest):
    initial_status = 'active.qualification'
    initial_bids = test_bids
    initial_lots = 2 * test_lots

    def setUp(self):
        super(Tender2LotContractResourceTest, self).setUp()
        # Create award
        response = self.app.post_json('/tenders/{}/awards'.format(self.tender_id), {'data': {
            'suppliers': [test_organization],
            'status': 'pending',
            'bid_id': self.initial_bids[0]['id'],
            'lotID': self.initial_lots[0]['id']
        }})
        award = response.json['data']
        self.award_id = award['id']
        self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, self.award_id), {"data": {"status": "active"}})

    def test_patch_tender_contract(self):
        response = self.app.post_json('/tenders/{}/contracts'.format(
            self.tender_id), {'data': {'title': 'contract title', 'description': 'contract description', 'awardID': self.award_id}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        contract = response.json['data']

        response = self.app.patch_json('/tenders/{}/contracts/{}'.format(self.tender_id, contract['id']), {"data": {"status": "active"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn("Can't sign contract before stand-still period end (", response.json['errors'][0]["description"])

        self.set_status('complete', {'status': 'active.awarded'})

        response = self.app.post_json('/tenders/{}/cancellations'.format(self.tender_id), {'data': {
            'reason': 'cancellation reason',
            'status': 'active',
            "cancellationOf": "lot",
            "relatedLot": self.initial_lots[0]['id']
        }})

        response = self.app.patch_json('/tenders/{}/contracts/{}'.format(self.tender_id, contract['id']), {"data": {"status": "active"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can update contract only in active lot status")


class TenderContractDocumentResourceTest(BaseTenderWebTest):
    #initial_data = tender_data
    initial_status = 'active.qualification'
    initial_bids = test_bids

    def setUp(self):
        super(TenderContractDocumentResourceTest, self).setUp()
        # Create award
        response = self.app.post_json('/tenders/{}/awards'.format(
            self.tender_id), {'data': {'suppliers': [test_organization], 'status': 'pending', 'bid_id': self.initial_bids[0]['id']}})
        award = response.json['data']
        self.award_id = award['id']
        response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, self.award_id), {"data": {"status": "active"}})
        # Create contract for award
        response = self.app.post_json('/tenders/{}/contracts'.format(self.tender_id), {'data': {'title': 'contract title', 'description': 'contract description', 'awardID': self.award_id}})
        contract = response.json['data']
        self.contract_id = contract['id']

    def test_not_found(self):
        response = self.app.post('/tenders/some_id/contracts/some_id/documents', status=404, upload_files=[
                                 ('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.post('/tenders/{}/contracts/some_id/documents'.format(self.tender_id), status=404, upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'contract_id'}
        ])

        response = self.app.post('/tenders/{}/contracts/{}/documents'.format(self.tender_id, self.contract_id), status=404, upload_files=[
                                 ('invalid_value', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'body', u'name': u'file'}
        ])

        response = self.app.get('/tenders/some_id/contracts/some_id/documents', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.get('/tenders/{}/contracts/some_id/documents'.format(self.tender_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'contract_id'}
        ])

        response = self.app.get('/tenders/some_id/contracts/some_id/documents/some_id', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.get('/tenders/{}/contracts/some_id/documents/some_id'.format(self.tender_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'contract_id'}
        ])

        response = self.app.get('/tenders/{}/contracts/{}/documents/some_id'.format(self.tender_id, self.contract_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'document_id'}
        ])

        response = self.app.put('/tenders/some_id/contracts/some_id/documents/some_id', status=404,
                                upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.put('/tenders/{}/contracts/some_id/documents/some_id'.format(self.tender_id), status=404, upload_files=[
                                ('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'contract_id'}
        ])

        response = self.app.put('/tenders/{}/contracts/{}/documents/some_id'.format(
            self.tender_id, self.contract_id), status=404, upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'document_id'}
        ])

    def test_create_tender_contract_document(self):
        response = self.app.post('/tenders/{}/contracts/{}/documents'.format(
            self.tender_id, self.contract_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])
        self.assertEqual('name.doc', response.json["data"]["title"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/tenders/{}/contracts/{}/documents'.format(self.tender_id, self.contract_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/tenders/{}/contracts/{}/documents?all=true'.format(self.tender_id, self.contract_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/tenders/{}/contracts/{}/documents/{}?download=some_id'.format(
            self.tender_id, self.contract_id, doc_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'download'}
        ])

        response = self.app.get('/tenders/{}/contracts/{}/documents/{}?{}'.format(
            self.tender_id, self.contract_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 7)
        self.assertEqual(response.body, 'content')

        response = self.app.get('/tenders/{}/contracts/{}/documents/{}'.format(
            self.tender_id, self.contract_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])

        tender = self.db.get(self.tender_id)
        tender['contracts'][-1]["status"] = "cancelled"
        self.db.save(tender)

        response = self.app.post('/tenders/{}/contracts/{}/documents'.format(
            self.tender_id, self.contract_id), upload_files=[('file', 'name.doc', 'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add document in current contract status")

        self.set_status('unsuccessful')

        response = self.app.post('/tenders/{}/contracts/{}/documents'.format(
            self.tender_id, self.contract_id), upload_files=[('file', 'name.doc', 'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add document in current (unsuccessful) tender status")

    def test_put_tender_contract_document(self):
        response = self.app.post('/tenders/{}/contracts/{}/documents'.format(
            self.tender_id, self.contract_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.put('/tenders/{}/contracts/{}/documents/{}'.format(self.tender_id, self.contract_id, doc_id),
                                status=404,
                                upload_files=[('invalid_name', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'body', u'name': u'file'}
        ])

        response = self.app.put('/tenders/{}/contracts/{}/documents/{}'.format(
            self.tender_id, self.contract_id, doc_id), upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/tenders/{}/contracts/{}/documents/{}?{}'.format(
            self.tender_id, self.contract_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 8)
        self.assertEqual(response.body, 'content2')

        response = self.app.get('/tenders/{}/contracts/{}/documents/{}'.format(
            self.tender_id, self.contract_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])

        response = self.app.put('/tenders/{}/contracts/{}/documents/{}'.format(
            self.tender_id, self.contract_id, doc_id), 'content3', content_type='application/msword')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/tenders/{}/contracts/{}/documents/{}?{}'.format(
            self.tender_id, self.contract_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 8)
        self.assertEqual(response.body, 'content3')

        tender = self.db.get(self.tender_id)
        tender['contracts'][-1]["status"] = "cancelled"
        self.db.save(tender)

        response = self.app.put('/tenders/{}/contracts/{}/documents/{}'.format(
            self.tender_id, self.contract_id, doc_id), upload_files=[('file', 'name.doc', 'content3')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current contract status")

        self.set_status('unsuccessful')

        response = self.app.put('/tenders/{}/contracts/{}/documents/{}'.format(
            self.tender_id, self.contract_id, doc_id), upload_files=[('file', 'name.doc', 'content3')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current (unsuccessful) tender status")

    def test_patch_tender_contract_document(self):
        response = self.app.post('/tenders/{}/contracts/{}/documents'.format(
            self.tender_id, self.contract_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.patch_json('/tenders/{}/contracts/{}/documents/{}'.format(self.tender_id, self.contract_id, doc_id), {"data": {"description": "document description"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])

        response = self.app.get('/tenders/{}/contracts/{}/documents/{}'.format(
            self.tender_id, self.contract_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('document description', response.json["data"]["description"])

        tender = self.db.get(self.tender_id)
        tender['contracts'][-1]["status"] = "cancelled"
        self.db.save(tender)

        response = self.app.patch_json('/tenders/{}/contracts/{}/documents/{}'.format(self.tender_id, self.contract_id, doc_id), {"data": {"description": "document description"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current contract status")

        self.set_status('unsuccessful')

        response = self.app.patch_json('/tenders/{}/contracts/{}/documents/{}'.format(self.tender_id, self.contract_id, doc_id), {"data": {"description": "document description"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current (unsuccessful) tender status")


class Tender2LotContractDocumentResourceTest(BaseTenderWebTest):
    initial_status = 'active.qualification'
    initial_bids = test_bids
    initial_lots = 2 * test_lots

    def setUp(self):
        super(Tender2LotContractDocumentResourceTest, self).setUp()
        # Create award
        response = self.app.post_json('/tenders/{}/awards'.format(self.tender_id), {'data': {
            'suppliers': [test_organization],
            'status': 'pending',
            'bid_id': self.initial_bids[0]['id'],
            'lotID': self.initial_lots[0]['id']
        }})
        award = response.json['data']
        self.award_id = award['id']
        self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, self.award_id), {"data": {"status": "active"}})
        # Create contract for award
        response = self.app.post_json('/tenders/{}/contracts'.format(self.tender_id), {'data': {'title': 'contract title', 'description': 'contract description', 'awardID': self.award_id}})
        contract = response.json['data']
        self.contract_id = contract['id']

    def test_create_tender_contract_document(self):
        response = self.app.post('/tenders/{}/contracts/{}/documents'.format(
            self.tender_id, self.contract_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])
        self.assertEqual('name.doc', response.json["data"]["title"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.post_json('/tenders/{}/cancellations'.format(self.tender_id), {'data': {
            'reason': 'cancellation reason',
            'status': 'active',
            "cancellationOf": "lot",
            "relatedLot": self.initial_lots[0]['id']
        }})

        response = self.app.post('/tenders/{}/contracts/{}/documents'.format(
            self.tender_id, self.contract_id), upload_files=[('file', 'name.doc', 'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can add document only in active lot status")

    def test_put_tender_contract_document(self):
        response = self.app.post('/tenders/{}/contracts/{}/documents'.format(
            self.tender_id, self.contract_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.put('/tenders/{}/contracts/{}/documents/{}'.format(self.tender_id, self.contract_id, doc_id),
                                status=404,
                                upload_files=[('invalid_name', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'body', u'name': u'file'}
        ])

        response = self.app.put('/tenders/{}/contracts/{}/documents/{}'.format(
            self.tender_id, self.contract_id, doc_id), upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.post_json('/tenders/{}/cancellations'.format(self.tender_id), {'data': {
            'reason': 'cancellation reason',
            'status': 'active',
            "cancellationOf": "lot",
            "relatedLot": self.initial_lots[0]['id']
        }})

        response = self.app.put('/tenders/{}/contracts/{}/documents/{}'.format(
            self.tender_id, self.contract_id, doc_id), upload_files=[('file', 'name.doc', 'content3')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can update document only in active lot status")

    def test_patch_tender_contract_document(self):
        response = self.app.post('/tenders/{}/contracts/{}/documents'.format(
            self.tender_id, self.contract_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.patch_json('/tenders/{}/contracts/{}/documents/{}'.format(self.tender_id, self.contract_id, doc_id), {"data": {"description": "document description"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])

        response = self.app.post_json('/tenders/{}/cancellations'.format(self.tender_id), {'data': {
            'reason': 'cancellation reason',
            'status': 'active',
            "cancellationOf": "lot",
            "relatedLot": self.initial_lots[0]['id']
        }})

        response = self.app.patch_json('/tenders/{}/contracts/{}/documents/{}'.format(self.tender_id, self.contract_id, doc_id), {"data": {"description": "new document description"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can update document only in active lot status")


class TenderContractValueAddedTaxPayer(BaseTenderWebTest):
    initial_status = 'active.tendering'
    initial_data = test_features_tender_data

    RESPONSE_CODE = {
        '200': '200 OK',
        '201': '201 Created',
        '403': '403 Forbidden',
        '422': '422 Unprocessable Entity'
    }

    def test_create_tender_contract_with_invalid_data(self):
        # Create bidder
        response = self.app.post_json(
            '/tenders/{}/bids'.format(self.tender_id),
            {'data': {
                'tenderers': [test_organization],
                'value': {'amount': 500, 'valueAddedTax': 20, 'valueAddedTaxPayer': False},
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
                u'description': [
                    u'valueAddedTaxPayer of bid should be identical to valueAddedTaxIncluded of value of tender'
                ],
                u'location': u'body',
                u'name': u'value'
            }
        )

        # Create bidder
        response = self.app.post_json(
            '/tenders/{}/bids'.format(self.tender_id),
            {'data': {
                'tenderers': [test_organization],
                'value': {'amount': 500, 'valueAddedTax': 20, 'valueAddedTaxPayer': True},
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
        self.assertTrue(response.json['data']['value']['valueAddedTaxPayer'])
        self.assertEqual(response.json['data']['value']['valueAddedTax'], 20)

        bid = response.json['data']

        # Change bidder status
        response = self.app.patch_json(
            '/tenders/{}/bids/{}?acc_token={}'.format(self.tender_id, bid['id'], self.tender_token),
            {'data': {'value': {'valueAddedTaxPayer': False}}}, status=422
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['422'])
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(
            response.json['errors'][0],
            {
                u'description': [
                    u'valueAddedTaxPayer of bid should be identical to valueAddedTaxIncluded of value of tender'
                ],
                u'location': u'body',
                u'name': u'value'
            }
        )

        # Create award
        self.set_status('active.qualification')
        response = self.app.post_json(
            '/tenders/{}/awards'.format(self.tender_id), {'data': {
                'suppliers': [test_organization],
                'status': 'pending',
                'bid_id': bid['id'],
                'value': {'amount': 100500, 'valueAddedTaxPayer': False}
            }}
        )
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')

        award = response.json['data']

        # But value:valueAddedTaxPayer currency stays unchanged
        self.assertTrue(award['value']['valueAddedTaxPayer'])
        self.assertEqual(award['value']['valueAddedTax'], 20)

        # Path award
        response = self.app.patch_json(
            '/tenders/{}/awards/{}?acc_token={}'.format(self.tender_id, award['id'], self.tender_token),
            {'data': {'value': {'valueAddedTaxPayer': False}}}
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        # Get award
        response = self.app.get(
            '/tenders/{}/awards'.format(self.tender_id, award['id'])
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        awards = response.json['data']

        # But value:valueAddedTaxPayer currency stays unchanged
        self.assertTrue(awards[0]['value']['valueAddedTaxPayer'])

    def test_create_tender_contract(self):
        # Create bidder with valueAddedTax = 20
        response = self.app.post_json(
            '/tenders/{}/bids'.format(self.tender_id),
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
        self.assertTrue(response.json['data']['value']['valueAddedTaxPayer'])
        self.assertEqual(response.json['data']['value']['valueAddedTax'], 20)

        bid_vat_20 = response.json['data']

        # Create bidder with valueAddedTax = 7
        response = self.app.post_json(
            '/tenders/{}/bids'.format(self.tender_id),
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
        self.assertTrue(response.json['data']['value']['valueAddedTaxPayer'])
        self.assertEqual(response.json['data']['value']['valueAddedTax'], 7)

        bid_vat_7 = response.json['data']

        # Create bidder with valueAddedTax = 0
        response = self.app.post_json(
            '/tenders/{}/bids'.format(self.tender_id),
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
        self.assertTrue(response.json['data']['value']['valueAddedTaxPayer'])
        self.assertEqual(response.json['data']['value']['valueAddedTax'], 0)

        bid_vat_0 = response.json['data']

        # Create first award
        self.set_status('active.qualification')
        response = self.app.post_json(
            '/tenders/{}/awards'.format(self.tender_id), {'data': {
                'suppliers': [test_organization],
                'status': 'pending',
                'bid_id': bid_vat_20['id'],
                'value': {'amount': 100500}
            }}
        )
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')

        first_award = response.json['data']

        self.assertTrue(first_award['value']['valueAddedTaxPayer'])
        self.assertEqual(first_award['value']['valueAddedTax'], 20)

        # Create second award
        response = self.app.post_json(
            '/tenders/{}/awards'.format(self.tender_id), {'data': {
                'suppliers': [test_organization],
                'status': 'pending',
                'bid_id': bid_vat_7['id'],
                'value': {'amount': 100500}
            }}
        )
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')

        second_award = response.json['data']

        self.assertTrue(second_award['value']['valueAddedTaxPayer'])
        self.assertEqual(second_award['value']['valueAddedTax'], 7)

        # Create third award
        response = self.app.post_json(
            '/tenders/{}/awards'.format(self.tender_id), {'data': {
                'suppliers': [test_organization],
                'status': 'pending',
                'bid_id': bid_vat_0['id'],
                'value': {'amount': 100500}
            }}
        )
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')

        third_award = response.json['data']

        self.assertTrue(third_award['value']['valueAddedTaxPayer'])
        self.assertEqual(third_award['value']['valueAddedTax'], 0)

        # Activate first award
        response = self.app.patch_json(
            '/tenders/{}/awards/{}?acc_token={}'.format(self.tender_id, first_award['id'], self.tender_token),
            {'data': {'status': 'active'}}
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        first_award = response.json['data']

        self.assertEqual(first_award['status'], 'active')
        self.assertTrue(first_award['value']['valueAddedTaxPayer'])
        self.assertEqual(first_award['value']['valueAddedTax'], 20)
        self.assertIn('sumValueAddedTax', first_award['value'])
        self.assertEqual(first_award['value']['sumValueAddedTax'], 100)
        self.assertIn('amountWithValueAddedTax', first_award['value'])
        self.assertEqual(first_award['value']['amountWithValueAddedTax'], 500)
        self.assertIn('amountWithoutValueAddedTax', first_award['value'])
        self.assertEqual(first_award['value']['amountWithoutValueAddedTax'], 416.67)

        # Get contracts
        response = self.app.get('/tenders/{}/contracts'.format(self.tender_id))

        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        contracts = response.json['data']

        self.assertEqual(contracts[0]['status'], 'pending')
        self.assertIn('value', contracts[0])
        self.assertTrue(contracts[0]['value']['valueAddedTaxPayer'])
        self.assertEqual(contracts[0]['value']['valueAddedTax'], 20)
        self.assertEqual(contracts[0]['value']['sumValueAddedTax'], 100)
        self.assertEqual(contracts[0]['value']['amountWithValueAddedTax'], 500)
        self.assertEqual(contracts[0]['value']['amountWithoutValueAddedTax'], 416.67)

        # Activate second award
        response = self.app.patch_json(
            '/tenders/{}/awards/{}?acc_token={}'.format(self.tender_id, second_award['id'], self.tender_token),
            {'data': {'status': 'active'}}
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        first_award = response.json['data']

        self.assertEqual(first_award['status'], 'active')
        self.assertTrue(first_award['value']['valueAddedTaxPayer'])
        self.assertEqual(first_award['value']['valueAddedTax'], 7)
        self.assertIn('sumValueAddedTax', first_award['value'])
        self.assertEqual(first_award['value']['sumValueAddedTax'], 35.0)
        self.assertIn('amountWithValueAddedTax', first_award['value'])
        self.assertEqual(first_award['value']['amountWithValueAddedTax'], 500)
        self.assertIn('amountWithoutValueAddedTax', first_award['value'])
        self.assertEqual(first_award['value']['amountWithoutValueAddedTax'], 467.29)

        # Get contracts
        response = self.app.get('/tenders/{}/contracts'.format(self.tender_id))

        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        contracts = response.json['data']

        self.assertEqual(contracts[1]['status'], 'pending')
        self.assertIn('value', contracts[1])
        self.assertTrue(contracts[1]['value']['valueAddedTaxPayer'])
        self.assertEqual(contracts[1]['value']['valueAddedTax'], 7)
        self.assertEqual(contracts[1]['value']['sumValueAddedTax'], 35.0)
        self.assertEqual(contracts[1]['value']['amountWithValueAddedTax'], 500)
        self.assertEqual(contracts[1]['value']['amountWithoutValueAddedTax'], 467.29)

        # Activate third award
        response = self.app.patch_json(
            '/tenders/{}/awards/{}?acc_token={}'.format(self.tender_id, third_award['id'], self.tender_token),
            {'data': {'status': 'active'}}
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        first_award = response.json['data']

        self.assertEqual(first_award['status'], 'active')
        self.assertTrue(first_award['value']['valueAddedTaxPayer'])
        self.assertEqual(first_award['value']['valueAddedTax'], 0)
        self.assertIn('sumValueAddedTax', first_award['value'])
        self.assertEqual(first_award['value']['sumValueAddedTax'], 0.0)
        self.assertIn('amountWithValueAddedTax', first_award['value'])
        self.assertEqual(first_award['value']['amountWithValueAddedTax'], 500)
        self.assertIn('amountWithoutValueAddedTax', first_award['value'])
        self.assertEqual(first_award['value']['amountWithoutValueAddedTax'], 500.0)

        # Get contracts
        response = self.app.get('/tenders/{}/contracts'.format(self.tender_id))

        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        contracts = response.json['data']

        self.assertEqual(contracts[2]['status'], 'pending')
        self.assertIn('value', contracts[1])
        self.assertTrue(contracts[2]['value']['valueAddedTaxPayer'])
        self.assertEqual(contracts[2]['value']['valueAddedTax'], 0)
        self.assertEqual(contracts[2]['value']['sumValueAddedTax'], 0.0)
        self.assertEqual(contracts[2]['value']['amountWithValueAddedTax'], 500)
        self.assertEqual(contracts[2]['value']['amountWithoutValueAddedTax'], 500.0)

        # Edit contract
        response = self.app.get('/tenders/{}/contracts'.format(self.tender_id))
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        contract = response.json['data'][0]

        self.assertEqual(contract['status'], 'pending')
        self.assertEqual(contract['value']['amount'], 100500)
        self.assertTrue(contract['value']['valueAddedTaxPayer'])
        self.assertEqual(contract['value']['valueAddedTax'], 20)

        # Change contract amount
        response = self.app.patch_json(
            '/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token),
            {'data': {'value': {'amount': 550}}}
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        contract = response.json['data']

        self.assertEqual(contract['value']['amount'], 550)
        self.assertEqual(contract['value']['valueAddedTax'], 20)

        # Change contract valueAddedTax
        response = self.app.patch_json(
            '/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token),
            {'data': {'value': {'valueAddedTax': 7}}}
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        contract = response.json['data']

        self.assertEqual(contract['value']['amount'], 550)
        self.assertEqual(contract['value']['valueAddedTax'], 7)
        self.assertTrue(contract['value']['valueAddedTaxPayer'])

        # Change contract valueAddedTaxPayer
        response = self.app.patch_json(
            '/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token),
            {'data': {'value': {'valueAddedTaxPayer': False}}}, status=403
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['403'])
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(
            response.json['errors'][0],
            {u'description': u"Can't update valueAddedTaxPayer for contract value", u'location': u'body',
             u'name': u'data'}
        )

        # Editing value in contract
        response = self.app.patch_json(
            '/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token),
            {'data': {'value': {
                'amount': 200.0,
                'sumValueAddedTax': 35.1,
            }}}
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.get(
            '/tenders/{}/contracts/{}'.format(self.tender_id, contract['id'])
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        contract = response.json['data']

        # Recalculation value in accordance with amount
        self.assertEqual(contract['value']['sumValueAddedTax'], 14.0)

        # Editing value in contract
        response = self.app.patch_json(
            '/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token),
            {'data': {'value': {
                'amount': 200.0,
                'amountWithValueAddedTax': 35.1,
            }}}
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.get(
            '/tenders/{}/contracts/{}'.format(self.tender_id, contract['id'])
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        contract = response.json['data']

        # Recalculation value in accordance with amount
        self.assertEqual(contract['value']['amountWithValueAddedTax'], 200.0)

        # Editing value in contract
        response = self.app.patch_json(
            '/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token),
            {'data': {'value': {
                'amount': 200.0,
                'amountWithoutValueAddedTax': 35.1,
            }}}
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.get(
            '/tenders/{}/contracts/{}'.format(self.tender_id, contract['id'])
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        contract = response.json['data']

        # Recalculation value in accordance with amount
        self.assertEqual(contract['value']['amountWithoutValueAddedTax'], 186.92)

        # Update only value:amountWithoutValueAddedTax field
        response = self.app.patch_json(
            '/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token),
            {'data': {'value': {
                'amountWithoutValueAddedTax': 500.08
            }}}
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.get(
            '/tenders/{}/contracts/{}'.format(self.tender_id, contract['id'])
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        contract = response.json['data']

        # But value:amountWithoutValueAddedTax currency stays unchanged
        self.assertEqual(contract['value']['amountWithoutValueAddedTax'], 186.92)

        # Update only value:amountWithValueAddedTax field
        response = self.app.patch_json(
            '/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token),
            {'data': {'value': {
                'amountWithValueAddedTax': 500.08
            }}}
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.get(
            '/tenders/{}/contracts/{}'.format(self.tender_id, contract['id'])
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        contract = response.json['data']

        # But value:amountWithValueAddedTax currency stays unchanged
        self.assertEqual(contract['value']['amountWithValueAddedTax'], 200.0)

        # Update only value:sumValueAddedTax field
        response = self.app.patch_json(
            '/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token),
            {'data': {'value': {
                'sumValueAddedTax': 500.08
            }}}
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.get(
            '/tenders/{}/contracts/{}'.format(self.tender_id, contract['id'])
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        contract = response.json['data']

        # But value:sumValueAddedTax currency stays unchanged
        self.assertEqual(contract['value']['sumValueAddedTax'], 14.0)

    def test_create_tender_contract_with_not_tender_vat(self):
        # Change tender value:valueAddedTaxIncluded to False
        self.set_status(
            'active.tendering',
            {'minimalStep': {'valueAddedTaxIncluded': False}, 'value': {'valueAddedTaxIncluded': False}}
        )

        response = self.app.get(
            '/tenders/{}'.format(self.tender_id)
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        tender = response.json['data']

        self.assertFalse(tender['value']['valueAddedTaxIncluded'])
        self.assertFalse(tender['minimalStep']['valueAddedTaxIncluded'])
        self.assertEqual(tender['status'], 'active.tendering')

        # Create bid
        response = self.app.post_json(
            '/tenders/{}/bids'.format(self.tender_id),
            {'data': {
                'tenderers': [test_organization],
                'value': {'amount': 500, 'valueAddedTax': 7, 'valueAddedTaxPayer': False},
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

        self.assertFalse(bid['value']['valueAddedTaxPayer'])
        self.assertEqual(bid['value']['valueAddedTax'], 7)

        self.set_status('active.qualification')

        response = self.app.get('/tenders/{}'.format(self.tender_id))
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        tender = response.json['data']

        self.assertFalse(tender['value']['valueAddedTaxIncluded'])
        self.assertFalse(tender['minimalStep']['valueAddedTaxIncluded'])

        # Create award
        response = self.app.post_json(
            '/tenders/{}/awards'.format(self.tender_id), {'data': {
                'suppliers': [test_organization],
                'status': 'pending',
                'bid_id': bid['id'],
                'value': {'amount': 500}
            }}
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['201'])
        self.assertEqual(response.content_type, 'application/json')

        award = response.json['data']

        self.assertFalse(award['value']['valueAddedTaxPayer'])
        self.assertEqual(award['value']['amount'], 500)
        self.assertEqual(award['value']['valueAddedTax'], 7)

        # Change award status to active
        self.assertEqual(award['status'], 'pending')

        response = self.app.patch_json(
            '/tenders/{}/awards/{}?acc_token={}'.format(self.tender_id, award['id'], self.tender_token),
            {'data': {'status': 'active'}}
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        award = response.json['data']

        self.assertEqual(award['status'], 'active')
        self.assertIn('sumValueAddedTax', award['value'])
        self.assertIn('amountWithValueAddedTax', award['value'])
        self.assertIn('amountWithoutValueAddedTax', award['value'])

        self.assertFalse(award['value']['valueAddedTaxPayer'])
        self.assertEqual(award['value']['amount'], 500)
        self.assertEqual(award['value']['valueAddedTax'], 7)
        self.assertEqual(award['value']['sumValueAddedTax'], 35.0)
        self.assertEqual(award['value']['amountWithValueAddedTax'], 535.0)
        self.assertEqual(award['value']['amountWithoutValueAddedTax'], 500.0)

        # Get contract
        response = self.app.get(
            '/tenders/{}/contracts'.format(self.tender_id)
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        contract = response.json['data'][0]

        self.assertFalse(contract['value']['valueAddedTaxPayer'])
        self.assertEqual(contract['value']['amount'], 500)
        self.assertEqual(contract['value']['valueAddedTax'], 7)
        self.assertEqual(contract['value']['sumValueAddedTax'], 35.0)
        self.assertEqual(contract['value']['amountWithValueAddedTax'], 535.0)
        self.assertEqual(contract['value']['amountWithoutValueAddedTax'], 500.0)

        # Editing value in contract
        response = self.app.patch_json(
            '/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token),
            {'data': {'value': {
                'amount': 200.0,
                'sumValueAddedTax': 35.1,
            }}}
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.get(
            '/tenders/{}/contracts/{}'.format(self.tender_id, contract['id'])
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        contract = response.json['data']

        # Recalculation value in accordance with amount
        self.assertEqual(contract['value']['sumValueAddedTax'], 14.0)

        # Editing value in contract
        response = self.app.patch_json(
            '/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token),
            {'data': {'value': {
                'amount': 200.0,
                'amountWithValueAddedTax': 35.1,
            }}}
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.get(
            '/tenders/{}/contracts/{}'.format(self.tender_id, contract['id'])
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        contract = response.json['data']

        # Recalculation value in accordance with amount
        self.assertEqual(contract['value']['amountWithValueAddedTax'], 214.0)

        # Editing value in contract
        response = self.app.patch_json(
            '/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token),
            {'data': {'value': {
                'amount': 200.0,
                'amountWithoutValueAddedTax': 35.1,
            }}}
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.get(
            '/tenders/{}/contracts/{}'.format(self.tender_id, contract['id'])
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        contract = response.json['data']

        # Recalculation value in accordance with amount
        self.assertEqual(contract['value']['amountWithoutValueAddedTax'], 200.0)

        # Update only value:amountWithoutValueAddedTax field
        response = self.app.patch_json(
            '/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token),
            {'data': {'value': {
                'amountWithoutValueAddedTax': 500.08
            }}}
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.get(
            '/tenders/{}/contracts/{}'.format(self.tender_id, contract['id'])
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        contract = response.json['data']

        # But value:amountWithoutValueAddedTax currency stays unchanged
        self.assertEqual(contract['value']['amountWithoutValueAddedTax'], 200.0)

        # Update only value:amountWithValueAddedTax field
        response = self.app.patch_json(
            '/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token),
            {'data': {'value': {
                'amountWithValueAddedTax': 500.08
            }}}
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.get(
            '/tenders/{}/contracts/{}'.format(self.tender_id, contract['id'])
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        contract = response.json['data']

        # But value:amountWithValueAddedTax currency stays unchanged
        self.assertEqual(contract['value']['amountWithValueAddedTax'], 214.0)

        # Update only value:sumValueAddedTax field
        response = self.app.patch_json(
            '/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token),
            {'data': {'value': {
                'sumValueAddedTax': 500.08
            }}}
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.get(
            '/tenders/{}/contracts/{}'.format(self.tender_id, contract['id'])
        )
        self.assertEqual(response.status, self.RESPONSE_CODE['200'])
        self.assertEqual(response.content_type, 'application/json')

        contract = response.json['data']

        # But value:sumValueAddedTax currency stays unchanged
        self.assertEqual(contract['value']['sumValueAddedTax'], 14.0)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TenderContractResourceTest))
    suite.addTest(unittest.makeSuite(TenderContractDocumentResourceTest))
    suite.addTest(unittest.makeSuite(TenderContractValueAddedTaxPayer))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
