# -*- coding: utf-8 -*-
import os
import decimal
import simplejson
import tempfile
import couchdb.json

from copy import deepcopy
from binascii import hexlify, unhexlify
from collections import defaultdict
from datetime import datetime
from functools import partial
from hashlib import sha512
from json import dumps, loads
from pyramid.compat import text_
from pyramid.threadlocal import get_current_registry
from uuid import uuid4
from yaml import safe_load

from cornice.resource import resource
from cornice.util import json_error
from couchdb import util
from couchdb_schematics.document import SchematicsDocument
from Crypto.Cipher import AES
from jsonpatch import make_patch, apply_patch as _apply_patch
from jsonpointer import resolve_pointer
from schematics.exceptions import ValidationError
from schematics.types import StringType
from pathlib import Path

from webob.multidict import NestedMultiDict
from openprocurement.api.constants import (
    ADDITIONAL_CLASSIFICATIONS_SCHEMES,
    LOGGER,
    ROUTE_PREFIX,
    TZ,
    VERSION,
)
from openprocurement.api.tests.fixtures.auth import MOCK_AUTH_USERS
from openprocurement.api.events import ErrorDesctiptorEvent
from openprocurement.api.interfaces import (
    IContentConfigurator,
    IAuction,
    IOPContent,
)
from openprocurement.api.traversal import factory
from openprocurement.api.config import AppMetaSchema


def route_prefix(conf_main):
    version = conf_main.api_version or VERSION
    return '/api/{}'.format(version)


def get_file_path(here, src):
    """
    Return correct path to file

    >>> get_file_path('/absolute/path/app/', 'need_file')
    '/absolute/path/app/need_file'


    >>> get_file_path('/absolute/path/app/', '/absolute/path/need_file')
    '/absolute/path/need_file'


    :param here: is path to location where app was initialized
    :param src: is path to file

    :return: correct path to file
    """

    path = Path(src)
    if not path.is_absolute():
        path = path.joinpath(here, path)
    return path.as_posix()


def validate_dkpp(items, *args):
    if items and not any([i.scheme in ADDITIONAL_CLASSIFICATIONS_SCHEMES for i in items]):
        raise ValidationError(
            u"One of additional classifications should be one of [{0}].".format(
                ', '.join(ADDITIONAL_CLASSIFICATIONS_SCHEMES)
            )
        )


def get_now():
    return datetime.now(TZ)


def get_type(obj):
    # This function need to wrap python type function
    # because this function can`t be mocked so it`s make
    # testing more difficult
    return type(obj)


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


def get_schematics_document(model):
    while not isinstance(model, SchematicsDocument):
        model = model.__parent__
    return model


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


def update_file_content_type(request):  # XXX TODO
    pass


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


def apply_data_patch(data, changes):
    patch_changes = []
    prepare_patch(patch_changes, data, changes)
    if not patch_changes:
        return {}
    return _apply_patch(data, patch_changes)


def get_revision_changes(dst, src):
    return make_patch(dst, src).patch


def set_item_transfer_token(item, request, acc):
    passed_transfer_token = request.json_body['data'].get('transfer_token')
    if request.authenticated_userid in ['concierge', 'convoy'] and passed_transfer_token:
        item.transfer_token = passed_transfer_token
    else:
        transfer_token = generate_id()
        item.transfer_token = sha512(transfer_token).hexdigest()
        acc['transfer'] = transfer_token


def set_ownership(item, request):
    if not item.get('owner'):
        item.owner = request.authenticated_userid
    owner_token = generate_id()
    item.owner_token = owner_token  # sha512(owner_token).hexdigest()
    acc = {'token': owner_token}
    if isinstance(getattr(type(item), 'transfer_token', None), StringType):
        set_item_transfer_token(item, request, acc)
    return acc


def request_params(request):
    try:
        params = NestedMultiDict(request.GET, request.POST)
    except UnicodeDecodeError:
        request.errors.add('body', 'data', 'could not decode params')
        request.errors.status = 422
        raise error_handler(request, False)
    except Exception as e:
        request.errors.add('body', str(e.__class__.__name__), str(e))
        request.errors.status = 422
        raise error_handler(request, False)
    return params


opresource = partial(resource, error_handler=error_handler, factory=factory)


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


def fix_url(item, app_url, conf_main):
    if isinstance(item, list):
        [
            fix_url(i, app_url, conf_main)
            for i in item
            if isinstance(i, dict) or isinstance(i, list)
        ]
    elif isinstance(item, dict):
        if item.get('format') and item.get('url') and '?download=' in item['url']:
            path = item["url"] if item["url"].startswith('/') else '/' + '/'.join(item['url'].split('/')[5:])
            item["url"] = app_url + route_prefix(conf_main) + path
            return
        [
            fix_url(item[i], app_url, conf_main)
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


def get_request_from_root(model):
    """Getting parent from model recursively until we reach Root"""
    if hasattr(model, '__parent__') and model.__parent__ is not None:
        return get_request_from_root(model.__parent__)
    else:
        return model.request if hasattr(model, 'request') else None


def get_document_creation_date(document):
    return (document.get('revisions')[0].date if document.get('revisions') else get_now())


def read_yaml(file_path):
    with open(file_path) as _file:
        data = _file.read()
    return safe_load(data)


def connection_mock_config(part, connector=(), base=None):
    """
    Combines two mappings in a given connection

    :param part: the part which must be connected
    :param connector: key or keys that connect two parts
    :param base: the base to which the part was attached

    :type: part: abc.Mapping
    :type: connector: abc.Iterable
    :type: base: abc.Mapping
    """
    part = deepcopy(part)
    base = deepcopy(base)
    crawler = base
    prev = []
    last = len(connector) - 1 if connector else 0

    if not base:
        return part

    if not part:
        return None

    if not connector:
        for key in part.keys():
            base[key] = part[key]

    for i, connect in enumerate(connector):
        head = crawler
        if prev:
            for key in prev:
                crawler = crawler[key]
        if not crawler.get(connect, None) and i < last:
            crawler[connect] = {}
        elif i == last:
            crawler[connect] = part
        crawler = head
        prev.append(connect)
    return base


def get_access_token_from_request(request):
    token = request.params.get('acc_token') or request.headers.get('X-Access-Token')
    if not token:
        if request.method in ['POST', 'PUT', 'PATCH'] and request.content_type == 'application/json':
            try:
                json = request.json_body
            except ValueError:
                json = None
            else:
                token = isinstance(json, dict) and json.get('access', {}).get('token')
    return token


def get_resource_accreditation(request, resource_type, context, accreditation_type):
    try:
        acc = request.registry.accreditation[resource_type][context._internal_type][accreditation_type]
    except KeyError:
        return ''
    return acc


def get_all_users():
    return MOCK_AUTH_USERS


def get_forbidden_users(allowed_levels):
    users = get_all_users()
    allowed = ['0']

    allowed.extend(allowed_levels)
    forbidden_users = []

    for user, info in users.items():
        if any([level not in allowed for level in info['level']]):
            forbidden_users.append(user)

    return forbidden_users


def get_auction(model):
    while not IAuction.providedBy(model):
        model = getattr(model, '__parent__', None)
        if model is None:
            return None
    return model


def log_auction_status_change(request, auction, status):
    """
        Log auction status change

        :param request: the request object, for context unpack
        :param auction: the auction object, in which you want to change the status
        :param status: the status to which you want to switch

        :returns: True
    """

    msg = 'Switched auction {} to {}'.format(auction.id, status)
    context_msg = {'MESSAGE_ID': 'switched_auction_{}'.format(status)}
    LOGGER.info(msg, extra=context_unpack(request, context_msg))
    return True


def read_json(filename, file_dir):
    """Read file & deserialize it as JSON"""
    full_filename = os.path.join(file_dir, filename)
    with open(full_filename, 'r') as f:
        data = f.read()
    return loads(data)


def create_app_meta(filepath):
    """This function returns schematics.models.Model object which contains configuration
    of the application. Configuration file reading will be performed only once.

    Current function must be called only once during app initialization.
    """
    config_data = defaultdict(lambda: None, read_yaml(filepath))
    # set app_meta.here as it's parent directory
    config_data['here'] = os.path.dirname(filepath)
    # load & validate app_meta
    app_meta = AppMetaSchema(config_data)
    app_meta.validate()
    return app_meta


def dump_dict_to_tempfile(dict_to_dump, fmt='json'):
    """Writes dict to a temporary file and returns it's path"""

    if fmt == 'json':
        s = dumps(dict_to_dump)

    tf = tempfile.NamedTemporaryFile('w', delete=False)
    tf.write(s)
    tf.close()

    return tf.name


def get_db():
    """Return db connection within current registry

    Note: this function works only inside some request thread.
    """
    r = get_current_registry()
    return r.db


def copy_model(m):
    """
    Copies schematics model

    copy.deepcopy won't work here, bacause the model object's internals cannot be copied.
    """
    m_cls = m.__class__
    data = m.serialize()
    m_copy = m_cls(data)

    if hasattr(m, '__parent__'):
        m_copy.__parent__ = m.__parent__

    return m_copy
