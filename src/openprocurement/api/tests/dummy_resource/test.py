# -*- coding: utf-8 -*-
import os
import unittest
from pyramid import testing
from mock import Mock, MagicMock, patch

from paste.deploy.loadwsgi import appconfig

from openprocurement.api.tests.dummy_resource.views import DummyResource

settings = appconfig('config:' + os.path.join(os.path.dirname(__file__), '..', 'tests.ini'))


class BaseAPIUnitTest(unittest.TestCase):
    """ Base TestCase class for unit tests of API functionality
    """

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()


class TestAPIResourceListing(BaseAPIUnitTest):
    """ TestCase for APIResource and APIResourceListing
    """

    def setUp(self):
        super(TestAPIResourceListing, self).setUp()
        self.config.include('cornice')
        self.config.scan('.views')

        self.request = testing.DummyRequest()
        self.request.registry.db = Mock()
        self.request.registry.server_id = Mock()
        self.request.registry.couchdb_server = Mock()
        self.request.registry.update_after = True

        self.context = Mock()

    def test_01_listing(self):

        view = DummyResource(self.request, self.context)
        response = view.get()

        self.assertEqual(response['data'], [])
        self.assertNotIn('prev_page', response)

    def test_02_listing_opt_fields(self):

        self.request.params['opt_fields'] = 'status'
        self.request.logging_context = MagicMock()

        view = DummyResource(self.request, self.context)
        response = view.get()

        self.assertEqual(response['data'], [])

    def test_03_listing_limit(self):

        self.request.params['limit'] = '10'

        view = DummyResource(self.request, self.context)
        response = view.get()

        self.assertEqual(response['data'], [])

    def test_04_listing_offset(self):

        self.request.params['offset'] = '2015-01-01T00:00:00+02:00'

        view = DummyResource(self.request, self.context)
        response = view.get()

        self.assertEqual(response['data'], [])

    def test_05_listing_descending(self):

        self.request.params['descending'] = '1'

        view = DummyResource(self.request, self.context)
        response = view.get()

        self.assertEqual(response['data'], [])

    def test_06_listing_feed(self):

        self.request.params['feed'] = 'changes'

        view = DummyResource(self.request, self.context)
        response = view.get()

        self.assertEqual(response['data'], [])


    def test_07_listing_mode(self):

        self.request.params['mode'] = u'test'

        view = DummyResource(self.request, self.context)
        response = view.get()

        self.assertEqual(response['data'], [])

    def test_08_listing_feed_and_offset_error(self):

        self.request.errors = Mock(**{'add': Mock()})

        self.request.params['feed'] = 'changes'
        self.request.params['offset'] = '0'

        view = DummyResource(self.request, self.context)

        class OffsetExpired(Exception):
            """ Test exception for error_handler mocking"""

        with patch('openprocurement.api.utils.api_resource.error_handler',
                   return_value=OffsetExpired):
            with self.assertRaises(OffsetExpired):
                response = view.get()


def suite():
    tests = unittest.TestSuite()
    tests.addTest(unittest.makeSuite(TestAPIResourceListing))
    return tests


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
