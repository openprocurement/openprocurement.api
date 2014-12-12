# -*- coding: utf-8 -*-
from cornice.resource import resource, view
from openprocurement.api.models import Contract
from openprocurement.api.utils import (
    apply_data_patch,
    save_tender,
)
from openprocurement.api.validation import (
    validate_contract_data,
    validate_patch_contract_data,
)


@resource(name='Tender Award Contracts',
          collection_path='/tenders/{tender_id}/awards/{award_id}/contracts',
          path='/tenders/{tender_id}/awards/{award_id}/contracts/{contract_id}',
          description="Tender award contracts")
class TenderAwardContractResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @view(content_type="application/json", permission='create_award_contract', validators=(validate_contract_data,), renderer='json')
    def collection_post(self):
        """Post a contract for award
        """
        tender = self.request.validated['tender']
        if tender.status not in ['active.awarded', 'complete']:
            self.request.errors.add('body', 'data', 'Can\'t add contract in current tender status')
            self.request.errors.status = 403
            return
        contract_data = self.request.validated['data']
        contract = Contract(contract_data)
        contract.awardID = self.request.validated['award_id']
        src = tender.serialize("plain")
        self.request.validated['award'].contracts.append(contract)
        save_tender(tender, src, self.request)
        self.request.response.status = 201
        self.request.response.headers['Location'] = self.request.route_url('Tender Award Contracts', tender_id=tender.id, award_id=self.request.validated['award_id'], contract_id=contract['id'])
        return {'data': contract.serialize()}

    @view(renderer='json', permission='view_tender')
    def collection_get(self):
        """List contracts for award
        """
        return {'data': [i.serialize() for i in self.request.validated['award'].contracts]}

    @view(renderer='json', permission='view_tender')
    def get(self):
        """Retrieving the contract for award
        """
        return {'data': self.request.validated['contract'].serialize()}

    @view(content_type="application/json", permission='edit_tender', validators=(validate_patch_contract_data,), renderer='json')
    def patch(self):
        """Update of contract
        """
        tender = self.request.validated['tender']
        if tender.status not in ['active.awarded', 'complete']:
            self.request.errors.add('body', 'data', 'Can\'t update contract in current tender status')
            self.request.errors.status = 403
            return
        contract = self.request.validated['contract']
        contract_data = self.request.validated['data']
        if contract_data:
            src = tender.serialize("plain")
            contract.import_data(apply_data_patch(contract.serialize(), contract_data))
            save_tender(tender, src, self.request)
        return {'data': contract.serialize()}
