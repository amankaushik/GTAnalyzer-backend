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


class AnalysisPerformer(object):
    """Perform Analysis on GH repo"""

    @staticmethod
    def perform_analysis(board, data):
        # 1. Get project-id from the project-slug
        auth_token = data[TG_AUTH_TOKEN]
        board_name = board[TG_API_PROJECT_NAME]
        # Get Project Details
        project_details, is_error = ProjectDetailsGetter\
            .get_project_details_by_slug(board_name, auth_token)
        if is_error:
            return project_details
        project_details = AnalysisPerformer._extract_project_details(project_details)
        # Get Project Milestones - Provided both Sprint and US
        milestones, is_error = ProjectDetailsGetter\
            .get_milestones(board_name, project_details.id, auth_token, "MILESTONES")
        if is_error:
            return milestones
        project_details.milestones = AnalysisPerformer._extract_milestones(milestones)

        # Get Project Tasks
        tasks, is_error = ProjectDetailsGetter \
            .get_milestones(board_name, project_details.id, auth_token, "TASKS")
        if is_error:
            return tasks
        tasks = AnalysisPerformer._extract_tasks(tasks)

        # Integrate Tasks with US
        project_details = AnalysisPerformer._integrate_tasks(project_details, tasks)

        # Get History - For each US and Task
        project_details = AnalysisPerformer._get_history(project_details, auth_token)

        project_details = json.loads(project_details.to_json())
        return project_details

    @staticmethod
    def _integrate_tasks(project_details, tasks):
        """Integrate task details with US"""
        task_dict = defaultdict(list)
        for task in tasks:
            task_dict[task.user_story].append(task)
        for milestone in project_details.milestones:
            for user_story in milestone.user_stories:
                user_story.tasks = task_dict[user_story.id]
        return project_details

    @staticmethod
    def _get_history(project_details, auth_token):
        """Get history for user stories and tasks"""
        for milestone in project_details.milestones:
            for user_story in milestone.user_stories:
                history, is_error = TaigaAPI.get_history(user_story.id,
                                                         auth_token, "HISTORY_US")
                if is_error:
                    user_story.history = None
                else:
                    user_story.history = AnalysisPerformer._extract_history(history)
                for task in user_story.tasks:
                    history, is_error = TaigaAPI.get_history(user_story.id,
                                                             auth_token, "HISTORY_TASK")
                    if is_error:
                        task.history = None
                    else:
                        task.history = AnalysisPerformer._extract_history(history)
        return project_details

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
        extracted.members = []
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
            extracted.created_date = DateTimeFormatter\
                .format_isodate_to_date(milestone[TG_ANLS_PRJ_MS_CR_DT])
            # estimated_start and estimated_finish already in required format
            extracted.estimated_finish = milestone[TG_ANLS_PRJ_MS_EST_FIN]
            extracted.estimated_start = milestone[TG_ANLS_PRJ_MS_EST_SRT]
            extracted.modified_date = DateTimeFormatter\
                .format_isodate_to_date(milestone[TG_ANLS_PRJ_MS_MD_DT])
            extracted.user_stories = []
            for user_story in milestone[TG_ANLS_PRJ_MS_US]:
                us = UserStoryDetails()
                us.id = user_story[TG_ANLS_PRJ_US_ID]
                us.ref = user_story[TG_ANLS_PRJ_US_REF]
                us.status = user_story[TG_ANLS_PRJ_US_STS_INFO][TG_ANLS_PRJ_US_STS_NAME]
                us.subject = user_story[TG_ANLS_PRJ_US_SUB]
                us.total_points = user_story[TG_ANLS_PRJ_US_TOT_PTS]
                us.modified_date = DateTimeFormatter\
                    .format_isodate_to_date(user_story[TG_ANLS_PRJ_US_MD_DT])
                us.created_date = DateTimeFormatter\
                    .format_isodate_to_date(user_story[TG_ANLS_PRJ_US_CR_DT])
                us.finish_date = DateTimeFormatter\
                    .format_isodate_to_date(user_story[TG_ANLS_PRJ_US_FIN_DT])
                us.is_closed = user_story[TG_ANLS_PRJ_US_IS_CLS]
                us.assigned_to = None
                if user_story[TG_ANLS_PRJ_US_ASG_INFO] is not None:
                    us.assigned_to = user_story[TG_ANLS_PRJ_US_ASG_INFO][TG_ANLS_PRJ_US_ASG_TO]
                extracted.user_stories.append(us)
            details.append(extracted)
        return details

    @staticmethod
    def _extract_tasks(tasks):
        """Extract required task details"""
        extracted = list()
        for task in tasks:
            tsk = TaskDetails()
            tsk.id = task[TG_ANLS_PRJ_TSK_ID]
            tsk.ref = task[TG_ANLS_PRJ_TSK_REF]
            tsk.status = task[TG_ANLS_PRJ_TSK_STS_INFO][TG_ANLS_PRJ_TSK_STS_NAME]
            tsk.subject = task[TG_ANLS_PRJ_TSK_SUB]
            tsk.user_story = task[TG_ANLS_PRJ_TSK_US]
            tsk.modified_date = DateTimeFormatter\
                .format_isodate_to_date(task[TG_ANLS_PRJ_TSK_MD_DT])
            tsk.created_date = DateTimeFormatter\
                .format_isodate_to_date(task[TG_ANLS_PRJ_TSK_CR_DT])
            tsk.finished_date = DateTimeFormatter\
                .format_isodate_to_date(task[TG_ANLS_PRJ_TSK_FIN_DT])
            tsk.due_date = DateTimeFormatter\
                .format_isodate_to_date(task[TG_ANLS_PRJ_TSK_DUE_DT])
            tsk.is_closed = task[TG_ANLS_PRJ_TSK_IS_CLS]
            tsk.assigned_to = None
            if task[TG_ANLS_PRJ_TSK_ASG_INFO] is not None:
                tsk.assigned_to = task[TG_ANLS_PRJ_TSK_ASG_INFO][TG_ANLS_PRJ_TSK_ASG_TO]
            extracted.append(tsk)
        return extracted

    @staticmethod
    def _extract_history(history):
        """Extract history details"""
        extracted = list()
        for event in history:
            tmp = HistoryEventDetails()
            tmp.created_at = DateTimeFormatter\
                .format_isodate_to_date(event[TG_ANLS_PRJ_HIS_CR_DT])
            tmp.diff = event[TG_ANLS_PRJ_HIS_DIFF]
            extracted.append(tmp)
        return extracted


class MilestonesGetter(object):
    """Get Milestones for a board"""

    @staticmethod
    @dataapi_response_decorator
    def get_milestones(data):
        details = []
        # Get Project Details
        project_details, is_error = ProjectDetailsGetter \
            .get_project_details_by_slug(data[TG_API_PROJECT_NAME], data[TG_AUTH_TOKEN])
        if is_error:
            return project_details, is_error
        project_id = project_details[TG_PROJECT_ID]
        # Get Project Milestones - Provided both Sprint and US
        milestones, is_error = ProjectDetailsGetter \
            .get_milestones(data[TG_API_PROJECT_NAME], project_id,
                            data[TG_AUTH_TOKEN], "MILESTONES")
        if is_error:
            return milestones, is_error
        for milestone in milestones:
            tmp = MilestoneDetails()
            tmp.name = milestone[TG_ANLS_PRJ_MS_NAME]
            tmp.created_date = DateTimeFormatter\
                .format_isodate_to_date(milestone[TG_ANLS_PRJ_MS_CR_DT])
            # estimated_start and estimated_finish already in required format
            tmp.estimated_finish = milestone[TG_ANLS_PRJ_MS_EST_FIN]
            tmp.estimated_start = milestone[TG_ANLS_PRJ_MS_EST_SRT]
            tmp.modified_date = DateTimeFormatter\
                .format_isodate_to_date(milestone[TG_ANLS_PRJ_MS_MD_DT])
            details.append(json.loads(tmp.to_json()))
        return details, is_error
