# -*- coding: utf-8 -*-


class ErrorDesctiptorEvent(object):
    """ Error descriptor event.
        'params' attribute can be extended with extra records by event handler.
    """

    def __init__(self, request, params):
        self.errors = request.errors
        self.params = params
        self.request = request
