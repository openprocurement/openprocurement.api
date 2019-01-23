# -*- coding: utf-8 -*-
from pytz import utc
from openprocurement.api.utils.common import get_now
from openprocurement.api.constants import DB_STATE_DOC_DEFAULT_NAME
from openprocurement.api.models.common import DBState, MigrationInfo


class DBStateDocManager(object):
    """Operates on `db state` document"""

    def __init__(self, db, doc_name=DB_STATE_DOC_DEFAULT_NAME):
        self._db = db
        self._docname = doc_name

    def _create_doc(self):
        """Write basic DBState document to the DB"""

        time_to_db = get_now().astimezone(utc)

        doc = DBState({
            '_id': self._docname,
            'db_created': time_to_db,
        })
        doc.store(self._db)

        return doc

    def assure_doc(self):
        """Check if db state doc is present and create it if it isn't"""

        doc_present = DBState.load(self._db, self._docname)
        if not doc_present:
            return self._create_doc()

    def write_migration_info(self, name, description, applied):
        """Write migration info to the database"""

        # I decided to do this check mandatory to make use of this manager easy as possible
        self.assure_doc()

        migration_info = MigrationInfo({
            'name': name,
            'description': description,
            'applied': applied
        })
        migration_info.validate()
        migration_info = migration_info.to_primitive()

        db_state_doc = DBState.load(self._db, self._docname)
        db_state_doc['migrations'].append(migration_info)

        db_state_doc.store(self._db)
