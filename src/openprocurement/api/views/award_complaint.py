# -*- coding: utf-8 -*-
from cornice.resource import resource, view
from openprocurement.api.models import Complaint
from openprocurement.api.utils import (
    apply_data_patch,
    filter_data,
    save_tender,
)
from openprocurement.api.validation import (
    validate_complaint_data,
    validate_patch_complaint_data,
    validate_tender_award_complaint_exists,
    validate_tender_award_exists_by_award_id,
)


@resource(name='Tender Award Complaints',
          collection_path='/tenders/{tender_id}/awards/{award_id}/complaints',
          path='/tenders/{tender_id}/awards/{award_id}/complaints/{id}',
          description="Tender award complaints")
class TenderAwardComplaintResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @view(content_type="application/json", validators=(validate_complaint_data, validate_tender_award_exists_by_award_id), renderer='json')
    def collection_post(self):
        """Post a complaint for award
        """
        tender = self.request.validated['tender']
        if tender.status not in ['active.qualification', 'active.awarded']:
            self.request.errors.add('body', 'data', 'Can\'t add complaint in current tender status')
            self.request.errors.status = 403
            return
        complaint_data = filter_data(self.request.validated['data'])
        complaint = Complaint(complaint_data)
        src = tender.serialize("plain")
        self.request.validated['award'].complaints.append(complaint)
        save_tender(tender, src, self.request)
        self.request.response.status = 201
        self.request.response.headers['Location'] = self.request.route_url('Tender Award Complaints', tender_id=tender.id, award_id=self.request.validated['award_id'], id=complaint['id'])
        return {'data': complaint.serialize("view")}

    @view(renderer='json', validators=(validate_tender_award_exists_by_award_id,))
    def collection_get(self):
        """List complaints for award
        """
        return {'data': [i.serialize("view") for i in self.request.validated['award'].complaints]}

    @view(renderer='json', validators=(validate_tender_award_complaint_exists,))
    def get(self):
        """Retrieving the complaint for award
        """
        return {'data': self.request.validated['complaint'].serialize("view")}

    @view(content_type="application/json", validators=(validate_patch_complaint_data, validate_tender_award_complaint_exists), renderer='json')
    def patch(self):
        """Post a complaint resolution for award
        """
        tender = self.request.validated['tender']
        if tender.status not in ['active.qualification', 'active.awarded']:
            self.request.errors.add('body', 'data', 'Can\'t update complaint in current tender status')
            self.request.errors.status = 403
            return
        complaint = self.request.validated['complaint']
        complaint_data = filter_data(self.request.validated['data'])
        if complaint_data:
            src = tender.serialize("plain")
            complaint.import_data(apply_data_patch(complaint.serialize(), complaint_data))
            save_tender(tender, src, self.request)
        return {'data': complaint.serialize("view")}
