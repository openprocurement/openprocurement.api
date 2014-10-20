# -*- coding: utf-8 -*-

def migrate_data(db):
    results = db.view('tenders/all', include_docs=True)
    for i in results:
        doc = i.doc
        if 'modifiedAt' in doc and 'modified' not in doc:
            doc['modified'] = doc.pop('modifiedAt')
            db.save(doc)
