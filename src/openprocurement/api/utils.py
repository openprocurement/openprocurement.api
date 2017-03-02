# -*- coding: utf-8 -*-
import argparse
import os
from logging import getLogger
from datetime import datetime, timedelta
from base64 import b64encode, b64decode
from cornice.resource import resource, view
from couchdb import Server as CouchdbServer, Session
from couchdb.http import Unauthorized, extract_credentials
from email.header import decode_header
from functools import partial
from jsonpatch import make_patch, apply_patch as _apply_patch
from openprocurement.api.traversal import factory
from rfc6266 import build_header
from pbkdf2 import PBKDF2
from time import time as ttime
from urllib import quote, unquote, urlencode
from urlparse import urlparse, urlunsplit, parse_qsl
from uuid import uuid4
from webob.multidict import NestedMultiDict
from binascii import hexlify, unhexlify
from Crypto.Cipher import AES
from cornice.util import json_error
from json import dumps
from ConfigParser import ConfigParser

from schematics.exceptions import ValidationError
from openprocurement.api.design import sync_design
from openprocurement.api.constants import LOGGER
from openprocurement.api.constants import (
    ADDITIONAL_CLASSIFICATIONS_SCHEMES, ADDITIONAL_CLASSIFICATIONS_SCHEMES_2017,
    DOCUMENT_BLACKLISTED_FIELDS, DOCUMENT_WHITELISTED_FIELDS,
    ROUTE_PREFIX, VERSION, TZ, WORKING_DAYS, SESSION
)

json_view = partial(view, renderer='json')

SECURITY = {u'admins': {u'names': [], u'roles': ['_admin']}, u'members': {u'names': [], u'roles': ['_admin']}}
VALIDATE_DOC_ID = '_design/_auth'
VALIDATE_DOC_UPDATE = """function(newDoc, oldDoc, userCtx){
    if(newDoc._deleted && newDoc.tenderID) {
        throw({forbidden: 'Not authorized to delete this document'});
    }
    if(userCtx.roles.indexOf('_admin') !== -1 && newDoc._id.indexOf('_design/') === 0) {
        return;
    }
    if(userCtx.name === '%s') {
        return;
    } else {
        throw({forbidden: 'Only authorized user may edit the database'});
    }
}"""

def validate_dkpp(items, *args):
    if items and not any([i.scheme in ADDITIONAL_CLASSIFICATIONS_SCHEMES for i in items]):
        raise ValidationError(u"One of additional classifications should be one of [{0}].".format(', '.join(ADDITIONAL_CLASSIFICATIONS_SCHEMES)))


def get_now():
    return datetime.now(TZ)



def set_parent(item, parent):
    if hasattr(item, '__parent__') and item.__parent__ is None:
        item.__parent__ = parent

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

def error_handler(errors, request_params=True, extra_params=None):
    params = {
        'ERROR_STATUS': errors.status
    }
    if request_params:
        params['ROLE'] = str(errors.request.authenticated_role)
        if errors.request.params:
            params['PARAMS'] = str(dict(errors.request.params))
    if errors.request.matchdict:
        for x, j in errors.request.matchdict.items():
            params[x.upper()] = j
    if extra_params and isinstance(extra_params, dict):
        params.update(extra_params)
    LOGGER.info('Error on processing request "{}"'.format(dumps(errors, indent=4)),
                extra=context_unpack(errors.request, {'MESSAGE_ID': 'error_handler'}, params))
    return json_error(errors)


def upload_file(request, blacklisted_fields=DOCUMENT_BLACKLISTED_FIELDS, whitelisted_fields=DOCUMENT_WHITELISTED_FIELDS):
    first_document = request.validated['documents'][-1] if 'documents' in request.validated and request.validated['documents'] else None
    if 'data' in request.validated and request.validated['data']:
        document = request.validated['document']
        url = document.url
        parsed_url = urlparse(url)
        parsed_query = dict(parse_qsl(parsed_url.query))
        if not url.startswith(request.registry.docservice_url) or \
                len(parsed_url.path.split('/')) != 3 or \
                set(['Signature', 'KeyID']) != set(parsed_query):
            request.errors.add('body', 'url', "Can add document only from document service.")
            request.errors.status = 403
            raise error_handler(request.errors)
        if not document.hash:
            request.errors.add('body', 'hash', "This field is required.")
            request.errors.status = 422
            raise error_handler(request.errors)
        keyid = parsed_query['KeyID']
        if keyid not in request.registry.keyring:
            request.errors.add('body', 'url', "Document url expired.")
            request.errors.status = 422
            raise error_handler(request.errors)
        dockey = request.registry.keyring[keyid]
        signature = parsed_query['Signature']
        key = urlparse(url).path.split('/')[-1]
        try:
            signature = b64decode(unquote(signature))
        except TypeError:
            request.errors.add('body', 'url', "Document url signature invalid.")
            request.errors.status = 422
            raise error_handler(request.errors)
        mess = "{}\0{}".format(key, document.hash.split(':', 1)[-1])
        try:
            if mess != dockey.verify(signature + mess.encode("utf-8")):
                raise ValueError
        except ValueError:
            request.errors.add('body', 'url', "Document url invalid.")
            request.errors.status = 422
            raise error_handler(request.errors)
        if first_document:
            for attr_name in type(first_document)._fields:
                if attr_name in whitelisted_fields:
                    setattr(document, attr_name, getattr(first_document, attr_name))
                elif attr_name not in blacklisted_fields and attr_name not in request.validated['json_data']:
                    setattr(document, attr_name, getattr(first_document, attr_name))
        document_route = request.matched_route.name.replace("collection_", "")
        document_path = request.current_route_path(_route_name=document_route, document_id=document.id, _query={'download': key})
        document.url = '/' + '/'.join(document_path.split('/')[3:])
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
        url = request.registry.docservice_upload_url or urlunsplit((parsed_url.scheme, parsed_url.netloc, '/upload', '', ''))
        files = {'file': (filename, in_file, content_type)}
        doc_url = None
        index = 10
        while index:
            try:
                r = SESSION.post(url,
                                files=files,
                                headers={'X-Client-Request-ID': request.environ.get('REQUEST_ID', '')},
                                auth=(request.registry.docservice_username, request.registry.docservice_password)
                                )
                json_data = r.json()
            except Exception, e:
                LOGGER.warning("Raised exception '{}' on uploading document to document service': {}.".format(type(e), e),
                               extra=context_unpack(request, {'MESSAGE_ID': 'document_service_exception'}, {'file_size': in_file.tell()}))
            else:
                if r.status_code == 200 and json_data.get('data', {}).get('url'):
                    doc_url = json_data['data']['url']
                    doc_hash = json_data['data']['hash']
                    break
                else:
                    LOGGER.warning("Error {} on uploading document to document service '{}': {}".format(r.status_code, url, r.text),
                                   extra=context_unpack(request, {'MESSAGE_ID': 'document_service_error'}, {'ERROR_STATUS': r.status_code, 'file_size': in_file.tell()}))
            in_file.seek(0)
            index -= 1
        else:
            request.errors.add('body', 'data', "Can't upload document to document service.")
            request.errors.status = 422
            raise error_handler(request.errors)
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
    document_path = request.current_route_path(_route_name=document_route, document_id=document.id, _query={'download': key})
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
        request.response.content_disposition = build_header(document.title, filename_compat=quote(document.title.encode('utf-8')))
        request.response.status = '302 Moved Temporarily'
        request.response.location = url
        return url
    else:
        data = request.registry.db.get_attachment(db_doc_id, filename)
        if data:
            request.response.content_type = document.format.encode('utf-8')
            request.response.content_disposition = build_header(document.title, filename_compat=quote(document.title.encode('utf-8')))
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
    item.owner_token = generate_id()


def request_params(request):
    try:
        params = NestedMultiDict(request.GET, request.POST)
    except UnicodeDecodeError:
        request.errors.add('body', 'data', 'could not decode params')
        request.errors.status = 422
        raise error_handler(request.errors, False)
    except Exception, e:
        request.errors.add('body', str(e.__class__.__name__), str(e))
        request.errors.status = 422
        raise error_handler(request.errors, False)
    return params


opresource = partial(resource, error_handler=error_handler, factory=factory)

class APIResource(object):

    def __init__(self, request, context):
        self.context = context
        self.request = request
        self.db = request.registry.db
        self.server_id = request.registry.server_id
        self.LOGGER = getLogger(type(self).__module__)


def forbidden(request):
    request.errors.add('url', 'permission', 'Forbidden')
    request.errors.status = 403
    return error_handler(request.errors)


def add_logging_context(event):
    request = event.request
    params = {
        'API_VERSION': VERSION,
        'TAGS': 'python,api',
        'USER': str(request.authenticated_userid or ''),
        #'ROLE': str(request.authenticated_role),
        'CURRENT_URL': request.url,
        'CURRENT_PATH': request.path_info,
        'REMOTE_ADDR': request.remote_addr or '',
        'USER_AGENT': request.user_agent or '',
        'REQUEST_METHOD': request.method,
        'TIMESTAMP': get_now().isoformat(),
        'REQUEST_ID': request.environ.get('REQUEST_ID', ''),
        'CLIENT_REQUEST_ID': request.headers.get('X-Client-Request-ID', ''),
    }

    request.logging_context = params


def set_logging_context(event):
    request = event.request

    params = {}
    params['ROLE'] = str(request.authenticated_role)
    if request.params:
        params['PARAMS'] = str(dict(request.params))
    if request.matchdict:
        for x, j in request.matchdict.items():
            params[x.upper()] = j
    update_logging_context(request, params)


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


def set_renderer(event):
    request = event.request
    try:
        json = request.json_body
    except ValueError:
        json = {}
    pretty = isinstance(json, dict) and json.get('options', {}).get('pretty') or request.params.get('opt_pretty')
    jsonp = request.params.get('opt_jsonp')
    if jsonp and pretty:
        request.override_renderer = 'prettyjsonp'
        return True
    if jsonp:
        request.override_renderer = 'jsonp'
        return True
    if pretty:
        request.override_renderer = 'prettyjson'
        return True


def fix_url(item, app_url):
    if isinstance(item, list):
        [
            fix_url(i, app_url)
            for i in item
            if isinstance(i, dict) or isinstance(i, list)
        ]
    elif isinstance(item, dict):
        if "format" in item and "url" in item and '?download=' in item['url']:
            path = item["url"] if item["url"].startswith('/') else '/' + '/'.join(item['url'].split('/')[5:])
            item["url"] = app_url + ROUTE_PREFIX + path
            return
        [
            fix_url(item[i], app_url)
            for i in item
            if isinstance(item[i], dict) or isinstance(item[i], list)
        ]


def beforerender(event):
    if event.rendering_val and isinstance(event.rendering_val, dict) and 'data' in event.rendering_val:
        fix_url(event.rendering_val['data'], event['request'].application_url)


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


def set_modetest_titles(item):
    if not item.title or u'[ТЕСТУВАННЯ]' not in item.title:
        item.title = u'[ТЕСТУВАННЯ] {}'.format(item.title or u'')
    if not item.title_en or u'[TESTING]' not in item.title_en:
        item.title_en = u'[TESTING] {}'.format(item.title_en or u'')
    if not item.title_ru or u'[ТЕСТИРОВАНИЕ]' not in item.title_ru:
        item.title_ru = u'[ТЕСТИРОВАНИЕ] {}'.format(item.title_ru or u'')


class Server(CouchdbServer):
    _uuid = None

    @property
    def uuid(self):
        """The uuid of the server.

        :rtype: basestring
        """
        if self._uuid is None:
            _, _, data = self.resource.get_json()
            self._uuid = data['uuid']
        return self._uuid


def set_api_security(settings):
    # CouchDB connection
    db_name = os.environ.get('DB_NAME', settings['couchdb.db_name'])
    server = Server(settings.get('couchdb.url'),
                    session=Session(retry_delays=range(10)))
    if 'couchdb.admin_url' not in settings and server.resource.credentials:
        try:
            server.version()
        except Unauthorized:
            server = Server(extract_credentials(
                settings.get('couchdb.url'))[0])

    if 'couchdb.admin_url' in settings and server.resource.credentials:
        aserver = Server(settings.get('couchdb.admin_url'),
                         session=Session(retry_delays=range(10)))
        users_db = aserver['_users']
        if SECURITY != users_db.security:
            LOGGER.info("Updating users db security",
                        extra={'MESSAGE_ID': 'update_users_security'})
            users_db.security = SECURITY
        username, password = server.resource.credentials
        user_doc = users_db.get(
            'org.couchdb.user:{}'.format(username),
            {'_id': 'org.couchdb.user:{}'.format(username)})
        if (not user_doc.get('derived_key', '') or
                PBKDF2(password, user_doc.get('salt', ''),
                       user_doc.get('iterations', 10)).hexread(
                           int(len(user_doc.get('derived_key', '')) / 2)) !=
                user_doc.get('derived_key', '')):
            user_doc.update({
                "name": username,
                "roles": [],
                "type": "user",
                "password": password
            })
            LOGGER.info("Updating api db main user",
                        extra={'MESSAGE_ID': 'update_api_main_user'})
            users_db.save(user_doc)
        security_users = [username, ]
        if ('couchdb.reader_username' in settings and
                'couchdb.reader_password' in settings):
            reader_username = settings.get('couchdb.reader_username')
            reader = users_db.get(
                'org.couchdb.user:{}'.format(reader_username),
                {'_id': 'org.couchdb.user:{}'.format(reader_username)})
            if (not reader.get('derived_key', '') or
                    PBKDF2(settings.get('couchdb.reader_password'),
                           reader.get('salt', ''), reader.get(
                               'iterations', 10)).hexread(int(len(reader.get(
                                   'derived_key', '')) / 2)) !=
                    reader.get('derived_key', '')):
                reader.update({
                    "name": reader_username,
                    "roles": ['reader'],
                    "type": "user",
                    "password": settings.get('couchdb.reader_password')
                })
                LOGGER.info("Updating api db reader user",
                            extra={'MESSAGE_ID': 'update_api_reader_user'})
                users_db.save(reader)
            security_users.append(reader_username)
        if db_name not in aserver:
            aserver.create(db_name)
        db = aserver[db_name]
        SECURITY[u'members'][u'names'] = security_users
        if SECURITY != db.security:
            LOGGER.info("Updating api db security",
                        extra={'MESSAGE_ID': 'update_api_security'})
            db.security = SECURITY
        auth_doc = db.get(VALIDATE_DOC_ID, {'_id': VALIDATE_DOC_ID})
        if (auth_doc.get('validate_doc_update') !=
                VALIDATE_DOC_UPDATE % username):
            auth_doc['validate_doc_update'] = VALIDATE_DOC_UPDATE % username
            LOGGER.info("Updating api db validate doc",
                        extra={'MESSAGE_ID': 'update_api_validate_doc'})
            db.save(auth_doc)
        # sync couchdb views
        sync_design(db)
        db = server[db_name]
    else:
        if db_name not in server:
            server.create(db_name)
        db = server[db_name]
        # sync couchdb views
        sync_design(db)
        aserver = None
    return aserver, server, db


def bootstrap_api_security():
    parser = argparse.ArgumentParser(description='---- Edge Bridge ----')
    parser.add_argument('config', type=str, help='Path to configuration file')
    params = parser.parse_args()
    if os.path.isfile(params.config):
        conf = ConfigParser()
        conf.read(params.config)
        settings = {k: v for k, v in conf.items('app:main')}
        set_api_security(settings)
