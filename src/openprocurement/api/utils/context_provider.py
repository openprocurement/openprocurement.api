# -*- coding: utf-8 -*-
from openprocurement.api.utils.common import copy_model


class ContextProvider(object):
    
    def __init__(self, local_ctx, global_ctx):
        self.l_ctx = local_ctx
        self.g_ctx = global_ctx


class ContextContainer(object):
    """Holds the context in two entities
    
    _ctx_ro - original unmodified context (read-only)
    _ctx - lazy copy of the original context
    """

    def __init__(self, ctx):
        self._ctx_ro = ctx

    @property
    def ctx(self):
        ctx = getattr(self, '_ctx')
        if not ctx:
            self._ctx = copy_model(self._ctx_ro)
        return self._ctx

    @property
    def ctx_ro(self):
        return self._ctx_ro
