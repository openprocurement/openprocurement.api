# -*- coding: utf-8 -*-
from logging import getLogger
from cornice.resource import resource, view
from openprocurement.api.models import Cancellation
from openprocurement.api.utils import (
    apply_patch,
    save_tender,
    error_handler,
    update_journal_handler_params,
)
from openprocurement.api.validation import (
    validate_cancellation_data,
    validate_patch_cancellation_data,
)


LOGGER = getLogger(__name__)


@resource(name='Tender Cancellations',
          collection_path='/tenders/{tender_id}/cancellations',
          path='/tenders/{tender_id}/cancellations/{cancellation_id}',
          description="Tender cancellations",
          error_handler=error_handler)
class TenderCancellationResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @view(content_type="application/json", validators=(validate_cancellation_data,), permission='edit_tender', renderer='json')
    def collection_post(self):
        """Post a cancellation
        """
        tender = self.request.validated['tender']
        if tender.status in ['complete', 'cancelled', 'unsuccessful']:
            self.request.errors.add('body', 'data', 'Can\'t add cancellation in current ({}) tender status'.format(tender.status))
            self.request.errors.status = 403
            return
        cancellation_data = self.request.validated['data']
        cancellation = Cancellation(cancellation_data)
        if cancellation.status == 'active':
            tender.status = 'cancelled'
        tender.cancellations.append(cancellation)
        if save_tender(self.request):
            update_journal_handler_params({'cancellation_id': cancellation.id})
            LOGGER.info('Created tender cancellation {}'.format(cancellation.id), extra={'MESSAGE_ID': 'tender_cancellation_create'})
            self.request.response.status = 201
            self.request.response.headers['Location'] = self.request.route_url('Tender Cancellations', tender_id=tender.id, cancellation_id=cancellation.id)
            return {'data': cancellation.serialize("view")}

    @view(renderer='json', permission='view_tender')
    def collection_get(self):
        """List cancellations
        """
        return {'data': [i.serialize("view") for i in self.request.validated['tender'].cancellations]}

    @view(renderer='json', permission='view_tender')
    def get(self):
        """Retrieving the cancellation
        """
        return {'data': self.request.validated['cancellation'].serialize("view")}

    @view(content_type="application/json", validators=(validate_patch_cancellation_data,), permission='edit_tender', renderer='json')
    def patch(self):
        """Post a cancellation resolution
        """
        tender = self.request.validated['tender']
        if tender.status in ['complete', 'cancelled', 'unsuccessful']:
            self.request.errors.add('body', 'data', 'Can\'t update cancellation in current ({}) tender status'.format(tender.status))
            self.request.errors.status = 403
            return
        apply_patch(self.request, save=False, src=self.request.context.serialize())
        if self.request.context.status == 'active':
            tender.status = 'cancelled'
        if save_tender(self.request):
            LOGGER.info('Updated tender cancellation {}'.format(self.request.context.id), extra={'MESSAGE_ID': 'tender_cancellation_patch'})
            return {'data': self.request.context.serialize("view")}
