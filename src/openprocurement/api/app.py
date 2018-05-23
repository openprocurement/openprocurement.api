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
from copy import copy
from collections import defaultdict as dd
from zope.component import getGlobalSiteManager

from pyramid.settings import asbool
from pyramid.config import Configurator
from libnacl.sign import Signer, Verifier
from pyramid.renderers import JSON, JSONP
from pkg_resources import iter_entry_points
from pyramid.authorization import ACLAuthorizationPolicy as AuthorizationPolicy

from openprocurement.api.utils import (
    forbidden,
    request_params,
    couchdb_json_decode,
    route_prefix,
    json_body,
    read_yaml,
)

from openprocurement.api.database import set_api_security
from openprocurement.api.design import sync_design
from openprocurement.api.auth import AuthenticationPolicy, authenticated_role, check_accreditation
from openprocurement.api.configurator import Configurator as ProjectConfigurator, configuration_info
from openprocurement.api.interfaces import IProjectConfigurator
from openprocurement.api.auth import get_auth
from .config import AppMetaSchema

LOGGER = getLogger("{}.init".format(__name__))
APP_META_FILE = 'app_meta.yaml'


def _couchdb_connection(config):
    database_config = config.registry.app_meta.config.db
    aserver, server, db = set_api_security(database_config)
    config.registry.couchdb_server = server
    if aserver:
        config.registry.admin_couchdb_server = aserver
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


def _create_app_meta(global_config):
    """This function returns schematics.models.Model object which contains configuration
    of the application. Configuration file reading will be performed only once.

    Current function must be called only once during app initialization.

    :param global_config: it is instance of pyramid global config
    :type global_config: dict
    :rtype: schematics.models.Model
    """
    file_place = os.path.join(global_config['here'], APP_META_FILE)
    config_data = dd(lambda: None, read_yaml(file_place))
    config_data['here'] = copy(global_config['here'])
    app_meta = AppMetaSchema(config_data)
    app_meta.validate()
    return app_meta


def _config_init(global_config, settings):
    app_meta = _create_app_meta(global_config)
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


def get_evenly_plugins(config, plugin_map, group):
    """
    Load plugin which fall into the group

    :param config: app config
    :param plugin_map: mapping of plugins names
    :param group: group of entry point

    :type config: Configurator
    :type plugin_map: abs.Mapping
    :type group: string

    :rtype: None
    """

    if not hasattr(plugin_map, '__iter__'):
        return
    for name in plugin_map:
        for entry_point in iter_entry_points(group, name):
            plugin = entry_point.load()
            value = plugin_map.get(name) if plugin_map.get(name) else {}
            plugin(config, dd(lambda: None, value))


def _set_up_configurator(config, plugins):
    get_evenly_plugins(config, plugins, 'openprocurement.api.configurator')
    gsm = getGlobalSiteManager()
    if gsm.queryUtility(IProjectConfigurator) is None:
        gsm.registerUtility(ProjectConfigurator(configuration_info, {}), IProjectConfigurator)


def _init_plugins(config):
    plugins = config.registry.app_meta.plugins
    LOGGER.info("Start plugins loading", extra={'MESSAGE_ID': 'included_plugin'})
    _set_up_configurator(config, plugins)
    get_evenly_plugins(config, plugins, 'openprocurement.api.plugins')


def main(global_config, **settings):
    config = _config_init(global_config, settings)
    _couchdb_connection(config)
    _init_plugins(config)
    _auction_module(config)
    # sync couchdb views
    sync_design(config.registry.db)
    _document_service_key(config)
    conf_main = config.registry.app_meta.config.main
    config.registry.server_id = conf_main.server_id
    config.registry.health_threshold = float(conf_main.get('health_threshold', 512))
    config.registry.health_threshold_func = conf_main.get('health_threshold_func', 'all')
    config.registry.update_after = asbool(conf_main.get('update_after', True))
    return config.make_wsgi_app()
