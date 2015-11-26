from openprocurement.api.models import Tender
from openprocurement.api.interfaces import ITender
from pyramid.events import subscriber
from pyramid.events import ApplicationCreated
from pyramid.request import Request


class makeBaseTender(object):
    def __init__(self, data):
        self.data = data

    def tender(self):
        return self.model(self.data)


class makeTender(makeBaseTender):
    model = Tender


@subscriber(ApplicationCreated)
def register_adapters(event):
    registry = event.app.registry

    registry.registerAdapter(makeTender, (dict, ), ITender, name='Tender')
