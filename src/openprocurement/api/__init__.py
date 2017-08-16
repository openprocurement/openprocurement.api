# -*- coding: utf-8 -*-
"""Main entry point
"""
if 'test' not in __import__('sys').argv[0]:
    import gevent.monkey
    gevent.monkey.patch_all()
import os
from libnacl.sign import Signer, Verifier
from libnacl.public import SecretKey, PublicKey
from logging import getLogger
from openprocurement.api.auth import AuthenticationPolicy, authenticated_role, check_accreditation
from openprocurement.api.models import Tender
from openprocurement.api.database import set_api_security
from openprocurement.api.utils import (
    forbidden,
    add_logging_context,
    set_logging_context,
    extract_tender,
    request_params,
    isTender,
    set_renderer,
    beforerender,
    register_tender_procurementMethodType,
    tender_from_data,
    ROUTE_PREFIX
)
from pkg_resources import iter_entry_points
from pyramid.authorization import ACLAuthorizationPolicy as AuthorizationPolicy
from pyramid.config import Configurator
from pyramid.events import NewRequest, BeforeRender, ContextFound
from pyramid.renderers import JSON, JSONP
from pyramid.settings import asbool

LOGGER = getLogger("{}.init".format(__name__))


def main(global_config, **settings):
    config = Configurator(
        autocommit=True,
        settings=settings,
        authentication_policy=AuthenticationPolicy(settings['auth.file'], __name__),
        authorization_policy=AuthorizationPolicy(),
        route_prefix=ROUTE_PREFIX,
    )
    config.include('pyramid_exclog')
    config.include("cornice")
    config.add_forbidden_view(forbidden)
    config.add_request_method(request_params, 'params', reify=True)
    config.add_request_method(authenticated_role, reify=True)
    config.add_request_method(extract_tender, 'tender', reify=True)
    config.add_request_method(check_accreditation)
    config.add_renderer('prettyjson', JSON(indent=4))
    config.add_renderer('jsonp', JSONP(param_name='opt_jsonp'))
    config.add_renderer('prettyjsonp', JSONP(indent=4, param_name='opt_jsonp'))
    config.add_subscriber(add_logging_context, NewRequest)
    config.add_subscriber(set_logging_context, ContextFound)
    config.add_subscriber(set_renderer, NewRequest)
    config.add_subscriber(beforerender, BeforeRender)
    config.scan("openprocurement.api.views.spore")
    config.scan("openprocurement.api.views.health")

    # tender procurementMethodType plugins support
    config.add_route_predicate('procurementMethodType', isTender)
    config.registry.tender_procurementMethodTypes = {}
    config.add_request_method(tender_from_data)
    config.add_directive('add_tender_procurementMethodType', register_tender_procurementMethodType)

    # search for plugins
    plugins = settings.get('plugins') and settings['plugins'].split(',')
    for entry_point in iter_entry_points('openprocurement.api.plugins'):
        if not plugins or entry_point.name in plugins:
            plugin = entry_point.load()
            plugin(config)

    # CouchDB connection
    aserver, server, db = set_api_security(settings)
    config.registry.couchdb_server = server
    if aserver:
        config.registry.admin_couchdb_server = aserver
    config.registry.db = db

    # Document Service key
    config.registry.docservice_url = settings.get('docservice_url')
    config.registry.docservice_username = settings.get('docservice_username')
    config.registry.docservice_password = settings.get('docservice_password')
    config.registry.docservice_upload_url = settings.get('docservice_upload_url')
    config.registry.docservice_key = dockey = Signer(settings.get('dockey', '').decode('hex'))
    config.registry.keyring = keyring = {}
    dockeys = settings.get('dockeys') if 'dockeys' in settings else dockey.hex_vk()
    for key in dockeys.split('\0'):
        keyring[key[:8]] = Verifier(key)

    # Archive keys
    arch_pubkey = settings.get('arch_pubkey', None)
    config.registry.arch_pubkey = PublicKey(arch_pubkey.decode('hex') if arch_pubkey else SecretKey().pk)

    # migrate data
    if not os.environ.get('MIGRATION_SKIP'):
        for entry_point in iter_entry_points('openprocurement.api.migrations'):
            plugin = entry_point.load()
            plugin(config.registry)

    config.registry.server_id = settings.get('id', '')

    # search subscribers
    subscribers_keys = [k for k in settings if k.startswith('subscribers.')]
    for k in subscribers_keys:
        subscribers = settings[k].split(',')
        for subscriber in subscribers:
            for entry_point in iter_entry_points('openprocurement.{}'.format(k), subscriber):
                if entry_point:
                    plugin = entry_point.load()
                    plugin(config)

    config.registry.health_threshold = float(settings.get('health_threshold', 512))
    config.registry.health_threshold_func = settings.get('health_threshold_func', 'all')
    config.registry.update_after = asbool(settings.get('update_after', True))
    return config.make_wsgi_app()


def includeme(config):
    config.add_tender_procurementMethodType(Tender)
    config.scan("openprocurement.api.views")
