"""
Module to interact with the GitHub API
"""

from urllib.request import Request, urlopen
from GTAnalyzer.settings import GH_API
from commons.decorators import http_error_decorator
import json
import logging

LOGGER = logging.getLogger(__name__)


@http_error_decorator
def flight_check(token):
    """check if a user can be authenticated with the info provided"""
    endpoint = "{}{}".format(GH_API.get("BASE"),
                             GH_API.get("FLIGHT_CHECK"))
    request_obj = Request(endpoint, headers=get_headers(token))
    response = urlopen(request_obj)
    return json.load(response)


@http_error_decorator
def get_repository_list(token, page,  _type=None, affiliation=None):
    """get a list of repositories for a user"""
    endpoint = "{}{}".format(GH_API.get("BASE"),
                             GH_API.get("LIST_REPO").format(page))
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


"""
@payload: a list of strings
"""
@http_error_decorator
def add_collaborator(token, owner, repo_name, collaborator_name):
    """Add collaborators to an existing repository"""
    headers = get_headers(token)
    # PUT request with no parameters
    headers.update({"Content-Length": 0})
    endpoint = "{}{}".format(GH_API.get("BASE"),
                             GH_API.get("ADD_COLLAB").format(owner, repo_name, collaborator_name))
    request_obj = Request(endpoint, headers=headers, method="PUT")
    response = urlopen(request_obj)
    return json.load(response)


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


@http_error_decorator
def get_commit(token, owner, repo_name, branch, start_date, end_date, author=None):
    """Get commits for the given repository for the given date range """
    endpoint = "{}{}".format(GH_API.get("BASE"),
                             GH_API.get("GET_COMMIT")
                             .format(owner, repo_name, branch, start_date, end_date))
    # Get commits only for a single author
    if author is not None:
        endpoint += "&author={}".format(author)
    request_obj = Request(endpoint, headers=get_headers(token))
    response = urlopen(request_obj)
    return json.load(response)


@http_error_decorator
def get_single_commit(token, owner, repo_name, sha):
    """Get a single commit"""
    endpoint = "{}{}".format(GH_API.get("BASE"),
                             GH_API.get("GET_SINGLE_COMMIT")
                             .format(owner, repo_name, sha))
    request_obj = Request(endpoint, headers=get_headers(token))
    response = urlopen(request_obj)
    return json.load(response)


@http_error_decorator
def get_single_pr(token, owner, repo_name, pr_num):
    """Get a single PR"""
    endpoint = "{}{}".format(GH_API.get("BASE"),
                             GH_API.get("GET_SINGLE_PR")
                             .format(owner, repo_name, pr_num))
    request_obj = Request(endpoint, headers=get_headers(token))
    response = urlopen(request_obj)
    return json.load(response)


@http_error_decorator
def get_collaborators(token, owner, repo_name):
    """get a list of collaborators for a repositories"""
    endpoint = "{}{}".format(GH_API.get("BASE"),
                             GH_API.get("GET_COLLAB").format(owner, repo_name))
    request_obj = Request(endpoint, headers=get_headers(token))
    response = urlopen(request_obj)
    return json.load(response)


@http_error_decorator
def get_pr(token, owner, repo_name, state="all"):
    """Get PRs for the given repository"""
    endpoint = "{}{}".format(GH_API.get("BASE"),
                             GH_API.get("GET_PR").format(owner, repo_name, state))
    request_obj = Request(endpoint, headers=get_headers(token))
    response = urlopen(request_obj)
    return json.load(response)


@http_error_decorator
def get_branches(token, owner, repo_name):
    """Get all branch names"""
    endpoint = "{}{}".format(GH_API.get("BASE"),
                             GH_API.get("GET_BRANCHES").format(owner, repo_name))
    request_obj = Request(endpoint, headers=get_headers(token))
    response = urlopen(request_obj)
    return json.load(response)
