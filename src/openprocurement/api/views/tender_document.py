# -*- coding: utf-8 -*-
from logging import getLogger
from functools import partial
from cornice.resource import resource, view
from openprocurement.api.utils import (
    get_file,
    save_tender,
    upload_file,
    apply_patch,
    error_handler,
    update_journal_handler_params,
    update_file_content_type,
    filter_by_fields,
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
          description="Tender related binary files (PDFs, etc.)",
          error_handler=error_handler)
class TenderDocumentResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @view(renderer='json', permission='view_tender')
    def collection_get(self):
        """Tender Documents List"""
        filter_fields = partial(filter_by_fields, request=self.request)
        if self.request.params.get('all', ''):
            collection_data = [filter_fields(i.serialize("view")) for i in self.request.context['documents']]
        else:
            collection_data = map(filter_fields, sorted(dict([
                (i.id, i.serialize("view"))
                for i in self.request.context['documents']
            ]).values(), key=lambda i: i['dateModified']))
        return {'data': collection_data}

    @view(renderer='json', permission='upload_tender_documents', validators=(validate_file_upload,))
    def collection_post(self):
        """Tender Document Upload"""
        if self.request.authenticated_role != 'auction' and self.request.validated['tender_status'] != 'active.enquiries' or \
           self.request.authenticated_role == 'auction' and self.request.validated['tender_status'] not in ['active.auction', 'active.qualification']:
            self.request.errors.add('body', 'data', 'Can\'t add document in current ({}) tender status'.format(self.request.validated['tender_status']))
            self.request.errors.status = 403
            return
        document = upload_file(self.request)
        self.request.validated['tender'].documents.append(document)
        if save_tender(self.request):
            update_journal_handler_params({'document_id': document.id})
            LOGGER.info('Created tender document {}'.format(document.id), extra={'MESSAGE_ID': 'tender_document_create'})
            self.request.response.status = 201
            document_route = self.request.matched_route.name.replace("collection_", "")
            self.request.response.headers['Location'] = self.request.current_route_url(_route_name=document_route, document_id=document.id, _query={})
            return {'data': filter_by_fields(document.serialize("view"), self.request)}

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
        return {'data': filter_by_fields(document_data, self.request)}

    @view(renderer='json', permission='upload_tender_documents', validators=(validate_file_update,))
    def put(self):
        """Tender Document Update"""
        if self.request.authenticated_role != 'auction' and self.request.validated['tender_status'] != 'active.enquiries' or \
           self.request.authenticated_role == 'auction' and self.request.validated['tender_status'] not in ['active.auction', 'active.qualification']:
            self.request.errors.add('body', 'data', 'Can\'t update document in current ({}) tender status'.format(self.request.validated['tender_status']))
            self.request.errors.status = 403
            return
        document = upload_file(self.request)
        self.request.validated['tender'].documents.append(document)
        if save_tender(self.request):
            LOGGER.info('Updated tender document {}'.format(self.request.context.id), extra={'MESSAGE_ID': 'tender_document_put'})
            return {'data': filter_by_fields(document.serialize("view"), self.request)}

    @view(content_type="application/json", renderer='json', permission='upload_tender_documents', validators=(validate_patch_document_data,))
    def patch(self):
        """Tender Document Update"""
        if self.request.authenticated_role != 'auction' and self.request.validated['tender_status'] != 'active.enquiries' or \
           self.request.authenticated_role == 'auction' and self.request.validated['tender_status'] not in ['active.auction', 'active.qualification']:
            self.request.errors.add('body', 'data', 'Can\'t update document in current ({}) tender status'.format(self.request.validated['tender_status']))
            self.request.errors.status = 403
            return
        if apply_patch(self.request, src=self.request.context.serialize()):
            update_file_content_type(self.request)
            LOGGER.info('Updated tender document {}'.format(self.request.context.id), extra={'MESSAGE_ID': 'tender_document_patch'})
            return {'data': filter_by_fields(self.request.context.serialize("view"), self.request)}
