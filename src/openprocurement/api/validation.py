# -*- coding: utf-8 -*-
from schematics.exceptions import (
    ModelValidationError, ModelConversionError, ValidationError
)
from openprocurement.api.utils import apply_data_patch, update_logging_context, error_handler


def validate_json_data(request):
    try:
        json = request.json_body
    except ValueError, e:
        request.errors.add('body', 'data', e.message)
        request.errors.status = 422
        raise error_handler(request.errors)
    if not isinstance(json, dict) or 'data' not in json or not isinstance(json.get('data'), dict):
        request.errors.add('body', 'data', "Data not available")
        request.errors.status = 422
        raise error_handler(request.errors)
    request.validated['json_data'] = json['data']
    return json['data']


def validate_data(request, model, partial=False, data=None):
    if data is None:
        data = validate_json_data(request)
    try:
        if partial and isinstance(request.context, model):
            initial_data = request.context.serialize()
            m = model(initial_data)
            new_patch = apply_data_patch(initial_data, data)
            if new_patch:
                m.import_data(new_patch, partial=True, strict=True)
            m.__parent__ = request.context.__parent__
            m.validate()
            role = request.context.get_role()
            method = m.to_patch
        else:
            m = model(data)
            m.__parent__ = request.context
            m.validate()
            method = m.serialize
            role = 'create'
    except (ModelValidationError, ModelConversionError), e:
        for i in e.message:
            request.errors.add('body', i, e.message[i])
        request.errors.status = 422
        raise error_handler(request.errors)
    except ValueError, e:
        request.errors.add('body', 'data', e.message)
        request.errors.status = 422
        raise error_handler(request.errors)
    else:
        if hasattr(type(m), '_options') and role not in type(m)._options.roles:
            request.errors.add('url', 'role', 'Forbidden')
            request.errors.status = 403
            raise error_handler(request.errors)
        else:
            data = method(role)
            request.validated['data'] = data
            if not partial:
                m = model(data)
                m.__parent__ = request.context
                request.validated[model.__name__.lower()] = m
    return data


def validate_patch_document_data(request):
    model = type(request.context)
    return validate_data(request, model, True)


def validate_document_data(request):
    context = request.context if 'documents' in request.context else request.context.__parent__
    model = type(context).documents.model_class
    return validate_data(request, model)


def validate_file_upload(request):
    update_logging_context(request, {'document_id': '__new__'})
    if request.registry.docservice_url and request.content_type == "application/json":
        return validate_document_data(request)
    if 'file' not in request.POST or not hasattr(request.POST['file'], 'filename'):
        request.errors.add('body', 'file', 'Not Found')
        request.errors.status = 404
        raise error_handler(request.errors)
    else:
        request.validated['file'] = request.POST['file']


def validate_file_update(request):
    if request.registry.docservice_url and request.content_type == "application/json":
        return validate_document_data(request)
    if request.content_type == 'multipart/form-data':
        validate_file_upload(request)


def validate_items_uniq(items, *args):
    if items:
        ids = [i.id for i in items]
        if [i for i in set(ids) if ids.count(i) > 1]:
            raise ValidationError(u"Item id should be uniq for all items")


def validate_cpv_group(items, *args):
    if items and len(set([i.classification.id[:3] for i in items])) != 1:
        raise ValidationError(u"CPV group of items be identical")
