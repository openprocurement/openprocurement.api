# -*- coding: utf-8 -*-
class DataEngine(object):

    def __init__(self, event):
        self._event = event

    @staticmethod
    def copy_model(m):
        """
        Copies schematics model

        copy.deepcopy won't work here, bacause the model object's internals cannot be copied.
        """
        m_cls = m.__class__
        data = m.serialize()
        m_copy = m_cls(data)

        if hasattr(m, '__parent__'):
            m_copy.__parent__ = m.__parent__

        return m_copy
