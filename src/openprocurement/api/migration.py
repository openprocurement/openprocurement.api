# -*- coding: utf-8 -*-
import logging


LOGGER = logging.getLogger(__name__)
SCHEMA_VERSION = 1
SCHEMA_DOC = 'openprocurement_schema'


def get_db_schema_version(db):
    schema_doc = db.get(SCHEMA_DOC, {"_id": SCHEMA_DOC})
    return schema_doc.get("version", 0)


def set_db_schema_version(db, version):
    schema_doc = db.get(SCHEMA_DOC, {"_id": SCHEMA_DOC})
    schema_doc["version"] = version
    db.save(schema_doc)


def migrate_data(db):
    cur_version = get_db_schema_version(db)
    if cur_version == SCHEMA_VERSION:
        return
    for step in xrange(cur_version, SCHEMA_VERSION):
        LOGGER.info("Migrate openprocurement schema from {} to {}".format(step, step + 1))
        migration_func = globals().get('from{}to{}'.format(step, step + 1))
        if migration_func:
            migration_func(db)
        set_db_schema_version(db, step + 1)


def from0to1(db):
    results = db.view('tenders/all', include_docs=True)
    for i in results:
        doc = i.doc
        if 'modifiedAt' in doc and 'modified' not in doc:
            doc['modified'] = doc.pop('modifiedAt')
            db.save(doc)
