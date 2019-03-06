# -*- coding: utf-8 -*-
from openprocurement.api.utils.common import (
    apply_data_patch,
    set_modetest_titles,
)
from openprocurement.api.models.auction_models import Revision


class DataEngine(object):

    def __init__(self, event):
        self._event = event

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


class DataValidationEngine(DataEngine):

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


class DataPersistenceEngine(DataEngine):

    def save_model(self, m):
        """Save model to the database & perform all the neccessary checks

        :param m: fork of the context, that contains the changes
        """

        if getattr(m, 'mode') == u'test':
            set_modetest_titles(m)
        patch = get_revision_changes(
            m.serialize("plain"),
            self._event.context.serialize("plain")
        )
        if patch:
            contract.revisions.append(
                Revision({'author': self._event.auth.user_id,
                          'changes': patch, 'rev': self._event.context.rev}))
            old_date_modified = self._event.context.dateModified
            contract.dateModified = get_now()
            try:
                contract.store(request.registry.db)
            except ModelValidationError, e:  # pragma: no cover
                for i in e.message:
                    request.errors.add('body', i, e.message[i])
                request.errors.status = 422
            except Exception, e:  # pragma: no cover
                request.errors.add('body', 'data', str(e))
            else:
                LOGGER.info('Saved contract {}: dateModified {} -> {}'.format(
                    contract.id, old_date_modified and old_date_modified.isoformat(),
                    contract.dateModified.isoformat()),
                    extra=context_unpack(request, {'MESSAGE_ID': 'save_contract'},
                                         {'CONTRACT_REV': contract.rev}))
                return True

    def update_model(self, m):
        pass
