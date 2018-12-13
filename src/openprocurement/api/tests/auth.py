# -*- coding: utf-8 -*-
import unittest

from mock import Mock, patch, mock_open, MagicMock
from pyramid import testing
from pyramid.tests.test_authentication import TestBasicAuthAuthenticationPolicy

from openprocurement.api.auth import (
    AuthenticationPolicy,
    check_accreditation,
    create_users_from_group,
    create_users_from_group_ini,
    create_user_structure,
    _ini_auth,
    _yaml_auth,
    _json_auth
)
from openprocurement.api.constants import (
    ALL_ACCREDITATIONS_GRANTED,
    TEST_ACCREDITATION,
)


@patch('openprocurement.api.auth.get_auth')
def get_mock_auth(return_value, mock_get_auth):
    mock_get_auth.return_value = return_value
    return mock_get_auth


class AuthTest(TestBasicAuthAuthenticationPolicy):

    def _makeOne(self, check):
        user = {'chrisr': {'group': 'tests', 'name': 'chrisr', 'level': ['1', '2', '3', '4']}}
        get_auth = get_mock_auth(user)
        return AuthenticationPolicy(get_auth(), 'SomeRealm')

    test_authenticated_userid_utf8 = None
    test_authenticated_userid_latin1 = None

    def test_unauthenticated_userid_bearer(self):
        request = testing.DummyRequest()
        request.headers['Authorization'] = 'Bearer chrisr'
        policy = self._makeOne(None)
        self.assertEqual(policy.unauthenticated_userid(request), 'chrisr')


class CheckAccreditationTest(unittest.TestCase):

    def test_user_has_accreditation(self):
        request = Mock()
        request.effective_principals = ['a:1', 'a:2']
        level = '1'

        result = check_accreditation(request, level)

        assert result

    def test_user_has_all_accreditations(self):
        request = Mock()
        request.effective_principals = [
            'a:3',
            'a:{0}'.format(ALL_ACCREDITATIONS_GRANTED),
        ]
        level = '9'

        result = check_accreditation(request, level)

        assert result

    def test_user_has_test_accreditation(self):
        request = Mock()
        request.effective_principals = [
            'a:{0}'.format(TEST_ACCREDITATION),
        ]
        level = TEST_ACCREDITATION

        result = check_accreditation(request, level)

        assert result


class TestCreateUserStructure(unittest.TestCase):

    def test_create_user_structure(self):
        group = 'group_name'
        name = 'user_name'
        info = {
            'token': 'acc_token',
            'levels': ['1', '3']
        }
        expected_result = {
            info['token']: {
                'group': group,
                'name': name,
                'level': info['levels']
            }
        }

        result = create_user_structure(group, name, info)
        self.assertEqual(expected_result, result)

    def test_create_user_structure_without_levels(self):
        group = 'group_name'
        name = 'user_name'
        info = {
            'token': 'acc_token',
        }
        expected_result = {
            info['token']: {
                'group': group,
                'name': name,
                'level': ['0']
            }
        }

        result = create_user_structure(group, name, info)
        self.assertEqual(expected_result, result)


class TestCreateUsersFromGroup(unittest.TestCase):

    def test_create_users(self):

        group = 'some_group'
        user_1 = {
            'token': 'token1'
        }
        user_2 = {
            'token': 'token2',
            'levels': ['3']
        }
        users_info = [('name1', user_1), ('name2', user_2)]

        expected_result = {
            'token1': {
                'name': 'name1',
                'level': ['0'],
                'group': group

            },
            'token2': {
                'name': 'name2',
                'level': ['3'],
                'group': group
            }
        }

        users = create_users_from_group(group, users_info)

        self.assertEqual(users, expected_result)


class TestCreateUsersFromGroupIni(unittest.TestCase):

    def test_create_users_from_ini(self):

        group = 'some_group'
        users_info = [('name1', 'token1'), ('name2', 'token2,3')]

        expected_result = {
            'token1': {
                'name': 'name1',
                'level': ['0'],
                'group': group

            },
            'token2': {
                'name': 'name2',
                'level': ['3'],
                'group': group
            }
        }

        users = create_users_from_group_ini(group, users_info)

        self.assertEqual(users, expected_result)


class TestIniTypeLoader(unittest.TestCase):

    def setUp(self):
        self.path = 'some_path'
        self.app_meta = {'app': 'meta'}

        self.patch_get_path = patch('openprocurement.api.auth.get_path_to_auth')
        self.mock_get_path = self.patch_get_path.start()
        self.mock_get_path.return_value = self.path

        self.patch_parser = patch('openprocurement.api.auth.ConfigParser')
        self.mock_config_parser_class = self.patch_parser.start()

        self.mock_parser = MagicMock()

        self.mock_config_parser_class.return_value = self.mock_parser

        self.patch_create_users_ini = patch('openprocurement.api.auth.create_users_from_group_ini')
        self.mock_create_users_ini = self.patch_create_users_ini.start()

        self.patch_logger = patch('openprocurement.api.auth.LOGGER')
        self.mock_logger = self.patch_logger.start()

    def tearDown(self):
        self.patch_get_path.stop()
        self.patch_parser.stop()
        self.patch_create_users_ini.stop()
        self.patch_logger.stop()

    def test_empty_config(self):
        self.mock_parser.sections.return_value = []

        result = _ini_auth(self.app_meta)
        self.assertEqual(result, {})

        self.assertEqual(self.mock_get_path.call_count, 1)
        self.mock_get_path.assert_called_with(self.app_meta)

        self.assertEqual(self.mock_config_parser_class.call_count, 1)

        self.assertEqual(self.mock_parser.read.call_count, 1)
        self.mock_parser.read.assert_called_with(self.path)

        self.assertEqual(self.mock_parser.sections.call_count, 2)

        self.mock_logger.warning.assert_called_with(
            "Auth file '%s' was empty, no user will be added", self.path
        )

        self.assertEqual(self.mock_create_users_ini.call_count, 0)

    def test_ini_type(self):
        config_sections = ['some', 'sections']
        config_items = ['some', 'items']

        self.mock_parser.sections.return_value = config_sections
        self.mock_parser.items.return_value = config_items

        users_info = [
            {'first': 'users'},
            {'second': 'users'}
        ]
        self.mock_create_users_ini.side_effect = iter(users_info)

        expected_result = {}

        for info in users_info:
            expected_result.update(info)

        result = _ini_auth(self.app_meta)
        self.assertEqual(result, expected_result)

        self.assertEqual(self.mock_get_path.call_count, 1)
        self.mock_get_path.assert_called_with(self.app_meta)

        self.assertEqual(self.mock_config_parser_class.call_count, 1)

        self.assertEqual(self.mock_parser.read.call_count, 1)
        self.mock_parser.read.assert_called_with(self.path)

        self.assertEqual(self.mock_parser.sections.call_count, 2)

        self.assertEqual(self.mock_logger.warning.call_count, 0)

        self.assertEqual(self.mock_create_users_ini.call_count, 2)
        self.mock_create_users_ini.assert_called_with(config_sections[-1], config_items)


class TestYamlTypeLoader(unittest.TestCase):

    def setUp(self):
        self.path = 'some_path'
        self.app_meta = {'app': 'meta'}

        self.patch_get_path = patch('openprocurement.api.auth.get_path_to_auth')
        self.mock_get_path = self.patch_get_path.start()
        self.mock_get_path.return_value = self.path

        # Such complex mock for `open` function needed because of using `with` statement
        self.auth_file = MagicMock()  # object that returned by __enter__ part of context manager
        self.enter_mock = MagicMock()  # mock __enter__
        self.enter_mock.return_value = self.auth_file
        self.mock_open_result = MagicMock()  # assign __enter__ to result of open()
        self.mock_open_result.__enter__ = self.enter_mock

        self.patch_open = patch('__builtin__.open', mock_open(read_data=''))
        self.mock_open = self.patch_open.start()
        self.mock_open.return_value = self.mock_open_result

        self.patch_yaml = patch('openprocurement.api.auth.yaml')
        self.mock_yaml = self.patch_yaml.start()

        self.patch_create_users = patch('openprocurement.api.auth.create_users_from_group')
        self.mock_create_users = self.patch_create_users.start()

        self.patch_logger = patch('openprocurement.api.auth.LOGGER')
        self.mock_logger = self.patch_logger.start()

    def tearDown(self):
        self.patch_get_path.stop()
        self.patch_open.stop()
        self.patch_yaml.stop()
        self.patch_create_users.stop()
        self.patch_logger.stop()

    def test_empty_config(self):
        self.mock_yaml.safe_load.return_value = {}

        result = _yaml_auth(self.app_meta)
        self.assertEqual(result, {})

        self.assertEqual(self.mock_get_path.call_count, 1)
        self.mock_get_path.assert_called_with(self.app_meta)

        self.assertEqual(self.mock_open.call_count, 1)
        self.mock_open.assert_called_with(self.path)

        self.assertEqual(self.mock_yaml.safe_load.call_count, 1)
        self.mock_yaml.safe_load.assert_called_with(self.auth_file)

        self.assertEqual(self.mock_logger.warning.call_count, 1)
        self.mock_logger.warning.assert_called_with(
            "Auth file '%s' was empty, no user will be added", self.path
        )
        self.assertEqual(self.mock_create_users.call_count, 0)

    def test_yaml_config(self):
        yaml_dict = {
            'group1': {
                'user1': 'token1'
            },
            'group2': {
                'user2': 'token2'
            }
        }
        self.mock_yaml.safe_load.return_value = yaml_dict

        users_info = [
            {'first': 'users'},
            {'second': 'users'}
        ]

        self.mock_create_users.side_effect = iter(users_info)

        expected_result = {}

        for info in users_info:
            expected_result.update(info)

        result = _yaml_auth(self.app_meta)
        self.assertEqual(result, expected_result)

        self.assertEqual(self.mock_get_path.call_count, 1)
        self.mock_get_path.assert_called_with(self.app_meta)

        self.assertEqual(self.mock_open.call_count, 1)
        self.mock_open.assert_called_with(self.path)

        self.assertEqual(self.mock_yaml.safe_load.call_count, 1)
        self.mock_yaml.safe_load.assert_called_with(self.auth_file)

        self.assertEqual(self.mock_logger.warning.call_count, 0)

        self.assertEqual(self.mock_create_users.call_count, 2)
        self.mock_create_users.assert_called_with('group2', yaml_dict['group2'].items())


class TestJsonTypeLoader(unittest.TestCase):

    def setUp(self):
        self.path = 'some_path'
        self.app_meta = {'app': 'meta'}

        self.patch_get_path = patch('openprocurement.api.auth.get_path_to_auth')
        self.mock_get_path = self.patch_get_path.start()
        self.mock_get_path.return_value = self.path

        # Such complex mock for `open` function needed because of using `with` statement
        self.auth_file = MagicMock()  # object that returned by __enter__ part of context manager
        self.enter_mock = MagicMock()  # mock __enter__
        self.enter_mock.return_value = self.auth_file
        self.mock_open_result = MagicMock()  # assign __enter__ to result of open()
        self.mock_open_result.__enter__ = self.enter_mock

        self.patch_open = patch('__builtin__.open', mock_open(read_data=''))
        self.mock_open = self.patch_open.start()
        self.mock_open.return_value = self.mock_open_result

        self.patch_json = patch('openprocurement.api.auth.json')
        self.mock_json = self.patch_json.start()

        self.patch_create_users = patch('openprocurement.api.auth.create_users_from_group')
        self.mock_create_users = self.patch_create_users.start()

        self.patch_logger = patch('openprocurement.api.auth.LOGGER')
        self.mock_logger = self.patch_logger.start()

    def tearDown(self):
        self.patch_get_path.stop()
        self.patch_open.stop()
        self.patch_json.stop()
        self.patch_create_users.stop()
        self.patch_logger.stop()

    def test_empty_config(self):
        self.mock_json.load.return_value = {}

        result = _json_auth(self.app_meta)
        self.assertEqual(result, {})

        self.assertEqual(self.mock_get_path.call_count, 1)
        self.mock_get_path.assert_called_with(self.app_meta)

        self.assertEqual(self.mock_open.call_count, 1)
        self.mock_open.assert_called_with(self.path)

        self.assertEqual(self.mock_json.load.call_count, 1)
        self.mock_json.load.assert_called_with(self.auth_file)

        self.assertEqual(self.mock_logger.warning.call_count, 1)
        self.mock_logger.warning.assert_called_with(
            "Auth file '%s' was empty, no user will be added", self.path
        )
        self.assertEqual(self.mock_create_users.call_count, 0)

    def test_yaml_config(self):
        yaml_dict = {
            'group1': {
                'user1': 'token1'
            },
            'group2': {
                'user2': 'token2'
            }
        }
        self.mock_json.load.return_value = yaml_dict

        users_info = [
            {'first': 'users'},
            {'second': 'users'}
        ]

        self.mock_create_users.side_effect = iter(users_info)

        expected_result = {}

        for info in users_info:
            expected_result.update(info)

        result = _json_auth(self.app_meta)
        self.assertEqual(result, expected_result)

        self.assertEqual(self.mock_get_path.call_count, 1)
        self.mock_get_path.assert_called_with(self.app_meta)

        self.assertEqual(self.mock_open.call_count, 1)
        self.mock_open.assert_called_with(self.path)

        self.assertEqual(self.mock_json.load.call_count, 1)
        self.mock_json.load.assert_called_with(self.auth_file)

        self.assertEqual(self.mock_logger.warning.call_count, 0)

        self.assertEqual(self.mock_create_users.call_count, 2)
        self.mock_create_users.assert_called_with('group2', yaml_dict['group2'].items())


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AuthTest))
    suite.addTest(unittest.makeSuite(CheckAccreditationTest))
    suite.addTest(unittest.makeSuite(TestCreateUsersFromGroup))
    suite.addTest(unittest.makeSuite(TestCreateUsersFromGroupIni))
    suite.addTest(unittest.makeSuite(TestCreateUserStructure))
    suite.addTest(unittest.makeSuite(TestIniTypeLoader))
    suite.addTest(unittest.makeSuite(TestYamlTypeLoader))
    suite.addTest(unittest.makeSuite(TestJsonTypeLoader))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
