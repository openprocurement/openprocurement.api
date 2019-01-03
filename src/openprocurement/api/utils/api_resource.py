# -*- coding: utf-8 -*-
from cornice.resource import view
from functools import partial
from logging import getLogger

from openprocurement.api.constants import (
    LOGGER,
)
from openprocurement.api.utils.common import (
    context_unpack,
    decrypt,
    encrypt,
    error_handler,
)


json_view = partial(view, renderer='json')


def get_listing_data(
        view_params, db_params, collections, model_serializer,
        resource_name, update_after):
    """ Util function for retrieving data from couchdb

    :param view_params:
        request: self.request
        log_message_id: self.log_message_id
    :param db_params:
        server: couchdb server (request.registry.couchdb_server)
        db: couchdb database
    :param collections: FIELDS, FEED, VIEW_MAP, CHANGES_VIEW_MAP
    :param model_serializer: callable for serialization of object 'model'
    :param resource_name: name of resource that retrieved
    :return: json object data
    """

    params = {}
    pparams = {}
    fields = view_params['request'].params.get('opt_fields', '')
    if fields:
        params['opt_fields'] = fields
        pparams['opt_fields'] = fields
        fields = fields.split(',')
        view_fields = fields + ['dateModified', 'id']
    limit = view_params['request'].params.get('limit', '')
    if limit:
        params['limit'] = limit
        pparams['limit'] = limit
    limit = int(limit) if limit.isdigit() and (100 if fields else 1000) >= int(limit) > 0 else 100
    descending = bool(view_params['request'].params.get('descending'))
    offset = view_params['request'].params.get('offset', '')
    if descending:
        params['descending'] = 1
    else:
        pparams['descending'] = 1
    feed = view_params['request'].params.get('feed', '')
    view_map = collections['FEED'].get(feed, collections['VIEW_MAP'])
    changes = view_map is collections['CHANGES_VIEW_MAP']
    if feed and feed in collections['FEED']:
        params['feed'] = feed
        pparams['feed'] = feed
    mode = view_params['request'].params.get('mode', '')
    if mode and mode in view_map:
        params['mode'] = mode
        pparams['mode'] = mode
    view_limit = limit + 1 if offset else limit
    if changes:
        if offset:
            view_offset = decrypt(db_params['server'].uuid, db_params['db'].name, offset)
            if view_offset and view_offset.isdigit():
                view_offset = int(view_offset)
            else:
                view_params['request'].errors.add('querystring', 'offset', 'Offset expired/invalid')
                view_params['request'].errors.status = 404
                raise error_handler(view_params['request'])
        if not offset:
            view_offset = 'now' if descending else 0
    else:
        if offset:
            view_offset = offset
        else:
            view_offset = '9' if descending else ''
    list_view = view_map.get(mode, view_map[u''])
    if update_after:
        view = partial(
            list_view,
            db_params['db'],
            limit=view_limit,
            startkey=view_offset,
            descending=descending,
            stale='update_after'
        )
    else:
        view = partial(list_view, db_params['db'], limit=view_limit, startkey=view_offset, descending=descending)
    if fields:
        if not changes and set(fields).issubset(set(collections['FIELDS'])):
            results = [
                (
                    dict([(i, j) for i, j in x.value.items() + [
                        ('id', x.id),
                        ('dateModified', x.key)
                    ] if i in view_fields
                          ]),
                    x.key
                )
                for x in view()
            ]
        elif changes and set(fields).issubset(set(collections['FIELDS'])):
            results = [
                (dict([(i, j) for i, j in x.value.items() + [('id', x.id)] if i in view_fields]), x.key)
                for x in view()
            ]
        elif fields:
            LOGGER.info(
                'Used custom fields for {} list: {}'.format(
                    resource_name,
                    ','.join(sorted(fields))
                ),
                extra=context_unpack(view_params['request'], {'MESSAGE_ID': view_params['log_message_id']})
            )

            results = [
                (model_serializer(view_params['request'], i[u'doc'], view_fields), i.key)
                for i in view(include_docs=True)
            ]
    else:
        results = [
            (
                {'id': i.id, 'dateModified': i.value['dateModified']} if changes else
                {'id': i.id, 'dateModified': i.key}, i.key
            )
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
            params['offset'] = encrypt(db_params['server'].uuid, db_params['db'].name, params['offset'])
            pparams['offset'] = encrypt(db_params['server'].uuid, db_params['db'].name, pparams['offset'])
    else:
        params['offset'] = offset
        pparams['offset'] = offset
    data = {
        'data': results,
        'next_page': {
            "offset": params['offset'],
            "path": view_params['request'].route_path(resource_name, _query=params),
            "uri": view_params['request'].route_url(resource_name, _query=params)
        }
    }
    if descending or offset:
        data['prev_page'] = {
            "offset": pparams['offset'],
            "path": view_params['request'].route_path(resource_name, _query=pparams),
            "uri": view_params['request'].route_url(resource_name, _query=pparams)
        }
    return data


class APIResource(object):

    def __init__(self, request, context):
        self.context = context
        self.request = request
        self.db = request.registry.db
        self.server_id = request.registry.server_id
        self.LOGGER = getLogger(type(self).__module__)


class APIResourceListing(APIResource):

    def __init__(self, request, context):
        super(APIResourceListing, self).__init__(request, context)
        self.server = request.registry.couchdb_server
        self.update_after = request.registry.update_after

    @json_view(permission='view_listing')
    def get(self):
        collections = {
            'FEED': self.FEED,
            'VIEW_MAP': self.VIEW_MAP,
            'CHANGES_VIEW_MAP': self.CHANGES_VIEW_MAP,
            'FIELDS': self.FIELDS
        }
        view_params = {
            'log_message_id': self.log_message_id,
            'request': self.request
        }
        db_params = {
            'server': self.server,
            'db': self.db
        }
        data = get_listing_data(
            view_params,
            db_params,
            collections,
            self.serialize_func,
            self.object_name_for_listing,
            self.update_after,
        )
        return data
