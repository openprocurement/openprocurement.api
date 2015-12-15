# -*- coding: utf-8 -*-
import binascii
from pyramid.authentication import BasicAuthAuthenticationPolicy, b64decode
from ConfigParser import ConfigParser


class AuthenticationPolicy(BasicAuthAuthenticationPolicy):
    def __init__(self, auth_file, realm='OpenProcurement', debug=False):
        self.realm = realm
        self.debug = debug
        config = ConfigParser()
        config.read(auth_file)
        self.users = {}
        for i in config.sections():
            self.users.update(dict([
                (k, {'name': j, 'group': i})
                for j, k in config.items(i)
            ]))

    def unauthenticated_userid(self, request):
        """ The userid parsed from the ``Authorization`` request header."""
        token = self._get_credentials(request)
        if token:
            user = self.users.get(token)
            if user:
                return user['name']

    def check(self, user, group, request):
        token = request.params.get('acc_token')
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
                    return ['g:{}'.format(group)]
        return ['g:{}'.format(group), '{}_{}'.format(user, token)]

    def callback(self, username, request):
        # Username arg is ignored.  Unfortunately _get_credentials winds up
        # getting called twice when authenticated_userid is called.  Avoiding
        # that, however, winds up duplicating logic from the superclass.
        token = self._get_credentials(request)
        if token:
            user = self.users.get(token)
            if user:
                return self.check(user['name'], user['group'], request)

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
            roles = location.__local_roles__
        except AttributeError:
            continue
        if roles and callable(roles):
            roles = roles()
        break
    return roles


def authenticated_role(request):
    principals = request.effective_principals
    if hasattr(request, 'context'):
        roles = get_local_roles(request.context)
        local_roles = [roles[i] for i in reversed(principals) if i in roles]
        if local_roles:
            return local_roles[0]
    groups = [g for g in reversed(principals) if g.startswith('g:')]
    return groups[0][2:] if groups else 'anonymous'
