# -*- coding: utf-8 -*-
"""Main entry point
"""
import os
import pkg_resources
from pyramid.config import Configurator
from pyramid.renderers import JSON, JSONP
from pyramid.events import NewRequest
from couchdb import Server
from openprocurement.api.design import tenders_all_view
from openprocurement.api.migration import migrate_data


VERSION = int(pkg_resources.get_distribution(__package__).parsed_version[0])


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


def main(global_config, **settings):
    config = Configurator(settings=settings)
    config.add_renderer('prettyjson', JSON(indent=4))
    config.add_renderer('jsonp', JSONP(param_name='opt_jsonp'))
    config.add_renderer('prettyjsonp', JSONP(indent=4, param_name='opt_jsonp'))
    config.add_subscriber(set_renderer, NewRequest)
    config.include("cornice")
    config.route_prefix = '/api/{}'.format(VERSION)
    config.scan("openprocurement.api.views")

    # CouchDB connection
    server = Server()
    config.registry.couchdb_server = server
    db_name = os.environ.get('DB_NAME', settings['couchdb.db_name'])
    if db_name not in server:
        server.create(db_name)
    config.registry.db = server[db_name]

    # sync couchdb views
    tenders_all_view.sync(config.registry.db)

    # migrate data
    migrate_data(config.registry.db)
    return config.make_wsgi_app()
