# -*- coding: utf-8 -*-
from logging import getLogger
from openprocurement.api.models import get_now
from openprocurement.api.utils import (
    apply_patch,
    save_auction,
    check_auction_status,
    opresource,
    json_view,
    context_unpack,
)
from openprocurement.api.validation import (
    validate_contract_data,
    validate_patch_contract_data,
)


LOGGER = getLogger(__name__)


@opresource(name='Auction Contracts',
            collection_path='/auctions/{auction_id}/contracts',
            path='/auctions/{auction_id}/contracts/{contract_id}',
            description="Auction contracts")
class AuctionAwardContractResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @json_view(content_type="application/json", permission='create_contract', validators=(validate_contract_data,))
    def collection_post(self):
        """Post a contract for award
        """
        auction = self.request.validated['auction']
        if auction.status not in ['active.awarded', 'complete']:
            self.request.errors.add('body', 'data', 'Can\'t add contract in current ({}) auction status'.format(auction.status))
            self.request.errors.status = 403
            return
        contract = self.request.validated['contract']
        auction.contracts.append(contract)
        if save_auction(self.request):
            LOGGER.info('Created auction contract {}'.format(contract.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'auction_contract_create'}, {'contract_id': contract.id}))
            self.request.response.status = 201
            self.request.response.headers['Location'] = self.request.route_url('Auction Contracts', auction_id=auction.id, contract_id=contract['id'])
            return {'data': contract.serialize()}

    @json_view(permission='view_auction')
    def collection_get(self):
        """List contracts for award
        """
        return {'data': [i.serialize() for i in self.request.context.contracts]}

    @json_view(permission='view_auction')
    def get(self):
        """Retrieving the contract for award
        """
        return {'data': self.request.validated['contract'].serialize()}

    @json_view(content_type="application/json", permission='edit_auction', validators=(validate_patch_contract_data,))
    def patch(self):
        """Update of contract
        """
        if self.request.validated['auction_status'] not in ['active.awarded', 'complete']:
            self.request.errors.add('body', 'data', 'Can\'t update contract in current ({}) auction status'.format(self.request.validated['auction_status']))
            self.request.errors.status = 403
        data = self.request.validated['data']
        if self.request.context.status != 'active' and 'status' in data and data['status'] == 'active':
            auction = self.request.validated['auction']
            award = [a for a in auction.awards if a.id == self.request.context.awardID][0]
            stand_still_end = award.complaintPeriod.endDate
            if stand_still_end > get_now():
                self.request.errors.add('body', 'data', 'Can\'t sign contract before stand-still period end ({})'.format(stand_still_end.isoformat()))
                self.request.errors.status = 403
                return
            pending_complaints = [
                i
                for i in auction.complaints
                if i.status == 'pending'
            ]
            pending_awards_complaints = [
                i
                for a in auction.awards
                for i in a.complaints
                if i.status == 'pending' and a.lotID == award.lotID
            ]
            if pending_complaints or pending_awards_complaints:
                self.request.errors.add('body', 'data', 'Can\'t sign contract before reviewing all complaints')
                self.request.errors.status = 403
                return
        contract_status = self.request.context.status
        apply_patch(self.request, save=False, src=self.request.context.serialize())
        if contract_status != self.request.context.status and contract_status != 'pending' and self.request.context.status != 'active':
            self.request.errors.add('body', 'data', 'Can\'t update contract status')
            self.request.errors.status = 403
            return
        check_auction_status(self.request)
        if save_auction(self.request):
            LOGGER.info('Updated auction contract {}'.format(self.request.context.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'auction_contract_patch'}))
            return {'data': self.request.context.serialize()}
