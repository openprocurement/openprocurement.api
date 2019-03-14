# -*- coding: utf-8 -*-
from openprocurement.api.utils.common import (
    apply_data_patch,
    get_db,
    get_now,
    set_modetest_titles,
    get_revision_changes,
)
from openprocurement.api.models.auction_models import Revision
from schematics.exceptions import ModelValidationError


class DataEngine(object):

    def __init__(self, event):
        self._event = event

    def create_model(self, model_cls):
        role = 'create'

        created_model = model_cls(self._event.data)
        created_model.__parent__ = self._event.ctx  # here ctx is Root
        created_model.validate()

        return created_model.serialize(role)

    def apply_data_on_context(self):
        """Applies event.data on event.context and returns applied data wrapped into invalid model
        """
        model_cls = self._event.ctx.l_ctx.ctx_ro.__class__

        initial_data = self._event.ctx.l_ctx.ctx_ro.serialize()
        updated_model = model_cls(initial_data)

        new_patch = apply_data_patch(initial_data, self._event.data)
        if new_patch:
            updated_model.import_data(new_patch, partial=True, strict=True)
        updated_model.__parent__ = self._event.ctx.l_ctx.ctx_ro.__parent__
        updated_model.validate()

        role = self._event.ctx.l_ctx.ctx_ro.get_role(self._event.auth.role)
        method = updated_model.to_patch

        self._event.ctx.cache['l_ctx_updated_data'] = method(role)
        self._event.ctx.cache['l_ctx_updated_model'] = model_cls(self._event.ctx.cache['l_ctx_updated_data'])

    def save(self):
        """Save model to the database & perform all the neccessary checks

        :param m: fork of the context, that contains the changes
        """

        g_ctx = self._event.ctx.g_ctx.ctx  # global edited context
        g_ctx_plain = self._event.ctx.cache['global_ctx_plain']
        db = get_db()

        if g_ctx.mode == u'test':
            set_modetest_titles(g_ctx)

        patch = get_revision_changes(
            g_ctx.serialize('plain'),
            g_ctx_plain
        )

        if patch:
            g_ctx.revisions.append(
                Revision({'author': self._event.auth.user_id,
                          'changes': patch, 'rev': g_ctx.rev}))
            old_date_modified = g_ctx.dateModified
            g_ctx.dateModified = get_now()
            try:
                g_ctx.store(db)
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

    def update(self, save=True):
        data = self._event.ctx.cache['l_ctx_updated_data']
        patch = apply_data_patch(self._event.ctx.l_ctx.ctx.serialize(), data)
        if patch:
            self._event.ctx.l_ctx.ctx.import_data(patch)
            if save:
                return self.save()
