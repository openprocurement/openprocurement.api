# -*- coding: utf-8 -*-
import unittest

from openprocurement.api.utils import VERSION
from openprocurement.api.tests.base import BaseWebTest
from json import dumps


class ArchiveBoxTest(BaseWebTest):

    def test_config_archive_box(self):
        box = self.app.app.registry.archive_box
        message = "message to encrypt"
        message = dumps(message)
        encrypted_data = box.encrypt(message)
        decrypted_data = box.decrypt(encrypted_data)
        self.assertNotEqual(message, encrypted_data)
        self.assertEqual(message, decrypted_data)

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ArchiveBoxTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
