# -*- coding: utf-8 -*-
from logging import getLogger
from openprocurement.api.utils import (
    apply_patch,
    save_auction,
    check_auction_status,
    opresource,
    json_view,
    context_unpack,
)
from openprocurement.api.validation import (
    validate_cancellation_data,
    validate_patch_cancellation_data,
)


LOGGER = getLogger(__name__)


@opresource(name='Auction Cancellations',
            collection_path='/auctions/{auction_id}/cancellations',
            path='/auctions/{auction_id}/cancellations/{cancellation_id}',
            description="Auction cancellations")
class AuctionCancellationResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @json_view(content_type="application/json", validators=(validate_cancellation_data,), permission='edit_auction')
    def collection_post(self):
        """Post a cancellation
        """
        auction = self.request.validated['auction']
        if auction.status in ['complete', 'cancelled', 'unsuccessful']:
            self.request.errors.add('body', 'data', 'Can\'t add cancellation in current ({}) auction status'.format(auction.status))
            self.request.errors.status = 403
            return
        cancellation = self.request.validated['cancellation']
        if any([i.status != 'active' for i in auction.lots if i.id == cancellation.relatedLot]):
            self.request.errors.add('body', 'data', 'Can add cancellation only in active lot status')
            self.request.errors.status = 403
            return
        if cancellation.relatedLot and cancellation.status == 'active':
            [setattr(i, 'status', 'cancelled') for i in auction.lots if i.id == cancellation.relatedLot]
            check_auction_status(self.request)
        elif cancellation.status == 'active':
            auction.status = 'cancelled'
        auction.cancellations.append(cancellation)
        if save_auction(self.request):
            LOGGER.info('Created auction cancellation {}'.format(cancellation.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'auction_cancellation_create'}, {'cancellation_id': cancellation.id}))
            self.request.response.status = 201
            self.request.response.headers['Location'] = self.request.route_url('Auction Cancellations', auction_id=auction.id, cancellation_id=cancellation.id)
            return {'data': cancellation.serialize("view")}

    @json_view(permission='view_auction')
    def collection_get(self):
        """List cancellations
        """
        return {'data': [i.serialize("view") for i in self.request.validated['auction'].cancellations]}

    @json_view(permission='view_auction')
    def get(self):
        """Retrieving the cancellation
        """
        return {'data': self.request.validated['cancellation'].serialize("view")}

    @json_view(content_type="application/json", validators=(validate_patch_cancellation_data,), permission='edit_auction')
    def patch(self):
        """Post a cancellation resolution
        """
        auction = self.request.validated['auction']
        if auction.status in ['complete', 'cancelled', 'unsuccessful']:
            self.request.errors.add('body', 'data', 'Can\'t update cancellation in current ({}) auction status'.format(auction.status))
            self.request.errors.status = 403
            return
        if any([i.status != 'active' for i in auction.lots if i.id == self.request.context.relatedLot]):
            self.request.errors.add('body', 'data', 'Can update cancellation only in active lot status')
            self.request.errors.status = 403
            return
        apply_patch(self.request, save=False, src=self.request.context.serialize())
        if self.request.context.relatedLot and self.request.context.status == 'active':
            [setattr(i, 'status', 'cancelled') for i in auction.lots if i.id == self.request.context.relatedLot]
            check_auction_status(self.request)
        elif self.request.context.status == 'active':
            auction.status = 'cancelled'
        if save_auction(self.request):
            LOGGER.info('Updated auction cancellation {}'.format(self.request.context.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'auction_cancellation_patch'}))
            return {'data': self.request.context.serialize("view")}
