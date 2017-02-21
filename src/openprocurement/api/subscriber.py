# -*- coding: utf-8 -*-
from Cookie import SimpleCookie
from os import environ
from binascii import hexlify, unhexlify
from Crypto.Cipher import AES
from pyramid.events import NewRequest
from webob.exc import HTTPPreconditionFailed
from logging import getLogger
from datetime import datetime
from pytz import timezone
from webob.exc import HTTPPreconditionFailed

TZ = timezone(environ['TZ'] if 'TZ' in environ else 'Europe/Kiev')

logger = getLogger(__name__)

def get_time():
    return datetime.now(TZ).isoformat()

def encrypt(sid):
    time = get_time()
    text = "{}{:^{}}".format(sid, time, AES.block_size * 2)
    return hexlify(AES.new(sid).encrypt(text)), time


def decrypt(sid, key):
    try:
        text = AES.new(sid).decrypt(unhexlify(key))
        text.startswith(sid)
    except:
        text = ''
    return text

def couch_uuid_validator(event):
    request = event.request
    couch_uuid = event.request.registry.couch_uuid
    cookies = SimpleCookie(request.environ.get('HTTP_COOKIE'))
    server_id = cookies.get('SERVER_ID', None)
    if server_id:
        value = server_id.value
        decrypted = decrypt(couch_uuid, value)
        if not decrypted or not decrypted.startswith(couch_uuid):
            logger.info('Invalid cookie: {}'.format(value,
                        extra={'MESSAGE_ID': 'serverid_invalid'}))
            response_cookie = SimpleCookie()
            value, time = encrypt(couch_uuid)
            response_cookie['SERVER_ID'] = value
            response_cookie['SERVER_ID']['path'] = '/'
            request.response = HTTPPreconditionFailed(
                headers={'Set-Cookie': response_cookie['SERVER_ID'].OutputString()}
            )
            request.response.empty_body = True
            logger.info('New cookie: {} ({})'.format(value, time),
                        extra={'MESSAGE_ID': 'serverid_new'})
            raise request.response
        else:
            time = decrypted[len(couch_uuid):]
            logger.debug('Valid cookie: {} ({})'.format(value, time),
                         extra={'MESSAGE_ID': 'serverid_valid'})
    elif request.method in ['POST', 'PATCH', 'PUT', 'DELETE']:
        value, time = encrypt(couch_uuid)
        response_cookie = SimpleCookie()
        response_cookie['SERVER_ID'] = value
        response_cookie['SERVER_ID']['path'] = '/'
        request.response = HTTPPreconditionFailed(
            headers={'Set-Cookie': response_cookie['SERVER_ID'].OutputString()}
        )
        request.response.empty_body = True
        logger.info('New cookie: {} ({})'.format(value, time),
                    extra={'MESSAGE_ID': 'serverid_new'})
        raise request.response
    if not server_id:
        value, time = encrypt(couch_uuid)
        request.response.set_cookie(name='SERVER_ID', value=value)
        logger.info('New cookie: {} ({})'.format(value, time),
                    extra={'MESSAGE_ID': 'serverid_new'})
        return request.response

def includeme(config):
    logger.info('init couch_uuid NewRequest subscriber')
    config.registry.couch_uuid = config.registry.couchdb_server.uuid
    config.add_subscriber(couch_uuid_validator, NewRequest)
