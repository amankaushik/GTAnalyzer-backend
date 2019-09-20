"""Support methods"""
from collections import namedtuple

from .APIPayloadKeyConstants import *
from GTAnalyzer.settings import GH_API


def validate_repo_create_csv(parsed):
    """validate the read/parsed csv data"""
    repo_name = GH_CREAT_REPO_REPO_NAME_KEY
    collaborator_name = GH_CREAT_REPO_COLLABORATOR_NAME_KEY
    try:
        assert "At least one record should be present", len(parsed) >= 1
        for record in parsed:
            assert "{} and at least one {} should be present".format(repo_name, collaborator_name), \
                len(record) >= 2
            if record.get(repo_name) is None:
                raise AssertionError("'{}' header not present".format(repo_name))
            if record.get(collaborator_name) is None:
                raise AssertionError("'{}' header not present".format(collaborator_name))
        return parsed, None
    except AssertionError as ae:
        return None, ae.args


def get_token(data):
    """Get GH personal token"""
    token = data.get(GH_TOKEN) if data.get(GH_TOKEN) is not None else GH_API.get("GH_TOKEN")
    return token


def get_username(data):
    """Get GH username"""
    username = data.get(GH_USERNAME)
    return username


def check_token_username(token, username):
    """Check that both token and username have non NULL values"""
    if token is None:
        return {'error': "Couldn't load 'token'. Must be present in API payload or as OS env var.",
                'saved': False}
    if username is None:
        return {'error': "Couldn't load 'username'. Must be present in API payload.",
                'saved': False}
    return None


class CreateRepoResponse(object):
    """Collection of named-tuples"""
    repo_name = None,  # String
    reason = None,  # String
    failed = None,  # Bool
    failure_step = None,  # String
    collaborator_status = None,  # list
    protection_enabled = None,  # Bool
    repo_created = None  # Bool
