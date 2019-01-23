# -*- coding: utf-8 -*-
from base64 import b64encode, b64decode
from email.header import decode_header
from time import time
from rfc6266 import build_header
from string import hexdigits
from urllib import unquote, quote, urlencode
from urlparse import urlparse, urlunsplit, parse_qsl, parse_qs

from openprocurement.api.constants import (
    DOCSERVICE_KEY_ID_LENGTH,
    DOCUMENT_BLACKLISTED_FIELDS,
    DOCUMENT_WHITELISTED_FIELDS,
    LOGGER,
    SESSION,
    TEMPORARY_DOCUMENT_EXPIRATION_SECONDS,
)
from openprocurement.api.utils.common import (
    context_unpack,
    error_handler,
    generate_id,
    update_logging_context,
)


def get_filename(data):
    try:
        pairs = decode_header(data.filename)
    except Exception:
        pairs = None
    if not pairs:
        return data.filename
    header = pairs[0]
    if header[1]:
        return header[0].decode(header[1])
    else:
        return header[0]


def generate_docservice_url(request, doc_id, temporary=True, prefix=None):
    docservice_key = getattr(request.registry, 'docservice_key', None)
    parsed_url = urlparse(request.registry.docservice_url)
    query = {}
    if temporary:
        expires = int(time()) + TEMPORARY_DOCUMENT_EXPIRATION_SECONDS
        mess = "{}\0{}".format(doc_id, expires)
        query['Expires'] = expires
    else:
        mess = doc_id
    if prefix:
        mess = '{}/{}'.format(prefix, mess)
        query['Prefix'] = prefix
    query['Signature'] = quote(b64encode(docservice_key.signature(mess.encode("utf-8"))))
    query['KeyID'] = docservice_key.hex_vk()[:DOCSERVICE_KEY_ID_LENGTH]
    return urlunsplit((parsed_url.scheme, parsed_url.netloc, '/get/{}'.format(doc_id), urlencode(query), ''))


def check_document(request, document, document_container):
    url = document.url
    parsed_url = urlparse(url)
    parsed_query = dict(parse_qsl(parsed_url.query))
    if not url.startswith(request.registry.docservice_url) or \
            len(parsed_url.path.split('/')) != 3 or \
            set(['Signature', 'KeyID']) != set(parsed_query):
        request.errors.add(document_container, 'url', "Can add document only from document service.")
        request.errors.status = 403
        raise error_handler(request)
    if not document.hash:
        request.errors.add(document_container, 'hash', "This field is required.")
        request.errors.status = 422
        raise error_handler(request)
    keyid = parsed_query['KeyID']
    if keyid not in request.registry.keyring:
        request.errors.add(document_container, 'url', "Document url expired.")
        request.errors.status = 422
        raise error_handler(request)
    dockey = request.registry.keyring[keyid]
    signature = parsed_query['Signature']
    key = urlparse(url).path.split('/')[-1]
    try:
        signature = b64decode(unquote(signature))
    except TypeError:
        request.errors.add(document_container, 'url', "Document url signature invalid.")
        request.errors.status = 422
        raise error_handler(request)
    mess = "{}\0{}".format(key, document.hash.split(':', 1)[-1])
    try:
        if mess != dockey.verify(signature + mess.encode("utf-8")):
            raise ValueError
    except ValueError:
        request.errors.add(document_container, 'url', "Document url invalid.")
        request.errors.status = 422
        raise error_handler(request)


def update_document_url(request, document, document_route, route_kwargs):
    key = urlparse(document.url).path.split('/')[-1]
    route_kwargs.update({'_route_name': document_route,
                         'document_id': document.id,
                         '_query': {'download': key}})
    document_path = request.current_route_path(**route_kwargs)
    document.url = '/' + '/'.join(document_path.split('/')[3:])
    return document


def get_first_document(request):
    documents = request.validated.get('documents')
    return documents[-1] if documents else None


def set_first_document_fields(request, first_document, document):
    for attr_name in type(first_document)._fields:
        if attr_name in DOCUMENT_WHITELISTED_FIELDS:
            setattr(document, attr_name, getattr(first_document, attr_name))
        elif attr_name not in DOCUMENT_BLACKLISTED_FIELDS and attr_name not in request.validated['json_data']:
            setattr(document, attr_name, getattr(first_document, attr_name))


def upload_file(
    request, blacklisted_fields=DOCUMENT_BLACKLISTED_FIELDS, whitelisted_fields=DOCUMENT_WHITELISTED_FIELDS
):
    first_document = get_first_document(request)
    if 'data' in request.validated and request.validated['data']:
        document = request.validated['document']
        check_document(request, document, 'body')

        if first_document:
            set_first_document_fields(request, first_document, document)

        document_route = request.matched_route.name.replace("collection_", "")
        document = update_document_url(request, document, document_route, {})
        return document
    if request.content_type == 'multipart/form-data':
        data = request.validated['file']
        filename = get_filename(data)
        content_type = data.type
        in_file = data.file
    else:
        filename = first_document.title
        content_type = request.content_type
        in_file = request.body_file

    if hasattr(request.context, "documents"):
        # upload new document
        model = type(request.context).documents.model_class
    else:
        # update document
        model = type(request.context)
    document = model({'title': filename, 'format': content_type})
    document.__parent__ = request.context
    if 'document_id' in request.validated:
        document.id = request.validated['document_id']
    if first_document:
        for attr_name in type(first_document)._fields:
            if attr_name not in blacklisted_fields:
                setattr(document, attr_name, getattr(first_document, attr_name))
    if request.registry.use_docservice:
        parsed_url = urlparse(request.registry.docservice_url)
        url = request.registry.docservice_upload_url or urlunsplit((
            parsed_url.scheme, parsed_url.netloc, '/upload', '', ''
        ))
        files = {'file': (filename, in_file, content_type)}
        doc_url = None
        index = 10
        while index:
            try:
                r = SESSION.post(
                    url,
                    files=files,
                    headers={'X-Client-Request-ID': request.environ.get('REQUEST_ID', '')},
                    auth=(request.registry.docservice_username, request.registry.docservice_password)
                )
                json_data = r.json()
            except Exception as e:
                LOGGER.warning(
                    "Raised exception '{}' on uploading document to document service': {}.".format(type(e), e),
                    extra=context_unpack(
                        request,
                        {'MESSAGE_ID': 'document_service_exception'},
                        {'file_size': in_file.tell()}
                    )
                )
            else:
                if r.status_code == 200 and json_data.get('data', {}).get('url'):
                    doc_url = json_data['data']['url']
                    doc_hash = json_data['data']['hash']
                    break
                else:
                    LOGGER.warning(
                        "Error {} on uploading document to document service '{}': {}".format(
                            r.status_code, url, r.text
                        ),
                        extra=context_unpack(
                            request,
                            {'MESSAGE_ID': 'document_service_error'},
                            {'ERROR_STATUS': r.status_code, 'file_size': in_file.tell()}
                        )
                    )
            in_file.seek(0)
            index -= 1
        else:
            request.errors.add('body', 'data', "Can't upload document to document service.")
            request.errors.status = 422
            raise error_handler(request)
        document.hash = doc_hash
        key = urlparse(doc_url).path.split('/')[-1]
    else:
        key = generate_id()
        filename = "{}_{}".format(document.id, key)
        request.validated['db_doc']['_attachments'][filename] = {
            "content_type": document.format,
            "data": b64encode(in_file.read())
        }
    document_route = request.matched_route.name.replace("collection_", "")
    document_path = request.current_route_path(
        _route_name=document_route,
        document_id=document.id,
        _query={'download': key}
    )
    document.url = '/' + '/'.join(document_path.split('/')[3:])
    update_logging_context(request, {'file_size': in_file.tell()})
    return document


def check_document_batch(request, document, document_container, route_kwargs):
    check_document(request, document, document_container)

    document_route = request.matched_route.name.replace("collection_", "")
    # Following piece of code was written by leits, so no one knows how it works
    # and why =)
    # To redefine document_route to get appropriate real document route when bid
    # is created with documents? I hope so :)
    if "Documents" not in document_route:
        specified_document_route_end = (
            document_container.lower().rsplit('documents')[0] + ' documents'
        ).lstrip().title()
        document_route = ' '.join([document_route[:-1], specified_document_route_end])

    return update_document_url(request, document, document_route, route_kwargs)


def get_file(request):
    db_doc_id = request.validated['db_doc'].id
    document = request.validated['document']
    key = request.params.get('download')
    if not any([key in i.url for i in request.validated['documents']]):
        request.errors.add('url', 'download', 'Not Found')
        request.errors.status = 404
        return
    filename = "{}_{}".format(document.id, key)
    if request.registry.use_docservice and filename not in request.validated['db_doc']['_attachments']:
        document = [i for i in request.validated['documents'] if key in i.url][-1]
        if 'Signature=' in document.url and 'KeyID' in document.url:
            url = document.url
        else:
            if 'download=' not in document.url:
                key = urlparse(document.url).path.replace('/get/', '')
            if not document.hash:
                url = generate_docservice_url(request, key, prefix='{}/{}'.format(db_doc_id, document.id))
            else:
                url = generate_docservice_url(request, key)
        request.response.content_type = document.format.encode('utf-8')
        request.response.content_disposition = build_header(
            document.title,
            filename_compat=quote(document.title.encode('utf-8'))
        )
        request.response.status = '302 Moved Temporarily'
        request.response.location = url
        return url
    else:
        data = request.registry.db.get_attachment(db_doc_id, filename)
        if data:
            request.response.content_type = document.format.encode('utf-8')
            request.response.content_disposition = build_header(
                document.title,
                filename_compat=quote(document.title.encode('utf-8'))
            )
            request.response.body_file = data
            return request.response
        request.errors.add('url', 'download', 'Not Found')
        request.errors.status = 404


def serialize_document_url(document):
    url = document.url
    if not url or '?download=' not in url:
        return url
    doc_id = parse_qs(urlparse(url).query)['download'][-1]
    root = document.__parent__
    parents = []
    while root.__parent__ is not None:
        parents[0:0] = [root]
        root = root.__parent__
    request = root.request
    if not request.registry.use_docservice:
        return url
    if 'status' in parents[0] and parents[0].status in type(parents[0])._options.roles:
        role = parents[0].status
        for index, obj in enumerate(parents):
            if obj.id != url.split('/')[(index - len(parents)) * 2 - 1]:
                break
            field = url.split('/')[(index - len(parents)) * 2]
            if "_" in field:
                field = field[0] + field.title().replace("_", "")[1:]
            roles = type(obj)._options.roles
            if roles[role if role in roles else 'default'](field, []):
                return url
    if not document.hash:
        path = [
            i for i in urlparse(url).path.split('/') if
            len(i) == 32 and
            not set(i).difference(hexdigits)  # noqa: F821
        ]
        return generate_docservice_url(request, doc_id, False, '{}/{}'.format(path[0], path[-1]))
    return generate_docservice_url(request, doc_id, False)
