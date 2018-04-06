# -*- coding: utf-8 -*-
import argparse
import os
from pbkdf2 import PBKDF2
from ConfigParser import ConfigParser
from couchdb import Server as CouchdbServer, Session
from couchdb.http import Unauthorized, extract_credentials
from openprocurement.api.design import sync_design
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


def _user_doc_update(users_db, username, password):
    user_doc = users_db.get(
        'org.couchdb.user:{}'.format(username),
        {'_id': 'org.couchdb.user:{}'.format(username)})
    if (not user_doc.get('derived_key', '') or
        PBKDF2(password, user_doc.get('salt', ''),
               user_doc.get('iterations', 10)).hexread(
            int(len(user_doc.get('derived_key', '')) / 2)) !=
            user_doc.get('derived_key', '')):
        user_doc.update({
            "name": username,
            "roles": [],
            "type": "user",
            "password": password
        })
        LOGGER.info("Updating api db main user",
                    extra={'MESSAGE_ID': 'update_api_main_user'})
        users_db.save(user_doc)


def _reader_update(users_db, security_users, settings):
    if ('couchdb.reader_username' in settings and
            'couchdb.reader_password' in settings):
        reader_username = settings.get('couchdb.reader_username')
        reader = users_db.get(
            'org.couchdb.user:{}'.format(reader_username),
            {'_id': 'org.couchdb.user:{}'.format(reader_username)})
        if (not reader.get('derived_key', '') or
            PBKDF2(settings.get('couchdb.reader_password'),
            reader.get('salt', ''), reader.get(
                'iterations', 10)).hexread(int(len(reader.get(
                    'derived_key', '')) / 2)) !=
                reader.get('derived_key', '')):
            reader.update({
                "name": reader_username,
                "roles": ['reader'],
                "type": "user",
                "password": settings.get('couchdb.reader_password')
            })
            LOGGER.info("Updating api db reader user",
                        extra={'MESSAGE_ID': 'update_api_reader_user'})
            users_db.save(reader)
        security_users.append(reader_username)


def set_admin_api_security(server, db_name, settings):
    aserver = Server(settings.get('couchdb.admin_url'),
                     session=Session(retry_delays=range(10)))
    users_db = aserver['_users']
    _update_security(users_db, "Updating users db security",
                     'update_users_security')
    username, password = server.resource.credentials
    _user_doc_update(users_db, username, password)
    security_users = [username, ]
    _reader_update(users_db, security_users, settings)
    if db_name not in aserver:
        aserver.create(db_name)
    db = aserver[db_name]
    SECURITY[u'members'][u'names'] = security_users
    _update_security(db, "Updating api db security", 'update_api_security')
    auth_doc = db.get(VALIDATE_DOC_ID, {'_id': VALIDATE_DOC_ID})
    if auth_doc.get('validate_doc_update') != VALIDATE_DOC_UPDATE % username:
        auth_doc['validate_doc_update'] = VALIDATE_DOC_UPDATE % username
        LOGGER.info("Updating api db validate doc",
                    extra={'MESSAGE_ID': 'update_api_validate_doc'})
        db.save(auth_doc)
    # sync couchdb views
    sync_design(db)
    db = server[db_name]
    return aserver, server, db


def set_api_security(settings):
    # CouchDB connection
    db_name = os.environ.get('DB_NAME', settings['couchdb.db_name'])
    server = Server(settings.get('couchdb.url'),
                    session=Session(retry_delays=range(10)))
    if 'couchdb.admin_url' not in settings and server.resource.credentials:
        try:
            server.version()
        except Unauthorized:
            server = Server(extract_credentials(
                settings.get('couchdb.url'))[0])

    if 'couchdb.admin_url' in settings and server.resource.credentials:
        aserver, server, db = set_admin_api_security(server, db_name, settings)
    else:
        if db_name not in server:
            server.create(db_name)
        db = server[db_name]
        # sync couchdb views
        sync_design(db)
        aserver = None
    return aserver, server, db


def bootstrap_api_security():
    parser = argparse.ArgumentParser(description='---- Bootstrap API Security ----')
    parser.add_argument('section', type=str, help='Section in configuration file')
    parser.add_argument('config', type=str, help='Path to configuration file')
    params = parser.parse_args()
    if os.path.isfile(params.config):
        conf = ConfigParser()
        conf.read(params.config)
        settings = {k: v for k, v in conf.items(params.section)}
        set_api_security(settings)
