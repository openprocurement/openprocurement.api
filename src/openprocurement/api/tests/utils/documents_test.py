# -*- coding: utf-8 -*-
import mock
import unittest

from libnacl.sign import Signer

from openprocurement.api.utils.documents import (
    generate_docservice_url,
)


class DocumentUtilsTestCase(unittest.TestCase):

    def test_generate_docservice_url(self):
        request = mock.MagicMock()
        request.registry = mock.MagicMock()
        request.registry.docservice_key = Signer('1234567890abcdef1234567890abcdef')
        request.registry.docservice_url = 'url'

        expected_result = (
                '/get/1234567890abcdef1234567890abcdef?KeyID='
                'c6c4f29c&Signature=t8L5VW%252BK5vvDwMsxHBhzs%'
                '252BcBXFsYAZ%2FM9WJmzgYLVpc8HC9mPbQhsshgGK94Xa'
                'CtvKFTb9IiTLlW59TM9mV7Bg%253D%253D'
        )
        result = generate_docservice_url(request, '1234567890abcdef1234567890abcdef', False)
        self.assertEqual(result, expected_result)

        expected_result = [
            '/get/1234567890abcdef1234567890abcdef?Prefix=test_prefix',
            '&KeyID=c6c4f29c&Signature=',
            '&Expires='
        ]
        result = generate_docservice_url(request, '1234567890abcdef1234567890abcdef', True, 'test_prefix')
        for item in expected_result:
            self.assertIn(item, result)
