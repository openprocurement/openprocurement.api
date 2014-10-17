# -*- coding: utf-8 -*-
""" Cornice services.
"""
from cornice.ext.spore import generate_spore_description
from cornice.service import Service, get_services
from cornice.resource import resource, view
from schematics.exceptions import ModelValidationError, ModelConversionError
from uuid import uuid4
from openprocurement.api.models import TenderDocument


spore = Service('spore', path='/spore', renderer='json')


def wrap_error(e):
    return {"errors": [str(e)]}


def wrap_data(data):
    return {"data": data}


def validate_data(request):
    try:
        json = request.json_body
    except ValueError, e:
        request.errors.add('body', 'data', e.message)
        request.errors.status = 422
        return
    if not isinstance(json, dict) or 'data' not in json:
        request.errors.add('body', 'data', "Data not available")
        request.errors.status = 422
        return
    data = json['data']
    try:
        TenderDocument(data).validate()
    except (ModelValidationError, ModelConversionError), e:
        for i in e.message:
            request.errors.add('body', i, e.message[i])
        request.errors.status = 422


def generate_tender_id(tid):
    return "UA-2014-DUS-" + tid


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
        self.db = request.registry.db

    def collection_get(self):
        # limit, skip, descending
        results = TenderDocument.view(self.db, 'tenders/all')
        return {'tenders': [i.serialize("view") for i in results]}

    @view(content_type="application/json", validators=(validate_data,))
    def collection_post(self):
        """This API request is targeted to creating new Tenders by procuring organizations.

        Creating new Tender
        -------------------

        Example request to create tender::

         POST /tenders

         {
             "data":{
                 "procuringEntity":{
                     "id":{
                         "name":"Державне управління справами",
                         "scheme":"https://ns.openprocurement.org/ua/edrpou",
                         "uid":"00037256",
                         "uri":"http://www.dus.gov.ua/"
                     },
                     "address":{
                         "country-name":"Україна",
                         "postal-code":"01220",
                         "region":"м. Київ",
                         "locality":"м. Київ",
                         "street-address":" вул. Банкова, 11, корпус 1"
                     },
                 },
                "totalValue":{
                    "amount":500,
                    "currency":"UAH"
                },
                "itemsToBeProcured":[
                    {
                        "description":"футляри до державних нагород",
                        "classificationScheme":"Other",
                        "otherClassificationScheme":"ДКПП",
                        "classificationID":"17.21.1",
                        "classificationDescription":"папір і картон гофровані, паперова й картонна тара",
                        "unitOfMeasure":"item",
                        "quantity":5
                    }
                ],
                "clarificationPeriod":{
                    "endDate":"2014-10-31T00:00:00"
                },
                "tenderPeriod":{
                    "endDate":"2014-11-06T10:00:00"
                },
                "awardPeriod":{
                    "endDate":"2014-11-13T00:00:00"
                }
            }
         }

        This is what one should expect in response::

         HTTP/1.1 201 Created

         {
             "data": {
                 "id": "4879d3f8-ee24-4316-9b5f-bbc9f89fa607",
                 "tenderID": "UA-2014-DUS-156",
                 "modifiedAt": "2014-10-27T08:06:58.158Z",
                 ...
             }
         }
        """
        try:
            tender = TenderDocument(self.request.json_body['data'])
            tender.id = uuid4().hex
            tender.tenderID = generate_tender_id(tender.id)
            tender.store(self.db)
        except Exception, e:
            return wrap_error(e)
        self.request.response.status = 201
        return wrap_data(tender.serialize("view"))

    @view(renderer='json')
    def get(self):
        """Tender Read"""
        try:
            tender = TenderDocument.load(self.db, self.request.matchdict['id'])
        except Exception, e:
            return wrap_error(e)
        if not tender:
            self.request.errors.add('url', 'id', 'Not Found')
            self.request.errors.status = 404
            return
        return wrap_data(tender.serialize("view"))

    @view(content_type="application/json", validators=(validate_data,))
    def put(self):
        """Tender Edit (full)"""
        try:
            tender = TenderDocument.load(self.db, self.request.matchdict['id'])
            tender.import_data(self.request.json_body['data'])
            tender.store(self.db)
        except Exception, e:
            return wrap_error(e)
        return wrap_data(tender.serialize("view"))

    @view(content_type="application/json", validators=(validate_data,))
    def patch(self):
        """Tender Edit (partial)

        For example here is how procuring entity can change number of items to be procured and total Value of a tender::

         PATCH /tenders/4879d3f8-ee24-4316-9b5f-bbc9f89fa607

         {
             "data": {
                 "totalValue":{
                     "amount":600,
                 },
                 "itemsToBeProcured":[
                     {
                         "quantity":6
                     }
                 ]
             }
         }

        And here is the response to be expected::

         HTTP/1.0 200 OK

         {
             "data": {
                 "id": "4879d3f8-ee24-4316-9b5f-bbc9f89fa607",
                 "tenderID": "UA-2014-DUS-156",
                 "modifiedAt": "2014-10-27T08:12:34.956Z",
                 ...
             }
         }
        """
        try:
            tender = TenderDocument.load(self.db, self.request.matchdict['id'])
            tender.import_data(self.request.json_body['data'])
            tender.store(self.db)
        except Exception, e:
            return wrap_error(e)
        return wrap_data(tender.serialize("view"))


@resource(name='Tender Documents',
          collection_path='/tenders/{tender_id}/documents',
          path='/tenders/{tender_id}/documents/{id}',
          description="Tender related binary files (PDFs, etc.)")
class TenderDocumentResource(object):
    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    def collection_get(self):
        """Tender Documents List"""
        try:
            tender = TenderDocument.load(self.db, self.request.matchdict['tender_id'])
        except Exception, e:
            return wrap_error(e)
        return {'documents': tender['_attachments']}

    def collection_post(self):
        """Tender Document Upload"""
        try:
            tender = TenderDocument.load(self.db, self.request.matchdict['tender_id'])
        except Exception, e:
            return wrap_error(e)
        try:
            for data in self.request.POST.values():
                self.db.put_attachment(tender._data, data.file, data.filename)
        except Exception, e:
            return wrap_error(e)
        tender = tender.reload(self.db)
        self.request.response.status = 201
        return {'documents': tender['_attachments']}

    def get(self):
        """Tender Document Read"""
        data = self.db.get_attachment(self.request.matchdict['tender_id'], self.request.matchdict['id'])
        self.request.response.body_file = data
        return self.request.response

    def put(self):
        """Tender Document Update"""
        try:
            tender = TenderDocument.load(self.db, self.request.matchdict['tender_id'])
        except Exception, e:
            return wrap_error(e)
        try:
            for data in self.request.POST.values():
                self.db.put_attachment(tender, data.file, data.filename)
        except Exception, e:
            return wrap_error(e)
        tender = tender.reload(self.db)
        return tender['_attachments'].get(self.request.matchdict['id'], {})
