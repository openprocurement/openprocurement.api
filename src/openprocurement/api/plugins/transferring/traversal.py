# -*- coding: utf-8 -*-
from openprocurement.api.traversal import Root as BaseRoot

from pyramid.security import ALL_PERMISSIONS, Allow  # , Everyone


class Root(BaseRoot):

    __acl__ = [
        # (Allow, Everyone, 'view_transfer'),
        (Allow, 'g:brokers', 'view_transfer'),
        (Allow, 'g:brokers', 'create_transfer'),
        (Allow, 'g:admins', ALL_PERMISSIONS),
    ]


def factory(request):
    root = Root(request)
    if not request.matchdict or not request.matchdict.get('transfer_id'):
        return root
    request.validated['transfer_id'] = request.matchdict['transfer_id']
    transfer = request.transfer
    transfer.__parent__ = root
    request.validated['transfer'] = transfer
    request.validated['id'] = request.matchdict['transfer_id']
    return transfer
