from collections import namedtuple

from openprocurement.api.utils.searchers import search_root_model
from openprocurement.api.utils.context_provider import ContextProvider
from openprocurement.api.validation import validate_json_data


class AuthData(object):

    def __init__(self, user_id, role):
        self.user_id = user_id
        self.role = role


class Event(object):

    def __init__(self, context, auth_data, data):
        self.ctx = context
        self.auth = auth_data
        self.data = data


def build_event(request, data):
    """Exctract fields from request that will be need for further work and build Event"""
    auth = AuthData(request.authenticated_userid, request.authenticated_role)
    low_ctx = request.context
    high_ctx = search_root_model(low_ctx)

    ctx = ContextProvider(high_ctx, low_ctx)
    if request.validated.get('global_ctx_plain'):
        ctx.cache.high_data_plain = request.validated['global_ctx_plain']
    request.event = Event(ctx, auth, data)


def validate_data_to_event(request, *args, **kwargs):
    """Checks request data general validity"""
    data = validate_json_data(request, leave_json_data_into_request=False)
    build_event(request, data)
