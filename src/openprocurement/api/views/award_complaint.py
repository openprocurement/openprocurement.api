# -*- coding: utf-8 -*-
from logging import getLogger
from openprocurement.api.models import STAND_STILL_TIME, get_now
from openprocurement.api.utils import (
    apply_patch,
    save_auction,
    add_next_award,
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


@opresource(name='Auction Award Complaints',
            collection_path='/auctions/{auction_id}/awards/{award_id}/complaints',
            path='/auctions/{auction_id}/awards/{award_id}/complaints/{complaint_id}',
            description="Auction award complaints")
class AuctionAwardComplaintResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @json_view(content_type="application/json", permission='create_award_complaint', validators=(validate_complaint_data,))
    def collection_post(self):
        """Post a complaint for award
        """
        auction = self.request.validated['auction']
        if auction.status not in ['active.qualification', 'active.awarded']:
            self.request.errors.add('body', 'data', 'Can\'t add complaint in current ({}) auction status'.format(auction.status))
            self.request.errors.status = 403
            return
        if any([i.status != 'active' for i in auction.lots if i.id == self.request.context.lotID]):
            self.request.errors.add('body', 'data', 'Can add complaint only in active lot status')
            self.request.errors.status = 403
            return
        if self.request.context.complaintPeriod and \
           (self.request.context.complaintPeriod.startDate and self.request.context.complaintPeriod.startDate > get_now() or
                self.request.context.complaintPeriod.endDate and self.request.context.complaintPeriod.endDate < get_now()):
            self.request.errors.add('body', 'data', 'Can add complaint only in complaintPeriod')
            self.request.errors.status = 403
            return
        complaint = self.request.validated['complaint']
        self.request.context.complaints.append(complaint)
        if save_auction(self.request):
            LOGGER.info('Created auction award complaint {}'.format(complaint.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'auction_award_complaint_create'}, {'complaint_id': complaint.id}))
            self.request.response.status = 201
            self.request.response.headers['Location'] = self.request.route_url('Auction Award Complaints', auction_id=auction.id, award_id=self.request.validated['award_id'], complaint_id=complaint['id'])
            return {'data': complaint.serialize("view")}

    @json_view(permission='view_auction')
    def collection_get(self):
        """List complaints for award
        """
        return {'data': [i.serialize("view") for i in self.request.context.complaints]}

    @json_view(permission='view_auction')
    def get(self):
        """Retrieving the complaint for award
        """
        return {'data': self.request.validated['complaint'].serialize("view")}

    @json_view(content_type="application/json", permission='review_complaint', validators=(validate_patch_complaint_data,))
    def patch(self):
        """Post a complaint resolution for award
        """
        auction = self.request.validated['auction']
        if auction.status not in ['active.qualification', 'active.awarded']:
            self.request.errors.add('body', 'data', 'Can\'t update complaint in current ({}) auction status'.format(auction.status))
            self.request.errors.status = 403
            return
        if any([i.status != 'active' for i in auction.lots if i.id == self.request.validated['award'].lotID]):
            self.request.errors.add('body', 'data', 'Can update complaint only in active lot status')
            self.request.errors.status = 403
            return
        complaint = self.request.context
        if complaint.status != 'pending':
            self.request.errors.add('body', 'data', 'Can\'t update complaint in current ({}) status'.format(complaint.status))
            self.request.errors.status = 403
            return
        if self.request.validated['data'].get('status', complaint.status) == 'cancelled':
            self.request.errors.add('body', 'data', 'Can\'t cancel complaint')
            self.request.errors.status = 403
            return
        apply_patch(self.request, save=False, src=complaint.serialize())
        if complaint.status == 'resolved':
            award = self.request.validated['award']
            if auction.status == 'active.awarded':
                auction.status = 'active.qualification'
                auction.awardPeriod.endDate = None
            now = get_now()
            if award.status == 'unsuccessful':
                for i in auction.awards[auction.awards.index(award):]:
                    if i.lotID != award.lotID:
                        continue
                    i.complaintPeriod.endDate = now + STAND_STILL_TIME
                    i.status = 'cancelled'
                    for j in i.complaints:
                        if j.status == 'pending':
                            j.status = 'cancelled'
            for i in auction.contracts:
                if award.id == i.awardID:
                    i.status = 'cancelled'
            award.complaintPeriod.endDate = now + STAND_STILL_TIME
            award.status = 'cancelled'
            add_next_award(self.request)
        elif complaint.status in ['declined', 'invalid'] and auction.status == 'active.awarded':
            check_auction_status(self.request)
        if save_auction(self.request):
            LOGGER.info('Updated auction award complaint {}'.format(self.request.context.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'auction_award_complaint_patch'}))
            return {'data': complaint.serialize("view")}
