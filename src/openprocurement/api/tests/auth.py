# -*- coding: utf-8 -*-
import unittest

from mock import Mock, patch
from pyramid import testing
from pyramid.tests.test_authentication import TestBasicAuthAuthenticationPolicy

from openprocurement.api.auth import (
    AuthenticationPolicy,
    check_accreditation,
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
        user = {'chrisr': {'group': 'tests', 'name': 'chrisr', 'level': '1234'}}
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


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AuthTest))
    suite.addTest(unittest.makeSuite(CheckAccreditationTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
