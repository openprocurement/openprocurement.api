# -*- coding: utf-8 -*-
import unittest
from email.header import Header
from openprocurement.api.tests.base import BaseTenderWebTest
from openprocurement.api.utils import SESSION
from uuid import uuid4


class TenderDocumentResourceTest(BaseTenderWebTest):
    docservice = False

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

        if self.docservice:
            response = self.app.get('/tenders/{}/documents/{}?download={}'.format(
                self.tender_id, doc_id, key))
            self.assertEqual(response.status, '302 Moved Temporarily')
            self.assertIn('http://localhost/get/', response.location)
            self.assertIn('Signature=', response.location)
            self.assertIn('KeyID=', response.location)
            self.assertIn('Expires=', response.location)
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
        self.assertNotIn('acc_token', response.headers['Location'])

        self.set_status('active.tendering')

        response = self.app.post('/tenders/{}/documents'.format(
            self.tender_id), upload_files=[('file', u'укр.doc', 'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add document in current (active.tendering) tender status")

    def test_put_tender_document(self):
        from six import BytesIO
        from urllib import quote
        body = u'''--BOUNDARY\nContent-Disposition: form-data; name="file"; filename={}\nContent-Type: application/msword\n\ncontent\n'''.format(u'\uff07')
        environ = self.app._make_environ()
        environ['CONTENT_TYPE'] = 'multipart/form-data; boundary=BOUNDARY'
        environ['REQUEST_METHOD'] = 'POST'
        req = self.app.RequestClass.blank(self.app._remove_fragment('/tenders/{}/documents'.format(self.tender_id)), environ)
        req.environ['wsgi.input'] = BytesIO(body.encode('utf8'))
        req.content_length = len(body)
        response = self.app.do_request(req, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "could not decode params")

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
            self.tender_id, doc_id), upload_files=[('file', 'name  name.doc', 'content2')])
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key = response.json["data"]["url"].split('?')[-1].split('=')[-1]

        if self.docservice:
            response = self.app.get('/tenders/{}/documents/{}?download={}'.format(
                self.tender_id, doc_id, key))
            self.assertEqual(response.status, '302 Moved Temporarily')
            self.assertIn('http://localhost/get/', response.location)
            self.assertIn('Signature=', response.location)
            self.assertIn('KeyID=', response.location)
            self.assertIn('Expires=', response.location)
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
        self.assertEqual('name name.doc', response.json["data"]["title"])
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

        if self.docservice:
            response = self.app.get('/tenders/{}/documents/{}?download={}'.format(
                self.tender_id, doc_id, key))
            self.assertEqual(response.status, '302 Moved Temporarily')
            self.assertIn('http://localhost/get/', response.location)
            self.assertIn('Signature=', response.location)
            self.assertIn('KeyID=', response.location)
            self.assertIn('Expires=', response.location)
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
        self.assertNotIn("documentType", response.json["data"])

        response = self.app.patch_json('/tenders/{}/documents/{}'.format(self.tender_id, doc_id), {"data": {
            "documentOf": "lot"
        }}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'This field is required.'], u'location': u'body', u'name': u'relatedItem'},
        ])

        response = self.app.patch_json('/tenders/{}/documents/{}'.format(self.tender_id, doc_id), {"data": {
            "documentOf": "lot",
            "relatedItem": '0' * 32
        }}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'relatedItem should be one of lots'], u'location': u'body', u'name': u'relatedItem'}
        ])

        response = self.app.patch_json('/tenders/{}/documents/{}'.format(self.tender_id, doc_id), {"data": {
            "documentOf": "item",
            "relatedItem": '0' * 32
        }}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'relatedItem should be one of items'], u'location': u'body', u'name': u'relatedItem'}
        ])

        response = self.app.patch_json('/tenders/{}/documents/{}'.format(self.tender_id, doc_id), {"data": {
            "description": "document description",
            "documentType": 'tenderNotice'
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertIn("documentType", response.json["data"])
        self.assertEqual(response.json["data"]["documentType"], 'tenderNotice')

        response = self.app.patch_json('/tenders/{}/documents/{}'.format(self.tender_id, doc_id), {"data": {
            "documentType": None
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertNotIn("documentType", response.json["data"])

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


class TenderDocumentWithS3ResourceTest(TenderDocumentResourceTest):
    docservice = True

    def setUp(self):
        super(TenderDocumentWithS3ResourceTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://localhost'
        def request(method, url, **kwargs):
            from requests.models import Response
            response = Response()
            if method == 'POST' and '/upload' in url:
                response = Response()
                response.status_code = 200
                response.encoding = 'application/json'
                response._content = '"http://localhost/get/{}?Signature=Signature&KeyID=KeyID&Expires=Expires"'.format(uuid4().hex)
                response.reason = '200 OK'
            return response

        self._srequest = SESSION.request
        SESSION.request = request

    def tearDown(self):
        SESSION.request = self._srequest
        super(TenderDocumentWithS3ResourceTest, self).tearDown()


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TenderDocumentResourceTest))
    suite.addTest(unittest.makeSuite(TenderDocumentWithS3ResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
