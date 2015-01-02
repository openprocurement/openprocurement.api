# -*- coding: utf-8 -*-
"""Main entry point
"""
import gevent.monkey
gevent.monkey.patch_all()
import os
import pkg_resources
from logging import getLogger
from urlparse import urlparse
from pyramid.config import Configurator
from openprocurement.api.auth import AuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy as AuthorizationPolicy
from pyramid.renderers import JSON, JSONP
from pyramid.events import NewRequest, BeforeRender, ContextFound
from couchdb import Server
from openprocurement.api.design import sync_design
from openprocurement.api.migration import migrate_data
from boto.s3.connection import S3Connection, Location
from openprocurement.api.traversal import factory

try:
    from systemd.journal import JournalHandler
except ImportError:
    JournalHandler = False

LOGGER = getLogger(__name__)
VERSION = int(pkg_resources.get_distribution(__package__).parsed_version[0])


def set_journal_handler(event):
    params = {'PARAMS': str(dict(event.request.params))}
    for i, j in event.request.matchdict.items():
        params[i.upper()] = j
    LOGGER.addHandler(JournalHandler(**params))


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


def get_local_roles(context):
    from pyramid.location import lineage
    roles = {}
    for location in lineage(context):
        try:
            roles = location.__local_roles__
        except AttributeError:
            continue
        if roles and callable(roles):
            roles = roles()
        break
    return roles


def authenticated_role(request):
    principals = reversed(request.effective_principals)
    roles = get_local_roles(request.context)
    local_roles = [roles[i] for i in principals if i in roles]
    if local_roles:
        return local_roles[0]
    groups = [g for g in principals if g.startswith('g:')]
    return groups[0][2:] if groups else 'anonymous'


def fix_url(item, app_url):
    if isinstance(item, list):
        [
            fix_url(i, app_url)
            for i in item
            if isinstance(i, dict) or isinstance(i, list)
        ]
    elif isinstance(item, dict):
        if "format" in item and "url" in item and '?download=' in item['url']:
            s = urlparse(item["url"])
            item["url"] = app_url + s.path + '?' + s.query
            return
        [
            fix_url(item[i], app_url)
            for i in item
            if isinstance(item[i], dict) or isinstance(item[i], list)
        ]


def beforerender(event):
    for i in LOGGER.handlers:
        LOGGER.removeHandler(i)
    if 'data' in event.rendering_val:
        fix_url(event.rendering_val['data'], event['request'].application_url)


def main(global_config, **settings):
    config = Configurator(
        settings=settings,
        root_factory=factory,
        authentication_policy=AuthenticationPolicy(settings['auth.file'], __name__),
        authorization_policy=AuthorizationPolicy(),
    )
    config.add_request_method(authenticated_role, reify=True)
    config.add_renderer('prettyjson', JSON(indent=4))
    config.add_renderer('jsonp', JSONP(param_name='opt_jsonp'))
    config.add_renderer('prettyjsonp', JSONP(indent=4, param_name='opt_jsonp'))
    if JournalHandler:
        config.add_subscriber(set_journal_handler, ContextFound)
    config.add_subscriber(set_renderer, NewRequest)
    config.add_subscriber(beforerender, BeforeRender)
    config.include('pyramid_exclog')
    config.include("cornice")
    config.route_prefix = '/api/{}'.format(VERSION)
    config.scan("openprocurement.api.views")

    # CouchDB connection
    server = Server(settings.get('couchdb.url'))
    config.registry.couchdb_server = server
    db_name = os.environ.get('DB_NAME', settings['couchdb.db_name'])
    if db_name not in server:
        server.create(db_name)
    config.registry.db = server[db_name]

    # sync couchdb views
    sync_design(config.registry.db)

    # migrate data
    migrate_data(config.registry.db)

    # S3 connection
    if 'aws.access_key' in settings and 'aws.secret_key' in settings and 'aws.s3_bucket' in settings:
        connection = S3Connection(settings['aws.access_key'], settings['aws.secret_key'])
        config.registry.s3_connection = connection
        bucket_name = settings['aws.s3_bucket']
        if bucket_name not in [b.name for b in connection.get_all_buckets()]:
            connection.create_bucket(bucket_name, location=Location.EU)
        config.registry.bucket_name = bucket_name
    return config.make_wsgi_app()
