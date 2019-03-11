# -*- coding: utf-8 -*-
from openprocurement.api.utils.common import copy_model


class ContextProvider(object):
    """Holds both containers for local & global contexts"""
    
    def __init__(self, local_ctx, global_ctx):
        self.l_ctx = local_ctx
        self.g_ctx = global_ctx


class ContextProviderCached(ContextProvider):
    """Contains different contexts & provides cache for different serializations"""

    def __init__(self, *args, **kwargs):
        super(ContextProviderCached, self).__init__(self, *args, **kwargs)
        self.cache = dict()


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


class ContextBuilderFromRequest(object):
    """Builds ContextProvider from objects found in the request"""

    @staticmethod
    def build(local_ctx, global_ctx, global_plain_ctx):
        """Build ContextProviderCached

        :param local_ctx: ContextContainer with local context
        :param global_ctx: ContextContainer with global context
        :param global_plain_ctx: global context serialized with `plain` role
        """
        local_ctx_container = ContextContainer(local_ctx)
        global_ctx_container = ContextContainer(global_ctx)

        cp = ContextProviderCached(local_ctx_container, global_ctx_container)
        cp.cache['global_ctx_plain'] = global_ctx_plain

        return cp
