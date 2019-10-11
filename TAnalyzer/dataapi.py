"""
Support Module for Views
"""
import logging
from TAnalyzer import TaigaAPI
from .utils import *
from .APIPayloadKeyConstants import *


LOGGER = logging.getLogger(__name__)


class AuthTokenGetter(object):
    """Supporting class for FlightCheckView"""

    @staticmethod
    def get_auth_token(data):
        password = get_password(data)
        username = get_username(data)
        result = check_password_username(password, username)
        if result is not None:  # check failed
            return result, True
        payload = {'username': username, 'password': password, 'type': 'normal'}
        response, is_error = TaigaAPI.get_auth_token(payload)
        if is_error:
            return {'error': response, 'saved': False}, True
        return response, False


class DataExtractor(object):
    """Extract 'data' from an HTTP Request"""

    @staticmethod
    def get_data_object(request):
        return request.data

    @staticmethod
    def get_file_upload_object(request):
        return request.FILES


class MembershipDetailsGetter(object):
    """Get details of a user's memberships"""

    @staticmethod
    def get_membership_details(data):
        auth_token = get_auth_token(data)
        user_id = get_user_id(data)
        payload = {'auth_token': auth_token, 'user_id': user_id}
        response, is_error = TaigaAPI.get_membership_details(payload)
        if is_error:
            return {'error': response, 'saved': False}, True
        response = MembershipDetailsGetter.extract_project_details(response)
        return response, False

    @staticmethod
    def extract_project_details(response):
        """Extract project details from the complete response"""
        return response
