from collections import namedtuple

from openprocurement.api.validation import validate_json_data
from openprocurement.api.utils.base_data_engine import DataEngine


Auth = namedtuple('Auth', ['role', 'user_id'])


Event = namedtuple(
    'Event',
    [
        'context',      # the data from the DB
        'auth',         # Auth
        'data',         # data that request brings
    ]
)


class AuthData(object):

    def __init__(self, user_id, role):
        self.user_id = user_id
        self.role = role


class Event(object):

    def __init__(self, context, auth_data, data):
        self.context = context
        self.auth = auth_data
        self._data = data
        # read-only context; needed for save process
        self._ro_context = DataEngine.copy_model(context)


def build_event(request, data):
    """Exctract fields from request that will be need for further work and build Event"""
    auth = AuthData(request.authenticated_userid, request.authenticated_role)
    request.event = Event(request.context, auth, data)


def validate_data_to_event(request, *args, **kwargs):
    """Checks request data general validity"""
    data = validate_json_data(request, leave_json_data_into_request=False)
    build_event(request, data)
