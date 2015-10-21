# -*- coding: utf-8 -*-
from logging import getLogger
from openprocurement.api.models import Cancellation
from openprocurement.api.utils import (
    apply_patch,
    save_tender,
    check_tender_status,
    opresource,
    json_view,
    context_unpack,
)
from openprocurement.api.validation import (
    validate_cancellation_data,
    validate_patch_cancellation_data,
)


LOGGER = getLogger(__name__)


@opresource(name='Tender Cancellations',
            collection_path='/tenders/{tender_id}/cancellations',
            path='/tenders/{tender_id}/cancellations/{cancellation_id}',
            description="Tender cancellations")
class TenderCancellationResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @json_view(content_type="application/json", validators=(validate_cancellation_data,), permission='edit_tender')
    def collection_post(self):
        """Post a cancellation
        """
        tender = self.request.validated['tender']
        if tender.status in ['complete', 'cancelled', 'unsuccessful']:
            self.request.errors.add('body', 'data', 'Can\'t add cancellation in current ({}) tender status'.format(tender.status))
            self.request.errors.status = 403
            return
        cancellation_data = self.request.validated['data']
        if any([i.status != 'active' for i in tender.lots if i.id == cancellation_data.get('relatedLot')]):
            self.request.errors.add('body', 'data', 'Can add cancellation only in active lot status')
            self.request.errors.status = 403
            return
        cancellation = Cancellation(cancellation_data)
        cancellation.__parent__ = self.request.context
        if cancellation.relatedLot and cancellation.status == 'active':
            [setattr(i, 'status', 'cancelled') for i in tender.lots if i.id == cancellation.relatedLot]
            check_tender_status(self.request)
        elif cancellation.status == 'active':
            tender.status = 'cancelled'
        tender.cancellations.append(cancellation)
        if save_tender(self.request):
            update_logging_context({'cancellation_id': cancellation.id}, self.request)
            LOGGER.info('Created tender cancellation {}'.format(cancellation.id), extra={'MESSAGE_ID': 'tender_cancellation_create'})
            self.request.response.status = 201
            self.request.response.headers['Location'] = self.request.route_url('Tender Cancellations', tender_id=tender.id, cancellation_id=cancellation.id)
            return {'data': cancellation.serialize("view")}

    @json_view(permission='view_tender')
    def collection_get(self):
        """List cancellations
        """
        return {'data': [i.serialize("view") for i in self.request.validated['tender'].cancellations]}

    @json_view(permission='view_tender')
    def get(self):
        """Retrieving the cancellation
        """
        return {'data': self.request.validated['cancellation'].serialize("view")}

    @json_view(content_type="application/json", validators=(validate_patch_cancellation_data,), permission='edit_tender')
    def patch(self):
        """Post a cancellation resolution
        """
        tender = self.request.validated['tender']
        if tender.status in ['complete', 'cancelled', 'unsuccessful']:
            self.request.errors.add('body', 'data', 'Can\'t update cancellation in current ({}) tender status'.format(tender.status))
            self.request.errors.status = 403
            return
        if any([i.status != 'active' for i in tender.lots if i.id == self.request.context.relatedLot]):
            self.request.errors.add('body', 'data', 'Can update cancellation only in active lot status')
            self.request.errors.status = 403
            return
        apply_patch(self.request, save=False, src=self.request.context.serialize())
        if self.request.context.relatedLot and self.request.context.status == 'active':
            [setattr(i, 'status', 'cancelled') for i in tender.lots if i.id == self.request.context.relatedLot]
            check_tender_status(self.request)
        elif self.request.context.status == 'active':
            tender.status = 'cancelled'
        if save_tender(self.request):
            LOGGER.info('Updated tender cancellation {}'.format(self.request.context.id), extra={'MESSAGE_ID': 'tender_cancellation_patch'})
            return {'data': self.request.context.serialize("view")}
