# -*- coding: utf-8 -*-
from logging import getLogger
from openprocurement.api.models import get_now
from openprocurement.api.utils import (
    save_auction,
    set_ownership,
    apply_patch,
    opresource,
    json_view,
    context_unpack,
)
from openprocurement.api.validation import (
    validate_bid_data,
    validate_patch_bid_data,
)


LOGGER = getLogger(__name__)


@opresource(name='Auction Bids',
            collection_path='/auctions/{auction_id}/bids',
            path='/auctions/{auction_id}/bids/{bid_id}',
            description="Auction bids")
class AuctionBidResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @json_view(content_type="application/json", permission='create_bid', validators=(validate_bid_data,))
    def collection_post(self):
        """Registration of new bid proposal

        Creating new Bid proposal
        -------------------------

        Example request to create bid proposal:

        .. sourcecode:: http

            POST /auctions/4879d3f8ee2443169b5fbbc9f89fa607/bids HTTP/1.1
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
        auction = self.request.validated['auction']
        if self.request.validated['auction_status'] != 'active.tendering' or auction.tenderPeriod.startDate and get_now() < auction.tenderPeriod.startDate or get_now() > auction.tenderPeriod.endDate:
            self.request.errors.add('body', 'data', 'Can\'t add bid in current ({}) auction status'.format(self.request.validated['auction_status']))
            self.request.errors.status = 403
            return
        bid = self.request.validated['bid']
        set_ownership(bid, self.request)
        auction.bids.append(bid)
        if save_auction(self.request):
            LOGGER.info('Created auction bid {}'.format(bid.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'auction_bid_create'}, {'bid_id': bid.id}))
            self.request.response.status = 201
            self.request.response.headers['Location'] = self.request.route_url('Auction Bids', auction_id=auction.id, bid_id=bid['id'])
            return {
                'data': bid.serialize('view'),
                'access': {
                    'token': bid.owner_token
                }
            }

    @json_view(permission='view_auction')
    def collection_get(self):
        """Bids Listing

        Get Bids List
        -------------

        Example request to get bids list:

        .. sourcecode:: http

            GET /auctions/4879d3f8ee2443169b5fbbc9f89fa607/bids HTTP/1.1
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
        auction = self.request.validated['auction']
        if self.request.validated['auction_status'] in ['active.tendering', 'active.auction']:
            self.request.errors.add('body', 'data', 'Can\'t view bids in current ({}) auction status'.format(self.request.validated['auction_status']))
            self.request.errors.status = 403
            return
        return {'data': [i.serialize(self.request.validated['auction_status']) for i in auction.bids]}

    @json_view(permission='view_auction')
    def get(self):
        """Retrieving the proposal

        Example request for retrieving the proposal:

        .. sourcecode:: http

            GET /auctions/4879d3f8ee2443169b5fbbc9f89fa607/bids/71b6c23ed8944d688e92a31ec8c3f61a HTTP/1.1
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
        if self.request.authenticated_role == 'bid_owner':
            return {'data': self.request.context.serialize('view')}
        if self.request.validated['auction_status'] in ['active.tendering', 'active.auction']:
            self.request.errors.add('body', 'data', 'Can\'t view bid in current ({}) auction status'.format(self.request.validated['auction_status']))
            self.request.errors.status = 403
            return
        return {'data': self.request.context.serialize(self.request.validated['auction_status'])}

    @json_view(content_type="application/json", permission='edit_bid', validators=(validate_patch_bid_data,))
    def patch(self):
        """Update of proposal

        Example request to change bid proposal:

        .. sourcecode:: http

            PATCH /auctions/4879d3f8ee2443169b5fbbc9f89fa607/bids/71b6c23ed8944d688e92a31ec8c3f61a HTTP/1.1
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
        if self.request.authenticated_role != 'Administrator' and self.request.validated['auction_status'] != 'active.tendering':
            self.request.errors.add('body', 'data', 'Can\'t update bid in current ({}) auction status'.format(self.request.validated['auction_status']))
            self.request.errors.status = 403
            return
        value = self.request.validated['data'].get("value") and self.request.validated['data']["value"].get("amount")
        if value and value != self.request.context.get("value", {}).get("amount"):
            self.request.validated['data']['date'] = get_now().isoformat()
        if self.request.context.lotValues:
            lotValues = dict([(i.relatedLot, i.value.amount) for i in self.request.context.lotValues])
            for lotvalue in self.request.validated['data'].get("lotValues", []):
                if lotvalue['relatedLot'] in lotValues and lotvalue.get("value", {}).get("amount") != lotValues[lotvalue['relatedLot']]:
                    lotvalue['date'] = get_now().isoformat()
        if apply_patch(self.request, src=self.request.context.serialize()):
            LOGGER.info('Updated auction bid {}'.format(self.request.context.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'auction_bid_patch'}))
            return {'data': self.request.context.serialize("view")}

    @json_view(permission='edit_bid')
    def delete(self):
        """Cancelling the proposal

        Example request for cancelling the proposal:

        .. sourcecode:: http

            DELETE /auctions/4879d3f8ee2443169b5fbbc9f89fa607/bids/71b6c23ed8944d688e92a31ec8c3f61a HTTP/1.1
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
        bid = self.request.context
        if self.request.validated['auction_status'] != 'active.tendering':
            self.request.errors.add('body', 'data', 'Can\'t delete bid in current ({}) auction status'.format(self.request.validated['auction_status']))
            self.request.errors.status = 403
            return
        res = bid.serialize("view")
        self.request.validated['auction'].bids.remove(bid)
        if save_auction(self.request):
            LOGGER.info('Deleted auction bid {}'.format(self.request.context.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'auction_bid_delete'}))
            return {'data': res}
