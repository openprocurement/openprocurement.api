# -*- coding: utf-8 -*-
from openprocurement.api.models import Award, Document, Question, Complaint, Contract, Cancellation, Lot, get_now
from schematics.exceptions import ModelValidationError, ModelConversionError
from openprocurement.api.utils import apply_data_patch, update_logging_context


def validate_json_data(request):
    try:
        json = request.json_body
    except ValueError, e:
        request.errors.add('body', 'data', e.message)
        request.errors.status = 422
        return
    if not isinstance(json, dict) or 'data' not in json or not isinstance(json.get('data'), dict):
        request.errors.add('body', 'data', "Data not available")
        request.errors.status = 422
        return
    return json['data']


def validate_data(request, model, partial=False, data=None):
    if data is None:
        data = validate_json_data(request)
    if data is None:
        return
    try:
        if partial and isinstance(request.context, model):
            initial_data = request.context.serialize()
            m = model(initial_data)
            new_patch = apply_data_patch(initial_data, data)
            m.import_data(new_patch, partial=True, strict=True)
            m.__parent__ = request.context.__parent__
            m.validate()
            role = request.context.get_role()
            method = m.to_patch
        else:
            m = model(data)
            m.__parent__ = request.context
            m.validate()
            method = m.serialize
            role = 'create'
    except (ModelValidationError, ModelConversionError), e:
        for i in e.message:
            request.errors.add('body', i, e.message[i])
        request.errors.status = 422
        data = None
    except ValueError, e:
        request.errors.add('body', 'data', e.message)
        request.errors.status = 422
        data = None
    else:
        if hasattr(m.__class__, '_options') and role not in m.__class__._options.roles:
            request.errors.add('url', 'role', 'Forbidden')
            request.errors.status = 403
            data = None
        else:
            data = method(role)
            request.validated['data'] = data
            if not partial:
                m = model(data)
                m.__parent__ = request.context
                request.validated[model.__name__.lower()] = m
    return data


def validate_tender_data(request):
    update_logging_context(request, {'tender_id': '__new__'})

    data = validate_json_data(request)
    if data is None:
        return

    model = request.tender_from_data(data, create=False)
    return validate_data(request, model, data=data)


def validate_patch_tender_data(request):
    return validate_data(request, request.tender.__class__, True)


def validate_tender_auction_data(request):
    data = validate_patch_tender_data(request)
    tender = request.validated['tender']
    if tender.status != 'active.auction':
        request.errors.add('body', 'data', 'Can\'t {} in current ({}) tender status'.format('report auction results' if request.method == 'POST' else 'update auction urls', tender.status))
        request.errors.status = 403
        return
    lot_id = request.matchdict.get('auction_lot_id')
    if tender.lots and any([i.status != 'active' for i in tender.lots if i.id == lot_id]):
        request.errors.add('body', 'data', 'Can {} only in active lot status'.format('report auction results' if request.method == 'POST' else 'update auction urls'))
        request.errors.status = 403
        return
    if data is not None:
        bids = data.get('bids', [])
        tender_bids_ids = [i.id for i in tender.bids]
        if len(bids) != len(tender.bids):
            request.errors.add('body', 'bids', "Number of auction results did not match the number of tender bids")
            request.errors.status = 422
            return
        if set([i['id'] for i in bids]) != set(tender_bids_ids):
            request.errors.add('body', 'bids', "Auction bids should be identical to the tender bids")
            request.errors.status = 422
            return
        data['bids'] = [x for (y, x) in sorted(zip([tender_bids_ids.index(i['id']) for i in bids], bids))]
        if data.get('lots'):
            tender_lots_ids = [i.id for i in tender.lots]
            if len(data.get('lots', [])) != len(tender.lots):
                request.errors.add('body', 'lots', "Number of lots did not match the number of tender lots")
                request.errors.status = 422
                return
            if set([i['id'] for i in data.get('lots', [])]) != set([i.id for i in tender.lots]):
                request.errors.add('body', 'lots', "Auction lots should be identical to the tender lots")
                request.errors.status = 422
                return
            data['lots'] = [
                x if x['id'] == lot_id else {}
                for (y, x) in sorted(zip([tender_lots_ids.index(i['id']) for i in data.get('lots', [])], data.get('lots', [])))
            ]
        tender_bids_lots_ids = dict([(i.id, [j['relatedLot'] for j in i.lotValues]) for i in tender.bids])
        if tender.lots and any([len(bid['lotValues']) != len(tender_bids_lots_ids.get(bid['id'], [])) for bid in bids]):
            request.errors.add('body', 'bids', [{u'lotValues': [u'Number of lots of auction results did not match the number of tender lots']}])
            request.errors.status = 422
            return
        if tender.lots and any([set([j['relatedLot'] for j in bid['lotValues']]) != set(tender_bids_lots_ids[bid['id']]) for bid in bids]):
            request.errors.add('body', 'bids', [{u'lotValues': [{u'relatedLot': ['relatedLot should be one of lots of bid']}]}])
            request.errors.status = 422
            return
        for bid in data['bids']:
            if 'lotValues' in bid:
                bid['lotValues'] = [
                    x if x['relatedLot'] == lot_id else {}
                    for (y, x) in sorted(zip([tender_bids_lots_ids[bid['id']].index(i['relatedLot']) for i in bid['lotValues']], bid['lotValues']))
                ]
    else:
        data = {}
    if request.method == 'POST':
        now = get_now().isoformat()
        if tender.lots:
            data['lots'] = [{'auctionPeriod': {'endDate': now}} if i.id == lot_id else {} for i in tender.lots]
        else:
            data['auctionPeriod'] = {'endDate': now}
    request.validated['data'] = data


def validate_bid_data(request):
    update_logging_context(request, {'bid_id': '__new__'})
    model = request.tender.__class__.bids.model_class
    return validate_data(request, model)


def validate_patch_bid_data(request):
    model = request.tender.__class__.bids.model_class
    return validate_data(request, model, True)


def validate_award_data(request):
    update_logging_context(request, {'award_id': '__new__'})
    model = request.tender.__class__.awards.model_class
    return validate_data(request, model)


def validate_patch_award_data(request):
    model = request.tender.__class__.awards.model_class
    return validate_data(request, model, True)


def validate_patch_document_data(request):
    return validate_data(request, Document, True)


def validate_question_data(request):
    update_logging_context(request, {'question_id': '__new__'})
    model = request.tender.__class__.questions.model_class
    return validate_data(request, model)


def validate_patch_question_data(request):
    model = request.tender.__class__.questions.model_class
    return validate_data(request, model, True)


def validate_complaint_data(request):
    update_logging_context(request, {'complaint_id': '__new__'})
    model = request.tender.__class__.complaints.model_class
    return validate_data(request, model)


def validate_patch_complaint_data(request):
    model = request.tender.__class__.complaints.model_class
    return validate_data(request, model, True)


def validate_cancellation_data(request):
    update_logging_context(request, {'cancellation_id': '__new__'})
    model = request.tender.__class__.cancellations.model_class
    return validate_data(request, model)


def validate_patch_cancellation_data(request):
    model = request.tender.__class__.cancellations.model_class
    return validate_data(request, model, True)


def validate_contract_data(request):
    update_logging_context(request, {'contract_id': '__new__'})
    model = request.tender.__class__.contracts.model_class
    return validate_data(request, model)


def validate_patch_contract_data(request):
    model = request.tender.__class__.contracts.model_class
    return validate_data(request, model, True)


def validate_lot_data(request):
    update_logging_context(request, {'lot_id': '__new__'})
    model = request.tender.__class__.lots.model_class
    return validate_data(request, model)


def validate_patch_lot_data(request):
    model = request.tender.__class__.lots.model_class
    return validate_data(request, model, True)


def validate_file_upload(request):
    update_logging_context(request, {'document_id': '__new__'})
    if 'file' not in request.POST or not hasattr(request.POST['file'], 'filename'):
        request.errors.add('body', 'file', 'Not Found')
        request.errors.status = 404
    else:
        request.validated['file'] = request.POST['file']


def validate_file_update(request):
    if request.content_type == 'multipart/form-data':
        validate_file_upload(request)
