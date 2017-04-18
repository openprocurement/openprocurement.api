# -*- coding: utf-8 -*-
from couchdb.design import ViewDefinition


FIELDS = [
    'auctionPeriod',
    'status',
    'tenderID',
    'lots',
    'procurementMethodType',
    'next_check',
    #'auctionUrl',
    #'awardPeriod',
    #'dateModified',
    #'description',
    #'description_en',
    #'description_ru',
    #'enquiryPeriod',
    #'minimalStep',
    #'mode',
    #'procuringEntity',
    #'tenderPeriod',
    #'title',
    #'title_en',
    #'title_ru',
    #'value',
]
CHANGES_FIELDS = FIELDS + [
    'dateModified',
]


def add_index_options(doc):
    doc['options'] = {'local_seq': True}


tenders_all_view = ViewDefinition('tenders', 'all', '''function(doc) {
    if(doc.doc_type == 'Tender') {
        emit(doc.tenderID, null);
    }
}''')


tenders_by_dateModified_view = ViewDefinition('tenders', 'by_dateModified', '''function(doc) {
    if(doc.doc_type == 'Tender' && doc.status != 'draft') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc.dateModified, data);
    }
}''' % FIELDS)

tenders_real_by_dateModified_view = ViewDefinition('tenders', 'real_by_dateModified', '''function(doc) {
    if(doc.doc_type == 'Tender' && doc.status != 'draft' && !doc.mode) {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc.dateModified, data);
    }
}''' % FIELDS)

tenders_test_by_dateModified_view = ViewDefinition('tenders', 'test_by_dateModified', '''function(doc) {
    if(doc.doc_type == 'Tender' && doc.status != 'draft' && doc.mode == 'test') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc.dateModified, data);
    }
}''' % FIELDS)

tenders_by_local_seq_view = ViewDefinition('tenders', 'by_local_seq', '''function(doc) {
    if(doc.doc_type == 'Tender' && doc.status != 'draft') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc._local_seq, data);
    }
}''' % CHANGES_FIELDS)

tenders_real_by_local_seq_view = ViewDefinition('tenders', 'real_by_local_seq', '''function(doc) {
    if(doc.doc_type == 'Tender' && doc.status != 'draft' && !doc.mode) {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc._local_seq, data);
    }
}''' % CHANGES_FIELDS)

tenders_test_by_local_seq_view = ViewDefinition('tenders', 'test_by_local_seq', '''function(doc) {
    if(doc.doc_type == 'Tender' && doc.status != 'draft' && doc.mode == 'test') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc._local_seq, data);
    }
}''' % CHANGES_FIELDS)

conflicts_view = ViewDefinition('conflicts', 'all', '''function(doc) {
    if (doc._conflicts) {
        emit(doc._rev, [doc._rev].concat(doc._conflicts));
    }
}''')


design_list = [tenders_all_view, tenders_by_dateModified_view, tenders_real_by_dateModified_view,
               tenders_test_by_dateModified_view, tenders_by_local_seq_view,
               tenders_real_by_local_seq_view, tenders_test_by_local_seq_view,
               conflicts_view]


def sync_design(db):
    ViewDefinition.sync_many(db, design_list, callback=add_index_options)
