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


@resource(name='Tender Documents',
          collection_path='/tenders/{tender_id}/documents',
          path='/tenders/{tender_id}/documents/{document_id}',
          description="Tender related binary files (PDFs, etc.)")
class TenderDocumentResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @view(renderer='json', permission='view_tender')
    def collection_get(self):
        """Tender Documents List"""
        tender = self.request.validated['tender']
        if self.request.params.get('all', ''):
            collection_data = [i.serialize("view") for i in tender['documents']]
        else:
            collection_data = sorted(dict([
                (i.id, i.serialize("view"))
                for i in tender['documents']
            ]).values(), key=lambda i: i['dateModified'])
        return {'data': collection_data}

    @view(renderer='json', permission='edit_tender', validators=(validate_file_upload,))
    def collection_post(self):
        """Tender Document Upload"""
        tender = self.request.validated['tender']
        if tender.status != 'active.enquiries':
            self.request.errors.add('body', 'data', 'Can\'t add document in current tender status')
            self.request.errors.status = 403
            return
        document = upload_file(self.request)
        tender.documents.append(document)
        save_tender(self.request)
        LOGGER.info('Created tender document {}'.format(document.id))
        self.request.response.status = 201
        document_route = self.request.matched_route.name.replace("collection_", "")
        self.request.response.headers['Location'] = self.request.current_route_url(_route_name=document_route, document_id=document.id, _query={})
        return {'data': document.serialize("view")}

    @view(permission='view_tender')
    def get(self):
        """Tender Document Read"""
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

    @view(renderer='json', permission='edit_tender', validators=(validate_file_update,))
    def put(self):
        """Tender Document Update"""
        tender = self.request.validated['tender']
        if tender.status != 'active.enquiries':
            self.request.errors.add('body', 'data', 'Can\'t update document in current tender status')
            self.request.errors.status = 403
            return
        document = upload_file(self.request)
        tender.documents.append(document)
        save_tender(self.request)
        LOGGER.info('Updated tender document {}'.format(self.request.context.id))
        return {'data': document.serialize("view")}

    @view(renderer='json', permission='edit_tender', validators=(validate_patch_document_data,))
    def patch(self):
        """Tender Document Update"""
        if self.request.validated['tender_status'] != 'active.enquiries':
            self.request.errors.add('body', 'data', 'Can\'t update document in current tender status')
            self.request.errors.status = 403
            return
        apply_patch(self.request, src=self.request.context.serialize())
        LOGGER.info('Updated tender document {}'.format(self.request.context.id))
        return {'data': self.request.context.serialize("view")}
