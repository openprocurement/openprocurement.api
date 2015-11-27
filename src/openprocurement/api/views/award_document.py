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


@opresource(name='Auction Award Documents',
            collection_path='/auctions/{auction_id}/awards/{award_id}/documents',
            path='/auctions/{auction_id}/awards/{award_id}/documents/{document_id}',
            description="Auction award documents")
class AuctionAwardDocumentResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @json_view(permission='view_auction')
    def collection_get(self):
        """Auction Award Documents List"""
        award = self.request.validated['award']
        if self.request.params.get('all', ''):
            collection_data = [i.serialize("view") for i in award['documents']]
        else:
            collection_data = sorted(dict([
                (i.id, i.serialize("view"))
                for i in award['documents']
            ]).values(), key=lambda i: i['dateModified'])
        return {'data': collection_data}

    @json_view(validators=(validate_file_upload,), permission='edit_auction')
    def collection_post(self):
        """Auction Award Document Upload
        """
        if self.request.validated['auction_status'] != 'active.qualification':
            self.request.errors.add('body', 'data', 'Can\'t add document in current ({}) auction status'.format(self.request.validated['auction_status']))
            self.request.errors.status = 403
            return
        if any([i.status != 'active' for i in self.request.validated['auction'].lots if i.id == self.request.context.lotID]):
            self.request.errors.add('body', 'data', 'Can add document only in active lot status')
            self.request.errors.status = 403
            return
        document = upload_file(self.request)
        self.request.validated['award'].documents.append(document)
        if save_auction(self.request):
            LOGGER.info('Created auction award document {}'.format(document.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'auction_award_document_create'}, {'document_id': document.id}))
            self.request.response.status = 201
            document_route = self.request.matched_route.name.replace("collection_", "")
            self.request.response.headers['Location'] = self.request.current_route_url(_route_name=document_route, document_id=document.id, _query={})
            return {'data': document.serialize("view")}

    @json_view(permission='view_auction')
    def get(self):
        """Auction Award Document Read"""
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

    @json_view(validators=(validate_file_update,), permission='edit_auction')
    def put(self):
        """Auction Award Document Update"""
        if self.request.validated['auction_status'] != 'active.qualification':
            self.request.errors.add('body', 'data', 'Can\'t update document in current ({}) auction status'.format(self.request.validated['auction_status']))
            self.request.errors.status = 403
            return
        if any([i.status != 'active' for i in self.request.validated['auction'].lots if i.id == self.request.validated['award'].lotID]):
            self.request.errors.add('body', 'data', 'Can update document only in active lot status')
            self.request.errors.status = 403
            return
        document = upload_file(self.request)
        self.request.validated['award'].documents.append(document)
        if save_auction(self.request):
            LOGGER.info('Updated auction award document {}'.format(self.request.context.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'auction_award_document_put'}))
            return {'data': document.serialize("view")}

    @json_view(content_type="application/json", validators=(validate_patch_document_data,), permission='edit_auction')
    def patch(self):
        """Auction Award Document Update"""
        if self.request.validated['auction_status'] != 'active.qualification':
            self.request.errors.add('body', 'data', 'Can\'t update document in current ({}) auction status'.format(self.request.validated['auction_status']))
            self.request.errors.status = 403
            return
        if any([i.status != 'active' for i in self.request.validated['auction'].lots if i.id == self.request.validated['award'].lotID]):
            self.request.errors.add('body', 'data', 'Can update document only in active lot status')
            self.request.errors.status = 403
            return
        if apply_patch(self.request, src=self.request.context.serialize()):
            update_file_content_type(self.request)
            LOGGER.info('Updated auction award document {}'.format(self.request.context.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'auction_award_document_patch'}))
            return {'data': self.request.context.serialize("view")}
