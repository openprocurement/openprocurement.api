# -*- coding: utf-8 -*-
from logging import getLogger
from openprocurement.api.utils import (
    get_file,
    save_auction,
    upload_file,
    apply_patch,
    update_file_content_type,
    opresource,
    json_view,
    context_unpack,
)
from openprocurement.api.validation import (
    validate_file_update,
    validate_file_upload,
    validate_patch_document_data,
)


LOGGER = getLogger(__name__)


@opresource(name='Auction Documents',
            collection_path='/auctions/{auction_id}/documents',
            path='/auctions/{auction_id}/documents/{document_id}',
            description="Auction related binary files (PDFs, etc.)")
class AuctionDocumentResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @json_view(permission='view_auction')
    def collection_get(self):
        """Auction Documents List"""
        auction = self.request.validated['auction']
        if self.request.params.get('all', ''):
            collection_data = [i.serialize("view") for i in auction['documents']]
        else:
            collection_data = sorted(dict([
                (i.id, i.serialize("view"))
                for i in auction['documents']
            ]).values(), key=lambda i: i['dateModified'])
        return {'data': collection_data}

    @json_view(permission='upload_auction_documents', validators=(validate_file_upload,))
    def collection_post(self):
        """Auction Document Upload"""
        if self.request.authenticated_role != 'auction' and self.request.validated['auction_status'] != 'active.enquiries' or \
           self.request.authenticated_role == 'auction' and self.request.validated['auction_status'] not in ['active.auction', 'active.qualification']:
            self.request.errors.add('body', 'data', 'Can\'t add document in current ({}) auction status'.format(self.request.validated['auction_status']))
            self.request.errors.status = 403
            return
        document = upload_file(self.request)
        self.request.validated['auction'].documents.append(document)
        if save_auction(self.request):
            LOGGER.info('Created auction document {}'.format(document.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'auction_document_create'}, {'document_id': document.id}))
            self.request.response.status = 201
            document_route = self.request.matched_route.name.replace("collection_", "")
            self.request.response.headers['Location'] = self.request.current_route_url(_route_name=document_route, document_id=document.id, _query={})
            return {'data': document.serialize("view")}

    @json_view(permission='view_auction')
    def get(self):
        """Auction Document Read"""
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

    @json_view(permission='upload_auction_documents', validators=(validate_file_update,))
    def put(self):
        """Auction Document Update"""
        if self.request.authenticated_role != 'auction' and self.request.validated['auction_status'] != 'active.enquiries' or \
           self.request.authenticated_role == 'auction' and self.request.validated['auction_status'] not in ['active.auction', 'active.qualification']:
            self.request.errors.add('body', 'data', 'Can\'t update document in current ({}) auction status'.format(self.request.validated['auction_status']))
            self.request.errors.status = 403
            return
        document = upload_file(self.request)
        self.request.validated['auction'].documents.append(document)
        if save_auction(self.request):
            LOGGER.info('Updated auction document {}'.format(self.request.context.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'auction_document_put'}))
            return {'data': document.serialize("view")}

    @json_view(content_type="application/json", permission='upload_auction_documents', validators=(validate_patch_document_data,))
    def patch(self):
        """Auction Document Update"""
        if self.request.authenticated_role != 'auction' and self.request.validated['auction_status'] != 'active.enquiries' or \
           self.request.authenticated_role == 'auction' and self.request.validated['auction_status'] not in ['active.auction', 'active.qualification']:
            self.request.errors.add('body', 'data', 'Can\'t update document in current ({}) auction status'.format(self.request.validated['auction_status']))
            self.request.errors.status = 403
            return
        if apply_patch(self.request, src=self.request.context.serialize()):
            update_file_content_type(self.request)
            LOGGER.info('Updated auction document {}'.format(self.request.context.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'auction_document_patch'}))
            return {'data': self.request.context.serialize("view")}
