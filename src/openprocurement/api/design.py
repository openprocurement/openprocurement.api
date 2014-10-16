from couchdb.design import ViewDefinition

tenders_all_view = ViewDefinition('tenders', 'all', '''function(doc) {
    if(doc.doc_type == 'TenderDocument') {
        emit(doc.tenderID, doc);
    }
}''')
