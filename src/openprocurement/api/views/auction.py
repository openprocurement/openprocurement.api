# -*- coding: utf-8 -*-
from logging import getLogger
from cornice.service import Service
from openprocurement.api.utils import (
    save_tender,
    apply_patch,
    add_next_award,
    error_handler,
)
from openprocurement.api.validation import (
    validate_tender_auction_data,
)


LOGGER = getLogger(__name__)


auction = Service(name='Tender Auction',
                  path='/tenders/{tender_id}/auction',
                  renderer='json',
                  error_handler=error_handler)


@auction.get(renderer='json', permission='auction')
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
    if request.validated['tender_status'] != 'active.auction':
        request.errors.add('body', 'data', 'Can\'t get auction info in current ({}) tender status'.format(request.validated['tender_status']))
        request.errors.status = 403
        return
    return {'data': request.validated['tender'].serialize("auction_view")}


@auction.patch(content_type="application/json", permission='auction', validators=(validate_tender_auction_data), renderer='json')
def patch_auction(request):
    """Set urls for access to auction.
    """
    if apply_patch(request, src=request.validated['tender_src']):
        LOGGER.info('Updated auction urls', extra={'MESSAGE_ID': 'tender_auction_patch'})
        return {'data': request.validated['tender'].serialize("auction_view")}


@auction.post(content_type="application/json", permission='auction', validators=(validate_tender_auction_data), renderer='json')
def post_auction(request):
    """Report auction results.

    Report auction results
    ----------------------

    Example request to report auction results:

    .. sourcecode:: http

        POST /tenders/4879d3f8ee2443169b5fbbc9f89fa607/auction HTTP/1.1
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
    apply_patch(request, save=False, src=request.validated['tender_src'])
    add_next_award(request)
    if save_tender(request):
        LOGGER.info('Report auction results', extra={'MESSAGE_ID': 'tender_auction_post'})
        return {'data': request.context.serialize(request.context.status)}
