"""collection of decorators used"""

import sys
import functools
import traceback
from threading import Thread
from rest_framework.response import Response
import urllib
import logging


LOGGER = logging.getLogger(__name__)


def error_decorator(func):
    """error decorator for API calls"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        #pylint: disable=broad-except
        except Exception as ex:
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
        #pylint: disable=broad-except
        except urllib.error.HTTPError as http_e:
            return http_e.reason, True
        except AssertionError as ae:
            return ae.args, True
        except Exception as ex:
            return ex.args, True
    return wrapper


def new_thread_decorator(func):
    """create a new daemon thread"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        LOGGER.info("starting new thread")
        t = Thread(target=func, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()
    return wrapper
