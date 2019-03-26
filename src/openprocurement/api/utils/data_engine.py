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

    def create_model(self, event, model_cls):
        role = 'create'

        untrusted_model = model_cls(event.data)
        untrusted_model.validate()

        filtered = untrusted_model.serialize(role)
        model = model_cls(filtered)
        model.__parent__ = event.ctx  # here ctx is Root

        return model

    def apply_data_on_context(self, event):
        """Applies event.data on event.context and returns applied data wrapped into invalid model
        """
        model_cls = event.ctx.low.__class__

        initial_data = event.ctx.low.serialize()
        updated_model = model_cls(initial_data)

        new_patch = apply_data_patch(initial_data, event.data)
        if new_patch:
            updated_model.import_data(new_patch, partial=True, strict=True)
        updated_model.__parent__ = event.ctx.low.__parent__
        updated_model.validate()

        role = event.ctx.low.get_role(event.auth.role)
        method = updated_model.to_patch

        event.ctx.cache.low_data = method(role)
        rough_model = event.ctx.cache.low_data_model = model_cls(event.ctx.cache.low_data)

        return rough_model

    def save(self, event, m=None):
        """Save model to the database & perform all the neccessary checks

        :param m: fork of the context, that contains the changes
        """

        high_ctx = m if m else event.ctx.high  # use given model if passed
        unchanged_data = self._data_before_changes(event)
        db = get_db()

        if high_ctx.mode == u'test':
            set_modetest_titles(high_ctx)

        patch = get_revision_changes(
            high_ctx.serialize('plain'),
            unchanged_data
        )

        if patch:
            high_ctx.revisions.append(
                Revision({'author': event.auth.user_id,
                          'changes': patch, 'rev': high_ctx.rev}))
            old_date_modified = high_ctx.dateModified
            high_ctx.dateModified = get_now()
            try:
                high_ctx.store(db)
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

    def update(self, event, save=True):
        data = event.ctx.cache.low_data
        patch = apply_data_patch(event.ctx.low.serialize(), data)
        if patch:
            event.ctx.low.import_data(patch)
            if save:
                return self.save(event)

    def _data_before_changes(self, event):
        cache = getattr(event.ctx.high, 'cache', None)
        if not cache:  # in case of POST
            return {}
        return event.ctx.cache.high_data_plain
