"""
Module to interact with the GitHub API
"""

from urllib.request import Request, urlopen, urlretrieve
from GTAnalyzer.settings import TG_API
from commons.decorators import http_error_decorator
from .APIPayloadKeyConstants import *
import json
import logging


LOGGER = logging.getLogger(__name__)


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
    auth_token = payload[TG_AUTH_TOKEN]
    user_id = payload[TG_USER_ID]
    endpoint = "{}{}".format(TG_API.get("BASE"),
                             TG_API.get("MEMBERSHIP").format(user_id))
    request_obj = Request(endpoint, headers=get_headers(auth_token))
    response = urlopen(request_obj)
    return json.load(response)


@http_error_decorator
def create_project_board(payload):
    """Create a project board"""
    auth_token = payload.pop(TG_AUTH_TOKEN)
    endpoint = "{}{}".format(TG_API.get("BASE"),
                             TG_API.get("CREATE_PROJECT"))
    data = str(json.dumps(payload)).encode('utf-8')
    request_obj = Request(endpoint, data=data, headers=get_headers(auth_token))
    response = urlopen(request_obj)
    return json.load(response)


@http_error_decorator
def add_user_to_project(payload):
    """Add a user to a project board"""
    auth_token = payload.pop(TG_AUTH_TOKEN)
    endpoint = "{}{}".format(TG_API.get("BASE"),
                             TG_API.get("ADD_MEMBERS"))
    data = str(json.dumps(payload)).encode('utf-8')
    request_obj = Request(endpoint, data=data, headers=get_headers(auth_token))
    response = urlopen(request_obj)
    return json.load(response)


@http_error_decorator
def get_project_details(payload):
    """Get project details"""
    project_slug = payload.pop(TG_PROJECT_SLUG)
    auth_token = payload.pop(TG_AUTH_TOKEN)
    endpoint = "{}{}".format(TG_API.get("BASE"),
                             TG_API.get("PROJECT_BY_SLUG").format(project_slug))
    request_obj = Request(endpoint, headers=get_headers(auth_token))
    response = urlopen(request_obj)
    return json.load(response)


@http_error_decorator
def get_milestones(payload, milestone_key):
    """Get project milestones/user-stories/tasks"""
    project_id = payload.pop(TG_PROJECT_ID)
    auth_token = payload.pop(TG_AUTH_TOKEN)
    endpoint = "{}{}".format(TG_API.get("BASE"),
                             TG_API.get(milestone_key).format(project_id))
    request_obj = Request(endpoint, headers=get_headers(auth_token))
    response = urlopen(request_obj)
    return json.load(response)


@http_error_decorator
def get_history(_id, auth_token, key):
    """Get US/Task/Wiki History"""
    endpoint = "{}{}".format(TG_API.get("BASE"),
                             TG_API.get(key).format(_id))
    request_obj = Request(endpoint, headers=get_headers(auth_token))
    response = urlopen(request_obj)
    return json.load(response)


@http_error_decorator
def get_project_export(payload):
    """Get project export"""
    auth_token = payload.pop(TG_AUTH_TOKEN)
    project_id = payload.pop(TG_PROJECT_ID)
    endpoint = "{}{}".format(TG_API.get("BASE"),
                             TG_API.get("EXPORT").format(project_id))
    request_obj = Request(endpoint, headers=get_headers(auth_token))
    response = urlopen(request_obj)
    return {"response": json.load(response), "status": response.status}


@http_error_decorator
def get_exported_data(payload, board_name):
    """Get project export data dump"""
    auth_token = payload.pop(TG_AUTH_TOKEN)
    url = payload.pop(TG_EXPORT_DONE)
    LOGGER.info("URL: %s", url)

    # request_obj = Request(url, headers=get_headers(auth_token))
    # filename = '{}-dump.json'.format(board_name)
    filename, headers = urlretrieve(url)
    LOGGER.info("Filename: %s", filename)
    LOGGER.info("Headers: %s", headers)
    return filename
