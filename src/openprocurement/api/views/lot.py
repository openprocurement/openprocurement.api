# -*- coding: utf-8 -*-
from logging import getLogger
from openprocurement.api.utils import (
    apply_patch,
    save_auction,
    opresource,
    json_view,
    context_unpack,
)
from openprocurement.api.validation import (
    validate_lot_data,
    validate_patch_lot_data,
)


LOGGER = getLogger(__name__)


@opresource(name='Auction Lots',
            collection_path='/auctions/{auction_id}/lots',
            path='/auctions/{auction_id}/lots/{lot_id}',
            description="Auction lots")
class AuctionLotResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @json_view(content_type="application/json", validators=(validate_lot_data,), permission='edit_auction')
    def collection_post(self):
        """Add a lot
        """
        auction = self.request.validated['auction']
        if auction.status not in ['active.enquiries']:
            self.request.errors.add('body', 'data', 'Can\'t add lot in current ({}) auction status'.format(auction.status))
            self.request.errors.status = 403
            return
        lot = self.request.validated['lot']
        auction.lots.append(lot)
        if save_auction(self.request):
            LOGGER.info('Created auction lot {}'.format(lot.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'auction_lot_create'}, {'lot_id': lot.id}))
            self.request.response.status = 201
            self.request.response.headers['Location'] = self.request.route_url('Auction Lots', auction_id=auction.id, lot_id=lot.id)
            return {'data': lot.serialize("view")}

    @json_view(permission='view_auction')
    def collection_get(self):
        """Lots Listing
        """
        return {'data': [i.serialize("view") for i in self.request.validated['auction'].lots]}

    @json_view(permission='view_auction')
    def get(self):
        """Retrieving the lot
        """
        return {'data': self.request.context.serialize("view")}

    @json_view(content_type="application/json", validators=(validate_patch_lot_data,), permission='edit_auction')
    def patch(self):
        """Update of lot
        """
        auction = self.request.validated['auction']
        if auction.status not in ['active.enquiries']:
            self.request.errors.add('body', 'data', 'Can\'t update lot in current ({}) auction status'.format(auction.status))
            self.request.errors.status = 403
            return
        if apply_patch(self.request, src=self.request.context.serialize()):
            LOGGER.info('Updated auction lot {}'.format(self.request.context.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'auction_lot_patch'}))
            return {'data': self.request.context.serialize("view")}

    @json_view(permission='edit_auction')
    def delete(self):
        """Lot deleting
        """
        auction = self.request.validated['auction']
        if auction.status not in ['active.enquiries']:
            self.request.errors.add('body', 'data', 'Can\'t delete lot in current ({}) auction status'.format(auction.status))
            self.request.errors.status = 403
            return
        lot = self.request.context
        res = lot.serialize("view")
        auction.lots.remove(lot)
        if save_auction(self.request):
            LOGGER.info('Deleted auction lot {}'.format(self.request.context.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'auction_lot_delete'}))
            return {'data': res}
