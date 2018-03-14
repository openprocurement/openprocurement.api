# -*- coding: utf-8 -*-


def not_found(self):
    response = self.app.get('/some_id/documents', status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'{}_id'.format(self.resource_name[:-1])}
    ])

    response = self.app.post('/some_id/documents', status=404, upload_files=[
                             ('file', 'name.doc', 'content')])
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'{}_id'.format(self.resource_name[:-1])}
    ])

    response = self.app.post('/{}/documents'.format(self.resource_id),
                             headers=self.access_header,
                             upload_files=[('file', u'укр.doc', 'content')],
                             status=415)
    self.assertEqual(response.status, '415 Unsupported Media Type')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"],
                     "Content-Type header should be one of ['application/json']")

    response = self.app.post_json('/some_id/documents',
                                  headers=self.access_header,
                                  params={'data': self.initial_document_data},
                                  status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'{}_id'.format(self.resource_name[:-1])}
    ])

    response = self.app.put('/some_id/documents/some_id', status=404, upload_files=[
                            ('file', 'name.doc', 'content2')])
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'{}_id'.format(self.resource_name[:-1])}
    ])

    response = self.app.put('/{}/documents/some_id'.format(self.resource_id),
                            headers=self.access_header,
                            status=404, upload_files=[('file', 'name.doc', 'content2')])
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location': u'url', u'name': u'document_id'}
    ])

    response = self.app.get('/some_id/documents/some_id', status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'{}_id'.format(self.resource_name[:-1])}
    ])

    response = self.app.get('/{}/documents/some_id'.format(self.resource_id),
                            headers=self.access_header, status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location': u'url', u'name': u'document_id'}
    ])


def create_document_in_forbidden_resource_status(self):

    self.set_status(self.forbidden_document_modification_actions_status)

    response = self.app.post_json('/{}/documents'.format(self.resource_id),
                                  headers=self.access_header,
                                  params={'data': self.initial_document_data},
                                  status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"],
                     "Can't update document in current ({}) {} status".format(self.forbidden_document_modification_actions_status, self.resource_name[:-1]))


def put_resource_document_invalid(self):
    from six import BytesIO
    from urllib import quote
    body = u'''--BOUNDARY\nContent-Disposition: form-data; name="file"; filename={}\nContent-Type: application/msword\n\ncontent\n'''.format(u'\uff07')
    environ = self.app._make_environ()
    environ['CONTENT_TYPE'] = 'multipart/form-data; boundary=BOUNDARY'
    environ['REQUEST_METHOD'] = 'POST'
    req = self.app.RequestClass.blank(self.app._remove_fragment('/{}/documents'.format(self.resource_id)), environ)
    req.headers.environ['X-Access-Token'] = str(self.resource_token)
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
    req = self.app.RequestClass.blank(self.app._remove_fragment('/{}/documents'.format(self.resource_id)), environ)
    req.environ['wsgi.input'] = BytesIO(body.encode(req.charset or 'utf8'))
    req.content_length = len(body)
    response = self.app.do_request(req, status=415)
    self.assertEqual(response.status, '415 Unsupported Media Type')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"],
                     "Content-Type header should be one of ['application/json']")

    response = self.app.post_json('/{}/documents'.format(self.resource_id),
                                  headers=self.access_header,
                                  params={'data': self.initial_document_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(u'укр.doc', response.json["data"]["title"])
    doc_id = response.json["data"]['id']
    self.assertIn(doc_id, response.headers['Location'])

    response = self.app.put('/{}/documents/{}'.format(self.resource_id, doc_id),
                            headers=self.access_header,
                            upload_files=[('file', 'name  name.doc', 'content2')],
                            status=415)
    self.assertEqual(response.status, '415 Unsupported Media Type')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"],
                     "Content-Type header should be one of ['application/json']")


def patch_resource_document(self):
    response = self.app.post_json('/{}/documents'.format(self.resource_id),
                                  headers=self.access_header,
                                  params={'data': self.initial_document_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']
    #dateModified = response.json["data"]['dateModified']
    self.assertIn(doc_id, response.headers['Location'])
    self.assertEqual(u'укр.doc', response.json["data"]["title"])
    self.assertNotIn("documentType", response.json["data"])

    response = self.app.patch_json('/{}/documents/{}'.format(self.resource_id, doc_id),
        headers=self.access_header, params={
            'data': {
                'documentOf': 'item',
                'relatedItem': '0' * 32
            }}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [u"Value must be one of ['asset', 'lot']."], u'location': u'body', u'name': u'documentOf'}
    ])

    response = self.app.patch_json('/{}/documents/{}'.format(self.resource_id, doc_id),
        headers=self.access_header, params={
            "data": {
                "description": "document description",
                "documentType": 'tenderNotice'
            }}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [u"Value must be one of {}.".format(str(self.document_types))], u'location': u'body', u'name': u'documentType'}
    ])
    response = self.app.patch_json('/{}/documents/{}'.format(self.resource_id, doc_id),
        headers=self.access_header, params={
            "data": {
                "description": "document description"
            }})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    self.assertNotIn("documentType", response.json["data"])

    response = self.app.get('/{}/documents/{}'.format(self.resource_id, doc_id),
                            headers=self.access_header)
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    self.assertEqual('document description', response.json["data"]["description"])
    #self.assertTrue(dateModified < response.json["data"]["dateModified"])

    self.set_status(self.forbidden_document_modification_actions_status)

    response = self.app.patch_json('/{}/documents/{}'.format(self.resource_id, doc_id),
        headers=self.access_header, params={
            "data": {
                "description": "document description"
            }}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"],
                     "Can't update document in current ({}) {} status".format(self.forbidden_document_modification_actions_status, self.resource_name[:-1]))


def create_resource_document_error(self):
    response = self.app.post('/{}/documents'.format(self.resource_id),
                             headers=self.access_header,
                             upload_files=[('file', u'укр.doc', 'content')],
                             status=415)
    self.assertEqual(response.status, '415 Unsupported Media Type')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"],
                     "Content-Type header should be one of ['application/json']")

    self.tearDownDS()
    response = self.app.post('/{}/documents'.format(self.resource_id),
                             headers=self.access_header,
                             upload_files=[('file', u'укр.doc', 'content')],
                             status=415)
    self.assertEqual(response.status, '415 Unsupported Media Type')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"],
                     "Content-Type header should be one of ['application/json']")

    self.setUpBadDS()
    response = self.app.post('/{}/documents'.format(self.resource_id),
                             headers=self.access_header,
                             upload_files=[('file', u'укр.doc', 'content')],
                             status=415)
    self.assertEqual(response.status, '415 Unsupported Media Type')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"],
                     "Content-Type header should be one of ['application/json']")


def create_resource_document_json_invalid(self):
    response = self.app.post_json('/{}/documents'.format(self.resource_id),
        headers=self.access_header, params={
            'data': {
                'title': u'укр.doc',
                'url': self.generate_docservice_url(),
                'format': 'application/msword',
            }}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "This field is required.")

    response = self.app.post_json('/{}/documents'.format(self.resource_id),
        headers=self.access_header, params={
            'data': {
                'title': u'укр.doc',
                'url': self.generate_docservice_url(),
                'hash': '0' * 32,
                'format': 'application/msword',
            }}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'], [
        {u'description': [u'Hash type is not supported.'], u'location': u'body', u'name': u'hash'}
    ])

    response = self.app.post_json('/{}/documents'.format(self.resource_id),
        headers=self.access_header, params={
            'data': {
                'title': u'укр.doc',
                'url': self.generate_docservice_url(),
                'hash': 'sha2048:' + '0' * 32,
                'format': 'application/msword',
            }}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'], [
        {u'description': [u'Hash type is not supported.'], u'location': u'body', u'name': u'hash'}
    ])

    response = self.app.post_json('/{}/documents'.format(self.resource_id),
        headers=self.access_header, params={
            'data': {
                'title': u'укр.doc',
                'url': self.generate_docservice_url(),
                'hash': 'sha512:' + '0' * 32,
                'format': 'application/msword',
            }}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'], [
        {u'description': [u'Hash value is wrong length.'], u'location': u'body', u'name': u'hash'}
    ])

    response = self.app.post_json('/{}/documents'.format(self.resource_id),
        headers=self.access_header, params={
            'data': {
                'title': u'укр.doc',
                'url': self.generate_docservice_url(),
                'hash': 'md5:' + 'O' * 32,
                'format': 'application/msword',
            }}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'], [
        {u'description': [u'Hash value is not hexadecimal.'], u'location': u'body', u'name': u'hash'}
    ])

    response = self.app.post_json('/{}/documents'.format(self.resource_id),
        headers=self.access_header, params={
            'data': {
                'title': u'укр.doc',
                'url': 'http://invalid.docservice.url/get/uuid',
                'hash': 'md5:' + '0' * 32,
                'format': 'application/msword',
            }}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can add document only from document service.")

    response = self.app.post_json('/{}/documents'.format(self.resource_id),
        headers=self.access_header, params={
            'data': {
                'title': u'укр.doc',
                'url': '/'.join(self.generate_docservice_url().split('/')[:4]),
                'hash': 'md5:' + '0' * 32,
                'format': 'application/msword',
            }}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can add document only from document service.")

    response = self.app.post_json('/{}/documents'.format(self.resource_id),
        headers=self.access_header, params={
            'data': {
                'title': u'укр.doc',
                'url': self.generate_docservice_url().split('?')[0],
                'hash': 'md5:' + '0' * 32,
                'format': 'application/msword',
            }}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can add document only from document service.")

    response = self.app.post_json('/{}/documents'.format(self.resource_id),
        headers=self.access_header, params={
            'data': {
                'title': u'укр.doc',
                'url': self.generate_docservice_url().replace(self.app.app.registry.keyring.keys()[-1], '0' * 8),
                'hash': 'md5:' + '0' * 32,
                'format': 'application/msword',
            }}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Document url expired.")

    response = self.app.post_json('/{}/documents'.format(self.resource_id),
        headers=self.access_header, params={
            'data': {
                'title': u'укр.doc',
                'url': self.generate_docservice_url().replace("Signature=", "Signature=ABC"),
                'hash': 'md5:' + '0' * 32,
                'format': 'application/msword',
            }}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Document url signature invalid.")

    response = self.app.post_json('/{}/documents'.format(self.resource_id),
        headers=self.access_header, params={
            'data': {
                'title': u'укр.doc',
                'url': self.generate_docservice_url().replace("Signature=", "Signature=bw%3D%3D"),
                'hash': 'md5:' + '0' * 32,
                'format': 'application/msword',
            }}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Document url invalid.")


def create_resource_document_json(self):
    response = self.app.post_json('/{}/documents'.format(self.resource_id),
                                  headers=self.access_header,
                                  params={'data': self.initial_document_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']
    self.assertIn(doc_id, response.headers['Location'])
    self.assertEqual(u'укр.doc', response.json["data"]["title"])
    self.assertIn('Signature=', response.json["data"]["url"])
    self.assertIn('KeyID=', response.json["data"]["url"])
    self.assertNotIn('Expires=', response.json["data"]["url"])
    key = response.json["data"]["url"].split('/')[-1].split('?')[0]
    tender = self.db.get(self.resource_id)
    self.assertIn(key, tender['documents'][-1]["url"])
    self.assertIn('Signature=', tender['documents'][-1]["url"])
    self.assertIn('KeyID=', tender['documents'][-1]["url"])
    self.assertNotIn('Expires=', tender['documents'][-1]["url"])

    response = self.app.get('/{}/documents'.format(self.resource_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"][0]["id"])
    self.assertEqual(u'укр.doc', response.json["data"][0]["title"])

    response = self.app.get('/{}/documents/{}'.format(self.resource_id, doc_id),
                            params={'download': 'some_id'}, status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location': u'url', u'name': u'download'}
    ])

    response = self.app.get('/{}/documents/{}'.format(self.resource_id, doc_id),
                            params={'download': key})
    self.assertEqual(response.status, '302 Moved Temporarily')
    self.assertIn('http://localhost/get/', response.location)
    self.assertIn('Signature=', response.location)
    self.assertIn('KeyID=', response.location)
    self.assertNotIn('Expires=', response.location)

    response = self.app.get('/{}/documents/{}'.format(
        self.resource_id, doc_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    self.assertEqual(u'укр.doc', response.json["data"]["title"])

    self.set_status(self.forbidden_document_modification_actions_status)

    response = self.app.post_json('/{}/documents'.format(self.resource_id),
                                  headers=self.access_header,
                                  params={'data': self.initial_document_data},
                                  status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"],
                     "Can't update document in current ({}) {} status".format(self.forbidden_document_modification_actions_status, self.resource_name[:-1]))


def put_resource_document_json(self):
    response = self.app.post_json('/{}/documents'.format(self.resource_id),
                                  headers=self.access_header,
                                  params={'data': self.initial_document_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(u'укр.doc', response.json["data"]["title"])
    doc_id = response.json["data"]['id']
    dateModified = response.json["data"]['dateModified']
    datePublished = response.json["data"]['datePublished']
    self.assertIn(doc_id, response.headers['Location'])

    response = self.app.put_json('/{}/documents/{}'.format(self.resource_id, doc_id),
        headers=self.access_header, params={
            'data': {
                'title': u'name.doc',
                'url': self.generate_docservice_url(),
                'hash': 'md5:' + '0' * 32,
                'format': 'application/msword',
            }})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    self.assertIn('Signature=', response.json["data"]["url"])
    self.assertIn('KeyID=', response.json["data"]["url"])
    self.assertNotIn('Expires=', response.json["data"]["url"])
    key = response.json["data"]["url"].split('/')[-1].split('?')[0]
    tender = self.db.get(self.resource_id)
    self.assertIn(key, tender['documents'][-1]["url"])
    self.assertIn('Signature=', tender['documents'][-1]["url"])
    self.assertIn('KeyID=', tender['documents'][-1]["url"])
    self.assertNotIn('Expires=', tender['documents'][-1]["url"])

    response = self.app.get('/{}/documents/{}'.format(self.resource_id, doc_id),
                            params={'download': key})
    self.assertEqual(response.status, '302 Moved Temporarily')
    self.assertIn('http://localhost/get/', response.location)
    self.assertIn('Signature=', response.location)
    self.assertIn('KeyID=', response.location)
    self.assertNotIn('Expires=', response.location)

    response = self.app.get('/{}/documents/{}'.format(
        self.resource_id, doc_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    self.assertEqual(u'name.doc', response.json["data"]["title"])
    dateModified2 = response.json["data"]['dateModified']
    self.assertTrue(dateModified < dateModified2)
    self.assertEqual(dateModified, response.json["data"]["previousVersions"][0]['dateModified'])
    self.assertEqual(response.json["data"]['datePublished'], datePublished)

    response = self.app.get('/{}/documents'.format(self.resource_id), params={'all': 'true'})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(dateModified, response.json["data"][0]['dateModified'])
    self.assertEqual(dateModified2, response.json["data"][1]['dateModified'])

    response = self.app.post_json('/{}/documents'.format(self.resource_id),
        headers=self.access_header, params={
            'data': {
                'title': 'name.doc',
                'url': self.generate_docservice_url(),
                'hash': 'md5:' + '0' * 32,
                'format': 'application/msword',
            }})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']
    dateModified = response.json["data"]['dateModified']
    self.assertIn(doc_id, response.headers['Location'])

    response = self.app.get('/{}/documents'.format(self.resource_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(dateModified2, response.json["data"][0]['dateModified'])
    self.assertEqual(dateModified, response.json["data"][1]['dateModified'])

    response = self.app.put_json('/{}/documents/{}'.format(self.resource_id, doc_id),
                                 headers=self.access_header,
                                 params={'data': self.initial_document_data})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    self.assertIn('Signature=', response.json["data"]["url"])
    self.assertIn('KeyID=', response.json["data"]["url"])
    self.assertNotIn('Expires=', response.json["data"]["url"])
    key = response.json["data"]["url"].split('/')[-1].split('?')[0]
    tender = self.db.get(self.resource_id)
    self.assertIn(key, tender['documents'][-1]["url"])
    self.assertIn('Signature=', tender['documents'][-1]["url"])
    self.assertIn('KeyID=', tender['documents'][-1]["url"])
    self.assertNotIn('Expires=', tender['documents'][-1]["url"])

    response = self.app.get('/{}/documents/{}'.format(self.resource_id, doc_id),
                            params={'download': key})
    self.assertEqual(response.status, '302 Moved Temporarily')
    self.assertIn('http://localhost/get/', response.location)
    self.assertIn('Signature=', response.location)
    self.assertIn('KeyID=', response.location)
    self.assertNotIn('Expires=', response.location)

    self.set_status(self.forbidden_document_modification_actions_status)

    response = self.app.put_json('/{}/documents/{}'.format(self.resource_id, doc_id),
                                 headers=self.access_header,
                                 params={'data': self.initial_document_data},
                                 status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"],
                     "Can't update document in current ({}) {} status".format(self.forbidden_document_modification_actions_status, self.resource_name[:-1]))
