""" Cornice services.
"""
from cornice.ext.spore import generate_spore_description
from cornice.service import Service, get_services
from cornice.resource import resource, view

from uuid import uuid4

from couchdb import Server

from .models import TenderDocument


server = Server()
spore = Service('spore', path='/spore', renderer='json')


def get_db(name='test'):
    if name not in server:
        server.create(name)
    return server[name]


def wrap_error(e):
    return {"errors": [str(e)]}


def wrap_data(data):
    return {"data": data}


@spore.get()
def get_spore(request):
    services = get_services()
    return generate_spore_description(services, 'Service name', request.application_url, '0.1')


@resource(name='Tender',
          collection_path='/tenders',
          path='/tenders/{id}',
          description="Open Contracting compatible data exchange format. See http://ocds.open-contracting.org/standard/r/master/#tender for more info")
class TenderResource(object):
    def __init__(self, request):
        self.request = request
        self.db = get_db()

    def collection_get(self):
        map_fun = """function(doc) { if (doc.doc_type == "TenderDocument") { emit(doc._id, doc);}}"""
        results = TenderDocument.query(self.db, map_fun, None)
        return {'tenders': [i.serialize("view") for i in results]}

    def collection_post(self):
        """Tender Create"""
        try:
            tender = TenderDocument(self.request.json_body)
            tender.id = uuid4().hex
            if not tender.tenderID:
                tender.tenderID = "UA-" + tender.id
            tender.store(self.db)
        except Exception as e:
            return wrap_error(e)
        self.request.response.status = 201
        return tender.serialize("view")

    @view(renderer='json')
    def get(self):
        """Tender Read"""
        try:
            tender = TenderDocument.load(self.db, self.request.matchdict['id'])
        except Exception as e:
            return wrap_error(e)
        if not tender:
            return wrap_error('Not Found')
        return wrap_data(tender.serialize("view"))

    def put(self):
        """Tender Edit (full)"""
        try:
            tender = TenderDocument.load(self.db, self.request.matchdict['id'])
            tender.import_data(self.request.json_body)
            tender.store(self.db)
        except Exception as e:
            return wrap_error(e)
        return wrap_data(tender.serialize("view"))

    def patch(self):
        """Tender Edit (partial)"""
        try:
            tender = TenderDocument.load(self.db, self.request.matchdict['id'])
            tender.import_data(self.request.json_body)
            tender.store(self.db)
        except Exception as e:
            return wrap_error(e)
        return wrap_data(tender.serialize("view"))


@resource(name='Tender Documents',
          collection_path='/tenders/{tender_id}/documents',
          path='/tenders/{tender_id}/documents/{id}',
          description="Tender related binary files (PDFs, etc.)")
class TenderDocumentResource(object):
    def __init__(self, request):
        self.request = request
        self.db = get_db()

    def collection_get(self):
        """Tender Documents List"""
        try:
            tender = TenderDocument.load(self.db, self.request.matchdict['tender_id'])
        except Exception as e:
            return wrap_error(e)
        return {'documents': getattr(tender, '_attachments', {})}

    def collection_post(self):
        """Tender Document Upload"""
        try:
            tender = TenderDocument.load(self.db, self.request.matchdict['tender_id'])
        except Exception as e:
            return wrap_error(e)
        try:
            for data in self.request.POST.values():
                self.db.put_attachment(tender, data.file, data.filename)
        except Exception as e:
            return wrap_error(e)
        return {'documents': getattr(tender, '_attachments', {})}

    def get(self):
        """Tender Document Read"""
        return self.db.fetch_attachment(self.request.matchdict['tender_id'], self.request.matchdict['id'])

    def put(self):
        """Tender Document Update"""
        try:
            tender = TenderDocument.load(self.db, self.request.matchdict['tender_id'])
        except Exception as e:
            return wrap_error(e)
        try:
            for data in self.request.POST.values():
                self.db.put_attachment(tender, data.file, data.filename)
        except Exception as e:
            return wrap_error(e)
        return getattr(tender, '_attachments', {}).get(self.request.matchdict['id'], {})
