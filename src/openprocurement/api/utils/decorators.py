# -*- coding: utf-8 -*-
from functools import wraps
from openprocurement.api.utils.common import error_handler


def validate_with(validators):
    def actual_validator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            request = args[1]
            kw = {'request': request, 'error_handler': error_handler}
            for validator in validators:
                validator(**kw)
            return func(*args, **kwargs)
        return wrapper
    return actual_validator
