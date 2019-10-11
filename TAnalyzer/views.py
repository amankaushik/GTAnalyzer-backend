from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework import status
from .decorators import *
from .dataapi import DataExtractor, AuthTokenGetter, MembershipDetailsGetter
import logging


LOGGER = logging.getLogger(__name__)


class APIViewPOST(APIView):
    throttle_classes = (UserRateThrottle,)
    http_method_names = ['post']


class GetAuthTokenView(APIViewPOST):
    """Get Auth token from username and password"""

    @staticmethod
    def post(request):
        """Get authentication header"""
        data = DataExtractor.get_data_object(request)
        response, is_error = AuthTokenGetter.get_auth_token(data)
        if is_error:
            return Response(response, status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(response)


class GetBoardListView(APIViewPOST):
    """Get the list of boards"""

    @staticmethod
    def post(request):
        """get the list of boards"""
        data = DataExtractor.get_data_object(request)
        response, is_error = MembershipDetailsGetter.get_membership_details(data)
        if is_error:
            return Response(response, status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(response)


class CreateBoardView(APIViewPOST):
    """Create new board(s)"""

    @staticmethod
    @error_decorator
    def post(request):
        """create new board(s)"""
        pass
