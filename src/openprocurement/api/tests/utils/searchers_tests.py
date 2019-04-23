# -*- coding: utf-8 -*-
import unittest

from openprocurement.api.utils.searchers import (
    path_to_kv,
    paths_to_key,
    search_list_with_dicts,
    search_root_model,
    traverse_nested_dicts,
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
        self.assertEqual(result['other'], 'I am User')

    def test_unsuccessful_search(self):
        result = search_list_with_dicts(self.container, 'login', 'user3')
        self.assertIsNone(result)


class TraverseNestedDictsTestCase(unittest.TestCase):

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
                    'leaf3': {
                        'bug1': 'wing1'
                    }
                }
            }
        }

    def test_ok(self):
        path = ('forest', 'tree2', 'leaf3', 'bug1')
        res = traverse_nested_dicts(self.testdict, path)
        self.assertEqual(res, 'wing1')


class PathsToKeyTestCase(unittest.TestCase):

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
        target_key = 'leaf3'
        target_r = (
            ('forest', 'tree2', 'leaf3'),
        )

        r = paths_to_key(target_key, self.testdict)

        self.assertEqual(r, target_r)

    def test_search_multiple_results(self):
        key = 'leaf2'
        target_r = (
            ('forest', 'tree1', 'leaf2'),
            ('forest', 'tree2', 'leaf2'),
        )

        r = paths_to_key(key, self.testdict)

        self.assertEqual(r, target_r)

    def test_no_results(self):
        key = 'neverland'
        target_r = None

        r = paths_to_key(key, self.testdict)

        self.assertEqual(r, target_r)


class SearchRootModelTestCase(unittest.TestCase):

    class Node(object):

        def __init__(self, name, parent):
            self.name = name
            self.__parent__ = parent

        def __repr__(self):
            return "{0} {1}".format(self.__class__.__name__, self.name)

    def setUp(self):
        self.root = self.Node('root', None)
        self.auction = self.Node('auction', self.root)
        self.award = self.Node('award', self.auction)

    def test_ok(self):
        res = search_root_model(self.award)
        self.assertEqual(res, self.auction)

    def test_search_starts_on_roots_child(self):
        res = search_root_model(self.auction)
        self.assertEqual(res, self.auction)
