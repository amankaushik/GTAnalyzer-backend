"""
Support Module for Views
"""
import logging
from .GitHubAPI import *
from .utils import *
from .custom_exceptions import CreateRepoFlowBroken
from .APIPayloadKeyConstants import *

LOGGER = logging.getLogger(__name__)


class FlightChecker(object):
    """Supporting class for FlightCheckView"""

    @staticmethod
    def perform_flight_check(data):
        token = get_token(data)
        username = get_username(data)
        result = check_token_username(token, username)
        if result is not None:  # check failed
            return result, True
        response, is_error = flight_check(token)
        if is_error:
            return {'error': response, 'saved': False}, True
        if response.get("login").lower() != username.lower():
            return {'error': "Provided username: '{}' doesn't match the token username: '{}'".format(
                username, response["login"].lower()),
                       'saved': False}, True
        return response, False


class RepositoryListGetter(object):
    """Getter class for ListRepositoryView"""

    @staticmethod
    def get_repository_list(data):
        token = get_token(data)
        return get_repository_list(token)


class DataExtractor(object):
    """Extract 'data' from an HTTP Request"""

    @staticmethod
    def get_data_object(request):
        return request.data

    @staticmethod
    def get_file_upload_object(request):
        return request.FILES


class RepositoryCreator(object):
    """Creator class for CreateRepositoryView"""

    @staticmethod
    def create_repository(data, key="file"):
        token = get_token(data)
        username = get_username(data)
        result = check_token_username(token, username)
        if result is not None:  # token-username validation failed
            return result, True
        parsed = list(map(lambda x: RepositoryCreator.sanitize_row(x),
                          data.get(GH_CREATE_DATA)))
        parsed = RepositoryCreator.convert_list_to_dic(parsed)
        parsed = RepositoryCreator.check_for_optional_fields(parsed)
        payload = RepositoryCreator.prepare_repo_flow_payload(parsed)
        return RepositoryCreator.create_repo_flow(payload, token, username), False

    @staticmethod
    def convert_list_to_dic(data):
        """covert list data to dictionary"""
        repo_name = GH_CREAT_REPO_REPO_NAME_KEY
        collaborator_name = GH_CREAT_REPO_COLLABORATOR_NAME_KEY
        # the fist entry of the list is the repository name
        # every other entry is the name of a collaborator
        records = []
        for row in data:
            tmp = dict()
            tmp[repo_name] = row[0]
            tmp[collaborator_name] = row[1:]
            records.append(tmp)
        return records

    @staticmethod
    def sanitize_row(row):
        return list(map(lambda x: x.strip(" "), row))

    @staticmethod
    def check_for_optional_fields(parsed):
        private = GH_CREAT_REPO_IS_PRIVATE_KEY
        for record in parsed:
            if record.get(private) is None:
                record[private] = True
        return parsed

    @staticmethod
    def prepare_repo_flow_payload(parsed):
        """Prepare payload to be used to create a repo and then add
        collaborators to it and enable protection on the master branch"""
        repo_name = GH_CREAT_REPO_REPO_NAME_KEY
        private = GH_CREAT_REPO_IS_PRIVATE_KEY
        collaborator_name = GH_CREAT_REPO_COLLABORATOR_NAME_KEY
        payload = {}
        for record in parsed:
            payload[record.get(repo_name)] = {
                "create_repo": {
                    "name": record.get(repo_name),
                    "auto_init": True,  # without this an empty repo is created (no branch)
                    "private": record.get(private),
                },
                "add_collaborators": record.get(collaborator_name)
            }
        return payload

    @staticmethod
    def create_repo_flow(payload, token, username):
        flow_response = {}
        for key, value in payload.items():
            # creating a repo, adding collaborators and adding branch protection is one
            # atomic transaction
            try:
                response, is_error = create_repository(token, value["create_repo"])
                if is_error:
                    raise CreateRepoFlowBroken({"reason": response, "repo_created": False,
                                                "step": "create repo", "repo_deleted": None,
                                                "failed": True})
                response, is_error = add_collaborator(token, value["add_collaborators"],
                                                      username, key)
                if is_error:
                    _, repo_deleted = delete_repository(token, username, key)
                    raise CreateRepoFlowBroken({"reason": response, "repo_created": True,
                                                "repo_deleted": (not repo_deleted, _),
                                                "step": "add collaborators", "failed": True})
                response, is_error = enable_protections(token, username, key)
                if is_error:
                    _, repo_deleted = delete_repository(token, username, key)
                    raise CreateRepoFlowBroken({"reason": response, "repo_created": True,
                                                "repo_deleted": not repo_deleted,
                                                "step": "enable branch protection",
                                                "failed": True})
                flow_response[key] = [{"reason": "N/A", "repo_created": True,
                                       "step": "N/A", "repo_deleted": None,
                                       "failed": False}]
            except CreateRepoFlowBroken as ex:
                flow_response[key] = ex.args
        return flow_response
