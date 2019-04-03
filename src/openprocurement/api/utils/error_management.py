# -*- coding: utf-8 -*-
from functools import wraps

from openprocurement.api.exceptions import CorniceErrors
from openprocurement.api.utils.common import error_handler


def handle_errors_on_view(func):
    """Decorator used to enable error handling for a particular view"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        view_obj = args[0]
        rq = view_obj.request
        try:
            return func(*args, **kwargs)
        except CorniceErrors as exc:
            rq.errors += exc.errors
            rq.errors.status = exc.errors.status
            raise error_handler(rq)

    return wrapper
