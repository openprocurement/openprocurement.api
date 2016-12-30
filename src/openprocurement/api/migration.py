# -*- coding: utf-8 -*-
import logging
from datetime import timedelta
from iso8601 import parse_date
from openprocurement.api.models import CPV_CODES, STAND_STILL_TIME, TZ, get_now
from openprocurement.api.traversal import Root
from email.header import decode_header


LOGGER = logging.getLogger(__name__)
SCHEMA_VERSION = 24
SCHEMA_DOC = 'openprocurement_schema'


def get_db_schema_version(db):
    schema_doc = db.get(SCHEMA_DOC, {"_id": SCHEMA_DOC})
    return schema_doc.get("version", SCHEMA_VERSION - 1)


def set_db_schema_version(db, version):
    schema_doc = db.get(SCHEMA_DOC, {"_id": SCHEMA_DOC})
    schema_doc["version"] = version
    db.save(schema_doc)


def migrate_data(registry, destination=None):
    cur_version = get_db_schema_version(registry.db)
    if cur_version == SCHEMA_VERSION:
        return cur_version
    for step in xrange(cur_version, destination or SCHEMA_VERSION):
        LOGGER.info("Migrate openprocurement schema from {} to {}".format(step, step + 1), extra={'MESSAGE_ID': 'migrate_data'})
        migration_func = globals().get('from{}to{}'.format(step, step + 1))
        if migration_func:
            migration_func(registry)
        set_db_schema_version(registry.db, step + 1)


def from0to1(registry):
    results = registry.db.view('tenders/all', include_docs=True)
    for i in results:
        doc = i.doc
        if 'modifiedAt' in doc and 'modified' not in doc:
            doc['modified'] = doc.pop('modifiedAt')
            registry.db.save(doc)


def from1to2(registry):
    results = registry.db.view('tenders/all', include_docs=True)
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
            registry.db.save(doc)


def from2to3(registry):
    results = registry.db.view('tenders/all', include_docs=True)
    for i in results:
        doc = i.doc
        if 'bidders' in doc:
            bids = []
            for bidder in doc['bidders']:
                uuid = bidder.pop('_id')
                bids.append({'id': uuid, 'bidders': [bidder]})
            del doc['bidders']
            doc['bids'] = bids
            registry.db.save(doc)


def from3to4(registry):
    results = registry.db.view('tenders/all', include_docs=True)
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
            registry.db.save(doc)


def from4to5(registry):
    results = registry.db.view('tenders/all', include_docs=True)
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
            registry.db.save(doc)


def from5to6(registry):
    results = registry.db.view('tenders/all', include_docs=True)
    for i in results:
        doc = i.doc
        changed = False
        if 'attachments' in doc:
            items = []
            for i in doc.pop('attachments'):
                items.append({
                    'id': i['id'],
                    'title': i['description'],
                    'modified': i['lastModified'],
                    'datePublished': i['lastModified'],
                    'url': '{}?download={}_{}'.format(i['uri'], len(i.get('revisions', [])), i['description']),
                })
            doc['documents'] = items
            changed = True
        if 'bids' in doc:
            for bid in doc['bids']:
                if 'attachments' in bid:
                    items = []
                    for i in bid.pop('attachments'):
                        items.append({
                            'id': i['id'],
                            'title': i['description'],
                            'modified': i['lastModified'],
                            'datePublished': i['lastModified'],
                            'url': '{}?download={}_{}'.format(i['uri'], len(i.get('revisions', [])), i['description']),
                        })
                    bid['documents'] = items
                    changed = True
        if changed:
            registry.db.save(doc)


def from10to11(registry):
    results = registry.db.view('tenders/all', include_docs=True)
    for i in results:
        doc = i.doc
        changed = False
        if doc.get("procuringEntity", {}).get("identifier", {}).get("scheme"):
            changed = True
            doc["procuringEntity"]["identifier"]["scheme"] = 'UA-EDR'
        for j in doc.get('bids', []):
            for i in j.get('tenderers', []):
                if i.get("identifier", {}).get("scheme"):
                    changed = True
                    i["identifier"]["scheme"] = 'UA-EDR'
        for i in doc.get('questions', []):
            if i.get("author", {}).get("identifier", {}).get("scheme"):
                changed = True
                i["author"]["identifier"]["scheme"] = 'UA-EDR'
        for i in doc.get('complaints', []):
            if i.get("author", {}).get("identifier", {}).get("scheme"):
                changed = True
                i["author"]["identifier"]["scheme"] = 'UA-EDR'
        for j in doc.get('awards', []):
            for i in j.get('suppliers', []):
                if i.get("identifier", {}).get("scheme"):
                    changed = True
                    i["identifier"]["scheme"] = 'UA-EDR'
            for i in j.get('complaints', []):
                if i.get("author", {}).get("identifier", {}).get("scheme"):
                    changed = True
                    i["author"]["identifier"]["scheme"] = 'UA-EDR'
        if changed:
            doc['dateModified'] = get_now().isoformat()
            registry.db.save(doc)


def fix_org(x, changed):
    if "identifier" in x:
        if x["identifier"].get("scheme") != u"UA-EDR":
            changed = True
            x["identifier"]["scheme"] = u'UA-EDR'
        if x["identifier"].get("id") is None:
            changed = True
            x["identifier"]["id"] = u"00000000"
    else:
        changed = True
        x["identifier"] = {
            "scheme": u"UA-EDR",
            "id": u"00000000"
        }
    if "address" in x:
        if "countryName" not in x["address"]:
            changed = True
            x["address"]["countryName"] = u"Україна"
    else:
        changed = True
        x["address"] = {"countryName": u"Україна"}
    if "contactPoint" in x:
        if "name" not in x["contactPoint"]:
            changed = True
            x["contactPoint"]["name"] = x["name"]
        if "email" not in x["contactPoint"] and "telephone" not in x["contactPoint"]:
            changed = True
            x["contactPoint"]["telephone"] = u"0440000000"
    else:
        changed = True
        x["contactPoint"] = {
            "name": x["name"],
            "telephone": u"0440000000"
        }
    return x, changed


def fix_value(item, value, changed):
    if item.get("amount") is None or not (0.0 <= item["amount"] <= value["amount"]):
        changed = True
        item["amount"] = value["amount"]
    if item.get("currency") is None or item["currency"] != value["currency"]:
        changed = True
        item["currency"] = value["currency"]
    if item.get("valueAddedTaxIncluded") is None or item["valueAddedTaxIncluded"] != value["valueAddedTaxIncluded"]:
        changed = True
        item["valueAddedTaxIncluded"] = value["valueAddedTaxIncluded"]
    return item, changed


def from11to12(registry):
    results = registry.db.view('tenders/all', include_docs=True)
    for i in results:
        doc = i.doc
        changed = False
        if 'owner' not in doc:
            doc['owner'] = 'broker05'
            doc['owner_token'] = doc.id
        if not doc.get("value", {}):
            changed = True
            doc["value"] = {"amount": 0.0, "currency": u"UAH", "valueAddedTaxIncluded": True}
        elif doc["value"]["amount"] < 0.0:
            changed = True
            doc["value"]["amount"] = 0.0
        value = doc["value"]
        if "minimalStep" in doc:
            doc["minimalStep"], changed = fix_value(doc["minimalStep"], value, changed)
        else:
            changed = True
            doc["minimalStep"] = value
        if doc.get("items", []):
            for item in doc["items"]:
                if not item.get('description'):
                    changed = True
                    item["description"] = u"item description"
                if item.get('classification') is not None and item['classification'].get('scheme') != 'CPV':
                    changed = True
                    item['classification']['scheme'] = 'CPV'
                if item.get('classification') is not None and item['classification'].get('id') not in CPV_CODES:
                    changed = True
                    item['classification']['id'] = CPV_CODES[0]
                if item.get('additionalClassifications') and not any([i['scheme'] == u'ДКПП' for i in item['additionalClassifications']]):
                    changed = True
                    item['additionalClassifications'][0]['scheme'] = u'ДКПП'
                if item.get('unit') is not None and 'code' not in item['unit']:
                    changed = True
                    item['unit']['code'] = 'code'
        else:
            changed = True
            doc["items"] = [
                {
                    "description": u"item description"
                }
            ]
        if "procuringEntity" in doc:
            doc["procuringEntity"], changed = fix_org(doc["procuringEntity"], changed)
        else:
            changed = True
            doc["procuringEntity"] = {
                "name": u"name",
                "identifier": {
                    "scheme": u"UA-EDR",
                    "id": u"00000000"
                },
                "address": {
                    "countryName": u"Україна"
                },
                "contactPoint": {
                    "name": u"name",
                    "telephone": u"0440000000"
                }
            }
        org = doc["procuringEntity"]
        for i in doc.get('complaints', []):
            if "author" in i:
                i["author"], changed = fix_org(i["author"], changed)
            else:
                changed = True
                i["author"] = org
        for i in doc.get('questions', []):
            if "author" in i:
                i["author"], changed = fix_org(i["author"], changed)
            else:
                changed = True
                i["author"] = org
        bid_id = None
        for item in doc.get('bids', []):
            if 'owner' not in item:
                item['owner'] = 'broker05'
            if 'owner_token' not in item:
                item['owner_token'] = item['id']
            if "value" in item:
                item["value"], changed = fix_value(item["value"], value, changed)
            else:
                changed = True
                item["value"] = value
            if 'tenderers' in item:
                items = item['tenderers']
                if len(items) != 1:
                    changed = True
                    item['tenderers'] = items = item['tenderers'][:1]
                item['tenderers'][0], changed = fix_org(item['tenderers'][0], changed)
            else:
                changed = True
                item['tenderers'] = [org]
            bid_id = item['id']
        if bid_id is None and 'awards' in doc:
            del doc['awards']
        for item in doc.get('awards', []):
            if 'bid_id' not in item:
                changed = True
                item['bid_id'] = bid_id
            if "value" in item:
                item["value"], changed = fix_value(item["value"], value, changed)
            if 'suppliers' in item:
                items = item['suppliers']
                if len(items) != 1:
                    changed = True
                    item['suppliers'] = items = item['suppliers'][:1]
                item['suppliers'][0], changed = fix_org(item['suppliers'][0], changed)
            else:
                changed = True
                item['suppliers'] = [org]
        if not (doc.get('enquiryPeriod', {}).get('startDate', '0000') <=
                doc.get('enquiryPeriod', {}).get('endDate', '9999') <=
                doc.get('tenderPeriod', {}).get('startDate', '0000') <=
                doc.get('tenderPeriod', {}).get('endDate', '9999') <=
                doc.get('auctionPeriod', {}).get('startDate', '9999') <=
                doc.get('auctionPeriod', {}).get('endDate', '9999') <=
                doc.get('awardPeriod', {}).get('startDate', '9999') <=
                doc.get('awardPeriod', {}).get('endDate', '9999')):
            changed = True
            status = doc['status']
            now = get_now()
            if status == 'active.enquiries':
                doc.update({
                    "enquiryPeriod": {
                        "startDate": (now).isoformat(),
                        "endDate": (now + timedelta(days=7)).isoformat()
                    },
                    "tenderPeriod": {
                        "startDate": (now + timedelta(days=7)).isoformat(),
                        "endDate": (now + timedelta(days=14)).isoformat()
                    },
                    "auctionPeriod": {},
                    "awardPeriod": {}
                })
            elif status == 'active.tendering':
                doc.update({
                    "enquiryPeriod": {
                        "startDate": (now - timedelta(days=10)).isoformat(),
                        "endDate": (now).isoformat()
                    },
                    "tenderPeriod": {
                        "startDate": (now).isoformat(),
                        "endDate": (now + timedelta(days=7)).isoformat()
                    },
                    "auctionPeriod": {},
                    "awardPeriod": {}
                })
            elif status == 'active.auction':
                doc.update({
                    "enquiryPeriod": {
                        "startDate": (now - timedelta(days=14)).isoformat(),
                        "endDate": (now - timedelta(days=7)).isoformat()
                    },
                    "tenderPeriod": {
                        "startDate": (now - timedelta(days=7)).isoformat(),
                        "endDate": (now).isoformat()
                    },
                    "auctionPeriod": {
                        "startDate": (now).isoformat()
                    },
                    "awardPeriod": {}
                })
            elif status == 'active.qualification':
                doc.update({
                    "enquiryPeriod": {
                        "startDate": (now - timedelta(days=15)).isoformat(),
                        "endDate": (now - timedelta(days=8)).isoformat()
                    },
                    "tenderPeriod": {
                        "startDate": (now - timedelta(days=8)).isoformat(),
                        "endDate": (now - timedelta(days=1)).isoformat()
                    },
                    "auctionPeriod": {
                        "startDate": (now - timedelta(days=1)).isoformat(),
                        "endDate": (now).isoformat()
                    },
                    "awardPeriod": {
                        "startDate": (now).isoformat()
                    }
                })
            elif status == 'active.awarded':
                doc.update({
                    "enquiryPeriod": {
                        "startDate": (now - timedelta(days=15)).isoformat(),
                        "endDate": (now - timedelta(days=8)).isoformat()
                    },
                    "tenderPeriod": {
                        "startDate": (now - timedelta(days=8)).isoformat(),
                        "endDate": (now - timedelta(days=1)).isoformat()
                    },
                    "auctionPeriod": {
                        "startDate": (now - timedelta(days=1)).isoformat(),
                        "endDate": (now).isoformat()
                    },
                    "awardPeriod": {
                        "startDate": (now).isoformat(),
                        "endDate": (now).isoformat()
                    }
                })
            else:
                doc.update({
                    "enquiryPeriod": {
                        "startDate": (now - timedelta(days=25)).isoformat(),
                        "endDate": (now - timedelta(days=18)).isoformat()
                    },
                    "tenderPeriod": {
                        "startDate": (now - timedelta(days=18)).isoformat(),
                        "endDate": (now - timedelta(days=11)).isoformat()
                    },
                    "auctionPeriod": {
                        "startDate": (now - timedelta(days=11)).isoformat(),
                        "endDate": (now - timedelta(days=10)).isoformat()
                    },
                    "awardPeriod": {
                        "startDate": (now - timedelta(days=10)).isoformat(),
                        "endDate": (now - timedelta(days=10)).isoformat()
                    }
                })
        if changed:
            doc['dateModified'] = get_now().isoformat()
            registry.db.save(doc)


def from12to13(registry):
    results = registry.db.view('tenders/all', include_docs=True)
    for i in results:
        doc = i.doc
        doc['procurementMethod'] = 'open'
        doc['awardCriteria'] = 'lowestCost'
        doc['submissionMethod'] = 'electronicAuction'
        doc['dateModified'] = get_now().isoformat()
        registry.db.save(doc)


def fix_rfc2047(item, changed):
    try:
        pairs = decode_header(item['title'])
    except Exception:
        pairs = None
    if pairs:
        header = pairs[0]
        if header[1]:
            title = header[0].decode(header[1])
        else:
            title = header[0].decode('utf8')
        if title != item['title']:
            changed = True
            item['title'] = title
    return changed


def from13to14(registry):
    results = registry.db.view('tenders/all', include_docs=True)
    for i in results:
        doc = i.doc
        changed = False
        for i in doc.get('documents', []):
            changed = fix_rfc2047(i, changed)
        for c in doc.get('complaints', []):
            for i in c.get('documents', []):
                changed = fix_rfc2047(i, changed)
        for b in doc.get('bids', []):
            for i in b.get('documents', []):
                changed = fix_rfc2047(i, changed)
        for a in doc.get('awards', []):
            for i in c.get('documents', []):
                changed = fix_rfc2047(i, changed)
            for c in a.get('complaints', []):
                for i in c.get('documents', []):
                    changed = fix_rfc2047(i, changed)
            for c in a.get('contracts', []):
                for i in c.get('documents', []):
                    changed = fix_rfc2047(i, changed)
        if changed:
            doc['dateModified'] = get_now().isoformat()
            registry.db.save(doc)


def from14to15(registry):
    results = registry.db.view('tenders/all', include_docs=True)
    for i in results:
        doc = i.doc
        changed = False
        if not doc.get('title'):
            doc['title'] = doc["items"][0]['description']
            changed = True
        for item in doc["items"]:
            if not item.get('classification'):
                changed = True
                item['classification'] = {
                    "scheme": u"CPV",
                    "id": u"41110000-3",
                    "description": u"Drinking water"
                }
            if not item.get('additionalClassifications'):
                changed = True
                item['additionalClassifications'] = [
                    {
                        "scheme": u"ДКПП",
                        "id": u"36.00.11-00.00",
                        "description": u"Вода питна"
                    }
                ]
        if changed:
            doc['dateModified'] = get_now().isoformat()
            registry.db.save(doc)


def from15to16(registry):
    results = registry.db.view('tenders/all', include_docs=True)
    for i in results:
        doc = i.doc
        changed = False
        for item in doc["items"]:
            if 'deliveryLocation' in item and 'longitudee' in item['deliveryLocation']:
                changed = True
                item['deliveryLocation']['longitude'] = item['deliveryLocation'].pop('longitudee')
        if changed:
            doc['dateModified'] = get_now().isoformat()
            registry.db.save(doc)


def from16to17(registry):
    results = registry.db.view('tenders/all', include_docs=True)
    for i in results:
        doc = i.doc
        changed = False
        for i in doc.get("awards", []):
            if 'complaintPeriod' in i:
                continue
            if i['status'] == 'pending':
                i['complaintPeriod'] = {'startDate': i['date']}
            elif i['status'] == 'cancelled':
                i['complaintPeriod'] = {'startDate': i['date'], 'endDate': i['date']}
            else:
                i['complaintPeriod'] = {'startDate': i['date'], 'endDate': (parse_date(i['date'], TZ) + STAND_STILL_TIME).isoformat()}
            changed = True
        if changed:
            doc['dateModified'] = get_now().isoformat()
            registry.db.save(doc)


def from17to18(registry):
    results = registry.db.iterview('tenders/all', 2**10, include_docs=True)
    for i in results:
        doc = i.doc
        contracts = []
        for i in doc.get("awards", []):
            contracts.extend(i.pop("contracts", []))
        if contracts:
            doc['contracts'] = contracts
            doc['dateModified'] = get_now().isoformat()
            registry.db.save(doc)


def from18to19(registry):

    def update_documents_type(item, changed):
        for document in item.get('documents', []):
            if document.get('documentType') == 'contractAnnexes':
                document['documentType'] = 'contractAnnexe'
                changed = True
        return changed

    results = registry.db.iterview('tenders/all', 2 ** 10, include_docs=True)
    docs = []
    for i in results:
        doc = i.doc
        changed = update_documents_type(doc, False)
        for item in ('bids', 'complaints', 'cancellations', 'contracts',
                     'awards'):
            for item_val in doc.get(item, []):
                changed = update_documents_type(item_val, changed)
                if item == 'awards':
                    for complaint in item_val.get('complaints', []):
                        changed = update_documents_type(complaint, changed)
        if changed:
            doc['dateModified'] = get_now().isoformat()
            docs.append(doc)
        if len(docs) >= 2 ** 7:
            registry.db.update(docs)
            docs = []
    if docs:
        registry.db.update(docs)


def from19to20(registry):
    results = registry.db.iterview('tenders/all', 2 ** 10, include_docs=True)
    docs = []
    for i in results:
        doc = i.doc
        changed = False
        for contract in doc.get('contracts', []):
            for document in contract.get('documents', []):
                if 'awards' in document['url']:
                    url = document['url'].split('/')
                    document['url'] = '/'.join(url[:3] + url[5:])
                    changed = True
        if changed:
            doc['dateModified'] = get_now().isoformat()
            docs.append(doc)
        if len(docs) >= 2 ** 7:
            result = registry.db.update(docs)
            docs = []
    if docs:
        registry.db.update(docs)


def from20to21(registry):
    results = registry.db.iterview('tenders/all', 2 ** 10, include_docs=True)
    docs = []
    for i in results:
        doc = i.doc
        if not doc.get('next_check') and doc['status'] in ['active.enquiries', 'active.tendering', 'active.auction', 'active.awarded']:
            doc['next_check'] = get_now().isoformat()
            docs.append(doc)
        if len(docs) >= 2 ** 7:
            result = registry.db.update(docs)
            docs = []
    if docs:
        registry.db.update(docs)


def from21to22(registry):
    results = registry.db.iterview('tenders/all', 2 ** 10, include_docs=True)
    docs = []
    for i in results:
        doc = i.doc
        changed = False
        for a in doc.get("awards", []):
            for c in a.get("complaints", []):
                if 'dateEscalated' in c and c['type'] == 'claim':
                    c['type'] = 'complaint'
                    changed = True
        if changed:
            doc['dateModified'] = get_now().isoformat()
            docs.append(doc)
        if len(docs) >= 2 ** 7:
            result = registry.db.update(docs)
            docs = []
    if docs:
        registry.db.update(docs)


def from22to23(registry):
    class Request(object):
        def __init__(self, registry):
            self.registry = registry
    len(registry.db.view('tenders/all', limit=1))
    results = registry.db.iterview('tenders/all', 2 ** 10, include_docs=True, stale='update_after')
    docs = []
    request = Request(registry)
    root = Root(request)
    for i in results:
        doc = i.doc
        if 'documents' not in doc and 'awards' not in doc and 'bids' not in doc and 'questions' not in doc and 'complaints' not in doc and 'cancellations' not in doc and 'contracts' not in doc:
            continue
        if 'documents' in doc and any([i.get('url', '').startswith(registry.docservice_url) for i in doc['documents']]):
            continue
        model = registry.tender_procurementMethodTypes.get(doc.get('procurementMethodType', 'belowThreshold'))
        if model:
            try:
                tender = model(doc)
                tender.__parent__ = root
                doc = tender.to_primitive()
            except:
                LOGGER.error("Failed migration of tender {} to schema 23.".format(doc.id), extra={'MESSAGE_ID': 'migrate_data_failed', 'TENDER_ID': doc.id})
            else:
                doc['dateModified'] = get_now().isoformat()
                docs.append(doc)
        if len(docs) >= 2 ** 7:
            result = registry.db.update(docs)
            docs = []
    if docs:
        registry.db.update(docs)


def from23to24(registry):
    len(registry.db.view('tenders/all', limit=1))
    results = registry.db.iterview('tenders/all', 2 ** 10, include_docs=True, stale='update_after')
    docs = []
    for i in results:
        doc = i.doc
        if not doc.get('operator'):
            doc['operator'] = 'UA'
            doc['dateModified'] = get_now().isoformat()
            docs.append(doc)
        if len(docs) >= 2 ** 7:
            result = registry.db.update(docs)
            docs = []
    if docs:
        registry.db.update(docs)
