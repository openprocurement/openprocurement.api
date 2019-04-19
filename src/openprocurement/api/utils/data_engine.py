# -*- coding: utf-8 -*-
from schematics.exceptions import (
    ModelValidationError,
    ModelConversionError,
)

from openprocurement.api.constants import LOGGER
from openprocurement.api.utils.common import (
    apply_data_patch,
    get_db,
    get_now,
    set_modetest_titles,
    get_revision_changes,
)
from openprocurement.api.models.auction_models import Revision
from openprocurement.api.utils.error_management import model_errors_to_cornice_errors
from openprocurement.api.exceptions import CorniceErrors


class DataEngine(object):

    def create_model(self, event, model_cls):
        role = 'create'

        try:
            untrusted_model = model_cls(event.data)
            untrusted_model.validate()
        except (ModelValidationError, ModelConversionError) as e:
            raise model_errors_to_cornice_errors(e)

        filtered = untrusted_model.serialize(role)
        model = model_cls(filtered)
        model.__parent__ = event.ctx.high  # here ctx is Root

        return model

    def apply_data_on_context(self, event):
        """
        Applies event.data on event.context and returns applied data wrapped into invalid model

        You ask: why this method returns invalid model?
        Because we need to filter the applied data with schematics role to provide protection
        to read-only fields, such as `id`, `rev`, `owner_token`, etc.
        After this filtering only editable fields remain.

        This issue could be solved by applying filtered data on the data on the untouched data
        from the DB, but it's unneccesary.
        """
        model_cls = event.ctx.low.__class__

        initial_data = event.ctx.low.serialize()
        updated_model = model_cls(initial_data)

        new_patch = apply_data_patch(initial_data, event.data)
        try:
            if new_patch:
                updated_model.import_data(new_patch, partial=True, strict=True)
            updated_model.__parent__ = event.ctx.low.__parent__
            updated_model.validate()
        except (ModelValidationError, ModelConversionError) as e:
            raise model_errors_to_cornice_errors(e)

        role = event.ctx.low.get_role(event.auth.role)

        event.ctx.cache.low_data = updated_model.to_patch(role)
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
            except ModelValidationError as e:  # pragma: no cover
                raise model_errors_to_cornice_errors(e)
            except Exception, e:  # pragma: no cover
                raise CorniceErrors(
                    422,
                    ('body', 'data', str(e))
                )
            else:
                event.logging_ctx.set_item('REV', high_ctx.rev)
                journal_logging_ctx = event.logging_ctx.to_journal_logging_context()
                journal_logging_ctx.set_item('MESSAGE_ID', 'save', add_prefix=False)

                LOGGER.info('Saved {}: dateModified {} -> {}'.format(
                    high_ctx.id,
                    old_date_modified and old_date_modified.isoformat(),
                    high_ctx.dateModified.isoformat()),
                    extra=journal_logging_ctx.get_context()
                )
            return True

    def update(self, event, save=True):
        data = event.ctx.cache.low_data
        patch = apply_data_patch(event.ctx.low.serialize(), data)
        if patch:
            event.ctx.low.import_data(patch)
            if save:
                return self.save(event)

    def _data_before_changes(self, event):
        cache = getattr(event.ctx, 'cache', None)
        if not cache:  # in case of POST
            return {}
        return event.ctx.cache.high_data_plain
