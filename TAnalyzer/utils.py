"""Support methods"""

from .APIPayloadKeyConstants import *
from GTAnalyzer.settings import TG_API


class FieldExtractor(object):
    """Extract field from payload"""

    @staticmethod
    def get_password(data):
        """Get GH personal token"""
        token = data.get(TG_PASSWORD) if data.get(TG_PASSWORD) is not None else TG_API.get("TG_TOKEN")
        return token

    @staticmethod
    def get_username(data):
        """Get Taiga username"""
        username = data.get(TG_USERNAME)
        return username

    @staticmethod
    def get_auth_token(data):
        """Get Taiga auth_token"""
        auth_token = data.get(TG_AUTH_TOKEN)
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
            return {'error': "Couldn't load 'password'. Must be present in API payload or as OS env var.",
                    'saved': False}
        if username is None:
            return {'error': "Couldn't load 'username'. Must be present in API payload.",
                    'saved': False}
        return None


class PayloadCreator(object):
    """Create a payload dictionary"""

    @staticmethod
    def create_auth_token_user_id_payload(data):
        """Create a dictionary object using auth-token and user-id"""
        auth_token = FieldExtractor.get_auth_token(data)
        user_id = FieldExtractor.get_user_id(data)
        return {TG_AUTH_TOKEN: auth_token, TG_USER_ID: user_id}

    @staticmethod
    def create_password_username_payload(data):
        """Create a dictionary object using password and username"""
        username = FieldExtractor.get_username(data)
        password = FieldExtractor.get_password(data)
        return {TG_USERNAME: username, TG_PASSWORD: password, 'type': 'normal'}

    @staticmethod
    def create_project_creation_payload(data):
        """Create a dictionary object using project details"""
        name = data.get(TG_PROJECT_NAME)
        description = data.get(TG_PROJECT_DESC)
        is_private = data.get(TG_PROJECT_PRIVACY)
        auth_token = FieldExtractor.get_auth_token(data)
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
