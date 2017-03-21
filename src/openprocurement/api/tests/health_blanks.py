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
REPLICATION_OK['checkpointed_source_seq'] = REPLICATION_OK['source_seq']


def health_view_503(self):
    response = self.app.get('/health', status=503)
    self.assertEqual(response.status, '503 Service Unavailable')

    response = self.app.get('/health?health_threshold_func=all', status=503)
    self.assertEqual(response.status, '503 Service Unavailable')

    response = self.app.get('/health?health_threshold_func=any', status=503)
    self.assertEqual(response.status, '503 Service Unavailable')


def health_view_threshold(self):
    response = self.app.get('/health?health_threshold=10000', status=200)
    self.assertEqual(response.status, '200 OK')


def health_view_200(self):
    response = self.app.get('/health', status=200)
    self.assertEqual(response.status, '200 OK')

    response = self.app.get('/health?health_threshold_func=all', status=200)
    self.assertEqual(response.status, '200 OK')

    response = self.app.get('/health?health_threshold_func=any', status=200)
    self.assertEqual(response.status, '200 OK')


def health_all(self):
    response = self.app.get('/health', status=200)
    self.assertEqual(response.status, '200 OK')

    response = self.app.get('/health?health_threshold_func=all', status=200)
    self.assertEqual(response.status, '200 OK')


def health_any(self):
    response = self.app.get('/health?health_threshold_func=any', status=200)
    self.assertEqual(response.status, '200 OK')
