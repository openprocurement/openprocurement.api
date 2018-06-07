# -*- coding: utf-8 -*-
import os
import json
import webtest
import unittest
from uuid import uuid4
from copy import deepcopy
from urllib import urlencode
from base64 import b64encode
from datetime import datetime
from types import FunctionType
from requests.models import Response

from openprocurement.api.utils import apply_data_patch
from openprocurement.api.constants import VERSION, SESSION
from openprocurement.api.design import sync_design
from openprocurement.api.config import DS

now = datetime.now()

JSON_RENDERER_ERROR = {u'description': u'Expecting value: line 1 column 1 (char 0)',
                        u'location': u'body', u'name': u'data'}


test_user_data = {
    'name': 'test',
    'password': 'test'
}


test_config_data = {
    'config': {
        'main': {
            'api_version': '2.4'
        },
        'auth': {
            'type': 'file',
            'src': 'test.ini'
        },
        'db': {
            'type': 'couchdb',
            'db_name': 'test_db',
            'url': 'localhost:5984',
        },
        'ds': {
            'user': test_user_data,
            'download_url': "http://localhost",
            'dockey': 'c1d4ce58057d33bc324a5e6b4c1cc598da66233e90e5f52e68775a0b262bb32f',
            'dockeys': ['172d32c81e1f6c95f287656bedd19ec5d0cefc9f130d7c8838263ef9003e4b76']
        },
        'auction': {
            'url': 'http://test-host.com',
            'public_key': 'b0cf560a77eb367fba1be5204614c49be7bba7685c3633c7d09d37371136c2b0'
        }
    },
    'here': os.getcwd(),
    'plugins': {}
}


def snitch(func):
    """
        This method is used to add test function to TestCase classes.
        snitch method gets test function and returns a copy of this function
        with 'test_' prefix at the beginning (to identify this function as
        an executable test).
        It provides a way to implement a storage (python module that
        contains non-executable test functions) for tests and to include
        different set of functions into different test cases.
    """
    return FunctionType(func.func_code, func.func_globals,
                        'test_' + func.func_name, closure=func.func_closure)


def create_blacklist(status_changes, statuses, roles):
    """
        This function is used to create blacklist for every status and
        auth role of different objects(lot, asset, e.t.c.).
        Since name of some role, depends on type of an object(lot - lot_owner, e.t.c.),
        we need `roles` argument.
        This function get `status_changes` and go through it keys(i.e. statuses).
        For every iteration we take one of roles and create white list for this auth role and status.
        Then from white list and `statuses` argument(actually all statuses of a certain object)
        we get black list.
    """
    status_blacklist = {}
    for status in statuses:
        status_blacklist[status] = {}
        for auth_role in roles:
            status_whitelist = {w for w in status_changes[status]['next_status']
                                if auth_role in status_changes[status]['next_status'][w]}
            if auth_role in status_changes[status]['editing_permissions']:
                status_whitelist.add(status)
            status_blacklist[status].update({auth_role: list(set(statuses) - status_whitelist)})
    return  status_blacklist


class PrefixedRequestClass(webtest.app.TestRequest):

    @classmethod
    def blank(cls, path, *args, **kwargs):
        path = '/api/%s%s' % (VERSION, path)
        return webtest.app.TestRequest.blank(path, *args, **kwargs)


class BaseWebTest(unittest.TestCase):

    """Base Web Test to test openprocurement.api.
    It setups the database before each test and delete it after.
    """

    initial_auth = None
    relative_to = os.path.dirname(__file__)

    @classmethod
    def setUpClass(cls):
        for _ in range(10):
            try:
                cls.app = webtest.TestApp("config:tests.ini", relative_to=cls.relative_to)
            except:
                pass
            else:
                break
        else:
            cls.app = webtest.TestApp("config:tests.ini", relative_to=cls.relative_to)
        cls.app.RequestClass = PrefixedRequestClass
        cls.couchdb_server = cls.app.app.registry.couchdb_server
        cls.db = cls.app.app.registry.db
        cls.db_name = cls.db.name

    @classmethod
    def tearDownClass(cls):
        try:
            cls.couchdb_server.delete(cls.db_name)
        except:
            pass

    def setUp(self):
        self.db_name += uuid4().hex
        self.couchdb_server.create(self.db_name)
        db = self.couchdb_server[self.db_name]
        sync_design(db)
        self.app.app.registry.db = db
        self.db = self.app.app.registry.db
        self.db_name = self.db.name
        if hasattr(self, 'initial_auth') and self.initial_auth is not None:
            self.app.authorization = self.initial_auth
        else:
            self.app.authorization = ('Basic', ('token', ''))

    def tearDown(self):
        self.couchdb_server.delete(self.db_name)


class BaseResourceWebTest(BaseWebTest):

    """Base Resource Web Test to test openprocurement.api.

    It takes care of database setup and cleanup,
    creates testing resource before each test,
    and adds resource name as prefix to all requests.
    """

    resource_name = ''
    initial_data = None
    initial_status = None
    init = False
    docservice = False

    # setup of Test Case that adds prefix
    @classmethod
    def blank(cls, path, *args, **kwargs):
        path = cls.resource_name + path
        p = path.split('?', 1)
        if p[0].endswith('/'):
            p[0] = p[0][:-1]
        path = '?'.join(p)
        path = '/api/%s/%s' % (VERSION, path)
        return webtest.app.TestRequest.blank(path, *args, **kwargs)

    @classmethod
    def setUpClass(cls):
        super(BaseResourceWebTest, cls).setUpClass()
        cls._blank = cls.app.RequestClass.blank
        cls.app.RequestClass.blank = cls.blank

    @classmethod
    def tearDownClass(cls):
        super(BaseResourceWebTest, cls).tearDownClass()
        cls.app.RequestClass.blank = cls._blank

    # setup of DS and related functionality
    def setUpDS(self):
        self.app.app.registry.use_docservice = True
        ds_config = deepcopy(test_config_data['config']['ds'])
        docservice = DS(ds_config)
        self.app.app.registry.docservice_url = docservice.download_url
        self.app.app.registry.docservice_upload_url = docservice.upload_url
        self.app.app.registry.docservice_username = docservice.user.name
        self.app.app.registry.docservice_password = docservice.user.password
        self.app.app.registry.docservice_key = dockey = docservice.signer
        self.app.app.registry.keyring = docservice.init_keyring(dockey)

        test = self
        def request(method, url, **kwargs):
            response = Response()
            if method == 'POST' and '/upload' in url:
                url = test.generate_docservice_url()
                response.status_code = 200
                response.encoding = 'application/json'
                response._content = '{{"data":{{"url":"{url}","hash":"md5:{md5}","format":"application/msword","title":"name.doc"}},"get_url":"{url}"}}'.format(url=url, md5='0'*32)
                response.reason = '200 OK'
            return response

        self._srequest = SESSION.request
        SESSION.request = request

    def setUpBadDS(self):
        self.app.app.registry.docservice_url = 'http://localhost'
        def request(method, url, **kwargs):
            response = Response()
            response.status_code = 403
            response.encoding = 'application/json'
            response._content = '"Unauthorized: upload_view failed permission check"'
            response.reason = '403 Forbidden'
            return response

        self._srequest = SESSION.request
        SESSION.request = request

    def generate_docservice_url(self):
        uuid = uuid4().hex
        key = self.app.app.registry.docservice_key
        keyid = key.hex_vk()[:8]
        signature = b64encode(key.signature("{}\0{}".format(uuid, '0' * 32)))
        query = {'Signature': signature, 'KeyID': keyid}
        return "http://localhost/get/{}?{}".format(uuid, urlencode(query))

    def tearDownDS(self):
        SESSION.request = self._srequest

    # methods for creating and switching statuses of resource under test
    def set_status(self, status, extra=None):
        data = {'status': status}
        if extra:
            data.update(extra)

        resource = self.db.get(self.resource_id)
        resource.update(apply_data_patch(resource, data))
        self.db.save(resource)

        response = self.app.get('/{}'.format(self.resource_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        resource = response.json['data']
        self.assertEqual(resource['status'], status)
        return resource

    def create_resource(self, extra=None, auth=None):
        if auth:
            self.app.authorization = auth
        data = deepcopy(self.initial_data)
        if extra:
            data.update(extra)
        response = self.app.post_json('/', {'data': data})
        self.assertEqual(response.status, '201 Created')
        resource = response.json['data']
        self.resource_token = response.json['access']['token']
        self.access_header = {'X-Access-Token': str(response.json['access']['token'])}
        self.resource_transfer = response.json['access']['transfer']
        self.resource_id = resource['id']
        status = resource['status']
        if self.initial_status and self.initial_status != status:
            resource = self.set_status(self.initial_status)
        return resource

    # set up and tear down of test method
    def setUp(self):
        super(BaseResourceWebTest, self).setUp()
        if self.docservice:
            self.setUpDS()
        if self.init:
            self.create_resource()

    def tearDown(self):
        if self.docservice:
            self.tearDownDS()
        if hasattr(self, 'resource_id'):
            del self.db[self.resource_id]
        super(BaseResourceWebTest, self).tearDown()


class DumpsTestAppwebtest(webtest.TestApp):
    hostname = "lb.api-sandbox.registry.ea.openprocurement.net"

    def do_request(self, req, status=None, expect_errors=None):
        req.headers.environ["HTTP_HOST"] = self.hostname
        if hasattr(self, 'file_obj') and not self.file_obj.closed:
            self.file_obj.write(req.as_bytes(True))
            self.file_obj.write("\n")
            if req.body:
                try:
                    self.file_obj.write(
                            'DATA:\n' + json.dumps(json.loads(req.body), indent=2, ensure_ascii=False).encode('utf8'))
                    self.file_obj.write("\n")
                except:
                    pass
            self.file_obj.write("\n")
        resp = super(DumpsTestAppwebtest, self).do_request(req, status=status, expect_errors=expect_errors)
        if hasattr(self, 'file_obj') and not self.file_obj.closed:
            headers = [(n.title(), v)
                       for n, v in resp.headerlist
                       if n.lower() != 'content-length']
            headers.sort()
            self.file_obj.write(str('Response: %s\n%s\n') % (
                resp.status,
                str('\n').join([str('%s: %s') % (n, v) for n, v in headers]),
            ))

            if resp.testbody:
                try:
                    self.file_obj.write(json.dumps(json.loads(resp.testbody), indent=2, ensure_ascii=False).encode('utf8'))
                except:
                    pass
            self.file_obj.write("\n\n")
        return resp
