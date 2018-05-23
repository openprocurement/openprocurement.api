# -*- coding: utf-8 -*-
from couchdb.design import ViewDefinition
from logging import getLogger

LOGGER = getLogger("{}.init".format(__name__))


def add_index_options(doc):
    doc['options'] = {'local_seq': True}


def sync_design(db):
    views = [j for i, j in globals().items() if "_view" in i]
    updated_docs = ViewDefinition.sync_many(
        db, views, callback=add_index_options
    )

    for doc in updated_docs:
        success, doc_id, rev_or_exc = doc
        if success:
            LOGGER.info("Design document '%s' was successfully updated. "
                        "Current revision: %s", doc_id, rev_or_exc,
                        extra={'MESSAGE_ID': 'update_design_document'})
        else:
            LOGGER.warning(
                "Failed to update design document '%s': '%s'", doc_id,
                ('{}: {}'.format(type(rev_or_exc).__name__, rev_or_exc))
            )


conflicts_view = ViewDefinition('conflicts', 'all', '''function(doc) {
    if (doc._conflicts) {
        emit(doc._rev, [doc._rev].concat(doc._conflicts));
    }
}''')
