# -*- coding: utf-8 -*-
from functools import partial
from hashlib import sha512
from logging import getLogger

from cornice.resource import resource
from schematics.exceptions import ModelValidationError

from openprocurement.api.plugins.transferring.traversal import factory
from openprocurement.api.plugins.transferring.models import Transfer
from openprocurement.api.utils import error_handler, context_unpack, get_now


transferresource = partial(resource, error_handler=error_handler,
                           factory=factory)

LOGGER = getLogger(__name__)


def extract_transfer(request, transfer_id=None):
    """ Extract transfer from db
    :param request:
    :param transfer_id: uuid4
    :return: transfer as Transfer instance or raise 404
    """
    db = request.registry.db
    if not transfer_id:
        transfer_id = request.matchdict['transfer_id']
    doc = db.get(transfer_id)
    if doc is None or doc.get('doc_type') != 'Transfer':
        request.errors.add('url', 'transfer_id', 'Not Found')
        request.errors.status = 404
        raise error_handler(request)

    return request.transfer_from_data(doc)


def transfer_from_data(request, data): #pylint: disable=unused-argument
    """ Convert transfer from dict into Transfer instance
    :param request:
    :param data: transfer as dict
    :return: transfer as Transfer instance
    """
    return Transfer(data)


def save_transfer(request):
    """ Save transfer object to database
    :param request:
    :return: True if Ok
    """
    transfer = request.validated['transfer']
    transfer.date = get_now()
    try:
        transfer.store(request.registry.db)
    except ModelValidationError, err:  # pragma: no cover
        for i in err.message:
            request.errors.add('body', i, err.message[i])
        request.errors.status = 422
    except Exception, err:  # pragma: no cover
        request.errors.add('body', 'data', str(err))
    else:
        LOGGER.info(
            'Saved transfer %s: at %s', transfer.id, get_now().isoformat(),
            extra=context_unpack(request, {'MESSAGE_ID': 'save_transfer'})
        )
        return True


def set_ownership(item, request, access_token=None, transfer_token=None):
    item.owner = request.authenticated_userid
    item.access_token = sha512(access_token).hexdigest()
    item.transfer_token = sha512(transfer_token).hexdigest()


def update_ownership(auction, transfer):
    auction.owner = transfer.owner
    auction.owner_token = transfer.access_token
    auction.transfer_token = transfer.transfer_token


def change_ownership(request, location):
    """ Change ownership for item in request.context
    :param request:
    :param location: location of item
    :return: True if OK
    """
    data = request.validated['ownership_data']
    if request.context.transfer_token == \
            sha512(data.get('transfer', '')).hexdigest():

        transfer = extract_transfer(request, transfer_id=data['id'])
        if transfer.get('usedFor') and transfer.get('usedFor') != location:
            request.errors.add('body', 'transfer', 'Transfer already used')
            request.errors.status = 403
            return
    else:
        request.errors.add('body', 'transfer', 'Invalid transfer')
        request.errors.status = 403
        return

    update_ownership(request.context, transfer)

    transfer.usedFor = location
    request.validated['transfer'] = transfer
    if save_transfer(request):
        LOGGER.info(
            'Updated transfer relation {}'.format(transfer.id),
            extra=context_unpack(
                request, {'MESSAGE_ID': 'transfer_relation_update'}
            )
        )
        return True
