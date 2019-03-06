# -*- coding: utf-8 -*-
from openprocurement.api.utils.base_data_engine import DataEngine
from openprocurement.api.utils.common import (
    apply_data_patch,
    set_modetest_titles,
)
from openprocurement.api.models.auction_models import Revision


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

    def save_context(self):
        """Save model to the database & perform all the neccessary checks

        :param m: fork of the context, that contains the changes
        """

        if contract.mode == u'test':
            set_modetest_titles(self._event.context)
        patch = get_revision_changes(contract.serialize("plain"),
                                     request.validated['contract_src'])
        if patch:
            contract.revisions.append(
                Revision({'author': request.authenticated_userid,
                          'changes': patch, 'rev': contract.rev}))
            old_date_modified = contract.dateModified
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
