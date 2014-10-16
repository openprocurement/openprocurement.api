"""Main entry point
"""
from pyramid.config import Configurator

VERSION = '0.1'


def main(global_config, **settings):
    config = Configurator(settings=settings)
#    config.route_prefix = '/api/0.1'
#    config.include("cornice", route_prefix='/api/0.1')
    config.include("cornice")
    config.route_prefix = '/api/{}'.format(VERSION)
    config.scan("openprocurement.api.views")
    return config.make_wsgi_app()
