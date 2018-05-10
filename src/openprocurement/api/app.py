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
from copy import deepcopy, copy
from collections import defaultdict as dd

from pyramid.settings import asbool
from pyramid.config import Configurator
from libnacl.sign import Signer, Verifier
from pyramid.renderers import JSON, JSONP
from pkg_resources import iter_entry_points
from libnacl.public import SecretKey, PublicKey
from pyramid.authorization import ACLAuthorizationPolicy as AuthorizationPolicy

from openprocurement.api.utils import (
    forbidden,
    request_params,
    couchdb_json_decode,
    route_prefix,
    json_body,
    read_yaml
)
from openprocurement.api.database import set_api_security
from openprocurement.api.auth import AuthenticationPolicy, authenticated_role, check_accreditation

from openprocurement.api.auth import get_auth

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
    """This function returns the function that returns the configuration of the application
    reading configuration file will be only once

    call of creating_app_meta must be only once in app initalization
    next times must call inner function

    if we have configuration file like this:
    plugins:
      api:
    config:
      auth:
        type: file
        src: auth.ini
      database:
        db_name: test
        couchdb.url: http://db.url

    in order to get the embedded configuration it is necessary to list the nesting level
    as the first argument, and it argument must be iterable
    example:
        app_meta = create_app_meta(global_config)
        conf_db = app_meta(('config', 'database')]

    If you want the default value, you can pass it to second argument
    example:
        conf_db = app_meta(('config', 'not_exist'), False]

    :param global_config: it is instance of pyramid global config
    :type global_config: dict
    :rtype: function

    inner return always copy of config it mean what you can change it and
    origin config will be without changes

    inner return defaultdict and it add flexibility to config
    you dont need to care about checking return value if it does not exist will
    be None

    example:
        conf_db = app_meta(('config', 'not_exist'))
        conf_db['foo'] == None
        True

    """
    file_place = os.path.join(global_config['here'], APP_META_FILE)
    config_data = dd(lambda: None, read_yaml(file_place))
    config_data['here'] = copy(global_config['here'])

    def inner(keys=(), alter=dd(lambda: None)):
        assert  hasattr(keys, '__iter__'), "keys must be iterable"
        level = config_data if keys else dd(lambda: None, config_data)
        for key in keys:
            if not level:
                break
            nested = isinstance(level[key], dict)
            level = dd(lambda: None, level[key]) if nested else deepcopy(level[key])
        meta = level if level else deepcopy(alter)
        return meta
    return inner


def _config_init(global_config, settings):
    app_meta = _create_app_meta(global_config)
    config = Configurator(
        autocommit=True,
        settings=settings,
        authentication_policy=AuthenticationPolicy(get_auth(app_meta), __name__),
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


def _init_plugins(config):
    plugins = config.registry.app_meta(['plugins'])
    LOGGER.info("Start plugins loading", extra={'MESSAGE_ID': 'included_plugin'})
    get_evenly_plugins(config, plugins, 'openprocurement.api.plugins')
    LOGGER.info("End plugins loading", extra={'MESSAGE_ID': 'included_plugin'})


def main(global_config, **settings):
    config = _config_init(global_config, settings)
    _couchdb_connection(config)
    _init_plugins(config)
    _document_service_key(config)
    conf_main = config.registry.app_meta(('config', 'main'))
    config.registry.server_id = conf_main.get('id', '')
    config.registry.health_threshold = float(conf_main.get('health_threshold', 512))
    config.registry.health_threshold_func = conf_main.get('health_threshold_func', 'all')
    config.registry.update_after = asbool(conf_main.get('update_after', True))
    return config.make_wsgi_app()
