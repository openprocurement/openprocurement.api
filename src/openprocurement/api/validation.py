# -*- coding: utf-8 -*-
from schematics.exceptions import (
    ModelValidationError, ModelConversionError, ValidationError
)
from jsonpatch import JsonPointerException

from openprocurement.api.utils import (
    apply_data_patch,
    check_document,
    error_handler,
    get_first_document,
    get_type,
    raise_operation_error,
    set_first_document_fields,
    update_document_url,
    update_logging_context,
)
from openprocurement.api.constants import (
    TEST_ACCREDITATION,
)

OPERATIONS = {"POST": "add", "PATCH": "update", "PUT": "update", "DELETE": "delete"}


def _get_json_from_request(request):
    try:
        json = request.json_body
    except ValueError, e:
        request.errors.add('body', 'data', e.message)
        request.errors.status = 422
        raise error_handler(request)
    return json


def validate_json_data(request):
    json = _get_json_from_request(request)
    if not isinstance(json, dict) or 'data' not in json or not isinstance(json.get('data'), dict):
        request.errors.add('body', 'data', "Data not available")
        request.errors.status = 422
        raise error_handler(request)
    request.validated['json_data'] = json['data']
    return json['data']


def _validation_model(request, model, container=False, data=None):
    if not container and isinstance(request.context, model):
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
    return m, method, role


def _validate_data(request, model, container=False, data=None):
    m, method, role = _validation_model(request, model, container, data)
    if hasattr(type(m), '_options') and role not in type(m)._options.roles:
        request.errors.add('url', 'role', 'Forbidden')
        request.errors.status = 403
        raise error_handler(request)

    request.validated['data'] = method(role)
    if container:
        m = model(request.validated['data'])
        m.__parent__ = request.context
        request.validated[container] = m
    return request.validated['data']


def validate_data(request, model, container=False, data=None):
    if data is None:
        data = validate_json_data(request)
    try:
        return _validate_data(request, model, container, data)
    except (ModelValidationError, ModelConversionError), e:
        for i in e.message:
            request.errors.add('body', i, e.message[i])
        request.errors.status = 422
        raise error_handler(request)
    except ValueError, e:
        request.errors.add('body', 'data', e.message)
        request.errors.status = 422
        raise error_handler(request)
    except JsonPointerException, e:
        request.errors.add('body', 'data', e.message)
        request.errors.status = 422
        raise error_handler(request)


def validate_patch_document_data(request, **kwargs):
    model = type(request.context)
    return validate_data(request, model)


def validate_document_data(request, **kwargs):
    context = request.context if 'documents' in request.context else request.context.__parent__
    model = get_type(context).documents.model_class
    validate_data(request, model, "document")

    first_document = get_first_document(request)
    document = request.validated['document']
    check_document(request, document, 'body')

    if first_document:
        set_first_document_fields(request, first_document, document)

    if not document.documentOf:
        document.documentOf = get_type(context).__name__.lower()
    document_route = request.matched_route.name.replace("collection_", "")
    document = update_document_url(request, document, document_route, {})
    request.validated['document'] = document


def validate_file_upload(request, **kwargs):
    update_logging_context(request, {'document_id': '__new__'})
    if request.registry.use_docservice and request.content_type == "application/json":
        return validate_document_data(request)
    if 'file' not in request.POST or not hasattr(request.POST['file'], 'filename'):
        request.errors.add('body', 'file', 'Not Found')
        request.errors.status = 404
        raise error_handler(request)
    else:
        request.validated['file'] = request.POST['file']


def validate_file_update(request, **kwargs):
    if request.registry.use_docservice and request.content_type == "application/json":
        return validate_document_data(request)
    if request.content_type == 'multipart/form-data':
        validate_file_upload(request)


def validate_uniq(items, field, error_message):
    if items:
        ids = [i.get(field) for i in items]
        if [i for i in set(ids) if ids.count(i) > 1]:
            raise ValidationError(error_message)


def validate_items_uniq(items):
    validate_uniq(items, 'id', u"Item id should be uniq for all items")


def validate_cpv_group(items, *args):
    if items and len(set([i.classification.id[:3] for i in items])) != 1:
        raise ValidationError(u"CPV group of items be identical")


def validate_change_status(request, error_handler, **kwargs):
    """
        This validator get dict from adapter and validate availibility
        to change status by dict.
    """
    # Get resource_type
    resource_type = request.validated['resource_type']
    # Get status from PATCH validated data
    new_status = request.json['data'].get("status")
    # Get model from context
    model = request.context

    # Check status in data and not equal to context status
    if not new_status or new_status == model.status:
        return

    # get available statuses from dict
    statuses = request.content_configurator.available_statuses[model.status]['next_status']
    # verify right status change (auth_role and target status)
    msg = 'Can\'t update {} in current ({}) status'.format(resource_type,
                                                           model.status)

    if new_status not in statuses or \
            request.authenticated_role not in statuses.get(new_status, {}):
        raise_operation_error(request, error_handler, msg)


def validate_accreditations(request, model, resource_type='resource'):
    if not any([
        request.check_accreditation(acc) for acc in
        iter(str(model.create_accreditation))
    ]):
        request.errors.add(
            'body',
            'accreditation',
            'Broker Accreditation level does '
            'not permit {} creation'.format(resource_type)
        )
        request.errors.status = 403
        raise error_handler(request)


def validate_t_accreditation(request, data, resource_type='resource'):
    """Users with test accreditation can create assets only in test mode

    't' stands for 'test', but if add 'test' to the function name,
    nosetests will collect it.
    """
    if (
        data and
        data.get('mode', None) is None and
        request.check_accreditation(TEST_ACCREDITATION)
    ):
        request.errors.add(
            'body',
            'mode',
            'Broker Accreditation level does '
            'not permit {} creation'.format(resource_type)
        )
        request.errors.status = 403
        raise error_handler(request)
