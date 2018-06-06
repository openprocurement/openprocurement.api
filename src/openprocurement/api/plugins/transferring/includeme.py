# -*- coding: utf-8 -*-
from logging import getLogger

from openprocurement.api.app import get_evenly_plugins
from openprocurement.api.plugins.transferring.utils import (
    transfer_from_data,
    extract_transfer,
    change_ownership
)

LOGGER = getLogger(__name__)


def includeme(config, plugin_map):  # pylint: disable=unused-argument
    config.add_request_method(extract_transfer, 'transfer', reify=True)
    config.add_request_method(transfer_from_data)
    config.add_request_method(change_ownership)
    config.scan("openprocurement.api.plugins.transferring.views")
    LOGGER.info("Included transferring plugin",
                extra={'MESSAGE_ID': 'included_plugin'})
    get_evenly_plugins(
        config, plugin_map['plugins'], 'transferring'
    )
