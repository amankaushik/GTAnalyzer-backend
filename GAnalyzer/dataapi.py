"""
Support Module for Views
"""
import logging
from .GitHubAPI import *
from .utils import *
from .APIPayloadKeyConstants import *
from .decorators import new_thread_decorator

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
                "collaborators": record.get(collaborator_name)
            }
        return payload

    @staticmethod
    def create_repo_flow(payload, token, username):
        crr = CreateRepoResponse()
        flow_response = []
        for key, value in payload.items():
            # creating a repo, adding collaborators and adding branch protection is one
            # atomic transaction
            crr.repo_name = key
            # 1. Create the repo
            response, is_error = create_repository(token, value["create_repo"])
            crr.repo_created = not is_error
            if is_error:
                crr.reason = response  # Only set reason if there is a failure
                crr.failed = True
                crr.failure_step = "Repo Creation"
                flow_response.append(crr.__dict__)
                break

            # 2. Add collaborators
            collaborator_response = []
            for collaborator in value["collaborators"]:
                response, is_error = add_collaborator(token, username, key, collaborator)
                collaborator_response.append({"collab_name": collaborator, collaborator: response, "failed": is_error})
            crr.collaborator_status = collaborator_response

            # 3. Enable branch protection on master branch
            response, is_error = enable_protections(token, username, key)
            crr.protection_enabled = not is_error
            if is_error:
                crr.reason = response  # Only set reason if there is a failure
                crr.failed = True
                crr.failure_step = "Enable Branch Protection"
                flow_response.append(crr.__dict__)
                break

            # 4. Create new commit
            # TODO

            flow_response.append(crr.__dict__)
        return flow_response


class Analyzer(object):
    """Perform repository analysis"""

    @staticmethod
    def perform_analysis_async(data):
        Analyzer._perform_analysis_threaded(data)
        # TODO: remove hard-coding
        return {'saved': True,
                'combinations': 10}, False

    @staticmethod
    @new_thread_decorator
    def _perform_analysis_threaded(data):
        # loop through each group in data and
        # perform analysis of each group sequentially
        from random import randint
        import time
        # get singleton object
        apt_object = AnalysisProgressTracker.get_instance()
        for _ in data['combinations']:
            apt_object.set_analysis_results(data['request_id'],
                                            randint(0, 100),
                                            "Checked")
            time.sleep(5)
        return


class AnalysisResultsPoller(object):
    """Poller for Analysis results"""

    @staticmethod
    def poll(data):
        apt_object = AnalysisProgressTracker.get_instance()
        return apt_object.get_analysis_results(), False
