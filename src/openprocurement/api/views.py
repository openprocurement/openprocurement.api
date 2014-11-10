# -*- coding: utf-8 -*-
""" Cornice services.
"""
import datetime
from cornice.ext.spore import generate_spore_description
from cornice.resource import resource, view
from cornice.service import Service, get_services
from jsonpatch import make_patch
from openprocurement.api import VERSION
from openprocurement.api.models import TenderDocument, Bid, Award, Document, revision
from schematics.exceptions import ModelValidationError, ModelConversionError
from urllib import quote
from uuid import uuid4
from base64 import b64encode


spore = Service(name='spore', path='/spore', renderer='json')
auction = Service(name='Tender Auction', path='/tenders/{tender_id}/auction', renderer='json')


def validate_data(request, model):
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
        model(data).validate()
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


def generate_tender_id(tid):
    return "UA-" + tid


def filter_data(data, fields=['id', 'doc_id', 'modified']):
    result = data.copy()
    for i in fields:
        if i in result:
            del result[i]
    return result


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
        next_offset = datetime.datetime.now().isoformat()
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
                    "totalValue": {
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
                    "totalValue": {
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
        try:
            tender.store(self.db)
        except Exception, e:
            return self.request.errors.add('body', 'data', str(e))
        self.request.response.status = 201
        self.request.response.headers[
            'Location'] = self.request.route_url('Tender', id=tender_id)
        return {'data': tender.serialize("view")}

    @view(renderer='json')
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
                    "totalValue": {
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
        tender = TenderDocument.load(self.db, self.request.matchdict['id'])
        if not tender:
            self.request.errors.add('url', 'id', 'Not Found')
            self.request.errors.status = 404
            return
        return {'data': tender.serialize("view")}

    @view(content_type="application/json", validators=(validate_tender_data,), renderer='json')
    def put(self):
        """Tender Edit (full)"""
        tender = TenderDocument.load(self.db, self.request.matchdict['id'])
        if not tender:
            self.request.errors.add('url', 'id', 'Not Found')
            self.request.errors.status = 404
            return
        src = tender.serialize("plain")
        tender_data = filter_data(self.request.json_body['data'])
        tender.import_data(tender_data)
        patch = make_patch(tender.serialize("plain"), src).patch
        if patch:
            tender.revisions.append(revision({'changes': patch}))
            try:
                tender.store(self.db)
            except Exception, e:
                return self.request.errors.add('body', 'data', str(e))
        return {'data': tender.serialize("view")}

    @view(content_type="application/json", validators=(validate_tender_data,), renderer='json')
    def patch(self):
        """Tender Edit (partial)

        For example here is how procuring entity can change number of items to be procured and total Value of a tender:

        .. sourcecode:: http

            PATCH /tenders/4879d3f8ee2443169b5fbbc9f89fa607 HTTP/1.1
            Host: example.com
            Accept: application/json

            {
                "data": {
                    "totalValue": {
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
                    "totalValue": {
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
        tender = TenderDocument.load(self.db, self.request.matchdict['id'])
        if not tender:
            self.request.errors.add('url', 'id', 'Not Found')
            self.request.errors.status = 404
            return
        src = tender.serialize("plain")
        tender_data = filter_data(self.request.json_body['data'])
        if tender_data:
            if 'tenderID' not in tender_data:
                tender_data['tenderID'] = tender.tenderID
            tender.import_data(tender_data)
            patch = make_patch(tender.serialize("plain"), src).patch
            if patch:
                tender.revisions.append(revision({'changes': patch}))
                try:
                    tender.store(self.db)
                except Exception, e:
                    return self.request.errors.add('body', 'data', str(e))
        return {'data': tender.serialize("view")}


@resource(name='Tender Documents',
          collection_path='/tenders/{tender_id}/documents',
          path='/tenders/{tender_id}/documents/{id}',
          description="Tender related binary files (PDFs, etc.)")
class TenderDocumentResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db
        self.tender_id = request.matchdict['tender_id']

    @view(renderer='json')
    def collection_get(self):
        """Tender Documents List"""
        tender = TenderDocument.load(self.db, self.tender_id)
        if not tender:
            self.request.errors.add('url', 'tender_id', 'Not Found')
            self.request.errors.status = 404
            return
        view_all = self.request.params.get('all', '')
        if self.request.params.get('all', ''):
            collection_data = [i.serialize("view") for i in tender['documents']]
        else:
            collection_data = sorted(dict([
                (i.id, i.serialize("view"))
                for i in tender['documents']
            ]).values(), key=lambda i: i['modified'])
        return {'data': collection_data}

    @view(renderer='json')
    def collection_post(self):
        """Tender Document Upload"""
        if 'file' not in self.request.POST:
            self.request.errors.add('body', 'file', 'Not Found')
            self.request.errors.status = 404
            return
        tender = TenderDocument.load(self.db, self.tender_id)
        if not tender:
            self.request.errors.add('url', 'tender_id', 'Not Found')
            self.request.errors.status = 404
            return
        src = tender.serialize("plain")
        data = self.request.POST['file']
        document = Document()
        document.id = uuid4().hex
        document.title = data.filename
        document.format = data.type
        key = uuid4().hex
        document.url = self.request.route_url('Tender Documents', tender_id=self.tender_id, id=document.id, _query={'download': key})
        tender.documents.append(document)
        filename = "{}_{}".format(document.id, key)
        tender['_attachments'][filename] = {
            "content_type": data.type,
            "data": b64encode(data.file.read())
        }
        patch = make_patch(tender.serialize("plain"), src).patch
        tender.revisions.append(revision({'changes': patch}))
        try:
            tender.store(self.db)
        except Exception, e:
            return self.request.errors.add('body', 'data', str(e))
        self.request.response.status = 201
        self.request.response.headers['Location'] = self.request.route_url('Tender Documents', tender_id=self.tender_id, id=document.id)
        return {'data': document.serialize("view")}

    def get(self):
        """Tender Document Read"""
        tender = TenderDocument.load(self.db, self.tender_id)
        if not tender:
            self.request.errors.add('url', 'tender_id', 'Not Found')
            self.request.errors.status = 404
            return
        documents = [i for i in tender.documents if i.id == self.request.matchdict['id']]
        if not documents:
            self.request.errors.add('url', 'id', 'Not Found')
            self.request.errors.status = 404
            return
        document = documents[-1]
        key = self.request.params.get('download')
        if key:
            filename = "{}_{}".format(document.id, key)
            data = self.db.get_attachment(self.tender_id, filename)
            if not data:
                self.request.errors.add('url', 'download', 'Not Found')
                self.request.errors.status = 404
                return
            self.request.response.content_type = tender['_attachments'][filename]["content_type"].encode('utf-8')
            self.request.response.content_disposition = 'attachment; filename={}'.format(quote(document.title.encode('utf-8')))
            self.request.response.body_file = data
            return self.request.response
        document_data = document.serialize("view")
        document_data['previousVersions'] = [
            i.serialize("view")
            for i in documents
            if i.url != document.url
        ]
        return {'data': document_data}

    @view(renderer='json')
    def put(self):
        """Tender Document Update"""
        if 'file' not in self.request.POST:
            self.request.errors.add('body', 'file', 'Not Found')
            self.request.errors.status = 404
            return
        tender = TenderDocument.load(self.db, self.tender_id)
        if not tender:
            self.request.errors.add('url', 'tender_id', 'Not Found')
            self.request.errors.status = 404
            return
        data = self.request.POST['file']
        documents = [i for i in tender.documents if i.id == self.request.matchdict['id']]
        if not documents:
            self.request.errors.add('url', 'id', 'Not Found')
            self.request.errors.status = 404
            return
        src = tender.serialize("plain")
        document = Document()
        document.id = self.request.matchdict['id']
        document.title = data.filename
        document.format = data.type
        document.datePublished = documents[0].datePublished
        key = uuid4().hex
        document.url = self.request.route_url('Tender Documents', tender_id=self.tender_id, id=document.id, _query={'download': key})
        tender.documents.append(document)
        filename = "{}_{}".format(document.id, key)
        tender['_attachments'][filename] = {
            "content_type": data.type,
            "data": b64encode(data.file.read())
        }
        patch = make_patch(tender.serialize("plain"), src).patch
        tender.revisions.append(revision({'changes': patch}))
        try:
            tender.store(self.db)
        except Exception, e:
            return self.request.errors.add('body', 'data', str(e))
        return {'data': document.serialize("view")}


@resource(name='Tender Bids',
          collection_path='/tenders/{tender_id}/bidders',
          path='/tenders/{tender_id}/bidders/{id}',
          description="Tender bidders")
class TenderBidderResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db
        self.tender_id = request.matchdict['tender_id']

    @view(content_type="application/json", validators=(validate_bid_data,), renderer='json')
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
                    "totalValue": {
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
                    "totalValue": {
                        "amount": 489,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": true
                    }
                }
            }

        """
        # See https://github.com/open-contracting/standard/issues/78#issuecomment-59830415
        # for more info upon schema
        tender = TenderDocument.load(self.db, self.tender_id)
        if not tender:
            self.request.errors.add('url', 'tender_id', 'Not Found')
            self.request.errors.status = 404
            return
        src = tender.serialize("plain")
        bid_data = filter_data(
            self.request.json_body['data'], fields=['id', 'date'])
        bid = Bid(bid_data)
        tender.bids.append(bid)
        patch = make_patch(tender.serialize("plain"), src).patch
        tender.revisions.append(revision({'changes': patch}))
        try:
            tender.store(self.db)
        except Exception, e:
            return self.request.errors.add('body', 'data', str(e))
        self.request.response.status = 201
        self.request.response.headers['Location'] = self.request.route_url('Tender Bids', tender_id=self.tender_id, id=bid['id'])
        return {'data': bid.serialize("view")}

    @view(renderer='json')
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
                        "totalValue": {
                            "amount": 489,
                            "currency": "UAH",
                            "valueAddedTaxIncluded": true
                        }
                    }
                ]
            }

        """
        tender = TenderDocument.load(self.db, self.tender_id)
        if not tender:
            self.request.errors.add('url', 'tender_id', 'Not Found')
            self.request.errors.status = 404
            return
        return {'data': [i.serialize("view") for i in tender.bids]}

    @view(renderer='json')
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
                    "totalValue": {
                        "amount": 600,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": true
                    }
                }
            }

        """
        tender = TenderDocument.load(self.db, self.tender_id)
        if not tender:
            self.request.errors.add('url', 'tender_id', 'Not Found')
            self.request.errors.status = 404
            return
        bid_id = self.request.matchdict['id']
        bids = [i for i in tender.bids if i.id == bid_id]
        if not bids:
            self.request.errors.add('url', 'id', 'Not Found')
            self.request.errors.status = 404
            return
        bid = bids[0]
        return {'data': bid.serialize("view")}

    @view(content_type="application/json", validators=(validate_bid_data,), renderer='json')
    def patch(self):
        """Update of proposal

        Example request to change bid proposal:

        .. sourcecode:: http

            PATCH /tenders/4879d3f8ee2443169b5fbbc9f89fa607/bidders/71b6c23ed8944d688e92a31ec8c3f61a HTTP/1.1
            Host: example.com
            Accept: application/json

            {
                "data": {
                    "totalValue": {
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
                    "totalValue": {
                        "amount": 600,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": true
                    }
                }
            }

        """
        tender = TenderDocument.load(self.db, self.tender_id)
        if not tender:
            self.request.errors.add('url', 'tender_id', 'Not Found')
            self.request.errors.status = 404
            return
        src = tender.serialize("plain")
        bid_id = self.request.matchdict['id']
        bids = [i for i in tender.bids if i.id == bid_id]
        if not bids:
            self.request.errors.add('url', 'id', 'Not Found')
            self.request.errors.status = 404
            return
        bid = bids[0]
        bid_data = filter_data(self.request.json_body['data'])
        if bid_data:
            if 'id' not in bid_data:
                bid_data['id'] = bid.id
            bid.import_data(bid_data)
            patch = make_patch(tender.serialize("plain"), src).patch
            if patch:
                tender.revisions.append(revision({'changes': patch}))
                try:
                    tender.store(self.db)
                except Exception, e:
                    return self.request.errors.add('body', 'data', str(e))
        return {'data': bid.serialize("view")}

    @view(renderer='json')
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
                    "totalValue": {
                        "amount": 489,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": true
                    }
                }
            }

        """
        tender = TenderDocument.load(self.db, self.tender_id)
        if not tender:
            self.request.errors.add('url', 'tender_id', 'Not Found')
            self.request.errors.status = 404
            return
        src = tender.serialize("plain")
        bid_id = self.request.matchdict['id']
        bids = [i for i in tender.bids if i.id == bid_id]
        if not bids:
            self.request.errors.add('url', 'id', 'Not Found')
            self.request.errors.status = 404
            return
        bid = bids[0]
        res = bid.serialize("view")
        tender.bids.remove(bid)
        patch = make_patch(tender.serialize("plain"), src).patch
        if patch:
            tender.revisions.append(revision({'changes': patch}))
            try:
                tender.store(self.db)
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

    @view(renderer='json')
    def collection_get(self):
        """Tender Bid Documents List"""
        tender = TenderDocument.load(self.db, self.tender_id)
        if not tender:
            self.request.errors.add('url', 'tender_id', 'Not Found')
            self.request.errors.status = 404
            return
        bids = [i for i in tender.bids if i.id == self.bid_id]
        if not bids:
            self.request.errors.add('url', 'bid_id', 'Not Found')
            self.request.errors.status = 404
            return
        bid = bids[0]
        if self.request.params.get('all', ''):
            collection_data = [i.serialize("view") for i in bid['documents']]
        else:
            collection_data = sorted(dict([
                (i.id, i.serialize("view"))
                for i in bid['documents']
            ]).values(), key=lambda i: i['modified'])
        return {'data': collection_data}

    @view(renderer='json')
    def collection_post(self):
        """Tender Bid Document Upload
        """
        if 'file' not in self.request.POST:
            self.request.errors.add('body', 'file', 'Not Found')
            self.request.errors.status = 404
            return
        tender = TenderDocument.load(self.db, self.tender_id)
        if not tender:
            self.request.errors.add('url', 'tender_id', 'Not Found')
            self.request.errors.status = 404
            return
        src = tender.serialize("plain")
        bids = [i for i in tender.bids if i.id == self.bid_id]
        if not bids:
            self.request.errors.add('url', 'bid_id', 'Not Found')
            self.request.errors.status = 404
            return
        bid = bids[0]
        data = self.request.POST['file']
        document = Document()
        document.id = uuid4().hex
        document.title = data.filename
        document.format = data.type
        key = uuid4().hex
        document.url = self.request.route_url('Tender Bid Documents', tender_id=self.tender_id, bid_id=self.bid_id, id=document.id, _query={'download': key})
        bid.documents.append(document)
        filename = "{}_{}".format(document.id, key)
        tender['_attachments'][filename] = {
            "content_type": data.type,
            "data": b64encode(data.file.read())
        }
        patch = make_patch(tender.serialize("plain"), src).patch
        tender.revisions.append(revision({'changes': patch}))
        try:
            tender.store(self.db)
        except Exception, e:
            return self.request.errors.add('body', 'data', str(e))
        self.request.response.status = 201
        self.request.response.headers['Location'] = self.request.route_url('Tender Bid Documents', tender_id=self.tender_id, bid_id=self.bid_id, id=document.id)
        return {'data': document.serialize("view")}

    def get(self):
        """Tender Bid Document Read"""
        tender = TenderDocument.load(self.db, self.tender_id)
        if not tender:
            self.request.errors.add('url', 'tender_id', 'Not Found')
            self.request.errors.status = 404
            return
        bids = [i for i in tender.bids if i.id == self.bid_id]
        if not bids:
            self.request.errors.add('url', 'bid_id', 'Not Found')
            self.request.errors.status = 404
            return
        bid = bids[0]
        documents = [i for i in bid.documents if i.id == self.request.matchdict['id']]
        if not documents:
            self.request.errors.add('url', 'id', 'Not Found')
            self.request.errors.status = 404
            return
        document = documents[-1]
        key = self.request.params.get('download')
        if key:
            filename = "{}_{}".format(document.id, key)
            data = self.db.get_attachment(self.tender_id, filename)
            if not data:
                self.request.errors.add('url', 'download', 'Not Found')
                self.request.errors.status = 404
                return
            self.request.response.content_type = tender['_attachments'][filename]["content_type"].encode('utf-8')
            self.request.response.content_disposition = 'attachment; filename={}'.format(quote(document.title.encode('utf-8')))
            self.request.response.body_file = data
            return self.request.response
        document_data = document.serialize("view")
        document_data['previousVersions'] = [
            i.serialize("view")
            for i in documents
            if i.url != document.url
        ]
        return {'data': document_data}

    @view(renderer='json')
    def put(self):
        """Tender Bid Document Update"""
        if 'file' not in self.request.POST:
            self.request.errors.add('body', 'file', 'Not Found')
            self.request.errors.status = 404
            return
        tender = TenderDocument.load(self.db, self.tender_id)
        if not tender:
            self.request.errors.add('url', 'tender_id', 'Not Found')
            self.request.errors.status = 404
            return
        data = self.request.POST['file']
        bids = [i for i in tender.bids if i.id == self.bid_id]
        if not bids:
            self.request.errors.add('url', 'bid_id', 'Not Found')
            self.request.errors.status = 404
            return
        bid = bids[0]
        documents = [i for i in bid.documents if i.id == self.request.matchdict['id']]
        if not documents:
            self.request.errors.add('url', 'id', 'Not Found')
            self.request.errors.status = 404
            return
        src = tender.serialize("plain")
        document = Document()
        document.id = self.request.matchdict['id']
        document.title = data.filename
        document.format = data.type
        document.datePublished = documents[0].datePublished
        key = uuid4().hex
        document.url = self.request.route_url('Tender Bid Documents', tender_id=self.tender_id, bid_id=self.bid_id, id=document.id, _query={'download': key})
        bid.documents.append(document)
        filename = "{}_{}".format(document.id, key)
        tender['_attachments'][filename] = {
            "content_type": data.type,
            "data": b64encode(data.file.read())
        }
        patch = make_patch(tender.serialize("plain"), src).patch
        tender.revisions.append(revision({'changes': patch}))
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
        self.tender_id = request.matchdict['tender_id']

    @view(renderer='json')
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
        tender = TenderDocument.load(self.db, self.tender_id)
        if not tender:
            self.request.errors.add('url', 'tender_id', 'Not Found')
            self.request.errors.status = 404
            return
        return {'data': [i.serialize("view") for i in tender.awards]}

    @view(content_type="application/json", validators=(validate_award_data,), renderer='json')
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
        tender = TenderDocument.load(self.db, self.tender_id)
        if not tender:
            self.request.errors.add('url', 'tender_id', 'Not Found')
            self.request.errors.status = 404
            return
        src = tender.serialize("plain")
        award_data = self.request.json_body['data']
        award = Award(award_data)
        tender.awards.append(award)
        patch = make_patch(tender.serialize("plain"), src).patch
        tender.revisions.append(revision({'changes': patch}))
        try:
            tender.store(self.db)
        except Exception, e:
            return self.request.errors.add('body', 'data', str(e))
        self.request.response.status = 201
        # self.request.response.headers['Location'] = self.request.route_url('Tender Bids', tender_id=self.tender_id, id=award['awardID'])
        return {'data': award.serialize("view")}


@auction.get(renderer='json')
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
                        "totalValue": {
                            "amount": 500,
                            "currency": "UAH",
                            "valueAddedTaxIncluded": true
                        }
                    },
                    {
                        "totalValue": {
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
    tender_id = request.matchdict['tender_id']
    tender = TenderDocument.load(db, tender_id)
    if not tender:
        request.errors.add('url', 'tender_id', 'Not Found')
        request.errors.status = 404
        return
    auction_info = tender.serialize("auction")
    return {'data': auction_info}


@auction.patch(content_type="application/json", validators=(validate_tender_data,), renderer='json')
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
                        "totalValue": {
                            "amount": 400,
                            "currency": "UAH"
                        }
                    },
                    {
                        "totalValue": {
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
                        "totalValue": {
                            "amount": 400,
                            "currency": "UAH",
                            "valueAddedTaxIncluded": true
                        }
                    },
                    {
                        "totalValue": {
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
    tender_id = request.matchdict['tender_id']
    tender = TenderDocument.load(db, tender_id)
    if not tender:
        request.errors.add('url', 'tender_id', 'Not Found')
        request.errors.status = 404
        return
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
    return {'data': tender.serialize("auction")}
