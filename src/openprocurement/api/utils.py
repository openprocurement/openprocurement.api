# -*- coding: utf-8 -*-
from base64 import b64encode
from jsonpatch import make_patch, apply_patch
from openprocurement.api.models import Revision
from urllib import quote
from uuid import uuid4
from pyramid.security import authenticated_userid


def generate_id():
    return uuid4().hex


def generate_tender_id(tid):
    return "UA-" + tid


def upload_file(tender, document, key, in_file, request):
    conn = getattr(request.registry, 's3_connection', None)
    if conn:
        bucket = conn.get_bucket(request.registry.bucket_name)
        filename = "{}/{}/{}".format(tender.id, document.id, key)
        key = bucket.new_key(filename)
        key.set_metadata('Content-Type', document.format)
        key.set_metadata("Content-Disposition", "attachment; filename*=UTF-8''%s" % quote(document.title))
        key.set_contents_from_file(in_file)
        key.set_acl('private')
    else:
        filename = "{}_{}".format(document.id, key)
        tender['_attachments'][filename] = {
            "content_type": document.format,
            "data": b64encode(in_file.read())
        }


def get_file(tender, document, key, db, request):
    conn = getattr(request.registry, 's3_connection', None)
    if conn:
        filename = "{}/{}/{}".format(tender.id, document.id, key)
        url = conn.generate_url(method='GET', bucket=request.registry.bucket_name, key=filename, expires_in=300)
        request.response.content_type = document.format.encode('utf-8')
        request.response.content_disposition = 'attachment; filename={}'.format(quote(document.title.encode('utf-8')))
        request.response.status = '302 Moved Temporarily'
        request.response.location = url
        return url
    else:
        filename = "{}_{}".format(document.id, key)
        data = db.get_attachment(tender.id, filename)
        if data:
            request.response.content_type = document.format.encode('utf-8')
            request.response.content_disposition = 'attachment; filename={}'.format(quote(document.title.encode('utf-8')))
            request.response.body_file = data
            return request.response
        request.errors.add('url', 'download', 'Not Found')
        request.errors.status = 404


def prepare_patch(changes, orig, patch, basepath=''):
    if isinstance(patch, dict):
        for i in patch:
            if i in orig:
                prepare_patch(changes, orig[i], patch[i], '{}/{}'.format(basepath, i))
            else:
                changes.append({'op': 'add', 'path': '{}/{}'.format(basepath, i), 'value': patch[i]})
    elif isinstance(patch, list):
        for i, j in enumerate(patch):
            if len(orig) > i:
                prepare_patch(changes, orig[i], patch[i], '{}/{}'.format(basepath, i))
            else:
                changes.append({'op': 'add', 'path': '{}/{}'.format(basepath, i), 'value': j})
    else:
        for x in make_patch(orig, patch).patch:
            x['path'] = '{}{}'.format(basepath, x['path'])
            changes.append(x)


def apply_data_patch(item, changes):
    patch_changes = []
    prepare_patch(patch_changes, item, changes)
    return apply_patch(item, patch_changes)


def tender_serialize(tender, fields):
    fields = fields.split(',') + ["dateModified", "id"]
    return dict([(i, j) for i, j in tender.serialize(tender.status).items() if i in fields])


def get_revision_changes(dst, src):
    return make_patch(dst, src).patch


def set_ownership(item, request):
    item.owner = request.authenticated_userid
    item.owner_token = generate_id()


def save_tender(tender, src, request):
    patch = get_revision_changes(tender.serialize("plain"), src)
    if patch:
        tender.revisions.append(Revision({'author': request.authenticated_userid, 'changes': patch}))
        try:
            tender.store(request.registry.db)
        except Exception, e:
            request.errors.add('body', 'data', str(e))
