import random

from rest_framework.views import APIView
from rest_framework.throttling import UserRateThrottle
from commons.decorators import *
from commons.utils import DataExtractor, Analyzer, AnalysisResultsPoller
from .APIPayloadKeyConstants import *
from .dataapi import AuthTokenGetter, MembershipDetailsGetter, \
    ProjectBoardCreator, AnalysisPerformer, MilestonesGetter
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


class AnalyzeView(APIView):
    """Analyze the Taiga Board"""
    throttle_classes = (UserRateThrottle,)
    http_method_names = ['post']

    @staticmethod
    @error_decorator
    def post(request):
        """Perform Analysis"""
        data = DataExtractor.get_data_object(request)
        request_id = random.randint(9999, 99999)
        data['request_id'] = request_id
        response, is_error = Analyzer.perform_analysis_async(data,
                                                             TG_ANLS_RP_LST,
                                                             TG_ANLS_RP_LST_NAME,
                                                             AnalysisPerformer)
        if is_error:
            return Response(response, status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(response)


class AnalysisResultsPollView(APIView):
    """Poll for Analysis Results"""
    throttle_classes = (UserRateThrottle,)
    http_method_names = ['post']

    @staticmethod
    @error_decorator
    def post(request):
        """Poll Results"""
        data = DataExtractor.get_data_object(request)
        response, is_error = AnalysisResultsPoller.poll(data)
        if is_error:
            return Response(response, status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(response)


class MilestonesView(APIView):
    """Get Milestones for a board"""
    throttle_classes = (UserRateThrottle,)
    http_method_names = ['post']

    @staticmethod
    @error_decorator
    def post(request):
        """Poll Results"""
        data = DataExtractor.get_data_object(request)
        response, is_error = MilestonesGetter.get_milestones(data)
        if is_error:
            return Response(response, status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(response)
