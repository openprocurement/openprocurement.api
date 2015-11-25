# -*- coding: utf-8 -*-
from logging import getLogger
from binascii import hexlify, unhexlify
from Crypto.Cipher import AES
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
from openprocurement.api.interfaces import ITender, IBaseTender
from openprocurement.api.models import get_tender, isTender
from openprocurement.api.utils import (
    generate_id,
    generate_tender_id,
    save_tender,
    set_ownership,
    tender_serialize,
    apply_patch,
    check_bids,
    check_tender_status,
    opresource,
    json_view,
    context_unpack,
)
from openprocurement.api.validation import (
    validate_patch_tender_data,
    validate_tender_data,
)


LOGGER = getLogger(__name__)
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


def encrypt(uuid, name, key):
    iv = "{:^{}.{}}".format(name, AES.block_size, AES.block_size)
    text = "{:^{}}".format(key, AES.block_size)
    return hexlify(AES.new(uuid, AES.MODE_CBC, iv).encrypt(text))


def decrypt(uuid, name, key):
    iv = "{:^{}.{}}".format(name, AES.block_size, AES.block_size)
    try:
        text = AES.new(uuid, AES.MODE_CBC, iv).decrypt(unhexlify(key)).strip()
    except:
        text = ''
    return text


@opresource(name='TendersRoot',
            path='/tenders',
#            custom_predicates=(isTender,),
            description="Open Contracting compatible data exchange format. See http://ocds.open-contracting.org/standard/r/master/#tender for more info")
class RootResource(object):

    def __init__(self, request):
        self.request = request
        self.server = request.registry.couchdb_server
        self.db = request.registry.db
        self.server_id = request.registry.server_id

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
        limit = int(limit) if limit.isdigit() and int(limit) > 0 else 100
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
        if fields:
            if not changes and set(fields).issubset(set(FIELDS)):
                results = [
                    (dict([(i, j) for i, j in x.value.items() + [('id', x.id), ('dateModified', x.key)] if i in view_fields]), x.key)
                    for x in list_view(self.db, limit=view_limit, startkey=view_offset, descending=descending)
                ]
            elif changes and set(fields).issubset(set(FIELDS)):
                results = [
                    (dict([(i, j) for i, j in x.value.items() + [('id', x.id)] if i in view_fields]), x.key)
                    for x in list_view(self.db, limit=view_limit, startkey=view_offset, descending=descending)
                ]
            elif fields:
                LOGGER.info('Used custom fields for tenders list: {}'.format(','.join(sorted(fields))),
                            extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_list_custom'}))

                results = [
                    (tender_serialize(self.request, i[u'doc'], view_fields), i.key)
                    for i in list_view(self.db, limit=view_limit, startkey=view_offset, descending=descending, include_docs=True)
                ]
        else:
            results = [
                ({'id': i.id, 'dateModified': i.value['dateModified']} if changes else {'id': i.id, 'dateModified': i.key}, i.key)
                for i in list_view(self.db, limit=view_limit, startkey=view_offset, descending=descending)
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
                "path": self.request.route_path('TendersRoot', _query=params),
                "uri": self.request.route_url('TendersRoot', _query=params)
            }
        }
        if descending or offset:
            data['prev_page'] = {
                "offset": pparams['offset'],
                "path": self.request.route_path('TendersRoot', _query=pparams),
                "uri": self.request.route_url('TendersRoot', _query=pparams)
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
        tender_data = self.request.validated['data']
        tender_id = generate_id()

        adapter = self.request.registry.queryAdapter(tender_data, IBaseTender,
                                                     tender_data.get('subtype',
                                                                     'Tender'))
        tender = adapter.tender()
        tender.__parent__ = self.request.context
        tender.id = tender_id
        if not tender.enquiryPeriod.startDate:
            tender.enquiryPeriod.startDate = get_now()
        tender.tenderID = generate_tender_id(tender.enquiryPeriod.startDate, self.db, self.server_id)
        if not tender.tenderPeriod.startDate:
            tender.tenderPeriod.startDate = tender.enquiryPeriod.endDate
        set_ownership(tender, self.request)
        self.request.validated['tender'] = tender
        self.request.validated['tender_src'] = {}
        if save_tender(self.request):
            LOGGER.info('Created tender {} ({})'.format(tender_id, tender.tenderID),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_create'}, {'tender_id': tender_id, 'tenderID': tender.tenderID}))
            self.request.response.status = 201
            self.request.response.headers[
                'Location'] = self.request.route_url('Tender', tender_id=tender_id)  # XXX
            return {
                'data': tender.serialize(tender.status),
                'access': {
                    'token': tender.owner_token
                }
            }


@opresource(name='Tender',
            path='/tenders/{tender_id}',
            custom_predicates=(isTender,),
            description="Open Contracting compatible data exchange format. See http://ocds.open-contracting.org/standard/r/master/#tender for more info")
class TenderResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

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
        tender = self.request.validated['tender']  # XXX self.request._tender ?
        tender_data = tender.serialize('chronograph_view' if self.request.authenticated_role == 'chronograph' else tender.status)
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
        if self.request.authenticated_role == 'chronograph' and tender.status == 'active.tendering' and data.get('status', tender.status) == 'active.auction':
            apply_patch(self.request, save=False, src=self.request.validated['tender_src'])
            check_bids(self.request)
            save_tender(self.request)
        elif self.request.authenticated_role == 'chronograph' and tender.status in ['active.qualification', 'active.awarded'] and data.get('status', tender.status) == tender.status:
            check_tender_status(self.request)
            save_tender(self.request)
        else:
            apply_patch(self.request, src=self.request.validated['tender_src'])
        LOGGER.info('Updated tender {}'.format(tender.id),
                    extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_patch'}))
        return {'data': tender.serialize(tender.status)}
