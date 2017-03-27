# -*- coding: utf-8 -*-
from pyramid.interfaces import IRequest
from openprocurement.api.interfaces import IContentConfigurator, IOPContent
from openprocurement.api.adapters import ContentConfigurator


def includeme(config):
    config.scan("openprocurement.api.views")
    config.scan("openprocurement.api.subscribers")
    config.registry.registerAdapter(ContentConfigurator, (IOPContent, IRequest),
                                    IContentConfigurator)
