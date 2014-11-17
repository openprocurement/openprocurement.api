# -*- coding: utf-8 -*-
from couchdb.design import ViewDefinition


def sync_design(db):
    views = [j for i, j in globals().items() if "view" in i]
    for view in views:
        view.sync(db)


tenders_all_view = ViewDefinition('tenders', 'all', '''function(doc) {
    if(doc.doc_type == 'TenderDocument') {
        emit(doc.tenderID, doc);
    }
}''')


tenders_by_dateModified_view = ViewDefinition('tenders', 'by_dateModified', '''function(doc) {
    if(doc.doc_type == 'TenderDocument') {
        emit(doc.dateModified, {'dateModified': doc.dateModified});
    }
}''')
