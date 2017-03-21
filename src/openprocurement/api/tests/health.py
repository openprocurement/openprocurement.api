# -*- coding: utf-8 -*-
from uuid import uuid4
from openprocurement.api.tests.base import BaseWebTest
from mock import Mock, MagicMock
from couchdb import Server as CouchdbServer
from openprocurement.api.tests.base import snitch
from openprocurement.api.tests.health_blanks import (
    health_view_503, health_view_threshold, health_view_200,
    health_all, health_any, REPLICATION, REPLICATION_OK
)


class HealthTestBase(object):

    return_value = []

    def setUp(self):
        self.db_name += uuid4().hex
        # self.couchdb_server.create(self.db_name)
        couchdb_server = Mock(spec=CouchdbServer)
        couchdb_server.tasks = MagicMock(return_value=self.return_value)
        self.app.app.registry.couchdb_server = couchdb_server
        self.db_name = self.db.name
        self.app.authorization = ('Basic', ('token', ''))


class HealthTest(HealthTestBase, BaseWebTest):
    return_value = []

    test_health_view_503 = snitch(health_view_503)

class HealthTest503(HealthTestBase, BaseWebTest):
    return_value = [REPLICATION]

    test_health_view_threshold = snitch(health_view_threshold)


class HealthTest200(HealthTestBase, BaseWebTest):
    return_value = [REPLICATION_OK]

    test_health_view_200 = snitch(health_view_200)


class HealthTest_all(HealthTestBase, BaseWebTest):
    return_value = [REPLICATION_OK, REPLICATION_OK]

    test_health_all = snitch(health_all)


class HealthTest_any(HealthTestBase, BaseWebTest):
    return_value = [REPLICATION_OK, REPLICATION]

    test_health_any = snitch(health_any)
