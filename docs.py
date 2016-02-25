
# -*- coding: utf-8 -*-
import json
import os
from datetime import timedelta, datetime
from uuid import uuid4

import openprocurement.api.tests.base as base_test
from openprocurement.api.tests.base import test_tender_data, test_bids, PrefixedRequestClass
from openprocurement.api.models import get_now
from openprocurement.api.tests.tender import BaseTenderWebTest
from webtest import TestApp

now = datetime.now()


bid = {
    "data": {
        "tenderers": [
            {
                "address": {
                    "countryName": "Україна",
                    "locality": "м. Вінниця",
                    "postalCode": "21100",
                    "region": "м. Вінниця",
                    "streetAddress": "вул. Островського, 33"
                },
                "contactPoint": {
                    "email": "soleksuk@gmail.com",
                    "name": "Сергій Олексюк",
                    "telephone": "+380 (432) 21-69-30"
                },
                "identifier": {
                    "scheme": u"UA-EDR",
                    "id": u"00137256",
                    "uri": u"http://www.sc.gov.ua/"
                },
                "name": "ДКП «Школяр»"
            }
        ],
        "value": {
            "amount": 500
        }
    }
}

bid2 = {
    "data": {
        "tenderers": [
            {
                "address": {
                    "countryName": "Україна",
                    "locality": "м. Львів",
                    "postalCode": "79013",
                    "region": "м. Львів",
                    "streetAddress": "вул. Островського, 34"
                },
                "contactPoint": {
                    "email": "aagt@gmail.com",
                    "name": "Андрій Олексюк",
                    "telephone": "+380 (322) 91-69-30"
                },
                "identifier": {
                    "scheme": u"UA-EDR",
                    "id": u"00137226",
                    "uri": u"http://www.sc.gov.ua/"
                },
                "name": "ДКП «Книга»"
            }
        ],
        "value": {
            "amount": 499
        }
    }
}

question = {
    "data": {
        "author": {
            "address": {
                "countryName": "Україна",
                "locality": "м. Вінниця",
                "postalCode": "21100",
                "region": "м. Вінниця",
                "streetAddress": "вул. Островського, 33"
            },
            "contactPoint": {
                "email": "soleksuk@gmail.com",
                "name": "Сергій Олексюк",
                "telephone": "+380 (432) 21-69-30"
            },
            "identifier": {
                "id": "00137226",
                "legalName": "Державне комунальне підприємство громадського харчування «Школяр»",
                "scheme": "UA-EDR",
                "uri": "http://sch10.edu.vn.ua/"
            },
            "name": "ДКП «Школяр»"
        },
        "description": "Просимо додати таблицю потрібної калорійності харчування",
        "title": "Калорійність"
    }
}

answer = {
    "data": {
        "answer": "Таблицю додано в файлі \"Kalorijnist.xslx\""
    }
}

cancellation = {
    'data': {
        'reason': 'cancellation reason'
    }
}

test_max_uid = uuid4().hex

test_tender_maximum_data = {
    "title": u"футляри до державних нагород",
    "title_en": u"Cases with state awards",
    "title_ru": u"футляры к государственным наградам",
    "procuringEntity": {
        "name": u"Державне управління справами",
        "identifier": {
            "scheme": u"UA-EDR",
            "id": u"00037256",
            "uri": u"http://www.dus.gov.ua/"
        },
        "address": {
            "countryName": u"Україна",
            "postalCode": u"01220",
            "region": u"м. Київ",
            "locality": u"м. Київ",
            "streetAddress": u"вул. Банкова, 11, корпус 1"
        },
        "contactPoint": {
            "name": u"Державне управління справами",
            "telephone": u"0440000000"
        }
    },
    "value": {
        "amount": 500,
        "currency": u"UAH"
    },
    "minimalStep": {
        "amount": 35,
        "currency": u"UAH"
    },
    "items": [
        {
            "id": test_max_uid,
            "description": u"футляри до державних нагород",
            "description_en": u"Cases with state awards",
            "description_ru": u"футляры к государственным наградам",
            "classification": {
                "scheme": u"CPV",
                "id": u"44617100-9",
                "description": u"Cartons"
            },
            "additionalClassifications": [
                {
                    "scheme": u"ДКПП",
                    "id": u"17.21.1",
                    "description": u"папір і картон гофровані, паперова й картонна тара"
                }
            ],
            "unit": {
                "name": u"item",
                "code": u"44617100-9"
            },
            "quantity": 5
        }
    ],
    "enquiryPeriod": {
        "endDate": (now + timedelta(days=7)).isoformat()
    },
    "tenderPeriod": {
        "endDate": (now + timedelta(days=14)).isoformat()
    },
    "procurementMethodType": "belowThreshold",
    "mode": u"test",
    "features": [
        {
            "code": "OCDS-123454-AIR-INTAKE",
            "featureOf": "item",
            "relatedItem": test_max_uid,
            "title": u"Потужність всмоктування",
            "title_en": "Air Intake",
            "description": u"Ефективна потужність всмоктування пилососа, в ватах (аероватах)",
            "enum": [
                {
                    "value": 0.1,
                    "title": u"До 1000 Вт"
                },
                {
                    "value": 0.15,
                    "title": u"Більше 1000 Вт"
                }
            ]
        },
        {
            "code": "OCDS-123454-YEARS",
            "featureOf": "tenderer",
            "title": u"Років на ринку",
            "title_en": "Years trading",
            "description": u"Кількість років, які організація учасник працює на ринку",
            "enum": [
                {
                    "value": 0.05,
                    "title": u"До 3 років"
                },
                {
                    "value": 0.1,
                    "title": u"Більше 3 років, менше 5 років"
                },
                {
                    "value": 0.15,
                    "title": u"Більше 5 років"
                }
            ]
        }
    ]
}


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
        if hasattr(self, 'file_obj') and not self.file_obj.closed:
            self.file_obj.write(req.as_bytes(True))
            self.file_obj.write("\n")
            if req.body:
                try:
                    self.file_obj.write(
                        '\n' + json.dumps(json.loads(req.body), indent=2, ensure_ascii=False).encode('utf8'))
                    self.file_obj.write("\n")
                except:
                    pass
            self.file_obj.write("\n")
        resp = super(DumpsTestAppwebtest, self).do_request(req, status=status, expect_errors=expect_errors)
        if hasattr(self, 'file_obj') and not self.file_obj.closed:
            headers = [(n.title(), v)
                       for n, v in resp.headerlist
                       if n.lower() != 'content-length']
            headers.sort()
            self.file_obj.write(str('\n%s\n%s\n') % (
                resp.status,
                str('\n').join([str('%s: %s') % (n, v) for n, v in headers]),
            ))

            if resp.testbody:
                try:
                    self.file_obj.write('\n' + json.dumps(json.loads(resp.testbody), indent=2, ensure_ascii=False).encode('utf8'))
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
        self.app.RequestClass = PrefixedRequestClass
        self.app.authorization = ('Basic', ('broker', ''))
        self.couchdb_server = self.app.app.registry.couchdb_server
        self.db = self.app.app.registry.db

    def test_docs_tutorial(self):
        request_path = '/tenders?opt_pretty=1'

        # Exploring basic rules
        #

        with open('docs/source/tutorial/tender-listing.http', 'w') as self.app.file_obj:
            self.app.authorization = ('Basic', ('broker', ''))
            response = self.app.get('/tenders')
            self.assertEqual(response.status, '200 OK')
            self.app.file_obj.write("\n")

        with open('docs/source/tutorial/tender-post-attempt.http', 'w') as self.app.file_obj:
            response = self.app.post(request_path, 'data', status=415)
            self.assertEqual(response.status, '415 Unsupported Media Type')

        self.app.authorization = ('Basic', ('broker', ''))

        with open('docs/source/tutorial/tender-post-attempt-json.http', 'w') as self.app.file_obj:
            self.app.authorization = ('Basic', ('broker', ''))
            response = self.app.post(
                request_path, 'data', content_type='application/json', status=422)
            self.assertEqual(response.status, '422 Unprocessable Entity')

        # Creating tender
        #

        with open('docs/source/tutorial/tender-post-attempt-json-data.http', 'w') as self.app.file_obj:
            response = self.app.post_json(
                '/tenders?opt_pretty=1', {"data": test_tender_data})
            self.assertEqual(response.status, '201 Created')

        tender = response.json['data']
        owner_token = response.json['access']['token']

        with open('docs/source/tutorial/blank-tender-view.http', 'w') as self.app.file_obj:
            response = self.app.get('/tenders/{}'.format(tender['id']))
            self.assertEqual(response.status, '200 OK')

        with open('docs/source/tutorial/initial-tender-listing.http', 'w') as self.app.file_obj:
            response = self.app.get('/tenders')
            self.assertEqual(response.status, '200 OK')

        with open('docs/source/tutorial/create-tender-procuringEntity.http', 'w') as self.app.file_obj:
            response = self.app.post_json(
                '/tenders?opt_pretty=1', {"data": test_tender_maximum_data})
            self.assertEqual(response.status, '201 Created')

        response = self.app.post_json('/tenders?opt_pretty=1', {"data": test_tender_data})
        self.assertEqual(response.status, '201 Created')

        with open('docs/source/tutorial/tender-listing-after-procuringEntity.http', 'w') as self.app.file_obj:
            response = self.app.get('/tenders')
            self.assertEqual(response.status, '200 OK')

        self.app.authorization = ('Basic', ('broker', ''))

        # Modifying tender
        #

        tenderPeriod_endDate = get_now() + timedelta(days=15, seconds=10)
        with open('docs/source/tutorial/patch-items-value-periods.http', 'w') as self.app.file_obj:
            response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender['id'], owner_token), {'data':
                {
                    "tenderPeriod": {
                        "endDate": tenderPeriod_endDate.isoformat()
                    }
                }
            })

        with open('docs/source/tutorial/tender-listing-after-patch.http', 'w') as self.app.file_obj:
            self.app.authorization = None
            response = self.app.get(request_path)
            self.assertEqual(response.status, '200 OK')

        self.app.authorization = ('Basic', ('broker', ''))
        self.tender_id = tender['id']

        # Uploading documentation
        #

        with open('docs/source/tutorial/upload-tender-notice.http', 'w') as self.app.file_obj:
            response = self.app.post('/tenders/{}/documents?acc_token={}'.format(
                self.tender_id, owner_token), upload_files=[('file', u'Notice.pdf', 'content')])
            self.assertEqual(response.status, '201 Created')

        doc_id = response.json["data"]["id"]
        with open('docs/source/tutorial/tender-documents.http', 'w') as self.app.file_obj:
            response = self.app.get('/tenders/{}/documents/{}'.format(
                self.tender_id, doc_id))
            self.assertEqual(response.status, '200 OK')

        with open('docs/source/tutorial/tender-document-add-documentType.http', 'w') as self.app.file_obj:
            response = self.app.patch_json('/tenders/{}/documents/{}?acc_token={}'.format(
                self.tender_id, doc_id, owner_token), {"data": {"documentType": "technicalSpecifications"}})
            self.assertEqual(response.status, '200 OK')

        with open('docs/source/tutorial/tender-document-edit-docType-desc.http', 'w') as self.app.file_obj:
            response = self.app.patch_json('/tenders/{}/documents/{}?acc_token={}'.format(
                self.tender_id, doc_id, owner_token), {"data": {"description": "document description modified"}})
            self.assertEqual(response.status, '200 OK')

        with open('docs/source/tutorial/upload-award-criteria.http', 'w') as self.app.file_obj:
            response = self.app.post('/tenders/{}/documents?acc_token={}'.format(
                self.tender_id, owner_token), upload_files=[('file', u'AwardCriteria.pdf', 'content')])
            self.assertEqual(response.status, '201 Created')

        doc_id = response.json["data"]["id"]

        with open('docs/source/tutorial/tender-documents-2.http', 'w') as self.app.file_obj:
            response = self.app.get('/tenders/{}/documents'.format(
                self.tender_id))
            self.assertEqual(response.status, '200 OK')

        with open('docs/source/tutorial/update-award-criteria.http', 'w') as self.app.file_obj:
            response = self.app.put('/tenders/{}/documents/{}?acc_token={}'.format(
                self.tender_id, doc_id, owner_token), upload_files=[('file', 'AwardCriteria-2.pdf', 'content2')])
            self.assertEqual(response.status, '200 OK')

        with open('docs/source/tutorial/tender-documents-3.http', 'w') as self.app.file_obj:
            response = self.app.get('/tenders/{}/documents'.format(
                self.tender_id))
            self.assertEqual(response.status, '200 OK')

        # Enquiries
        #

        with open('docs/source/tutorial/ask-question.http', 'w') as self.app.file_obj:
            response = self.app.post_json('/tenders/{}/questions'.format(
                self.tender_id), question, status=201)
            question_id = response.json['data']['id']
            self.assertEqual(response.status, '201 Created')

        with open('docs/source/tutorial/answer-question.http', 'w') as self.app.file_obj:
            response = self.app.patch_json('/tenders/{}/questions/{}?acc_token={}'.format(
                self.tender_id, question_id, owner_token), answer, status=200)
            self.assertEqual(response.status, '200 OK')

        with open('docs/source/tutorial/list-question.http', 'w') as self.app.file_obj:
            response = self.app.get('/tenders/{}/questions'.format(
                self.tender_id))
            self.assertEqual(response.status, '200 OK')

        with open('docs/source/tutorial/get-answer.http', 'w') as self.app.file_obj:
            response = self.app.get('/tenders/{}/questions/{}'.format(
                self.tender_id, question_id))
            self.assertEqual(response.status, '200 OK')

        # Registering bid
        #

        self.set_status('active.tendering')
        self.app.authorization = ('Basic', ('broker', ''))
        bids_access = {}
        with open('docs/source/tutorial/register-bidder.http', 'w') as self.app.file_obj:
            response = self.app.post_json('/tenders/{}/bids'.format(
                self.tender_id), bid)
            bid1_id = response.json['data']['id']
            bids_access[bid1_id] = response.json['access']['token']
            self.assertEqual(response.status, '201 Created')

        # Proposal Uploading
        #

        with open('docs/source/tutorial/upload-bid-proposal.http', 'w') as self.app.file_obj:
            response = self.app.post('/tenders/{}/bids/{}/documents?acc_token={}'.format(
                self.tender_id, bid1_id, bids_access[bid1_id]), upload_files=[('file', 'Proposal.pdf', 'content')])
            self.assertEqual(response.status, '201 Created')

        with open('docs/source/tutorial/bidder-documents.http', 'w') as self.app.file_obj:
            response = self.app.get('/tenders/{}/bids/{}/documents?acc_token={}'.format(
                self.tender_id, bid1_id, bids_access[bid1_id]))
            self.assertEqual(response.status, '200 OK')

        # Bid invalidation
        #

        with open('docs/source/tutorial/bidder-after-changing-tender.http', 'w') as self.app.file_obj:
            response = self.app.get('/tenders/{}/bids/{}?acc_token={}'.format(
                self.tender_id, bid1_id, bids_access[bid1_id]))
            self.assertEqual(response.status, '200 OK')

        # Bid confirmation
        #

        with open('docs/source/tutorial/register-2nd-bidder.http', 'w') as self.app.file_obj:
            response = self.app.post_json('/tenders/{}/bids'.format(
                self.tender_id), bid2)
            bid2_id = response.json['data']['id']
            bids_access[bid2_id] = response.json['access']['token']
            self.assertEqual(response.status, '201 Created')

        # Auction
        #

        self.set_status('active.auction')
        self.app.authorization = ('Basic', ('auction', ''))
        patch_data = {
            'auctionUrl': u'http://auction-sandbox.openprocurement.org/tenders/{}'.format(self.tender_id),
            'bids': [
                {
                    "id": bid1_id,
                    "participationUrl": u'http://auction-sandbox.openprocurement.org/tenders/{}?key_for_bid={}'.format(self.tender_id, bid1_id)
                },
                {
                    "id": bid2_id,
                    "participationUrl": u'http://auction-sandbox.openprocurement.org/tenders/{}?key_for_bid={}'.format(self.tender_id, bid2_id)
                }
            ]
        }
        response = self.app.patch_json('/tenders/{}/auction?acc_token={}'.format(self.tender_id, owner_token),
                                       {'data': patch_data})
        self.assertEqual(response.status, '200 OK')

        self.app.authorization = ('Basic', ('broker', ''))

        with open('docs/source/tutorial/auction-url.http', 'w') as self.app.file_obj:
            response = self.app.get('/tenders/{}'.format(self.tender_id))
            self.assertEqual(response.status, '200 OK')

        with open('docs/source/tutorial/bidder-participation-url.http', 'w') as self.app.file_obj:
            response = self.app.get(
                '/tenders/{}/bids/{}?acc_token={}'.format(self.tender_id, bid1_id, bids_access[bid1_id]))
            self.assertEqual(response.status, '200 OK')

        with open('docs/source/tutorial/bidder2-participation-url.http', 'w') as self.app.file_obj:
            response = self.app.get(
                '/tenders/{}/bids/{}?acc_token={}'.format(self.tender_id, bid2_id, bids_access[bid2_id]))
            self.assertEqual(response.status, '200 OK')

        # Confirming qualification
        #

        self.app.authorization = ('Basic', ('auction', ''))
        response = self.app.get('/tenders/{}/auction'.format(self.tender_id))
        auction_bids_data = response.json['data']['bids']
        response = self.app.post_json('/tenders/{}/auction'.format(self.tender_id),
                                      {'data': {'bids': auction_bids_data}})

        self.app.authorization = ('Basic', ('broker', ''))

        response = self.app.get('/tenders/{}/awards?acc_token={}'.format(self.tender_id, owner_token))
        # get pending award
        award_id = [i['id'] for i in response.json['data'] if i['status'] == 'pending'][0]

        with open('docs/source/tutorial/confirm-qualification.http', 'w') as self.app.file_obj:
            self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(self.tender_id, award_id, owner_token), {"data": {"status": "active"}})
            self.assertEqual(response.status, '200 OK')

        #### Uploading contract documentation
        #

        response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(
                self.tender_id, owner_token))
        self.contract_id = response.json['data'][0]['id']

        with open('docs/source/tutorial/tender-contract-upload-document.http', 'w') as self.app.file_obj:
            response = self.app.post('/tenders/{}/contracts/{}/documents?acc_token={}'.format(
                self.tender_id, self.contract_id, owner_token), upload_files=[('file', 'contract_first_document.doc', 'content')])
            self.assertEqual(response.status, '201 Created')

        with open('docs/source/tutorial/tender-contract-get-documents.http', 'w') as self.app.file_obj:
            response = self.app.get('/tenders/{}/contracts/{}/documents'.format(
                self.tender_id, self.contract_id))
        self.assertEqual(response.status, '200 OK')

        with open('docs/source/tutorial/tender-contract-upload-second-document.http', 'w') as self.app.file_obj:
            response = self.app.post('/tenders/{}/contracts/{}/documents?acc_token={}'.format(
                self.tender_id, self.contract_id, owner_token), upload_files=[('file', 'contract_second_document.doc', 'content')])
            self.assertEqual(response.status, '201 Created')

        with open('docs/source/tutorial/tender-contract-get-documents-again.http', 'w') as self.app.file_obj:
            response = self.app.get('/tenders/{}/contracts/{}/documents'.format(
                self.tender_id, self.contract_id))
        self.assertEqual(response.status, '200 OK')

        #### Contract signing
        #

        tender = self.db.get(self.tender_id)
        for i in tender.get('awards', []):
            i['complaintPeriod']['endDate'] = i['complaintPeriod']['startDate']
        self.db.save(tender)

        with open('docs/source/tutorial/tender-contract-sign.http', 'w') as self.app.file_obj:
            response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
                    self.tender_id, self.contract_id, owner_token), {'data': {'status': 'active'}})
            self.assertEqual(response.status, '200 OK')


        # Preparing the cancellation request
        #

        self.set_status('active.awarded')
        with open('docs/source/tutorial/prepare-cancellation.http', 'w') as self.app.file_obj:
            response = self.app.post_json('/tenders/{}/cancellations?acc_token={}'.format(
                self.tender_id, owner_token), cancellation)
            self.assertEqual(response.status, '201 Created')

        cancellation_id = response.json['data']['id']

        # Filling cancellation with protocol and supplementary documentation
        #

        with open('docs/source/tutorial/upload-cancellation-doc.http', 'w') as self.app.file_obj:
            response = self.app.post('/tenders/{}/cancellations/{}/documents?acc_token={}'.format(
                self.tender_id, cancellation_id, owner_token), upload_files=[('file', u'Notice.pdf', 'content')])
            cancellation_doc_id = response.json['data']['id']
            self.assertEqual(response.status, '201 Created')

        with open('docs/source/tutorial/patch-cancellation.http', 'w') as self.app.file_obj:
            response = self.app.patch_json('/tenders/{}/cancellations/{}/documents/{}?acc_token={}'.format(
                self.tender_id, cancellation_id, cancellation_doc_id, owner_token), {'data': {"description": 'Changed description'}})
            self.assertEqual(response.status, '200 OK')

        with open('docs/source/tutorial/update-cancellation-doc.http', 'w') as self.app.file_obj:
            response = self.app.put('/tenders/{}/cancellations/{}/documents/{}?acc_token={}'.format(
                self.tender_id, cancellation_id, cancellation_doc_id, owner_token), upload_files=[('file', 'Notice-2.pdf', 'content2')])
            self.assertEqual(response.status, '200 OK')

        # Activating the request and cancelling tender
        #

        with open('docs/source/tutorial/active-cancellation.http', 'w') as self.app.file_obj:
            response = self.app.patch_json('/tenders/{}/cancellations/{}?acc_token={}'.format(
                self.tender_id, cancellation_id, owner_token), {"data": {"status": "active"}})
            self.assertEqual(response.status, '200 OK')


    def test_docs_complaints(self):

        ###################### Tender Conditions Claims/Complaints ##################
        #
        #### Claim Submission (with documents)
        #

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

        self.app.authorization = ('Basic', ('broker', ''))

        #### Claim's Answer
        #

        with open('docs/source/complaints/complaint-answer.http', 'w') as self.app.file_obj:
            response = self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(self.tender_id, complaint1_id, self.tender_token),
                {
                    "data": {
                        "status": "answered",
                        "resolutionType": "resolved",
                        "tendererAction": "Виправлено неконкурентні умови",
                        "resolution": "Виправлено неконкурентні умови"
                    }
                }
            )
            self.assertEqual(response.status, '200 OK')


        #### Satisfied Claim
        #

        with open('docs/source/complaints/complaint-satisfy.http', 'w') as self.app.file_obj:
            response = self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(
                    self.tender_id, complaint1_id, complaint1_token), {"data":{"status":"resolved","satisfied":True}})
            self.assertEqual(response.status, '200 OK')

        #### Satisfied Claim
        #


        response = self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(
                self.tender_id, complaint2_id, self.tender_token), {"data":{"status":"answered","resolutionType":"resolved","resolution":"Виправлено неконкурентні умови"}})
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

        self.app.authorization = ('Basic', ('broker', ''))


        response = self.app.post_json('/tenders/{}/complaints'.format(
            self.tender_id), test_complaint_data)
        self.assertEqual(response.status, '201 Created')
        complaint3_id = response.json['data']['id']
        complaint3_token = response.json['access']['token']
        self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(
                self.tender_id, complaint3_id, self.tender_token), {"data":{"status":"answered","resolutionType":"resolved","resolution":"Виправлено неконкурентні умови"}})
        self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(
                self.tender_id, complaint3_id, complaint3_token), {"data":{"status":"pending","satisfied":False}})

        response = self.app.post_json('/tenders/{}/complaints'.format(
            self.tender_id), test_complaint_data)
        self.assertEqual(response.status, '201 Created')
        del test_complaint_data['data']['status']
        complaint4_id = response.json['data']['id']
        complaint4_token = response.json['access']['token']
        self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(
                self.tender_id, complaint4_id, self.tender_token), {"data":{"status":"answered","resolutionType":"resolved","resolution":"Виправлено неконкурентні умови"}})
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

        self.app.authorization = ('Basic', ('broker', ''))
        # create tender
        response = self.app.post_json('/tenders',
                                      {"data": test_tender_data})
        tender_id = self.tender_id = response.json['data']['id']
        owner_token = self.tender_token = response.json['access']['token']
        # create bids
        self.set_status('active.tendering')
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.post_json('/tenders/{}/bids'.format(tender_id),
                                      {'data': {'tenderers': [test_tender_data["procuringEntity"]], "value": {"amount": 450}}})
        bid_id = response.json['data']['id']
        bid_token = response.json['access']['token']
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.post_json('/tenders/{}/bids'.format(tender_id),
                                      {'data': {'tenderers': [test_tender_data["procuringEntity"]], "value": {"amount": 475}}})
        # get auction info
        self.set_status('active.auction')
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
        # posting auction results
        self.app.authorization = ('Basic', ('auction', ''))
        response = self.app.post_json('/tenders/{}/auction'.format(tender_id),
                                      {'data': {'bids': auction_bids_data}})
        # get awards
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.get('/tenders/{}/awards?acc_token={}'.format(tender_id, owner_token))
        award_id = [i['id'] for i in response.json['data'] if i['status'] == 'pending'][0]


        with open('docs/source/complaints/award-complaint-submission.http', 'w') as self.app.file_obj:
            response = self.app.post_json('/tenders/{}/awards/{}/complaints?acc_token={}'.format(
                self.tender_id, award_id, bid_token), test_complaint_data)
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
            response = self.app.post_json('/tenders/{}/awards/{}/complaints?acc_token={}'.format(
                self.tender_id, award_id, bid_token), test_complaint_data)
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

        self.app.authorization = ('Basic', ('broker', ''))

        #### Claim's Answer
        #

        with open('docs/source/complaints/award-complaint-answer.http', 'w') as self.app.file_obj:
            response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(self.tender_id, award_id, complaint1_id, self.tender_token),
                {
                    "data": {
                        "status": "answered",
                        "resolutionType": "resolved",
                        "tendererAction": "Виправлено неконкурентні умови",
                        "resolution": "Виправлено неконкурентні умови"
                    }
                }
            )
            self.assertEqual(response.status, '200 OK')


        #### Satisfied Claim
        #

        with open('docs/source/complaints/award-complaint-satisfy.http', 'w') as self.app.file_obj:
            response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(
                    self.tender_id, award_id, complaint1_id, complaint1_token), {"data":{"status":"resolved","satisfied":True}})
            self.assertEqual(response.status, '200 OK')

        #### Satisfied Claim
        #
        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(
                self.tender_id, award_id, complaint2_id, self.tender_token), {"data":{"status":"answered","resolutionType":"resolved","resolution":"Виправлено неконкурентні умови"}})
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

        self.app.authorization = ('Basic', ('broker', ''))

        response = self.app.post_json('/tenders/{}/awards/{}/complaints?acc_token={}'.format(
            self.tender_id, award_id, bid_token), test_complaint_data)
        self.assertEqual(response.status, '201 Created')
        complaint3_id = response.json['data']['id']
        complaint3_token = response.json['access']['token']
        self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(
                self.tender_id, award_id, complaint3_id, self.tender_token), {"data":{"status":"answered","resolutionType":"resolved","resolution":"Виправлено неконкурентні умови"}})
        self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(
                self.tender_id, award_id, complaint3_id, complaint3_token), {"data":{"status":"pending","satisfied":False}})


        response = self.app.post_json('/tenders/{}/awards/{}/complaints?acc_token={}'.format(
            self.tender_id, award_id, bid_token), test_complaint_data)
        self.assertEqual(response.status, '201 Created')
        complaint4_id = response.json['data']['id']
        complaint4_token = response.json['access']['token']
        self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(
                self.tender_id, award_id, complaint4_id, self.tender_token), {"data":{"status":"answered","resolutionType":"resolved","resolution":"Виправлено неконкурентні умови"}})
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
