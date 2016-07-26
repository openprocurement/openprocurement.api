# -*- coding: utf-8 -*-
from openprocurement.api.utils import (
    apply_patch,
    save_tender,
    add_next_award,
    opresource,
    json_view,
    context_unpack,
    APIResource,
    get_now
)
from openprocurement.api.validation import (
    validate_cancellation_data,
    validate_patch_cancellation_data,
)


@opresource(name='Tender Cancellations',
            collection_path='/tenders/{tender_id}/cancellations',
            path='/tenders/{tender_id}/cancellations/{cancellation_id}',
            procurementMethodType='belowThreshold',
            description="Tender cancellations")
class TenderCancellationResource(APIResource):

    def cancel_tender(self):
        tender = self.request.validated['tender']
        if tender.status in ['active.tendering', 'active.auction']:
            tender.bids = []
        tender.status = 'cancelled'

    def cancel_lot(self, cancellation=None):
        if not cancellation:
            cancellation = self.context
        tender = self.request.validated['tender']
        [setattr(i, 'status', 'cancelled') for i in tender.lots if i.id == cancellation.relatedLot]
        statuses = set([lot.status for lot in tender.lots])
        if statuses == set(['cancelled']):
            self.cancel_tender()
        elif not statuses.difference(set(['unsuccessful', 'cancelled'])):
            tender.status = 'unsuccessful'
        elif not statuses.difference(set(['complete', 'unsuccessful', 'cancelled'])):
            tender.status = 'complete'
        if tender.status == 'active.auction' and all([
            i.auctionPeriod and i.auctionPeriod.endDate
            for i in self.request.validated['tender'].lots
            if i.numberOfBids > 1 and i.status == 'active'
        ]):
            add_next_award(self.request)

    @json_view(content_type="application/json", validators=(validate_cancellation_data,), permission='edit_tender')
    def collection_post(self):
        """Post a cancellation
        """
        tender = self.request.validated['tender']
        if tender.status in ['complete', 'cancelled', 'unsuccessful']:
            self.request.errors.add('body', 'data', 'Can\'t add cancellation in current ({}) tender status'.format(tender.status))
            self.request.errors.status = 403
            return
        cancellation = self.request.validated['cancellation']
        cancellation.date = get_now()
        if any([i.status != 'active' for i in tender.lots if i.id == cancellation.relatedLot]):
            self.request.errors.add('body', 'data', 'Can add cancellation only in active lot status')
            self.request.errors.status = 403
            return
        if cancellation.relatedLot and cancellation.status == 'active':
            self.cancel_lot(cancellation)
        elif cancellation.status == 'active':
            self.cancel_tender()
        tender.cancellations.append(cancellation)
        if save_tender(self.request):
            self.LOGGER.info('Created tender cancellation {}'.format(cancellation.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_cancellation_create'}, {'cancellation_id': cancellation.id}))
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
            self.cancel_lot()
        elif self.request.context.status == 'active':
            self.cancel_tender()
        if save_tender(self.request):
            self.LOGGER.info('Updated tender cancellation {}'.format(self.request.context.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_cancellation_patch'}))
            return {'data': self.request.context.serialize("view")}
