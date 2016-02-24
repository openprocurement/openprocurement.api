# -*- coding: utf-8 -*-

from openprocurement.api.tests.base import BaseWebTest


class HealthTest(BaseWebTest):

    def test_health_view(self):
        response = self.app.get('/health', status=503)
        self.assertEqual(response.status, '503 Service Unavailable')
