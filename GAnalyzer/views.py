from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework import status
from .dataapi import DataExtractor, RepositoryListGetter, RepositoryCreator, FlightChecker, Analyzer, \
    AnalysisResultsPoller
from .decorators import error_decorator
import logging
import random


LOGGER = logging.getLogger(__name__)


class ListRepositoryView(APIView):
    """class to list all the repositories for an account"""
    throttle_classes = (UserRateThrottle,)
    http_method_names = ['post']
    @staticmethod
    @error_decorator
    def post(request):
        """GET the list of all repositories"""
        data = DataExtractor.get_data_object(request)
        response = RepositoryListGetter.get_repository_list(data)
        return Response(response)


class CreateRepositoryView(APIView):
    """Create a new GitHub Repository"""
    throttle_classes = (UserRateThrottle,)
    http_method_names = ['post']
    @staticmethod
    def post(request):
        """Create a new repository"""
        data = DataExtractor.get_data_object(request)
        response, is_error = RepositoryCreator.create_repository(data)
        if is_error:
            return Response(response, status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(response)


class FlightCheckView(APIView):
    """Check if the provided credentials work"""
    throttle_classes = (UserRateThrottle,)
    http_method_names = ['post']

    @staticmethod
    @error_decorator
    def post(request):
        """GET the list of all repositories"""
        data = DataExtractor.get_data_object(request)
        response, is_error = FlightChecker.perform_flight_check(data)
        if is_error:
            return Response(response, status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(response)


class AnalyzeView(APIView):
    """Analyze the GH repository"""
    throttle_classes = (UserRateThrottle,)
    http_method_names = ['post']

    @staticmethod
    @error_decorator
    def post(request):
        """Perform Analysis"""
        data = DataExtractor.get_data_object(request)
        request_id = random.randint(9999, 99999)
        data['request_id'] = request_id
        response, is_error = Analyzer.perform_analysis_async(data)
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
