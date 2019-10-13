from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework import status
from .decorators import *
from .utils import DataExtractor
from .dataapi import AuthTokenGetter, MembershipDetailsGetter,\
    ProjectBoardCreator
import logging


LOGGER = logging.getLogger(__name__)


class APIViewPOST(APIView):
    throttle_classes = (UserRateThrottle,)
    http_method_names = ['post']


class GetAuthTokenView(APIViewPOST):
    """Get Auth token from username and password"""

    @staticmethod
    @view_response_decorator
    def post(request):
        """Get authentication header"""
        data = DataExtractor.get_data_object(request)
        return AuthTokenGetter.get_auth_token(data)


class GetBoardListView(APIViewPOST):
    """Get the list of boards"""

    @staticmethod
    @view_response_decorator
    def post(request):
        """get the list of boards"""
        data = DataExtractor.get_data_object(request)
        return MembershipDetailsGetter.get_membership_details(data)


class CreateBoardView(APIViewPOST):
    """Create new board(s)"""

    @staticmethod
    @view_response_decorator
    def post(request):
        """create new board(s)"""
        data = DataExtractor.get_data_object(request)
        return ProjectBoardCreator.bulk_create_project_boards(data)
