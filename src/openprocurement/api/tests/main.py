# -*- coding: utf-8 -*-

import unittest

from openprocurement.api.tests import auth, spore, migration, models, utils
from openprocurement.api.tests.dummy_resource import test

def suite():
    suite = unittest.TestSuite()
    suite.addTest(auth.suite())
    suite.addTest(spore.suite())
    suite.addTest(migration.suite())
    tests.addTest(models.suite())
    tests.addTest(utils.suite())
    tests.addTest(test.suite())
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
