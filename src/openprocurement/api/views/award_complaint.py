# -*- coding: utf-8 -*-
from logging import getLogger
from cornice.resource import resource, view
from openprocurement.api.models import Complaint, STAND_STILL_TIME, get_now
from openprocurement.api.utils import (
    apply_patch,
    save_tender,
    add_next_award,
    error_handler,
    update_journal_handler_params,
)
from openprocurement.api.validation import (
    validate_complaint_data,
    validate_patch_complaint_data,
)


LOGGER = getLogger(__name__)


@resource(name='Tender Award Complaints',
          collection_path='/tenders/{tender_id}/awards/{award_id}/complaints',
          path='/tenders/{tender_id}/awards/{award_id}/complaints/{complaint_id}',
          description="Tender award complaints",
          error_handler=error_handler)
class TenderAwardComplaintResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @view(content_type="application/json", permission='create_award_complaint', validators=(validate_complaint_data,), renderer='json')
    def collection_post(self):
        """Post a complaint for award
        """
        tender = self.request.validated['tender']
        if tender.status not in ['active.qualification', 'active.awarded']:
            self.request.errors.add('body', 'data', 'Can\'t add complaint in current ({}) tender status'.format(tender.status))
            self.request.errors.status = 403
            return
        if self.request.context.complaintPeriod and \
           (self.request.context.complaintPeriod.startDate and self.request.context.complaintPeriod.startDate > get_now() or
                self.request.context.complaintPeriod.endDate and self.request.context.complaintPeriod.endDate < get_now()):
            self.request.errors.add('body', 'data', 'Can add complaint only in complaintPeriod')
            self.request.errors.status = 403
            return
        complaint_data = self.request.validated['data']
        complaint = Complaint(complaint_data)
        self.request.context.complaints.append(complaint)
        if save_tender(self.request):
            update_journal_handler_params({'complaint_id': complaint.id})
            LOGGER.info('Created tender award complaint {}'.format(complaint.id), extra={'MESSAGE_ID': 'tender_award_complaint_create'})
            self.request.response.status = 201
            self.request.response.headers['Location'] = self.request.route_url('Tender Award Complaints', tender_id=tender.id, award_id=self.request.validated['award_id'], complaint_id=complaint['id'])
            return {'data': complaint.serialize("view")}

    @view(renderer='json', permission='view_tender')
    def collection_get(self):
        """List complaints for award
        """
        return {'data': [i.serialize("view") for i in self.request.context.complaints]}

    @view(renderer='json', permission='view_tender')
    def get(self):
        """Retrieving the complaint for award
        """
        return {'data': self.request.validated['complaint'].serialize("view")}

    @view(content_type="application/json", permission='review_complaint', validators=(validate_patch_complaint_data,), renderer='json')
    def patch(self):
        """Post a complaint resolution for award
        """
        tender = self.request.validated['tender']
        if tender.status not in ['active.qualification', 'active.awarded']:
            self.request.errors.add('body', 'data', 'Can\'t update complaint in current ({}) tender status'.format(tender.status))
            self.request.errors.status = 403
            return
        complaint = self.request.context
        if complaint.status != 'pending':
            self.request.errors.add('body', 'data', 'Can\'t update complaint in current ({}) status'.format(complaint.status))
            self.request.errors.status = 403
            return
        apply_patch(self.request, save=False, src=complaint.serialize())
        if complaint.status == 'cancelled':
            self.request.errors.add('body', 'data', 'Can\'t cancel complaint')
            self.request.errors.status = 403
            return
        if complaint.status == 'resolved':
            award = self.request.validated['award']
            if tender.status == 'active.awarded':
                tender.status = 'active.qualification'
                tender.awardPeriod.endDate = None
            now = get_now()
            if award.status == 'unsuccessful':
                for i in tender.awards[tender.awards.index(award):]:
                    i.complaintPeriod.endDate = now + STAND_STILL_TIME
                    i.status = 'cancelled'
                    for j in i.complaints:
                        if j.status == 'pending':
                            j.status = 'cancelled'
            for i in award.contracts:
                i.status = 'cancelled'
            award.complaintPeriod.endDate = now + STAND_STILL_TIME
            award.status = 'cancelled'
            add_next_award(self.request)
        elif complaint.status in ['declined', 'invalid'] and tender.status == 'active.awarded':
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
            LOGGER.info('Updated tender award complaint {}'.format(self.request.context.id), extra={'MESSAGE_ID': 'tender_award_complaint_patch'})
            return {'data': complaint.serialize("view")}
