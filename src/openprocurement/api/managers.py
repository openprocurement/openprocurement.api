# -*- coding: utf-8 -*-
class Manager(object):
    parent_name = ''
    parent = None

    def __init__(self, parent=None, parent_name=''):
        if all([parent, parent_name]):
            setattr(self, parent_name, parent)
        elif any([parent, parent_name]):
            raise AttributeError('parent and parent_name should be present or absent both')

    def get(self, request):
        raise NotImplementedError

    def get_list(self, request):
        raise NotImplementedError

    def create(self, request):
        raise NotImplementedError

    def update(self, request):
        raise NotImplementedError

    def delete(self, request):
        raise NotImplementedError


class ModelManagerBase(object):

    # DataEngine class
    DATA_ENGINE_CLS = None
    MODEL_CLS = None

    def __init__(self, event, data_engine_cls=None):
        self._event = event
        self._data_engine = self.DATA_ENGINE_CLS() if not data_engine_cls else data_engine_cls()

    def get_applied_data(self):
        return self._data_engine.apply_data_on_model(self._event.data, self._event.context)

    def create_model(self):
        return self._data_engine.create_model(self._event.data, self.MODEL_CLS)
