# -*- coding: utf-8 -*-
import logging

from pyramid.interfaces import IRequest
from openprocurement.api.interfaces import IContentConfigurator, IOPContent
from openprocurement.api.adapters import ContentConfigurator
from openprocurement.api.utils import get_content_configurator, request_get_now, configure_plugins

LOGGER = logging.getLogger(__name__)


def includeme(config, plugin_config=None):
    config.scan("openprocurement.api.views")
    config.scan("openprocurement.api.subscribers")
    config.registry.registerAdapter(ContentConfigurator, (IOPContent, IRequest),
                                    IContentConfigurator)
    config.add_request_method(
        get_content_configurator, 'content_configurator', reify=True
    )
    config.add_request_method(request_get_now, 'now', reify=True)
    if plugin_config and plugin_config.get('plugins'):
        for name in plugin_config['plugins']:
            configure_plugins(
                config, {name: plugin_config['plugins'][name]},
                'openprocurement.api.plugins', name
            )

    LOGGER.info("Included openprocurement.api plugin",
                extra={'MESSAGE_ID': 'included_plugin'})
