# -*- coding: utf-8 -*-
from openprocurement.api.utils.searchers import search_root_model
from openprocurement.api.utils.context_provider import ContextProvider
from openprocurement.api.validation import validate_json_data
from openprocurement.api.models.schematics_extender import Model
from openprocurement.api.constants import ACCREDITATION_REGEX_IN_EFFECTIVE_PRINCIPALS


class AuthData(object):

    def __init__(self, user_id, role, accreditations):
        self.user_id = user_id
        self.role = role
        self.accreditations = accreditations


class Event(object):

    def __init__(self, context, auth_data, data):
        self.ctx = context
        self.auth = auth_data
        self.data = data


def build_event(request, data):
    """Exctract fields from request that will be need for further work and build Event"""
    accreditations = extract_accreditation_levels_from_request(request)
    auth = AuthData(request.authenticated_userid, request.authenticated_role, accreditations)
    low_ctx = request.context
    high_ctx = search_root_model(low_ctx)

    ctx = ContextProvider(high_ctx, low_ctx)
    ctx.cache.high_data_plain = high_ctx.serialize('plain') if isinstance(high_ctx, Model) else {}
    request.event = Event(ctx, auth, data)


def extract_accreditation_levels_from_request(request):
    principals = request.effective_principals
    accreditations = []
    # accreditation is stored in a string, not in some pyramid's auth subclass
    principals_as_str = (p for p in principals if type(p) is str)

    for p in principals_as_str:
        regex_result = ACCREDITATION_REGEX_IN_EFFECTIVE_PRINCIPALS.match(p)
        if not regex_result:  # regex_result will be equal to None if nothing was found
            continue
        found_accreditation_level = regex_result.group('level')
        found_accreditation_level = int(found_accreditation_level)
        accreditations.append(found_accreditation_level)

    return accreditations


def validate_data_to_event(request, *args, **kwargs):
    """Checks request data general validity"""
    data = validate_json_data(request, leave_json_data_into_request=False)
    build_event(request, data)
