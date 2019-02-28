from collections import namedtuple

from openprocurement.api.validation import validate_json_data


Auth = namedtuple('Auth', ['role', 'user_id'])


Event = namedtuple(
    'Event',
    [
        'context',      # the data from the DB
        'auth',         # Auth
        'data',         # data that request brings
    ]
)


def build_event(request, data):
    """Exctract fields from request that will be need for further work and build Event"""
    auth = Auth(role=request.authenticated_role, user_id=request.authenticated_userid)
    request.event = Event(request.context, auth, data)


def validate_data_to_event(request, *args, **kwargs):
    """Checks request data general validity"""
    data = validate_json_data(request, leave_json_data_into_request=False)
    build_event(request, data)
