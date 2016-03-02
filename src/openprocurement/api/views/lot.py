# -*- coding: utf-8 -*-
from openprocurement.api.utils import (
    apply_patch,
    save_tender,
    opresource,
    json_view,
    context_unpack,
    APIResource,
)
from openprocurement.api.validation import (
    validate_lot_data,
    validate_patch_lot_data,
)


@opresource(name='Tender Lots',
            collection_path='/tenders/{tender_id}/lots',
            path='/tenders/{tender_id}/lots/{lot_id}',
            procurementMethodType='belowThreshold',
            description="Tender lots")
class TenderLotResource(APIResource):

    @json_view(content_type="application/json", validators=(validate_lot_data,), permission='edit_tender')
    def collection_post(self):
        """Add a lot
        """
        tender = self.request.validated['tender']
        if tender.status not in ['active.enquiries']:
            self.request.errors.add('body', 'data', 'Can\'t add lot in current ({}) tender status'.format(tender.status))
            self.request.errors.status = 403
            return
        lot = self.request.validated['lot']
        tender.lots.append(lot)
        if save_tender(self.request):
            self.LOGGER.info('Created tender lot {}'.format(lot.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_lot_create'}, {'lot_id': lot.id}))
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
            self.LOGGER.info('Updated tender lot {}'.format(self.request.context.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_lot_patch'}))
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
            self.LOGGER.info('Deleted tender lot {}'.format(self.request.context.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_lot_delete'}))
            return {'data': res}
