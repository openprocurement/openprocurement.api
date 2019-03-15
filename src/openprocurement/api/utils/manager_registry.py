# -*- coding: utf-8 -*-
from pyramid.threadlocal import get_current_registry


class ManagerRegistry(object):
    """Registry for model managers"""

    _NAME_IN_GLOBAL_REGISTRY = 'manager_registry'

    def __init__(self):
        self._mapping = {}

    def get_manager(self, name):
        return self._mapping.get(name)

    def register_manager(self, slug, manager_cls):
        self._mapping[slug] = manager_cls

    @classmethod
    def get_manager_registry(cls):
        """Get global manager registry instance

        This classmethod provides singleton functionality for the class.
        """
        r = get_current_registry()
        mr = getattr(r, cls._NAME_IN_GLOBAL_REGISTRY, None)

        if mr:
            return mr

        new_mr = cls()
        setattr(r, cls._NAME_IN_GLOBAL_REGISTRY, new_mr)
        return new_mr
