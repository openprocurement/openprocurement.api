# -*- coding: utf-8 -*-
import binascii
from hashlib import sha512
from pyramid.authentication import BasicAuthAuthenticationPolicy, b64decode
from ConfigParser import ConfigParser

GROUP_PREFIX = 'g:'
LEVEL_PREFIX = 'a:'
OPERATOR_PREFIX = 'operator:'


class AuthenticationPolicy(BasicAuthAuthenticationPolicy):
    def __init__(self, auth_file, realm='OpenProcurement', debug=False):
        self.realm = realm
        self.debug = debug
        config = ConfigParser()
        config.read(auth_file)
        self.users = {}
        for i in config.sections():
            if config.has_option(i, 'token'):
                self.users.update({config.get(i, 'token'): {
                    'name': i,
                    'level': config.get(i, 'level') if config.has_option(i, 'level') else '1234',
                    'operator': config.get(i, 'operator') if config.has_option(i, 'operator') else 'UA',
                    'group': config.get(i, 'group') if config.has_option(i, 'group') else 'brokers'
                }})
        self.operators = dict(config.items('operators')) if config.has_section('operators') else {}

    def unauthenticated_userid(self, request):
        """ The userid parsed from the ``Authorization`` request header."""
        token = self._get_credentials(request)
        if token:
            user = self.users.get(token)
            if user:
                return user['name']

    def check(self, user, request):
        token = request.params.get('acc_token')
        auth_groups = ['{}{}'.format(GROUP_PREFIX, user['group'])]
        for i in user['level']:
            auth_groups.append('{}{}'.format(LEVEL_PREFIX, i))
        auth_groups.append('{}{}'.format(OPERATOR_PREFIX, user['operator']))
        if not token:
            token = request.headers.get('X-Access-Token')
            if not token:
                if request.method in ['POST', 'PUT', 'PATCH'] and request.content_type == 'application/json':
                    try:
                        json = request.json_body
                    except ValueError:
                        json = None
                    token = isinstance(json, dict) and json.get('access', {}).get('token')
                if not token:
                    return auth_groups
        auth_groups.append('{}_{}'.format(user['name'], token))
        auth_groups.append('{}_{}'.format(user['name'], sha512(token).hexdigest()))
        return auth_groups

    def callback(self, username, request):
        # Username arg is ignored.  Unfortunately _get_credentials winds up
        # getting called twice when authenticated_userid is called.  Avoiding
        # that, however, winds up duplicating logic from the superclass.
        token = self._get_credentials(request)
        if token:
            user = self.users.get(token)
            if user:
                return self.check(user, request)

    def _get_credentials(self, request):
        authorization = request.headers.get('Authorization')
        if not authorization:
            return None
        try:
            authmeth, auth = authorization.split(' ', 1)
        except ValueError:  # not enough values to unpack
            return None
        if authmeth.lower() == 'bearer':
            return auth
        if authmeth.lower() != 'basic':
            return None

        try:
            authbytes = b64decode(auth.strip())
        except (TypeError, binascii.Error):  # can't decode
            return None

        # try utf-8 first, then latin-1; see discussion in
        # https://github.com/Pylons/pyramid/issues/898
        try:
            auth = authbytes.decode('utf-8')
        except UnicodeDecodeError:  # pragma: no cover
            auth = authbytes.decode('latin-1')

        try:
            username, _ = auth.split(':', 1)
        except ValueError:  # not enough values to unpack
            return None
        return username


def get_local_roles(context):
    from pyramid.location import lineage
    roles = {}
    for location in lineage(context):
        try:
            local_roles = location.__local_roles__
        except AttributeError:
            continue
        if local_roles and callable(local_roles):
            local_roles = local_roles()
        roles.update(local_roles)
    return roles


def authenticated_role(request):
    principals = request.effective_principals
    if hasattr(request, 'context'):
        roles = get_local_roles(request.context)
        local_roles = [roles[i] for i in reversed(principals) if i in roles]
        if local_roles:
            return local_roles[0]
    groups = [g for g in reversed(principals) if g.startswith(GROUP_PREFIX)]
    return groups[0][2:] if groups else 'anonymous'


def check_accreditation(request, level):
    return "{}{}".format(LEVEL_PREFIX, level) in request.effective_principals


def get_operator(request):
    operator_principals = [
        i[len(OPERATOR_PREFIX):]
        for i in request.effective_principals
        if i.startswith(OPERATOR_PREFIX)
    ]
    return operator_principals[0] if operator_principals else ''


def get_prefix(request):
    operators = request._get_authentication_policy().operators
    return operators.get(request.operator, request.operator.upper())
