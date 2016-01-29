# -*- coding: utf-8 -*-
import json
import os
from datetime import timedelta

import openprocurement.api.tests.base as base_test
from openprocurement.api.models import get_now
from openprocurement.api.tests.tender import BaseTenderWebTest
from webtest import TestApp

test_tender_data = base_test.test_tender_data
test_bids = base_test.test_bids


test_complaint_data = {'data':
        {
            'title': 'complaint title',
            'description': 'complaint description',
            'author': test_tender_data["procuringEntity"]
        }
    }

class DumpsTestAppwebtest(TestApp):
    def do_request(self, req, status=None, expect_errors=None):
        req.headers.environ["HTTP_HOST"] = "api-sandbox.openprocurement.org"
        if not self.file_obj.closed:
            self.file_obj.write(req.as_bytes(True))
            self.file_obj.write("\n")
            if req.body:
                try:
                    self.file_obj.write(
                            'DATA:\n' + json.dumps(json.loads(req.body), indent=2, ensure_ascii=False).encode('utf8'))
                    self.file_obj.write("\n")
                except:
                    pass
            self.file_obj.write("\n")
        resp = super(DumpsTestAppwebtest, self).do_request(req, status=status, expect_errors=expect_errors)
        if not self.file_obj.closed:
            headers = [(n.title(), v)
                       for n, v in resp.headerlist
                       if n.lower() != 'content-length']
            headers.sort()
            self.file_obj.write(str('Response: %s\n%s\n') % (
                resp.status,
                str('\n').join([str('%s: %s') % (n, v) for n, v in headers]),
            ))

            if resp.testbody:
                try:
                    self.file_obj.write(json.dumps(json.loads(resp.testbody), indent=2, ensure_ascii=False).encode('utf8'))
                except:
                    pass
            self.file_obj.write("\n\n")
        return resp


class TenderResourceTest(BaseTenderWebTest):
    initial_data = test_tender_data
    initial_bids = test_bids

    def setUp(self):
        self.app = DumpsTestAppwebtest(
                "config:tests.ini", relative_to=os.path.dirname(base_test.__file__))
        self.app.RequestClass = base_test.PrefixedRequestClass
        self.app.authorization = ('Basic', ('token', ''))
        self.couchdb_server = self.app.app.registry.couchdb_server
        self.db = self.app.app.registry.db

    def test_docs_complaints(self):
        request_path = '/tenders?opt_pretty=1'


        ###################### Tender Conditions Claims/Complaints ##################
        #
        #### Claim Submission (with documents)
        #

        with open('docs/source/complaints/complaint-submission.http', 'w') as self.app.file_obj:
            self.app.file_obj.close()
            self.create_tender()

        with open('docs/source/complaints/complaint-submission.http', 'w') as self.app.file_obj:
            response = self.app.post_json('/tenders/{}/complaints'.format(
                self.tender_id), test_complaint_data)
            self.assertEqual(response.status, '201 Created')

        complaint1_id = response.json['data']['id']
        complaint1_token = response.json['access']['token']

        with open('docs/source/complaints/complaint-submission-upload.http', 'w') as self.app.file_obj:
            response = self.app.post('/tenders/{}/complaints/{}/documents?acc_token={}'.format(
                    self.tender_id, complaint1_id, complaint1_token), upload_files=[('file', u'Complaint_Attachement.pdf', 'content')])
            self.assertEqual(response.status, '201 Created')

        with open('docs/source/complaints/complaint-claim.http', 'w') as self.app.file_obj:
            response = self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(
                    self.tender_id, complaint1_id, complaint1_token), {"data":{"status":"claim"}})
            self.assertEqual(response.status, '200 OK')

        #### Claim Submission (without documents)
        #

        test_complaint_data['data']['status'] = 'claim'

        with open('docs/source/complaints/complaint-submission-claim.http', 'w') as self.app.file_obj:
            response = self.app.post_json('/tenders/{}/complaints'.format(
                self.tender_id), test_complaint_data)
            self.assertEqual(response.status, '201 Created')

        complaint2_id = response.json['data']['id']
        complaint2_token = response.json['access']['token']

        #### Tender Conditions Claim/Complaint Retrieval
        #

        with open('docs/source/complaints/complaints-list.http', 'w') as self.app.file_obj:
            self.app.authorization = None
            response = self.app.get('/tenders/{}/complaints'.format(self.tender_id))
            self.assertEqual(response.status, '200 OK')

        with open('docs/source/complaints/complaint.http', 'w') as self.app.file_obj:
            response = self.app.get('/tenders/{}/complaints/{}'.format(self.tender_id, complaint1_id))
            self.assertEqual(response.status, '200 OK')

        self.app.authorization = ('Basic', ('token', ''))

        #### Claim's Answer
        #

        with open('docs/source/complaints/complaint-answer.http', 'w') as self.app.file_obj:
            response = self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(
                    self.tender_id, complaint1_id, self.tender_token), {"data":{"status":"answered","resolutionType":"resolved","resolution":"Виправлено"}})
            self.assertEqual(response.status, '200 OK')


        #### Satisfied Claim
        #

        with open('docs/source/complaints/complaint-satisfy.http', 'w') as self.app.file_obj:
            response = self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(
                    self.tender_id, complaint1_id, complaint1_token), {"data":{"status":"resolved","satisfied":True}})
            self.assertEqual(response.status, '200 OK')

        #### Satisfied Claim
        #

        with open('docs/source/complaints/complaint-escalate.http', 'w') as self.app.file_obj:
            self.app.file_obj.close()

            response = self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(
                    self.tender_id, complaint2_id, self.tender_token), {"data":{"status":"answered","resolutionType":"resolved","resolution":"Виправлено"}})
            self.assertEqual(response.status, '200 OK')

        with open('docs/source/complaints/complaint-escalate.http', 'w') as self.app.file_obj:
            response = self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(
                    self.tender_id, complaint2_id, complaint2_token), {"data":{"status":"pending","satisfied":False}})
            self.assertEqual(response.status, '200 OK')

        #### Rejecting Tender Conditions Complaint
        #

        self.app.authorization = ('Basic', ('reviewer', ''))

        with open('docs/source/complaints/complaint-reject.http', 'w') as self.app.file_obj:
            response = self.app.patch_json('/tenders/{}/complaints/{}'.format(
                    self.tender_id, complaint2_id), {"data":{"status":"invalid"}})
            self.assertEqual(response.status, '200 OK')

        #### Submitting Tender Conditions Complaint Resolution
        #

        self.app.authorization = ('Basic', ('token', ''))

        with open('docs/source/complaints/complaint-resolve.http', 'w') as self.app.file_obj:
            self.app.file_obj.close()

            response = self.app.post_json('/tenders/{}/complaints'.format(
                self.tender_id), test_complaint_data)
            self.assertEqual(response.status, '201 Created')
            complaint3_id = response.json['data']['id']
            complaint3_token = response.json['access']['token']
            self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(
                    self.tender_id, complaint3_id, self.tender_token), {"data":{"status":"answered","resolutionType":"resolved","resolution":"Виправлено"}})
            self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(
                    self.tender_id, complaint3_id, complaint3_token), {"data":{"status":"pending","satisfied":False}})


            response = self.app.post_json('/tenders/{}/complaints'.format(
                self.tender_id), test_complaint_data)
            self.assertEqual(response.status, '201 Created')
            complaint4_id = response.json['data']['id']
            complaint4_token = response.json['access']['token']
            self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(
                    self.tender_id, complaint4_id, self.tender_token), {"data":{"status":"answered","resolutionType":"resolved","resolution":"Виправлено"}})
            self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(
                    self.tender_id, complaint4_id, complaint4_token), {"data":{"status":"pending","satisfied":False}})


        self.app.authorization = ('Basic', ('reviewer', ''))

        with open('docs/source/complaints/complaint-resolution-upload.http', 'w') as self.app.file_obj:
            response = self.app.post('/tenders/{}/complaints/{}/documents'.format(
                    self.tender_id, complaint3_id), upload_files=[('file', u'ComplaintResolution.pdf', 'content')])
            self.assertEqual(response.status, '201 Created')

        with open('docs/source/complaints/complaint-resolve.http', 'w') as self.app.file_obj:
            response = self.app.patch_json('/tenders/{}/complaints/{}'.format(
                    self.tender_id, complaint3_id), {"data":{"status":"resolved"}})
            self.assertEqual(response.status, '200 OK')

        with open('docs/source/complaints/complaint-decline.http', 'w') as self.app.file_obj:
            response = self.app.patch_json('/tenders/{}/complaints/{}'.format(
                    self.tender_id, complaint4_id), {"data":{"status":"declined"}})
            self.assertEqual(response.status, '200 OK')



        ###################### Tender Award Claims/Complaints ##################
        #

        #### Tender Award Claim Submission (with documents)
        #

        self.app.authorization = ('Basic', ('token', ''))
        self.set_status('active.qualification')

        with open('docs/source/complaints/award-complaint-submission.http', 'w') as self.app.file_obj:
            self.app.file_obj.close()

            request_path = '/tenders/{}/awards'.format(self.tender_id)
            response = self.app.post_json(request_path, {'data': {'suppliers': [test_tender_data["procuringEntity"]], 'status': u'active', 'bid_id': self.initial_bids[0]['id'], "value": {"amount": 500}}})

        award_id = response.json['data']['id']

        del test_complaint_data['data']['status']

        with open('docs/source/complaints/award-complaint-submission.http', 'w') as self.app.file_obj:
            response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(
                self.tender_id, award_id), test_complaint_data)
            self.assertEqual(response.status, '201 Created')


        complaint1_id = response.json['data']['id']
        complaint1_token = response.json['access']['token']

        with open('docs/source/complaints/award-complaint-submission-upload.http', 'w') as self.app.file_obj:
            response = self.app.post('/tenders/{}/awards/{}/complaints/{}/documents?acc_token={}'.format(
                    self.tender_id, award_id, complaint1_id, complaint1_token), upload_files=[('file', u'Complaint_Attachement.pdf', 'content')])
            self.assertEqual(response.status, '201 Created')

        with open('docs/source/complaints/award-complaint-claim.http', 'w') as self.app.file_obj:
            response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(
                    self.tender_id, award_id, complaint1_id, complaint1_token), {"data":{"status":"claim"}})
            self.assertEqual(response.status, '200 OK')

        #### Tender Award Claim Submission (without documents)
        #

        test_complaint_data['data']['status'] = 'claim'

        with open('docs/source/complaints/award-complaint-submission-claim.http', 'w') as self.app.file_obj:
            response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(
                self.tender_id, award_id,), test_complaint_data)
            self.assertEqual(response.status, '201 Created')

        complaint2_id = response.json['data']['id']
        complaint2_token = response.json['access']['token']

        #### Tender Award Claim/Complaint Retrieval
        #

        with open('docs/source/complaints/award-complaints-list.http', 'w') as self.app.file_obj:
            self.app.authorization = None
            response = self.app.get('/tenders/{}/awards/{}/complaints'.format(self.tender_id, award_id,))
            self.assertEqual(response.status, '200 OK')

        with open('docs/source/complaints/award-complaint.http', 'w') as self.app.file_obj:
            response = self.app.get('/tenders/{}/awards/{}/complaints/{}'.format(self.tender_id, award_id, complaint1_id))
            self.assertEqual(response.status, '200 OK')

        self.app.authorization = ('Basic', ('token', ''))

        #### Claim's Answer
        #

        with open('docs/source/complaints/award-complaint-answer.http', 'w') as self.app.file_obj:
            response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(
                    self.tender_id, award_id, complaint1_id, self.tender_token), {"data":{"status":"answered","resolutionType":"resolved","resolution":"Виправлено"}})
            self.assertEqual(response.status, '200 OK')


        #### Satisfied Claim
        #

        with open('docs/source/complaints/award-complaint-satisfy.http', 'w') as self.app.file_obj:
            response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(
                    self.tender_id, award_id, complaint1_id, complaint1_token), {"data":{"status":"resolved","satisfied":True}})
            self.assertEqual(response.status, '200 OK')

        #### Satisfied Claim
        #

        with open('docs/source/complaints/award-complaint-escalate.http', 'w') as self.app.file_obj:
            self.app.file_obj.close()

            response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(
                    self.tender_id, award_id, complaint2_id, self.tender_token), {"data":{"status":"answered","resolutionType":"resolved","resolution":"Виправлено"}})
            self.assertEqual(response.status, '200 OK')

        with open('docs/source/complaints/award-complaint-escalate.http', 'w') as self.app.file_obj:
            response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(
                    self.tender_id, award_id, complaint2_id, complaint2_token), {"data":{"status":"pending","satisfied":False}})
            self.assertEqual(response.status, '200 OK')

        #### Rejecting Tender Award Complaint
        #

        self.app.authorization = ('Basic', ('reviewer', ''))

        with open('docs/source/complaints/award-complaint-reject.http', 'w') as self.app.file_obj:
            response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}'.format(
                    self.tender_id, award_id, complaint2_id), {"data":{"status":"invalid"}})
            self.assertEqual(response.status, '200 OK')

        #### Submitting Tender Award Complaint Resolution
        #

        self.app.authorization = ('Basic', ('token', ''))

        with open('docs/source/complaints/award-complaint-resolve.http', 'w') as self.app.file_obj:
            self.app.file_obj.close()

            response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(
                self.tender_id, award_id), test_complaint_data)
            self.assertEqual(response.status, '201 Created')
            complaint3_id = response.json['data']['id']
            complaint3_token = response.json['access']['token']
            self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(
                    self.tender_id, award_id, complaint3_id, self.tender_token), {"data":{"status":"answered","resolutionType":"resolved","resolution":"Виправлено"}})
            self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(
                    self.tender_id, award_id, complaint3_id, complaint3_token), {"data":{"status":"pending","satisfied":False}})


            response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(
                self.tender_id, award_id), test_complaint_data)
            self.assertEqual(response.status, '201 Created')
            complaint4_id = response.json['data']['id']
            complaint4_token = response.json['access']['token']
            self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(
                    self.tender_id, award_id, complaint4_id, self.tender_token), {"data":{"status":"answered","resolutionType":"resolved","resolution":"Виправлено"}})
            self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(
                    self.tender_id, award_id, complaint4_id, complaint4_token), {"data":{"status":"pending","satisfied":False}})


        self.app.authorization = ('Basic', ('reviewer', ''))

        with open('docs/source/complaints/award-complaint-resolution-upload.http', 'w') as self.app.file_obj:
            response = self.app.post('/tenders/{}/awards/{}/complaints/{}/documents'.format(
                    self.tender_id, award_id, complaint3_id), upload_files=[('file', u'ComplaintResolution.pdf', 'content')])
            self.assertEqual(response.status, '201 Created')

        with open('docs/source/complaints/award-complaint-resolve.http', 'w') as self.app.file_obj:
            response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}'.format(
                    self.tender_id, award_id, complaint3_id), {"data":{"status":"resolved"}})
            self.assertEqual(response.status, '200 OK')

        with open('docs/source/complaints/award-complaint-decline.http', 'w') as self.app.file_obj:
            response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}'.format(
                    self.tender_id, award_id, complaint4_id), {"data":{"status":"declined"}})
            self.assertEqual(response.status, '200 OK')