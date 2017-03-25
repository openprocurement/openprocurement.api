# -*- coding: utf-8 -*-


class ErrorDesctiptorEvent(object):
    """ Error descriptor event.
        'params' attribute can be extended with extra records by event handler.
    """

    def __init__(self, errors, params):
        self.errors = errors
        self.params = params
        self.request = errors.request
