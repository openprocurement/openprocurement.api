# -*- coding: utf-8 -*-
from barbecue import chef
from base64 import b64encode
from cornice.resource import resource, view
from cornice.util import json_error
from couchdb.http import ResourceConflict
from email.header import decode_header
from functools import partial
from json import dumps
from jsonpatch import make_patch, apply_patch as _apply_patch
from logging import getLogger
from openprocurement.api.models import Document, Revision, Award, Period, get_now
from openprocurement.api.interfaces import IBaseTender
from pkg_resources import get_distribution
from rfc6266 import build_header
from schematics.exceptions import ModelValidationError
from time import sleep
from urllib import quote
from urlparse import urlparse, parse_qs
from uuid import uuid4
from webob.multidict import NestedMultiDict


PKG = get_distribution(__package__)
LOGGER = getLogger(PKG.project_name)
VERSION = '{}.{}'.format(int(PKG.parsed_version[0]), int(PKG.parsed_version[1]))
json_view = partial(view, renderer='json')


def generate_id():
    return uuid4().hex


def generate_tender_id(ctime, db, server_id=''):
    key = ctime.date().isoformat()
    tenderIDdoc = 'tenderID_' + server_id if server_id else 'tenderID'
    while True:
        try:
            tenderID = db.get(tenderIDdoc, {'_id': tenderIDdoc})
            index = tenderID.get(key, 1)
            tenderID[key] = index + 1
            db.save(tenderID)
        except ResourceConflict:  # pragma: no cover
            pass
        except Exception:  # pragma: no cover
            sleep(1)
        else:
            break
    return 'UA-{:04}-{:02}-{:02}-{:06}{}'.format(ctime.year, ctime.month, ctime.day, index, server_id and '-' + server_id)


def get_filename(data):
    try:
        pairs = decode_header(data.filename)
    except Exception:
        pairs = None
    if not pairs:
        return data.filename
    header = pairs[0]
    if header[1]:
        return header[0].decode(header[1])
    else:
        return header[0]


def upload_file(request):
    first_document = request.validated['documents'][0] if 'documents' in request.validated and request.validated['documents'] else None
    if request.content_type == 'multipart/form-data':
        data = request.validated['file']
        filename = get_filename(data)
        content_type = data.type
        in_file = data.file
    else:
        filename = first_document.title
        content_type = request.content_type
        in_file = request.body_file
    document = Document({
        'title': filename,
        'format': content_type
    })
    document.__parent__ = request.context
    if 'document_id' in request.validated:
        document.id = request.validated['document_id']
    if first_document:
        document.datePublished = first_document.datePublished
    key = generate_id()
    document_route = request.matched_route.name.replace("collection_", "")
    document_path = request.current_route_path(_route_name=document_route, document_id=document.id, _query={'download': key})
    document.url = '/tenders' + document_path.split('/tenders', 1)[1]
    conn = getattr(request.registry, 's3_connection', None)
    if conn:
        bucket = conn.get_bucket(request.registry.bucket_name)
        filename = "{}/{}/{}".format(request.validated['tender_id'], document.id, key)
        key = bucket.new_key(filename)
        key.set_metadata('Content-Type', document.format)
        key.set_metadata("Content-Disposition", build_header(document.title, filename_compat=quote(document.title.encode('utf-8'))))
        key.set_contents_from_file(in_file)
        key.set_acl('private')
    else:
        filename = "{}_{}".format(document.id, key)
        request.validated['tender']['_attachments'][filename] = {
            "content_type": document.format,
            "data": b64encode(in_file.read())
        }
    return document


def update_file_content_type(request):
    conn = getattr(request.registry, 's3_connection', None)
    if conn:
        document = request.validated['document']
        key = parse_qs(urlparse(document.url).query).get('download').pop()
        bucket = conn.get_bucket(request.registry.bucket_name)
        filename = "{}/{}/{}".format(request.validated['tender_id'], document.id, key)
        key = bucket.get_key(filename)
        key.set_metadata('Content-Type', document.format)
        key.copy(key.bucket.name, key.name, key.metadata, preserve_acl=True)


def get_file(request):
    tender_id = request.validated['tender_id']
    document = request.validated['document']
    key = request.params.get('download')
    conn = getattr(request.registry, 's3_connection', None)
    filename = "{}_{}".format(document.id, key)
    if conn and filename not in request.validated['tender']['_attachments']:
        filename = "{}/{}/{}".format(tender_id, document.id, key)
        url = conn.generate_url(method='GET', bucket=request.registry.bucket_name, key=filename, expires_in=300)
        request.response.content_type = document.format.encode('utf-8')
        request.response.content_disposition = build_header(document.title, filename_compat=quote(document.title.encode('utf-8')))
        request.response.status = '302 Moved Temporarily'
        request.response.location = url
        return url
    else:
        filename = "{}_{}".format(document.id, key)
        data = request.registry.db.get_attachment(tender_id, filename)
        if data:
            request.response.content_type = document.format.encode('utf-8')
            request.response.content_disposition = build_header(document.title, filename_compat=quote(document.title.encode('utf-8')))
            request.response.body_file = data
            return request.response
        request.errors.add('url', 'download', 'Not Found')
        request.errors.status = 404


def prepare_patch(changes, orig, patch, basepath=''):
    if isinstance(patch, dict):
        for i in patch:
            if i in orig:
                prepare_patch(changes, orig[i], patch[i], '{}/{}'.format(basepath, i))
            else:
                changes.append({'op': 'add', 'path': '{}/{}'.format(basepath, i), 'value': patch[i]})
    elif isinstance(patch, list):
        if len(patch) < len(orig):
            for i in reversed(range(len(patch), len(orig))):
                changes.append({'op': 'remove', 'path': '{}/{}'.format(basepath, i)})
        for i, j in enumerate(patch):
            if len(orig) > i:
                prepare_patch(changes, orig[i], patch[i], '{}/{}'.format(basepath, i))
            else:
                changes.append({'op': 'add', 'path': '{}/{}'.format(basepath, i), 'value': j})
    else:
        for x in make_patch(orig, patch).patch:
            x['path'] = '{}{}'.format(basepath, x['path'])
            changes.append(x)


def apply_data_patch(item, changes):
    patch_changes = []
    prepare_patch(patch_changes, item, changes)
    if not patch_changes:
        return {}
    return _apply_patch(item, patch_changes)


def tender_serialize(tender, fields):
    return dict([(i, j) for i, j in tender.serialize(tender.status).items() if i in fields])

def tender_construct_and_serialize(request, tender_data, fields):
    adapter = request.registry.queryAdapter(tender_data, IBaseTender, name=tender_data['doc_type'])
    tender = adapter.tender()
    return dict([(i, j) for i, j in tender.serialize(tender.status).items() if i in fields])

def get_revision_changes(dst, src):
    return make_patch(dst, src).patch


def set_ownership(item, request):
    item.owner = request.authenticated_userid
    item.owner_token = generate_id()


def set_modetest_titles(tender):
    if not tender.title or u'[ТЕСТУВАННЯ]' not in tender.title:
        tender.title = u'[ТЕСТУВАННЯ] {}'.format(tender.title or u'')
    if not tender.title_en or u'[TESTING]' not in tender.title_en:
        tender.title_en = u'[TESTING] {}'.format(tender.title_en or u'')
    if not tender.title_ru or u'[ТЕСТИРОВАНИЕ]' not in tender.title_ru:
        tender.title_ru = u'[ТЕСТИРОВАНИЕ] {}'.format(tender.title_ru or u'')


def save_tender(request):
    tender = request.validated['tender']
    if tender.mode == u'test':
        set_modetest_titles(tender)
    patch = get_revision_changes(tender.serialize("plain"), request.validated['tender_src'])
    if patch:
        tender.revisions.append(Revision({'author': request.authenticated_userid, 'changes': patch, 'rev': tender.rev}))
        old_dateModified = tender.dateModified
        tender.dateModified = get_now()
        try:
            tender.store(request.registry.db)
        except ModelValidationError, e:
            for i in e.message:
                request.errors.add('body', i, e.message[i])
            request.errors.status = 422
        except Exception, e:  # pragma: no cover
            request.errors.add('body', 'data', str(e))
        else:
            LOGGER.info('Saved tender {}: dateModified {} -> {}'.format(tender.id, old_dateModified and old_dateModified.isoformat(), tender.dateModified.isoformat()),
                        extra=context_unpack(request, {'MESSAGE_ID': 'save_tender'}, {'TENDER_REV': tender.rev}))
            return True


def apply_patch(request, data=None, save=True, src=None):
    data = request.validated['data'] if data is None else data
    patch = data and apply_data_patch(src or request.context.serialize(), data)
    if patch:
        request.context.import_data(patch)
        if save:
            return save_tender(request)


def check_bids(request):
    tender = request.validated['tender']
    if tender.lots:
        [setattr(i, 'status', 'unsuccessful') for i in tender.lots if i.numberOfBids == 0]
        if max([i.numberOfBids for i in tender.lots]) < 2:
            #tender.status = 'active.qualification'
            add_next_award(request)
        if set([i.status for i in tender.lots]) == set(['unsuccessful']):
            tender.status = 'unsuccessful'
    else:
        if tender.numberOfBids == 0:
            tender.status = 'unsuccessful'
        if tender.numberOfBids == 1:
            #tender.status = 'active.qualification'
            add_next_award(request)


def check_tender_status(request):
    tender = request.validated['tender']
    now = get_now()
    if tender.lots:
        if any([i.status == 'pending' for i in tender.complaints]):
            return
        for lot in tender.lots:
            if lot.status != 'active':
                continue
            lot_awards = [i for i in tender.awards if i.lotID == lot.id]
            if not lot_awards:
                continue
            last_award = lot_awards[-1]
            pending_awards_complaints = any([
                i.status == 'pending'
                for a in lot_awards
                for i in a.complaints
            ])
            stand_still_end = max([
                a.complaintPeriod.endDate or now
                for a in lot_awards
            ])
            if pending_awards_complaints or not stand_still_end <= now:
                continue
            elif last_award.status == 'unsuccessful':
                lot.status = 'unsuccessful'
                continue
            elif last_award.status == 'active' and any([i.status == 'active' and i.awardID == last_award.id for i in tender.contracts]):
                lot.status = 'complete'
        statuses = set([lot.status for lot in tender.lots])
        if statuses == set(['cancelled']):
            tender.status = 'cancelled'
        elif not statuses.difference(set(['unsuccessful', 'cancelled'])):
            tender.status = 'unsuccessful'
        elif not statuses.difference(set(['complete', 'unsuccessful', 'cancelled'])):
            tender.status = 'complete'
    else:
        pending_complaints = any([
            i.status == 'pending'
            for i in tender.complaints
        ])
        pending_awards_complaints = any([
            i.status == 'pending'
            for a in tender.awards
            for i in a.complaints
        ])
        stand_still_ends = [
            a.complaintPeriod.endDate
            for a in tender.awards
            if a.complaintPeriod.endDate
        ]
        stand_still_end = max(stand_still_ends) if stand_still_ends else now
        stand_still_time_expired = stand_still_end < now
        active_awards = any([
            a.status == 'active'
            for a in tender.awards
        ])
        if not active_awards and not pending_complaints and not pending_awards_complaints and stand_still_time_expired:
            tender.status = 'unsuccessful'
        if tender.contracts and tender.contracts[-1].status == 'active':
            tender.status = 'complete'


def add_next_award(request):
    tender = request.validated['tender']
    now = get_now()
    if not tender.awardPeriod:
        tender.awardPeriod = Period({})
    if not tender.awardPeriod.startDate:
        tender.awardPeriod.startDate = now
    if tender.lots:
        statuses = set()
        for lot in tender.lots:
            if lot.status != 'active':
                continue
            lot_awards = [i for i in tender.awards if i.lotID == lot.id]
            if lot_awards and lot_awards[-1].status in ['pending', 'active']:
                statuses.add(lot_awards[-1].status if lot_awards else 'unsuccessful')
                continue
            lot_items = [i.id for i in tender.items if i.relatedLot == lot.id]
            features = [
                i
                for i in (tender.features or [])
                if i.featureOf == 'tenderer' or i.featureOf == 'lot' and i.relatedItem == lot.id or i.featureOf == 'item' and i.relatedItem in lot_items
            ]
            codes = [i.code for i in features]
            bids = [
                {
                    'id': bid.id,
                    'value': [i for i in bid.lotValues if lot.id == i.relatedLot][0].value,
                    'tenderers': bid.tenderers,
                    'parameters': [i for i in bid.parameters if i.code in codes],
                    'date': [i for i in bid.lotValues if lot.id == i.relatedLot][0].date
                }
                for bid in tender.bids
                if lot.id in [i.relatedLot for i in bid.lotValues]
            ]
            if not bids:
                lot.status = 'unsuccessful'
                statuses.add('unsuccessful')
                continue
            unsuccessful_awards = [i.bid_id for i in lot_awards if i.status == 'unsuccessful']
            bids = chef(bids, features, unsuccessful_awards)
            if bids:
                bid = bids[0]
                award = Award({
                    'bid_id': bid['id'],
                    'lotID': lot.id,
                    'status': 'pending',
                    'value': bid['value'],
                    'suppliers': bid['tenderers'],
                    'complaintPeriod': {
                        'startDate': now.isoformat()
                    }
                })
                tender.awards.append(award)
                request.response.headers['Location'] = request.route_url('Tender Awards', tender_id=tender.id, award_id=award['id'])
                statuses.add('pending')
            else:
                statuses.add('unsuccessful')
        if statuses.difference(set(['unsuccessful', 'active'])):
            tender.awardPeriod.endDate = None
            tender.status = 'active.qualification'
        else:
            tender.awardPeriod.endDate = now
            tender.status = 'active.awarded'
    else:
        if not tender.awards or tender.awards[-1].status not in ['pending', 'active']:
            unsuccessful_awards = [i.bid_id for i in tender.awards if i.status == 'unsuccessful']
            bids = chef(tender.bids, tender.features or [], unsuccessful_awards)
            if bids:
                bid = bids[0].serialize()
                award = Award({
                    'bid_id': bid['id'],
                    'status': 'pending',
                    'value': bid['value'],
                    'suppliers': bid['tenderers'],
                    'complaintPeriod': {
                        'startDate': get_now().isoformat()
                    }
                })
                tender.awards.append(award)
                request.response.headers['Location'] = request.route_url('Tender Awards', tender_id=tender.id, award_id=award['id'])
        if tender.awards[-1].status == 'pending':
            tender.awardPeriod.endDate = None
            tender.status = 'active.qualification'
        else:
            tender.awardPeriod.endDate = now
            tender.status = 'active.awarded'


def request_params(request):
    try:
        params = NestedMultiDict(request.GET, request.POST)
    except UnicodeDecodeError:
        request.errors.add('body', 'data', 'could not decode params')
        request.errors.status = 422
        raise error_handler(request.errors, False)
    except:
        request.errors.add('body', str(e.__class__.__name__), str(e))
        request.errors.status = 422
        raise error_handler(request.errors, False)
    return params


def error_handler(errors, request_params=True):
    params = {
        'ERROR_STATUS': errors.status
    }
    if request_params:
        params['ROLE'] = str(errors.request.authenticated_role)
        if errors.request.params:
            params['PARAMS'] = str(dict(errors.request.params))
    if errors.request.matchdict:
        for x, j in errors.request.matchdict.items():
            params[x.upper()] = j
    if 'tender' in errors.request.validated:
        params['TENDER_REV'] = errors.request.validated['tender'].rev
        params['TENDERID'] = errors.request.validated['tender'].tenderID
        params['TENDER_STATUS'] = errors.request.validated['tender'].status
    LOGGER.info('Error on processing request "{}"'.format(dumps(errors, indent=4)),
                extra=context_unpack(errors.request, {'MESSAGE_ID': 'error_handler'}, params))
    return json_error(errors)


opresource = partial(resource, error_handler=error_handler)


def forbidden(request):
    request.errors.add('url', 'permission', 'Forbidden')
    request.errors.status = 403
    return error_handler(request.errors)


def add_logging_context(event):
    request = event.request
    params = {
        'TENDERS_API_VERSION': VERSION,
        'TAGS': 'python,api',
        'USER': str(request.authenticated_userid or ''),
        #'ROLE': str(request.authenticated_role),
        'CURRENT_URL': request.url,
        'CURRENT_PATH': request.path_info,
        'REMOTE_ADDR': request.remote_addr or '',
        'USER_AGENT': request.user_agent or '',
        'REQUEST_METHOD': request.method,
        'AWARD_ID': '',
        'BID_ID': '',
        'COMPLAINT_ID': '',
        'CONTRACT_ID': '',
        'DOCUMENT_ID': '',
        'QUESTION_ID': '',
        'TENDER_ID': '',
        'TIMESTAMP': get_now().isoformat(),
        'REQUEST_ID': request.environ.get('REQUEST_ID', ''),
        'CLIENT_REQUEST_ID': request.headers.get('X-Client-Request-ID', ''),
    }

    request.logging_context = params


def set_logging_context(event):
    request = event.request

    params = {}
    params['ROLE'] = str(request.authenticated_role)
    if request.params:
        params['PARAMS'] = str(dict(request.params))
    if request.matchdict:
        for x, j in request.matchdict.items():
            params[x.upper()] = j
    if 'tender' in request.validated:
        params['TENDER_REV'] = request.validated['tender'].rev
        params['TENDERID'] = request.validated['tender'].tenderID
        params['TENDER_STATUS'] = request.validated['tender'].status
    update_logging_context(request, params)


def update_logging_context(request, params):
    if not request.__dict__.get('logging_context'):
        request.logging_context = {}

    for x, j in params.items():
        request.logging_context[x.upper()] = j


def context_unpack(request, msg, params=None):
    if params:
        update_logging_context(request, params)
    logging_context = request.logging_context
    journal_context = msg
    for key, value in logging_context.items():
        journal_context["JOURNAL_" + key] = value
    return journal_context


def extract_tender_adapter(request, tid=None):

    if tid is None:
        tid = request.matchdict.get('tender_id')
    db = request.registry.db
    doc = db.get(tid)
    if doc is None:
        request.errors.add('url', 'tender_id', 'Not Found')
        request.errors.status = 404
        raise error_handler(request.errors)

    return request.registry.queryAdapter(doc, IBaseTender,
                                         name=doc.get('subtype', 'Tender'))


def extract_tender(request, tid=None):
    adapter = extract_tender_adapter(request, tid)
    if not adapter:
        return None
    return adapter.tender()
