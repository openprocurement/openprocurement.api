# -*- coding: utf-8 -*-
from openprocurement.api.models import get_now
from openprocurement.api.utils import (
    get_file,
    save_tender,
    upload_file,
    apply_patch,
    update_file_content_type,
    opresource,
    json_view,
    context_unpack,
    APIResource,
)
from openprocurement.api.validation import (
    validate_file_update,
    validate_file_upload,
    validate_patch_document_data,
)


@opresource(name='Tender Bid Documents',
            collection_path='/tenders/{tender_id}/bids/{bid_id}/documents',
            path='/tenders/{tender_id}/bids/{bid_id}/documents/{document_id}',
            procurementMethodType='belowThreshold',
            description="Tender bidder documents")
class TenderBidDocumentResource(APIResource):

    @json_view(permission='view_tender')
    def collection_get(self):
        """Tender Bid Documents List"""
        if self.request.validated['tender_status'] in ['active.tendering', 'active.auction'] and self.request.authenticated_role != 'bid_owner':
            self.request.errors.add('body', 'data', 'Can\'t view bid documents in current ({}) tender status'.format(self.request.validated['tender_status']))
            self.request.errors.status = 403
            return
        if self.request.params.get('all', ''):
            collection_data = [i.serialize("view") for i in self.context.documents]
        else:
            collection_data = sorted(dict([
                (i.id, i.serialize("view"))
                for i in self.context.documents
            ]).values(), key=lambda i: i['dateModified'])
        return {'data': collection_data}

    @json_view(validators=(validate_file_upload,), permission='edit_bid')
    def collection_post(self):
        """Tender Bid Document Upload
        """
        if self.request.validated['tender_status'] not in ['active.tendering', 'active.qualification']:
            self.request.errors.add('body', 'data', 'Can\'t add document in current ({}) tender status'.format(self.request.validated['tender_status']))
            self.request.errors.status = 403
            return
        tender = self.request.validated['tender']
        if self.request.validated['tender_status'] == 'active.tendering' and (tender.tenderPeriod.startDate and get_now() < tender.tenderPeriod.startDate or get_now() > tender.tenderPeriod.endDate):
            self.request.errors.add('body', 'data', 'Document can be added only during the tendering period: from ({}) to ({}).'.format(tender.tenderPeriod.startDate and tender.tenderPeriod.startDate.isoformat(), tender.tenderPeriod.endDate.isoformat()))
            self.request.errors.status = 403
            return
        if self.request.validated['tender_status'] == 'active.qualification' and not [i for i in self.request.validated['tender'].awards if i.status == 'pending' and i.bid_id == self.request.validated['bid_id']]:
            self.request.errors.add('body', 'data', 'Can\'t add document because award of bid is not in pending state')
            self.request.errors.status = 403
            return
        document = upload_file(self.request)
        self.context.documents.append(document)
        if self.request.validated['tender_status'] == 'active.tendering':
            self.request.validated['tender'].modified = False
        if save_tender(self.request):
            self.LOGGER.info('Created tender bid document {}'.format(document.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_bid_document_create'}, {'document_id': document.id}))
            self.request.response.status = 201
            document_route = self.request.matched_route.name.replace("collection_", "")
            self.request.response.headers['Location'] = self.request.current_route_url(_route_name=document_route, document_id=document.id, _query={})
            return {'data': document.serialize("view")}

    @json_view(permission='view_tender')
    def get(self):
        """Tender Bid Document Read"""
        if self.request.validated['tender_status'] in ['active.tendering', 'active.auction'] and self.request.authenticated_role != 'bid_owner':
            self.request.errors.add('body', 'data', 'Can\'t view bid document in current ({}) tender status'.format(self.request.validated['tender_status']))
            self.request.errors.status = 403
            return
        if self.request.params.get('download'):
            return get_file(self.request)
        document = self.request.validated['document']
        document_data = document.serialize("view")
        document_data['previousVersions'] = [
            i.serialize("view")
            for i in self.request.validated['documents']
            if i.url != document.url
        ]
        return {'data': document_data}

    @json_view(validators=(validate_file_update,), permission='edit_bid')
    def put(self):
        """Tender Bid Document Update"""
        if self.request.validated['tender_status'] not in ['active.tendering', 'active.qualification']:
            self.request.errors.add('body', 'data', 'Can\'t update document in current ({}) tender status'.format(self.request.validated['tender_status']))
            self.request.errors.status = 403
            return
        tender = self.request.validated['tender']
        if self.request.validated['tender_status'] == 'active.tendering' and (tender.tenderPeriod.startDate and get_now() < tender.tenderPeriod.startDate or get_now() > tender.tenderPeriod.endDate):
            self.request.errors.add('body', 'data', 'Document can be updated only during the tendering period: from ({}) to ({}).'.format(tender.tenderPeriod.startDate and tender.tenderPeriod.startDate.isoformat(), tender.tenderPeriod.endDate.isoformat()))
            self.request.errors.status = 403
            return
        if self.request.validated['tender_status'] == 'active.qualification' and not [i for i in self.request.validated['tender'].awards if i.status == 'pending' and i.bid_id == self.request.validated['bid_id']]:
            self.request.errors.add('body', 'data', 'Can\'t update document because award of bid is not in pending state')
            self.request.errors.status = 403
            return
        document = upload_file(self.request)
        self.request.validated['bid'].documents.append(document)
        if self.request.validated['tender_status'] == 'active.tendering':
            self.request.validated['tender'].modified = False
        if save_tender(self.request):
            self.LOGGER.info('Updated tender bid document {}'.format(self.request.context.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_bid_document_put'}))
            return {'data': document.serialize("view")}

    @json_view(content_type="application/json", validators=(validate_patch_document_data,), permission='edit_bid')
    def patch(self):
        """Tender Bid Document Update"""
        if self.request.validated['tender_status'] not in ['active.tendering', 'active.qualification']:
            self.request.errors.add('body', 'data', 'Can\'t update document in current ({}) tender status'.format(self.request.validated['tender_status']))
            self.request.errors.status = 403
            return
        tender = self.request.validated['tender']
        if self.request.validated['tender_status'] == 'active.tendering' and (tender.tenderPeriod.startDate and get_now() < tender.tenderPeriod.startDate or get_now() > tender.tenderPeriod.endDate):
            self.request.errors.add('body', 'data', 'Document can be updated only during the tendering period: from ({}) to ({}).'.format(tender.tenderPeriod.startDate and tender.tenderPeriod.startDate.isoformat(), tender.tenderPeriod.endDate.isoformat()))
            self.request.errors.status = 403
            return
        if self.request.validated['tender_status'] == 'active.qualification' and not [i for i in self.request.validated['tender'].awards if i.status == 'pending' and i.bid_id == self.request.validated['bid_id']]:
            self.request.errors.add('body', 'data', 'Can\'t update document because award of bid is not in pending state')
            self.request.errors.status = 403
            return
        if self.request.validated['tender_status'] == 'active.tendering':
            self.request.validated['tender'].modified = False
        if apply_patch(self.request, src=self.request.context.serialize()):
            update_file_content_type(self.request)
            self.LOGGER.info('Updated tender bid document {}'.format(self.request.context.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_bid_document_patch'}))
            return {'data': self.request.context.serialize("view")}
