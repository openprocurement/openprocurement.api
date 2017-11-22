# -*- coding: utf-8 -*-
from cornice.service import Service, get_services
from openprocurement.api.utils import VERSION, generate_spore_description


spore = Service(name='spore', path='/spore', renderer='json')


@spore.get()
def get_spore(request):
    services = get_services()
    return generate_spore_description(services, 'Service name', request.application_url, request.registry.settings.get('api_version', VERSION))
