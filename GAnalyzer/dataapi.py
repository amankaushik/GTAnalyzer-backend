"""
Support Module for Views
"""
from .GitHubAPI import *
from .utils import *
from .custom_exceptions import CreateRepoFlowBroken
from .APIPayloadKeyConstants import *
import csv


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
        if result is None:
            return result, True
        reader = csv.DictReader(data[key].read().decode('utf-8').splitlines())
        parsed = [RepositoryCreator.sanitize_csv_row(row) for row in reader]
        parsed = RepositoryCreator.check_for_optional_fields(parsed)
        parsed, _error = validate_repo_create_csv(parsed)
        if parsed is None:  # validation failed
            return _error, True
        payload = RepositoryCreator.prepare_repo_flow_payload(parsed)
        return RepositoryCreator.create_repo_flow(payload, token, username), False

    @staticmethod
    def sanitize_csv_row(row):
        return {key.strip(): value.strip() for key, value in row.items()}

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
                "add_collaborators": []
            }
        for record in parsed:
            for key in record.keys():
                if key == collaborator_name or key == "":
                    payload[record.get(repo_name)]["add_collaborators"].append(record[key])

        return payload

    @staticmethod
    def create_repo_flow(payload, token, username):
        flow_response = {}
        create_success = []
        create_failure = {}
        for key, value in payload.items():
            # creating a repo, adding collaborators and adding branch protection is one
            # atomic transaction
            try:
                response, is_error = create_repository(token, value["create_repo"])
                if is_error:
                    raise CreateRepoFlowBroken({"reason": response, "repo_created": False,
                                                "step": "create repo"})
                response, is_error = add_collaborator(token, value["add_collaborators"],
                                                      username, key)
                if is_error:
                    _, repo_deleted = delete_repository(token, username, key)
                    raise CreateRepoFlowBroken({"reason": response, "repo_created": True,
                                                "repo_deleted": (not repo_deleted, _),
                                                "step": "add collaborators"})
                response, is_error = enable_protections(token, username, key)
                if is_error:
                    _, repo_deleted = delete_repository(token, username, key)
                    raise CreateRepoFlowBroken({"reason": response, "repo_created": True,
                                                "repo_deleted": not repo_deleted,
                                                "step": "enable branch protection"})
                create_success.append(key)
            except CreateRepoFlowBroken as ex:
                create_failure[key] = ex.args
        flow_response["failed_repositories"] = create_failure
        flow_response["successful_repositories"] = create_success
        return flow_response
