# -*- coding: utf-8 -*-
from pkg_resources import get_distribution
from logging import getLogger
from base64 import b64encode
from jsonpatch import make_patch, apply_patch as _apply_patch
#from json_tools import diff, patch
from openprocurement.api.models import Document, Revision, Award, get_now
from urllib import quote
from uuid import uuid4
from schematics.exceptions import ModelValidationError
from couchdb.http import ResourceConflict
from time import sleep
from cornice.util import json_error
from json import dumps
from urlparse import urlparse, parse_qs
from email.header import decode_header
from rfc6266 import build_header

try:
    from systemd.journal import JournalHandler
except ImportError:  # pragma: no cover
    JournalHandler = False


PKG = get_distribution(__package__)
LOGGER = getLogger(PKG.project_name)
VERSION = '{}.{}'.format(int(PKG.parsed_version[0]), int(PKG.parsed_version[1]))


def generate_id():
    return uuid4().hex


def generate_tender_id(ctime, db):
    key = ctime.date().isoformat()
    while True:
        try:
            tenderID = db.get('tenderID', {'_id': 'tenderID'})
            index = tenderID.get(key, 1)
            tenderID[key] = index + 1
            db.save(tenderID)
        except ResourceConflict:  # pragma: no cover
            pass
        except Exception:  # pragma: no cover
            sleep(1)
        else:
            break
    return 'UA-{:04}-{:02}-{:02}-{:06}'.format(ctime.year, ctime.month, ctime.day, index)


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


def get_revision_changes(dst, src):
    #return diff(dst, src)
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
            LOGGER.info('Saved tender {}: dateModified {} -> {}'.format(tender.id, old_dateModified and old_dateModified.isoformat(), tender.dateModified.isoformat()), extra={'MESSAGE_ID': 'save_tender'})
            return True


def apply_patch(request, data=None, save=True, src=None):
    data = request.validated['data'] if data is None else data
    patch = data and apply_data_patch(src or request.context.serialize(), data)
    if patch:
        request.context.import_data(patch)
        if save:
            return save_tender(request)


def add_next_award(request):
    tender = request.validated['tender']
    unsuccessful_awards = [i.bid_id for i in tender.awards if i.status == 'unsuccessful']
    bids = [i for i in sorted(tender.bids, key=lambda i: (i.value.amount, i.date)) if i.id not in unsuccessful_awards]
    if bids:
        bid = bids[0].serialize()
        award_data = {
            'bid_id': bid['id'],
            'status': 'pending',
            'value': bid['value'],
            'suppliers': bid['tenderers'],
            'complaintPeriod': {
                'startDate': get_now().isoformat()
            }
        }
        award = Award(award_data)
        tender.awards.append(award)
        request.response.headers['Location'] = request.route_url('Tender Awards', tender_id=tender.id, award_id=award['id'])
    else:
        tender.awardPeriod.endDate = get_now()
        tender.status = 'active.awarded'


def error_handler(errors):
    for i in LOGGER.handlers:
        if isinstance(i, JournalHandler):
            i._extra['ERROR_STATUS'] = errors.status
            if 'ROLE' not in i._extra:
                i._extra['ROLE'] = str(errors.request.authenticated_role)
            if errors.request.params and 'PARAMS' not in i._extra:
                i._extra['PARAMS'] = str(dict(errors.request.params))
            if errors.request.matchdict:
                for x, j in errors.request.matchdict.items():
                    i._extra[x.upper()] = j
            if 'tender' in errors.request.validated:
                i._extra['TENDERID'] = errors.request.validated['tender'].tenderID
                i._extra['TENDER_STATUS'] = errors.request.validated['tender'].status
    LOGGER.info('Error on processing request "{}"'.format(dumps(errors, indent=4)), extra={'MESSAGE_ID': 'error_handler'})
    for i in LOGGER.handlers:
        LOGGER.removeHandler(i)
    return json_error(errors)


def forbidden(request):
    request.errors.add('url', 'permission', 'Forbidden')
    request.errors.status = 403
    return error_handler(request.errors)


def set_journal_handler(event):
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
    for i in LOGGER.handlers:
        LOGGER.removeHandler(i)
    LOGGER.addHandler(JournalHandler(**params))


def update_journal_handler_role(event):
    request = event.request
    for i in LOGGER.handlers:
        if isinstance(i, JournalHandler):
            i._extra['ROLE'] = str(request.authenticated_role)
            if request.params:
                i._extra['PARAMS'] = str(dict(request.params))
            if request.matchdict:
                for x, j in request.matchdict.items():
                    i._extra[x.upper()] = j
            if 'tender' in request.validated:
                i._extra['TENDERID'] = request.validated['tender'].tenderID
                i._extra['TENDER_STATUS'] = request.validated['tender'].status


def cleanup_journal_handler(event):
    for i in LOGGER.handlers:
        LOGGER.removeHandler(i)


def update_journal_handler_params(params):
    for i in LOGGER.handlers:
        if isinstance(i, JournalHandler):
            for x, j in params.items():
                i._extra[x.upper()] = j
