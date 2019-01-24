# -*- coding: utf-8 -*-
import unittest

from openprocurement.api.utils.decorators import (
    call_before,
)


class CallBeforeTestCase(unittest.TestCase):

    class SomeClass(object):
        def __init__(self):
            self.run_first = False

        def want_run_first(self, *args, **kwargs):
            self.run_first = True

        @call_before(want_run_first)
        def some_method(self, param1, param2=None):
            pass

    def setUp(self):
        self.scarecrow = self.SomeClass()

    def test_ok(self):
        self.scarecrow.some_method('some_param', param2='i_am_here')
        self.assertTrue(self.scarecrow.run_first)
