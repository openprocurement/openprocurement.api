# -*- coding: utf-8 -*-
from datetime import timedelta
from logging import getLogger
from cornice.resource import resource, view
from iso8601 import parse_date
from openprocurement.api.design import (
    tenders_by_dateModified_view,
    tenders_real_by_dateModified_view,
    tenders_test_by_dateModified_view,
)
from openprocurement.api.models import Tender, get_now
from openprocurement.api.utils import (
    generate_id,
    generate_tender_id,
    save_tender,
    set_ownership,
    tender_serialize,
    apply_patch,
    add_next_award,
    error_handler,
    update_journal_handler_params,
)
from openprocurement.api.validation import (
    validate_patch_tender_data,
    validate_tender_data,
)


LOGGER = getLogger(__name__)
VIEW_MAP = {
    u'test': tenders_test_by_dateModified_view,
    u'_all_': tenders_by_dateModified_view,
}


@resource(name='Tender',
          collection_path='/tenders',
          path='/tenders/{tender_id}',
          description="Open Contracting compatible data exchange format. See http://ocds.open-contracting.org/standard/r/master/#tender for more info",
          error_handler=error_handler)
class TenderResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @view(renderer='json', permission='view_tender')
    def collection_get(self):
        """Tenders List

        Get Tenders List
        ----------------

        Example request to get tenders list:

        .. sourcecode:: http

            GET /tenders HTTP/1.1
            Host: example.com
            Accept: application/json

        This is what one should expect in response:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "data": [
                    {
                        "id": "64e93250be76435397e8c992ed4214d1",
                        "dateModified": "2014-10-27T08:06:58.158Z"
                    }
                ]
            }

        """
        # http://wiki.apache.org/couchdb/HTTP_view_API#Querying_Options
        params = {}
        fields = self.request.params.get('opt_fields', '')
        if fields:
            params['opt_fields'] = fields
        limit = self.request.params.get('limit', '')
        if limit:
            params['limit'] = limit
        limit = int(limit) if limit.isdigit() else 100
        descending = self.request.params.get('descending')
        offset = self.request.params.get('offset', '9' if descending else '')
        if descending:
            params['descending'] = descending
        mode = self.request.params.get('mode')
        if mode:
            params['mode'] = mode
        list_view = VIEW_MAP.get(mode, tenders_real_by_dateModified_view)
        if fields:
            LOGGER.info('Used custom fields for tenders list: {}'.format(','.join(sorted(fields.split(',')))), extra={'MESSAGE_ID': 'tender_list_custom'})
            fields = fields.split(',') + ['dateModified', 'id']
            list_view_name = '/'.join([list_view.design, list_view.name])
            results = [
                tender_serialize(i, fields)
                for i in Tender.view(self.db, list_view_name, limit=limit + 1, startkey=offset, descending=bool(descending), include_docs=True)
            ]
        else:
            results = [
                {'id': i.id, 'dateModified': i.key}
                for i in list_view(self.db, limit=limit + 1, startkey=offset, descending=bool(descending))
            ]
        if len(results) > limit:
            results, last = results[:-1], results[-1]
            params['offset'] = last['dateModified']
        elif len(results) > 0:
            params['offset'] = (parse_date(results[-1]['dateModified']) + timedelta(microseconds=-1 if descending else 1)).isoformat()
        else:
            params['offset'] = offset
        return {
            'data': results,
            'next_page': {
                "offset": params['offset'],
                "path": self.request.route_path('collection_Tender', _query=params),
                "uri": self.request.route_url('collection_Tender', _query=params)
            }
        }

    @view(content_type="application/json", permission='create_tender', validators=(validate_tender_data,), renderer='json')
    def collection_post(self):
        """This API request is targeted to creating new Tenders by procuring organizations.

        Creating new Tender
        -------------------

        Example request to create tender:

        .. sourcecode:: http

            POST /tenders HTTP/1.1
            Host: example.com
            Accept: application/json

            {
                "data": {
                    "procuringEntity": {
                        "id": {
                            "name": "Державне управління справами",
                            "scheme": "https://ns.openprocurement.org/ua/edrpou",
                            "uid": "00037256",
                            "uri": "http://www.dus.gov.ua/"
                        },
                        "address": {
                            "countryName": "Україна",
                            "postalCode": "01220",
                            "region": "м. Київ",
                            "locality": "м. Київ",
                            "streetAddress": "вул. Банкова, 11, корпус 1"
                        }
                    },
                    "value": {
                        "amount": 500,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": true
                    },
                    "itemsToBeProcured": [
                        {
                            "description": "футляри до державних нагород",
                            "primaryClassification": {
                                "scheme": "CPV",
                                "id": "44617100-9",
                                "description": "Cartons"
                            },
                            "additionalClassification": [
                                {
                                    "scheme": "ДКПП",
                                    "id": "17.21.1",
                                    "description": "папір і картон гофровані, паперова й картонна тара"
                                }
                            ],
                            "unitOfMeasure": "item",
                            "quantity": 5
                        }
                    ],
                    "enquiryPeriod": {
                        "endDate": "2014-10-31T00:00:00"
                    },
                    "tenderPeriod": {
                        "startDate": "2014-11-03T00:00:00",
                        "endDate": "2014-11-06T10:00:00"
                    },
                    "awardPeriod": {
                        "endDate": "2014-11-13T00:00:00"
                    },
                    "deliveryDate": {
                        "endDate": "2014-11-20T00:00:00"
                    },
                    "minimalStep": {
                        "amount": 35,
                        "currency": "UAH"
                    }
                }
            }

        This is what one should expect in response:

        .. sourcecode:: http

            HTTP/1.1 201 Created
            Location: http://localhost/api/0.1/tenders/64e93250be76435397e8c992ed4214d1
            Content-Type: application/json

            {
                "data": {
                    "id": "64e93250be76435397e8c992ed4214d1",
                    "tenderID": "UA-64e93250be76435397e8c992ed4214d1",
                    "dateModified": "2014-10-27T08:06:58.158Z",
                    "procuringEntity": {
                        "id": {
                            "name": "Державне управління справами",
                            "scheme": "https://ns.openprocurement.org/ua/edrpou",
                            "uid": "00037256",
                            "uri": "http://www.dus.gov.ua/"
                        },
                        "address": {
                            "countryName": "Україна",
                            "postalCode": "01220",
                            "region": "м. Київ",
                            "locality": "м. Київ",
                            "streetAddress": "вул. Банкова, 11, корпус 1"
                        }
                    },
                    "value": {
                        "amount": 500,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": true
                    },
                    "itemsToBeProcured": [
                        {
                            "description": "футляри до державних нагород",
                            "primaryClassification": {
                                "scheme": "CPV",
                                "id": "44617100-9",
                                "description": "Cartons"
                            },
                            "additionalClassification": [
                                {
                                    "scheme": "ДКПП",
                                    "id": "17.21.1",
                                    "description": "папір і картон гофровані, паперова й картонна тара"
                                }
                            ],
                            "unitOfMeasure": "item",
                            "quantity": 5
                        }
                    ],
                    "enquiryPeriod": {
                        "endDate": "2014-10-31T00:00:00"
                    },
                    "tenderPeriod": {
                        "startDate": "2014-11-03T00:00:00",
                        "endDate": "2014-11-06T10:00:00"
                    },
                    "awardPeriod": {
                        "endDate": "2014-11-13T00:00:00"
                    },
                    "deliveryDate": {
                        "endDate": "2014-11-20T00:00:00"
                    },
                    "minimalStep": {
                        "amount": 35,
                        "currency": "UAH"
                    }
                }
            }

        """
        tender_data = self.request.validated['data']
        tender_id = generate_id()
        tender = Tender(tender_data)
        tender.id = tender_id
        if not tender.enquiryPeriod.startDate:
            tender.enquiryPeriod.startDate = get_now()
        tender.tenderID = generate_tender_id(tender.enquiryPeriod.startDate, self.db)
        if not tender.tenderPeriod.startDate:
            tender.tenderPeriod.startDate = tender.enquiryPeriod.endDate
        set_ownership(tender, self.request)
        self.request.validated['tender'] = tender
        self.request.validated['tender_src'] = {}
        if save_tender(self.request):
            update_journal_handler_params({'tender_id': tender_id, 'tenderID': tender.tenderID})
            LOGGER.info('Created tender {} ({})'.format(tender_id, tender.tenderID), extra={'MESSAGE_ID': 'tender_create'})
            self.request.response.status = 201
            self.request.response.headers[
                'Location'] = self.request.route_url('Tender', tender_id=tender_id)
            return {
                'data': tender.serialize(tender.status),
                'access': {
                    'token': tender.owner_token
                }
            }

    @view(renderer='json', permission='view_tender')
    def get(self):
        """Tender Read

        Get Tender
        ----------

        Example request to get tender:

        .. sourcecode:: http

            GET /tenders/64e93250be76435397e8c992ed4214d1 HTTP/1.1
            Host: example.com
            Accept: application/json

        This is what one should expect in response:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "data": {
                    "id": "64e93250be76435397e8c992ed4214d1",
                    "tenderID": "UA-64e93250be76435397e8c992ed4214d1",
                    "dateModified": "2014-10-27T08:06:58.158Z",
                    "procuringEntity": {
                        "id": {
                            "name": "Державне управління справами",
                            "scheme": "https://ns.openprocurement.org/ua/edrpou",
                            "uid": "00037256",
                            "uri": "http://www.dus.gov.ua/"
                        },
                        "address": {
                            "countryName": "Україна",
                            "postalCode": "01220",
                            "region": "м. Київ",
                            "locality": "м. Київ",
                            "streetAddress": "вул. Банкова, 11, корпус 1"
                        }
                    },
                    "value": {
                        "amount": 500,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": true
                    },
                    "itemsToBeProcured": [
                        {
                            "description": "футляри до державних нагород",
                            "primaryClassification": {
                                "scheme": "CPV",
                                "id": "44617100-9",
                                "description": "Cartons"
                            },
                            "additionalClassification": [
                                {
                                    "scheme": "ДКПП",
                                    "id": "17.21.1",
                                    "description": "папір і картон гофровані, паперова й картонна тара"
                                }
                            ],
                            "unitOfMeasure": "item",
                            "quantity": 5
                        }
                    ],
                    "enquiryPeriod": {
                        "endDate": "2014-10-31T00:00:00"
                    },
                    "tenderPeriod": {
                        "startDate": "2014-11-03T00:00:00",
                        "endDate": "2014-11-06T10:00:00"
                    },
                    "awardPeriod": {
                        "endDate": "2014-11-13T00:00:00"
                    },
                    "deliveryDate": {
                        "endDate": "2014-11-20T00:00:00"
                    },
                    "minimalStep": {
                        "amount": 35,
                        "currency": "UAH"
                    }
                }
            }

        """
        tender = self.request.validated['tender']
        tender_data = tender.serialize('view' if self.request.authenticated_role == 'chronograph' else tender.status)
        return {'data': tender_data}

    #@view(content_type="application/json", validators=(validate_tender_data, ), permission='edit_tender', renderer='json')
    #def put(self):
        #"""Tender Edit (full)"""
        #tender = self.request.validated['tender']
        #if tender.status in ['complete', 'unsuccessful', 'cancelled']:
            #self.request.errors.add('body', 'data', 'Can\'t update tender in current ({}) status'.format(tender.status))
            #self.request.errors.status = 403
            #return
        #apply_patch(self.request, src=self.request.validated['tender_src'])
        #return {'data': tender.serialize(tender.status)}

    @view(content_type="application/json", validators=(validate_patch_tender_data, ), permission='edit_tender', renderer='json')
    def patch(self):
        """Tender Edit (partial)

        For example here is how procuring entity can change number of items to be procured and total Value of a tender:

        .. sourcecode:: http

            PATCH /tenders/4879d3f8ee2443169b5fbbc9f89fa607 HTTP/1.1
            Host: example.com
            Accept: application/json

            {
                "data": {
                    "value": {
                        "amount": 600
                    },
                    "itemsToBeProcured": [
                        {
                            "quantity": 6
                        }
                    ]
                }
            }

        And here is the response to be expected:

        .. sourcecode:: http

            HTTP/1.0 200 OK
            Content-Type: application/json

            {
                "data": {
                    "id": "4879d3f8ee2443169b5fbbc9f89fa607",
                    "tenderID": "UA-64e93250be76435397e8c992ed4214d1",
                    "dateModified": "2014-10-27T08:12:34.956Z",
                    "value": {
                        "amount": 600
                    },
                    "itemsToBeProcured": [
                        {
                            "quantity": 6
                        }
                    ]
                }
            }

        """
        tender = self.request.validated['tender']
        if self.request.authenticated_role != 'Administrator' and tender.status in ['complete', 'unsuccessful', 'cancelled']:
            self.request.errors.add('body', 'data', 'Can\'t update tender in current ({}) status'.format(tender.status))
            self.request.errors.status = 403
            return
        data = self.request.validated['data']
        if self.request.authenticated_role == 'tender_owner' and 'status' in data and data['status'] not in ['cancelled', tender.status]:
            self.request.errors.add('body', 'data', 'Can\'t update tender status')
            self.request.errors.status = 403
            return
        if self.request.authenticated_role == 'chronograph' and tender.status == 'active.tendering' and data.get('status', tender.status) == 'active.qualification' and tender.numberOfBids == 1:
            apply_patch(self.request, save=False, src=self.request.validated['tender_src'])
            add_next_award(self.request)
            save_tender(self.request)
        else:
            apply_patch(self.request, src=self.request.validated['tender_src'])
        LOGGER.info('Updated tender {}'.format(tender.id), extra={'MESSAGE_ID': 'tender_patch'})
        return {'data': tender.serialize(tender.status)}
