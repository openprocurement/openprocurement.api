# -*- coding: utf-8 -*-
"""Main entry point
"""
# flake8: noqa
if 'test' not in __import__('sys').argv[0]:
    import gevent.monkey
    gevent.monkey.patch_all()

import simplejson
from logging import getLogger

from libnacl.public import SecretKey, PublicKey
from libnacl.sign import Signer, Verifier
from pkg_resources import iter_entry_points
from pyramid.authorization import ACLAuthorizationPolicy as AuthorizationPolicy
from pyramid.config import Configurator
from pyramid.renderers import JSON, JSONP
from pyramid.settings import asbool

from openprocurement.api.auth import AuthenticationPolicy, authenticated_role, check_accreditation
from openprocurement.api.database import set_api_security
from openprocurement.api.utils import (
    forbidden,
    request_params,
    couchdb_json_decode,
    route_prefix,
    json_body,
    configure_plugins,
    read_yaml,
    check_settings
)

LOGGER = getLogger("{}.init".format(__name__))


def _default(config, settings):
    config.registry.health_threshold = float(settings.get('health_threshold', 512))
    config.registry.health_threshold_func = settings.get('health_threshold_func', 'all')
    config.registry.update_after = asbool(settings.get('update_after', True))
    check_settings(config.registry.__dict__, section='_default')


def _couchdb_connection(config, settings):
    aserver, server, db = set_api_security(settings)
    config.registry.couchdb_server = server
    if aserver:
        config.registry.admin_couchdb_server = aserver
    config.registry.db = db
    # readjust couchdb json decoder
    couchdb_json_decode()
    check_settings(config.registry.__dict__, section='_couchdb_connection')


def _document_service_key(config, settings):
    config.registry.docservice_url = settings.get('docservice_url')
    config.registry.docservice_username = settings.get('docservice_username')
    config.registry.docservice_password = settings.get('docservice_password')
    config.registry.docservice_upload_url = settings.get('docservice_upload_url')
    config.registry.docservice_key = dockey = Signer(settings.get('dockey', '').decode('hex'))
    config.registry.keyring = keyring = {}
    dockeys = settings.get('dockeys') if 'dockeys' in settings else dockey.hex_vk()
    for key in dockeys.split('\0'):
        keyring[key[:8]] = Verifier(key)
    check_settings(config.registry.__dict__, section='_document_service_key')


def _auction(config, settings):
    # config.registry.auction_module_url = settings.get('auction_url')
    config.registry.signer = Signer(settings.get('auction_public_key', '').decode('hex'))
    check_settings(config.registry.__dict__, section='_auction')


def _config_init(settings):
    config = Configurator(
        autocommit=True,
        settings=settings,
        authentication_policy=AuthenticationPolicy(settings['auth.file'], __name__),
        authorization_policy=AuthorizationPolicy(),
        route_prefix=route_prefix(settings),
    )
    config.include('pyramid_exclog')
    config.include("cornice")
    config.add_forbidden_view(forbidden)
    config.add_request_method(request_params, 'params', reify=True)
    config.add_request_method(authenticated_role, reify=True)
    config.add_request_method(check_accreditation)
    config.add_request_method(json_body, 'json_body', reify=True)
    config.add_renderer('json', JSON(serializer=simplejson.dumps))
    config.add_renderer('prettyjson', JSON(indent=4, serializer=simplejson.dumps))
    config.add_renderer('jsonp', JSONP(param_name='opt_jsonp', serializer=simplejson.dumps))
    config.add_renderer('prettyjsonp', JSONP(indent=4, param_name='opt_jsonp', serializer=simplejson.dumps))
    check_settings(config.registry.settings, section='_config_init')
    return config


def _search_subscribers(config, settings, plugins):
    subscribers_keys = [k for k in settings if k.startswith('subscribers.')]
    for k in subscribers_keys:
        subscribers = settings[k].split(',')
        for subscriber in subscribers:
            configure_plugins(config, plugins, 'openprocurement.{}'.format(k), subscriber)


def _init_plugins(config, settings):
    plugins = read_yaml(settings['plugins'])
    LOGGER.info("Start plugins loading", extra={'MESSAGE_ID': 'included_plugin'})
    for name in plugins:
        for entry_point in iter_entry_points('openprocurement.api.plugins', name):
            plugin = entry_point.load()
            plugin(config, plugins.get(name))
    LOGGER.info("End plugins loading", extra={'MESSAGE_ID': 'included_plugin'})


def main(_, **settings):
    config = _config_init(settings)
    _init_plugins(config, settings)
    _couchdb_connection(config, settings)
    _document_service_key(config, settings)
    _auction(config, settings)
    # Archive keys
    arch_pubkey = settings.get('arch_pubkey', None)
    config.registry.arch_pubkey = PublicKey(arch_pubkey.decode('hex') if arch_pubkey else SecretKey().pk)
    config.registry.server_id = settings.get('id', '')
    check_settings(config.registry.__dict__, section='main')
    _default(config, settings)
    # _search_subscribers(config, settings, config.plugins)
    return config.make_wsgi_app()
