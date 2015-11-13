from openprocurement.api.models import Tender, TenderEU
from openprocurement.api.interfaces import ITender, ITenderEU, IBaseTender
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


class makeTenderEU(makeBaseTender):
    model = TenderEU


class loadTender(object):
    def __init__(self, request, tid):
        self.request = request
        self.tid = tid

    def _tenderAdapter(self):
        db = self.request.registry.db
        doc = db.get(self.tid)
        if doc is None:
            return None

        return self.request.registry.queryAdapter(doc, IBaseTender,
                                                  name=doc.get('subtype',
                                                               'Tender'))

    def tender(self):
        adapter = self._tenderAdapter()
        if adapter is None:
            return None
        return adapter.tender()

    @property
    def model(self):
        adapter = self._tenderAdapter()
        if adapter is None:
            return None
        return adapter.model


@subscriber(ApplicationCreated)
def register_adapters(event):
    registry = event.app.registry

    registry.registerAdapter(makeTender, (dict, ), ITender, name='Tender')
    registry.registerAdapter(makeTenderEU, (dict, ), ITenderEU,
                             name='TenderEU')

    registry.registerAdapter(loadTender, (Request, unicode), IBaseTender)
