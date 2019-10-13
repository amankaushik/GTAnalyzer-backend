"""collection of decorators used"""

import sys
import functools
import traceback
from rest_framework.response import Response
from rest_framework import status
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
            return {'type': 'HTTPError',
                    'message': http_e.reason}, True
        except AssertionError as ae:
            return {'type': 'AssertionError',
                    'message': ae.args}, True
        except Exception as ex:
            _exc_type, _exc_value, exc_traceback = sys.exc_info()
            return {'type': 'Exception',
                    'message': traceback.format_tb(exc_traceback)}, True
    return wrapper


def dataapi_response_decorator(func):
    """decorator for modifying response"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        response, is_error = func(*args, **kwargs)
        if is_error:
            LOGGER.info("Error in dataapi_response_decorator")
            return {'error': response, 'saved': False}, True
        return response, False
    return wrapper


def view_response_decorator(func):
    """decorator for modifying view response"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        response, is_error = func(*args, **kwargs)
        if is_error:
            LOGGER.info("Error in view_response_decorator")
            return Response(response, status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(response)
    return wrapper
