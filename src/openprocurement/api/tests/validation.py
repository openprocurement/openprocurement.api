# -*- coding: utf-8 -*-
import mock
import unittest

from openprocurement.api.validation import validate_document_data


@mock.patch('openprocurement.api.validation.check_document', autospec=True)
@mock.patch('openprocurement.api.validation.set_first_document_fields', autospec=True)
@mock.patch('openprocurement.api.validation.get_first_document', autospec=True)
@mock.patch('openprocurement.api.validation.update_document_url', autospec=True)
@mock.patch('openprocurement.api.validation.validate_data', autospec=True)
@mock.patch('openprocurement.api.validation.get_type', autospec=True)
class ValidateDocumentDataTest(unittest.TestCase):

    def setUp(self):
        self.mocked_request = mock.MagicMock()
        self.document_mock = mock.MagicMock()
        self.document_mock_with_updated_url = mock.MagicMock()
        self.mocked_request.validated = {'document': self.document_mock}
        self.mocked_request.context = mock.MagicMock()
        self.mocked_request.matched_route.name.replace = mock.MagicMock(return_value='document_route')

        self.type_of_context = mock.MagicMock()
        self.model_class = mock.MagicMock()
        self.type_of_context.documents.model_class = self.model_class

    def test_documentOf_in_document(self, mocked_get_type, mocked_validate_data, mocked_update_document_url, mocked_get_first, mocked_set_first_document_fields, mocked_check_document):
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

    def test_documentOf_not_in_document(self, mocked_get_type, mocked_validate_data, mocked_update_document_url, mocked_get_first, mocked_set_first_document_fields, mocked_check_document):
        # Mocking
        self.mocked_request.context.__contains__.return_value = True
        self.document_mock.documentOf = None
        self.type_of_context.__name__ = mock.MagicMock()
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


    def test_first_document(self, mocked_get_type, mocked_validate_data, mocked_update_document_url, mocked_get_first, mocked_set_first_document_fields, mocked_check_document):
        # Mocking
        self.mocked_request.context.__contains__.return_value = True
        self.document_mock.documentOf = 'resourceName'
        first_document = mock.MagicMock()

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

    def test_not_first_document(self, mocked_get_type, mocked_validate_data, mocked_update_document_url, mocked_get_first, mocked_set_first_document_fields, mocked_check_document):
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


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ValidateDocumentDataTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
