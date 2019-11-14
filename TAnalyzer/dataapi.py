"""
Support Module for Views
"""
import logging
from GTAnalyzer.settings import TG_API
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


class ProjectDetailsGetter(object):
    """Get a projects' details"""

    @staticmethod
    def get_project_details_by_slug(board_name, auth_token):
        payload = {
            TG_PROJECT_SLUG: board_name,
            TG_AUTH_TOKEN: auth_token
        }
        details, is_error = TaigaAPI.get_project_details(payload)
        if is_error:
            return {"error": details,
                    "failed": True, "board_name": board_name}, is_error
        return details, is_error

    @staticmethod
    def get_milestones(board_name, project_id, auth_token, milestone_key):
        """Get project milestones/user-stories/tasks"""
        payload = {
            TG_PROJECT_ID: project_id,
            TG_AUTH_TOKEN: auth_token
        }
        details, is_error = TaigaAPI.get_milestones(payload, milestone_key)
        if is_error:
            return {"error": details,
                    "failed": True, "board_name": board_name}, is_error
        return details, is_error


class ProjectExportGetter(object):
    """Get an export of the project's data"""

    @staticmethod
    def request_project_export(project_id, auth_token, board_name):
        payload = {
            TG_PROJECT_ID: project_id,
            TG_AUTH_TOKEN: auth_token
        }
        details, is_error = TaigaAPI.get_project_export(payload)
        if is_error:
            return {"error": details,
                    "failed": True, "board_name": board_name}, is_error
        return details, is_error

    @staticmethod
    def get_exported_data(payload, board_name):
        """Get project export"""
        return TaigaAPI.get_exported_data(payload, board_name)


class AnalysisPerformer(object):
    """Perform Analysis on GH repo"""

    @staticmethod
    @dataapi_response_decorator
    def perform_analysis(board, data):
        # 1. Get project-id from the project-slug
        auth_token = data[TG_AUTH_TOKEN]
        board_name = board[TG_API_PROJECT_NAME]
        # Get Project Details
        project_details, is_error = ProjectDetailsGetter\
            .get_project_details_by_slug(board_name, auth_token)
        if is_error:
            return project_details, is_error
        project_details = AnalysisPerformer._extract_project_details(project_details)
        project_id = project_details.id
        # Get Project Milestones - Provided both Sprint and US
        milestones, is_error = ProjectDetailsGetter\
            .get_milestones(board_name, project_id, auth_token, "MILESTONES")
        if is_error:
            return milestones, is_error
        project_details.milestones = AnalysisPerformer._extract_milestones(milestones)
        # Get US History - For each US
        # TODO
        # Get Project Tasks
        tasks, is_error = ProjectDetailsGetter \
            .get_milestones(board_name, project_id, auth_token, "TASKS")
        if is_error:
            return tasks, is_error
        tasks = AnalysisPerformer._extract_tasks(tasks)
        # 6. Get Task History - For each Task
        # TODO

        return {}, is_error

    @staticmethod
    def _make_project_export_url(project_id, project_slug, export_id):
        """Get the export url string"""
        return TG_API["MEDIA"].format(project_id, project_slug, export_id)

    @staticmethod
    def _extract_project_details(project_details):
        """Extract required project details"""
        extracted = ProjectDetails()
        extracted.id = project_details[TG_PROJECT_ID]
        extracted.name = project_details[TG_ANLS_PRJ_NAME]
        for member in project_details[TG_ANLS_PRJ_MEM]:
            tmp = dict()
            tmp["id"] = member[TG_ANLS_PRJ_MEM_ID]
            tmp["name"] = member[TG_ANLS_PRJ_MEM_NAME]
            tmp["username"] = member[TG_ANLS_PRJ_MEM_UNAME]
            extracted.members.append(tmp)
        return extracted

    @staticmethod
    def _extract_milestones(milestones):
        """Extract required milestone details"""
        details = list()
        for milestone in milestones:
            extracted = MilestoneDetails()
            extracted.id = milestone[TG_ANLS_PRJ_MS_ID]
            extracted.name = milestone[TG_ANLS_PRJ_MS_NAME]
            extracted.slug = milestone[TG_ANLS_PRJ_MS_SLUG]
            extracted.is_closed = milestone[TG_ANLS_PRJ_MS_CLS]
            extracted.total_points = milestone[TG_ANLS_PRJ_MS_TOT_PTS]
            extracted.closed_points = milestone[TG_ANLS_PRJ_MS_CLS_PTS]
            extracted.created_date = milestone[TG_ANLS_PRJ_MS_CR_DT]
            extracted.estimated_finish = milestone[TG_ANLS_PRJ_MS_EST_FIN]
            extracted.estimated_start = milestone[TG_ANLS_PRJ_MS_EST_SRT]
            extracted.modified_date = milestone[TG_ANLS_PRJ_MS_MD_DT]
            for user_story in milestones[TG_ANLS_PRJ_MS_US]:
                us = UserStoryDetails()
                us.id = user_story[TG_ANLS_PRJ_US_ID]
                us.status = user_story[TG_ANLS_PRJ_US_STS_INFO][TG_ANLS_PRJ_US_STS_NAME]
                us.subject = user_story[TG_ANLS_PRJ_US_SUB]
                us.total_points = user_story[TG_ANLS_PRJ_US_TOT_PTS]
                us.modified_date = user_story[TG_ANLS_PRJ_US_MD_DT]
                us.created_date = user_story[TG_ANLS_PRJ_US_CR_DT]
                us.finish_date = user_story[TG_ANLS_PRJ_US_FIN_DT]
                us.is_closed = user_story[TG_ANLS_PRJ_US_IS_CLS]
                us.assigned_to = user_story[TG_ANLS_PRJ_US_ASG_INFO][TG_ANLS_PRJ_US_ASG_TO]
                extracted.user_stories.append(us)
            details.append(extracted)
        return details

    @staticmethod
    def _extract_user_stories(user_stories):
        """Extract required user story details"""
        extracted = dict()
        return extracted

    @staticmethod
    def _extract_tasks(tasks):
        """Extract required task details"""
        extracted = dict()
        return extracted
