# -*- coding: utf-8 -*-
""" Cornice services.
"""
from cornice.ext.spore import generate_spore_description
from cornice.service import Service, get_services
from cornice.resource import resource, view
from schematics.exceptions import ModelValidationError, ModelConversionError
from uuid import uuid4
from openprocurement.api.models import TenderDocument, Organization


spore = Service('spore', path='/spore', renderer='json')


def wrap_data(data):
    return {"data": data}


def validate_data(request):
    try:
        json = request.json_body
    except ValueError, e:
        request.errors.add('body', 'data', e.message)
        request.errors.status = 422
        return
    if not isinstance(json, dict) or 'data' not in json:
        request.errors.add('body', 'data', "Data not available")
        request.errors.status = 422
        return
    data = json['data']
    try:
        TenderDocument(data).validate()
    except (ModelValidationError, ModelConversionError), e:
        for i in e.message:
            request.errors.add('body', i, e.message[i])
        request.errors.status = 422


def validate_bidder_data(request):
    try:
        json = request.json_body
    except ValueError, e:
        request.errors.add('body', 'data', e.message)
        request.errors.status = 422
        return
    if not isinstance(json, dict) or 'data' not in json:
        request.errors.add('body', 'data', "Data not available")
        request.errors.status = 422
        return
    data = json['data']
    try:
        Organization(data).validate()
    except (ModelValidationError, ModelConversionError), e:
        for i in e.message:
            request.errors.add('body', i, e.message[i])
        request.errors.status = 422


def generate_tender_id(tid):
    return "UA-2014-DUS-" + tid


def filter_data(data, fields=['id', 'doc_id', 'modified']):
    result = data.copy()
    for i in fields:
        if i in result:
            del result[i]
    return result


@spore.get()
def get_spore(request):
    services = get_services()
    return generate_spore_description(services, 'Service name', request.application_url, '0.1')


@resource(name='Tender',
          collection_path='/tenders',
          path='/tenders/{id}',
          description="Open Contracting compatible data exchange format. See http://ocds.open-contracting.org/standard/r/master/#tender for more info")
class TenderResource(object):
    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    def collection_get(self):
        # limit, skip, descending
        results = TenderDocument.view(self.db, 'tenders/all')
        return {'tenders': [i.serialize("view") for i in results]}

    @view(content_type="application/json", validators=(validate_data,))
    def collection_post(self):
        """This API request is targeted to creating new Tenders by procuring organizations.

        Creating new Tender
        -------------------

        Example request to create tender:

        .. sourcecode:: http

            POST /tenders HTTP/1.1

            {
                "data":{
                    "procuringEntity":{
                        "id":{
                            "name":"Державне управління справами",
                            "scheme":"https://ns.openprocurement.org/ua/edrpou",
                            "uid":"00037256",
                            "uri":"http://www.dus.gov.ua/"
                        },
                        "address":{
                            "countryName":"Україна",
                            "postalCode":"01220",
                            "region":"м. Київ",
                            "locality":"м. Київ",
                            "streetAddress":"вул. Банкова, 11, корпус 1"
                        }
                    },
                    "totalValue":{
                        "amount":500,
                        "currency":"UAH"
                    },
                    "itemsToBeProcured":[
                        {
                            "description":"футляри до державних нагород",
                            "classificationScheme":"Other",
                            "otherClassificationScheme":"ДКПП",
                            "classificationID":"17.21.1",
                            "classificationDescription":"папір і картон гофровані, паперова й картонна тара",
                            "unitOfMeasure":"item",
                            "quantity":5
                        }
                    ],
                    "clarificationPeriod":{
                        "endDate":"2014-10-31T00:00:00"
                    },
                    "tenderPeriod":{
                        "endDate":"2014-11-06T10:00:00"
                    },
                    "awardPeriod":{
                        "endDate":"2014-11-13T00:00:00"
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
                    "tenderID": "UA-2014-DUS-156",
                    "modified": "2014-10-27T08:06:58.158Z",
                    ...
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
        self.request.response.headers['Location'] = self.request.route_url('Tender', id=tender_id)
        return wrap_data(tender.serialize("view"))

    @view(renderer='json')
    def get(self):
        """Tender Read"""
        tender = TenderDocument.load(self.db, self.request.matchdict['id'])
        if not tender:
            self.request.errors.add('url', 'id', 'Not Found')
            self.request.errors.status = 404
            return
        return wrap_data(tender.serialize("view"))

    @view(content_type="application/json", validators=(validate_data,))
    def put(self):
        """Tender Edit (full)"""
        tender = TenderDocument.load(self.db, self.request.matchdict['id'])
        if not tender:
            self.request.errors.add('url', 'id', 'Not Found')
            self.request.errors.status = 404
            return
        tender_data = filter_data(self.request.json_body['data'])
        try:
            tender.import_data(tender_data)
            tender.store(self.db)
        except Exception, e:
            return self.request.errors.add('body', 'data', str(e))
        return wrap_data(tender.serialize("view"))

    @view(content_type="application/json", validators=(validate_data,))
    def patch(self):
        """Tender Edit (partial)

        For example here is how procuring entity can change number of items to be procured and total Value of a tender:

        .. sourcecode:: http

            PATCH /tenders/4879d3f8ee2443169b5fbbc9f89fa607 HTTP/1.1

            {
                "data":{
                    "totalValue":{
                        "amount":600
                    },
                    "itemsToBeProcured":[
                        {
                            "quantity":6
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
                    "tenderID": "UA-2014-DUS-156",
                    "modified": "2014-10-27T08:12:34.956Z",
                    ...
                }
            }

        """
        tender = TenderDocument.load(self.db, self.request.matchdict['id'])
        if not tender:
            self.request.errors.add('url', 'id', 'Not Found')
            self.request.errors.status = 404
            return
        tender_data = filter_data(self.request.json_body['data'])
        if 'tenderID' not in tender_data:
            tender_data['tenderID'] = tender.tenderID
        try:
            tender.import_data(tender_data)
            tender.store(self.db)
        except Exception, e:
            return self.request.errors.add('body', 'data', str(e))
        return wrap_data(tender.serialize("view"))


@resource(name='Tender Documents',
          collection_path='/tenders/{tender_id}/documents',
          path='/tenders/{tender_id}/documents/{id}',
          description="Tender related binary files (PDFs, etc.)")
class TenderDocumentResource(object):
    def __init__(self, request):
        self.request = request
        self.db = request.registry.db
        self.tender_id = request.matchdict['tender_id']

    def collection_get(self):
        """Tender Documents List"""
        tender = TenderDocument.load(self.db, self.tender_id)
        if not tender:
            self.request.errors.add('url', 'tender_id', 'Not Found')
            self.request.errors.status = 404
            return
        return {'documents': tender['_attachments']}

    def collection_post(self):
        """Tender Document Upload"""
        tender = TenderDocument.load(self.db, self.tender_id)
        if not tender:
            self.request.errors.add('url', 'tender_id', 'Not Found')
            self.request.errors.status = 404
            return
        for data in self.request.POST.values():
            try:
                self.db.put_attachment(tender._data, data.file, data.filename)
            except Exception, e:
                return self.request.errors.add('body', 'data', str(e))
        tender = tender.reload(self.db)
        self.request.response.status = 201
        self.request.response.headers['Location'] = self.request.route_url('Tender Documents', tender_id=self.tender_id, id=data.filename)
        return {'documents': tender['_attachments']}

    def get(self):
        """Tender Document Read"""
        data = self.db.get_attachment(self.tender_id, self.request.matchdict['id'])
        if not data:
            self.request.errors.add('url', 'id', 'Not Found')
            self.request.errors.status = 404
            return
        self.request.response.body_file = data
        return self.request.response

    def put(self):
        """Tender Document Update"""
        tender = TenderDocument.load(self.db, self.tender_id)
        if not tender:
            self.request.errors.add('url', 'tender_id', 'Not Found')
            self.request.errors.status = 404
            return
        for data in self.request.POST.values():
            if data.filename not in tender['_attachments']:
                self.request.errors.add('url', 'id', 'Not Found')
                self.request.errors.status = 404
                return
            try:
                self.db.put_attachment(tender, data.file, data.filename)
            except Exception, e:
                return self.request.errors.add('body', 'data', str(e))
        tender = tender.reload(self.db)
        return tender['_attachments'].get(self.request.matchdict['id'], {})


@resource(name='Tender Bidders',
          collection_path='/tenders/{tender_id}/bidders',
          path='/tenders/{tender_id}/bidders/{id}',
          description="Tender bidders")
class TenderBidderResource(object):
    def __init__(self, request):
        self.request = request
        self.db = request.registry.db
        self.tender_id = request.matchdict['tender_id']

    @view(content_type="application/json", validators=(validate_bidder_data,))
    def collection_post(self):
        """Registration of new bidder

        Creating new Bidder
        -------------------

        Example request to create bidder:

        .. sourcecode:: http

            POST /tenders/4879d3f8ee2443169b5fbbc9f89fa607/bidders HTTP/1.1

            {
                "data":{
                    "bidders":[
                        {
                            "id":{
                                "name":"Державне управління справами",
                                "scheme":"https://ns.openprocurement.org/ua/edrpou",
                                "uid":"00037256",
                                "uri":"http://www.dus.gov.ua/"
                            },
                            "address":{
                                "countryName":"Україна",
                                "postalCode":"01220",
                                "region":"м. Київ",
                                "locality":"м. Київ",
                                "streetAddress":"вул. Банкова, 11, корпус 1"
                            }
                        }
                    ],
                    "totalValue":{
                        "amount":489,
                        "currency":"UAH"
                    }
                }
            }

        This is what one should expect in response:

        .. sourcecode:: http

            HTTP/1.1 201 Created
            Content-Type: application/json

            {
                "data": {
                    "_id":"4879d3f8ee2443169b5fbbc9f89fa607",
                    "status":"registration",
                    "date":"2014-10-28T11:44:17.947Z"
                    ...
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
        bidder_data = filter_data(self.request.json_body['data'], fields=['_id'])
        bidder = Organization(bidder_data)
        tender.bidders.append(bidder)
        try:
            tender.store(self.db)
        except Exception, e:
            return self.request.errors.add('body', 'data', str(e))
        self.request.response.status = 201
        #self.request.response.headers['Location'] = self.request.route_url('Tender Bidders', tender_id=self.tender_id, id=bidder['_id'])
        return wrap_data(bidder.serialize("view", bidder))
