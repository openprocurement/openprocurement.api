# -*- coding: utf-8 -*-
import unittest

from openprocurement.api.utils.searchers import (
    path_to_kv,
    search_list_with_dicts,
)


class PathToKvTestCase(unittest.TestCase):

    def setUp(self):
        self.testdict = {
            'forest': {
                'tree1': {
                    'leaf1': 'green',
                    'leaf2': 'brown'
                },
                'tree2': {
                    'leaf1': 'green',
                    'leaf2': 'brown',
                    'leaf3': 'green-brown'
                }
            }
        }

    def test_search_single_result(self):
        kv = ('leaf3', 'green-brown')
        target_r = (
            ('forest', 'tree2', 'leaf3'),
        )

        r = path_to_kv(kv, self.testdict)

        self.assertEqual(r, target_r)

    def test_search_multiple_results(self):
        kv = ('leaf1', 'green')
        target_r = (
            ('forest', 'tree1', 'leaf1'),
            ('forest', 'tree2', 'leaf1'),
        )

        r = path_to_kv(kv, self.testdict)

        self.assertEqual(r, target_r)

    def test_no_results(self):
        kv = ('root', 'no')
        target_r = None

        r = path_to_kv(kv, self.testdict)

        self.assertEqual(r, target_r)


class SearchListWithDictsTestCase(unittest.TestCase):

    def setUp(self):
        self.container = (
            {
                'login': 'user1',
                'password': 'qwerty123',
            },
            {
                'login': 'user2',
                'password': 'abcd321',
                'other': 'I am User',
            }
        )

    def test_successful_search(self):
        result = search_list_with_dicts(self.container, 'login', 'user2')
        assert result['other'] == 'I am User'

    def test_unsuccessful_search(self):
        result = search_list_with_dicts(self.container, 'login', 'user3')
        assert result is None
