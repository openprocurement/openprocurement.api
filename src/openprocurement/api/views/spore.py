# -*- coding: utf-8 -*-
import re

from cornice.service import Service, get_services
from openprocurement.api.constants import VERSION


spore = Service(name='spore', path='/spore', renderer='json')


URL_PLACEHOLDER = re.compile(r'\{([a-zA-Z0-9_-]*)\}')


def _get_view_info(service, view, method, args):
    # the :foobar syntax should be removed.
    # see https://github.com/SPORE/specifications/issues/5
    service_path = URL_PLACEHOLDER.sub(':\g<1>', service.path)

    # get the list of placeholders
    service_params = URL_PLACEHOLDER.findall(service.path)

    format_name = 'json' if 'json' in args['renderer'] else args['renderer']

    view_info = {
        'path': service_path,
        'method': method,
        'formats': [format_name]
    }
    if service_params:
        view_info['required_params'] = service_params

    if hasattr(view, '__doc__'):
        view_info['description'] = view.__doc__

    return view_info


def _generate_spore_description(service, spore_doc):
    for method, view, args in service.definitions:
        view_info = _get_view_info(service, view, method, args)

        # we have the values, but we need to merge this with
        # possible previous values for this method.
        method_name = '{method}_{service}'.format(
            method=method.lower(), service=service.name.lower())
        spore_doc['methods'][method_name] = view_info


def generate_spore_description(services, name, base_url, version, **kwargs):
    """Utility to turn cornice web services into a SPORE-readable file.

    See https://github.com/SPORE/specifications for more information on SPORE.
    """

    spore_doc = dict(
        base_url=base_url,
        name=name,
        version=version,
        expected_status=[200, ],
        methods={},
        **kwargs
    )

    for service in services:
        _generate_spore_description(service, spore_doc)

    return spore_doc


@spore.get()
def get_spore(request):
    services = get_services()
    return generate_spore_description(
        services, 'Service name', request.application_url, request.registry.settings.get('api_version', VERSION)
    )
