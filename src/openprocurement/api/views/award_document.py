# -*- coding: utf-8 -*-
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


@opresource(name='Tender Award Documents',
            collection_path='/tenders/{tender_id}/awards/{award_id}/documents',
            path='/tenders/{tender_id}/awards/{award_id}/documents/{document_id}',
            procurementMethodType='belowThreshold',
            description="Tender award documents")
class TenderAwardDocumentResource(APIResource):

    def validate_award_document(self, operation):
        if self.request.validated['tender_status'] != 'active.qualification':
            self.request.errors.add('body', 'data', 'Can\'t {} document in current ({}) tender status'.format(operation, self.request.validated['tender_status']))
            self.request.errors.status = 403
            return
        if any([i.status != 'active' for i in self.request.validated['tender'].lots if i.id == self.request.validated['award'].lotID]):
            self.request.errors.add('body', 'data', 'Can {} document only in active lot status'.format(operation))
            self.request.errors.status = 403
            return
        if operation == 'update' and self.request.authenticated_role != self.context.author:
            self.request.errors.add('url', 'role', 'Can update document only author')
            self.request.errors.status = 403
            return
        return True

    @json_view(permission='view_tender')
    def collection_get(self):
        """Tender Award Documents List"""
        if self.request.params.get('all', ''):
            collection_data = [i.serialize("view") for i in self.context.documents]
        else:
            collection_data = sorted(dict([
                (i.id, i.serialize("view"))
                for i in self.context.documents
            ]).values(), key=lambda i: i['dateModified'])
        return {'data': collection_data}

    @json_view(validators=(validate_file_upload,), permission='upload_tender_documents')
    def collection_post(self):
        """Tender Award Document Upload
        """
        if not self.validate_award_document('add'):
            return
        document = upload_file(self.request)
        self.context.documents.append(document)
        if save_tender(self.request):
            self.LOGGER.info('Created tender award document {}'.format(document.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_award_document_create'}, {'document_id': document.id}))
            self.request.response.status = 201
            document_route = self.request.matched_route.name.replace("collection_", "")
            self.request.response.headers['Location'] = self.request.current_route_url(_route_name=document_route, document_id=document.id, _query={})
            return {'data': document.serialize("view")}

    @json_view(permission='view_tender')
    def get(self):
        """Tender Award Document Read"""
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

    @json_view(validators=(validate_file_update,), permission='edit_tender')
    def put(self):
        """Tender Award Document Update"""
        if not self.validate_award_document('update'):
            return
        document = upload_file(self.request)
        self.request.validated['award'].documents.append(document)
        if save_tender(self.request):
            self.LOGGER.info('Updated tender award document {}'.format(self.request.context.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_award_document_put'}))
            return {'data': document.serialize("view")}

    @json_view(content_type="application/json", validators=(validate_patch_document_data,), permission='edit_tender')
    def patch(self):
        """Tender Award Document Update"""
        if not self.validate_award_document('update'):
            return
        if apply_patch(self.request, src=self.request.context.serialize()):
            update_file_content_type(self.request)
            self.LOGGER.info('Updated tender award document {}'.format(self.request.context.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_award_document_patch'}))
            return {'data': self.request.context.serialize("view")}
