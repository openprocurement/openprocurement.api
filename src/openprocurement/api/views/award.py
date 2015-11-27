# -*- coding: utf-8 -*-
from logging import getLogger
from openprocurement.api.models import Contract, STAND_STILL_TIME, get_now
from openprocurement.api.utils import (
    apply_patch,
    save_auction,
    add_next_award,
    opresource,
    json_view,
    context_unpack,
)
from openprocurement.api.validation import (
    validate_award_data,
    validate_patch_award_data,
)


LOGGER = getLogger(__name__)


@opresource(name='Auction Awards',
            collection_path='/auctions/{auction_id}/awards',
            path='/auctions/{auction_id}/awards/{award_id}',
            description="Auction awards")
class AuctionAwardResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @json_view(permission='view_auction')
    def collection_get(self):
        """Auction Awards List

        Get Awards List
        ---------------

        Example request to get awards list:

        .. sourcecode:: http

            GET /auctions/4879d3f8ee2443169b5fbbc9f89fa607/awards HTTP/1.1
            Host: example.com
            Accept: application/json

        This is what one should expect in response:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "data": [
                    {
                        "status": "active",
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
                        "value": {
                            "amount": 489,
                            "currency": "UAH",
                            "valueAddedTaxIncluded": true
                        }
                    }
                ]
            }

        """
        return {'data': [i.serialize("view") for i in self.request.validated['auction'].awards]}

    @json_view(content_type="application/json", permission='create_award', validators=(validate_award_data,))
    def collection_post(self):
        """Accept or reject bidder application

        Creating new Award
        ------------------

        Example request to create award:

        .. sourcecode:: http

            POST /auctions/4879d3f8ee2443169b5fbbc9f89fa607/awards HTTP/1.1
            Host: example.com
            Accept: application/json

            {
                "data": {
                    "status": "active",
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
                    "date": "2014-10-28T11:44:17.947Z",
                    "status": "active",
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
                    "value": {
                        "amount": 489,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": true
                    }
                }
            }

        """
        auction = self.request.validated['auction']
        if auction.status != 'active.qualification':
            self.request.errors.add('body', 'data', 'Can\'t create award in current ({}) auction status'.format(auction.status))
            self.request.errors.status = 403
            return
        award = self.request.validated['award']
        if any([i.status != 'active' for i in auction.lots if i.id == award.lotID]):
            self.request.errors.add('body', 'data', 'Can create award only in active lot status')
            self.request.errors.status = 403
            return
        award.complaintPeriod = {'startDate': get_now().isoformat()}
        auction.awards.append(award)
        if save_auction(self.request):
            LOGGER.info('Created auction award {}'.format(award.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'auction_award_create'}, {'award_id': award.id}))
            self.request.response.status = 201
            self.request.response.headers['Location'] = self.request.route_url('Auction Awards', auction_id=auction.id, award_id=award['id'])
            return {'data': award.serialize("view")}

    @json_view(permission='view_auction')
    def get(self):
        """Retrieving the award

        Example request for retrieving the award:

        .. sourcecode:: http

            GET /auctions/4879d3f8ee2443169b5fbbc9f89fa607/awards/71b6c23ed8944d688e92a31ec8c3f61a HTTP/1.1
            Host: example.com
            Accept: application/json

        And here is the response to be expected:

        .. sourcecode:: http

            HTTP/1.0 200 OK
            Content-Type: application/json

            {
                "data": {
                    "id": "4879d3f8ee2443169b5fbbc9f89fa607",
                    "date": "2014-10-28T11:44:17.947Z",
                    "status": "active",
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
                    "value": {
                        "amount": 489,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": true
                    }
                }
            }

        """
        return {'data': self.request.validated['award'].serialize("view")}

    @json_view(content_type="application/json", permission='edit_auction', validators=(validate_patch_award_data,))
    def patch(self):
        """Update of award

        Example request to change the award:

        .. sourcecode:: http

            PATCH /auctions/4879d3f8ee2443169b5fbbc9f89fa607/awards/71b6c23ed8944d688e92a31ec8c3f61a HTTP/1.1
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
                    "id": "4879d3f8ee2443169b5fbbc9f89fa607",
                    "date": "2014-10-28T11:44:17.947Z",
                    "status": "active",
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
                    "value": {
                        "amount": 600,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": true
                    }
                }
            }

        """
        auction = self.request.validated['auction']
        if auction.status not in ['active.qualification', 'active.awarded']:
            self.request.errors.add('body', 'data', 'Can\'t update award in current ({}) auction status'.format(auction.status))
            self.request.errors.status = 403
            return
        award = self.request.context
        if any([i.status != 'active' for i in auction.lots if i.id == award.lotID]):
            self.request.errors.add('body', 'data', 'Can update award only in active lot status')
            self.request.errors.status = 403
            return
        award_status = award.status
        apply_patch(self.request, save=False, src=self.request.context.serialize())
        if award_status == 'pending' and award.status == 'active':
            award.complaintPeriod.endDate = get_now() + STAND_STILL_TIME
            auction.contracts.append(Contract({'awardID': award.id}))
            add_next_award(self.request)
        elif award_status == 'active' and award.status == 'cancelled':
            award.complaintPeriod.endDate = get_now()
            for i in auction.contracts:
                if i.awardID == award.id:
                    i.status = 'cancelled'
            add_next_award(self.request)
        elif award_status == 'pending' and award.status == 'unsuccessful':
            award.complaintPeriod.endDate = get_now() + STAND_STILL_TIME
            add_next_award(self.request)
        else:
            self.request.errors.add('body', 'data', 'Can\'t update award in current ({}) status'.format(award_status))
            self.request.errors.status = 403
            return
        if save_auction(self.request):
            LOGGER.info('Updated auction award {}'.format(self.request.context.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'auction_award_patch'}, {'TENDER_REV': auction.rev}))
            return {'data': award.serialize("view")}
