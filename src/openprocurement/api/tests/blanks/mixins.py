# -*- coding: utf-8 -*-

from openprocurement.api.tests.base import snitch

from .core_resource import empty_listing
from .resource import (
    listing,
    listing_changes,
    listing_draft,
    resource_not_found,
    dateModified_resource,
    get_resource,
    create_resource
)
from .document import (
    not_found,
    create_document_in_forbidden_resource_status,
    put_resource_document_invalid,
    patch_resource_document,
    create_resource_document_error,
    create_resource_document_json_invalid,
    create_resource_document_json,
    put_resource_document_json
)


class CoreResourceTestMixin(object):
    """ Mixin that contains tests for core packages
    """

    test_empty_listing = snitch(empty_listing)


class ResourceTestMixin(object):
    """ Mixin with common tests for Asset and Lot
    """

    test_01_listing = snitch(listing)
    test_02_listing_changes = snitch(listing_changes)
    test_03_listing_draft = snitch(listing_draft)
    test_04_resource_not_found = snitch(resource_not_found)
    test_05_dateModified_resource = snitch(dateModified_resource)
    test_06_get_resource = snitch(get_resource)
    test_07_create_resource = snitch(create_resource)


class ResourceDocumentTestMixin(object):
    """ Mixin with common tests for Asset and Lot documents
    """

    test_01_not_found = snitch(not_found)
    test_02_create_document_in_forbidden_resource_status = snitch(create_document_in_forbidden_resource_status)
    test_03_put_resource_document_invalid = snitch(put_resource_document_invalid)
    test_04_patch_resource_document = snitch(patch_resource_document)
    test_05_create_resource_document_error = snitch(create_resource_document_error)
    test_06_create_resource_document_json_invalid = snitch(create_resource_document_json_invalid)
    test_07_create_resource_document_json = snitch(create_resource_document_json)
    test_08_put_resource_document_json = snitch(put_resource_document_json)
