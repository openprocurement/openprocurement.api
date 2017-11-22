# -*- coding: utf-8 -*-
from cornice.service import Service, get_services
from openprocurement.api.utils import VERSION
from cornice_swagger.swagger import CorniceSwagger


swagger = Service(name='swagger_docs', path='/swagger', renderer='json')


@swagger.get()
def get_swagger(request):
    doc_generator = CorniceSwagger(get_services())
    return doc_generator(
        'Open Procurement API',
        request.registry.settings.get(
            'api_version',
            VERSION
        )
    )

