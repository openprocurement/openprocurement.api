# -*- coding: utf-8 -*-
import argparse
import os
from pbkdf2 import PBKDF2
from ConfigParser import ConfigParser
from couchdb import Server as CouchdbServer, Session
from couchdb.http import Unauthorized, extract_credentials
from openprocurement.api.config import DB
from logging import getLogger

LOGGER = getLogger("{}.init".format(__name__))

SECURITY = {
    u'admins': {
        u'names': [],
        u'roles': ['_admin']
    },
    u'members': {
        u'names': [],
        u'roles': ['_admin']
    }
}
VALIDATE_DOC_ID = '_design/_auth'
VALIDATE_DOC_UPDATE = """function(newDoc, oldDoc, userCtx){
    if(newDoc._deleted && newDoc.tenderID) {
        throw({forbidden: 'Not authorized to delete this document'});
    }
    if(userCtx.roles.indexOf('_admin') !== -1 && newDoc._id.indexOf('_design/') === 0) {
        return;
    }
    if(userCtx.name === '%s') {
        return;
    } else {
        throw({forbidden: 'Only authorized user may edit the database'});
    }
}"""


def _update_security(db, log_message, message_id):
    if SECURITY != db.security:
        LOGGER.info(log_message, extra={'MESSAGE_ID': message_id})
        db.security = SECURITY


class Server(CouchdbServer):
    _uuid = None

    @property
    def uuid(self):
        """The uuid of the server.

        :rtype: basestring
        """
        if self._uuid is None:
            _, _, data = self.resource.get_json()
            self._uuid = data['uuid']
        return self._uuid


def _update_user(db, username, password, roles=None):
    user_doc = db.get(
        'org.couchdb.user:{}'.format(username),
        {'_id': 'org.couchdb.user:{}'.format(username)}
    )
    if (not user_doc.get('derived_key', '') or
            PBKDF2(
                password,
                user_doc.get('salt', ''),
                user_doc.get('iterations', 10)
            ).hexread(int(len(user_doc.get('derived_key', '')) / 2)) !=
            user_doc.get('derived_key', '')):
        user_doc.update({
            "name": username,
            "roles": [] if roles is None else list(roles),
            "type": "user",
            "password": password
        })
        db.save(user_doc)
        return True
    return False


def _user_doc_update(users_db, username, password):
    if _update_user(users_db, username, password):
        LOGGER.info("Updating api db main user",
                    extra={'MESSAGE_ID': 'update_api_main_user'})


def _reader_update(users_db, security_users, config):
    if not config.reader:
        return
    reader_username = config.reader.name
    reader_password = config.reader.password
    if _update_user(users_db, reader_username, reader_password, ('reader',)):
        LOGGER.info("Updating api db reader user",
                    extra={'MESSAGE_ID': 'update_api_reader_user'})
    security_users.append(reader_username)


def set_admin_api_security(server, db_name, config):
    from openprocurement.api.utils.db_state_doc import DBStateDocManager

    aserver = Server(config.create_url('admin'), session=Session(retry_delays=range(10)))
    users_db = aserver['_users']
    _update_security(users_db, "Updating users db security",
                     'update_users_security')
    username, password = server.resource.credentials
    _user_doc_update(users_db, username, password)
    security_users = [username, ]
    _reader_update(users_db, security_users, config)
    if db_name not in aserver:
        aserver.create(db_name)
    adb = aserver[db_name]
    SECURITY[u'members'][u'names'] = security_users
    _update_security(adb, "Updating api db security", 'update_api_security')
    auth_doc = adb.get(VALIDATE_DOC_ID, {'_id': VALIDATE_DOC_ID})
    if auth_doc.get('validate_doc_update') != VALIDATE_DOC_UPDATE % username:
        auth_doc['validate_doc_update'] = VALIDATE_DOC_UPDATE % username
        LOGGER.info("Updating api db validate doc",
                    extra={'MESSAGE_ID': 'update_api_validate_doc'})
        adb.save(auth_doc)
    db = server[db_name]
    DBStateDocManager(db).assure_doc()
    return aserver, server, adb, db


def set_api_security(config):
    from openprocurement.api.utils.db_state_doc import DBStateDocManager

    db_name = os.environ.get('DB_NAME', config.db_name)
    db_full_url = config.create_url('writer')
    server = Server(db_full_url, session=Session(retry_delays=range(10)))
    if not config.admin and server.resource.credentials:
        try:
            server.version()
        except Unauthorized:
            server = Server(extract_credentials(db_full_url)[0])
    if config.admin and server.resource.credentials:
        aserver, server, adb, db = set_admin_api_security(server, db_name, config)
    else:
        if db_name not in server:
            server.create(db_name)
        db = server[db_name]
        aserver = None
        adb = None
        DBStateDocManager(db).assure_doc()
    return aserver, server, adb, db


def bootstrap_api_security():
    parser = argparse.ArgumentParser(description='---- Bootstrap API Security ----')
    parser.add_argument('section', type=str, help='Section in configuration file')
    parser.add_argument('config', type=str, help='Path to configuration file')
    params = parser.parse_args()
    if os.path.isfile(params.config):
        conf = ConfigParser()
        conf.read(params.config)
        settings = DB({k: v for k, v in conf.items(params.section)})
        settings.validate()
        set_api_security(settings)
