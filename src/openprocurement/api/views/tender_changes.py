# -*- coding: utf-8 -*-
from logging import getLogger
from cornice.resource import resource, view
from binascii import hexlify, unhexlify
from Crypto.Cipher import AES
from openprocurement.api.design import tenders_real_by_dateModified_view
from openprocurement.api.models import Tender
from openprocurement.api.views.tender import VIEW_MAP
from openprocurement.api.utils import (
    tender_serialize,
    error_handler,
)


LOGGER = getLogger(__name__)


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


@resource(name='TenderChanges',
          collection_path='/tenders_changes',
          path='/tenders_changes/{tender_id}',
          description="Open Contracting compatible data exchange format. See http://ocds.open-contracting.org/standard/r/master/#tender for more info",
          error_handler=error_handler)
class TenderResource(object):

    def __init__(self, request):
        self.request = request
        self.server = request.registry.couchdb_server
        self.db = request.registry.db

    @view(renderer='json', permission='view_tender')
    def collection_get(self):
        """Tenders Changes List

        Get Tenders Changes List
        ------------------------

        Example request to get tenders list:

        .. sourcecode:: http

            GET /tenders_changes HTTP/1.1
            Host: example.com
            Accept: application/json

        This is what one should expect in response:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "data": [
                    {
                        "id": "8341b3dd87f243709dc202501fc76f70"
                    }
                ]
            }

        """
        params = {}
        fields = self.request.params.get('opt_fields', '')
        if fields:
            params['opt_fields'] = fields
        limit = self.request.params.get('limit', '')
        if limit:
            params['limit'] = limit
        limit = int(limit) if limit.isdigit() else 100
        descending = self.request.params.get('descending')
        offset = self.request.params.get('offset', '')
        #offset = int(offset) if offset.isdigit() else 0
        if offset:
            offset = decrypt(self.server.uuid, self.db.name, offset)
        if offset.isdigit():
            offset = int(offset)
        else:
            offset = 'now' if descending else 0
        mode = self.request.params.get('mode')
        if mode:
            params['mode'] = mode
        list_view = VIEW_MAP.get(mode, tenders_real_by_dateModified_view)
        list_view_name = '/'.join([list_view.design, list_view.name])
        if fields:
            LOGGER.info('Used custom fields for tenders list: {}'.format(','.join(sorted(fields.split(',')))), extra={'MESSAGE_ID': 'tender_list_custom'})
            fields = fields.split(',') + ['id']
            changes = self.db.changes(since=offset, limit=limit, filter='_view', view=list_view_name, descending=bool(descending), include_docs=True)
            results = [tender_serialize(Tender(i[u'doc']), fields) for i in changes[u'results']]
        else:
            changes = self.db.changes(since=offset, limit=limit, filter='_view', view=list_view_name, descending=bool(descending))
            results = [{'id': i['id']} for i in changes[u'results']]
        #params['offset'] = changes[u'last_seq']
        params['offset'] = encrypt(self.server.uuid, self.db.name, changes[u'last_seq'])
        return {
            'data': results,
            'next_page': {
                "offset": params['offset'],
                "path": self.request.route_path('collection_TenderChanges', _query=params),
                "uri": self.request.route_url('collection_TenderChanges', _query=params)
            }
        }
