# -*- coding: utf-8 -*-
from cornice.resource import resource, view
from openprocurement.api.models import Award, Complaint, STAND_STILL_TIME, get_now
from openprocurement.api.utils import (
    apply_data_patch,
    save_tender,
)
from openprocurement.api.validation import (
    validate_complaint_data,
    validate_patch_complaint_data,
)


@resource(name='Tender Award Complaints',
          collection_path='/tenders/{tender_id}/awards/{award_id}/complaints',
          path='/tenders/{tender_id}/awards/{award_id}/complaints/{complaint_id}',
          description="Tender award complaints")
class TenderAwardComplaintResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @view(content_type="application/json", permission='view_tender', validators=(validate_complaint_data,), renderer='json')
    def collection_post(self):
        """Post a complaint for award
        """
        tender = self.request.validated['tender']
        if tender.status not in ['active.qualification', 'active.awarded']:
            self.request.errors.add('body', 'data', 'Can\'t add complaint in current tender status')
            self.request.errors.status = 403
            return
        complaint_data = self.request.validated['data']
        complaint = Complaint(complaint_data)
        src = tender.serialize("plain")
        self.request.validated['award'].complaints.append(complaint)
        save_tender(tender, src, self.request)
        self.request.response.status = 201
        self.request.response.headers['Location'] = self.request.route_url('Tender Award Complaints', tender_id=tender.id, award_id=self.request.validated['award_id'], complaint_id=complaint['id'])
        return {'data': complaint.serialize("view")}

    @view(renderer='json', permission='view_tender')
    def collection_get(self):
        """List complaints for award
        """
        return {'data': [i.serialize("view") for i in self.request.validated['award'].complaints]}

    @view(renderer='json', permission='view_tender')
    def get(self):
        """Retrieving the complaint for award
        """
        return {'data': self.request.validated['complaint'].serialize("view")}

    @view(content_type="application/json", permission='edit_tender', validators=(validate_patch_complaint_data,), renderer='json')
    def patch(self):
        """Post a complaint resolution for award
        """
        tender = self.request.validated['tender']
        if tender.status not in ['active.qualification', 'active.awarded']:
            self.request.errors.add('body', 'data', 'Can\'t update complaint in current tender status')
            self.request.errors.status = 403
            return
        complaint = self.request.validated['complaint']
        if complaint.status != 'accepted':
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
            if complaint.status == 'satisfied':
                award = self.request.validated['award']
                if tender.status == 'active.awarded':
                    tender.status = 'active.qualification'
                    tender.awardPeriod.endDate = None
                if award.status == 'unsuccessful':
                    for i in tender.awards[tender.awards.index(award):]:
                        i.status = 'cancelled'
                        for j in i.complaints:
                            if j.status == 'accepted':
                                j.status = 'cancelled'
                award.status = 'cancelled'
                unsuccessful_awards = [i.bid_id for i in tender.awards if i.status == 'unsuccessful']
                bids = [i for i in sorted(tender.bids, key=lambda i: (i.value.amount, i.date)) if i.id not in unsuccessful_awards]
                if bids:
                    bid = bids[0].serialize()
                    award_data = {
                        'bid_id': bid['id'],
                        'status': 'pending',
                        'value': bid['value'],
                        'suppliers': bid['tenderers'],
                    }
                    award = Award(award_data)
                    tender.awards.append(award)
                else:
                    tender.awardPeriod.endDate = get_now()
                    tender.status = 'active.awarded'
            elif complaint.status in ['rejected', 'invalid'] and tender.status == 'active.awarded':
                accepted_complaints = [
                    i
                    for i in tender.complaints
                    if i.status == 'accepted'
                ]
                accepted_awards_complaints = [
                    i
                    for a in tender.awards
                    for i in a.complaints
                    if i.status == 'accepted'
                ]
                stand_still_time_expired = tender.awardPeriod.endDate + STAND_STILL_TIME < get_now()
                if not accepted_complaints and not accepted_awards_complaints and stand_still_time_expired:
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
