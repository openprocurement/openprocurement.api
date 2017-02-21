# -*- coding: utf-8 -*-
import uuid
import unittest
import webtest
from pyramid.request import Request
import os
from os import environ
from openprocurement.api.subscriber import get_time, encrypt, decrypt, couch_uuid_validator
from datetime import datetime
from pytz import timezone
from openprocurement.api.tests.base import PrefixedRequestClass, test_tender_data

TZ = timezone(environ['TZ'] if 'TZ' in environ else 'Europe/Kiev')

class SubscriberTest(unittest.TestCase):

    relative_to = os.path.dirname(__file__)

    @classmethod
    def setUpClass(cls):
        cls.app = webtest.TestApp("config:test_subscriber.ini", relative_to=cls.relative_to)
        cls.app.RequestClass = PrefixedRequestClass

    def test_get_time(self):
        time = get_time()
        local_time = datetime.now(TZ).isoformat()
        self.assertEqual(time.split('+')[1], local_time.split('+')[1])

    def test_encrypt(self):
        sid = uuid.uuid4().hex
        value, time = encrypt(sid)
        self.assertEqual(len(value), 128)

    def test_decrypt(self):
        sid = uuid.uuid4().hex
        value, time = encrypt(sid)

        decrypted = decrypt(sid, value)
        self.assertEqual(decrypted.startswith(sid), True)

        value = ''
        for x in xrange(0, 32):
            value += 'hello'
        decrypted = decrypt(sid, value)
        self.assertNotEqual(decrypted.startswith(sid), True)

    def test_couch_uuid_validator(self):
        # Request without cookie SERVER_ID
        self.assertEqual(self.app.cookies, {})
        resp = self.app.get('/tenders')
        self.assertEqual(resp.status, '200 OK')
        self.assertEqual(len(resp.json['data']), 0)
        header = resp.headers.get('Set-Cookie', None).split(';')[0].split('=')
        header_name = header[0]
        header_value = header[1]
        self.assertEqual(header_name, 'SERVER_ID')
        self.assertEqual(len(header_value), 128)

        # Request POST without cookie SERVER_ID
        self.app.reset()
        self.assertEqual(self.app.cookies, {})
        resp = self.app.post_json('/tenders', {'data': test_tender_data}, status=412)
        self.assertEqual(resp.status, '412 Precondition Failed')
        header = resp.headers.get('Set-Cookie', None).split(';')[0].split('=')
        header_name = header[0]
        header_value = header[1]
        self.assertEqual(header_name, 'SERVER_ID')
        self.assertEqual(len(header_value), 128)

        # Request with valid cookie SERVER_ID
        cookie = self.app.cookies.get('SERVER_ID', None)
        self.assertNotEqual(cookie, None)
        resp = self.app.get('/tenders')
        self.assertEqual(resp.status, '200 OK')
        self.assertEqual(len(resp.json['data']), 0)
        header = resp.headers.get('Set-Cookie', None)
        self.assertEqual(header, None)

        # Request with invalid cookie SERVER_ID
        cookie_value = 'f2154s5adf2as1f54asdf1as56f46asf3das4f654as31f456'
        self.app.set_cookie('SERVER_ID', cookie_value)
        resp = self.app.get('/tenders', status=412)
        self.assertEqual(resp.status, '412 Precondition Failed')
        self.assertEqual(resp.request.cookies.get('SERVER_ID', None), cookie_value)
        header = resp.headers.get('Set-Cookie', None).split(';')[0].split('=')
        header_name = header[0]
        header_value = header[1]
        self.assertEqual(header_name, 'SERVER_ID')
        self.assertEqual(len(header_value), 128)
