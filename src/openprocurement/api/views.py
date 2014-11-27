# -*- coding: utf-8 -*-
""" Cornice services.
"""
from datetime import datetime
from cornice.ext.spore import generate_spore_description
from cornice.resource import resource, view
from cornice.service import Service, get_services
from jsonpatch import make_patch, apply_patch
from openprocurement.api import VERSION
from openprocurement.api.models import TenderDocument, Bid, Award, Document, Revision, Question, Complaint, get_now
from schematics.exceptions import ModelValidationError, ModelConversionError
from urllib import quote
from uuid import uuid4
from base64 import b64encode


spore = Service(name='spore', path='/spore', renderer='json')
auction = Service(name='Tender Auction', path='/tenders/{tender_id}/auction', renderer='json')


def validate_data(request, model, partial=False):
    try:
        json = request.json_body
    except ValueError, e:
        request.errors.add('body', 'data', e.message)
        request.errors.status = 422
        return
    if not isinstance(json, dict) or 'data' not in json or not isinstance(json.get('data'), dict):
        request.errors.add('body', 'data', "Data not available")
        request.errors.status = 422
        return
    data = json['data']
    try:
        model(data).validate(partial=partial)
    except (ModelValidationError, ModelConversionError), e:
        for i in e.message:
            request.errors.add('body', i, e.message[i])
        request.errors.status = 422
    request.validated['data'] = data
    return data


def validate_tender_data(request):
    return validate_data(request, TenderDocument)


def validate_patch_tender_data(request):
    return validate_data(request, TenderDocument, True)


def validate_tender_auction_data(request):
    data = validate_patch_tender_data(request)
    tender = validate_tender_exists_by_tender_id(request)
    if data is None or not tender:
        return
    if tender.status != 'auction':
        request.errors.add('body', 'data', 'Can\'t report auction results in current tender status')
        request.errors.status = 403
        return
    bids = data.get('bids', [])
    tender_bids_ids = [i.id for i in tender.bids]
    if len(bids) != len(tender.bids):
        request.errors.add('body', 'bids', "Number of auction results did not match the number of tender bids")
        request.errors.status = 422
    elif not all(['id' in i for i in bids]):
        request.errors.add('body', 'bids', "Results of auction bids should contains id of bid")
        request.errors.status = 422
    elif set([i['id'] for i in bids]) != set(tender_bids_ids):
        request.errors.add('body', 'bids', "Auction bids should be identical to the tender bids")
        request.errors.status = 422


def validate_bid_data(request):
    return validate_data(request, Bid)


def validate_patch_bid_data(request):
    return validate_data(request, Bid, True)


def validate_award_data(request):
    return validate_data(request, Award)


def validate_document_data(request):
    return validate_data(request, Document)


def validate_patch_document_data(request):
    return validate_data(request, Document, True)


def validate_question_data(request):
    return validate_data(request, Question)


def validate_patch_question_data(request):
    return validate_data(request, Question, True)


def validate_complaint_data(request):
    return validate_data(request, Complaint)


def validate_patch_complaint_data(request):
    return validate_data(request, Complaint, True)


def validate_tender_exists(request, key='id'):
    tender = request.matchdict.get(key) and TenderDocument.load(request.registry.db, request.matchdict[key])
    if tender:
        request.validated[key] = request.matchdict[key]
        request.validated['tender'] = tender
        return tender
    else:
        request.errors.add('url', key, 'Not Found')
        request.errors.status = 404


def validate_tender_exists_by_tender_id(request):
    return validate_tender_exists(request, 'tender_id')


def validate_tender_document_exists(request):
    tender = validate_tender_exists(request, 'tender_id')
    if tender:
        documents = [i for i in tender.documents if i.id == request.matchdict['id']]
        if not documents:
            request.errors.add('url', 'id', 'Not Found')
            request.errors.status = 404
        else:
            request.validated['id'] = request.matchdict['id']
            request.validated['documents'] = documents
            request.validated['document'] = documents[-1]


def validate_tender_bid_exists(request, key='id'):
    tender = validate_tender_exists(request, 'tender_id')
    if tender:
        bids = [i for i in tender.bids if i.id == request.matchdict[key]]
        if bids:
            request.validated[key] = request.matchdict[key]
            request.validated['bids'] = bids
            bid = bids[0]
            request.validated['bid'] = bid
            return bid
        else:
            request.errors.add('url', key, 'Not Found')
            request.errors.status = 404


def validate_tender_bid_exists_by_bid_id(request):
    return validate_tender_bid_exists(request, 'bid_id')


def validate_tender_bid_document_exists(request):
    bid = validate_tender_bid_exists(request, 'bid_id')
    if bid:
        documents = [i for i in bid.documents if i.id == request.matchdict['id']]
        if not documents:
            request.errors.add('url', 'id', 'Not Found')
            request.errors.status = 404
        else:
            request.validated['id'] = request.matchdict['id']
            request.validated['documents'] = documents
            request.validated['document'] = documents[-1]


def validate_tender_question_exists(request, key='id'):
    tender = validate_tender_exists(request, 'tender_id')
    if tender:
        questions = [i for i in tender.questions if i.id == request.matchdict[key]]
        if questions:
            request.validated[key] = request.matchdict[key]
            request.validated['questions'] = questions
            question = questions[0]
            request.validated['question'] = question
            return question
        else:
            request.errors.add('url', key, 'Not Found')
            request.errors.status = 404


def validate_tender_complaint_exists(request, key='id'):
    tender = validate_tender_exists(request, 'tender_id')
    if tender:
        complaints = [i for i in tender.complaints if i.id == request.matchdict[key]]
        if complaints:
            request.validated[key] = request.matchdict[key]
            request.validated['complaints'] = complaints
            complaint = complaints[0]
            request.validated['complaint'] = complaint
            return complaint
        else:
            request.errors.add('url', key, 'Not Found')
            request.errors.status = 404


def validate_file_upload(request):
    if 'file' not in request.POST:
        request.errors.add('body', 'file', 'Not Found')
        request.errors.status = 404
    else:
        request.validated['file'] = request.POST['file']


def validate_file_update(request):
    if request.content_type == 'multipart/form-data':
        validate_file_upload(request)


def generate_tender_id(tid):
    return "UA-" + tid


def filter_data(data, fields=['id', 'doc_id', 'date', 'dateModified', 'url']):
    result = data.copy()
    for i in fields:
        if i in result:
            del result[i]
    return result


def upload_file(tender, document, key, in_file, request):
    conn = getattr(request.registry, 's3_connection', None)
    if conn:
        bucket = conn.get_bucket(request.registry.bucket_name)
        filename = "{}/{}/{}".format(tender.id, document.id, key)
        key = bucket.new_key(filename)
        key.set_metadata('Content-Type', document.format)
        key.set_metadata("Content-Disposition", "attachment; filename*=UTF-8''%s" % quote(document.title))
        key.set_contents_from_file(in_file)
        key.set_acl('private')
    else:
        filename = "{}_{}".format(document.id, key)
        tender['_attachments'][filename] = {
            "content_type": document.format,
            "data": b64encode(in_file.read())
        }


def get_file(tender, document, key, db, request):
    conn = getattr(request.registry, 's3_connection', None)
    if conn:
        filename = "{}/{}/{}".format(tender.id, document.id, key)
        url = conn.generate_url(method='GET', bucket=request.registry.bucket_name, key=filename, expires_in=300)
        request.response.content_type = document.format.encode('utf-8')
        request.response.content_disposition = 'attachment; filename={}'.format(quote(document.title.encode('utf-8')))
        request.response.status = '302 Moved Temporarily'
        request.response.location = url
        return url
    else:
        filename = "{}_{}".format(document.id, key)
        data = db.get_attachment(tender.id, filename)
        if data:
            request.response.content_type = document.format.encode('utf-8')
            request.response.content_disposition = 'attachment; filename={}'.format(quote(document.title.encode('utf-8')))
            request.response.body_file = data
            return request.response
        request.errors.add('url', 'download', 'Not Found')
        request.errors.status = 404


def apply_data_patch(item, changes):
    patch_changes = []
    for i, j in changes.items():
        if i in item:
            for x in make_patch(item[i], j).patch:
                if x['op'] == u'remove':
                    continue
                x['path'] = '/{}{}'.format(i, x['path'])
                patch_changes.append(x)
        else:
            patch_changes.append({'op': 'add', 'path': '/{}'.format(i), 'value': j})
    return apply_patch(item, patch_changes)


def tender_serialize(tender, fields):
    if fields:
        fields = fields.split(',') + ["dateModified", "id"]
        return dict([(i, j) for i, j in tender.serialize(tender.status).items() if i in fields])
    return tender.serialize("listing")


@spore.get()
def get_spore(request):
    services = get_services()
    return generate_spore_description(services, 'Service name', request.application_url, VERSION)


@resource(name='Tender',
          collection_path='/tenders',
          path='/tenders/{id}',
          description="Open Contracting compatible data exchange format. See http://ocds.open-contracting.org/standard/r/master/#tender for more info")
class TenderResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @view(renderer='json')
    def collection_get(self):
        """Tenders List

        Get Tenders List
        ----------------

        Example request to get tenders list:

        .. sourcecode:: http

            GET /tenders HTTP/1.1
            Host: example.com
            Accept: application/json

        This is what one should expect in response:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "data": [
                    {
                        "id": "64e93250be76435397e8c992ed4214d1",
                        "dateModified": "2014-10-27T08:06:58.158Z"
                    }
                ]
            }

        """
        # http://wiki.apache.org/couchdb/HTTP_view_API#Querying_Options
        params = {}
        fields = self.request.params.get('opt_fields', '')
        if fields:
            params['opt_fields'] = fields
        limit = self.request.params.get('limit', '')
        if limit:
            params['limit'] = limit
        limit = int(limit) if limit.isdigit() else 100
        descending = self.request.params.get('descending')
        offset = self.request.params.get('offset', '9' if descending else '0')
        if descending:
            params['descending'] = descending
        next_offset = datetime.min.isoformat() if descending else get_now().isoformat()
        results = TenderDocument.view(self.db, 'tenders/by_dateModified', limit=limit + 1, startkey=offset, descending=bool(descending))
        results = [tender_serialize(i, fields) for i in results]
        if len(results) > limit:
            results, last = results[:-1], results[-1]
            params['offset'] = last['dateModified']
        else:
            params['offset'] = next_offset
        next_url = self.request.route_url('collection_Tender', _query=params)
        next_path = self.request.route_path('collection_Tender', _query=params)
        return {
            'data': results,
            'next_page': {
                "offset": params['offset'],
                "path": next_path,
                "uri": next_url
            }
        }

    @view(content_type="application/json", validators=(validate_tender_data,), renderer='json')
    def collection_post(self):
        """This API request is targeted to creating new Tenders by procuring organizations.

        Creating new Tender
        -------------------

        Example request to create tender:

        .. sourcecode:: http

            POST /tenders HTTP/1.1
            Host: example.com
            Accept: application/json

            {
                "data": {
                    "procuringEntity": {
                        "id": {
                            "name": "Державне управління справами",
                            "scheme": "https://ns.openprocurement.org/ua/edrpou",
                            "uid": "00037256",
                            "uri": "http://www.dus.gov.ua/"
                        },
                        "address": {
                            "countryName": "Україна",
                            "postalCode": "01220",
                            "region": "м. Київ",
                            "locality": "м. Київ",
                            "streetAddress": "вул. Банкова, 11, корпус 1"
                        }
                    },
                    "value": {
                        "amount": 500,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": true
                    },
                    "itemsToBeProcured": [
                        {
                            "description": "футляри до державних нагород",
                            "primaryClassification": {
                                "scheme": "CPV",
                                "id": "44617100-9",
                                "description": "Cartons"
                            },
                            "additionalClassification": [
                                {
                                    "scheme": "ДКПП",
                                    "id": "17.21.1",
                                    "description": "папір і картон гофровані, паперова й картонна тара"
                                }
                            ],
                            "unitOfMeasure": "item",
                            "quantity": 5
                        }
                    ],
                    "enquiryPeriod": {
                        "endDate": "2014-10-31T00:00:00"
                    },
                    "tenderPeriod": {
                        "startDate": "2014-11-03T00:00:00",
                        "endDate": "2014-11-06T10:00:00"
                    },
                    "awardPeriod": {
                        "endDate": "2014-11-13T00:00:00"
                    },
                    "deliveryDate": {
                        "endDate": "2014-11-20T00:00:00"
                    },
                    "minimalStep": {
                        "amount": 35,
                        "currency": "UAH"
                    }
                }
            }

        This is what one should expect in response:

        .. sourcecode:: http

            HTTP/1.1 201 Created
            Location: http://localhost/api/0.1/tenders/64e93250be76435397e8c992ed4214d1
            Content-Type: application/json

            {
                "data": {
                    "id": "64e93250be76435397e8c992ed4214d1",
                    "tenderID": "UA-64e93250be76435397e8c992ed4214d1",
                    "dateModified": "2014-10-27T08:06:58.158Z",
                    "procuringEntity": {
                        "id": {
                            "name": "Державне управління справами",
                            "scheme": "https://ns.openprocurement.org/ua/edrpou",
                            "uid": "00037256",
                            "uri": "http://www.dus.gov.ua/"
                        },
                        "address": {
                            "countryName": "Україна",
                            "postalCode": "01220",
                            "region": "м. Київ",
                            "locality": "м. Київ",
                            "streetAddress": "вул. Банкова, 11, корпус 1"
                        }
                    },
                    "value": {
                        "amount": 500,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": true
                    },
                    "itemsToBeProcured": [
                        {
                            "description": "футляри до державних нагород",
                            "primaryClassification": {
                                "scheme": "CPV",
                                "id": "44617100-9",
                                "description": "Cartons"
                            },
                            "additionalClassification": [
                                {
                                    "scheme": "ДКПП",
                                    "id": "17.21.1",
                                    "description": "папір і картон гофровані, паперова й картонна тара"
                                }
                            ],
                            "unitOfMeasure": "item",
                            "quantity": 5
                        }
                    ],
                    "enquiryPeriod": {
                        "endDate": "2014-10-31T00:00:00"
                    },
                    "tenderPeriod": {
                        "startDate": "2014-11-03T00:00:00",
                        "endDate": "2014-11-06T10:00:00"
                    },
                    "awardPeriod": {
                        "endDate": "2014-11-13T00:00:00"
                    },
                    "deliveryDate": {
                        "endDate": "2014-11-20T00:00:00"
                    },
                    "minimalStep": {
                        "amount": 35,
                        "currency": "UAH"
                    }
                }
            }

        """
        tender_data = filter_data(self.request.validated['data'])
        tender_id = uuid4().hex
        tender_data['doc_id'] = tender_id
        tender_data['tenderID'] = generate_tender_id(tender_id)
        tender = TenderDocument(tender_data)
        if tender.enquiryPeriod:
            tender.enquiryPeriod.startDate = tender.dateModified
        else:
            tender.enquiryPeriod = {'startDate': tender.dateModified}
        try:
            tender.store(self.db)
        except Exception, e:
            return self.request.errors.add('body', 'data', str(e))
        self.request.response.status = 201
        self.request.response.headers[
            'Location'] = self.request.route_url('Tender', id=tender_id)
        return {'data': tender.serialize(tender.status)}

    @view(renderer='json', validators=(validate_tender_exists,))
    def get(self):
        """Tender Read

        Get Tender
        ----------

        Example request to get tender:

        .. sourcecode:: http

            GET /tenders/64e93250be76435397e8c992ed4214d1 HTTP/1.1
            Host: example.com
            Accept: application/json

        This is what one should expect in response:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "data": {
                    "id": "64e93250be76435397e8c992ed4214d1",
                    "tenderID": "UA-64e93250be76435397e8c992ed4214d1",
                    "dateModified": "2014-10-27T08:06:58.158Z",
                    "procuringEntity": {
                        "id": {
                            "name": "Державне управління справами",
                            "scheme": "https://ns.openprocurement.org/ua/edrpou",
                            "uid": "00037256",
                            "uri": "http://www.dus.gov.ua/"
                        },
                        "address": {
                            "countryName": "Україна",
                            "postalCode": "01220",
                            "region": "м. Київ",
                            "locality": "м. Київ",
                            "streetAddress": "вул. Банкова, 11, корпус 1"
                        }
                    },
                    "value": {
                        "amount": 500,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": true
                    },
                    "itemsToBeProcured": [
                        {
                            "description": "футляри до державних нагород",
                            "primaryClassification": {
                                "scheme": "CPV",
                                "id": "44617100-9",
                                "description": "Cartons"
                            },
                            "additionalClassification": [
                                {
                                    "scheme": "ДКПП",
                                    "id": "17.21.1",
                                    "description": "папір і картон гофровані, паперова й картонна тара"
                                }
                            ],
                            "unitOfMeasure": "item",
                            "quantity": 5
                        }
                    ],
                    "enquiryPeriod": {
                        "endDate": "2014-10-31T00:00:00"
                    },
                    "tenderPeriod": {
                        "startDate": "2014-11-03T00:00:00",
                        "endDate": "2014-11-06T10:00:00"
                    },
                    "awardPeriod": {
                        "endDate": "2014-11-13T00:00:00"
                    },
                    "deliveryDate": {
                        "endDate": "2014-11-20T00:00:00"
                    },
                    "minimalStep": {
                        "amount": 35,
                        "currency": "UAH"
                    }
                }
            }

        """
        tender = self.request.validated['tender']
        tender_data = tender.serialize(tender.status)
        if tender.status in ['auction', 'qualification', 'awarded', 'contract-signed']:
            # auction url
            tender_data['auctionUrl'] = 'http://auction-sandbox.openprocurement.org/tenders/{}'.format(tender.id)
        return {'data': tender_data}

    @view(content_type="application/json", validators=(validate_tender_data, validate_tender_exists), renderer='json')
    def put(self):
        """Tender Edit (full)"""
        tender = self.request.validated['tender']
        src = tender.serialize("plain")
        tender_data = filter_data(self.request.validated['data'])
        tender.import_data(tender_data)
        patch = make_patch(tender.serialize("plain"), src).patch
        if patch:
            tender.revisions.append(Revision({'changes': patch}))
            try:
                tender.store(self.db)
            except Exception, e:
                return self.request.errors.add('body', 'data', str(e))
        return {'data': tender.serialize(tender.status)}

    @view(content_type="application/json", validators=(validate_patch_tender_data, validate_tender_exists), renderer='json')
    def patch(self):
        """Tender Edit (partial)

        For example here is how procuring entity can change number of items to be procured and total Value of a tender:

        .. sourcecode:: http

            PATCH /tenders/4879d3f8ee2443169b5fbbc9f89fa607 HTTP/1.1
            Host: example.com
            Accept: application/json

            {
                "data": {
                    "value": {
                        "amount": 600
                    },
                    "itemsToBeProcured": [
                        {
                            "quantity": 6
                        }
                    ]
                }
            }

        And here is the response to be expected:

        .. sourcecode:: http

            HTTP/1.0 200 OK
            Content-Type: application/json

            {
                "data": {
                    "id": "4879d3f8ee2443169b5fbbc9f89fa607",
                    "tenderID": "UA-64e93250be76435397e8c992ed4214d1",
                    "dateModified": "2014-10-27T08:12:34.956Z",
                    "value": {
                        "amount": 600
                    },
                    "itemsToBeProcured": [
                        {
                            "quantity": 6
                        }
                    ]
                }
            }

        """
        tender = self.request.validated['tender']
        src = tender.serialize("plain")
        tender_data = filter_data(self.request.validated['data'])
        if tender_data:
            tender.import_data(apply_data_patch(src, tender_data))
            patch = make_patch(tender.serialize("plain"), src).patch
            if patch:
                tender.revisions.append(Revision({'changes': patch}))
                try:
                    tender.store(self.db)
                except Exception, e:
                    return self.request.errors.add('body', 'data', str(e))
        return {'data': tender.serialize(tender.status)}


@resource(name='Tender Documents',
          collection_path='/tenders/{tender_id}/documents',
          path='/tenders/{tender_id}/documents/{id}',
          description="Tender related binary files (PDFs, etc.)")
class TenderDocumentResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @view(renderer='json', validators=(validate_tender_exists_by_tender_id,))
    def collection_get(self):
        """Tender Documents List"""
        tender = self.request.validated['tender']
        if self.request.params.get('all', ''):
            collection_data = [i.serialize("view") for i in tender['documents']]
        else:
            collection_data = sorted(dict([
                (i.id, i.serialize("view"))
                for i in tender['documents']
            ]).values(), key=lambda i: i['dateModified'])
        return {'data': collection_data}

    @view(renderer='json', validators=(validate_file_upload, validate_tender_exists_by_tender_id,))
    def collection_post(self):
        """Tender Document Upload"""
        tender = self.request.validated['tender']
        if tender.status != 'enquiries':
            self.request.errors.add('body', 'data', 'Can\'t add document in current tender status')
            self.request.errors.status = 403
            return
        src = tender.serialize("plain")
        data = self.request.validated['file']
        document = Document()
        document.id = uuid4().hex
        document.title = data.filename
        document.format = data.type
        key = uuid4().hex
        document.url = self.request.route_url('Tender Documents', tender_id=tender.id, id=document.id, _query={'download': key})
        tender.documents.append(document)
        upload_file(tender, document, key, data.file, self.request)
        patch = make_patch(tender.serialize("plain"), src).patch
        tender.revisions.append(Revision({'changes': patch}))
        try:
            tender.store(self.db)
        except Exception, e:
            return self.request.errors.add('body', 'data', str(e))
        self.request.response.status = 201
        self.request.response.headers['Location'] = self.request.route_url('Tender Documents', tender_id=tender.id, id=document.id)
        return {'data': document.serialize("view")}

    @view(validators=(validate_tender_document_exists,))
    def get(self):
        """Tender Document Read"""
        document = self.request.validated['document']
        key = self.request.params.get('download')
        if key:
            return get_file(self.request.validated['tender'], document, key, self.db, self.request)
        document_data = document.serialize("view")
        document_data['previousVersions'] = [
            i.serialize("view")
            for i in self.request.validated['documents']
            if i.url != document.url
        ]
        return {'data': document_data}

    @view(renderer='json', validators=(validate_file_update, validate_tender_document_exists,))
    def put(self):
        """Tender Document Update"""
        tender = self.request.validated['tender']
        first_document = self.request.validated['documents'][0]
        if tender.status != 'enquiries':
            self.request.errors.add('body', 'data', 'Can\'t update document in current tender status')
            self.request.errors.status = 403
            return
        if self.request.content_type == 'multipart/form-data':
            data = self.request.validated['file']
            filename = data.filename
            content_type = data.type
            in_file = data.file
        else:
            filename = first_document.title
            content_type = self.request.content_type
            in_file = self.request.body_file
        document = Document()
        document.id = self.request.validated['id']
        document.title = filename
        document.format = content_type
        document.datePublished = first_document.datePublished
        key = uuid4().hex
        document.url = self.request.route_url('Tender Documents', tender_id=tender.id, id=document.id, _query={'download': key})
        src = tender.serialize("plain")
        tender.documents.append(document)
        upload_file(tender, document, key, in_file, self.request)
        patch = make_patch(tender.serialize("plain"), src).patch
        tender.revisions.append(Revision({'changes': patch}))
        try:
            tender.store(self.db)
        except Exception, e:
            return self.request.errors.add('body', 'data', str(e))
        return {'data': document.serialize("view")}

    @view(renderer='json', validators=(validate_patch_document_data, validate_tender_document_exists,))
    def patch(self):
        """Tender Document Update"""
        tender = self.request.validated['tender']
        document = self.request.validated['document']
        if tender.status != 'enquiries':
            self.request.errors.add('body', 'data', 'Can\'t update document in current tender status')
            self.request.errors.status = 403
            return
        document_data = filter_data(self.request.validated['data'])
        if document_data:
            src = tender.serialize("plain")
            document.import_data(document_data)
            patch = make_patch(tender.serialize("plain"), src).patch
            if patch:
                tender.revisions.append(Revision({'changes': patch}))
                try:
                    tender.store(self.db)
                except Exception, e:
                    return self.request.errors.add('body', 'data', str(e))
        return {'data': document.serialize("view")}


@resource(name='Tender Bids',
          collection_path='/tenders/{tender_id}/bids',
          path='/tenders/{tender_id}/bids/{id}',
          description="Tender bids")
class TenderBidderResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @view(content_type="application/json", validators=(validate_bid_data, validate_tender_exists_by_tender_id), renderer='json')
    def collection_post(self):
        """Registration of new bid proposal

        Creating new Bid proposal
        -------------------------

        Example request to create bid proposal:

        .. sourcecode:: http

            POST /tenders/4879d3f8ee2443169b5fbbc9f89fa607/bids HTTP/1.1
            Host: example.com
            Accept: application/json

            {
                "data": {
                    "tenderers": [
                        {
                            "id": {
                                "name": "Державне управління справами",
                                "scheme": "https://ns.openprocurement.org/ua/edrpou",
                                "uid": "00037256",
                                "uri": "http://www.dus.gov.ua/"
                            },
                            "address": {
                                "countryName": "Україна",
                                "postalCode": "01220",
                                "region": "м. Київ",
                                "locality": "м. Київ",
                                "streetAddress": "вул. Банкова, 11, корпус 1"
                            }
                        }
                    ],
                    "value": {
                        "amount": 489,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": true
                    }
                }
            }

        This is what one should expect in response:

        .. sourcecode:: http

            HTTP/1.1 201 Created
            Content-Type: application/json

            {
                "data": {
                    "id": "4879d3f8ee2443169b5fbbc9f89fa607",
                    "status": "registration",
                    "date": "2014-10-28T11:44:17.947Z",
                    "tenderers": [
                        {
                            "id": {
                                "name": "Державне управління справами",
                                "scheme": "https://ns.openprocurement.org/ua/edrpou",
                                "uid": "00037256",
                                "uri": "http://www.dus.gov.ua/"
                            },
                            "address": {
                                "countryName": "Україна",
                                "postalCode": "01220",
                                "region": "м. Київ",
                                "locality": "м. Київ",
                                "streetAddress": "вул. Банкова, 11, корпус 1"
                            }
                        }
                    ],
                    "value": {
                        "amount": 489,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": true
                    }
                }
            }

        """
        # See https://github.com/open-contracting/standard/issues/78#issuecomment-59830415
        # for more info upon schema
        tender = self.request.validated['tender']
        if tender.status != 'tendering':
            self.request.errors.add('body', 'data', 'Can\'t add bid in current tender status')
            self.request.errors.status = 403
            return
        bid_data = filter_data(self.request.validated['data'])
        bid = Bid(bid_data)
        src = tender.serialize("plain")
        tender.bids.append(bid)
        patch = make_patch(tender.serialize("plain"), src).patch
        tender.revisions.append(Revision({'changes': patch}))
        try:
            tender.store(self.db)
        except Exception, e:
            return self.request.errors.add('body', 'data', str(e))
        self.request.response.status = 201
        self.request.response.headers['Location'] = self.request.route_url('Tender Bids', tender_id=tender.id, id=bid['id'])
        return {'data': bid.serialize("view")}

    @view(renderer='json', validators=(validate_tender_exists_by_tender_id,))
    def collection_get(self):
        """Bids Listing

        Get Bids List
        -------------

        Example request to get bids list:

        .. sourcecode:: http

            GET /tenders/4879d3f8ee2443169b5fbbc9f89fa607/bids HTTP/1.1
            Host: example.com
            Accept: application/json

        This is what one should expect in response:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "data": [
                    {
                        "value": {
                            "amount": 489,
                            "currency": "UAH",
                            "valueAddedTaxIncluded": true
                        }
                    }
                ]
            }

        """
        tender = self.request.validated['tender']
        if tender.status in ['enquiries', 'tendering']:
            return {'data': []}
        return {'data': [i.serialize(tender.status) for i in tender.bids]}

    @view(renderer='json', validators=(validate_tender_bid_exists,))
    def get(self):
        """Retrieving the proposal

        Example request for retrieving the proposal:

        .. sourcecode:: http

            GET /tenders/4879d3f8ee2443169b5fbbc9f89fa607/bids/71b6c23ed8944d688e92a31ec8c3f61a HTTP/1.1
            Host: example.com
            Accept: application/json

        And here is the response to be expected:

        .. sourcecode:: http

            HTTP/1.0 200 OK
            Content-Type: application/json

            {
                "data": {
                    "value": {
                        "amount": 600,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": true
                    }
                }
            }

        """
        tender = self.request.validated['tender']
        if tender.status in ['enquiries', 'tendering']:
            return {'data': {}}
        bid_data = self.request.validated['bid'].serialize(tender.status)
        if tender.status in ['auction', 'qualification', 'awarded', 'contract-signed']:
            # auction participation url
            bid_data['participationUrl'] = 'http://auction-sandbox.openprocurement.org/tenders/{}?bidder_id={}'.format(tender.id, self.request.validated['id'])
        return {'data': bid_data}

    @view(content_type="application/json", validators=(validate_patch_bid_data, validate_tender_bid_exists), renderer='json')
    def patch(self):
        """Update of proposal

        Example request to change bid proposal:

        .. sourcecode:: http

            PATCH /tenders/4879d3f8ee2443169b5fbbc9f89fa607/bids/71b6c23ed8944d688e92a31ec8c3f61a HTTP/1.1
            Host: example.com
            Accept: application/json

            {
                "data": {
                    "value": {
                        "amount": 600
                    }
                }
            }

        And here is the response to be expected:

        .. sourcecode:: http

            HTTP/1.0 200 OK
            Content-Type: application/json

            {
                "data": {
                    "value": {
                        "amount": 600,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": true
                    }
                }
            }

        """
        tender = self.request.validated['tender']
        if tender.status != 'tendering':
            self.request.errors.add('body', 'data', 'Can\'t change bid in current tender status')
            self.request.errors.status = 403
            return
        bid = self.request.validated['bid']
        bid_data = filter_data(self.request.validated['data'])
        if bid_data:
            src = tender.serialize("plain")
            bid.import_data(apply_data_patch(bid.serialize(), bid_data))
            patch = make_patch(tender.serialize("plain"), src).patch
            if patch:
                tender.revisions.append(Revision({'changes': patch}))
                try:
                    tender.store(self.db)
                except Exception, e:
                    return self.request.errors.add('body', 'data', str(e))
        return {'data': bid.serialize("view")}

    @view(renderer='json', validators=(validate_tender_bid_exists,))
    def delete(self):
        """Cancelling the proposal

        Example request for cancelling the proposal:

        .. sourcecode:: http

            DELETE /tenders/4879d3f8ee2443169b5fbbc9f89fa607/bids/71b6c23ed8944d688e92a31ec8c3f61a HTTP/1.1
            Host: example.com
            Accept: application/json

        And here is the response to be expected:

        .. sourcecode:: http

            HTTP/1.0 200 OK
            Content-Type: application/json

            {
                "data": {
                    "value": {
                        "amount": 489,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": true
                    }
                }
            }

        """
        tender = self.request.validated['tender']
        bid = self.request.validated['bid']
        if tender.status != 'tendering':
            self.request.errors.add('body', 'data', 'Can\'t delete bid in current tender status')
            self.request.errors.status = 403
            return
        src = tender.serialize("plain")
        res = bid.serialize("view")
        tender.bids.remove(bid)
        patch = make_patch(tender.serialize("plain"), src).patch
        if patch:
            tender.revisions.append(Revision({'changes': patch}))
            try:
                tender.store(self.db)
            except Exception, e:
                return self.request.errors.add('body', 'data', str(e))
        return {'data': res}


@resource(name='Tender Bid Documents',
          collection_path='/tenders/{tender_id}/bids/{bid_id}/documents',
          path='/tenders/{tender_id}/bids/{bid_id}/documents/{id}',
          description="Tender bidder documents")
class TenderBidderDocumentResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @view(renderer='json', validators=(validate_tender_bid_exists_by_bid_id,))
    def collection_get(self):
        """Tender Bid Documents List"""
        bid = self.request.validated['bid']
        if self.request.params.get('all', ''):
            collection_data = [i.serialize("view") for i in bid['documents']]
        else:
            collection_data = sorted(dict([
                (i.id, i.serialize("view"))
                for i in bid['documents']
            ]).values(), key=lambda i: i['dateModified'])
        return {'data': collection_data}

    @view(renderer='json', validators=(validate_file_upload, validate_tender_bid_exists_by_bid_id,))
    def collection_post(self):
        """Tender Bid Document Upload
        """
        tender = self.request.validated['tender']
        if tender.status not in ['tendering', 'auction', 'qualification']:
            self.request.errors.add('body', 'data', 'Can\'t add document in current tender status')
            self.request.errors.status = 403
            return
        src = tender.serialize("plain")
        data = self.request.validated['file']
        document = Document()
        document.id = uuid4().hex
        document.title = data.filename
        document.format = data.type
        key = uuid4().hex
        document.url = self.request.route_url('Tender Bid Documents', tender_id=tender.id, bid_id=self.request.validated['bid_id'], id=document.id, _query={'download': key})
        self.request.validated['bid'].documents.append(document)
        upload_file(tender, document, key, data.file, self.request)
        patch = make_patch(tender.serialize("plain"), src).patch
        tender.revisions.append(Revision({'changes': patch}))
        try:
            tender.store(self.db)
        except Exception, e:
            return self.request.errors.add('body', 'data', str(e))
        self.request.response.status = 201
        self.request.response.headers['Location'] = self.request.route_url('Tender Bid Documents', tender_id=tender.id, bid_id=self.request.validated['bid_id'], id=document.id)
        return {'data': document.serialize("view")}

    @view(renderer='json', validators=(validate_tender_bid_document_exists,))
    def get(self):
        """Tender Bid Document Read"""
        document = self.request.validated['document']
        key = self.request.params.get('download')
        if key:
            return get_file(self.request.validated['tender'], document, key, self.db, self.request)
        document_data = document.serialize("view")
        document_data['previousVersions'] = [
            i.serialize("view")
            for i in self.request.validated['documents']
            if i.url != document.url
        ]
        return {'data': document_data}

    @view(renderer='json', validators=(validate_file_update, validate_tender_bid_document_exists,))
    def put(self):
        """Tender Bid Document Update"""
        tender = self.request.validated['tender']
        first_document = self.request.validated['documents'][0]
        if tender.status not in ['tendering', 'auction', 'qualification']:
            self.request.errors.add('body', 'data', 'Can\'t update document in current tender status')
            self.request.errors.status = 403
            return
        src = tender.serialize("plain")
        if self.request.content_type == 'multipart/form-data':
            data = self.request.validated['file']
            filename = data.filename
            content_type = data.type
            in_file = data.file
        else:
            filename = first_document.title
            content_type = self.request.content_type
            in_file = self.request.body_file
        document = Document()
        document.id = self.request.matchdict['id']
        document.title = filename
        document.format = content_type
        document.datePublished = first_document.datePublished
        key = uuid4().hex
        document.url = self.request.route_url('Tender Bid Documents', tender_id=tender.id, bid_id=self.request.validated['bid_id'], id=document.id, _query={'download': key})
        self.request.validated['bid'].documents.append(document)
        upload_file(tender, document, key, in_file, self.request)
        patch = make_patch(tender.serialize("plain"), src).patch
        tender.revisions.append(Revision({'changes': patch}))
        try:
            tender.store(self.db)
        except Exception, e:
            return self.request.errors.add('body', 'data', str(e))
        return {'data': document.serialize("view")}

    @view(renderer='json', validators=(validate_patch_document_data, validate_tender_bid_document_exists,))
    def patch(self):
        """Tender Bid Document Update"""
        tender = self.request.validated['tender']
        if tender.status not in ['tendering', 'auction', 'qualification']:
            self.request.errors.add('body', 'data', 'Can\'t update document in current tender status')
            self.request.errors.status = 403
            return
        document = self.request.validated['document']
        document_data = filter_data(self.request.validated['data'])
        if document_data:
            src = tender.serialize("plain")
            document.import_data(document_data)
            patch = make_patch(tender.serialize("plain"), src).patch
            if patch:
                tender.revisions.append(Revision({'changes': patch}))
                try:
                    tender.store(self.db)
                except Exception, e:
                    return self.request.errors.add('body', 'data', str(e))
        return {'data': document.serialize("view")}


@resource(name='Tender Awards',
          collection_path='/tenders/{tender_id}/awards',
          path='/tenders/{tender_id}/awards/{id}',
          description="Tender awards")
class TenderAwardResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @view(renderer='json', validators=(validate_tender_exists_by_tender_id,))
    def collection_get(self):
        """Tender Awards List

        Get Awards List
        ---------------

        Example request to get awards list:

        .. sourcecode:: http

            GET /tenders/4879d3f8ee2443169b5fbbc9f89fa607/awards HTTP/1.1
            Host: example.com
            Accept: application/json

        This is what one should expect in response:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "data": [
                    {
                        "awardStatus": "active",
                        "suppliers": [
                            {
                                "id": {
                                    "name": "Державне управління справами",
                                    "scheme": "https://ns.openprocurement.org/ua/edrpou",
                                    "uid": "00037256",
                                    "uri": "http://www.dus.gov.ua/"
                                },
                                "address": {
                                    "countryName": "Україна",
                                    "postalCode": "01220",
                                    "region": "м. Київ",
                                    "locality": "м. Київ",
                                    "streetAddress": "вул. Банкова, 11, корпус 1"
                                }
                            }
                        ],
                        "awardValue": {
                            "amount": 489,
                            "currency": "UAH",
                            "valueAddedTaxIncluded": true
                        }
                    }
                ]
            }

        """
        return {'data': [i.serialize("view") for i in self.request.validated['tender'].awards]}

    @view(content_type="application/json", validators=(validate_award_data, validate_tender_exists_by_tender_id), renderer='json')
    def collection_post(self):
        """Accept or reject bidder application

        Creating new Award
        ------------------

        Example request to create award:

        .. sourcecode:: http

            POST /tenders/4879d3f8ee2443169b5fbbc9f89fa607/awards HTTP/1.1
            Host: example.com
            Accept: application/json

            {
                "data": {
                    "awardStatus": "active",
                    "suppliers": [
                        {
                            "id": {
                                "name": "Державне управління справами",
                                "scheme": "https://ns.openprocurement.org/ua/edrpou",
                                "uid": "00037256",
                                "uri": "http://www.dus.gov.ua/"
                            },
                            "address": {
                                "countryName": "Україна",
                                "postalCode": "01220",
                                "region": "м. Київ",
                                "locality": "м. Київ",
                                "streetAddress": "вул. Банкова, 11, корпус 1"
                            }
                        }
                    ],
                    "awardValue": {
                        "amount": 489,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": true
                    }
                }
            }

        This is what one should expect in response:

        .. sourcecode:: http

            HTTP/1.1 201 Created
            Content-Type: application/json

            {
                "data": {
                    "awardID": "4879d3f8ee2443169b5fbbc9f89fa607",
                    "awardDate": "2014-10-28T11:44:17.947Z",
                    "awardStatus": "active",
                    "suppliers": [
                        {
                            "id": {
                                "name": "Державне управління справами",
                                "scheme": "https://ns.openprocurement.org/ua/edrpou",
                                "uid": "00037256",
                                "uri": "http://www.dus.gov.ua/"
                            },
                            "address": {
                                "countryName": "Україна",
                                "postalCode": "01220",
                                "region": "м. Київ",
                                "locality": "м. Київ",
                                "streetAddress": "вул. Банкова, 11, корпус 1"
                            }
                        }
                    ],
                    "awardValue": {
                        "amount": 489,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": true
                    }
                }
            }

        """
        tender = self.request.validated['tender']
        if tender.status != 'qualification':
            self.request.errors.add('body', 'data', 'Can\'t create award in current tender status')
            self.request.errors.status = 403
            return
        src = tender.serialize("plain")
        award_data = self.request.validated['data']
        award = Award(award_data)
        tender.awards.append(award)
        patch = make_patch(tender.serialize("plain"), src).patch
        tender.revisions.append(Revision({'changes': patch}))
        try:
            tender.store(self.db)
        except Exception, e:
            return self.request.errors.add('body', 'data', str(e))
        self.request.response.status = 201
        # self.request.response.headers['Location'] = self.request.route_url('Tender Bids', tender_id=tender.id, id=award['awardID'])
        return {'data': award.serialize("view")}


@auction.get(renderer='json', validators=(validate_tender_exists_by_tender_id,))
def get_auction(request):
    """Get auction info.

    Get tender auction info
    -----------------------

    Example request to get tender auction information:

    .. sourcecode:: http

        GET /tenders/4879d3f8ee2443169b5fbbc9f89fa607/auction HTTP/1.1
        Host: example.com
        Accept: application/json

    This is what one should expect in response:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "data": {
                "dateModified": "2014-10-27T08:06:58.158Z",
                "bids": [
                    {
                        "value": {
                            "amount": 500,
                            "currency": "UAH",
                            "valueAddedTaxIncluded": true
                        }
                    },
                    {
                        "value": {
                            "amount": 485,
                            "currency": "UAH",
                            "valueAddedTaxIncluded": true
                        }
                    }
                ],
                "minimalStep":{
                    "amount": 35,
                    "currency": "UAH"
                },
                "tenderPeriod":{
                    "startDate": "2014-11-04T08:00:00"
                }
            }
        }

    """
    tender = request.validated['tender']
    if tender.status != 'auction':
        request.errors.add('body', 'data', 'Can\'t get auction info in current tender status')
        request.errors.status = 403
        return
    auction_info = tender.serialize("auction_view")
    return {'data': auction_info}


@auction.patch(content_type="application/json", validators=(validate_tender_auction_data), renderer='json')
def patch_auction(request):
    """Report auction results.

    Report auction results
    ----------------------

    Example request to report auction results:

    .. sourcecode:: http

        PATCH /tenders/4879d3f8ee2443169b5fbbc9f89fa607/auction HTTP/1.1
        Host: example.com
        Accept: application/json

        {
            "data": {
                "dateModified": "2014-10-27T08:06:58.158Z",
                "bids": [
                    {
                        "value": {
                            "amount": 400,
                            "currency": "UAH"
                        }
                    },
                    {
                        "value": {
                            "amount": 385,
                            "currency": "UAH"
                        }
                    }
                ]
            }
        }

    This is what one should expect in response:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "data": {
                "dateModified": "2014-10-27T08:06:58.158Z",
                "bids": [
                    {
                        "value": {
                            "amount": 400,
                            "currency": "UAH",
                            "valueAddedTaxIncluded": true
                        }
                    },
                    {
                        "value": {
                            "amount": 385,
                            "currency": "UAH",
                            "valueAddedTaxIncluded": true
                        }
                    }
                ],
                "minimalStep":{
                    "amount": 35,
                    "currency": "UAH"
                },
                "tenderPeriod":{
                    "startDate": "2014-11-04T08:00:00"
                }
            }
        }

    """
    tender = request.validated['tender']
    auction_data = filter_data(request.validated['data'])
    if auction_data:
        auction_data['tenderID'] = tender.tenderID
        bids = auction_data.get('bids', [])
        tender_bids_ids = [i.id for i in tender.bids]
        auction_data['bids'] = [x for (y, x) in sorted(zip([tender_bids_ids.index(i['id']) for i in bids], bids))]
        src = tender.serialize("plain")
        tender.import_data(apply_data_patch(src, auction_data))
        patch = make_patch(tender.serialize("plain"), src).patch
        if patch:
            tender.revisions.append(Revision({'changes': patch}))
            try:
                tender.store(request.registry.db)
            except Exception, e:
                return request.errors.add('body', 'data', str(e))
    return {'data': tender.serialize("auction_view")}


@resource(name='Tender Questions',
          collection_path='/tenders/{tender_id}/questions',
          path='/tenders/{tender_id}/questions/{id}',
          description="Tender questions")
class TenderQuestionResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @view(content_type="application/json", validators=(validate_question_data, validate_tender_exists_by_tender_id), renderer='json')
    def collection_post(self):
        """Post a question
        """
        tender = self.request.validated['tender']
        question_data = filter_data(self.request.validated['data'])
        question = Question(question_data)
        src = tender.serialize("plain")
        tender.questions.append(question)
        patch = make_patch(tender.serialize("plain"), src).patch
        tender.revisions.append(Revision({'changes': patch}))
        try:
            tender.store(self.db)
        except Exception, e:
            return self.request.errors.add('body', 'data', str(e))
        self.request.response.status = 201
        self.request.response.headers['Location'] = self.request.route_url('Tender Bids', tender_id=tender.id, id=question['id'])
        return {'data': question.serialize("view")}

    @view(renderer='json', validators=(validate_tender_exists_by_tender_id,))
    def collection_get(self):
        """List questions
        """
        return {'data': [i.serialize("view") for i in self.request.validated['tender'].questions]}

    @view(renderer='json', validators=(validate_tender_question_exists,))
    def get(self):
        """Retrieving the question
        """
        return {'data': self.request.validated['question'].serialize("view")}

    @view(content_type="application/json", validators=(validate_patch_question_data, validate_tender_question_exists), renderer='json')
    def patch(self):
        """Post an Answer
        """
        tender = self.request.validated['tender']
        question = self.request.validated['question']
        question_data = filter_data(self.request.validated['data'])
        if question_data:
            src = tender.serialize("plain")
            question.import_data(apply_data_patch(question.serialize(), question_data))
            patch = make_patch(tender.serialize("plain"), src).patch
            if patch:
                tender.revisions.append(Revision({'changes': patch}))
                try:
                    tender.store(self.db)
                except Exception, e:
                    return self.request.errors.add('body', 'data', str(e))
        return {'data': question.serialize("view")}


@resource(name='Tender Complaints',
          collection_path='/tenders/{tender_id}/complaints',
          path='/tenders/{tender_id}/complaints/{id}',
          description="Tender complaints")
class TenderComplaintResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @view(content_type="application/json", validators=(validate_complaint_data, validate_tender_exists_by_tender_id), renderer='json')
    def collection_post(self):
        """Post a complaint
        """
        tender = self.request.validated['tender']
        complaint_data = filter_data(self.request.validated['data'])
        complaint = Complaint(complaint_data)
        src = tender.serialize("plain")
        tender.complaints.append(complaint)
        patch = make_patch(tender.serialize("plain"), src).patch
        tender.revisions.append(Revision({'changes': patch}))
        try:
            tender.store(self.db)
        except Exception, e:
            return self.request.errors.add('body', 'data', str(e))
        self.request.response.status = 201
        self.request.response.headers['Location'] = self.request.route_url('Tender Bids', tender_id=tender.id, id=complaint['id'])
        return {'data': complaint.serialize("view")}

    @view(renderer='json', validators=(validate_tender_exists_by_tender_id,))
    def collection_get(self):
        """List complaints
        """
        return {'data': [i.serialize("view") for i in self.request.validated['tender'].complaints]}

    @view(renderer='json', validators=(validate_tender_complaint_exists,))
    def get(self):
        """Retrieving the complaint
        """
        return {'data': self.request.validated['complaint'].serialize("view")}

    @view(content_type="application/json", validators=(validate_patch_complaint_data, validate_tender_complaint_exists), renderer='json')
    def patch(self):
        """Post a complaint resolution
        """
        tender = self.request.validated['tender']
        complaint = self.request.validated['complaint']
        complaint_data = filter_data(self.request.validated['data'])
        if complaint_data:
            src = tender.serialize("plain")
            complaint.import_data(apply_data_patch(complaint.serialize(), complaint_data))
            patch = make_patch(tender.serialize("plain"), src).patch
            if patch:
                tender.revisions.append(Revision({'changes': patch}))
                try:
                    tender.store(self.db)
                except Exception, e:
                    return self.request.errors.add('body', 'data', str(e))
        return {'data': complaint.serialize("view")}
