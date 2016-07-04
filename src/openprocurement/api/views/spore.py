# -*- coding: utf-8 -*-
from cornice.ext.spore import generate_spore_description
from cornice.service import Service, get_services
from openprocurement.api.utils import VERSION


spore = Service(name='spore', path='/spore', renderer='json')


@spore.get()
def get_spore(request):
    services = get_services()
    return generate_spore_description(services, 'Service name', request.application_url, request.registry.settings.get('api_version', VERSION))
