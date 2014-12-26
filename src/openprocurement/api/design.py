# -*- coding: utf-8 -*-
from couchdb.design import ViewDefinition


def sync_design(db):
    views = [j for i, j in globals().items() if "_view" in i]
    for view in views:
        view.sync(db)


tenders_all_view = ViewDefinition('tenders', 'all', '''function(doc) {
    if(doc.doc_type == 'Tender') {
        emit(doc.tenderID, null);
    }
}''')


tenders_by_dateModified_view = ViewDefinition('tenders', 'by_dateModified', '''function(doc) {
    if(doc.doc_type == 'Tender') {
        emit(doc.dateModified, null);
    }
}''')

tenders_by_dateModified_active_view = ViewDefinition('tenders', 'by_dateModified_active', '''function(doc) {
    if(doc.doc_type == 'Tender' && doc.status.substring(0, 7) === 'active.') {
        emit(doc.dateModified, null);
    }
}''')
