# -*- coding: utf-8 -*-
import decimal
import simplejson
from base64 import b64encode, b64decode
from binascii import hexlify, unhexlify
from datetime import datetime, timedelta, time
from email.header import decode_header
from functools import partial
from hashlib import sha512
from json import dumps
from logging import getLogger
from re import compile
from time import time as ttime
from string import hexdigits
from urllib import quote, unquote, urlencode
from urlparse import urlparse, urlunsplit, parse_qsl, parse_qs
from uuid import uuid4

import couchdb.json
from cornice.resource import resource, view
from cornice.util import json_error
from couchdb import util
from couchdb_schematics.document import SchematicsDocument
from Crypto.Cipher import AES
from jsonpatch import make_patch, apply_patch as _apply_patch
from jsonpointer import resolve_pointer
from pkg_resources import iter_entry_points
from rfc6266 import build_header
from schematics.exceptions import ValidationError
from schematics.types import StringType
from webob.multidict import NestedMultiDict
from pyramid.compat import text_

from openprocurement.api.constants import (
    ADDITIONAL_CLASSIFICATIONS_SCHEMES, DOCUMENT_BLACKLISTED_FIELDS,
    DOCUMENT_WHITELISTED_FIELDS, ROUTE_PREFIX, TZ, SESSION, LOGGER,
    WORKING_DAYS, VERSION
)
from openprocurement.api.events import ErrorDesctiptorEvent
from openprocurement.api.interfaces import IOPContent
from openprocurement.api.interfaces import IContentConfigurator
from openprocurement.api.traversal import factory

ACCELERATOR_RE = compile(r'.accelerator=(?P<accelerator>\d+)')
json_view = partial(view, renderer='json')


def route_prefix(settings):
    return '/api/{}'.format(settings.get('api_version', VERSION))


def validate_dkpp(items, *args):
    if items and not any([i.scheme in ADDITIONAL_CLASSIFICATIONS_SCHEMES for i in items]):
        raise ValidationError(
            u"One of additional classifications should be one of [{0}].".format(
                ', '.join(ADDITIONAL_CLASSIFICATIONS_SCHEMES)
            )
        )


def get_now():
    return datetime.now(TZ)


def request_get_now(request):
    return get_now()


def set_parent(item, parent):
    if hasattr(item, '__parent__') and item.__parent__ is None:
        item.__parent__ = parent


def get_root(item):
    """ traverse back to root op content object (plan, tender, contract, etc.)
    """
    while not IOPContent.providedBy(item):
        item = item.__parent__
    return item


def generate_id():
    return uuid4().hex


def get_filename(data):
    try:
        pairs = decode_header(data.filename)
    except Exception:
        pairs = None
    if not pairs:
        return data.filename
    header = pairs[0]
    if header[1]:
        return header[0].decode(header[1])
    else:
        return header[0]


def get_schematics_document(model):
    while not isinstance(model, SchematicsDocument):
        model = model.__parent__
    return model


def generate_docservice_url(request, doc_id, temporary=True, prefix=None):
    docservice_key = getattr(request.registry, 'docservice_key', None)
    parsed_url = urlparse(request.registry.docservice_url)
    query = {}
    if temporary:
        expires = int(ttime()) + 300  # EXPIRES
        mess = "{}\0{}".format(doc_id, expires)
        query['Expires'] = expires
    else:
        mess = doc_id
    if prefix:
        mess = '{}/{}'.format(prefix, mess)
        query['Prefix'] = prefix
    query['Signature'] = quote(b64encode(docservice_key.signature(mess.encode("utf-8"))))
    query['KeyID'] = docservice_key.hex_vk()[:8]
    return urlunsplit((parsed_url.scheme, parsed_url.netloc, '/get/{}'.format(doc_id), urlencode(query), ''))


def error_handler(request, request_params=True):
    errors = request.errors
    params = {
        'ERROR_STATUS': errors.status
    }
    if request_params:
        params['ROLE'] = str(request.authenticated_role)
        if request.params:
            params['PARAMS'] = str(dict(request.params))
    if request.matchdict:
        for x, j in request.matchdict.items():
            params[x.upper()] = j
    if 'tender' in request.validated:
        params['TENDER_REV'] = request.validated['tender'].rev
        params['TENDERID'] = request.validated['tender'].tenderID
        params['TENDER_STATUS'] = request.validated['tender'].status
    if 'auction' in request.validated:
        params['AUCTION_REV'] = request.validated['auction'].rev
        params['AUCTIONID'] = request.validated['auction'].auctionID
        params['AUCTION_STATUS'] = request.validated['auction'].status
    request.registry.notify(ErrorDesctiptorEvent(request, params))
    LOGGER.info('Error on processing request "{}"'.format(dumps(errors, indent=4)),
                extra=context_unpack(request, {'MESSAGE_ID': 'error_handler'}, params))
    return json_error(request)


def raise_operation_error(request, error_handler, message):
    """
    This function mostly used in views validators to add access errors and
    raise exceptions if requested operation is forbidden.
    """
    request.errors.add('body', 'data', message)
    request.errors.status = 403
    raise error_handler(request)


def upload_file(
    request, blacklisted_fields=DOCUMENT_BLACKLISTED_FIELDS, whitelisted_fields=DOCUMENT_WHITELISTED_FIELDS
):
    first_document = request.validated['documents'][-1] if 'documents' in request.validated and \
            request.validated['documents'] else None
    if 'data' in request.validated and request.validated['data']:
        document = request.validated['document']
        check_document(request, document, 'body')

        if first_document:
            for attr_name in type(first_document)._fields:
                if attr_name in whitelisted_fields:
                    setattr(document, attr_name, getattr(first_document, attr_name))
                elif attr_name not in blacklisted_fields and attr_name not in request.validated['json_data']:
                    setattr(document, attr_name, getattr(first_document, attr_name))

        document_route = request.matched_route.name.replace("collection_", "")
        document = update_document_url(request, document, document_route, {})
        return document
    if request.content_type == 'multipart/form-data':
        data = request.validated['file']
        filename = get_filename(data)
        content_type = data.type
        in_file = data.file
    else:
        filename = first_document.title
        content_type = request.content_type
        in_file = request.body_file

    if hasattr(request.context, "documents"):
        # upload new document
        model = type(request.context).documents.model_class
    else:
        # update document
        model = type(request.context)
    document = model({'title': filename, 'format': content_type})
    document.__parent__ = request.context
    if 'document_id' in request.validated:
        document.id = request.validated['document_id']
    if first_document:
        for attr_name in type(first_document)._fields:
            if attr_name not in blacklisted_fields:
                setattr(document, attr_name, getattr(first_document, attr_name))
    if request.registry.docservice_url:
        parsed_url = urlparse(request.registry.docservice_url)
        url = request.registry.docservice_upload_url or urlunsplit((
            parsed_url.scheme, parsed_url.netloc, '/upload', '', ''
        ))
        files = {'file': (filename, in_file, content_type)}
        doc_url = None
        index = 10
        while index:
            try:
                r = SESSION.post(
                    url,
                    files=files,
                    headers={'X-Client-Request-ID': request.environ.get('REQUEST_ID', '')},
                    auth=(request.registry.docservice_username, request.registry.docservice_password)
                )
                json_data = r.json()
            except Exception, e:
                LOGGER.warning(
                    "Raised exception '{}' on uploading document to document service': {}.".format(type(e), e),
                    extra=context_unpack(
                        request,
                        {'MESSAGE_ID': 'document_service_exception'},
                        {'file_size': in_file.tell()}
                    )
                )
            else:
                if r.status_code == 200 and json_data.get('data', {}).get('url'):
                    doc_url = json_data['data']['url']
                    doc_hash = json_data['data']['hash']
                    break
                else:
                    LOGGER.warning(
                        "Error {} on uploading document to document service '{}': {}".format(
                            r.status_code, url, r.text
                        ),
                        extra=context_unpack(
                            request,
                            {'MESSAGE_ID': 'document_service_error'},
                            {'ERROR_STATUS': r.status_code, 'file_size': in_file.tell()}
                        )
                    )
            in_file.seek(0)
            index -= 1
        else:
            request.errors.add('body', 'data', "Can't upload document to document service.")
            request.errors.status = 422
            raise error_handler(request)
        document.hash = doc_hash
        key = urlparse(doc_url).path.split('/')[-1]
    else:
        key = generate_id()
        filename = "{}_{}".format(document.id, key)
        request.validated['db_doc']['_attachments'][filename] = {
            "content_type": document.format,
            "data": b64encode(in_file.read())
        }
    document_route = request.matched_route.name.replace("collection_", "")
    document_path = request.current_route_path(
        _route_name=document_route,
        document_id=document.id,
        _query={'download': key}
    )
    document.url = '/' + '/'.join(document_path.split('/')[3:])
    update_logging_context(request, {'file_size': in_file.tell()})
    return document


def update_file_content_type(request):  # XXX TODO
    pass


def get_file(request):
    db_doc_id = request.validated['db_doc'].id
    document = request.validated['document']
    key = request.params.get('download')
    if not any([key in i.url for i in request.validated['documents']]):
        request.errors.add('url', 'download', 'Not Found')
        request.errors.status = 404
        return
    filename = "{}_{}".format(document.id, key)
    if request.registry.docservice_url and filename not in request.validated['db_doc']['_attachments']:
        document = [i for i in request.validated['documents'] if key in i.url][-1]
        if 'Signature=' in document.url and 'KeyID' in document.url:
            url = document.url
        else:
            if 'download=' not in document.url:
                key = urlparse(document.url).path.replace('/get/', '')
            if not document.hash:
                url = generate_docservice_url(request, key, prefix='{}/{}'.format(db_doc_id, document.id))
            else:
                url = generate_docservice_url(request, key)
        request.response.content_type = document.format.encode('utf-8')
        request.response.content_disposition = build_header(
            document.title,
            filename_compat=quote(document.title.encode('utf-8'))
        )
        request.response.status = '302 Moved Temporarily'
        request.response.location = url
        return url
    else:
        data = request.registry.db.get_attachment(db_doc_id, filename)
        if data:
            request.response.content_type = document.format.encode('utf-8')
            request.response.content_disposition = build_header(
                document.title,
                filename_compat=quote(document.title.encode('utf-8'))
            )
            request.response.body_file = data
            return request.response
        request.errors.add('url', 'download', 'Not Found')
        request.errors.status = 404


def prepare_patch(changes, orig, patch, basepath=''):
    if isinstance(patch, dict):
        for i in patch:
            if i in orig:
                prepare_patch(changes, orig[i], patch[i], '{}/{}'.format(basepath, i))
            else:
                changes.append({'op': 'add', 'path': '{}/{}'.format(basepath, i), 'value': patch[i]})
    elif isinstance(patch, list):
        if len(patch) < len(orig):
            for i in reversed(range(len(patch), len(orig))):
                changes.append({'op': 'remove', 'path': '{}/{}'.format(basepath, i)})
        for i, j in enumerate(patch):
            if len(orig) > i:
                prepare_patch(changes, orig[i], patch[i], '{}/{}'.format(basepath, i))
            else:
                changes.append({'op': 'add', 'path': '{}/{}'.format(basepath, i), 'value': j})
    else:
        for x in make_patch(orig, patch).patch:
            x['path'] = '{}{}'.format(basepath, x['path'])
            changes.append(x)


def apply_data_patch(item, changes):
    patch_changes = []
    prepare_patch(patch_changes, item, changes)
    if not patch_changes:
        return {}
    return _apply_patch(item, patch_changes)


def get_revision_changes(dst, src):
    return make_patch(dst, src).patch


def set_ownership(item, request):
    if not item.get('owner'):
        item.owner = request.authenticated_userid
    owner_token = generate_id()
    item.owner_token = sha512(owner_token).hexdigest()
    acc = {'token': owner_token}
    if isinstance(getattr(type(item), 'transfer_token', None), StringType):
        transfer_token = generate_id()
        item.transfer_token = sha512(transfer_token).hexdigest()
        acc['transfer'] = transfer_token
    return acc


def check_document(request, document, document_container):
    url = document.url
    parsed_url = urlparse(url)
    parsed_query = dict(parse_qsl(parsed_url.query))
    if not url.startswith(request.registry.docservice_url) or \
            len(parsed_url.path.split('/')) != 3 or \
            set(['Signature', 'KeyID']) != set(parsed_query):
        request.errors.add(document_container, 'url', "Can add document only from document service.")
        request.errors.status = 403
        raise error_handler(request)
    if not document.hash:
        request.errors.add(document_container, 'hash', "This field is required.")
        request.errors.status = 422
        raise error_handler(request)
    keyid = parsed_query['KeyID']
    if keyid not in request.registry.keyring:
        request.errors.add(document_container, 'url', "Document url expired.")
        request.errors.status = 422
        raise error_handler(request)
    dockey = request.registry.keyring[keyid]
    signature = parsed_query['Signature']
    key = urlparse(url).path.split('/')[-1]
    try:
        signature = b64decode(unquote(signature))
    except TypeError:
        request.errors.add(document_container, 'url', "Document url signature invalid.")
        request.errors.status = 422
        raise error_handler(request)
    mess = "{}\0{}".format(key, document.hash.split(':', 1)[-1])
    try:
        if mess != dockey.verify(signature + mess.encode("utf-8")):
            raise ValueError
    except ValueError:
        request.errors.add(document_container, 'url', "Document url invalid.")
        request.errors.status = 422
        raise error_handler(request)


def update_document_url(request, document, document_route, route_kwargs):
    key = urlparse(document.url).path.split('/')[-1]
    route_kwargs.update({'_route_name': document_route,
                         'document_id': document.id,
                         '_query': {'download': key}})
    document_path = request.current_route_path(**route_kwargs)
    document.url = '/' + '/'.join(document_path.split('/')[3:])
    return document


def check_document_batch(request, document, document_container, route_kwargs):
    check_document(request, document, document_container)

    document_route = request.matched_route.name.replace("collection_", "")
    # Following piece of code was written by leits, so no one knows how it works
    # and why =)
    # To redefine document_route to get appropriate real document route when bid
    # is created with documents? I hope so :)
    if "Documents" not in document_route:
        specified_document_route_end = (
            document_container.lower().rsplit('documents')[0] + ' documents'
        ).lstrip().title()
        document_route = ' '.join([document_route[:-1], specified_document_route_end])

    return update_document_url(request, document, document_route, route_kwargs)


def request_params(request):
    try:
        params = NestedMultiDict(request.GET, request.POST)
    except UnicodeDecodeError:
        request.errors.add('body', 'data', 'could not decode params')
        request.errors.status = 422
        raise error_handler(request, False)
    except Exception, e:
        request.errors.add('body', str(e.__class__.__name__), str(e))
        request.errors.status = 422
        raise error_handler(request, False)
    return params


opresource = partial(resource, error_handler=error_handler, factory=factory)


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
        view_map = self.FEED.get(feed, self.VIEW_MAP)
        changes = view_map is self.CHANGES_VIEW_MAP
        if feed and feed in self.FEED:
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
                    self.request.errors.add('querystring', 'offset', 'Offset expired/invalid')
                    self.request.errors.status = 404
                    raise error_handler(self.request)
            if not offset:
                view_offset = 'now' if descending else 0
        else:
            if offset:
                view_offset = offset
            else:
                view_offset = '9' if descending else ''
        list_view = view_map.get(mode, view_map[u''])
        if self.update_after:
            view = partial(
                list_view, self.db, limit=view_limit, startkey=view_offset, descending=descending, stale='update_after'
            )
        else:
            view = partial(list_view, self.db, limit=view_limit, startkey=view_offset, descending=descending)
        if fields:
            if not changes and set(fields).issubset(set(self.FIELDS)):
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
            elif changes and set(fields).issubset(set(self.FIELDS)):
                results = [
                    (dict([(i, j) for i, j in x.value.items() + [('id', x.id)] if i in view_fields]), x.key)
                    for x in view()
                ]
            elif fields:
                self.LOGGER.info(
                    'Used custom fields for {} list: {}'.format(
                        self.object_name_for_listing,
                        ','.join(sorted(fields))
                    ),
                    extra=context_unpack(self.request, {'MESSAGE_ID': self.log_message_id})
                    )

                results = [
                    (self.serialize_func(self.request, i[u'doc'], view_fields), i.key)
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
                params['offset'] = encrypt(self.server.uuid, self.db.name, params['offset'])
                pparams['offset'] = encrypt(self.server.uuid, self.db.name, pparams['offset'])
        else:
            params['offset'] = offset
            pparams['offset'] = offset
        data = {
            'data': results,
            'next_page': {
                "offset": params['offset'],
                "path": self.request.route_path(self.object_name_for_listing, _query=params),
                "uri": self.request.route_url(self.object_name_for_listing, _query=params)
            }
        }
        if descending or offset:
            data['prev_page'] = {
                "offset": pparams['offset'],
                "path": self.request.route_path(self.object_name_for_listing, _query=pparams),
                "uri": self.request.route_url(self.object_name_for_listing, _query=pparams)
            }
        return data


def forbidden(request):
    request.errors.add('url', 'permission', 'Forbidden')
    request.errors.status = 403
    return error_handler(request)


def update_logging_context(request, params):
    if not request.__dict__.get('logging_context'):
        request.logging_context = {}

    for x, j in params.items():
        request.logging_context[x.upper()] = j


def context_unpack(request, msg, params=None):
    if params:
        update_logging_context(request, params)
    logging_context = request.logging_context
    journal_context = msg
    for key, value in logging_context.items():
        journal_context["JOURNAL_" + key] = value
    return journal_context


def get_content_configurator(request):
    content_type = request.path[len(ROUTE_PREFIX)+1:].split('/')[0][:-1]
    if hasattr(request, content_type):  # content is constructed
        context = getattr(request, content_type)
        return request.registry.queryMultiAdapter((context, request),
                                                  IContentConfigurator)


def fix_url(item, app_url, settings=None):
    if not settings:
        settings = {}
    if isinstance(item, list):
        [
            fix_url(i, app_url, settings)
            for i in item
            if isinstance(i, dict) or isinstance(i, list)
        ]
    elif isinstance(item, dict):
        if "format" in item and "url" in item and '?download=' in item['url']:
            path = item["url"] if item["url"].startswith('/') else '/' + '/'.join(item['url'].split('/')[5:])
            item["url"] = app_url + route_prefix(settings) + path
            return
        [
            fix_url(item[i], app_url, settings)
            for i in item
            if isinstance(item[i], dict) or isinstance(item[i], list)
        ]


def encrypt(uuid, name, key):
    iv = "{:^{}.{}}".format(name, AES.block_size, AES.block_size)
    text = "{:^{}}".format(key, AES.block_size)
    return hexlify(AES.new(uuid, AES.MODE_CBC, iv).encrypt(text))


def decrypt(uuid, name, key):
    iv = "{:^{}.{}}".format(name, AES.block_size, AES.block_size)
    try:
        text = AES.new(uuid, AES.MODE_CBC, iv).decrypt(unhexlify(key)).strip()
    except Exception:
        text = ''
    return text


def set_modetest_titles(item):
    if not item.title or u'[ТЕСТУВАННЯ]' not in item.title:
        item.title = u'[ТЕСТУВАННЯ] {}'.format(item.title or u'')
    if not item.title_en or u'[TESTING]' not in item.title_en:
        item.title_en = u'[TESTING] {}'.format(item.title_en or u'')
    if not item.title_ru or u'[ТЕСТИРОВАНИЕ]' not in item.title_ru:
        item.title_ru = u'[ТЕСТИРОВАНИЕ] {}'.format(item.title_ru or u'')


def json_body(self):
    return simplejson.loads(text_(self.body, self.charset), parse_float=decimal.Decimal)


def couchdb_json_decode():
    def my_encode(obj, dumps=simplejson.dumps):
        return dumps(obj, allow_nan=False, ensure_ascii=False)

    def my_decode(string_):
        if isinstance(string_, util.btype):
            string_ = string_.decode("utf-8")
        return simplejson.loads(string_, parse_float=decimal.Decimal)

    couchdb.json.use(decode=my_decode, encode=my_encode)


def prepare_revision(item, patch, author):
    now = get_now()
    status_changes = [
        p
        for p in patch
        if not p['path'].startswith('/bids/') and p['path'].endswith("/status") and p['op'] == "replace"
    ]
    for change in status_changes:
        obj = resolve_pointer(item, change['path'].replace('/status', ''))
        if obj and hasattr(obj, "date"):
            date_path = change['path'].replace('/status', '/date')
            if obj.date and not any([p for p in patch if date_path == p['path']]):
                patch.append({"op": "replace",
                              "path": date_path,
                              "value": obj.date.isoformat()})
            elif not obj.date:
                patch.append({"op": "remove", "path": date_path})
            obj.date = now
    return {
        'author': author,
        'changes': patch,
        'rev': item.rev
    }


def load_plugins(config, group, **kwargs):
    plugins = kwargs.get('plugins')
    for entry_point in iter_entry_points(group, kwargs.get('name')):
        if not plugins or entry_point.name in plugins:
            plugin = entry_point.load()
            plugin(config)


def serialize_document_url(document):
    url = document.url
    if not url or '?download=' not in url:
        return url
    doc_id = parse_qs(urlparse(url).query)['download'][-1]
    root = document.__parent__
    parents = []
    while root.__parent__ is not None:
        parents[0:0] = [root]
        root = root.__parent__
    request = root.request
    if not request.registry.docservice_url:
        return url
    if 'status' in parents[0] and parents[0].status in type(parents[0])._options.roles:
        role = parents[0].status
        for index, obj in enumerate(parents):
            if obj.id != url.split('/')[(index - len(parents)) * 2 - 1]:
                break
            field = url.split('/')[(index - len(parents)) * 2]
            if "_" in field:
                field = field[0] + field.title().replace("_", "")[1:]
            roles = type(obj)._options.roles
            if roles[role if role in roles else 'default'](field, []):
                return url
    if not document.hash:
        path = [
            i for i in urlparse(url).path.split('/') if
            len(i) == 32 and
            not set(i).difference(hexdigits)  # noqa: F821
        ]
        return generate_docservice_url(request, doc_id, False, '{}/{}'.format(path[0], path[-1]))
    return generate_docservice_url(request, doc_id, False)


def get_request_from_root(model):
    """Getting parent from model recursively until we reach Root"""
    if hasattr(model, '__parent__') and model.__parent__ is not None:
        return get_request_from_root(model.__parent__)
    else:
        return model.request if hasattr(model, 'request') else None


def is_holiday(date):
    """Check if date is holiday
    Calculation is based on WORKING_DAYS dictionary, constructed in following format:
        <date_string>: <bool>

    where:
        - `date_string` - string representing the date in ISO 8601 format, `YYYY-MM-DD`.
        - `bool` - boolean representing work status of the day:
            - `True` **IF IT'S A HOLIDAY** but the day is not at weekend
            - `False` if day is at weekend, but it's a working day
    :param date: date to check
    :type date: datetime.timedelta
    :return: True if date is work day, False if it isn't
    :rtype: bool
    """

    date_iso = date.date().isoformat()
    return (
        date.weekday() in [5, 6] and  # date's weekday is Saturday or Sunday
        WORKING_DAYS.get(date_iso, True) or  # but it's not a holiday
        WORKING_DAYS.get(date_iso, False)  # or date in't at weekend, but it's holiday
    )


def accelerated_calculate_business_date(date, period, context):
    if context and 'procurementMethodDetails' in context and context['procurementMethodDetails']:
        re_obj = ACCELERATOR_RE.search(context['procurementMethodDetails'])
        if re_obj and 'accelerator' in re_obj.groupdict():
            return date + (period / int(re_obj.groupdict()['accelerator']))


def calculate_business_date(date_obj, timedelta_obj, context=None, working_days=False):
    """This method calculates end of business period from given start and timedelta
    The calculation of end of business period is complex, so this method is used project-wide.
    Also this method provides support of accelerated calculation, useful while testing.
    :param date_obj: the start of period
    :param timedelta_obj: duration of the period
    :param context: object, that holds data related to particular business process,
        usually it's Auction model's instance. Must be present to use acceleration
        mode.
    :param working_days: make calculations taking into account working days
    :type date_obj: datetime.datetime
    :type timedelta_obj: datetime.timedelta
    :type context: openprocurement.api.models.Tender
    :type working_days: bool
    :return: the end of period
    :rtype: datetime.datetime
    """

    accelerated_calculation = accelerated_calculate_business_date(date_obj, timedelta_obj, context)
    if accelerated_calculation:
        return accelerated_calculation

    if working_days:
        if timedelta_obj > timedelta():
            if is_holiday(date_obj):
                date_obj = datetime.combine(date_obj.date(), time(0, tzinfo=date_obj.tzinfo)) + timedelta(1)
                while is_holiday(date_obj):
                    date_obj += timedelta(1)
        else:
            if is_holiday(date_obj):
                date_obj = datetime.combine(date_obj.date(), time(0, tzinfo=date_obj.tzinfo))
                while is_holiday(date_obj):
                    date_obj -= timedelta(1)
                date_obj += timedelta(1)
        for _ in xrange(abs(timedelta_obj.days)):
            date_obj += timedelta(1) if timedelta_obj > timedelta() else -timedelta(1)
            while is_holiday(date_obj):
                date_obj += timedelta(1) if timedelta_obj > timedelta() else -timedelta(1)
        return date_obj
    return date_obj + timedelta_obj


def get_document_creation_date(document):
    return (
        document.get('revisions')[0].date
        if document.get('revisions')
        else get_now()
    )
