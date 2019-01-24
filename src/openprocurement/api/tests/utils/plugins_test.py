# -*- coding: utf-8 -*-
import unittest

from openprocurement.api.exceptions import ConfigAliasError
from openprocurement.api.utils.plugins import (
    format_aliases,
    get_plugin_aliases,
    make_aliases,
)


class FormatAliasesTestCase(unittest.TestCase):

    def test_format_aliases(self):
        result = format_aliases({'auctions.rubble.financial': ['Alias']})
        self.assertEqual(result, "auctions.rubble.financial aliases: ['Alias']")


class GetPluginAliasesTestCase(unittest.TestCase):

    def test_get_plugin_error(self):
        data = {'auctions.rubble.financial': {'aliases': ['One', 'One']}}
        with self.assertRaises(ConfigAliasError):
            get_plugin_aliases(data)


class MakeAliasesTestCase(unittest.TestCase):

    def test_make_alias(self):
        data = {'auctions.rubble.financial': {'aliases': ['One', 'Two']}}
        result = make_aliases(data)
        self.assertEqual(result, [{'auctions.rubble.financial': ['One', 'Two']}])

    def test_make_bad_alias(self):
        result = make_aliases(None)
        self.assertEqual(result, [])
