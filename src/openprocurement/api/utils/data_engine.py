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

        untrusted_model = model_cls(self._event.data)
        untrusted_model.__parent__ = self._event.ctx  # here ctx is Root
        untrusted_model.validate()

        filtered = untrusted_model.serialize(role)
        model = model_cls(filtered)

        return model

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

        self._event.ctx.cache.low_data = method(role)
        self._event.ctx.cache.low_data_model = model_cls(self._event.ctx.cache.low_data)

    def save(self):
        """Save model to the database & perform all the neccessary checks

        :param m: fork of the context, that contains the changes
        """

        high_ctx = self._event.ctx.high  # global edited context
        unchanged_data = self._unchanged_data()
        db = get_db()

        if high_ctx.mode == u'test':
            set_modetest_titles(high_ctx)

        patch = get_revision_changes(
            high_ctx.serialize('plain'),
            unchanged_data
        )

        if patch:
            high_ctx.revisions.append(
                Revision({'author': self._event.auth.user_id,
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

    def update(self, save=True):
        data = self._event.ctx.cache.low_data
        patch = apply_data_patch(self._event.ctx.low.serialize(), data)
        if patch:
            self._event.ctx.low.import_data(patch)
            if save:
                return self.save()

    def _unchanged_data(self):
        cache = getattr(self._event.ctx.high, 'cache', None)
        if not cache:  # in case of POST
            return {}
        return self._event.ctx.cache.high_data_plain


class RevisionBuilderFacade(object):
    pass


class BaseRevisionBuilder(object):

    def __init__(self, event):
        self._event = event

    def build(self):
        raise NotImplementedError

class InitialRevisionBuilder(BaseRevisionBuilder):
    """Build Revision object for a freshly created object"""

    def build(self):
        pass


class CommonRevisionBuilder(BaseRevisionBuilder):
    """Build Revision object for common change of some object"""

    def build(self):
        pass
