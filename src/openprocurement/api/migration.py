# -*- coding: utf-8 -*-
import logging


LOGGER = logging.getLogger(__name__)
SCHEMA_VERSION = 5
SCHEMA_DOC = 'openprocurement_schema'


def get_db_schema_version(db):
    schema_doc = db.get(SCHEMA_DOC, {"_id": SCHEMA_DOC})
    return schema_doc.get("version", 0)


def set_db_schema_version(db, version):
    schema_doc = db.get(SCHEMA_DOC, {"_id": SCHEMA_DOC})
    schema_doc["version"] = version
    db.save(schema_doc)


def migrate_data(db, destination=None):
    cur_version = get_db_schema_version(db)
    if cur_version == SCHEMA_VERSION:
        return
    for step in xrange(cur_version, destination or SCHEMA_VERSION):
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


def from1to2(db):
    results = db.view('tenders/all', include_docs=True)
    for i in results:
        doc = i.doc
        if 'bidders' in doc or 'procuringEntity' in doc:
            if 'procuringEntity' in doc and 'address' in doc['procuringEntity']:
                address = doc['procuringEntity']['address']
                if 'country-name' in address:
                    address['countryName'] = address.pop('country-name')
                if 'street-address' in address:
                    address['streetAddress'] = address.pop('street-address')
                if 'postal-code' in address:
                    address['postalCode'] = address.pop('postal-code')
            if 'bidders' in doc:
                for bidder in doc['bidders']:
                    if 'address' in bidder:
                        address = bidder['address']
                        if 'country-name' in address:
                            address['countryName'] = address.pop('country-name')
                        if 'street-address' in address:
                            address['streetAddress'] = address.pop('street-address')
                        if 'postal-code' in address:
                            address['postalCode'] = address.pop('postal-code')
            db.save(doc)


def from2to3(db):
    results = db.view('tenders/all', include_docs=True)
    for i in results:
        doc = i.doc
        if 'bidders' in doc:
            bids = []
            for bidder in doc['bidders']:
                uuid = bidder.pop('_id')
                bids.append({'id': uuid, 'bidders': [bidder]})
            del doc['bidders']
            doc['bids'] = bids
            db.save(doc)


def from3to4(db):
    results = db.view('tenders/all', include_docs=True)
    for i in results:
        doc = i.doc
        if 'itemsToBeProcured' in doc:
            items = []
            for item in doc['itemsToBeProcured']:
                classificationScheme = item.pop('classificationScheme')
                otherClassificationScheme = item.pop('otherClassificationScheme')
                item['primaryClassification'] = {
                    "scheme": otherClassificationScheme if classificationScheme == 'Other' else classificationScheme,
                    "id": item.pop('classificationID'),
                    "description": item.pop('classificationDescription')
                }
                items.append(item)
            doc['itemsToBeProcured'] = items
            db.save(doc)


def from4to5(db):
    results = db.view('tenders/all', include_docs=True)
    for i in results:
        doc = i.doc
        changed = False
        if 'clarificationPeriod' in doc:
            doc['enquiryPeriod'] = doc.pop('clarificationPeriod')
            changed = True
        if 'clarifications' in doc:
            doc['hasEnquiries'] = doc.pop('clarifications')
            changed = True
        if changed:
            db.save(doc)
