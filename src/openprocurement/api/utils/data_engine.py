# -*- coding: utf-8 -*-
from openprocurement.api.utils.common import apply_data_patch


class DataEngine(object):

    def __init__(self, event):
        self._event = event

    def apply_data_on_model(self):
        """Applies event.data on event.context and returns applied data wrapped into invalid model
        """
        model_cls = self._event.context.__class__

        initial_data = self._event.context.serialize()
        updated_model = model_cls(initial_data)

        new_patch = apply_data_patch(initial_data, self._event.data)
        if new_patch:
            updated_model.import_data(new_patch, partial=True, strict=True)
        updated_model.__parent__ = self._event.context.__parent__
        updated_model.validate()

        role = self._event.context.get_role(self._event.auth.role)
        method = updated_model.to_patch

        updated_filtered_model_data = method(role)
        updated_filtered_model = model_cls(updated_filtered_model_data)

        return updated_filtered_model

    def create_model(self, data, model):
        role = 'create'
        model_cls = self._event.context.__class__

        updated_model = model_cls(self._event.data)
        updated_model.__parent__ = self._event.context.__parent__
        updated_model.validate()
        method = updated_model.serialize

        return method(role)

    @staticmethod
    def copy_model(m):
        """
        Copies schematics model

        copy.deepcopy won't work here, bacause the model object's internals cannot be copied.
        """
        m_cls = m.__class__
        data = m.serialize()
        m_copy = m_cls(data)

        if hasattr(m, '__parent__'):
            m_copy.__parent__ = m.__parent__

        return m_copy
