# -*- coding: utf-8 -*-
from cornice.resource import resource, view
from openprocurement.api.models import Complaint, STAND_STILL_TIME, get_now
from openprocurement.api.utils import (
    apply_data_patch,
    save_tender,
)
from openprocurement.api.validation import (
    validate_complaint_data,
    validate_patch_complaint_data,
)


@resource(name='Tender Complaints',
          collection_path='/tenders/{tender_id}/complaints',
          path='/tenders/{tender_id}/complaints/{complaint_id}',
          description="Tender complaints")
class TenderComplaintResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @view(content_type="application/json", validators=(validate_complaint_data,), permission='create_tender', renderer='json')
    def collection_post(self):
        """Post a complaint
        """
        tender = self.request.validated['tender']
        if tender.status != 'active.enquiries':
            self.request.errors.add('body', 'data', 'Can\'t add complaint in current tender status')
            self.request.errors.status = 403
            return
        complaint_data = self.request.validated['data']
        complaint = Complaint(complaint_data)
        src = tender.serialize("plain")
        tender.complaints.append(complaint)
        save_tender(tender, src, self.request)
        self.request.response.status = 201
        self.request.response.headers['Location'] = self.request.route_url('Tender Complaints', tender_id=tender.id, complaint_id=complaint['id'])
        return {'data': complaint.serialize("view")}

    @view(renderer='json', permission='view_tender')
    def collection_get(self):
        """List complaints
        """
        return {'data': [i.serialize("view") for i in self.request.validated['tender'].complaints]}

    @view(renderer='json', permission='view_tender')
    def get(self):
        """Retrieving the complaint
        """
        return {'data': self.request.validated['complaint'].serialize("view")}

    @view(content_type="application/json", validators=(validate_patch_complaint_data,), permission='review_complaint', renderer='json')
    def patch(self):
        """Post a complaint resolution
        """
        tender = self.request.validated['tender']
        if tender.status not in ['active.enquiries', 'active.tendering', 'active.auction', 'active.qualification', 'active.awarded']:
            self.request.errors.add('body', 'data', 'Can\'t update complaint in current tender status')
            self.request.errors.status = 403
            return
        complaint = self.request.validated['complaint']
        if complaint.status != 'pending':
            self.request.errors.add('body', 'data', 'Can\'t update complaint in current status')
            self.request.errors.status = 403
            return
        complaint_data = self.request.validated['data']
        if complaint_data:
            if complaint_data.get('status', '') == 'cancelled':
                self.request.errors.add('body', 'data', 'Can\'t cancel complaint')
                self.request.errors.status = 403
                return
            src = tender.serialize("plain")
            complaint.import_data(apply_data_patch(complaint.serialize(), complaint_data))
            if complaint.status == 'resolved' and tender.status != 'active.enquiries':
                for i in tender.complaints:
                    if i.status == 'pending':
                        i.status = 'cancelled'
                tender.status = 'cancelled'
            elif complaint.status in ['declined', 'invalid'] and tender.status == 'active.awarded':
                pending_complaints = [
                    i
                    for i in tender.complaints
                    if i.status == 'pending'
                ]
                pending_awards_complaints = [
                    i
                    for a in tender.awards
                    for i in a.complaints
                    if i.status == 'pending'
                ]
                stand_still_time_expired = tender.awardPeriod.endDate + STAND_STILL_TIME < get_now()
                if not pending_complaints and not pending_awards_complaints and stand_still_time_expired:
                    active_awards = [
                        a
                        for a in tender.awards
                        if a.status == 'active'
                    ]
                    if active_awards:
                        tender.status = 'complete'
                    else:
                        tender.status = 'unsuccessful'
            save_tender(tender, src, self.request)
        return {'data': complaint.serialize("view")}
