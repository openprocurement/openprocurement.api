# -*- coding: utf-8 -*-
"""Main entry point
"""
# flake8: noqa
if 'test' not in __import__('sys').argv[0]:
    import gevent.monkey
    gevent.monkey.patch_all()

import os
import simplejson
from logging import getLogger
from copy import copy, deepcopy
from collections import defaultdict as dd
from zope.component import getGlobalSiteManager

from pyramid.settings import asbool
from pyramid.config import Configurator
from libnacl.sign import Signer, Verifier
from pyramid.renderers import JSON, JSONP
from pyramid.authorization import ACLAuthorizationPolicy as AuthorizationPolicy

from openprocurement.api.utils import (
    forbidden,
    request_params,
    couchdb_json_decode,
    route_prefix,
    json_body,
    read_yaml,
    get_evenly_plugins,
    get_plugins,
    create_app_meta,
)
from openprocurement.api.utils.manager_registry import init_manager_registry

from openprocurement.api.database import set_api_security
from openprocurement.api.design import sync_design
from openprocurement.api.auth import AuthenticationPolicy, authenticated_role, check_accreditation
from openprocurement.api.configurator import Configurator as ProjectConfigurator, configuration_info
from openprocurement.api.interfaces import IProjectConfigurator
from openprocurement.api.auth import get_auth
from openprocurement.api.constants import APP_META_FILE

LOGGER = getLogger("{}.init".format(__name__))


def _couchdb_connection(config):
    database_config = config.registry.app_meta.config.db
    aserver, server, adb, db = set_api_security(database_config)
    config.registry.couchdb_server = server
    if aserver:
        config.registry.admin_couchdb_server = aserver
        config.registry.adb = adb
    config.registry.db = db
    # readjust couchdb json decoder
    couchdb_json_decode()


def _auction_module(config):
    auction_module_conf = config.registry.app_meta.config.auction
    if not auction_module_conf:
        return
    config.registry.auction_module_url = auction_module_conf.url
    config.registry.signer = auction_module_conf.signer


def _document_service_key(config):
    docsrv_conf = config.registry.app_meta.config.ds
    if not docsrv_conf:
        config.registry.use_docservice = False
        return
    config.registry.use_docservice = True
    config.registry.docservice_url = docsrv_conf.download_url
    config.registry.docservice_username = docsrv_conf.user.name
    config.registry.docservice_password = docsrv_conf.user.password
    config.registry.docservice_upload_url = docsrv_conf.upload_url
    config.registry.docservice_key = dockey = docsrv_conf.signer
    config.registry.keyring = docsrv_conf.init_keyring(dockey)


def _config_init(global_config, settings):
    app_meta_filepath = os.path.join(global_config['here'], APP_META_FILE)
    app_meta = create_app_meta(app_meta_filepath)
    config = Configurator(
        autocommit=True,
        settings=settings,
        authentication_policy=AuthenticationPolicy(get_auth(app_meta), __name__),
        authorization_policy=AuthorizationPolicy(),
        route_prefix=route_prefix(app_meta.config.main),
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


def _set_up_configurator(config, plugins):
    configurator_plugin_map = {
        key: value for key, value in plugins.items() if 'configurator' in key
    }

    # To prevent search of entry points for configurator plugins in 'openprocurement.api.plugins' group
    for key in configurator_plugin_map:
        plugins.pop(key)

    get_evenly_plugins(config, configurator_plugin_map, 'openprocurement.api.configurator')
    gsm = getGlobalSiteManager()
    if gsm.queryUtility(IProjectConfigurator) is None:
        gsm.registerUtility(ProjectConfigurator(configuration_info, {}), IProjectConfigurator)


def _init_plugins(config):
    plugins = deepcopy(config.registry.app_meta.plugins)
    LOGGER.info("Start plugins loading", extra={'MESSAGE_ID': 'included_plugin'})
    _set_up_configurator(config, plugins)
    config.registry.accreditation = {}
    get_evenly_plugins(config, plugins, 'openprocurement.api.plugins')
    LOGGER.info("End plugins loading", extra={'MESSAGE_ID': 'included_plugin'})


def main(global_config, **settings):
    config = _config_init(global_config, settings)
    _couchdb_connection(config)
    init_manager_registry(config.registry)
    config.registry.m = 'lalalal'
    _init_plugins(config)
    _auction_module(config)
    # sync couchdb views
    sync_design(getattr(config.registry, 'adb', config.registry.db))
    _document_service_key(config)
    conf_main = config.registry.app_meta.config.main
    config.registry.server_id = conf_main.server_id
    config.registry.health_threshold = float(conf_main.get('health_threshold', 512))
    config.registry.health_threshold_func = conf_main.get('health_threshold_func', 'all')
    config.registry.update_after = asbool(conf_main.get('update_after', True))
    return config.make_wsgi_app()
