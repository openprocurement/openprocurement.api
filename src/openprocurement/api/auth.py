# -*- coding: utf-8 -*-
import binascii
import os
import yaml
import json
from ConfigParser import ConfigParser
from collections import defaultdict
from copy import deepcopy
from hashlib import sha512
from logging import getLogger

from pyramid.authentication import BasicAuthAuthenticationPolicy, b64decode

from openprocurement.api.utils import (
    get_access_token_from_request,
    get_file_path
)
from openprocurement.api.constants import (
    ALL_ACCREDITATIONS_GRANTED,
    TEST_ACCREDITATION,
)

auth_mapping = {}


LOGGER = getLogger("{}.init".format(__name__))


def auth(auth_type=None):
    def decorator(func):
        auth_mapping[auth_type] = func
        return func
    return decorator


def get_path_to_auth(app_meta):
    conf_auth = app_meta.config.auth

    file_path = get_file_path(app_meta.here, conf_auth.src)
    if not os.path.isfile(file_path):
        raise IOError("Auth file '{}' was doesn`t exist".format(file_path))

    return file_path


def create_user_structure(group, name, info):
    """
    Create dictionary that contains information about user permissions and accreditaion level.

    :param group:
    :type group: str

    :param name: name of user
    :type name: str

    :param info: information about user is such structure:
        {
            'token': 'token',
            'levels': ['0', '1']
        }
    :type info: dict

    :return: user auth info dictionary with structure below
    {
        'token': {
            'name': 'broker1',
            'level': ['1', '2'],
            'group': 'brokers'
        }
    }
    :rtype: dict
    """
    single_value = {
        'name': name,
        'level': info.get('levels', [ALL_ACCREDITATIONS_GRANTED]),
        'group': group
    }
    single_key = info['token']
    user = {single_key: single_value}
    return user


def create_users_from_group(group, users_info):
    """
    Create dictionary that contains information about users permissions and accreditaion level
    that was defined in configuration file

    :param group: name of the group of users
    :type group: str

    :param: users_info: list of tuples that consist of two elements ('user_name', user_info)
        user_info have to look like:

    :type users_info: list

    :return: dictionary with users auth information
    :rtype: dict
    """

    users = {}

    for key, value in users_info:
        users.update(create_user_structure(group, key, value))
    LOGGER.info("Authentication permissions for users from the section "
                "[%s] has been added",
                group)
    return users


def create_users_from_group_ini(group, users_info):
    """
    Create dictionary that contains information about users permissions and accreditaion level
    that was defined in configuration ini file

    :param group: name of the group of users
    :type group: str

    :param: users_info: list of tuples that consist of two elements ('user_name', 'user_token')
        user_token: contain token itself and accreditaion levels that separated from token by comma
        it looks in such way 'token,1234'
    :type users_info: list

    :return: dictionary with users auth information
    :rtype: dict
    """

    users = {}

    for key, value in users_info:
        levels = [l for l in value.split(',', 1)[1]] if ',' in value else [ALL_ACCREDITATIONS_GRANTED]
        info = {'levels': levels, 'token': value.split(',', 1)[0]}

        users.update(create_user_structure(group, key, info))

    LOGGER.info("Authentication permissions for users from the section "
                "[%s] has been added",
                group)
    return users


@auth(auth_type="void")
def void_auth(app_meta):
    return {}


@auth(auth_type="ini")
def ini_auth(app_meta):
    file_path = get_path_to_auth(app_meta)

    config = ConfigParser()
    users = {}
    config.read(file_path)

    if not config.sections():
        LOGGER.warning("Auth file '%s' was empty, no user will be added",
                       file_path)

    for item in config.sections():
        users.update(create_users_from_group_ini(item, config.items(item)))

    return users


# Backward compatibility for `file` type
auth_mapping['file'] = ini_auth


@auth(auth_type="yaml")
def yaml_auth(app_meta):
    file_path = get_path_to_auth(app_meta)

    users = {}

    with open(file_path) as auth_file:
        config = yaml.safe_load(auth_file)

    if not config:
        LOGGER.warning("Auth file '%s' was empty, no user will be added",
                       file_path)
    for item in config:
        users.update(create_users_from_group(item, config[item].items()))

    return users


@auth(auth_type="json")
def json_auth(app_meta):
    file_path = get_path_to_auth(app_meta)

    users = {}

    with open(file_path) as auth_file:
        config = json.load(auth_file)

    if not config:
        LOGGER.warning("Auth file '%s' was empty, no user will be added",
                       file_path)
    for item in config:
        users.update(create_users_from_group(item, config[item].items()))

    return users


def _auth_factory(auth_type):
    auth_func = auth_mapping.get(auth_type, None)
    return auth_func


def validate_auth_config(users):
    """
    Validate configuration what return auth function
    and return only validated users

    validation check if users have required keys 'group, name, level'
    and check value of this  keys, expecting that they are not empty

    :param users: result of auth function
    :type users: abc.Mapping

    :rparam: validated_users
    :rtype: abc.Mapping
    """

    validated_users = {}
    need_keys = ('group', 'name', 'level')
    for general_key, general_value in users.items():
        if all((x in general_value.keys() for x in need_keys)) \
           and all(value for value in general_value.values()):
            validated_users[general_key] = deepcopy(general_value)
        else:
            LOGGER.warning("The user with username '%s' wasn`t added to "
                           "authentication permission, because invalid config",
                           general_key)
    return validated_users


def get_auth(app_meta):
    """
    Find auth function, get auth users and return only validated users


    :param app_meta: function what get app meta configuration

    :rparam: validated_users
    :rtype: abc.Mapping

    """
    auth_type = app_meta.config.auth.type
    auth_func = _auth_factory(auth_type)
    if hasattr(auth_func, '__call__'):
        return validate_auth_config(auth_func(app_meta))
    LOGGER.warning("The authentication configuration has not been added to "
                   "the app meta settings file")
    return {}


class AuthenticationPolicy(BasicAuthAuthenticationPolicy):

    def __init__(self, users, realm='OpenProcurement', debug=False):
        self.realm = realm
        self.debug = debug
        self.users = users if users else defaultdict(lambda x: None)

    def unauthenticated_userid(self, request):
        """ The userid parsed from the ``Authorization`` request header."""
        token = self._get_credentials(request)
        if token:
            user = self.users.get(token)
            if user:
                return user['name']
            toket_sha512 = sha512(token).hexdigest()
            user = self.users.get(toket_sha512)
            if user:
                return user['name']

    def check(self, user, request):
        auth_groups = ['g:{}'.format(user['group'])]
        for i in user['level']:
            auth_groups.append('a:{}'.format(i))
        token = get_access_token_from_request(request)
        if token:
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
            toket_sha512 = sha512(token).hexdigest()
            user = self.users.get(toket_sha512)
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
    groups = [g for g in reversed(principals) if g.startswith('g:')]
    return groups[0][2:] if groups else 'anonymous'


def check_accreditation(request, level):
    if level == TEST_ACCREDITATION:
        return (
            "a:{0}".format(TEST_ACCREDITATION) in request.effective_principals
        )
    return (
        "a:{0}".format(level) in request.effective_principals or
        "a:{0}".format(ALL_ACCREDITATIONS_GRANTED) in
        request.effective_principals
    )
