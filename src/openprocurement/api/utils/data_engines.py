# -*- coding: utf-8 -*-
from schematics.exceptions import ModelValidationError

from openprocurement.api.utils.base_data_engine import DataEngine
from openprocurement.api.utils.searchers import search_root_child_model
from openprocurement.api.utils.common import (
    apply_data_patch,
    get_db,
    get_now,
    get_revision_changes,
    set_modetest_titles,
)
from openprocurement.api.models.auction_models import Revision


class DataValidationEngine(DataEngine):

    updated_context = property(_get_updated_context)
    updated_context_data = property(_get_updated_context_data)
    created_model = property(_get_created_model)

    def _apply_data_on_context(self):
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

        self._updated_context_data = method(role)
        self._updated_context = model_cls(updated_filtered_model_data)

    def _get_updated_context(self):
        uc = getattr(self, '_updated_context')
        if not uc:
            self._apply_data_on_context()
            uc = self._updated_context
        return uc

    def _get_updated_context_data(self):
        ucd = getattr(self, '_updated_context_data')
        if not ucd:
            self._apply_data_on_context()
            ucd = self._updated_context_data
        return ucd

    def _create_model(self):
        role = 'create'
        model_cls = self._event.context.__class__

        created_model = model_cls(self._event.data)
        created_model.__parent__ = self._event.context.__parent__
        created_model.validate()

        self._created_model = created_model.serialize(role)

    def _get_created_model(self):
        m = getattr(self, '_created_model')
        if not m:
            self._create_model()
            m = self._created_model
        return m




class DataPersistenceEngine(DataEngine):

    def save(self):
        """Save model to the database & perform all the neccessary checks

        :param m: fork of the context, that contains the changes
        """

        ctx = search_root_child_model(self._event.context)
        db = get_db()

        if ctx.mode == u'test':
            set_modetest_titles(ctx)

        patch = get_revision_changes(
            ctx.serialize("plain"),
            self._event._root_model_data
        )

        if patch:
            ctx.revisions.append(
                Revision({'author': self._event.auth.user_id,
                          'changes': patch, 'rev': ctx.rev}))
            # old_date_modified = ctx.dateModified
            ctx.dateModified = get_now()
            try:
                ctx.store(db)
            except ModelValidationError, e:  # pragma: no cover
                for i in e.message:
                    raise RuntimeError("Save error")  # TODO this is temporary stub of exception
                    # request.errors.add('body', i, e.message[i])
                # request.errors.status = 422
            # except Exception, e:  # pragma: no cover
            #     request.errors.add('body', 'data', str(e))
            # else:
            #     LOGGER.info('Saved {}: dateModified {} -> {}'.format(
            #         ctx.id, old_date_modified and old_date_modified.isoformat(),
            #         ctx.dateModified.isoformat()),
            #         extra=context_unpack(request, {'MESSAGE_ID': 'save'},
            #                              {'REV': ctx.rev}))
            return True

    def update_model(self, m):
        pass
