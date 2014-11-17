# -*- coding: utf-8 -*-
""" Cornice services.
"""
from cornice.ext.spore import generate_spore_description
from cornice.resource import resource, view
from cornice.service import Service, get_services
from jsonpatch import make_patch
from openprocurement.api import VERSION
from openprocurement.api.models import TenderDocument, Bid, Award, Document, revision, get_now
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


def validate_tender_data(request):
    return validate_data(request, TenderDocument)


def validate_bid_data(request):
    return validate_data(request, Bid)


def validate_award_data(request):
    return validate_data(request, Award)


def validate_document_data(request):
    return validate_data(request, Document, True)


def validate_tender_exists(request, key='id'):
    tender = request.matchdict.get(key) and TenderDocument.load(request.registry.db, request.matchdict[key])
    if tender:
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


def validate_tender_bid_exists(request, key='id'):
    tender = validate_tender_exists(request, 'tender_id')
    if tender:
        bids = [i for i in tender.bids if i.id == request.matchdict[key]]
        if bids:
            return bids[0]
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


def validate_file_upload(request):
    if 'file' not in request.POST:
        request.errors.add('body', 'file', 'Not Found')
        request.errors.status = 404


def validate_file_update(request):
    if request.content_type == 'multipart/form-data':
        validate_file_upload(request)


def generate_tender_id(tid):
    return "UA-" + tid


def filter_data(data, fields=['id', 'doc_id', 'modified', 'url']):
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
        self.tender = self.request.matchdict.get('id') and TenderDocument.load(self.db, self.request.matchdict['id'])

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
                        "modified": "2014-10-27T08:06:58.158Z"
                    }
                ]
            }

        """
        # http://wiki.apache.org/couchdb/HTTP_view_API#Querying_Options
        params = {}
        limit = self.request.params.get('limit', '')
        if limit:
            params['limit'] = limit
        limit = int(limit) if limit.isdigit() else 100
        offset = self.request.params.get('offset', '')
        descending = self.request.params.get('descending')
        if descending:
            params['descending'] = descending
        next_offset = get_now().isoformat()
        results = TenderDocument.view(self.db, 'tenders/by_modified', limit=limit + 1, startkey=offset, descending=bool(descending))
        results = [i.serialize("listing") for i in results]
        if len(results) > limit:
            results, last = results[:-1], results[-1]
            params['offset'] = last['modified']
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
                    "modified": "2014-10-27T08:06:58.158Z",
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
        tender_data = filter_data(self.request.json_body['data'])
        tender_id = uuid4().hex
        tender_data['doc_id'] = tender_id
        tender_data['tenderID'] = generate_tender_id(tender_id)
        tender = TenderDocument(tender_data)
        if tender.enquiryPeriod:
            tender.enquiryPeriod.startDate = tender.modified
        else:
            tender.enquiryPeriod = {'startDate': tender.modified}
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
                    "modified": "2014-10-27T08:06:58.158Z",
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
        return {'data': self.tender.serialize(self.tender.status)}

    @view(content_type="application/json", validators=(validate_tender_data, validate_tender_exists), renderer='json')
    def put(self):
        """Tender Edit (full)"""
        src = self.tender.serialize("plain")
        tender_data = filter_data(self.request.json_body['data'])
        self.tender.import_data(tender_data)
        patch = make_patch(self.tender.serialize("plain"), src).patch
        if patch:
            self.tender.revisions.append(revision({'changes': patch}))
            try:
                self.tender.store(self.db)
            except Exception, e:
                return self.request.errors.add('body', 'data', str(e))
        return {'data': self.tender.serialize(self.tender.status)}

    @view(content_type="application/json", validators=(validate_tender_data, validate_tender_exists), renderer='json')
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
                    "modified": "2014-10-27T08:12:34.956Z",
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
        src = self.tender.serialize("plain")
        tender_data = filter_data(self.request.json_body['data'])
        if tender_data:
            if 'tenderID' not in tender_data:
                tender_data['tenderID'] = self.tender.tenderID
            self.tender.import_data(tender_data)
            patch = make_patch(self.tender.serialize("plain"), src).patch
            if patch:
                self.tender.revisions.append(revision({'changes': patch}))
                try:
                    self.tender.store(self.db)
                except Exception, e:
                    return self.request.errors.add('body', 'data', str(e))
        return {'data': self.tender.serialize(self.tender.status)}


@resource(name='Tender Documents',
          collection_path='/tenders/{tender_id}/documents',
          path='/tenders/{tender_id}/documents/{id}',
          description="Tender related binary files (PDFs, etc.)")
class TenderDocumentResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db
        self.tender_id = request.matchdict['tender_id']
        self.document_id = self.request.matchdict.get('id')
        self.tender = TenderDocument.load(self.db, self.tender_id)
        if self.tender and self.document_id:
            self.documents = [i for i in self.tender.documents if i.id == self.document_id]
            self.document = self.documents and self.documents[-1]

    @view(renderer='json', validators=(validate_tender_exists_by_tender_id,))
    def collection_get(self):
        """Tender Documents List"""
        if self.request.params.get('all', ''):
            collection_data = [i.serialize("view") for i in self.tender['documents']]
        else:
            collection_data = sorted(dict([
                (i.id, i.serialize("view"))
                for i in self.tender['documents']
            ]).values(), key=lambda i: i['modified'])
        return {'data': collection_data}

    @view(renderer='json', validators=(validate_file_upload, validate_tender_exists_by_tender_id,))
    def collection_post(self):
        """Tender Document Upload"""
        if self.tender.status != 'enquiries':
            self.request.errors.add('body', 'data', 'Can\'t add document in current tender status')
            self.request.errors.status = 403
            return
        src = self.tender.serialize("plain")
        data = self.request.POST['file']
        document = Document()
        document.id = uuid4().hex
        document.title = data.filename
        document.format = data.type
        key = uuid4().hex
        document.url = self.request.route_url('Tender Documents', tender_id=self.tender_id, id=document.id, _query={'download': key})
        self.tender.documents.append(document)
        upload_file(self.tender, document, key, data.file, self.request)
        patch = make_patch(self.tender.serialize("plain"), src).patch
        self.tender.revisions.append(revision({'changes': patch}))
        try:
            self.tender.store(self.db)
        except Exception, e:
            return self.request.errors.add('body', 'data', str(e))
        self.request.response.status = 201
        self.request.response.headers['Location'] = self.request.route_url('Tender Documents', tender_id=self.tender_id, id=document.id)
        return {'data': document.serialize("view")}

    @view(validators=(validate_tender_document_exists,))
    def get(self):
        """Tender Document Read"""
        key = self.request.params.get('download')
        if key:
            return get_file(self.tender, self.document, key, self.db, self.request)
        document_data = self.document.serialize("view")
        document_data['previousVersions'] = [
            i.serialize("view")
            for i in self.documents
            if i.url != self.document.url
        ]
        return {'data': document_data}

    @view(renderer='json', validators=(validate_file_update, validate_tender_document_exists,))
    def put(self):
        """Tender Document Update"""
        if self.tender.status != 'enquiries':
            self.request.errors.add('body', 'data', 'Can\'t update document in current tender status')
            self.request.errors.status = 403
            return
        src = self.tender.serialize("plain")
        if self.request.content_type == 'multipart/form-data':
            data = self.request.POST['file']
            filename = data.filename
            content_type = data.type
            in_file = data.file
        else:
            filename = self.documents[0].title
            content_type = self.request.content_type
            in_file = self.request.body_file
        document = Document()
        document.id = self.document_id
        document.title = filename
        document.format = content_type
        document.datePublished = self.documents[0].datePublished
        key = uuid4().hex
        document.url = self.request.route_url('Tender Documents', tender_id=self.tender_id, id=document.id, _query={'download': key})
        self.tender.documents.append(document)
        upload_file(self.tender, document, key, in_file, self.request)
        patch = make_patch(self.tender.serialize("plain"), src).patch
        self.tender.revisions.append(revision({'changes': patch}))
        try:
            self.tender.store(self.db)
        except Exception, e:
            return self.request.errors.add('body', 'data', str(e))
        return {'data': document.serialize("view")}

    @view(renderer='json', validators=(validate_document_data, validate_tender_document_exists,))
    def patch(self):
        """Tender Document Update"""
        if self.tender.status != 'enquiries':
            self.request.errors.add('body', 'data', 'Can\'t update document in current tender status')
            self.request.errors.status = 403
            return
        src = self.tender.serialize("plain")
        document_data = filter_data(self.request.json_body['data'])
        if document_data:
            if 'id' not in document_data:
                document_data['id'] = self.document_id
            self.document.import_data(document_data)
            patch = make_patch(self.tender.serialize("plain"), src).patch
            if patch:
                self.tender.revisions.append(revision({'changes': patch}))
                try:
                    self.tender.store(self.db)
                except Exception, e:
                    return self.request.errors.add('body', 'data', str(e))
        return {'data': self.document.serialize("view")}


@resource(name='Tender Bids',
          collection_path='/tenders/{tender_id}/bidders',
          path='/tenders/{tender_id}/bidders/{id}',
          description="Tender bidders")
class TenderBidderResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db
        self.tender_id = request.matchdict['tender_id']
        self.tender = TenderDocument.load(self.db, self.tender_id)
        self.bid_id = request.matchdict.get('id')
        if self.tender and self.bid_id:
            bids = [i for i in self.tender.bids if i.id == self.bid_id]
            self.bid = bids and bids[0]

    @view(content_type="application/json", validators=(validate_bid_data, validate_tender_exists_by_tender_id), renderer='json')
    def collection_post(self):
        """Registration of new bid proposal

        Creating new Bid proposal
        -------------------------

        Example request to create bid proposal:

        .. sourcecode:: http

            POST /tenders/4879d3f8ee2443169b5fbbc9f89fa607/bidders HTTP/1.1
            Host: example.com
            Accept: application/json

            {
                "data": {
                    "bidders": [
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
                    "bidders": [
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
        if self.tender.status != 'tendering':
            self.request.errors.add('body', 'data', 'Can\'t add bid in current tender status')
            self.request.errors.status = 403
            return
        src = self.tender.serialize("plain")
        bid_data = filter_data(
            self.request.json_body['data'], fields=['id', 'date'])
        bid = Bid(bid_data)
        self.tender.bids.append(bid)
        patch = make_patch(self.tender.serialize("plain"), src).patch
        self.tender.revisions.append(revision({'changes': patch}))
        try:
            self.tender.store(self.db)
        except Exception, e:
            return self.request.errors.add('body', 'data', str(e))
        self.request.response.status = 201
        self.request.response.headers['Location'] = self.request.route_url('Tender Bids', tender_id=self.tender_id, id=bid['id'])
        return {'data': bid.serialize("view")}

    @view(renderer='json', validators=(validate_tender_exists_by_tender_id,))
    def collection_get(self):
        """Bids Listing

        Get Bids List
        -------------

        Example request to get bids list:

        .. sourcecode:: http

            GET /tenders/4879d3f8ee2443169b5fbbc9f89fa607/bidders HTTP/1.1
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
        if self.tender.status in ['enquiries', 'tendering']:
            return {'data': []}
        return {'data': [i.serialize(self.tender.status) for i in self.tender.bids]}

    @view(renderer='json', validators=(validate_tender_bid_exists,))
    def get(self):
        """Retrieving the proposal

        Example request for retrieving the proposal:

        .. sourcecode:: http

            GET /tenders/4879d3f8ee2443169b5fbbc9f89fa607/bidders/71b6c23ed8944d688e92a31ec8c3f61a HTTP/1.1
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
        if self.tender.status in ['enquiries', 'tendering']:
            return {'data': {}}
        return {'data': self.bid.serialize(self.tender.status)}

    @view(content_type="application/json", validators=(validate_bid_data, validate_tender_bid_exists), renderer='json')
    def patch(self):
        """Update of proposal

        Example request to change bid proposal:

        .. sourcecode:: http

            PATCH /tenders/4879d3f8ee2443169b5fbbc9f89fa607/bidders/71b6c23ed8944d688e92a31ec8c3f61a HTTP/1.1
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
        if self.tender.status != 'tendering':
            self.request.errors.add('body', 'data', 'Can\'t change bid in current tender status')
            self.request.errors.status = 403
            return
        src = self.tender.serialize("plain")
        bid_data = filter_data(self.request.json_body['data'])
        if bid_data:
            if 'id' not in bid_data:
                bid_data['id'] = self.bid.id
            self.bid.import_data(bid_data)
            patch = make_patch(self.tender.serialize("plain"), src).patch
            if patch:
                self.tender.revisions.append(revision({'changes': patch}))
                try:
                    self.tender.store(self.db)
                except Exception, e:
                    return self.request.errors.add('body', 'data', str(e))
        return {'data': self.bid.serialize("view")}

    @view(renderer='json', validators=(validate_tender_bid_exists,))
    def delete(self):
        """Cancelling the proposal

        Example request for cancelling the proposal:

        .. sourcecode:: http

            DELETE /tenders/4879d3f8ee2443169b5fbbc9f89fa607/bidders/71b6c23ed8944d688e92a31ec8c3f61a HTTP/1.1
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
        if self.tender.status != 'tendering':
            self.request.errors.add('body', 'data', 'Can\'t delete bid in current tender status')
            self.request.errors.status = 403
            return
        src = self.tender.serialize("plain")
        res = self.bid.serialize("view")
        self.tender.bids.remove(self.bid)
        patch = make_patch(self.tender.serialize("plain"), src).patch
        if patch:
            self.tender.revisions.append(revision({'changes': patch}))
            try:
                self.tender.store(self.db)
            except Exception, e:
                return self.request.errors.add('body', 'data', str(e))
        return {'data': res}


@resource(name='Tender Bid Documents',
          collection_path='/tenders/{tender_id}/bidders/{bid_id}/documents',
          path='/tenders/{tender_id}/bidders/{bid_id}/documents/{id}',
          description="Tender bidder documents")
class TenderBidderDocumentResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db
        self.tender_id = request.matchdict['tender_id']
        self.bid_id = request.matchdict['bid_id']
        self.document_id = self.request.matchdict.get('id')
        self.tender = TenderDocument.load(self.db, self.tender_id)
        if self.tender:
            bids = [i for i in self.tender.bids if i.id == self.bid_id]
            self.bid = bids and bids[0]
            if self.bid and self.document_id:
                self.documents = [i for i in self.bid.documents if i.id == self.document_id]
                self.document = self.documents and self.documents[-1]

    @view(renderer='json', validators=(validate_tender_bid_exists_by_bid_id,))
    def collection_get(self):
        """Tender Bid Documents List"""
        if self.request.params.get('all', ''):
            collection_data = [i.serialize("view") for i in self.bid['documents']]
        else:
            collection_data = sorted(dict([
                (i.id, i.serialize("view"))
                for i in self.bid['documents']
            ]).values(), key=lambda i: i['modified'])
        return {'data': collection_data}

    @view(renderer='json', validators=(validate_file_upload, validate_tender_bid_exists_by_bid_id,))
    def collection_post(self):
        """Tender Bid Document Upload
        """
        if self.tender.status not in ['tendering', 'auction', 'qualification']:
            self.request.errors.add('body', 'data', 'Can\'t add document in current tender status')
            self.request.errors.status = 403
            return
        src = self.tender.serialize("plain")
        data = self.request.POST['file']
        document = Document()
        document.id = uuid4().hex
        document.title = data.filename
        document.format = data.type
        key = uuid4().hex
        document.url = self.request.route_url('Tender Bid Documents', tender_id=self.tender_id, bid_id=self.bid_id, id=document.id, _query={'download': key})
        self.bid.documents.append(document)
        upload_file(self.tender, document, key, data.file, self.request)
        patch = make_patch(self.tender.serialize("plain"), src).patch
        self.tender.revisions.append(revision({'changes': patch}))
        try:
            self.tender.store(self.db)
        except Exception, e:
            return self.request.errors.add('body', 'data', str(e))
        self.request.response.status = 201
        self.request.response.headers['Location'] = self.request.route_url('Tender Bid Documents', tender_id=self.tender_id, bid_id=self.bid_id, id=document.id)
        return {'data': document.serialize("view")}

    @view(renderer='json', validators=(validate_tender_bid_document_exists,))
    def get(self):
        """Tender Bid Document Read"""
        key = self.request.params.get('download')
        if key:
            return get_file(self.tender, self.document, key, self.db, self.request)
        document_data = self.document.serialize("view")
        document_data['previousVersions'] = [
            i.serialize("view")
            for i in self.documents
            if i.url != self.document.url
        ]
        return {'data': document_data}

    @view(renderer='json', validators=(validate_file_update, validate_tender_bid_document_exists,))
    def put(self):
        """Tender Bid Document Update"""
        if self.tender.status not in ['tendering', 'auction', 'qualification']:
            self.request.errors.add('body', 'data', 'Can\'t update document in current tender status')
            self.request.errors.status = 403
            return
        src = self.tender.serialize("plain")
        if self.request.content_type == 'multipart/form-data':
            data = self.request.POST['file']
            filename = data.filename
            content_type = data.type
            in_file = data.file
        else:
            filename = self.documents[0].title
            content_type = self.request.content_type
            in_file = self.request.body_file
        document = Document()
        document.id = self.request.matchdict['id']
        document.title = filename
        document.format = content_type
        document.datePublished = self.documents[0].datePublished
        key = uuid4().hex
        document.url = self.request.route_url('Tender Bid Documents', tender_id=self.tender_id, bid_id=self.bid_id, id=document.id, _query={'download': key})
        self.bid.documents.append(document)
        upload_file(self.tender, document, key, in_file, self.request)
        patch = make_patch(self.tender.serialize("plain"), src).patch
        self.tender.revisions.append(revision({'changes': patch}))
        try:
            self.tender.store(self.db)
        except Exception, e:
            return self.request.errors.add('body', 'data', str(e))
        return {'data': document.serialize("view")}

    @view(renderer='json', validators=(validate_document_data, validate_tender_bid_document_exists,))
    def patch(self):
        """Tender Bid Document Update"""
        if self.tender.status not in ['tendering', 'auction', 'qualification']:
            self.request.errors.add('body', 'data', 'Can\'t update document in current tender status')
            self.request.errors.status = 403
            return
        src = self.tender.serialize("plain")
        document_data = filter_data(self.request.json_body['data'])
        if document_data:
            if 'id' not in document_data:
                document_data['id'] = self.document_id
            self.document.import_data(document_data)
            patch = make_patch(self.tender.serialize("plain"), src).patch
            if patch:
                self.tender.revisions.append(revision({'changes': patch}))
                try:
                    self.tender.store(self.db)
                except Exception, e:
                    return self.request.errors.add('body', 'data', str(e))
        return {'data': self.document.serialize("view")}


@resource(name='Tender Awards',
          collection_path='/tenders/{tender_id}/awards',
          path='/tenders/{tender_id}/awards/{id}',
          description="Tender awards")
class TenderAwardResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db
        self.tender_id = request.matchdict['tender_id']
        self.tender = TenderDocument.load(self.db, self.tender_id)

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
        return {'data': [i.serialize("view") for i in self.tender.awards]}

    @view(content_type="application/json", validators=(validate_award_data, validate_tender_exists_by_tender_id), renderer='json')
    def collection_post(self):
        """Accept or reject bidder application

        Creating new Award
        ------------------

        Example request to create award:

        .. sourcecode:: http

            POST /tenders/4879d3f8ee2443169b5fbbc9f89fa607/bidders HTTP/1.1
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
        if self.tender.status != 'qualification':
            self.request.errors.add('body', 'data', 'Can\'t create award in current tender status')
            self.request.errors.status = 403
            return
        src = self.tender.serialize("plain")
        award_data = self.request.json_body['data']
        award = Award(award_data)
        self.tender.awards.append(award)
        patch = make_patch(self.tender.serialize("plain"), src).patch
        self.tender.revisions.append(revision({'changes': patch}))
        try:
            self.tender.store(self.db)
        except Exception, e:
            return self.request.errors.add('body', 'data', str(e))
        self.request.response.status = 201
        # self.request.response.headers['Location'] = self.request.route_url('Tender Bids', tender_id=self.tender_id, id=award['awardID'])
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
                "modified": "2014-10-27T08:06:58.158Z",
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
    db = request.registry.db
    tender = TenderDocument.load(db, request.matchdict['tender_id'])
    auction_info = tender.serialize("auction_view")
    return {'data': auction_info}


@auction.patch(content_type="application/json", validators=(validate_tender_data, validate_tender_exists_by_tender_id), renderer='json')
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
                "modified": "2014-10-27T08:06:58.158Z",
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
                "modified": "2014-10-27T08:06:58.158Z",
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
    db = request.registry.db
    tender = TenderDocument.load(db, request.matchdict['tender_id'])
    src = tender.serialize("plain")
    auction_data = filter_data(request.json_body['data'])
    if auction_data:
        auction_data['tenderID'] = tender.tenderID
        tender.import_data(auction_data)
        patch = make_patch(tender.serialize("plain"), src).patch
        if patch:
            tender.revisions.append(revision({'changes': patch}))
            try:
                tender.store(db)
            except Exception, e:
                return request.errors.add('body', 'data', str(e))
    return {'data': tender.serialize("auction_view")}
