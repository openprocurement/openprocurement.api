# -*- coding: utf-8 -*-
""" Cornice services.
"""
from cornice.ext.spore import generate_spore_description
from cornice.resource import resource, view
from cornice.service import Service, get_services
from openprocurement.api import VERSION
from openprocurement.api.models import TenderDocument, Bid, Award
from schematics.exceptions import ModelValidationError, ModelConversionError
from uuid import uuid4


spore = Service(name='spore', path='/spore', renderer='json')
auction = Service(name='Tender Auction', path='/tenders/{tender_id}/auction', renderer='json')


def validate_tender_data(request):
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


def validate_bid_data(request):
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
        Bid(data).validate()
    except (ModelValidationError, ModelConversionError), e:
        for i in e.message:
            request.errors.add('body', i, e.message[i])
        request.errors.status = 422


def validate_award_data(request):
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
        Award(data).validate()
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
    return generate_spore_description(services, 'Service name', request.application_url, VERSION)


@resource(name='Tender',
          collection_path='/tenders',
          path='/tenders/{id}',
          description="Open Contracting compatible data exchange format. See http://ocds.open-contracting.org/standard/r/master/#tender for more info")
class TenderResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

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
        # limit, skip, descending
        results = TenderDocument.view(self.db, 'tenders/all')
        return {'data': [i.serialize("listing") for i in results]}

    @view(content_type="application/json", validators=(validate_tender_data,))
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
                    "clarificationPeriod": {
                        "endDate": "2014-10-31T00:00:00"
                    },
                    "tenderPeriod": {
                        "endDate": "2014-11-06T10:00:00"
                    },
                    "awardPeriod": {
                        "endDate": "2014-11-13T00:00:00"
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
                    "clarificationPeriod": {
                        "endDate": "2014-10-31T00:00:00"
                    },
                    "tenderPeriod": {
                        "endDate": "2014-11-06T10:00:00"
                    },
                    "awardPeriod": {
                        "endDate": "2014-11-13T00:00:00"
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
                    "tenderID": "UA-2014-DUS-156",
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
                    "clarificationPeriod": {
                        "endDate": "2014-10-31T00:00:00"
                    },
                    "tenderPeriod": {
                        "endDate": "2014-11-06T10:00:00"
                    },
                    "awardPeriod": {
                        "endDate": "2014-11-13T00:00:00"
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

    @view(content_type="application/json", validators=(validate_tender_data,))
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
        return {'data': tender.serialize("view")}

    @view(content_type="application/json", validators=(validate_tender_data,))
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
                    "tenderID": "UA-2014-DUS-156",
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
        tender_data = filter_data(self.request.json_body['data'])
        if tender_data:
            if 'tenderID' not in tender_data:
                tender_data['tenderID'] = tender.tenderID
            try:
                tender.import_data(tender_data)
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
        self.request.response.headers['Location'] = self.request.route_url(
            'Tender Documents', tender_id=self.tender_id, id=data.filename)
        return {'documents': tender['_attachments']}

    def get(self):
        """Tender Document Read"""
        data = self.db.get_attachment(
            self.tender_id, self.request.matchdict['id'])
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


@resource(name='Tender Bids',
          collection_path='/tenders/{tender_id}/bidders',
          path='/tenders/{tender_id}/bidders/{id}',
          description="Tender bidders")
class TenderBidderResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db
        self.tender_id = request.matchdict['tender_id']

    @view(content_type="application/json", validators=(validate_bid_data,))
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
        bid_data = filter_data(
            self.request.json_body['data'], fields=['id', 'date'])
        bid = Bid(bid_data)
        tender.bids.append(bid)
        try:
            tender.store(self.db)
        except Exception, e:
            return self.request.errors.add('body', 'data', str(e))
        self.request.response.status = 201
        # self.request.response.headers['Location'] = self.request.route_url('Tender Bids', tender_id=self.tender_id, id=bid['id'])
        return {'data': bid.serialize("view")}


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

    def collection_post(self):
        """Tender Bid Document Upload
        """
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
        for data in self.request.POST.values():
            try:
                self.db.put_attachment(tender._data, data.file, data.filename)
            except Exception, e:
                return self.request.errors.add('body', 'data', str(e))
        tender = tender.reload(self.db)
        self.request.response.status = 201
        # self.request.response.headers['Location'] = self.request.route_url('Tender Bid Documents', tender_id=self.tender_id, bid_id=self.bid_id, id=data.filename)
        return {'documents': tender['_attachments']}


@resource(name='Tender Awards',
          collection_path='/tenders/{tender_id}/awards',
          path='/tenders/{tender_id}/awards/{id}',
          description="Tender awards")
class TenderAwardResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db
        self.tender_id = request.matchdict['tender_id']

    @view(content_type="application/json", validators=(validate_award_data,))
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
        award_data = self.request.json_body['data']
        award = Award(award_data)
        tender.awards.append(award)
        try:
            tender.store(self.db)
        except Exception, e:
            return self.request.errors.add('body', 'data', str(e))
        self.request.response.status = 201
        # self.request.response.headers['Location'] = self.request.route_url('Tender Bids', tender_id=self.tender_id, id=award['awardID'])
        return {'data': award.serialize("view")}


@auction.get()
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
                        "amount": 500,
                        "currency": "UAH"
                    },
                    {
                        "amount": 485,
                        "currency": "UAH"
                    }
                ],
                "minimalStep":{
                    "amount": 35,
                    "currency": "UAH"
                },
                "period":{
                    "startDate": "2014-11-06T12:00:00"
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
    auction_info["minimalStep"] = {
        "amount": 35,
        "currency": "UAH"
    }
    return {'data': auction_info}


@auction.patch(content_type="application/json", validators=(validate_tender_data,))
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
                        "amount": 400,
                        "currency": "UAH"
                    },
                    {
                        "amount": 385,
                        "currency": "UAH"
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
                        "amount": 400,
                        "currency": "UAH"
                    },
                    {
                        "amount": 385,
                        "currency": "UAH"
                    }
                ],
                "minimalStep":{
                    "amount": 35,
                    "currency": "UAH"
                },
                "period":{
                    "startDate": "2014-11-06T12:00:00"
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
    auction_data = filter_data(request.json_body['data'])
    try:
        tender.import_data(auction_data)
        tender.store(db)
    except Exception, e:
        return request.errors.add('body', 'data', str(e))
    return {'data': tender.serialize("auction")}
