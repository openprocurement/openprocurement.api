# -*- coding: utf-8 -*-
from cornice.resource import resource, view
from openprocurement.api.models import Bid
from openprocurement.api.utils import (
    apply_data_patch,
    save_tender,
)
from openprocurement.api.validation import (
    validate_bid_data,
    validate_patch_bid_data,
)


@resource(name='Tender Bids',
          collection_path='/tenders/{tender_id}/bids',
          path='/tenders/{tender_id}/bids/{bid_id}',
          description="Tender bids")
class TenderBidResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @view(content_type="application/json", permission='view_tender', validators=(validate_bid_data,), renderer='json')
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
        if tender.status != 'active.tendering':
            self.request.errors.add('body', 'data', 'Can\'t add bid in current tender status')
            self.request.errors.status = 403
            return
        bid_data = self.request.validated['data']
        bid = Bid(bid_data)
        src = tender.serialize("plain")
        tender.bids.append(bid)
        save_tender(tender, src, self.request)
        self.request.response.status = 201
        self.request.response.headers['Location'] = self.request.route_url('Tender Bids', tender_id=tender.id, bid_id=bid['id'])
        return {'data': bid.serialize("view")}

    @view(renderer='json', permission='view_tender')
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
        if tender.status in ['active.enquiries', 'active.tendering']:
            return {'data': []}
        return {'data': [i.serialize(tender.status) for i in tender.bids]}

    @view(renderer='json', permission='view_tender')
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
        if tender.status in ['active.enquiries', 'active.tendering']:
            return {'data': {}}
        bid_data = self.request.validated['bid'].serialize(tender.status)
        if tender.status in ['active.auction', 'active.qualification', 'active.awarded', 'complete']:
            # auction participation url
            bid_data['participationUrl'] = 'http://auction-sandbox.openprocurement.org/tenders/{}?bidder_id={}'.format(tender.id, self.request.validated['id'])
        return {'data': bid_data}

    @view(content_type="application/json", permission='view_tender', validators=(validate_patch_bid_data,), renderer='json')
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
        if tender.status != 'active.tendering':
            self.request.errors.add('body', 'data', 'Can\'t update bid in current tender status')
            self.request.errors.status = 403
            return
        bid = self.request.validated['bid']
        bid_data = self.request.validated['data']
        if bid_data:
            src = tender.serialize("plain")
            bid.import_data(apply_data_patch(bid.serialize(), bid_data))
            save_tender(tender, src, self.request)
        return {'data': bid.serialize("view")}

    @view(renderer='json', permission='view_tender')
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
        if tender.status != 'active.tendering':
            self.request.errors.add('body', 'data', 'Can\'t delete bid in current tender status')
            self.request.errors.status = 403
            return
        src = tender.serialize("plain")
        res = bid.serialize("view")
        tender.bids.remove(bid)
        save_tender(tender, src, self.request)
        return {'data': res}
