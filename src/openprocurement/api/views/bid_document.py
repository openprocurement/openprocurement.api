# -*- coding: utf-8 -*-
from cornice.resource import resource, view
from uuid import uuid4
from openprocurement.api.models import Document, Revision
from openprocurement.api.utils import (
    filter_data,
    get_file,
    get_revision_changes,
    upload_file,
)
from openprocurement.api.validation import (
    validate_file_update,
    validate_file_upload,
    validate_patch_document_data,
    validate_tender_bid_document_exists,
    validate_tender_bid_exists_by_bid_id,
)


@resource(name='Tender Bid Documents',
          collection_path='/tenders/{tender_id}/bids/{bid_id}/documents',
          path='/tenders/{tender_id}/bids/{bid_id}/documents/{id}',
          description="Tender bidder documents")
class TenderBidderDocumentResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @view(renderer='json', validators=(validate_tender_bid_exists_by_bid_id,))
    def collection_get(self):
        """Tender Bid Documents List"""
        bid = self.request.validated['bid']
        if self.request.params.get('all', ''):
            collection_data = [i.serialize("view") for i in bid['documents']]
        else:
            collection_data = sorted(dict([
                (i.id, i.serialize("view"))
                for i in bid['documents']
            ]).values(), key=lambda i: i['dateModified'])
        return {'data': collection_data}

    @view(renderer='json', validators=(validate_file_upload, validate_tender_bid_exists_by_bid_id,))
    def collection_post(self):
        """Tender Bid Document Upload
        """
        tender = self.request.validated['tender']
        if tender.status not in ['tendering', 'auction', 'qualification']:
            self.request.errors.add('body', 'data', 'Can\'t add document in current tender status')
            self.request.errors.status = 403
            return
        src = tender.serialize("plain")
        data = self.request.validated['file']
        document = Document()
        document.id = uuid4().hex
        document.title = data.filename
        document.format = data.type
        key = uuid4().hex
        document.url = self.request.route_url('Tender Bid Documents', tender_id=tender.id, bid_id=self.request.validated['bid_id'], id=document.id, _query={'download': key})
        self.request.validated['bid'].documents.append(document)
        upload_file(tender, document, key, data.file, self.request)
        patch = get_revision_changes(tender.serialize("plain"), src)
        tender.revisions.append(Revision({'changes': patch}))
        try:
            tender.store(self.db)
        except Exception, e:
            return self.request.errors.add('body', 'data', str(e))
        self.request.response.status = 201
        self.request.response.headers['Location'] = self.request.route_url('Tender Bid Documents', tender_id=tender.id, bid_id=self.request.validated['bid_id'], id=document.id)
        return {'data': document.serialize("view")}

    @view(renderer='json', validators=(validate_tender_bid_document_exists,))
    def get(self):
        """Tender Bid Document Read"""
        document = self.request.validated['document']
        key = self.request.params.get('download')
        if key:
            return get_file(self.request.validated['tender'], document, key, self.db, self.request)
        document_data = document.serialize("view")
        document_data['previousVersions'] = [
            i.serialize("view")
            for i in self.request.validated['documents']
            if i.url != document.url
        ]
        return {'data': document_data}

    @view(renderer='json', validators=(validate_file_update, validate_tender_bid_document_exists,))
    def put(self):
        """Tender Bid Document Update"""
        tender = self.request.validated['tender']
        first_document = self.request.validated['documents'][0]
        if tender.status not in ['tendering', 'auction', 'qualification']:
            self.request.errors.add('body', 'data', 'Can\'t update document in current tender status')
            self.request.errors.status = 403
            return
        src = tender.serialize("plain")
        if self.request.content_type == 'multipart/form-data':
            data = self.request.validated['file']
            filename = data.filename
            content_type = data.type
            in_file = data.file
        else:
            filename = first_document.title
            content_type = self.request.content_type
            in_file = self.request.body_file
        document = Document()
        document.id = self.request.matchdict['id']
        document.title = filename
        document.format = content_type
        document.datePublished = first_document.datePublished
        key = uuid4().hex
        document.url = self.request.route_url('Tender Bid Documents', tender_id=tender.id, bid_id=self.request.validated['bid_id'], id=document.id, _query={'download': key})
        self.request.validated['bid'].documents.append(document)
        upload_file(tender, document, key, in_file, self.request)
        patch = get_revision_changes(tender.serialize("plain"), src)
        tender.revisions.append(Revision({'changes': patch}))
        try:
            tender.store(self.db)
        except Exception, e:
            return self.request.errors.add('body', 'data', str(e))
        return {'data': document.serialize("view")}

    @view(renderer='json', validators=(validate_patch_document_data, validate_tender_bid_document_exists,))
    def patch(self):
        """Tender Bid Document Update"""
        tender = self.request.validated['tender']
        if tender.status not in ['tendering', 'auction', 'qualification']:
            self.request.errors.add('body', 'data', 'Can\'t update document in current tender status')
            self.request.errors.status = 403
            return
        document = self.request.validated['document']
        document_data = filter_data(self.request.validated['data'])
        if document_data:
            src = tender.serialize("plain")
            document.import_data(document_data)
            patch = get_revision_changes(tender.serialize("plain"), src)
            if patch:
                tender.revisions.append(Revision({'changes': patch}))
                try:
                    tender.store(self.db)
                except Exception, e:
                    return self.request.errors.add('body', 'data', str(e))
        return {'data': document.serialize("view")}
