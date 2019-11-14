"""Support methods"""

import logging
from collections import defaultdict

from TAnalyzer.APIPayloadKeyConstants import *
from GAnalyzer.APIPayloadKeyConstants import *
from commons.decorators import new_thread_decorator

LOGGER = logging.getLogger(__name__)


class FieldExtractor(object):
    """Extract field from payload"""

    @staticmethod
    def get_username(data, api_key):
        """Get username"""
        username = data.get(api_key)
        return username

    @staticmethod
    def get_auth_token(data, api_key):
        """Get auth_token/password"""
        auth_token = data.get(api_key)
        return auth_token

    @staticmethod
    def get_user_id(data):
        """Get Taiga user id"""
        user_id = data.get(TG_USER_ID)
        return user_id


class Validator(object):
    """Perform validations"""

    @staticmethod
    def check_password_username(password, username):
        """Check that both password and username have non NULL values"""
        if password is None:
            return {'error': "Couldn't load 'token/password'. Must be present in API payload.",
                    'saved': False}
        if username is None:
            return {'error': "Couldn't load 'username'. Must be present in API payload.",
                    'saved': False}
        return None

    @staticmethod
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


class PayloadCreator(object):
    """Create a payload dictionary"""

    @staticmethod
    def create_auth_token_user_id_payload(data):
        """Create a dictionary object using auth-token and user-id"""
        auth_token = FieldExtractor.get_auth_token(data, TG_AUTH_TOKEN)
        user_id = FieldExtractor.get_user_id(data)
        return {TG_AUTH_TOKEN: auth_token, TG_USER_ID: user_id}

    @staticmethod
    def create_password_username_payload(data):
        """Create a dictionary object using password and username"""
        username = FieldExtractor.get_username(data, TG_USERNAME)
        password = FieldExtractor.get_auth_token(data, TG_PASSWORD)
        return {TG_USERNAME: username, TG_PASSWORD: password, 'type': 'normal'}

    @staticmethod
    def create_project_creation_payload(data):
        """Create a dictionary object using project details"""
        name = data.get(TG_PROJECT_NAME)
        description = data.get(TG_PROJECT_DESC)
        is_private = data.get(TG_PROJECT_PRIVACY)
        auth_token = FieldExtractor.get_auth_token(data, TG_AUTH_TOKEN)
        return {TG_API_PROJECT_NAME: name, TG_API_PROJECT_DESC: description,
                TG_AUTH_TOKEN: auth_token, TG_PROJECT_PRIVACY: is_private}

    @staticmethod
    def create_bulk_membership_creation_payload(data):
        """Create a dictionary object using project id and member names"""
        payload = {
            TG_API_PROJECT_ID: data[TG_PROJECT_ID],
            TG_API_MEMBERS: [],
            TG_AUTH_TOKEN: data[TG_AUTH_TOKEN]
        }
        for member in data[TG_MEMBERS]:
            payload[TG_API_MEMBERS].append({
                TG_API_ROLE_ID: data[TG_API_ROLE_ID],
                TG_USERNAME: member
            })
        return payload


class DataExtractor(object):
    """Extract 'data' from an HTTP Request"""

    @staticmethod
    def get_data_object(request):
        return request.data

    @staticmethod
    def get_file_upload_object(request):
        return request.FILES


class AnalysisProgressTracker(object):
    """A non-thread safe singleton class to track the progress of an analysis"""
    __instance = None
    # dict of dict
    __analysis_results = None

    @staticmethod
    def get_instance():
        """Get the singleton instance"""
        if AnalysisProgressTracker.__instance is None:
            return AnalysisProgressTracker()
        return AnalysisProgressTracker.__instance

    def __init__(self):
        """Constructor"""
        if AnalysisProgressTracker.__instance is not None:
            raise Exception('Trying to initialize a Singleton class.')
        AnalysisProgressTracker.__instance = self
        self.__analysis_results = defaultdict(dict)

    def get_analysis_results(self, request_id, group_id=None):
        if group_id is not None:
            return self.__analysis_results[request_id][group_id]
        return self.__analysis_results[request_id]

    def set_analysis_results(self, request_id, group_id, value):
        self.__analysis_results[request_id][group_id] = value


class CreateRepoResponse(object):
    """Collection of variables"""
    repo_name = None,  # String
    reason = None,  # String
    failed = None,  # Bool
    failure_step = None,  # String
    collaborator_status = None,  # list
    protection_enabled = None,  # Bool
    repo_created = None  # Bool


class AnalysisResultsPoller(object):
    """Poller for Analysis results"""
    @staticmethod
    def poll(data):
        request_id = data.get('request_id')
        apt_object = AnalysisProgressTracker.get_instance()
        return apt_object.get_analysis_results(request_id), False


class Analyzer(object):
    """Perform analysis"""

    @staticmethod
    def perform_analysis_async(data, list_key, entity_key, performer_class):
        # number of entities to Analyse
        num_combinations = len(data.get(list_key))
        request_id = data.get('request_id')
        Analyzer._perform_analysis_threaded(data, list_key,
                                            entity_key, performer_class)
        return {'saved': True,
                'combinations': num_combinations,
                'request_id': request_id}, False

    @staticmethod
    @new_thread_decorator
    def _perform_analysis_threaded(data, list_key, entity_key,
                                   performer_class):
        # loop through each group in data and
        # perform analysis of each group sequentially
        # get singleton object
        apt_object = AnalysisProgressTracker.get_instance()
        for entity in data.pop(list_key):
            entity_name = entity.get(entity_key)
            result = performer_class.perform_analysis(entity, data)
            apt_object.set_analysis_results(data['request_id'],
                                            entity_name,
                                            result)
        return


class ProjectDetails(object):
    """Project Details Object"""
    id = None,  # String
    name = None,  # String
    members = [],  # List
    milestones = [],  # List of MilestoneDetails object


class MilestoneDetails(object):
    """Milestone Details object"""
    id = None,  # String
    name = None,  # String
    slug = None,  # String
    is_closed = None,  # Bool
    closed_points = None,  # Int
    total_points = None,  # Int
    created_date = None,  # String
    modified_date = None,  # String
    estimated_finish = None,  # String
    estimated_start = None,  # String
    user_stories = [],  # List of UserStoryDetails object


class UserStoryDetails(object):
    """User Story Details"""
    id = None,  # String
    assigned_to = None,  # String (username)
    status = None,  # String
    subject = None,  # String
    total_points = None,  # Int
    created_date = None,  # String
    modified_date = None,  # String
    finish_date = None,  # String
    is_closed = None,  # Bool
    history = [],
    tasks = [],  # List of TaskDetails Object


class TaskDetails(object):
    """Task Details"""
    pass


