# -*- coding: utf-8 -*-
from uuid import uuid4
from openprocurement.api.tests.base import BaseWebTest
from mock import Mock, MagicMock
from couchdb import Server as CouchdbServer
from copy import copy

REPLICATION = {
    "pid": "<0.17282.20>",
    "checkpoint_interval": 5000,
    "checkpointed_source_seq": 0,
    "continuous": True,
    "doc_id": "de1a666d189db087bcd6151d2c0014a2",
    "doc_write_failures": 0,
    "docs_read": 231078,
    "docs_written": 231078,
    "missing_revisions_found": 231076,
    "progress": 100,
    "replication_id":"c54108a5a3c6f23208936eb961611021+continuous+create_target",
    "revisions_checked": 1000,
    "source":"http://op_db_reader:*****@source/openprocurement/",
    "source_seq": 1000,
    "started_on": 1476261621,
    "target": "http://target:*****@target/openprocurement/",
    "type": "replication",
    "updated_on":1476366001
}

REPLICATION_OK = copy(REPLICATION)
REPLICATION_OK['replication_id'] = "54c8d937582043c3ae0ed58f254ac875+continuous+create_target"
REPLICATION_OK['checkpointed_source_seq'] = REPLICATION_OK['source_seq']
REPLICATION_OK_2 = copy(REPLICATION_OK)
REPLICATION_OK_2['replication_id'] = "1e5df0b70431430499147a72cff7fed6+continuous+create_target"


class HealthTestBase(BaseWebTest):

    return_value = []

    def setUp(self):
        self.db_name += uuid4().hex
        # self.couchdb_server.create(self.db_name)
        couchdb_server = Mock(spec=CouchdbServer)
        couchdb_server.tasks = MagicMock(return_value=self.return_value)
        self.app.app.registry.couchdb_server = couchdb_server
        self.db_name = self.db.name

    def test_health_view(self):
        response = self.app.get('/health', status=503)
        self.assertEqual(response.status, '503 Service Unavailable')

        response = self.app.get('/health?health_threshold_func=all', status=503)
        self.assertEqual(response.status, '503 Service Unavailable')

        response = self.app.get('/health?health_threshold_func=any', status=503)
        self.assertEqual(response.status, '503 Service Unavailable')


class HealthTest503(HealthTestBase):
    return_value = [REPLICATION]

    def test_health_view(self):
        response = self.app.get('/health?health_threshold=10000', status=200)
        self.assertEqual(response.status, '200 OK')


class HealthTest200(HealthTestBase):
    return_value = [REPLICATION_OK]

    def test_health_view(self):
        response = self.app.get('/health', status=200)
        self.assertEqual(response.status, '200 OK')

        response = self.app.get('/health?health_threshold_func=all', status=200)
        self.assertEqual(response.status, '200 OK')

        response = self.app.get('/health?health_threshold_func=any', status=200)
        self.assertEqual(response.status, '200 OK')


class HealthTest_all(HealthTestBase):
    return_value = [REPLICATION_OK, REPLICATION_OK_2]

    def test_health_view(self):
        response = self.app.get('/health', status=200)
        self.assertEqual(response.status, '200 OK')

        response = self.app.get('/health?health_threshold_func=all', status=200)
        self.assertEqual(response.status, '200 OK')


class HealthTest_any(HealthTestBase):
    return_value = [REPLICATION_OK, REPLICATION]

    def test_health_view(self):
        response = self.app.get('/health?health_threshold_func=any', status=200)
        self.assertEqual(response.status, '200 OK')
