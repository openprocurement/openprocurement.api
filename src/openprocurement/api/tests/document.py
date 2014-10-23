# -*- coding: utf-8 -*-
import unittest

from openprocurement.api.tests.base import BaseTenderWebTest


class TenderDocumentResourceTest(BaseTenderWebTest):

    def test_empty_listing(self):
        response = self.app.get('/tenders/{}/documents'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json, {"documents": {}})

    def test_get_tender_not_found(self):
        response = self.app.get('/tenders/some_id/documents', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

    def test_post_tender_not_found(self):
        response = self.app.post('/tenders/some_id/documents', status=404, upload_files=[
                                 ('upload', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

    def test_put_tender_not_found(self):
        response = self.app.put('/tenders/some_id/documents/some_id', status=404, upload_files=[
                                ('upload', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

    def test_put_tender_document_not_found(self):
        response = self.app.put('/tenders/{}/documents/some_id'.format(
            self.tender_id), status=404, upload_files=[('upload', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'id'}
        ])

    def test_get_tender_document_not_found(self):
        response = self.app.get('/tenders/{}/documents/some_id'.format(
            self.tender_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'id'}
        ])

    def test_create_tender_document(self):
        response = self.app.post('/tenders/{}/documents'.format(
            self.tender_id), upload_files=[('upload', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        self.assertTrue('name.doc' in response.headers['Location'])
        self.assertTrue('name.doc' in response.json["documents"])

        response = self.app.get('/tenders/{}/documents'.format(
            self.tender_id, 'name.doc'))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertTrue('name.doc' in response.json["documents"])

        response = self.app.get('/tenders/{}/documents/{}'.format(
            self.tender_id, 'name.doc'))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'text/html')
        self.assertEqual(response.content_length, 7)
        self.assertEqual(response.body, 'content')

    def test_put_tender_document(self):
        response = self.app.post('/tenders/{}/documents'.format(
            self.tender_id), upload_files=[('upload', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        self.assertTrue('name.doc' in response.json["documents"])

        response = self.app.put('/tenders/{}/documents/{}'.format(
            self.tender_id, 'name.doc'), upload_files=[('upload', 'name.doc', 'content2')])
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json["content_type"], 'application/msword')
        self.assertEqual(response.json["length"], '8')


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TenderDocumentResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
