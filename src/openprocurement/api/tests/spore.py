# -*- coding: utf-8 -*-
import unittest

from openprocurement.api.tests.base import BaseWebTest


class SporeTest(BaseWebTest):

    def test_spore(self):
        response = self.app.get('/spore')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SporeTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
