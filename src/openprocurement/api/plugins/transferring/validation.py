# -*- coding: utf-8 -*-
from openprocurement.api.utils import update_logging_context
from openprocurement.api.validation import validate_json_data, validate_data
from openprocurement.api.plugins.transferring.models import Transfer


def validate_transfer_data(request, **kwargs):  # pylint: disable=unused-argument

    update_logging_context(request, {'transfer_id': '__new__'})
    data = validate_json_data(request)
    if data is None:
        return
    model = Transfer
    return validate_data(request, model, 'transfer', data=data)


def validate_set_or_change_ownership_data(request, **kwargs):  # pylint: disable=unused-argument
    if request.errors:
        # do not run validation if some errors are already detected
        return
    data = validate_json_data(request)
    fields_set = set(['id', 'transfer', 'auction_token'])
    request_set = set([field for field in fields_set if data.get(field)])
    if not data.get('id'):
        request.errors.add('body', 'id', 'This field is required.')

    if len(fields_set.difference(request_set)) != 1:
        err = 'Request must contain either "id and transfer" or "id and auction_token".'
        request.errors.add('body', 'name', err)

    if request.errors:
        request.errors.status = 422
        return
    request.validated['ownership_data'] = data


def validate_ownership_data(request, **kwargs):  # pylint: disable=unused-argument
    if request.errors:
        # do not run validation if some errors are already detected
        return
    data = validate_json_data(request)

    for field in ['id', 'transfer']:
        if not data.get(field):
            request.errors.add('body', field, 'This field is required.')
    if request.errors:
        request.errors.status = 422
        return
    request.validated['ownership_data'] = data


def validate_accreditation_level(request, auction, level_name):
    level = getattr(type(auction), level_name)
    if not request.check_accreditation(level):
        err = 'Broker Accreditation level does not permit ownership change'
        request.errors.add('body', 'data', err)
        request.errors.status = 403
        return

    if auction.get('mode', None) is None and request.check_accreditation('t'):
        err = 'Broker Accreditation level does not permit ownership change'
        request.errors.add('body', 'data', err)
        request.errors.status = 403
        return


def validate_auction_accreditation_level(request, **kwargs):  # pylint: disable=unused-argument
    if hasattr(request.validated['auction'], 'transfer_accreditation'):
        predicate = 'transfer_accreditation'
    else:
        predicate = 'create_accreditation'
    validate_accreditation_level(request, request.validated['auction'], predicate)


def validate_bid_accreditation_level(request):
    validate_accreditation_level(request, request.validated['auction'], 'edit_accreditation')


def validate_contract_accreditation_level(request):
    validate_accreditation_level(request, request.validated['contract'], 'create_accreditation')


validate_complaint_accreditation_level = validate_bid_accreditation_level
