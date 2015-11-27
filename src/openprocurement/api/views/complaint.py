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
    validate_complaint_data,
    validate_patch_complaint_data,
)


LOGGER = getLogger(__name__)


@opresource(name='Auction Complaints',
            collection_path='/auctions/{auction_id}/complaints',
            path='/auctions/{auction_id}/complaints/{complaint_id}',
            description="Auction complaints")
class AuctionComplaintResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @json_view(content_type="application/json", validators=(validate_complaint_data,), permission='create_complaint')
    def collection_post(self):
        """Post a complaint
        """
        auction = self.request.validated['auction']
        if auction.status not in ['active.enquiries', 'active.tendering']:
            self.request.errors.add('body', 'data', 'Can\'t add complaint in current ({}) auction status'.format(auction.status))
            self.request.errors.status = 403
            return
        complaint = self.request.validated['complaint']
        auction.complaints.append(complaint)
        if save_auction(self.request):
            LOGGER.info('Created auction complaint {}'.format(complaint.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'auction_complaint_create'}, {'complaint_id': complaint.id}))
            self.request.response.status = 201
            self.request.response.headers['Location'] = self.request.route_url('Auction Complaints', auction_id=auction.id, complaint_id=complaint.id)
            return {'data': complaint.serialize("view")}

    @json_view(permission='view_auction')
    def collection_get(self):
        """List complaints
        """
        return {'data': [i.serialize("view") for i in self.request.context.complaints]}

    @json_view(permission='view_auction')
    def get(self):
        """Retrieving the complaint
        """
        return {'data': self.request.validated['complaint'].serialize("view")}

    @json_view(content_type="application/json", validators=(validate_patch_complaint_data,), permission='review_complaint')
    def patch(self):
        """Post a complaint resolution
        """
        auction = self.request.validated['auction']
        if auction.status not in ['active.enquiries', 'active.tendering', 'active.auction', 'active.qualification', 'active.awarded']:
            self.request.errors.add('body', 'data', 'Can\'t update complaint in current ({}) auction status'.format(auction.status))
            self.request.errors.status = 403
            return
        if self.request.context.status != 'pending':
            self.request.errors.add('body', 'data', 'Can\'t update complaint in current ({}) status'.format(self.request.context.status))
            self.request.errors.status = 403
            return
        if self.request.validated['data'].get('status', self.request.context.status) == 'cancelled':
            self.request.errors.add('body', 'data', 'Can\'t cancel complaint')
            self.request.errors.status = 403
            return
        apply_patch(self.request, save=False, src=self.request.context.serialize())
        if self.request.context.status == 'resolved' and auction.status != 'active.enquiries':
            for i in auction.complaints:
                if i.status == 'pending':
                    i.status = 'cancelled'
            [setattr(i, 'status', 'cancelled') for i in auction.lots]
            auction.status = 'cancelled'
        elif self.request.context.status in ['declined', 'invalid'] and auction.status == 'active.awarded':
            check_auction_status(self.request)
        if save_auction(self.request):
            LOGGER.info('Updated auction complaint {}'.format(self.request.context.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'auction_complaint_patch'}))
            return {'data': self.request.context.serialize("view")}
