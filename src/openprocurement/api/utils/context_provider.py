# -*- coding: utf-8 -*-
class ContextProvider(object):
    """Holds both containers for local & global contexts"""

    def __init__(self, high, low):
        self.high = high  # main context
        self.low = low  # subcontext
        self.cache = ContextCache()


class ContextCache(object):
    """Contains atrifacts needed during context lifecycle"""

    _allowed_fields = (
        'high_data_plain',        # unchanged data of the high context
        'low_data',         # unchanged data of the low context
        'low_data_model',   # data of low context load into model (not neccesarily valid)
        'document',  # validated document model
    )

    def __setattr__(self, name, value):
        if name in self._allowed_fields:
            super(ContextCache, self).__setattr__(name, value)
        else:
            raise RuntimeError(
                '{0} can not contain <{1}> attribute'.format(
                    self.__class__.__name__,
                    name
                )
            )
