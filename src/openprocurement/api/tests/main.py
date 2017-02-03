# -*- coding: utf-8 -*-

import unittest

from openprocurement.api.tests import auth, spore


def suite():
    suite = unittest.TestSuite()
    suite.addTest(auth.suite())
    suite.addTest(spore.suite())
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
