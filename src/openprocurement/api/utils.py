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
from pkg_resources import get_distribution
from rfc6266 import build_header
from schematics.exceptions import ModelValidationError
from time import sleep
from urllib import quote
from urlparse import urlparse, parse_qs
from uuid import uuid4
from webob.multidict import NestedMultiDict
from pyramid.exceptions import URLDecodeError
from pyramid.compat import decode_path_info


PKG = get_distribution(__package__)
LOGGER = getLogger(PKG.project_name)
VERSION = '{}.{}'.format(int(PKG.parsed_version[0]), int(PKG.parsed_version[1]))
ROUTE_PREFIX = '/api/{}'.format(VERSION)
json_view = partial(view, renderer='json')


def generate_id():
    return uuid4().hex


def generate_auction_id(ctime, db, server_id=''):
    key = ctime.date().isoformat()
    auctionIDdoc = 'auctionID_' + server_id if server_id else 'auctionID'
    while True:
        try:
            auctionID = db.get(auctionIDdoc, {'_id': auctionIDdoc})
            index = auctionID.get(key, 1)
            auctionID[key] = index + 1
            db.save(auctionID)
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
    document.url = '/auctions' + document_path.split('/auctions', 1)[1]
    conn = getattr(request.registry, 's3_connection', None)
    if conn:
        bucket = conn.get_bucket(request.registry.bucket_name)
        filename = "{}/{}/{}".format(request.validated['auction_id'], document.id, key)
        key = bucket.new_key(filename)
        key.set_metadata('Content-Type', document.format)
        key.set_metadata("Content-Disposition", build_header(document.title, filename_compat=quote(document.title.encode('utf-8'))))
        key.set_contents_from_file(in_file)
        key.set_acl('private')
    else:
        filename = "{}_{}".format(document.id, key)
        request.validated['auction']['_attachments'][filename] = {
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
        filename = "{}/{}/{}".format(request.validated['auction_id'], document.id, key)
        key = bucket.get_key(filename)
        key.set_metadata('Content-Type', document.format)
        key.copy(key.bucket.name, key.name, key.metadata, preserve_acl=True)


def get_file(request):
    auction_id = request.validated['auction_id']
    document = request.validated['document']
    key = request.params.get('download')
    conn = getattr(request.registry, 's3_connection', None)
    filename = "{}_{}".format(document.id, key)
    if conn and filename not in request.validated['auction']['_attachments']:
        filename = "{}/{}/{}".format(auction_id, document.id, key)
        url = conn.generate_url(method='GET', bucket=request.registry.bucket_name, key=filename, expires_in=300)
        request.response.content_type = document.format.encode('utf-8')
        request.response.content_disposition = build_header(document.title, filename_compat=quote(document.title.encode('utf-8')))
        request.response.status = '302 Moved Temporarily'
        request.response.location = url
        return url
    else:
        filename = "{}_{}".format(document.id, key)
        data = request.registry.db.get_attachment(auction_id, filename)
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


def auction_serialize(request, auction_data, fields):
    auction = request.auction_from_data(auction_data, raise_error=False)
    if auction is None:
        return dict([(i, auction_data.get(i, '')) for i in ['procurementMethodType', 'dateModified', 'id']])
    return dict([(i, j) for i, j in auction.serialize(auction.status).items() if i in fields])


def get_revision_changes(dst, src):
    return make_patch(dst, src).patch


def set_ownership(item, request):
    item.owner = request.authenticated_userid
    item.owner_token = generate_id()


def set_modetest_titles(auction):
    if not auction.title or u'[ТЕСТУВАННЯ]' not in auction.title:
        auction.title = u'[ТЕСТУВАННЯ] {}'.format(auction.title or u'')
    if not auction.title_en or u'[TESTING]' not in auction.title_en:
        auction.title_en = u'[TESTING] {}'.format(auction.title_en or u'')
    if not auction.title_ru or u'[ТЕСТИРОВАНИЕ]' not in auction.title_ru:
        auction.title_ru = u'[ТЕСТИРОВАНИЕ] {}'.format(auction.title_ru or u'')


def save_auction(request):
    auction = request.validated['auction']
    if auction.mode == u'test':
        set_modetest_titles(auction)
    patch = get_revision_changes(auction.serialize("plain"), request.validated['auction_src'])
    if patch:
        auction.revisions.append(Revision({'author': request.authenticated_userid, 'changes': patch, 'rev': auction.rev}))
        old_dateModified = auction.dateModified
        auction.dateModified = get_now()
        try:
            auction.store(request.registry.db)
        except ModelValidationError, e:
            for i in e.message:
                request.errors.add('body', i, e.message[i])
            request.errors.status = 422
        except Exception, e:  # pragma: no cover
            request.errors.add('body', 'data', str(e))
        else:
            LOGGER.info('Saved auction {}: dateModified {} -> {}'.format(auction.id, old_dateModified and old_dateModified.isoformat(), auction.dateModified.isoformat()),
                        extra=context_unpack(request, {'MESSAGE_ID': 'save_auction'}, {'AUCTION_REV': auction.rev}))
            return True


def apply_patch(request, data=None, save=True, src=None):
    data = request.validated['data'] if data is None else data
    patch = data and apply_data_patch(src or request.context.serialize(), data)
    if patch:
        request.context.import_data(patch)
        if save:
            return save_auction(request)


def check_bids(request):
    auction = request.validated['auction']
    if auction.lots:
        [setattr(i, 'status', 'unsuccessful') for i in auction.lots if i.numberOfBids == 0]
        if max([i.numberOfBids for i in auction.lots]) < 2:
            #auction.status = 'active.qualification'
            add_next_award(request)
        if set([i.status for i in auction.lots]) == set(['unsuccessful']):
            auction.status = 'unsuccessful'
    else:
        if auction.numberOfBids == 0:
            auction.status = 'unsuccessful'
        if auction.numberOfBids == 1:
            #auction.status = 'active.qualification'
            add_next_award(request)


def check_auction_status(request):
    auction = request.validated['auction']
    now = get_now()
    if auction.lots:
        if any([i.status == 'pending' for i in auction.complaints]):
            return
        for lot in auction.lots:
            if lot.status != 'active':
                continue
            lot_awards = [i for i in auction.awards if i.lotID == lot.id]
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
            elif last_award.status == 'active' and any([i.status == 'active' and i.awardID == last_award.id for i in auction.contracts]):
                lot.status = 'complete'
        statuses = set([lot.status for lot in auction.lots])
        if statuses == set(['cancelled']):
            auction.status = 'cancelled'
        elif not statuses.difference(set(['unsuccessful', 'cancelled'])):
            auction.status = 'unsuccessful'
        elif not statuses.difference(set(['complete', 'unsuccessful', 'cancelled'])):
            auction.status = 'complete'
    else:
        pending_complaints = any([
            i.status == 'pending'
            for i in auction.complaints
        ])
        pending_awards_complaints = any([
            i.status == 'pending'
            for a in auction.awards
            for i in a.complaints
        ])
        stand_still_ends = [
            a.complaintPeriod.endDate
            for a in auction.awards
            if a.complaintPeriod.endDate
        ]
        stand_still_end = max(stand_still_ends) if stand_still_ends else now
        stand_still_time_expired = stand_still_end < now
        active_awards = any([
            a.status == 'active'
            for a in auction.awards
        ])
        if not active_awards and not pending_complaints and not pending_awards_complaints and stand_still_time_expired:
            auction.status = 'unsuccessful'
        if auction.contracts and auction.contracts[-1].status == 'active':
            auction.status = 'complete'


def add_next_award(request):
    auction = request.validated['auction']
    now = get_now()
    if not auction.awardPeriod:
        auction.awardPeriod = Period({})
    if not auction.awardPeriod.startDate:
        auction.awardPeriod.startDate = now
    if auction.lots:
        statuses = set()
        for lot in auction.lots:
            if lot.status != 'active':
                continue
            lot_awards = [i for i in auction.awards if i.lotID == lot.id]
            if lot_awards and lot_awards[-1].status in ['pending', 'active']:
                statuses.add(lot_awards[-1].status if lot_awards else 'unsuccessful')
                continue
            lot_items = [i.id for i in auction.items if i.relatedLot == lot.id]
            features = [
                i
                for i in (auction.features or [])
                if i.featureOf == 'auctioner' or i.featureOf == 'lot' and i.relatedItem == lot.id or i.featureOf == 'item' and i.relatedItem in lot_items
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
                for bid in auction.bids
                if lot.id in [i.relatedLot for i in bid.lotValues]
            ]
            if not bids:
                lot.status = 'unsuccessful'
                statuses.add('unsuccessful')
                continue
            unsuccessful_awards = [i.bid_id for i in lot_awards if i.status == 'unsuccessful']
            bids = chef(bids, features, unsuccessful_awards, True)
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
                auction.awards.append(award)
                request.response.headers['Location'] = request.route_url('Auction Awards', auction_id=auction.id, award_id=award['id'])
                statuses.add('pending')
            else:
                statuses.add('unsuccessful')
        if statuses.difference(set(['unsuccessful', 'active'])):
            auction.awardPeriod.endDate = None
            auction.status = 'active.qualification'
        else:
            auction.awardPeriod.endDate = now
            auction.status = 'active.awarded'
    else:
        if not auction.awards or auction.awards[-1].status not in ['pending', 'active']:
            unsuccessful_awards = [i.bid_id for i in auction.awards if i.status == 'unsuccessful']
            bids = chef(auction.bids, auction.features or [], unsuccessful_awards, True)
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
                auction.awards.append(award)
                request.response.headers['Location'] = request.route_url('Auction Awards', auction_id=auction.id, award_id=award['id'])
        if auction.awards[-1].status == 'pending':
            auction.awardPeriod.endDate = None
            auction.status = 'active.qualification'
        else:
            auction.awardPeriod.endDate = now
            auction.status = 'active.awarded'


def request_params(request):
    try:
        params = NestedMultiDict(request.GET, request.POST)
    except UnicodeDecodeError:
        request.errors.add('body', 'data', 'could not decode params')
        request.errors.status = 422
        raise error_handler(request.errors, False)
    except Exception, e:
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
    if 'auction' in errors.request.validated:
        params['AUCTION_REV'] = errors.request.validated['auction'].rev
        params['AUCTIONID'] = errors.request.validated['auction'].auctionID
        params['AUCTION_STATUS'] = errors.request.validated['auction'].status
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
        'AUCTIONS_API_VERSION': VERSION,
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
        'AUCTION_ID': '',
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
    if 'auction' in request.validated:
        params['AUCTION_REV'] = request.validated['auction'].rev
        params['AUCTIONID'] = request.validated['auction'].auctionID
        params['AUCTION_STATUS'] = request.validated['auction'].status
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


def extract_auction_adapter(request, auction_id):
    db = request.registry.db
    doc = db.get(auction_id)
    if doc is None:
        request.errors.add('url', 'auction_id', 'Not Found')
        request.errors.status = 404
        raise error_handler(request.errors)

    return request.auction_from_data(doc)


def extract_auction(request):
    try:
        # empty if mounted under a path in mod_wsgi, for example
        path = decode_path_info(request.environ['PATH_INFO'] or '/')
    except KeyError:
        path = '/'
    except UnicodeDecodeError as e:
        raise URLDecodeError(e.encoding, e.object, e.start, e.end, e.reason)

    auction_id = ""
    # extract auction id
    parts = path.split('/')
    if len(parts) < 4 or parts[3] != 'auctions':
        return

    auction_id = parts[4]
    return extract_auction_adapter(request, auction_id)


class isAuction(object):
    def __init__(self, val, config):
        self.val = val

    def text(self):
        return 'procurementMethodType = %s' % (self.val,)

    phash = text

    def __call__(self, context, request):
        if request.auction is not None:
            return getattr(request.auction, 'procurementMethodType', None) == self.val
        return False


def set_renderer(event):
    request = event.request
    try:
        json = request.json_body
    except ValueError:
        json = {}
    pretty = isinstance(json, dict) and json.get('options', {}).get('pretty') or request.params.get('opt_pretty')
    jsonp = request.params.get('opt_jsonp')
    if jsonp and pretty:
        request.override_renderer = 'prettyjsonp'
        return True
    if jsonp:
        request.override_renderer = 'jsonp'
        return True
    if pretty:
        request.override_renderer = 'prettyjson'
        return True


def fix_url(item, app_url):
    if isinstance(item, list):
        [
            fix_url(i, app_url)
            for i in item
            if isinstance(i, dict) or isinstance(i, list)
        ]
    elif isinstance(item, dict):
        if "format" in item and "url" in item and '?download=' in item['url']:
            path = item["url"] if item["url"].startswith('/auctions') else '/auctions' + item['url'].split('/auctions', 1)[1]
            item["url"] = app_url + ROUTE_PREFIX + path
            return
        [
            fix_url(item[i], app_url)
            for i in item
            if isinstance(item[i], dict) or isinstance(item[i], list)
        ]


def beforerender(event):
    if event.rendering_val and 'data' in event.rendering_val:
        fix_url(event.rendering_val['data'], event['request'].application_url)


def register_auction_procurementMethodType(config, model):
    """Register a auction procurementMethodType.
    :param config:
        The pyramid configuration object that will be populated.
    :param model:
        The auction model class
    """
    config.registry.auction_procurementMethodTypes[model.procurementMethodType.default] = model


def auction_from_data(request, data, raise_error=True, create=True):
    procurementMethodType = data.get('procurementMethodType', 'belowThreshold')
    model = request.registry.auction_procurementMethodTypes.get(procurementMethodType)
    if model is None and raise_error:
        request.errors.add('data', 'procurementMethodType', 'Not implemented')
        request.errors.status = 415
        raise error_handler(request.errors)
    if model is not None and create:
        model = model(data)
    return model
