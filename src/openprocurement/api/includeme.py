# -*- coding: utf-8 -*-
from pyramid.interfaces import IRequest
from openprocurement.api.interfaces import IContentConfigurator, IOPContent
from openprocurement.api.adapters import ContentConfigurator
from openprocurement.api.utils import get_content_configurator


def includeme(config):
    config.scan("openprocurement.api.views")
    config.scan("openprocurement.api.subscribers")
    config.registry.registerAdapter(ContentConfigurator, (IOPContent, IRequest),
                                    IContentConfigurator)
    config.add_request_method(get_content_configurator, 'content_configurator', reify=True)
