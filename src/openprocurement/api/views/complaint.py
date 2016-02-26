# -*- coding: utf-8 -*-
from logging import getLogger
from openprocurement.api.models import get_now
from openprocurement.api.utils import (
    apply_patch,
    check_tender_status,
    context_unpack,
    json_view,
    opresource,
    save_tender,
    set_ownership,
)
from openprocurement.api.validation import (
    validate_complaint_data,
    validate_patch_complaint_data,
)


LOGGER = getLogger(__name__)


@opresource(name='Tender Complaints',
            collection_path='/tenders/{tender_id}/complaints',
            path='/tenders/{tender_id}/complaints/{complaint_id}',
            procurementMethodType='belowThreshold',
            description="Tender complaints")
class TenderComplaintResource(object):

    def __init__(self, request, context):
        self.context = context
        self.request = request
        self.db = request.registry.db

    @json_view(content_type="application/json", validators=(validate_complaint_data,), permission='create_complaint')
    def collection_post(self):
        """Post a complaint
        """
        tender = self.context
        if tender.status not in ['active.enquiries', 'active.tendering']:
            self.request.errors.add('body', 'data', 'Can\'t add complaint in current ({}) tender status'.format(tender.status))
            self.request.errors.status = 403
            return
        complaint = self.request.validated['complaint']
        if complaint.status == 'claim':
            complaint.dateSubmitted = get_now()
        else:
            complaint.status = 'draft'
        set_ownership(complaint, self.request)
        tender.complaints.append(complaint)
        if save_tender(self.request):
            LOGGER.info('Created tender complaint {}'.format(complaint.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_complaint_create'}, {'complaint_id': complaint.id}))
            self.request.response.status = 201
            self.request.response.headers['Location'] = self.request.route_url('Tender Complaints', tender_id=tender.id, complaint_id=complaint.id)
            return {
                'data': complaint.serialize(tender.status),
                'access': {
                    'token': complaint.owner_token
                }
            }

    @json_view(permission='view_tender')
    def collection_get(self):
        """List complaints
        """
        return {'data': [i.serialize("view") for i in self.context.complaints]}

    @json_view(permission='view_tender')
    def get(self):
        """Retrieving the complaint
        """
        return {'data': self.context.serialize("view")}

    @json_view(content_type="application/json", validators=(validate_patch_complaint_data,), permission='edit_complaint')
    def patch(self):
        """Post a complaint resolution
        """
        tender = self.request.validated['tender']
        if tender.status not in ['active.enquiries', 'active.tendering', 'active.auction', 'active.qualification', 'active.awarded']:
            self.request.errors.add('body', 'data', 'Can\'t update complaint in current ({}) tender status'.format(tender.status))
            self.request.errors.status = 403
            return
        if self.context.status not in ['draft', 'claim', 'answered', 'pending']:
            self.request.errors.add('body', 'data', 'Can\'t update complaint in current ({}) status'.format(self.context.status))
            self.request.errors.status = 403
            return
        data = self.request.validated['data']
        # complaint_owner
        if self.request.authenticated_role == 'complaint_owner' and self.context.status in ['draft', 'claim', 'answered', 'pending'] and data.get('status', self.context.status) == 'cancelled':
            apply_patch(self.request, save=False, src=self.context.serialize())
            self.context.dateCanceled = get_now()
        elif self.request.authenticated_role == 'complaint_owner' and tender.status in ['active.enquiries', 'active.tendering'] and self.context.status == 'draft' and data.get('status', self.context.status) == self.context.status:
            apply_patch(self.request, save=False, src=self.context.serialize())
        elif self.request.authenticated_role == 'complaint_owner' and tender.status in ['active.enquiries', 'active.tendering'] and self.context.status == 'draft' and data.get('status', self.context.status) == 'claim':
            apply_patch(self.request, save=False, src=self.context.serialize())
            self.context.dateSubmitted = get_now()
        elif self.request.authenticated_role == 'complaint_owner' and self.context.status == 'answered' and data.get('status', self.context.status) == self.context.status:
            apply_patch(self.request, save=False, src=self.context.serialize())
        elif self.request.authenticated_role == 'complaint_owner' and self.context.status == 'answered' and data.get('satisfied', self.context.satisfied) is True and data.get('status', self.context.status) == 'resolved':
            apply_patch(self.request, save=False, src=self.context.serialize())
        elif self.request.authenticated_role == 'complaint_owner' and self.context.status == 'answered' and data.get('satisfied', self.context.satisfied) is False and data.get('status', self.context.status) == 'pending':
            apply_patch(self.request, save=False, src=self.context.serialize())
            self.context.type = 'complaint'
            self.context.dateEscalated = get_now()
        # tender_owner
        elif self.request.authenticated_role == 'tender_owner' and self.context.status == 'claim' and data.get('status', self.context.status) == self.context.status:
            apply_patch(self.request, save=False, src=self.context.serialize())
        elif self.request.authenticated_role == 'tender_owner' and self.context.status == 'claim' and data.get('resolution', self.context.resolution) and data.get('resolutionType', self.context.resolutionType) and data.get('status', self.context.status) == 'answered':
            if len(data.get('resolution', self.context.resolution)) < 20:
                self.request.errors.add('body', 'data', 'Can\'t update complaint: resolution too short')
                self.request.errors.status = 403
                return
            apply_patch(self.request, save=False, src=self.context.serialize())
            self.context.dateAnswered = get_now()
        elif self.request.authenticated_role == 'tender_owner' and self.context.status == 'pending':
            apply_patch(self.request, save=False, src=self.context.serialize())
        # reviewers
        elif self.request.authenticated_role == 'reviewers' and self.context.status == 'pending' and data.get('status', self.context.status) == self.context.status:
            apply_patch(self.request, save=False, src=self.context.serialize())
        elif self.request.authenticated_role == 'reviewers' and self.context.status == 'pending' and data.get('status', self.context.status) in ['resolved', 'invalid', 'declined']:
            apply_patch(self.request, save=False, src=self.context.serialize())
            self.context.dateDecision = get_now()
        else:
            self.request.errors.add('body', 'data', 'Can\'t update complaint')
            self.request.errors.status = 403
            return
        if self.context.tendererAction and not self.context.tendererActionDate:
            self.context.tendererActionDate = get_now()
        if self.context.status not in ['draft', 'claim', 'answered', 'pending'] and tender.status in ['active.qualification', 'active.awarded']:
            check_tender_status(self.request)
        if save_tender(self.request):
            LOGGER.info('Updated tender complaint {}'.format(self.context.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_complaint_patch'}))
            return {'data': self.context.serialize("view")}
