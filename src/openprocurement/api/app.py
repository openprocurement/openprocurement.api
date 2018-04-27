# -*- coding: utf-8 -*-
"""Main entry point
"""
# flake8: noqa
if 'test' not in __import__('sys').argv[0]:
    import gevent.monkey
    gevent.monkey.patch_all()

import os
from collections import defaultdict
from copy import deepcopy, copy
from libnacl.public import SecretKey, PublicKey
from libnacl.sign import Signer, Verifier
from logging import getLogger
from pkg_resources import iter_entry_points
from pyramid.authorization import ACLAuthorizationPolicy as AuthorizationPolicy
from pyramid.config import Configurator
from pyramid.renderers import JSON, JSONP
from pyramid.settings import asbool
import simplejson

from openprocurement.api.auth import AuthenticationPolicy, authenticated_role, check_accreditation
from openprocurement.api.database import set_api_security
from openprocurement.api.utils import (
    forbidden,
    request_params,
    couchdb_json_decode,
    route_prefix,
    json_body,
    configure_plugins,
    read_yaml
)

LOGGER = getLogger("{}.init".format(__name__))
APP_META_FILE = 'app_meta.yaml'


def _couchdb_connection(config):
    aserver, server, db = set_api_security(config)
    config.registry.couchdb_server = server
    if aserver:
        config.registry.admin_couchdb_server = aserver
    config.registry.db = db
    # readjust couchdb json decoder
    couchdb_json_decode()


def _document_service_key(config):
    docsrv_conf = config.registry.app_meta(('config', 'docservice'))
    config.registry.docservice_url = docsrv_conf['docservice_url']
    config.registry.docservice_username = docsrv_conf['docservice_username']
    config.registry.docservice_password = docsrv_conf['docservice_password']
    config.registry.docservice_upload_url = docsrv_conf['docservice_upload_url']
    config.registry.docservice_key = dockey = Signer(docsrv_conf.get('dockey', '').decode('hex'))
    config.registry.auction_module_url = docsrv_conf['auction_url']
    config.registry.signer = Signer(docsrv_conf.get('auction_public_key', '').decode('hex'))
    config.registry.keyring = keyring = {}
    dockeys = docsrv_conf['dockeys'] if 'dockeys' in docsrv_conf else dockey.hex_vk()
    for key in dockeys.split('\0'):
        keyring[key[:8]] = Verifier(key)


def _create_app_meta(global_config):
    file_place = os.path.join(global_config['here'], APP_META_FILE)
    config_data = defaultdict(lambda: None, read_yaml(file_place))
    config_data['here'] = copy(global_config['here'])

    def inner(keys=(), alter=defaultdict(lambda: None)):
        assert  hasattr(keys, '__iter__'), "keys must be iterable"
        level = config_data if keys else defaultdict(lambda: None, config_data)
        for key in keys:
            if not level: break
            nested = type(level[key]) is dict
            level = defaultdict(lambda: None, level[key]) if nested else deepcopy(level[key])
        meta = level if level else deepcopy(alter)
        return meta
    return inner

auth_mapping = {}

def auth(auth_type=None):
    def decorator(func):
        auth_mapping[auth_type] = func
        return func
    return decorator

@auth(auth_type="file")
def _file_auth(app_meta):
    conf_auth = app_meta(('config', 'auth'))
    return os.path.join(app_meta(['here']), conf_auth.get('src', None))

def _auth_factory(auth_type):
    auth_func = auth_mapping.get(auth_type, None)
    return auth_func


def _get_auth(app_meta):
    auth_type = app_meta(('config', 'auth', 'type'))
    auth_func = _auth_factory(auth_type)
    return auth_func(app_meta)


def _config_init(global_config, settings):
    app_meta = _create_app_meta(global_config)
    res = _get_auth(app_meta)
    config = Configurator(
        autocommit=True,
        settings=settings,
        authentication_policy=AuthenticationPolicy(_get_auth(app_meta), __name__),
        authorization_policy=AuthorizationPolicy(),
        route_prefix=route_prefix(app_meta(('config', 'main'))),
    )
    config.include('pyramid_exclog')
    config.include("cornice")
    config.add_forbidden_view(forbidden)
    config.registry.app_meta = app_meta
    config.add_request_method(request_params, 'params', reify=True)
    config.add_request_method(authenticated_role, reify=True)
    config.add_request_method(check_accreditation)
    config.add_request_method(json_body, 'json_body', reify=True)
    config.add_renderer('json', JSON(serializer=simplejson.dumps))
    config.add_renderer('prettyjson', JSON(indent=4, serializer=simplejson.dumps))
    config.add_renderer('jsonp', JSONP(param_name='opt_jsonp', serializer=simplejson.dumps))
    config.add_renderer('prettyjsonp', JSONP(indent=4, param_name='opt_jsonp', serializer=simplejson.dumps))
    return config


def _search_subscribers(config, settings, plugins):
    subscribers_keys = [k for k in settings if k.startswith('subscribers.')]
    for k in subscribers_keys:
        subscribers = settings[k].split(',')
        for subscriber in subscribers:
            configure_plugins(config, plugins, 'openprocurement.{}'.format(k), subscriber)


def _init_plugins(config):
    plugins = config.registry.app_meta(['plugins'])
    LOGGER.info("Start plugins loading", extra={'MESSAGE_ID': 'included_plugin'})
    for name in plugins:
        for entry_point in iter_entry_points('openprocurement.api.plugins', name):
            plugin = entry_point.load()
            plugin(config, plugins.get(name))
    LOGGER.info("End plugins loading", extra={'MESSAGE_ID': 'included_plugin'})


def main(global_config, **settings):
    config = _config_init(global_config, settings)
    _init_plugins(config)
    _couchdb_connection(config)
    _document_service_key(config)
    conf_main = config.registry.app_meta(('config', 'main'))
    config.registry.server_id = conf_main.get('id', '')
    config.registry.health_threshold = float(conf_main.get('health_threshold', 512))
    config.registry.health_threshold_func = conf_main.get('health_threshold_func', 'all')
    config.registry.update_after = asbool(conf_main.get('update_after', True))
    return config.make_wsgi_app()
