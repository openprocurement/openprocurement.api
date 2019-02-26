# -*- coding: utf-8 -*-
from cornice.errors import Errors


class BaseConfigError(Exception):
    """Base config error class"""
    def __init__(self, msg):
        super(BaseConfigError, self).__init__(msg)
        self.msg = msg

    def __str__(self):
        return self.msg


class ConfigAliasError(BaseConfigError):
    """Error class for aliases stuff."""
    def __init__(self, msg):
        super(ConfigAliasError, self).__init__(msg)
        self.msg = msg


class CorniceErrors(Exception):
    """This exception serves as container for further translation into `error_handler` call"""

    def __init__(self, error_code, error_entry):
        super(CorniceErrors, self).__init__(self)
        self.errors = Errors()
        self.errors.status = error_code
        self.errors.add(*error_entry)
