"""Support methods"""

from .APIPayloadKeyConstants import *
from GTAnalyzer.settings import TG_API


def get_password(data):
    """Get GH personal token"""
    token = data.get(TG_PASSWORD) if data.get(TG_PASSWORD) is not None else TG_API.get("TG_TOKEN")
    return token


def get_username(data):
    """Get Taiga username"""
    username = data.get(TG_USERNAME)
    return username


def get_auth_token(data):
    """Get Taiga auth_token"""
    auth_token = data.get(TG_AUTH_TOKEN)
    return auth_token


def get_user_id(data):
    """Get Taiga user id"""
    user_id = data.get(TG_USER_ID)
    return user_id


def check_password_username(password, username):
    """Check that both password and username have non NULL values"""
    if password is None:
        return {'error': "Couldn't load 'password'. Must be present in API payload or as OS env var.",
                'saved': False}
    if username is None:
        return {'error': "Couldn't load 'username'. Must be present in API payload.",
                'saved': False}
    return None
