"""
Module to interact with the GitHub API
"""

from urllib.request import Request, urlopen
from GTAnalyzer.settings import GH_API
from .decorators import http_error_decorator
import json


@http_error_decorator
def flight_check(token):
    """check if a user can be authenticated with the info provided"""
    endpoint = "{}{}".format(GH_API.get("BASE"),
                             GH_API.get("FLIGHT_CHECK"))
    request_obj = Request(endpoint, headers=get_headers(token))
    response = urlopen(request_obj)
    return json.load(response)


def get_repository_list(token, _type=None, affiliation=None):
    """get a list of repositories for a user"""
    endpoint = "{}{}".format(GH_API.get("BASE"),
                             GH_API.get("LIST_REPO"))
    if _type is not None:
        endpoint += "type={}".format(_type)
    if affiliation is not None:
        endpoint += "affiliation={}".format(affiliation)
    request_obj = Request(endpoint, headers=get_headers(token))
    response = urlopen(request_obj)
    return json.load(response)


def get_headers(token):
    """Get headers for the GitHub API"""
    headers = {
        "Accept": GH_API.get("V3_HEADER"),
        "Authorization": "token {}".format(token),
        "Content-Type": "application/json"
    }
    return headers


@http_error_decorator
def create_repository(token, payload):
    """Create a new repository
    Creates a new repo with an initial commit"""
    endpoint = "{}{}".format(GH_API.get("BASE"),
                             GH_API.get("CREATE_REPO"))
    data = str(json.dumps(payload)).encode('utf-8')
    request_obj = Request(endpoint, headers=get_headers(token), data=data)
    response = urlopen(request_obj)
    json.load(response)


@http_error_decorator
def add_collaborator(token, payload, owner, repo_name):
    """Add collaborators to an existing repository"""
    headers = get_headers(token)
    headers.update({"Content-Length": 0})
    for user in payload:
        endpoint = "{}{}".format(GH_API.get("BASE"),
                                 GH_API.get("ADD_COLLAB").format(owner, repo_name, user))
        print(endpoint)
        request_obj = Request(endpoint, headers=headers, method="PUT")
        urlopen(request_obj)
    return json.dumps({"done": True})


@http_error_decorator
def enable_protections(token, owner, repo_name, branch="master"):
    """Enable 'protection' on a branch"""
    headers = get_headers(token)
    headers.update({"Accept": "application/vnd.github.luke-cage-preview+json"})
    endpoint = "{}{}".format(GH_API.get("BASE"),
                             GH_API.get("BRANCH_PROTECT").format(owner, repo_name, branch))
    data = str(json.dumps(get_protection_config())).encode('utf-8')
    request_obj = Request(endpoint, headers=headers, method="PUT", data=data)
    response = urlopen(request_obj)
    return json.load(response)


@http_error_decorator
def delete_repository(token, owner, repo_name):
    """Delete an existing repository"""
    endpoint = "{}{}".format(GH_API.get("BASE"),
                             GH_API.get("DELETE_REPO").format(owner, repo_name))
    request_obj = Request(endpoint, headers=get_headers(token), method="DELETE")
    response = urlopen(request_obj)
    return json.load(response)


def get_protection_config():
    """branch protection config"""
    config = dict()
    config["required_status_checks"] = None
    config["enforce_admins"] = None
    config["restrictions"] = None
    config["required_pull_request_reviews"] = {
        "dismiss_stale_reviews": True,
        "require_code_owner_reviews": True,
        "required_approving_review_count": 1
    }
    return config
