"""
Module to interact with the GitHub API
"""

import urllib
from urllib.request import Request, urlopen
from urllib import parse
from GTAnalyzer.settings import TG_API
from .decorators import http_error_decorator
import json


@http_error_decorator
def get_auth_token(payload):
    """Get authentication token using username and password"""
    endpoint = "{}{}".format(TG_API.get("BASE"),
                             TG_API.get("AUTH"))
    data = str(json.dumps(payload)).encode('utf-8')
    request_obj = Request(endpoint, data=data, headers=get_headers())
    response = urlopen(request_obj)
    return json.load(response)


def get_headers(token=None):
    """Get headers for the GitHub API"""
    headers = {
        "Content-Type": "application/json"
    }
    if token is not None:
        headers.update({"Authorization": "Bearer {}".format(token)})
    return headers


@http_error_decorator
def get_membership_details(payload):
    """Get details of a user's memberships"""
    auth_token = payload["auth_token"]
    user_id = payload["user_id"]
    endpoint = "{}{}".format(TG_API.get("BASE"),
                             TG_API.get("MEMBERSHIP").format(user_id))
    request_obj = Request(endpoint, headers=get_headers(auth_token))
    response = urlopen(request_obj)
    return json.load(response)
