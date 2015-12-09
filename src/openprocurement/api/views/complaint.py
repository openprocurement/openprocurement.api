# -*- coding: utf-8 -*-
from logging import getLogger
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
        set_ownership(complaint, self.request)
        tender.complaints.append(complaint)
        if save_tender(self.request):
            LOGGER.info('Created tender complaint {}'.format(complaint.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_complaint_create'}, {'complaint_id': complaint.id}))
            self.request.response.status = 201
            self.request.response.headers['Location'] = self.request.route_url('Tender Complaints', tender_id=tender.id, complaint_id=complaint.id)
            return {
                'data': complaint.serialize("view"),
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

    @json_view(content_type="application/json", validators=(validate_patch_complaint_data,), permission='review_complaint')
    def patch(self):
        """Post a complaint resolution
        """
        tender = self.request.validated['tender']
        if tender.status not in ['active.enquiries', 'active.tendering', 'active.auction', 'active.qualification', 'active.awarded']:
            self.request.errors.add('body', 'data', 'Can\'t update complaint in current ({}) tender status'.format(tender.status))
            self.request.errors.status = 403
            return
        if self.context.status != 'draft':
            self.request.errors.add('body', 'data', 'Can\'t update complaint in current ({}) status'.format(self.context.status))
            self.request.errors.status = 403
            return
        if self.request.validated['data'].get('status', self.context.status) == 'cancelled':
            self.request.errors.add('body', 'data', 'Can\'t cancel complaint')
            self.request.errors.status = 403
            return
        apply_patch(self.request, save=False, src=self.context.serialize())
        if self.context.status == 'resolved' and tender.status != 'active.enquiries':
            for i in tender.complaints:
                if i.status == 'pending':
                    i.status = 'cancelled'
            [setattr(i, 'status', 'cancelled') for i in tender.lots]
            tender.status = 'cancelled'
        elif self.context.status in ['declined', 'invalid'] and tender.status == 'active.awarded':
            check_tender_status(self.request)
        if save_tender(self.request):
            LOGGER.info('Updated tender complaint {}'.format(self.context.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_complaint_patch'}))
            return {'data': self.context.serialize("view")}
