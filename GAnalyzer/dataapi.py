"""
Support Module for Views
"""
import logging
from datetime import datetime, timezone
from .GitHubAPI import *
from .utils import *
from .APIPayloadKeyConstants import *
from .decorators import new_thread_decorator

LOGGER = logging.getLogger(__name__)


class FlightChecker(object):
    """Supporting class for FlightCheckView"""

    @staticmethod
    def perform_flight_check(data):
        token = get_token(data)
        username = get_username(data)
        result = check_token_username(token, username)
        if result is not None:  # check failed
            return result, True
        response, is_error = flight_check(token)
        if is_error:
            return {'error': response, 'saved': False}, True
        if response.get("login").lower() != username.lower():
            return {'error': "Provided username: '{}' doesn't match the token username: '{}'".format(
                username, response["login"].lower()),
                       'saved': False}, True
        return response, False


class RepositoryListGetter(object):
    """Getter class for ListRepositoryView"""

    @staticmethod
    def get_repository_list(data):
        token = get_token(data)
        return get_repository_list(token)


class DataExtractor(object):
    """Extract 'data' from an HTTP Request"""

    @staticmethod
    def get_data_object(request):
        return request.data

    @staticmethod
    def get_file_upload_object(request):
        return request.FILES


class RepositoryCreator(object):
    """Creator class for CreateRepositoryView"""

    @staticmethod
    def create_repository(data, key="file"):
        token = get_token(data)
        username = get_username(data)
        result = check_token_username(token, username)
        if result is not None:  # token-username validation failed
            return result, True
        parsed = list(map(lambda x: RepositoryCreator.sanitize_row(x),
                          data.get(GH_CREATE_DATA)))
        parsed = RepositoryCreator.convert_list_to_dic(parsed)
        parsed = RepositoryCreator.check_for_optional_fields(parsed)
        payload = RepositoryCreator.prepare_repo_flow_payload(parsed)
        return RepositoryCreator.create_repo_flow(payload, token, username), False

    @staticmethod
    def convert_list_to_dic(data):
        """covert list data to dictionary"""
        repo_name = GH_CREAT_REPO_REPO_NAME_KEY
        collaborator_name = GH_CREAT_REPO_COLLABORATOR_NAME_KEY
        # the fist entry of the list is the repository name
        # every other entry is the name of a collaborator
        records = []
        for row in data:
            tmp = dict()
            tmp[repo_name] = row[0]
            tmp[collaborator_name] = row[1:]
            records.append(tmp)
        return records

    @staticmethod
    def sanitize_row(row):
        return list(map(lambda x: x.strip(" "), row))

    @staticmethod
    def check_for_optional_fields(parsed):
        private = GH_CREAT_REPO_IS_PRIVATE_KEY
        for record in parsed:
            if record.get(private) is None:
                record[private] = True
        return parsed

    @staticmethod
    def prepare_repo_flow_payload(parsed):
        """Prepare payload to be used to create a repo and then add
        collaborators to it and enable protection on the master branch"""
        repo_name = GH_CREAT_REPO_REPO_NAME_KEY
        private = GH_CREAT_REPO_IS_PRIVATE_KEY
        collaborator_name = GH_CREAT_REPO_COLLABORATOR_NAME_KEY
        payload = {}
        for record in parsed:
            payload[record.get(repo_name)] = {
                "create_repo": {
                    "name": record.get(repo_name),
                    "auto_init": True,  # without this an empty repo is created (no branch)
                    "private": record.get(private),
                },
                "collaborators": record.get(collaborator_name)
            }
        return payload

    @staticmethod
    def create_repo_flow(payload, token, username):
        crr = CreateRepoResponse()
        flow_response = []
        for key, value in payload.items():
            # creating a repo, adding collaborators and adding branch protection is one
            # atomic transaction
            crr.repo_name = key
            # 1. Create the repo
            response, is_error = create_repository(token, value["create_repo"])
            crr.repo_created = not is_error
            if is_error:
                crr.reason = response  # Only set reason if there is a failure
                crr.failed = True
                crr.failure_step = "Repo Creation"
                flow_response.append(crr.__dict__)
                break

            # 2. Add collaborators
            collaborator_response = []
            for collaborator in value["collaborators"]:
                response, is_error = add_collaborator(token, username, key, collaborator)
                collaborator_response.append({"collab_name": collaborator, collaborator: response, "failed": is_error})
            crr.collaborator_status = collaborator_response

            # 3. Enable branch protection on master branch
            response, is_error = enable_protections(token, username, key)
            crr.protection_enabled = not is_error
            if is_error:
                crr.reason = response  # Only set reason if there is a failure
                crr.failed = True
                crr.failure_step = "Enable Branch Protection"
                flow_response.append(crr.__dict__)
                break
            flow_response.append(crr.__dict__)
        return flow_response


class Analyzer(object):
    """Perform repository analysis"""

    @staticmethod
    def perform_analysis_async(data):
        # number of repos to Analyse
        num_combinations = len(data.get(GH_ANALYSE_REPO_LIST))
        request_id = data.get('request_id')
        Analyzer._perform_analysis_threaded(data)
        return {'saved': True,
                'combinations': num_combinations,
                'request_id': request_id}, False

    @staticmethod
    @new_thread_decorator
    def _perform_analysis_threaded(data):
        # loop through each group in data and
        # perform analysis of each group sequentially
        # get singleton object
        apt_object = AnalysisProgressTracker.get_instance()
        for repo in data.pop(GH_ANALYSE_REPO_LIST):
            repo_name = repo.get(GH_ANALYSE_REPO_LIST_NAME)
            result = AnalysisPerformer.perform_analysis(repo, data)
            apt_object.set_analysis_results(data['request_id'],
                                            repo_name,
                                            result)
        return


class AnalysisResultsPoller(object):
    """Poller for Analysis results"""

    @staticmethod
    def poll(data):
        request_id = data.get('request_id')
        apt_object = AnalysisProgressTracker.get_instance()
        return apt_object.get_analysis_results(request_id), False


class AnalysisPerformer(object):
    """Perform Analysis on GH repo"""

    @staticmethod
    def perform_analysis(repo, data):
        username = get_username(data)
        token = get_token(data)
        repo_name = repo.get(GH_ANALYSE_REPO_LIST_NAME)
        start_date = datetime.fromtimestamp(int(repo.get(GH_ANALYSE_REPO_LIST_ST_DT)),
                                            tz=timezone.utc).isoformat()
        end_date = datetime.fromtimestamp(int(repo.get(GH_ANALYSE_REPO_LIST_ED_DT)),
                                          tz=timezone.utc).isoformat()
        # TODO: Check for Taiga Integration
        # Get a list of branches for this repo
        branches, is_error = AnalysisPerformer._get_branches(token, username, repo_name)
        if is_error:
            return branches
        # Collect data for each branch
        # Get a list of collaborators for this repo
        c_names, is_error = AnalysisPerformer._get_collaborators(token, username, repo_name)
        if is_error:
            return c_names
        # complete data required for Analysis
        data_dump = {}
        for branch in branches:
            data_dump[branch] = {name: {} for name in c_names}
            # Get commit data for each collaborator for the given date range
            commit_data, is_error = AnalysisPerformer._get_commits(token, username, repo_name, branch,
                                                                   start_date, end_date, c_names)
            if is_error:
                return commit_data
            commit_data = AnalysisPerformer._add_commit_stats(token,
                                                              username, repo_name, commit_data)
            if is_error:
                return commit_data
            data_dump[branch] = AnalysisPerformer._merge(data_dump[branch],
                                                         commit_data, "commits")
        # Get PR data for each collaborator
        # c_pr: collaborator to PR number mapping
        pr_details, c_pr, is_error = AnalysisPerformer._get_pr(token, username, repo_name, c_names, branches)
        if is_error:
            return pr_details
        data_dump = AnalysisPerformer._merge_pr_data(data_dump, c_pr)
        data_dump["pr_details"] = pr_details
        return data_dump

    @staticmethod
    def _merge_pr_data(data_dump, c_pr):
        """Merge PR data into all data"""
        for branch, pr_details in c_pr.items():
            for author, pr in pr_details.items():
                data_dump[branch][author].update(pr)
        return data_dump

    @staticmethod
    def _get_branches(token, username, repo_name):
        """Get branches for the given repo"""
        branches, is_error = get_branches(token, username, repo_name)
        if is_error:
            return {"repo_name": repo_name, "error": branches, "failed": True}, \
                   is_error
        # branch names
        return [branch[GH_API_BRANCH_NAME] for branch in branches], is_error

    @staticmethod
    def _make_commit_details_object(data):
        """make a dict object with required commit details"""
        commit = data[GH_API_COMMIT]
        author = data[GH_API_COMMITTER]
        return {
            "author": author[GH_API_USERNAME],
            "author_display": commit[GH_API_COMMITTER][GH_API_AUTHOR_DISPLAY],
            "message": commit[GH_API_COMMIT_MESSAGE],
            "comment_count": commit[GH_API_COMMIT_CMT_CNT],
            "sha": data[GH_API_COMMIT_SHA],
            "url": data[GH_API_COMMIT_URL],
            "date": commit[GH_API_COMMITTER][GH_API_COMMIT_DT]
        }

    @staticmethod
    def _get_commits(token, username, repo_name, branch, start_date, end_date, c_names):
        """get commits for a repository"""
        commits_dump, is_error = get_commit(token, username, repo_name, branch,
                                            start_date, end_date)
        if is_error:
            return {"repo_name": repo_name, "error": commits_dump, "failed": True}, \
                   is_error
        commit_map = defaultdict(list)
        for commit_data in commits_dump:
            commit_map[commit_data[GH_API_COMMITTER][GH_API_USERNAME]] \
                .append(AnalysisPerformer._make_commit_details_object(commit_data))
        return commit_map, is_error

    @staticmethod
    def _merge(data_dump, partial_data, key_name):
        """merge partial data into the central data"""
        for key in partial_data.keys():
            if data_dump.get(key) is not None:
                data_dump[key].update({key_name: partial_data[key]})
        return data_dump

    @staticmethod
    def _get_collaborators(token, username, repo_name):
        """get collaborators for a repository"""
        collaborators, is_error = get_collaborators(token, username, repo_name)
        if is_error:
            return {"repo_name": repo_name, "error": collaborators, "failed": True}, \
                   is_error
        # collaborator names
        return [collaborator[GH_API_USERNAME] for collaborator in collaborators], \
               is_error

    @staticmethod
    def _make_pr_details_object(data):
        """Create a dictionary with PR details"""
        return {
            "url": data[GH_API_PR_URL],
            "title": data[GH_API_PR_TITLE],
            "state": data[GH_API_PR_STATE],
            "number": data[GH_API_PR_NUM],
            "body": data[GH_API_PR_BODY],
            "created_at": data[GH_API_PR_CR_DT],
            "closed_at": data.get(GH_API_PR_CL_DT),
            "merged_at": data.get(GH_API_PR_MR_DT),
            "assignees": data[GH_API_PR_ASG],
            "requested_reviewers": data[GH_API_PR_REV],
            "head": data[GH_API_PR_HEAD][GH_API_PR_REF],
            "base": data[GH_API_PR_BASE][GH_API_PR_REF],
            "user": data[GH_API_PR_USER][GH_API_PR_USERNAME]
        }

    @staticmethod
    def _get_pr(token, username, repo_name, c_names, branches):
        """Get PRs for the given repository"""
        pr_dump, is_error = get_pr(token, username, repo_name)
        if is_error:
            return {"repo_name": repo_name, "error": pr_dump, "failed": True}, {}, \
                   is_error
        pr_details = {}
        # branch to collaborator to PR
        c_pr = {}
        # c_pr = {branch: {name: {"assignee": [], "reviewer": [], "author": []}
        #         for name in c_names} for branch in branches}
        for pr in pr_dump:
            details = AnalysisPerformer._make_pr_details_object(pr)
            pr_num = details["number"]
            head = details["head"]
            base = details["base"]
            c_pr = AnalysisPerformer._extract_assignee_reviewer(details.pop("assignees"),
                                                                "assignee", pr_num, head, base,
                                                                c_names, branches, c_pr)
            c_pr = AnalysisPerformer._extract_assignee_reviewer(details.pop("requested_reviewers"),
                                                                "reviewer", pr_num, head, base,
                                                                c_names, branches, c_pr)
            c_pr = AnalysisPerformer._extract_assignee_reviewer([{GH_API_PR_USERNAME: details["user"]}],
                                                                "author", pr_num, head, base,
                                                                c_names, branches, c_pr)
            if details["user"] in c_names:
                single_pr = AnalysisPerformer._get_single_pr(token,
                                                             username, repo_name, pr_num)
                details.update(single_pr)
                pr_details[pr_num] = details
        return pr_details, c_pr, is_error

    @staticmethod
    def _extract_assignee_reviewer(data, insert_key, pr_num, head, base,
                                   c_names, branches, c_pr):
        for name in data:
            author = name[GH_API_PR_USERNAME]
            if author in c_names:
                for branch in [head, base]:
                    if branch in branches:
                        try:
                            _val = c_pr[branch][author][insert_key]
                        except KeyError:
                            c_pr[branch] = {author: defaultdict(list)}
                        c_pr[branch][author][insert_key].append(pr_num)
        return c_pr

    @staticmethod
    def _get_single_pr(token, username, repo_name, pr_num):
        """Get details of a single PR"""
        pr_data, is_error = get_single_pr(token, username, repo_name, pr_num)
        details = {
            "num_comments": None,
            "num_rev_comments": None,
            "num_commits": None,
            "num_add": None,
            "num_del": None,
            "num_files": None
        }
        if not is_error:
            details["num_comments"] = pr_data[GH_API_PR_COMMENTS]
            details["num_rev_comments"] = pr_data[GH_API_PR_REV_COMMENTS]
            details["num_commits"] = pr_data[GH_API_PR_COMMITS]
            details["num_add"] = pr_data[GH_API_PR_ADD]
            details["num_del"] = pr_data[GH_API_PR_DEL]
            details["num_files"] = pr_data[GH_API_PR_FILES]
        return details

    @staticmethod
    def _get_single_commit(token, username, repo_name, sha):
        """Get a single commit"""
        commit_data, is_error = get_single_commit(token, username, repo_name, sha)
        if is_error:
            return {
                GH_API_COMMIT_ADD: None,
                GH_API_COMMIT_DEL: None,
                GH_API_COMMIT_TOT: None
            }
        return commit_data[GH_API_COMMIT_STATS]

    @staticmethod
    def _add_commit_stats(token, username, repo_name, commit_data):
        """Add commit stats to the commit object"""
        for _author, commit_list in commit_data.items():
            for commit in commit_list:
                # in-place modification
                commit[GH_API_COMMIT_STATS] = AnalysisPerformer._get_single_commit(
                    token, username, repo_name, commit["sha"]
                )
        return commit_data
