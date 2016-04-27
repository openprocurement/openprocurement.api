# -*- coding: utf-8 -*-

from pyramid.security import (
    ALL_PERMISSIONS,
    Allow,
    Deny,
    Everyone,
)


class Root(object):
    __name__ = None
    __parent__ = None
    __acl__ = [
        # (Allow, Everyone, ALL_PERMISSIONS),
        (Allow, Everyone, 'view_tender'),
        (Deny, 'broker05', 'create_bid'),
        (Deny, 'broker05', 'create_complaint'),
        (Deny, 'broker05', 'create_question'),
        (Deny, 'broker05', 'create_tender'),
        (Allow, 'g:brokers', 'create_bid'),
        (Allow, 'g:brokers', 'create_complaint'),
        (Allow, 'g:brokers', 'create_question'),
        (Allow, 'g:brokers', 'create_tender'),
        (Allow, 'g:auction', 'auction'),
        (Allow, 'g:auction', 'upload_tender_documents'),
        (Allow, 'g:contracting', 'extract_credentials'),
        (Allow, 'g:chronograph', 'edit_tender'),
        (Allow, 'g:Administrator', 'edit_tender'),
        (Allow, 'g:Administrator', 'edit_bid'),
        (Allow, 'g:admins', ALL_PERMISSIONS),
    ]

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db


def get_item(parent, key, request):
    request.validated['{}_id'.format(key)] = request.matchdict['{}_id'.format(key)]
    items = [i for i in getattr(parent, '{}s'.format(key), []) if i.id == request.matchdict['{}_id'.format(key)]]
    if not items:
        from openprocurement.api.utils import error_handler
        request.errors.add('url', '{}_id'.format(key), 'Not Found')
        request.errors.status = 404
        raise error_handler(request.errors)
    else:
        if key == 'document':
            request.validated['{}s'.format(key)] = items
        item = items[-1]
        request.validated[key] = item
        request.validated['id'] = request.matchdict['{}_id'.format(key)]
        item.__parent__ = parent
        return item


def factory(request):
    request.validated['tender_src'] = {}
    root = Root(request)
    if not request.matchdict or not request.matchdict.get('tender_id'):
        return root
    request.validated['tender_id'] = request.matchdict['tender_id']
    tender = request.tender
    tender.__parent__ = root
    request.validated['tender'] = tender
    request.validated['tender_status'] = tender.status
    if request.method != 'GET':
        request.validated['tender_src'] = tender.serialize('plain')
        if tender._initial.get('next_check'):
            request.validated['tender_src']['next_check'] = tender._initial.get('next_check')
    if request.matchdict.get('award_id'):
        award = get_item(tender, 'award', request)
        if request.matchdict.get('complaint_id'):
            complaint = get_item(award, 'complaint', request)
            if request.matchdict.get('document_id'):
                return get_item(complaint, 'document', request)
            else:
                return complaint
        elif request.matchdict.get('document_id'):
            return get_item(award, 'document', request)
        else:
            return award
    elif request.matchdict.get('contract_id'):
        contract = get_item(tender, 'contract', request)
        if request.matchdict.get('document_id'):
            return get_item(contract, 'document', request)
        else:
            return contract
    elif request.matchdict.get('bid_id'):
        bid = get_item(tender, 'bid', request)
        if request.matchdict.get('document_id'):
            return get_item(bid, 'document', request)
        else:
            return bid
    elif request.matchdict.get('complaint_id'):
        complaint = get_item(tender, 'complaint', request)
        if request.matchdict.get('document_id'):
            return get_item(complaint, 'document', request)
        else:
            return complaint
    elif request.matchdict.get('cancellation_id'):
        cancellation = get_item(tender, 'cancellation', request)
        if request.matchdict.get('document_id'):
            return get_item(cancellation, 'document', request)
        else:
            return cancellation
    elif request.matchdict.get('document_id'):
        return get_item(tender, 'document', request)
    elif request.matchdict.get('question_id'):
        return get_item(tender, 'question', request)
    elif request.matchdict.get('lot_id'):
        return get_item(tender, 'lot', request)
    request.validated['id'] = request.matchdict['tender_id']
    return tender
