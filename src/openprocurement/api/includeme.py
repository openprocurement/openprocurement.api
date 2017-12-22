from pyramid.interfaces import IRequest
from openprocurement.api.interfaces import IContentConfigurator, IOPContent
from openprocurement.api.adapters import ContentConfigurator
from openprocurement.api.models import Tender

def includeme(config):
    config.add_tender_procurementMethodType(Tender)
    config.scan("openprocurement.api.views")
    config.registry.registerAdapter(ContentConfigurator, (IOPContent, IRequest),
                                    IContentConfigurator)