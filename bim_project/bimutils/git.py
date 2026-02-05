import yaml
import base64
import requests
import typer
from rich.console import Console
from rich.table import Table

import sys
import logging
import os

from tools import Tools
from mlogger import Logs


logger = logging.getLogger(__name__)
tools = Tools()
logs = Logs()

class Git:

    _url = "https://git.bimeister.io/api/v4"
    def __init__(self):
        self.tag = Tag
        self.project = Project
        self.branch = Branch
        self.job = Job
        self.pipeline = Pipeline
        self.tree = Tree
        self.product_collection = Product_collection_file
        self.chart = Chart
        self.headers = self.get_headers()
        self.console = Console()

    @classmethod
    def get_headers(cls) -> dict:
        """ Function returns header in structure Gitlab expects. """
        headers = {"PRIVATE-TOKEN": os.getenv("GITLAB_TOKEN")}
        return headers


    def display_table_with_branches_commits_tags_jobs(self, data) -> Table:
        """ Create table, fill with data(branches, commits, tags, helm chart job status, FT job status) and print it out. """

        if not data:
            return False
        table = Table(show_lines=False)
        table.add_column("Branch", justify="left", no_wrap=True, style="#875fff", max_width=55)
        table.add_column("Commit", justify="left", style="#875fff")
        table.add_column("Tag", justify="left", style="#875fff")
        table.add_column("Helm charts", justify="left", style="#875fff")
        for x in data:
            table.add_row(x[0], x[1], x[2], x[3])
        self.console.print(table)


class Project(Git):

    def get_project_id(self, project='bimeister') -> int:
        """ Get from Gitlab ID of the project bimeister. """

        url = f"{self._url}/search?scope=projects&search={project}&per_page=100"
        response = tools.make_request('GET', url, headers=self.headers, return_err_response=True, print_err=True)
        data = response.json()
        try:
            for proj in reversed(data):
                if proj['name'] == project:
                    return proj['id']
        except Exception as err:
            logger.error(err)
            return None
        logger.error(f"Id for project {project} not found.")
        return False


class Chart(Git):
    
    def is_chart_available(self, project_id, commit) -> bool:
        """ Check if helm charts are available for download. """

        # get all pipelines
        pipelines = self.pipeline().get_pipelines(project_id, commit=commit)
        for pipeline in pipelines:
            pipeline_jobs = self.job().get_pipeline_jobs(project_id, pipeline['id'])
            for job in pipeline_jobs:
                if job['name'].lower() == "build chart" and job['status'] == 'success':
                    return True
        return False


class Tag(Git):

    def search_tag(self, project_id, search: list) -> dict:
        """ Search for needed tags. """

        __url = f"{self._url}/projects/{project_id}/repository/tags"
        tag_data = dict()
        for x in search:
            try:
                payload = {'search': x}
                response = requests.get(url=__url, headers=self.headers, params=payload, verify=False)
                response.raise_for_status()
                data = response.json()
            except requests.exceptions.RequestException as err:
                logger.error(err)
                print(logs.err_message)
                return False
            for tag in data:
                branch: list = self.branch().get_branch_name_using_commit(project_id, tag['commit']['short_id'])
                tag_data[tag['commit']['short_id']] = {'tag_name': tag['name'], 'branch_name': branch}
        if not tag_data:
            return False
        else:
            '''Some tags may have more than one branch, and they may have the same branches like another tags which has only one branch in the list.
               Need to remove duplicate branches from such tags.
            '''
            branches = set(branch for v in tag_data.values() for branch in v['branch_name'] if len(v['branch_name']) == 1 )
            for value in tag_data.values():
                if len(value['branch_name']) > 1:
                    for branch in value['branch_name'][:]:
                        if branch in branches:
                            value['branch_name'].remove(branch)
            return tag_data


class Branch(Git):

    def search_branches_commits_tags_jobs(self, project_id, search: list):
        """ Search branches with their commits, tags and jobs. """

        result_data: list = []
        with self.console.status("[magenta]Searching tags...[/magenta]", spinner="earth") as status:
            tags: dict = self.tag().search_tag(project_id, search)
            status.update("[magenta]Searching branches...[/magenta]")
            for x in search:
                url = f"{self._url}/projects/{project_id}/repository/branches?regex=\D{x}"
                try:
                    response = requests.get(url=url, headers=self.headers)
                    response.raise_for_status()
                except requests.exceptions.RequestException as err:
                    logger.error(err)
                    print(logs.err_message)
                    return False
                for branch in response.json():
                    branch_commit = branch['commit']['short_id']                                
                    if tags and tags.get(branch_commit):
                        tag_name =  tags[branch_commit]['tag_name']
                        del tags[branch_commit]
                    elif tags and tags.get(branch['commit']['parent_ids'][0][:8]):
                        branch_commit = branch['commit']['parent_ids'][0][:8]
                        tag_name = tags.get(branch['commit']['parent_ids'][0][:8])['tag_name']
                        del tags[branch['commit']['parent_ids'][0][:8]]
                    else:
                        tag_name = '-'
                    result_data.append([
                        branch['name'],
                        branch_commit,
                        tag_name,
                        'Ready' if self.chart().is_chart_available(project_id, commit=branch_commit) else 'Not ready'
                                    ])
            if tags:
                for tag in tags:
                    if len(tags[tag]['branch_name']) > 1:
                        branch_name = tags[tag]['branch_name'][-1]
                    else:
                        branch_name = tags[tag]['branch_name'][0]
                    result_data.append([branch_name,
                                        tag,
                                        tags[tag]['tag_name'],
                                        'Ready' if self.chart().is_chart_available(project_id, commit=tag) else 'Not ready'
                                        ])
        if not result_data:
            self.console.print("No branches were found!")
            return None
        return result_data

    def get_branch_name_using_commit(self, project_id, commit) -> list:
        """ Get branch name(s) using commit from a given repository. """

        url = f"{self._url}/projects/{project_id}/repository/commits/{commit}/refs?type=branch&per_page=100"
        try:
            response = requests.get(url=url, headers=self.headers, verify=False)
            response.raise_for_status()
            branches: list = [branch['name'] for branch in response.json()]
            next_page = response.headers['X-Next-Page']
            while next_page:
                url_next_page = f"https://git.bimeister.io/api/v4/projects/{project_id}/repository/commits/{commit}/refs?id={project_id}&page={next_page}&per_page=100&sha={commit}&type=branch"
                response = requests.get(url=url_next_page, headers=self.headers, verify=False)
                for branch in response.json():
                    branches.append(branch['name'])
                next_page = response.headers['X-Next-Page']
            return branches if branches else False
        except requests.exceptions.RequestException as err:
            logger.error(err)
            print(logs.err_message)
            return False


class Job(Git):

    _jobs: tuple = (
                "build chart",
                    )
    _build_job: str = "build_chart"

    def get_pipeline_jobs(self, project_id, pipeline_id) -> list:
        """ Get a list of jobs for provided pipeline. """

        if not pipeline_id:
            return []
        url = f"{self._url}/projects/{project_id}/pipelines/{pipeline_id}/jobs"
        try:
            response = requests.get(url=url, headers=self.headers, verify=False)
            response.raise_for_status()
            jobs = response.json()
        except requests.exceptions.RequestException as err:
            logger.error(err)
            print(logs.err_message)
            return False
        return jobs

    def get_specific_jobs(self, project_id: int, commit: str, branch_name: str) -> dict:
        """ Get id, status, name of jobs and pipeline_id pointed out in 'specific_jobs' tuple from pipeline. """

        pipelines = self.pipeline().get_pipelines(project_id, commit)
        pipeline_id = False
        if pipelines:
            for pipeline in pipelines:
                if pipeline['ref'] == branch_name:
                    pipeline_id = pipeline['id']
                    break
        if not pipeline_id:
            needed_jobs: dict = {'pipeline_id': False}
            return needed_jobs
        all_jobs: list = self.get_pipeline_jobs(project_id, pipeline_id)
        needed_jobs: dict = {'pipeline_id': pipeline_id}
        for j in all_jobs:
            if j['name'].lower() in self._jobs:
                name: str = '_'.join((j['name'].lower().split()))
                needed_jobs[name] = {'id': j['id'], 'name': name, 'status': j['status']}
        return needed_jobs

    def get_job(self, project_id: int, commit: str, branch_name: str, job_name: str) -> dict:
        """ Get id, status, name and pipeline_id of job from pipeline. """

        pipelines = self.pipeline().get_pipelines(project_id, commit)
        pipeline_id = False
        if pipelines:
            for pipeline in pipelines:
                if pipeline['ref'] == branch_name:
                    pipeline_id = pipeline['id']
                    break
        job: dict = {}
        if not pipeline_id:
            return job
        all_jobs: list = self.get_pipeline_jobs(project_id, pipeline_id)
        for j in all_jobs:
            if '_'.join((j['name'].lower().split())) == job_name:
                job.update({'id': j['id'], 
                            'name': job_name,
                            'status': j['status'],
                            'pipeline_id': pipeline_id,
                            'branch': branch_name
                             })
        return job

    def run_job(self, project_id: int, job_id: list):
        """ Execute job run for a given job id list. """

        if not project_id or not job_id or not isinstance(job_id, list):
            logger.error(f"{self.job.__qualname__} Incorrect data transferred.")
            raise TypeError("Run job function accepts project_id and job_id as a list.")
        for id in job_id:
            url = f"{self._url}/projects/{project_id}/jobs/{id}/play"
            try:
                response = requests.post(url=url, headers=self.headers, verify=False)
                response.raise_for_status()
                data = response.json()
                if response.status_code == 200:
                    print(f"Job started successfully                \
                          \nname: {data['name']}                    \
                          \npipeline id: {data['pipeline']['id']}   \
                          \nref: {data['pipeline']['ref']}          \
                          \nurl: {data['pipeline']['web_url']}      ")
            except requests.exceptions.RequestException as err:
                logger.error(err)
                print(logs.err_message)
                return False                
            except Exception as err:
                logger.error(err)
                print(logs.err_message)
                return False                


class Pipeline(Git):

    def get_pipelines(self, project_id, commit) -> list:
        """ Get list of pipeline(s) with 'success' status for provided commit. """

        branches: list = self.branch().get_branch_name_using_commit(project_id, commit)
        pipelines: list = []
        if not branches:
            return False
        for branch in branches:
            url = f"{self._url}/projects/{project_id}/pipelines?ref={branch}"
            try:
                payload = {
                    "order_by": "updated_at",
                    "status": "success"
                        }
                response = requests.get(url=url, headers=self.headers, params=payload, verify=False)
                response.raise_for_status()
                for pipeline in response.json():
                    pipelines.append(pipeline)
            except requests.exceptions.RequestException as err:
                logger.error(err)
                print(logs.err_message)
                return False
        # sort pipelines by id
        pipelines = sorted(pipelines, key=lambda x: x['id'], reverse=True)
        return pipelines


class Tree(Git):

    def print_list_of_branch_files(self, project_id, branch_name):
        """ Get a list of tree. """

        url = f"{self._url}/projects/{project_id}/repository/tree?ref={branch_name}"
        try:
            response = requests.get(url=url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as err:
            logger.error(err)
            print(logs.err_message)
            return False
        except Exception as err:
            logger.error(err)
            print(logs.err_message)
            return False
        for x in data:
            print(x['name'])


class Product_collection_file(Git):

    def get_product_collection_file_content(self, project_id, commit):
        """ Get a product-collection.yaml file content. """

        url = f"{self._url}/projects/{project_id}/repository/files/product-collections%2Eyaml?ref={commit}"
        try:
            response = requests.get(url=url, headers=self.headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(logs.err_message)
            logger.error(err)
            return False
        except requests.exceptions.RequestException as err:
            logger.error(err)
            print(logs.err_message)
            return False
        data_base64 = response.json()['content']
        data_bytes = data_base64.encode('utf-8')
        decode_bytes = base64.b64decode(data_bytes)
        decode_string = decode_bytes.decode('utf-8')
        data: dict = yaml.safe_load(decode_string)
        return(data)

    def parse_product_collection_yaml(self, data: dict, project_name=''):
        """ Function returns a tuple with the project name and two lists of services and DB for a chosen project. """

        if not data:
            return False
        if not project_name:
            for num, project in enumerate(data['collections'], 1):
                print(f"{num}. {project}")
            try:
                inp = int(input('Choose number of the project: '))
                project = list(data['collections'])[inp - 1]
            except ValueError:
                print("Incorrect input.")
                return None
            except IndexError:
                print(f"Incorrect input. Should be between 1 and {len(list(data['collections']))}")
                return None
            except Exception as err:
                logger.error(err)
                print(logs.err_message)
                return None
        else:
            project = project_name
        modules_and_services: dict = data['modules']
        modules = set(data['collections'][project]['modules'])
        # cache = data['collections'][project]['infrastructure']['caсhe'] # The key 'cache' was copied from the product-collection.yaml file, because it has a flow with unicode. Does not work when just type 'cache' from keyboard.
        services: list = []
        for module in modules:
            if module not in modules_and_services:
                print(f"<{module}> module does not exist in the global modules list!")
                continue
            elif module == 'spatium':
                for x in data['services']['spatium']['additional_containers']:
                    services.append('spatium_api') if x == 'api' else services.append(x)
            for service in modules_and_services[module]:
                if service not in services and service != 'spatium':
                    services.append(service)
        services = sorted(services)
        db: list = []
        for svc in services:
            try:
                if svc in data['services']['spatium']['additional_containers'] or svc == 'spatium_api':
                    db.extend(data['services']['spatium']['db'])
                elif data['services'][svc].get('db') and data['services'][svc]['db'] == ['db']:
                    db.append('bimeisterdb')
                elif data['services'][svc].get('db'):
                    db.extend(data['services'][svc]['db'])
            except TypeError:
                print("Warning! This version works with product-collection.yaml file only since release-133.")
                return False
        db = sorted(set(db)) # remove duplicates from the list using set
        return project, services, db

    def compare_two_commits(self, first_commit_services: list, first_commit_db: list, second_commit_services: list, second_commit_db: list):
        """ Compare to commits with each other. Search for the difference in DBs lists and services lists. """

        first_commit_services: set = set(first_commit_services)
        first_commit_db: set = set(first_commit_db)
        second_commit_services: set = set(second_commit_services)
        second_commit_db: set = set(second_commit_db)

        if not first_commit_db == second_commit_db:
            db_removed = first_commit_db.difference(second_commit_db)
            db_added = second_commit_db.difference(first_commit_db)
            print("\nDatabases:", end=" ")
            if db_removed:
                self.console.print(f"\n  [bold red]Removed: [bold]{db_removed}[/bold red]")
            if db_added:
                self.console.print("[bold green]{0}  Added: {1}[/bold green]".format("" if db_removed else "\n", db_added))
        else:
            print("\nDatabases: Total match!")
        if not first_commit_services == second_commit_services:
            svc_removed = first_commit_services.difference(second_commit_services)
            svc_added = second_commit_services.difference(first_commit_services)
            print("Services:", end=" ")
            if svc_removed:
                self.console.print("\n  [bold red]Removed: {0}[/bold red]".format(svc_removed))
            if svc_added:
                self.console.print("[bold green]{0}  Added: {1}[/bold green]".format("" if svc_removed else "\n", svc_added))
        else:
            print("Services: Total match!")

    def print_services_and_db(self, svc: list, db: list, project_name=''):
        """ Function for displaying collection on a screen. """

        table = Table(title=project_name, show_footer=True)
        table.add_column("Services", style="cyan", justify="left", no_wrap=True, footer=f"Total: {len(svc)}")
        table.add_column("Databases", style="cyan", justify="left", footer=f"Total: {len(db)}")
        if not svc or not db:
            return False
        # make lists 'db' and 'svc' equal length
        max_length: int = max(len(svc), len(db))
        svc.extend([''] * (max_length - len(svc)))
        db.extend([''] * (max_length - len(db)))
        for service, database in zip(svc, db):
            table.add_row(service, database)
        self.console.print(table)



git_app = typer.Typer(help="Get info from gitlab. Search branches, tags, commits, product-collection.yaml data.")

@git_app.command()
def search(
    branches: list[str] = typer.Argument(..., help="Search pattern by it's name"),
    project_id: str = typer.Option("bimeister", "--project", "-p", help="Name of the project in gitlab")
        ):
    """ Get table with info about branches, commits, tags, helm charts. """

    g = Git()
    project = g.project()
    branch = g.branch()
    project_id = project.get_project_id(project='bimeister')
    if not project_id:
        sys.exit()
    data = branch.search_branches_commits_tags_jobs(project_id, search=branches)
    g.display_table_with_branches_commits_tags_jobs(data)

@git_app.command()
def build_charts(commit: str = typer.Argument(..., help="Requires commit to activate job")):
    """ Activate gitlab job: Build Charts. For a given commit. """

    g = Git()
    project = g.project()
    branch = g.branch()
    job = g.job()
    project_id = project.get_project_id(project='bimeister')
    branches: list = branch.get_branch_name_using_commit(project_id, commit)
    if len(branches) == 1:
        branch_name = branches[0]
    else:
        branch_name = input(f"{branches} commit appears in several branches: {branches}\nSelect branch: ")
    charts_jobs = job.get_specific_jobs(project_id, commit=commit, branch_name=branch_name)
    pipeline_id = charts_jobs['pipeline_id']
    if not pipeline_id:
        print("No pipelines with 'success' status. Can't run the job.")
        sys.exit()
    job.run_job(project_id, str(charts_jobs['build_chart']['id']).split())

@git_app.command()
def commit(
    commit: str = typer.Argument(..., help="Commit for product-collection.yaml info from"),
    project_name: str = typer.Option(None, "--project", "-p", help="Provide project name from the product-collection.yaml without prompt")
        ):
    """ Get info about services and databases from the product-collection.yaml file for a given commit. """

    g = Git()
    project = g.project()
    product_collection = g.product_collection()
    project_id = project.get_project_id(project='bimeister')
    file_content: dict = product_collection.get_product_collection_file_content(project_id, commit)
    if not file_content:
        sys.exit()
    data = product_collection.parse_product_collection_yaml(file_content, project_name=project_name)
    if not data:
        sys.exit()
    else:
        project_name, services, db = data
    if not services or not db:
        sys.exit()
    product_collection.print_services_and_db(services, db)

@git_app.command()
def compare(
    commits: list[str] = typer.Argument(help="Flag expects two commits to compare differences between them")
        ):
    """ Compare two commits for difference in product-collection.yaml in DBs list and services list """

    g = Git()
    project = g.project()
    product_collection = g.product_collection()
    project_id = project.get_project_id(project='bimeister')

    if len(commits) != 2:
        print("Need two commits two compare.")
        return None
    first_commit, second_commit = commits[0], commits[1]
    first_commit_data: dict = product_collection.get_product_collection_file_content(project_id, first_commit)
    second_commit_data: dict = product_collection.get_product_collection_file_content(project_id, second_commit)
    if not first_commit_data or not second_commit_data:
        sys.exit()
    data = product_collection.parse_product_collection_yaml(first_commit_data)
    if not data:
        sys.exit()
    first_commit_project_name, first_commit_services, first_commit_db = data
    data = product_collection.parse_product_collection_yaml(second_commit_data, project_name=first_commit_project_name)
    if not data:
        sys.exit()
    second_commit_project_name, second_commit_services, second_commit_db = data
    product_collection.compare_two_commits(first_commit_services, first_commit_db, second_commit_services, second_commit_db)












    ### NOT IN USE ###
    # def get_tags(self, project_id):
    #     """ Get needed tags for provided project_id. """

    #     url = f"{self.__url}/projects/{project_id}/repository/tags"
    #     try:
    #         response = requests.get(url=url, headers=self.__headers, verify=False)
    #         response.raise_for_status()
    #         data = response.json()
    #     except requests.exceptions.RequestException as err:
    #         print(self.__error_msg)
    #         return False
    #     return data

    # def search_branches_commits_tags_jobs(self, project_id, search: list):
    #     """ Search branches with their commits, tags and jobs. """

    #     tags: dict = self.tag().search_tag(project_id, search)
    #     result_data: list = []
    #     for x in search:
    #         url = f"{self._url}/projects/{project_id}/repository/branches?regex=\D{x}"
    #         try:
    #             response = requests.get(url=url, headers=self.headers)
    #             response.raise_for_status()
    #         except requests.exceptions.RequestException as err:
    #             print(self._error_msg)
    #             logger.error(err)
    #             return False
    #         for branch in response.json():
    #             branch_commit = branch['commit']['short_id']
    #             if tags and tags.get(branch['commit']['short_id']):
    #                 tag_name =  tags[branch['commit']['short_id']]['tag_name']
    #                 del tags[branch['commit']['short_id']]
    #             elif tags and tags.get(branch['commit']['parent_ids'][0][:8]):
    #                 branch_commit = branch['commit']['parent_ids'][0][:8]
    #                 tag_name = tags.get(branch['commit']['parent_ids'][0][:8])['tag_name']
    #                 del tags[branch['commit']['parent_ids'][0][:8]]
    #             else:
    #                 tag_name = '-'
    #             build_chart_job: dict = self.job().get_job(project_id, branch_commit, branch['name'], self.job._build_job)
    #             result_data.append([
    #                 branch['name'],
    #                 branch_commit,
    #                 tag_name,
    #                 'Ready' if build_chart_job and build_chart_job['status'] == 'success' else 'Not ready',
    #                 build_chart_job['pipeline_id'] if build_chart_job and build_chart_job['pipeline_id'] else '-'
    #                             ])
    #     if tags:
    #         for tag in tags:
    #             if len(tags[tag]['branch_name']) > 1:
    #                 branch_name = tags[tag]['branch_name'][-1]
    #             else:
    #                 branch_name = tags[tag]['branch_name'][0]
    #             build_chart_job: dict = self.job().get_job(project_id, tag, branch_name, self.job._build_job)
    #             result_data.append([branch_name,
    #                                 tag,
    #                                 tags[tag]['tag_name'],
    #                                 'Ready' if build_chart_job and build_chart_job['status'] == 'success' else 'Not ready',
    #                                 build_chart_job['pipeline_id'] if build_chart_job and build_chart_job['pipeline_id'] else '-'
    #                                 ])
    #     if not result_data:
    #         print("No branches were found!")
    #         return False
    #     return result_data

    # def is_chart_available(self, repo_url='https://nexus.dev.bimeister.io/repository/bim-helm', chart_name='bimeister', commit=None) -> bool:
    #     """ Check if helm charts are available for download. """

    #     result: bool = False
    #     for x in range(17, 19):
    #         version: str = f"1.{x}.0-sha{commit}"
    #         try:
    #             # Helm repos typically have an index.yaml file
    #             response = requests.get(f"{repo_url}/index.yaml")
    #             response.raise_for_status()
    #             index = yaml.safe_load(response.text)
    #             if chart_name in index.get('entries', {}):
    #                 if commit:
    #                     result = any(chart['version'] == version for chart in index['entries'][chart_name])
    #                 else:
    #                     return False
    #                 if result:
    #                     break
    #                 else:
    #                     continue
    #             else:
    #                 logger.error("Incorrect chart name.")
    #                 return False
    #         except Exception as err:
    #             logger.error(err)
    #             return False
    #     return result    