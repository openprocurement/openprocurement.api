# -*- coding: utf-8 -*-
from openprocurement.api.models import TenderDocument, Bid, Award, Document, Question, Complaint
from schematics.exceptions import ModelValidationError, ModelConversionError


def validate_data(request, model, partial=False):
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
    data = json['data']
    try:
        model(data).validate(partial=partial)
    except (ModelValidationError, ModelConversionError), e:
        for i in e.message:
            request.errors.add('body', i, e.message[i])
        request.errors.status = 422
    request.validated['data'] = data
    return data


def validate_tender_data(request):
    return validate_data(request, TenderDocument)


def validate_patch_tender_data(request):
    return validate_data(request, TenderDocument, True)


def validate_tender_auction_data(request):
    data = validate_patch_tender_data(request)
    tender = validate_tender_exists_by_tender_id(request)
    if data is None or not tender:
        return
    if tender.status != 'auction':
        request.errors.add('body', 'data', 'Can\'t report auction results in current tender status')
        request.errors.status = 403
        return
    bids = data.get('bids', [])
    tender_bids_ids = [i.id for i in tender.bids]
    if len(bids) != len(tender.bids):
        request.errors.add('body', 'bids', "Number of auction results did not match the number of tender bids")
        request.errors.status = 422
    elif not all(['id' in i for i in bids]):
        request.errors.add('body', 'bids', "Results of auction bids should contains id of bid")
        request.errors.status = 422
    elif set([i['id'] for i in bids]) != set(tender_bids_ids):
        request.errors.add('body', 'bids', "Auction bids should be identical to the tender bids")
        request.errors.status = 422


def validate_bid_data(request):
    return validate_data(request, Bid)


def validate_patch_bid_data(request):
    return validate_data(request, Bid, True)


def validate_award_data(request):
    return validate_data(request, Award)


def validate_patch_document_data(request):
    return validate_data(request, Document, True)


def validate_question_data(request):
    return validate_data(request, Question)


def validate_patch_question_data(request):
    return validate_data(request, Question, True)


def validate_complaint_data(request):
    return validate_data(request, Complaint)


def validate_patch_complaint_data(request):
    return validate_data(request, Complaint, True)


def validate_tender_exists(request, key='id'):
    tender = request.matchdict.get(key) and TenderDocument.load(request.registry.db, request.matchdict[key])
    if tender:
        request.validated[key] = request.matchdict[key]
        request.validated['tender'] = tender
        return tender
    else:
        request.errors.add('url', key, 'Not Found')
        request.errors.status = 404


def validate_tender_exists_by_tender_id(request):
    return validate_tender_exists(request, 'tender_id')


def validate_tender_document_exists(request):
    tender = validate_tender_exists(request, 'tender_id')
    if tender:
        documents = [i for i in tender.documents if i.id == request.matchdict['id']]
        if not documents:
            request.errors.add('url', 'id', 'Not Found')
            request.errors.status = 404
        else:
            request.validated['id'] = request.matchdict['id']
            request.validated['documents'] = documents
            request.validated['document'] = documents[-1]


def validate_tender_bid_exists(request, key='id'):
    tender = validate_tender_exists(request, 'tender_id')
    if tender:
        bids = [i for i in tender.bids if i.id == request.matchdict[key]]
        if bids:
            request.validated[key] = request.matchdict[key]
            request.validated['bids'] = bids
            bid = bids[0]
            request.validated['bid'] = bid
            return bid
        else:
            request.errors.add('url', key, 'Not Found')
            request.errors.status = 404


def validate_tender_bid_exists_by_bid_id(request):
    return validate_tender_bid_exists(request, 'bid_id')


def validate_tender_bid_document_exists(request):
    bid = validate_tender_bid_exists(request, 'bid_id')
    if bid:
        documents = [i for i in bid.documents if i.id == request.matchdict['id']]
        if not documents:
            request.errors.add('url', 'id', 'Not Found')
            request.errors.status = 404
        else:
            request.validated['id'] = request.matchdict['id']
            request.validated['documents'] = documents
            request.validated['document'] = documents[-1]


def validate_tender_question_exists(request, key='id'):
    tender = validate_tender_exists(request, 'tender_id')
    if tender:
        questions = [i for i in tender.questions if i.id == request.matchdict[key]]
        if questions:
            request.validated[key] = request.matchdict[key]
            request.validated['questions'] = questions
            question = questions[0]
            request.validated['question'] = question
            return question
        else:
            request.errors.add('url', key, 'Not Found')
            request.errors.status = 404


def validate_tender_complaint_exists(request, key='id'):
    tender = validate_tender_exists(request, 'tender_id')
    if tender:
        complaints = [i for i in tender.complaints if i.id == request.matchdict[key]]
        if complaints:
            request.validated[key] = request.matchdict[key]
            request.validated['complaints'] = complaints
            complaint = complaints[0]
            request.validated['complaint'] = complaint
            return complaint
        else:
            request.errors.add('url', key, 'Not Found')
            request.errors.status = 404


def validate_file_upload(request):
    if 'file' not in request.POST:
        request.errors.add('body', 'file', 'Not Found')
        request.errors.status = 404
    else:
        request.validated['file'] = request.POST['file']


def validate_file_update(request):
    if request.content_type == 'multipart/form-data':
        validate_file_upload(request)
