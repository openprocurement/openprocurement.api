# -*- coding: utf-8 -*-
from logging import getLogger
from cornice.resource import resource, view
from openprocurement.api.utils import (
    get_file,
    save_tender,
    upload_file,
    apply_patch,
)
from openprocurement.api.validation import (
    validate_file_update,
    validate_file_upload,
    validate_patch_document_data,
)


LOGGER = getLogger(__name__)


@resource(name='Tender Bid Documents',
          collection_path='/tenders/{tender_id}/bids/{bid_id}/documents',
          path='/tenders/{tender_id}/bids/{bid_id}/documents/{document_id}',
          description="Tender bidder documents")
class TenderBidDocumentResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @view(renderer='json', permission='view_tender')
    def collection_get(self):
        """Tender Bid Documents List"""
        if self.request.validated['tender_status'] in ['active.tendering', 'active.auction'] and self.request.authenticated_role != 'bid_owner':
            self.request.errors.add('body', 'data', 'Can\'t view bid documents in current tender status')
            self.request.errors.status = 403
            return
        bid = self.request.validated['bid']
        if self.request.params.get('all', ''):
            collection_data = [i.serialize("view") for i in bid['documents']]
        else:
            collection_data = sorted(dict([
                (i.id, i.serialize("view"))
                for i in bid['documents']
            ]).values(), key=lambda i: i['dateModified'])
        return {'data': collection_data}

    @view(renderer='json', validators=(validate_file_upload,), permission='edit_bid')
    def collection_post(self):
        """Tender Bid Document Upload
        """
        tender = self.request.validated['tender']
        if tender.status not in ['active.tendering', 'active.auction', 'active.qualification']:
            self.request.errors.add('body', 'data', 'Can\'t add document in current tender status')
            self.request.errors.status = 403
            return
        document = upload_file(self.request)
        self.request.validated['bid'].documents.append(document)
        save_tender(self.request)
        LOGGER.info('Created tender bid document {}'.format(document.id))
        self.request.response.status = 201
        document_route = self.request.matched_route.name.replace("collection_", "")
        self.request.response.headers['Location'] = self.request.current_route_url(_route_name=document_route, document_id=document.id, _query={})
        return {'data': document.serialize("view")}

    @view(renderer='json', permission='view_tender')
    def get(self):
        """Tender Bid Document Read"""
        if self.request.validated['tender_status'] in ['active.tendering', 'active.auction'] and self.request.authenticated_role != 'bid_owner':
            self.request.errors.add('body', 'data', 'Can\'t view bid document in current tender status')
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

    @view(renderer='json', validators=(validate_file_update,), permission='edit_bid')
    def put(self):
        """Tender Bid Document Update"""
        tender = self.request.validated['tender']
        if tender.status not in ['active.tendering', 'active.auction', 'active.qualification']:
            self.request.errors.add('body', 'data', 'Can\'t update document in current tender status')
            self.request.errors.status = 403
            return
        document = upload_file(self.request)
        self.request.validated['bid'].documents.append(document)
        save_tender(self.request)
        LOGGER.info('Updated tender bid document {}'.format(self.request.context.id))
        return {'data': document.serialize("view")}

    @view(renderer='json', validators=(validate_patch_document_data,), permission='edit_bid')
    def patch(self):
        """Tender Bid Document Update"""
        if self.request.validated['tender_status'] not in ['active.tendering', 'active.auction', 'active.qualification']:
            self.request.errors.add('body', 'data', 'Can\'t update document in current tender status')
            self.request.errors.status = 403
            return
        apply_patch(self.request, src=self.request.context.serialize())
        LOGGER.info('Updated tender bid document {}'.format(self.request.context.id))
        return {'data': self.request.context.serialize("view")}
