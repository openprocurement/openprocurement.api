# -*- coding: utf-8 -*-
from logging import getLogger
from openprocurement.api.models import Complaint, get_now
from openprocurement.api.utils import (
    apply_patch,
    save_tender,
    update_journal_handler_params,
    opresource,
    json_view,
)
from openprocurement.api.validation import (
    validate_complaint_data,
    validate_patch_complaint_data,
)


LOGGER = getLogger(__name__)


@opresource(name='Tender Complaints',
            collection_path='/tenders/{tender_id}/complaints',
            path='/tenders/{tender_id}/complaints/{complaint_id}',
            description="Tender complaints")
class TenderComplaintResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @json_view(content_type="application/json", validators=(validate_complaint_data,), permission='create_complaint')
    def collection_post(self):
        """Post a complaint
        """
        tender = self.request.validated['tender']
        if tender.status not in ['active.enquiries', 'active.tendering']:
            self.request.errors.add('body', 'data', 'Can\'t add complaint in current ({}) tender status'.format(tender.status))
            self.request.errors.status = 403
            return
        complaint_data = self.request.validated['data']
        complaint = Complaint(complaint_data)
        tender.complaints.append(complaint)
        if save_tender(self.request):
            update_journal_handler_params({'complaint_id': complaint.id})
            LOGGER.info('Created tender complaint {}'.format(complaint.id), extra={'MESSAGE_ID': 'tender_complaint_create'})
            self.request.response.status = 201
            self.request.response.headers['Location'] = self.request.route_url('Tender Complaints', tender_id=tender.id, complaint_id=complaint.id)
            return {'data': complaint.serialize("view")}

    @json_view(permission='view_tender')
    def collection_get(self):
        """List complaints
        """
        return {'data': [i.serialize("view") for i in self.request.validated['tender'].complaints]}

    @json_view(permission='view_tender')
    def get(self):
        """Retrieving the complaint
        """
        return {'data': self.request.validated['complaint'].serialize("view")}

    @json_view(content_type="application/json", validators=(validate_patch_complaint_data,), permission='review_complaint')
    def patch(self):
        """Post a complaint resolution
        """
        tender = self.request.validated['tender']
        if tender.status not in ['active.enquiries', 'active.tendering', 'active.auction', 'active.qualification', 'active.awarded']:
            self.request.errors.add('body', 'data', 'Can\'t update complaint in current ({}) tender status'.format(tender.status))
            self.request.errors.status = 403
            return
        if self.request.context.status != 'pending':
            self.request.errors.add('body', 'data', 'Can\'t update complaint in current ({}) status'.format(self.request.context.status))
            self.request.errors.status = 403
            return
        apply_patch(self.request, save=False, src=self.request.context.serialize())
        if self.request.context.status == 'cancelled':
            self.request.errors.add('body', 'data', 'Can\'t cancel complaint')
            self.request.errors.status = 403
            return
        if self.request.context.status == 'resolved' and tender.status != 'active.enquiries':
            for i in tender.complaints:
                if i.status == 'pending':
                    i.status = 'cancelled'
            tender.status = 'cancelled'
        elif self.request.context.status in ['declined', 'invalid'] and tender.status == 'active.awarded':
            now = get_now()
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
            stand_still_ends = [
                a.complaintPeriod.endDate
                for a in tender.awards
                if a.complaintPeriod.endDate
            ]
            stand_still_end = max(stand_still_ends) if stand_still_ends else now
            stand_still_time_expired = stand_still_end < now
            active_awards = [
                a
                for a in tender.awards
                if a.status == 'active'
            ]
            if not active_awards and not pending_complaints and not pending_awards_complaints and stand_still_time_expired:
                tender.status = 'unsuccessful'
        if save_tender(self.request):
            LOGGER.info('Updated tender complaint {}'.format(self.request.context.id), extra={'MESSAGE_ID': 'tender_complaint_patch'})
            return {'data': self.request.context.serialize("view")}
