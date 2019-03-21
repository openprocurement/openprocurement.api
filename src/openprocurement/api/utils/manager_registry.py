# -*- coding: utf-8 -*-
from pyramid.threadlocal import get_current_registry


class ManagerRegistry(object):
    """Registry for model managers"""

    NAME_IN_GLOBAL_REGISTRY = 'manager_registry'

    def __init__(self):
        self._mapping = {}

    def get_manager(self, name):
        return self._mapping.get(name)

    def register_manager(self, slug, manager_cls):
        self._mapping[slug] = manager_cls


def init_manager_registry(registry):

    new_mr = ManagerRegistry()
    setattr(registry, ManagerRegistry.NAME_IN_GLOBAL_REGISTRY, new_mr)
