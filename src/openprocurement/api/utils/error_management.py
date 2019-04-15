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


def model_errors_to_cornice_errors(model_exc):
    errors_gen = (i for i in model_exc.message)

    # use first error occurence to init the exception
    first_error = next(errors_gen)
    ce = CorniceErrors(422, ('body', first_error, model_exc.message[first_error]))

    # add latter errors to the exceptions if any
    for i in errors_gen:
        ce.errors.add('body', i, model_exc.message[i])
    return ce
