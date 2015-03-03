# -*- coding: utf-8 -*-
import unittest
from email.header import Header
from openprocurement.api.tests.base import BaseTenderWebTest


class TenderDocumentResourceTest(BaseTenderWebTest):
    s3_connection = False

    def test_not_found(self):
        response = self.app.get('/tenders/some_id/documents', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.post('/tenders/some_id/documents', status=404, upload_files=[
                                 ('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.post('/tenders/{}/documents'.format(self.tender_id), status=404, upload_files=[
                                 ('invalid_name', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'body', u'name': u'file'}
        ])

        response = self.app.put('/tenders/some_id/documents/some_id', status=404, upload_files=[
                                ('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.put('/tenders/{}/documents/some_id'.format(
            self.tender_id), status=404, upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'document_id'}
        ])

        response = self.app.get('/tenders/some_id/documents/some_id', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.get('/tenders/{}/documents/some_id'.format(
            self.tender_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'document_id'}
        ])

    def test_create_tender_document(self):
        response = self.app.get('/tenders/{}/documents'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json, {"data": []})

        response = self.app.post('/tenders/{}/documents'.format(
            self.tender_id), upload_files=[('file', u'укр.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])
        self.assertEqual(u'укр.doc', response.json["data"]["title"])
        key = response.json["data"]["url"].split('?')[-1].split('=')[-1]

        response = self.app.get('/tenders/{}/documents'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])
        self.assertEqual(u'укр.doc', response.json["data"][0]["title"])

        if self.s3_connection:
            response = self.app.get('/tenders/{}/documents/{}?download={}'.format(
                self.tender_id, doc_id, key))
            self.assertEqual(response.status, '302 Moved Temporarily')
            self.assertEqual(response.location, 'http://s3/{}/{}/{}/{}'.format('bucket', self.tender_id, doc_id, key))
        else:
            response = self.app.get('/tenders/{}/documents/{}?download=some_id'.format(
                self.tender_id, doc_id), status=404)
            self.assertEqual(response.status, '404 Not Found')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.json['status'], 'error')
            self.assertEqual(response.json['errors'], [
                {u'description': u'Not Found', u'location': u'url', u'name': u'download'}
            ])

            response = self.app.get('/tenders/{}/documents/{}?download={}'.format(
                self.tender_id, doc_id, key))
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/msword')
            self.assertEqual(response.content_length, 7)
            self.assertEqual(response.body, 'content')

        response = self.app.get('/tenders/{}/documents/{}'.format(
            self.tender_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual(u'укр.doc', response.json["data"]["title"])

        response = self.app.post('/tenders/{}/documents?acc_token=acc_token'.format(
            self.tender_id), upload_files=[('file', u'укр.doc'.encode("ascii", "xmlcharrefreplace"), 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(u'укр.doc', response.json["data"]["title"])
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])
        self.assertFalse('acc_token' in response.headers['Location'])

        self.set_status('active.tendering')

        response = self.app.post('/tenders/{}/documents'.format(
            self.tender_id), upload_files=[('file', u'укр.doc', 'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add document in current (active.tendering) tender status")

    def test_put_tender_document(self):
        from six import BytesIO
        from urllib import quote
        body = u'''--BOUNDARY\nContent-Disposition: form-data; name="file"; filename*=utf-8''{}\nContent-Type: application/msword\n\ncontent\n'''.format(quote('укр.doc'))
        environ = self.app._make_environ()
        environ['CONTENT_TYPE'] = 'multipart/form-data; boundary=BOUNDARY'
        environ['REQUEST_METHOD'] = 'POST'
        req = self.app.RequestClass.blank(self.app._remove_fragment('/tenders/{}/documents'.format(self.tender_id)), environ)
        req.environ['wsgi.input'] = BytesIO(body.encode(req.charset or 'utf8'))
        req.content_length = len(body)
        response = self.app.do_request(req)
        #response = self.app.post('/tenders/{}/documents'.format(
            #self.tender_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(u'укр.doc', response.json["data"]["title"])
        doc_id = response.json["data"]['id']
        dateModified = response.json["data"]['dateModified']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.put('/tenders/{}/documents/{}'.format(
            self.tender_id, doc_id), upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key = response.json["data"]["url"].split('?')[-1].split('=')[-1]

        if self.s3_connection:
            response = self.app.get('/tenders/{}/documents/{}?download={}'.format(
                self.tender_id, doc_id, key))
            self.assertEqual(response.status, '302 Moved Temporarily')
            self.assertEqual(response.location, 'http://s3/{}/{}/{}/{}'.format('bucket', self.tender_id, doc_id, key))
        else:
            response = self.app.get('/tenders/{}/documents/{}?download={}'.format(
                self.tender_id, doc_id, key))
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/msword')
            self.assertEqual(response.content_length, 8)
            self.assertEqual(response.body, 'content2')

        response = self.app.get('/tenders/{}/documents/{}'.format(
            self.tender_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])
        dateModified2 = response.json["data"]['dateModified']
        self.assertTrue(dateModified < dateModified2)
        self.assertEqual(dateModified, response.json["data"]["previousVersions"][0]['dateModified'])

        response = self.app.get('/tenders/{}/documents?all=true'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(dateModified, response.json["data"][0]['dateModified'])
        self.assertEqual(dateModified2, response.json["data"][1]['dateModified'])

        response = self.app.post('/tenders/{}/documents'.format(
            self.tender_id), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        dateModified = response.json["data"]['dateModified']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.get('/tenders/{}/documents'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(dateModified2, response.json["data"][0]['dateModified'])
        self.assertEqual(dateModified, response.json["data"][1]['dateModified'])

        response = self.app.put('/tenders/{}/documents/{}'.format(self.tender_id, doc_id), status=404, upload_files=[
                                ('invalid_name', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'body', u'name': u'file'}
        ])

        response = self.app.put('/tenders/{}/documents/{}'.format(
            self.tender_id, doc_id), 'content3', content_type='application/msword')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key = response.json["data"]["url"].split('?')[-1].split('=')[-1]

        if self.s3_connection:
            response = self.app.get('/tenders/{}/documents/{}?download={}'.format(
                self.tender_id, doc_id, key))
            self.assertEqual(response.status, '302 Moved Temporarily')
            self.assertEqual(response.location, 'http://s3/{}/{}/{}/{}'.format('bucket', self.tender_id, doc_id, key))
        else:
            response = self.app.get('/tenders/{}/documents/{}?download={}'.format(
                self.tender_id, doc_id, key))
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/msword')
            self.assertEqual(response.content_length, 8)
            self.assertEqual(response.body, 'content3')

        self.set_status('active.tendering')

        response = self.app.put('/tenders/{}/documents/{}'.format(
            self.tender_id, doc_id), upload_files=[('file', 'name.doc', 'content3')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current (active.tendering) tender status")

    def test_patch_tender_document(self):
        response = self.app.post('/tenders/{}/documents'.format(
            self.tender_id), upload_files=[('file', str(Header(u'укр.doc', 'utf-8')), 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        #dateModified = response.json["data"]['dateModified']
        self.assertIn(doc_id, response.headers['Location'])
        self.assertEqual(u'укр.doc', response.json["data"]["title"])

        response = self.app.patch_json('/tenders/{}/documents/{}'.format(self.tender_id, doc_id), {"data": {"description": "document description"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])

        response = self.app.get('/tenders/{}/documents/{}'.format(self.tender_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('document description', response.json["data"]["description"])
        #self.assertTrue(dateModified < response.json["data"]["dateModified"])

        self.set_status('active.tendering')

        response = self.app.patch_json('/tenders/{}/documents/{}'.format(self.tender_id, doc_id), {"data": {"description": "document description"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current (active.tendering) tender status")


import boto
from boto.utils import find_matching_headers
from boto.utils import merge_headers_by_name

try:
    from hashlib import md5
except ImportError:
    from md5 import md5


NOT_IMPL = None


class MockAcl(object):

    def __init__(self, parent=NOT_IMPL):
        pass

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        pass

    def to_xml(self):
        return '<mock_ACL_XML/>'


class MockKey(object):

    def __init__(self, bucket=None, name=None):
        self.bucket = bucket
        self.name = name
        self.data = None
        self.etag = None
        self.size = None
        self.closed = True
        self.content_encoding = None
        self.content_language = None
        self.content_type = None
        self.last_modified = 'Wed, 06 Oct 2010 05:11:54 GMT'
        self.BufferSize = 8192
        self.metadata = {}

    def set_contents_from_file(self, fp, headers=None, replace=NOT_IMPL,
                               cb=NOT_IMPL, num_cb=NOT_IMPL,
                               policy=NOT_IMPL, md5=NOT_IMPL,
                               res_upload_handler=NOT_IMPL):
        self.data = fp.read()
        self.set_etag()
        self.size = len(self.data)
        self._handle_headers(headers)

    def set_acl(self, acl_str, headers=None):
        pass

    def _handle_headers(self, headers):
        if not headers:
            return
        if find_matching_headers('Content-Encoding', headers):
            self.content_encoding = merge_headers_by_name('Content-Encoding',
                                                          headers)
        if find_matching_headers('Content-Type', headers):
            self.content_type = merge_headers_by_name('Content-Type', headers)
        if find_matching_headers('Content-Language', headers):
            self.content_language = merge_headers_by_name('Content-Language',
                                                          headers)

    def set_etag(self):
        """
        Set etag attribute by generating hex MD5 checksum on current
        contents of mock key.
        """
        m = md5()
        m.update(self.data)
        hex_md5 = m.hexdigest()
        self.etag = hex_md5

    def set_metadata(self, name, value):
        # Ensure that metadata that is vital to signing is in the correct
        # case. Applies to ``Content-Type`` & ``Content-MD5``.
        if name.lower() == 'content-type':
            self.metadata['Content-Type'] = value
        elif name.lower() == 'content-md5':
            self.metadata['Content-MD5'] = value
        else:
            self.metadata[name] = value

    def copy(self, dst_bucket_name, dst_key, metadata=NOT_IMPL,
             reduced_redundancy=NOT_IMPL, preserve_acl=NOT_IMPL):
        dst_bucket = self.bucket.connection.get_bucket(dst_bucket_name)
        return dst_bucket.copy_key(dst_key, self.bucket.name, self.name, metadata)


class MockBucket(object):

    def __init__(self, connection=None, name=None, key_class=NOT_IMPL):
        self.name = name
        self.keys = {}
        self.acls = {name: MockAcl()}
        # default object ACLs are one per bucket and not supported for keys
        self.def_acl = MockAcl()
        self.subresources = {}
        self.connection = connection
        self.logging = False

    def new_key(self, key_name=None):
        mock_key = MockKey(self, key_name)
        self.keys[key_name] = mock_key
        self.acls[key_name] = MockAcl()
        return mock_key

    def get_key(self, key_name, headers=NOT_IMPL, version_id=NOT_IMPL):
        # Emulate behavior of boto when get_key called with non-existent key.
        if key_name not in self.keys:
            return None
        return self.keys[key_name]

    def copy_key(self, new_key_name, src_bucket_name,
                 src_key_name, metadata=NOT_IMPL, src_version_id=NOT_IMPL,
                 storage_class=NOT_IMPL, preserve_acl=NOT_IMPL,
                 encrypt_key=NOT_IMPL, headers=NOT_IMPL, query_args=NOT_IMPL):
        import copy
        src_key = self.connection.get_bucket(src_bucket_name).get_key(src_key_name)
        new_key = self.new_key(key_name=new_key_name)
        new_key.data = copy.copy(src_key.data)
        new_key.size = len(new_key.data)
        return new_key


class MockProvider(object):

    def __init__(self, provider):
        self.provider = provider

    def get_provider_name(self):
        return self.provider


class MockConnection(object):

    def __init__(self, aws_access_key_id=NOT_IMPL,
                 aws_secret_access_key=NOT_IMPL, is_secure=NOT_IMPL,
                 port=NOT_IMPL, proxy=NOT_IMPL, proxy_port=NOT_IMPL,
                 proxy_user=NOT_IMPL, proxy_pass=NOT_IMPL,
                 host=NOT_IMPL, debug=NOT_IMPL,
                 https_connection_factory=NOT_IMPL,
                 calling_format=NOT_IMPL,
                 path=NOT_IMPL, provider='s3',
                 bucket_class=NOT_IMPL):
        self.buckets = {}
        self.provider = MockProvider(provider)

    def create_bucket(self, bucket_name, headers=NOT_IMPL, location=NOT_IMPL,
                      policy=NOT_IMPL, storage_class=NOT_IMPL):
        if bucket_name in self.buckets:
            raise boto.exception.StorageCreateError(
                409, 'BucketAlreadyOwnedByYou',
                "<Message>Your previous request to create the named bucket "
                "succeeded and you already own it.</Message>")
        mock_bucket = MockBucket(name=bucket_name, connection=self)
        self.buckets[bucket_name] = mock_bucket
        return mock_bucket

    def get_bucket(self, bucket_name, validate=NOT_IMPL, headers=NOT_IMPL):
        if bucket_name not in self.buckets:
            raise boto.exception.StorageResponseError(404, 'NoSuchBucket', 'Not Found')
        return self.buckets[bucket_name]

    def get_all_buckets(self, headers=NOT_IMPL):
        return self.buckets.itervalues()

    def generate_url(self, expires_in, method, bucket='', key='', headers=None,
                     query_auth=True, force_http=False, response_headers=None,
                     expires_in_absolute=False, version_id=None):
        return 'http://s3/{}/{}'.format(bucket, key)


class TenderDocumentWithS3ResourceTest(TenderDocumentResourceTest):
    s3_connection = True

    def setUp(self):
        super(TenderDocumentWithS3ResourceTest, self).setUp()
        # Create mock s3 connection
        connection = MockConnection()
        self.app.app.registry.s3_connection = connection
        bucket_name = 'bucket'
        if bucket_name not in [b.name for b in connection.get_all_buckets()]:
            connection.create_bucket(bucket_name)
        self.app.app.registry.bucket_name = bucket_name


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TenderDocumentResourceTest))
    suite.addTest(unittest.makeSuite(TenderDocumentWithS3ResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
