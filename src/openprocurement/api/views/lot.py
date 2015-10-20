# -*- coding: utf-8 -*-
from logging import getLogger
from openprocurement.api.models import Lot
from openprocurement.api.utils import (
    apply_patch,
    save_tender,
    update_journal_handler_params,
    opresource,
    json_view,
)
from openprocurement.api.validation import (
    validate_lot_data,
    validate_patch_lot_data,
)


LOGGER = getLogger(__name__)


@opresource(name='Tender Lots',
            collection_path='/tenders/{tender_id}/lots',
            path='/tenders/{tender_id}/lots/{lot_id}',
            description="Tender lots")
class TenderLotResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @json_view(content_type="application/json", validators=(validate_lot_data,), permission='edit_tender')
    def collection_post(self):
        """Add a lot
        """
        tender = self.request.validated['tender']
        if tender.status not in ['active.enquiries']:
            self.request.errors.add('body', 'data', 'Can\'t add lot in current ({}) tender status'.format(tender.status))
            self.request.errors.status = 403
            return
        lot_data = self.request.validated['data']
        lot = Lot(lot_data)
        lot.__parent__ = self.request.context
        tender.lots.append(lot)
        if save_tender(self.request):
            update_journal_handler_params({'lot_id': lot.id})
            LOGGER.info('Created tender lot {}'.format(lot.id), extra={'MESSAGE_ID': 'tender_lot_create'})
            self.request.response.status = 201
            self.request.response.headers['Location'] = self.request.route_url('Tender Lots', tender_id=tender.id, lot_id=lot.id)
            return {'data': lot.serialize("view")}

    @json_view(permission='view_tender')
    def collection_get(self):
        """Lots Listing
        """
        return {'data': [i.serialize("view") for i in self.request.validated['tender'].lots]}

    @json_view(permission='view_tender')
    def get(self):
        """Retrieving the lot
        """
        return {'data': self.request.context.serialize("view")}

    @json_view(content_type="application/json", validators=(validate_patch_lot_data,), permission='edit_tender')
    def patch(self):
        """Update of lot
        """
        tender = self.request.validated['tender']
        if tender.status not in ['active.enquiries']:
            self.request.errors.add('body', 'data', 'Can\'t update lot in current ({}) tender status'.format(tender.status))
            self.request.errors.status = 403
            return
        if apply_patch(self.request, src=self.request.context.serialize()):
            LOGGER.info('Updated tender lot {}'.format(self.request.context.id), extra={'MESSAGE_ID': 'tender_lot_patch'})
            return {'data': self.request.context.serialize("view")}

    @json_view(permission='edit_tender')
    def delete(self):
        """Lot deleting
        """
        tender = self.request.validated['tender']
        if tender.status not in ['active.enquiries']:
            self.request.errors.add('body', 'data', 'Can\'t delete lot in current ({}) tender status'.format(tender.status))
            self.request.errors.status = 403
            return
        lot = self.request.context
        res = lot.serialize("view")
        tender.lots.remove(lot)
        if save_tender(self.request):
            LOGGER.info('Deleted tender lot {}'.format(self.request.context.id), extra={'MESSAGE_ID': 'tender_lot_delete'})
            return {'data': res}
