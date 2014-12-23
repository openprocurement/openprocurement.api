# -*- coding: utf-8 -*-
from cornice.resource import resource, view
from openprocurement.api.models import Document
from openprocurement.api.utils import (
    generate_id,
    get_file,
    save_tender,
    upload_file,
)
from openprocurement.api.validation import (
    validate_file_update,
    validate_file_upload,
    validate_patch_document_data,
)


@resource(name='Tender Award Complaint Documents',
          collection_path='/tenders/{tender_id}/awards/{award_id}/complaints/{complaint_id}/documents',
          path='/tenders/{tender_id}/awards/{award_id}/complaints/{complaint_id}/documents/{document_id}',
          description="Tender award complaint documents")
class TenderAwardComplaintDocumentResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @view(renderer='json', permission='view_tender')
    def collection_get(self):
        """Tender Award Complaint Documents List"""
        complaint = self.request.validated['complaint']
        if self.request.params.get('all', ''):
            collection_data = [i.serialize("view") for i in complaint['documents']]
        else:
            collection_data = sorted(dict([
                (i.id, i.serialize("view"))
                for i in complaint['documents']
            ]).values(), key=lambda i: i['dateModified'])
        return {'data': collection_data}

    @view(renderer='json', permission='review_complaint', validators=(validate_file_upload,))
    def collection_post(self):
        """Tender Award Complaint Document Upload
        """
        tender = self.request.validated['tender']
        if tender.status not in ['active.qualification', 'active.awarded']:
            self.request.errors.add('body', 'data', 'Can\'t add document in current tender status')
            self.request.errors.status = 403
            return
        document = upload_file(self.request)
        self.request.validated['complaint'].documents.append(document)
        save_tender(self.request)
        self.request.response.status = 201
        document_route = self.request.matched_route.name.replace("collection_", "")
        self.request.response.headers['Location'] = self.request.current_route_url(_route_name=document_route, document_id=document.id)
        return {'data': document.serialize("view")}

    @view(renderer='json', permission='view_tender')
    def get(self):
        """Tender Award Complaint Document Read"""
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

    @view(renderer='json', validators=(validate_file_update,), permission='review_complaint')
    def put(self):
        """Tender Award Complaint Document Update"""
        tender = self.request.validated['tender']
        if tender.status not in ['active.qualification', 'active.awarded']:
            self.request.errors.add('body', 'data', 'Can\'t update document in current tender status')
            self.request.errors.status = 403
            return
        document = upload_file(self.request)
        self.request.validated['complaint'].documents.append(document)
        save_tender(self.request)
        return {'data': document.serialize("view")}

    @view(renderer='json', validators=(validate_patch_document_data,), permission='review_complaint')
    def patch(self):
        """Tender Award Complaint Document Update"""
        if self.request.validated['tender_status'] not in ['active.qualification', 'active.awarded']:
            self.request.errors.add('body', 'data', 'Can\'t update document in current tender status')
            self.request.errors.status = 403
            return
        document = self.request.validated['document']
        document_data = self.request.validated['data']
        if document_data:
            document.import_data(document_data)
            document.dateModified = None
            save_tender(self.request)
        return {'data': document.serialize("view")}
