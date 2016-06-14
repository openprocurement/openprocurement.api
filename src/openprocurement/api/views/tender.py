# -*- coding: utf-8 -*-
from functools import partial
from openprocurement.api.design import (
    FIELDS,
    tenders_by_dateModified_view,
    tenders_real_by_dateModified_view,
    tenders_test_by_dateModified_view,
    tenders_by_local_seq_view,
    tenders_real_by_local_seq_view,
    tenders_test_by_local_seq_view,
)
from openprocurement.api.models import get_now
from openprocurement.api.utils import (
    apply_patch,
    check_status,
    context_unpack,
    decrypt,
    encrypt,
    generate_id,
    generate_tender_id,
    json_view,
    opresource,
    save_tender,
    set_ownership,
    tender_serialize,
    APIResource,
)
from openprocurement.api.validation import (
    validate_patch_tender_data,
    validate_tender_data,
)


VIEW_MAP = {
    u'': tenders_real_by_dateModified_view,
    u'test': tenders_test_by_dateModified_view,
    u'_all_': tenders_by_dateModified_view,
}
CHANGES_VIEW_MAP = {
    u'': tenders_real_by_local_seq_view,
    u'test': tenders_test_by_local_seq_view,
    u'_all_': tenders_by_local_seq_view,
}
FEED = {
    u'dateModified': VIEW_MAP,
    u'changes': CHANGES_VIEW_MAP,
}


@opresource(name='Tenders',
            path='/tenders',
            description="Open Contracting compatible data exchange format. See http://ocds.open-contracting.org/standard/r/master/#tender for more info")
class TendersResource(APIResource):

    def __init__(self, request, context):
        super(TendersResource, self).__init__(request, context)
        self.server = request.registry.couchdb_server
        self.update_after = request.registry.update_after

    @json_view(permission='view_tender')
    def get(self):
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
        pparams = {}
        fields = self.request.params.get('opt_fields', '')
        if fields:
            params['opt_fields'] = fields
            pparams['opt_fields'] = fields
            fields = fields.split(',')
            view_fields = fields + ['dateModified', 'id']
        limit = self.request.params.get('limit', '')
        if limit:
            params['limit'] = limit
            pparams['limit'] = limit
        limit = int(limit) if limit.isdigit() and (100 if fields else 1000) >= int(limit) > 0 else 100
        descending = bool(self.request.params.get('descending'))
        offset = self.request.params.get('offset', '')
        if descending:
            params['descending'] = 1
        else:
            pparams['descending'] = 1
        feed = self.request.params.get('feed', '')
        view_map = FEED.get(feed, VIEW_MAP)
        changes = view_map is CHANGES_VIEW_MAP
        if feed and feed in FEED:
            params['feed'] = feed
            pparams['feed'] = feed
        mode = self.request.params.get('mode', '')
        if mode and mode in view_map:
            params['mode'] = mode
            pparams['mode'] = mode
        view_limit = limit + 1 if offset else limit
        if changes:
            if offset:
                view_offset = decrypt(self.server.uuid, self.db.name, offset)
                if view_offset and view_offset.isdigit():
                    view_offset = int(view_offset)
                else:
                    self.request.errors.add('params', 'offset', 'Offset expired/invalid')
                    self.request.errors.status = 404
                    return
            if not offset:
                view_offset = 'now' if descending else 0
        else:
            if offset:
                view_offset = offset
            else:
                view_offset = '9' if descending else ''
        list_view = view_map.get(mode, view_map[u''])
        if self.update_after:
            view = partial(list_view, self.db, limit=view_limit, startkey=view_offset, descending=descending, stale='update_after')
        else:
            view = partial(list_view, self.db, limit=view_limit, startkey=view_offset, descending=descending)
        if fields:
            if not changes and set(fields).issubset(set(FIELDS)):
                results = [
                    (dict([(i, j) for i, j in x.value.items() + [('id', x.id), ('dateModified', x.key)] if i in view_fields]), x.key)
                    for x in view()
                ]
            elif changes and set(fields).issubset(set(FIELDS)):
                results = [
                    (dict([(i, j) for i, j in x.value.items() + [('id', x.id)] if i in view_fields]), x.key)
                    for x in view()
                ]
            elif fields:
                self.LOGGER.info('Used custom fields for tenders list: {}'.format(','.join(sorted(fields))),
                            extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_list_custom'}))

                results = [
                    (tender_serialize(self.request, i[u'doc'], view_fields), i.key)
                    for i in view(include_docs=True)
                ]
        else:
            results = [
                ({'id': i.id, 'dateModified': i.value['dateModified']} if changes else {'id': i.id, 'dateModified': i.key}, i.key)
                for i in view()
            ]
        if results:
            params['offset'], pparams['offset'] = results[-1][1], results[0][1]
            if offset and view_offset == results[0][1]:
                results = results[1:]
            elif offset and view_offset != results[0][1]:
                results = results[:limit]
                params['offset'], pparams['offset'] = results[-1][1], view_offset
            results = [i[0] for i in results]
            if changes:
                params['offset'] = encrypt(self.server.uuid, self.db.name, params['offset'])
                pparams['offset'] = encrypt(self.server.uuid, self.db.name, pparams['offset'])
        else:
            params['offset'] = offset
            pparams['offset'] = offset
        data = {
            'data': results,
            'next_page': {
                "offset": params['offset'],
                "path": self.request.route_path('Tenders', _query=params),
                "uri": self.request.route_url('Tenders', _query=params)
            }
        }
        if descending or offset:
            data['prev_page'] = {
                "offset": pparams['offset'],
                "path": self.request.route_path('Tenders', _query=pparams),
                "uri": self.request.route_url('Tenders', _query=pparams)
            }
        return data

    @json_view(content_type="application/json", permission='create_tender', validators=(validate_tender_data,))
    def post(self):
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
        tender_id = generate_id()
        tender = self.request.validated['tender']
        tender.id = tender_id
        tender.tenderID = generate_tender_id(get_now(), self.db, self.server_id)
        if hasattr(tender, "initialize"):
            tender.initialize()
        if self.request.json_body['data'].get('status') == 'draft':
            tender.status = 'draft'
        transfer = tender.transfer_token
        set_ownership(tender, self.request)
        self.request.validated['tender'] = tender
        self.request.validated['tender_src'] = {}
        if save_tender(self.request):
            self.LOGGER.info('Created tender {} ({})'.format(tender_id, tender.tenderID),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_create'}, {'tender_id': tender_id, 'tenderID': tender.tenderID}))
            self.request.response.status = 201
            self.request.response.headers[
                'Location'] = self.request.route_url('Tender', tender_id=tender_id)
            return {
                'data': tender.serialize(tender.status),
                'access': {
                    'token': tender.owner_token,
                    'transfer': transfer
                }
            }


@opresource(name='Tender',
            path='/tenders/{tender_id}',
            procurementMethodType='belowThreshold',
            description="Open Contracting compatible data exchange format. See http://ocds.open-contracting.org/standard/r/master/#tender for more info")
class TenderResource(APIResource):

    @json_view(permission='view_tender')
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
        if self.request.authenticated_role == 'chronograph':
            tender_data = self.context.serialize('chronograph_view')
        else:
            tender_data = self.context.serialize(self.context.status)
        return {'data': tender_data}

    #@json_view(content_type="application/json", validators=(validate_tender_data, ), permission='edit_tender')
    #def put(self):
        #"""Tender Edit (full)"""
        #tender = self.request.validated['tender']
        #if tender.status in ['complete', 'unsuccessful', 'cancelled']:
            #self.request.errors.add('body', 'data', 'Can\'t update tender in current ({}) status'.format(tender.status))
            #self.request.errors.status = 403
            #return
        #apply_patch(self.request, src=self.request.validated['tender_src'])
        #return {'data': tender.serialize(tender.status)}

    @json_view(content_type="application/json", validators=(validate_patch_tender_data, ), permission='edit_tender')
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
        tender = self.context
        if self.request.authenticated_role != 'Administrator' and tender.status in ['complete', 'unsuccessful', 'cancelled']:
            self.request.errors.add('body', 'data', 'Can\'t update tender in current ({}) status'.format(tender.status))
            self.request.errors.status = 403
            return
        if self.request.authenticated_role == 'chronograph':
            apply_patch(self.request, save=False, src=self.request.validated['tender_src'])
            check_status(self.request)
            save_tender(self.request)
        else:
            apply_patch(self.request, src=self.request.validated['tender_src'])
        self.LOGGER.info('Updated tender {}'.format(tender.id),
                    extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_patch'}))
        return {'data': tender.serialize(tender.status)}
