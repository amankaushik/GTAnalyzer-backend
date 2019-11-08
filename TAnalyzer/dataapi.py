"""
Support Module for Views
"""
import logging
from TAnalyzer import TaigaAPI
from commons.utils import *
from commons.decorators import dataapi_response_decorator

LOGGER = logging.getLogger(__name__)


class AuthTokenGetter(object):
    """Supporting class for FlightCheckView"""

    @staticmethod
    @dataapi_response_decorator
    def get_auth_token(data):
        payload = PayloadCreator.create_password_username_payload(data)
        return TaigaAPI.get_auth_token(payload)


class MembershipDetailsGetter(object):
    """Get details of a user's memberships"""

    @staticmethod
    @dataapi_response_decorator
    def get_membership_details(data):
        payload = PayloadCreator.create_auth_token_user_id_payload(data)
        response, is_error = TaigaAPI.get_membership_details(payload)
        if not is_error:
            response = MembershipDetailsGetter.extract_project_details(response)
        return response, is_error

    @staticmethod
    def extract_project_details(response):
        """Extract project details from the complete response"""
        # TODO: extract required fields from response
        return response


class ProjectBoardCreator(object):
    """Create a project board"""

    @staticmethod
    @dataapi_response_decorator
    def create_project_board(data):
        payload = PayloadCreator.create_project_creation_payload(data)
        auth_token = payload[TG_AUTH_TOKEN]
        # 1. Create Project Board
        response, is_error = TaigaAPI.create_project_board(payload)
        # 2. Add members to the project
        if not is_error:
            payload_membership = ProjectBoardCreator.extract_project_details(response)
            # add member names to the payload
            payload_membership.update({TG_MEMBERS: data[TG_MEMBERS]})
            # add auth_token to the payload
            payload_membership.update({TG_AUTH_TOKEN: auth_token})
            response, is_error = MembershipCreator.add_user_to_project(payload_membership)
            if not is_error:
                response = ProjectBoardCreator.extract_member_details(response)
            else:
                response.update({"message": "{}\n{}".format(response["message"],
                                                            "Project board created, member addition failed.")})
        else:
            response.update({"message": "{}\n{}".format(response["message"],
                                                        "Project board creation failed.")})
        return response, is_error

    @staticmethod
    def bulk_create_project_boards(projects):
        response_list = []
        for project in projects:
            tmp = {
                TG_PROJECT_NAME: project[TG_PROJECT_NAME],
                TG_PROJECT_DESC: project[TG_PROJECT_DESC],
            }
            response, is_error = ProjectBoardCreator.create_project_board(project)
            tmp.update({TG_ERROR: is_error})
            if is_error:
                tmp.update({TG_ERROR_MESSAGE: response})
            else:
                tmp.update({TG_MEMBERS: response})
            response_list.append(tmp)
        return response_list, False

    @staticmethod
    def extract_project_details(data):
        details = {
            TG_PROJECT_NAME: data[TG_API_PROJECT_NAME],
            TG_PROJECT_SLUG: data[TG_API_PROJECT_SLUG],
            TG_PROJECT_ID: data[TG_PROJECT_ID],
        }
        for role in data[TG_API_ROLES]:
            # hard-coding. Extracting role_id only of "Back" role
            # Each project is assigned unique role_id(s) at the time of creation
            if role["name"] == "Back":
                details.update({TG_API_ROLE_ID: role["id"]})
                break
        return details

    @staticmethod
    def extract_member_details(data):
        return data


class MembershipCreator(object):
    """Add a user as a member to a project"""

    @staticmethod
    def add_user_to_project(data):
        payload = PayloadCreator.create_bulk_membership_creation_payload(data)
        return TaigaAPI.add_user_to_project(payload)


class AnalysisPerformer(object):
    """Perform Analysis on GH repo"""

    @staticmethod
    def perform_analysis(board, data):
        return {board, data}
