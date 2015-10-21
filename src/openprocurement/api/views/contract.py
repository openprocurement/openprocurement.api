# -*- coding: utf-8 -*-
from logging import getLogger
from openprocurement.api.models import Contract, get_now
from openprocurement.api.utils import (
    apply_patch,
    save_tender,
    check_tender_status,
    opresource,
    json_view,
)
from openprocurement.api.validation import (
    validate_contract_data,
    validate_patch_contract_data,
)


LOGGER = getLogger(__name__)


@opresource(name='Tender Contracts',
            collection_path='/tenders/{tender_id}/contracts',
            path='/tenders/{tender_id}/contracts/{contract_id}',
            description="Tender contracts")
class TenderAwardContractResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @json_view(content_type="application/json", permission='create_contract', validators=(validate_contract_data,))
    def collection_post(self):
        """Post a contract for award
        """
        tender = self.request.validated['tender']
        if tender.status not in ['active.awarded', 'complete']:
            self.request.errors.add('body', 'data', 'Can\'t add contract in current ({}) tender status'.format(tender.status))
            self.request.errors.status = 403
            return
        contract_data = self.request.validated['data']
        contract = Contract(contract_data)
        contract.__parent__ = self.request.context
        tender.contracts.append(contract)
        if save_tender(self.request):
            update_logging_context({'contract_id': contract.id})
            LOGGER.info('Created tender contract {}'.format(contract.id), extra={'MESSAGE_ID': 'tender_contract_create'})
            self.request.response.status = 201
            self.request.response.headers['Location'] = self.request.route_url('Tender Contracts', tender_id=tender.id, contract_id=contract['id'])
            return {'data': contract.serialize()}

    @json_view(permission='view_tender')
    def collection_get(self):
        """List contracts for award
        """
        return {'data': [i.serialize() for i in self.request.context.contracts]}

    @json_view(permission='view_tender')
    def get(self):
        """Retrieving the contract for award
        """
        return {'data': self.request.validated['contract'].serialize()}

    @json_view(content_type="application/json", permission='edit_tender', validators=(validate_patch_contract_data,))
    def patch(self):
        """Update of contract
        """
        if self.request.validated['tender_status'] not in ['active.awarded', 'complete']:
            self.request.errors.add('body', 'data', 'Can\'t update contract in current ({}) tender status'.format(self.request.validated['tender_status']))
            self.request.errors.status = 403
        data = self.request.validated['data']
        if self.request.context.status != 'active' and 'status' in data and data['status'] == 'active':
            tender = self.request.validated['tender']
            award = [a for a in tender.awards if a.id == self.request.context.awardID][0]
            stand_still_end = award.complaintPeriod.endDate
            if stand_still_end > get_now():
                self.request.errors.add('body', 'data', 'Can\'t sign contract before stand-still period end ({})'.format(stand_still_end.isoformat()))
                self.request.errors.status = 403
                return
            pending_complaints = [
                i
                for i in tender.complaints
                if i.status == 'pending'
            ]
            pending_awards_complaints = [
                i
                for a in tender.awards
                for i in a.complaints
                if i.status == 'pending' and a.lotID == award.lotID
            ]
            if pending_complaints or pending_awards_complaints:
                self.request.errors.add('body', 'data', 'Can\'t sign contract before reviewing all complaints')
                self.request.errors.status = 403
                return
        apply_patch(self.request, save=False, src=self.request.context.serialize())
        check_tender_status(self.request)
        if save_tender(self.request):
            LOGGER.info('Updated tender contract {}'.format(self.request.context.id), extra={'MESSAGE_ID': 'tender_contract_patch'})
            return {'data': self.request.context.serialize()}
