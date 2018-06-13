# -*- coding: utf-8 -*-
import unittest

from mock import MagicMock, Mock, patch
from openprocurement.api.validation import (
    validate_accreditations,
    validate_document_data,
    validate_t_accreditation,
)
from openprocurement.api.tests.base import (
    DummyException,
)


@patch('openprocurement.api.validation.check_document', autospec=True)
@patch('openprocurement.api.validation.set_first_document_fields', autospec=True)
@patch('openprocurement.api.validation.get_first_document', autospec=True)
@patch('openprocurement.api.validation.update_document_url', autospec=True)
@patch('openprocurement.api.validation.validate_data', autospec=True)
@patch('openprocurement.api.validation.get_type', autospec=True)
class ValidateDocumentDataTest(unittest.TestCase):

    def setUp(self):
        self.mocked_request = MagicMock()
        self.document_mock = MagicMock()
        self.document_mock_with_updated_url = MagicMock()
        self.mocked_request.validated = {'document': self.document_mock}
        self.mocked_request.context = MagicMock()
        self.mocked_request.matched_route.name.replace = MagicMock(return_value='document_route')

        self.type_of_context = MagicMock()
        self.model_class = MagicMock()
        self.type_of_context.documents.model_class = self.model_class

    def test_documentOf_in_document(
        self,
        mocked_get_type,
        mocked_validate_data,
        mocked_update_document_url,
        mocked_get_first,
        mocked_set_first_document_fields,
        mocked_check_document
    ):
        # Mocking
        self.mocked_request.context.__contains__.return_value = True
        self.document_mock.documentOf = 'resourceName'

        mocked_get_type.return_value = self.type_of_context
        mocked_get_first.return_value = None

        mocked_update_document_url.return_value = self.document_mock_with_updated_url

        # Testing
        validate_document_data(self.mocked_request)

        self.assertEqual(mocked_validate_data.call_count, 1)
        mocked_validate_data.assert_called_with(self.mocked_request, self.model_class, "document")

        self.assertEqual(mocked_get_first.call_count, 1)
        mocked_get_first.assert_called_with(self.mocked_request)

        self.assertEqual(mocked_check_document.call_count, 1)
        mocked_check_document.assert_called_with(self.mocked_request, self.document_mock, 'body')

        self.assertEqual(mocked_update_document_url.call_count, 1)
        mocked_update_document_url.assert_called_with(
            self.mocked_request,
            self.document_mock,
            'document_route',
            {}
        )

        self.assertEqual(mocked_get_type.call_count, 1)
        mocked_get_type.assert_called_with(self.mocked_request.context)

        self.assertEqual(mocked_set_first_document_fields.call_count, 0)

        self.assertEqual(self.document_mock.documentOf, 'resourceName')

        self.assertIs(self.mocked_request.validated['document'], self.document_mock_with_updated_url)

    def test_documentOf_not_in_document(
        self,
        mocked_get_type,
        mocked_validate_data,
        mocked_update_document_url,
        mocked_get_first,
        mocked_set_first_document_fields,
        mocked_check_document
    ):
        # Mocking
        self.mocked_request.context.__contains__.return_value = True
        self.document_mock.documentOf = None
        self.type_of_context.__name__ = MagicMock()
        self.type_of_context.__name__.lower.return_value = 'resource_from_context'

        mocked_get_type.return_value = self.type_of_context
        mocked_get_first.return_value = None

        mocked_update_document_url.return_value = self.document_mock_with_updated_url

        # Testing
        validate_document_data(self.mocked_request)

        self.assertEqual(mocked_validate_data.call_count, 1)
        mocked_validate_data.assert_called_with(self.mocked_request, self.model_class, "document")

        self.assertEqual(mocked_get_first.call_count, 1)
        mocked_get_first.assert_called_with(self.mocked_request)

        self.assertEqual(mocked_check_document.call_count, 1)
        mocked_check_document.assert_called_with(self.mocked_request, self.document_mock, 'body')

        self.assertEqual(mocked_update_document_url.call_count, 1)
        mocked_update_document_url.assert_called_with(
            self.mocked_request,
            self.document_mock,
            'document_route',
            {}
        )

        self.assertEqual(mocked_get_type.call_count, 2)
        mocked_get_type.assert_called_with(self.mocked_request.context)

        self.assertEqual(mocked_set_first_document_fields.call_count, 0)

        self.assertEqual(self.document_mock.documentOf, 'resource_from_context')

        self.assertIs(self.mocked_request.validated['document'], self.document_mock_with_updated_url)

    def test_first_document(
        self,
        mocked_get_type,
        mocked_validate_data,
        mocked_update_document_url,
        mocked_get_first,
        mocked_set_first_document_fields,
        mocked_check_document
    ):
        # Mocking
        self.mocked_request.context.__contains__.return_value = True
        self.document_mock.documentOf = 'resourceName'
        first_document = MagicMock()

        mocked_get_type.return_value = self.type_of_context
        mocked_get_first.return_value = first_document

        mocked_update_document_url.return_value = self.document_mock_with_updated_url

        # Testing
        validate_document_data(self.mocked_request)

        self.assertEqual(mocked_validate_data.call_count, 1)
        mocked_validate_data.assert_called_with(self.mocked_request, self.model_class, "document")

        self.assertEqual(mocked_get_first.call_count, 1)
        mocked_get_first.assert_called_with(self.mocked_request)

        self.assertEqual(mocked_check_document.call_count, 1)
        mocked_check_document.assert_called_with(self.mocked_request, self.document_mock, 'body')

        self.assertEqual(mocked_update_document_url.call_count, 1)
        mocked_update_document_url.assert_called_with(
            self.mocked_request,
            self.document_mock,
            'document_route',
            {}
        )

        self.assertEqual(mocked_get_type.call_count, 1)
        mocked_get_type.assert_called_with(self.mocked_request.context)

        self.assertEqual(mocked_set_first_document_fields.call_count, 1)
        mocked_set_first_document_fields.assert_called_with(
            self.mocked_request,
            first_document,
            self.document_mock
        )

        self.assertEqual(self.document_mock.documentOf, 'resourceName')

        self.assertIs(self.mocked_request.validated['document'], self.document_mock_with_updated_url)

    def test_not_first_document(
        self,
        mocked_get_type,
        mocked_validate_data,
        mocked_update_document_url,
        mocked_get_first,
        mocked_set_first_document_fields,
        mocked_check_document
    ):
        # Mocking
        self.mocked_request.context.__contains__.return_value = True
        self.document_mock.documentOf = 'resourceName'

        mocked_get_type.return_value = self.type_of_context
        mocked_get_first.return_value = None

        mocked_update_document_url.return_value = self.document_mock_with_updated_url

        # Testing
        validate_document_data(self.mocked_request)

        self.assertEqual(mocked_validate_data.call_count, 1)
        mocked_validate_data.assert_called_with(self.mocked_request, self.model_class, "document")

        self.assertEqual(mocked_get_first.call_count, 1)
        mocked_get_first.assert_called_with(self.mocked_request)

        self.assertEqual(mocked_check_document.call_count, 1)
        mocked_check_document.assert_called_with(self.mocked_request, self.document_mock, 'body')

        self.assertEqual(mocked_update_document_url.call_count, 1)
        mocked_update_document_url.assert_called_with(
            self.mocked_request,
            self.document_mock,
            'document_route',
            {}
        )

        self.assertEqual(mocked_get_type.call_count, 1)
        mocked_get_type.assert_called_with(self.mocked_request.context)

        self.assertEqual(mocked_set_first_document_fields.call_count, 0)

        self.assertEqual(self.document_mock.documentOf, 'resourceName')

        self.assertIs(self.mocked_request.validated['document'], self.document_mock_with_updated_url)


class ValidateAccreditationsTest(unittest.TestCase):

    def test_ok(self):
        request = Mock()
        model = Mock()

        model.create_accreditation = '3'
        request.check_accreditation.return_value = True

        validate_accreditations(request, model)

        assert request.check_accreditation.call_count == 1

    @patch('openprocurement.api.validation.error_handler')
    def test_raises_exception(self, handler):
        request = Mock()
        model = Mock()
        handler.side_effect = DummyException

        model.create_accreditation = '5'

        request.check_accreditation.return_value = False

        with self.assertRaises(DummyException):
            validate_accreditations(request, model)

        assert request.check_accreditation.call_count == 1
        assert request.errors.status == 403


class ValidateTAccreditationTest(unittest.TestCase):

    def test_user_without_t_accreditation(self):
        request = Mock()
        data = Mock()

        data.get.return_value = None
        # user has not 't' accreditation
        request.check_accreditation.return_value = False

        validate_t_accreditation(request, data)

        assert request.check_accreditation.call_count == 1

    @patch('openprocurement.api.validation.error_handler')
    def test_user_with_t_tries_create_non_test_item(self, handler):
        request = Mock()
        data = Mock()
        handler.side_effect = DummyException

        data.get.return_value = None
        # user has 't' accreditation
        request.check_accreditation.return_value = True

        with self.assertRaises(DummyException):
            validate_t_accreditation(request, data)

        assert request.check_accreditation.call_count == 1
        assert request.errors.status == 403


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ValidateDocumentDataTest))
    suite.addTest(unittest.makeSuite(ValidateAccreditationsTest))
    suite.addTest(unittest.makeSuite(ValidateTAccreditationTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
