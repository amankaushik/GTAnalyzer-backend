"""collection of decorators used"""

import sys
import functools
import traceback
from rest_framework.response import Response
import urllib


def error_decorator(func):
    """error decorator for API calls"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        #pylint: disable=broad-except
        except Exception:
            _exc_type, _exc_value, exc_traceback = sys.exc_info()
            response = {'error': traceback.format_tb(exc_traceback), 'saved': False}
            return Response(response, status=500)
    return wrapper


def http_error_decorator(func):
    """error decorator for handling urllib.HTTPError"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs), False
        # pylint: disable=broad-except
        except urllib.error.HTTPError as http_e:
            return http_e.reason, True

    return wrapper
