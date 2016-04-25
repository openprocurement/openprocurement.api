# -*- coding: utf-8 -*-
import unittest
from pyramid import testing
from openprocurement.api.auth import AuthenticationPolicy
from pyramid.tests.test_authentication import TestBasicAuthAuthenticationPolicy
from openprocurement.api.tests.base import test_tender_data, test_organization, BaseWebTest, BaseTenderWebTest


class AuthTest(TestBasicAuthAuthenticationPolicy):
    def _makeOne(self, check):
        return AuthenticationPolicy('src/openprocurement/api/tests/auth.ini', 'SomeRealm')

    test_authenticated_userid_utf8 = None
    test_authenticated_userid_latin1 = None

    def test_unauthenticated_userid_bearer(self):
        request = testing.DummyRequest()
        request.headers['Authorization'] = 'Bearer chrisr'
        policy = self._makeOne(None)
        self.assertEqual(policy.unauthenticated_userid(request), 'chrisr')


class AccreditationTenderTest(BaseWebTest):
    def test_create_tender_accreditation(self):
        self.app.authorization = ('Basic', ('broker1', ''))
        response = self.app.post_json('/tenders', {"data": test_tender_data})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')

        for broker in ['broker2', 'broker3', 'broker4']:
            self.app.authorization = ('Basic', (broker, ''))
            response = self.app.post_json('/tenders', {"data": test_tender_data}, status=403)
            self.assertEqual(response.status, '403 Forbidden')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.json['errors'][0]["description"], "Broker Accreditation level does not permit tender creation")


class AccreditationTenderQuestionTest(BaseTenderWebTest):
    def test_create_tender_question_accreditation(self):
        self.app.authorization = ('Basic', ('broker2', ''))
        response = self.app.post_json('/tenders/{}/questions'.format(self.tender_id),
                                      {'data': {'title': 'question title', 'description': 'question description', 'author': test_organization}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')

        for broker in ['broker1', 'broker3', 'broker4']:
            self.app.authorization = ('Basic', (broker, ''))
            response = self.app.post_json('/tenders/{}/questions'.format(self.tender_id),
                                          {'data': {'title': 'question title', 'description': 'question description', 'author': test_organization}},
                                          status=403)
            self.assertEqual(response.status, '403 Forbidden')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.json['errors'][0]["description"], "Broker Accreditation level does not permit question creation")


class AccreditationTenderBidTest(BaseTenderWebTest):
    initial_status = 'active.tendering'

    def test_create_tender_bid_accreditation(self):
        self.app.authorization = ('Basic', ('broker2', ''))
        response = self.app.post_json('/tenders/{}/bids'.format(self.tender_id),
                                      {'data': {'tenderers': [test_organization], "value": {"amount": 500}}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')

        for broker in ['broker1', 'broker3', 'broker4']:
            self.app.authorization = ('Basic', (broker, ''))
            response = self.app.post_json('/tenders/{}/bids'.format(self.tender_id),
                                          {'data': {'tenderers': [test_organization], "value": {"amount": 500}}},
                                          status=403)
            self.assertEqual(response.status, '403 Forbidden')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.json['errors'][0]["description"], "Broker Accreditation level does not permit bid creation")



def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AuthTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
