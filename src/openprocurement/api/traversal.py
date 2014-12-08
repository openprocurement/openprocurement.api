# -*- coding: utf-8 -*-

from openprocurement.api.models import Tender
from pyramid.security import (
    ALL_PERMISSIONS,
    Allow,
    Authenticated,
    Everyone,
)


class Root(object):
    __name__ = None
    __parent__ = None
    __acl__ = [
        (Allow, Everyone, ALL_PERMISSIONS),
        (Allow, Authenticated, 'view_tenders'),
        (Allow, Authenticated, 'create_tender'),
        (Allow, 'auction', 'auction'),
        (Allow, 'chronograph', 'edit_tender'),
        (Allow, 'chronograph', 'view_tender'),
        (Allow, 'g:admins', ALL_PERMISSIONS),
    ]

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db


def get_item(parent, key, request, root):
    request.validated['{}_id'.format(key)] = request.matchdict['{}_id'.format(key)]
    items = [i for i in getattr(parent, '{}s'.format(key), []) if i.id == request.matchdict['{}_id'.format(key)]]
    if not items:
        request.errors.add('url', '{}_id'.format(key), 'Not Found')
        request.errors.status = 404
        return root
    else:
        request.validated['{}s'.format(key)] = items
        item = items[-1]
        request.validated[key] = item
        request.validated['id'] = request.matchdict['{}_id'.format(key)]
        item.__parent__ = parent
        return item


def factory(request):
    root = Root(request)
    if not request.matchdict.get('tender_id'):
        return root
    request.validated['tender_id'] = request.matchdict['tender_id']
    tender = Tender.load(root.db, request.matchdict['tender_id'])
    if not tender:
        request.errors.add('url', 'tender_id', 'Not Found')
        request.errors.status = 404
        return root
    tender.__parent__ = root
    request.validated['tender'] = tender
    if request.matchdict.get('award_id'):
        award = get_item(tender, 'award', request, root)
        if award == root:
            return root
        elif request.matchdict.get('complaint_id'):
            complaint = get_item(award, 'complaint', request, root)
            if complaint == root:
                return root
            elif request.matchdict.get('document_id'):
                return get_item(complaint, 'document', request, root)
            else:
                return complaint
        elif request.matchdict.get('document_id'):
            return get_item(award, 'document', request, root)
        else:
            return award
    elif request.matchdict.get('bid_id'):
        bid = get_item(tender, 'bid', request, root)
        if bid == root:
            return root
        elif request.matchdict.get('document_id'):
            return get_item(bid, 'document', request, root)
        else:
            return bid
    elif request.matchdict.get('complaint_id'):
        complaint = get_item(tender, 'complaint', request, root)
        if complaint == root:
            return root
        elif request.matchdict.get('document_id'):
            return get_item(complaint, 'document', request, root)
        else:
            return complaint
    elif request.matchdict.get('document_id'):
        return get_item(tender, 'document', request, root)
    elif request.matchdict.get('question_id'):
        return get_item(tender, 'question', request, root)
    request.validated['id'] = request.matchdict['tender_id']
    return tender
