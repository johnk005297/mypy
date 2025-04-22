import yaml
import base64
import requests
from log import Logs
from colorama import init, Fore
init(autoreset=True)
from rich.console import Console
from rich.table import Table

class Git:
    _headers = {"PRIVATE-TOKEN": "my-token"}
    _url = "https://git.company.io/api/v4"
    _logger = Logs().f_logger(__name__)
    _error_msg = "Unexpected error. Check logs!"

    def __init__(self):
        self.tag = Tag
        self.project = Project
        self.branch = Branch
        self.job = Job
        self.pipeline = Pipeline
        self.tree = Tree
        self.product_collection = Product_collection_file
        self.chart = Chart

    def display_table_with_branches_commits_tags_jobs(self, data) -> Table:
        """ Create table, fill with data(branches, commits, tags, helm chart job status, FT job status) and print it out. """

        if not data:
            return False
        table = Table(show_lines=False)
        table.add_column("Branch", justify="left", no_wrap=True, style="#875fff", max_width=55)
        table.add_column("Commit", justify="left", style="#875fff")
        table.add_column("Tag", justify="left", style="#875fff")
        table.add_column("Helm charts", justify="left", style="#875fff")
        # table.add_column("Pipeline", justify="left", style="#875fff")
        for x in data:
            # table.add_row(x[0], x[1], x[2], x[3], str(x[4]))
            table.add_row(x[0], x[1], x[2], x[3])
        console = Console()
        console.print(table)


class Project(Git):

    def get_project_id(self, project='bimeister') -> int:
        """ Get from Gitlab ID of the project bimeister. """

        __url = f"{self._url}/search?scope=projects&search={project}"
        try:
            response = requests.get(url=__url, headers=self._headers, verify=False)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.ConnectionError as err:
            self._logger.error(err)
            print("No connection to gitlab. Check the logs. Exit!")
            return False
        except requests.exceptions.RequestException as err:
            print(self._error_msg)
            self._logger.error(err)
            return False
        project: dict = [x for x in data if x['name'] == project][0]
        return project['id'] if project else False

class Chart(Git):

    def is_chart_available(self, repo_url='https://nexus.bimeister.io/service/rest/repository/browse/bim-helm/bimeister', commit=None):
        """ Check if helm charts are available for download. """

        result: bool = False
        for x in range(15, 25):
            version: str = f"1.{x}.0-sha{commit}"
            try:
                response = requests.get(repo_url)
                response.raise_for_status()
                index = yaml.safe_load(response.text)
                search = index.find(version)
                if search == -1:
                    continue
                elif search > -1:
                    result = True
                    return True
            except Exception as err:
                self._logger.error(err)
                return False
        return result

class Tag(Git):

    def search_tag(self, project_id, search: list) -> dict:
        """ Search for needed tags. """

        __url = f"{self._url}/projects/{project_id}/repository/tags"
        tag_data = dict()
        for x in search:
            try:
                payload = {'search': x}
                response = requests.get(url=__url, headers=self._headers, params=payload, verify=False)
                response.raise_for_status()
                data = response.json()
            except requests.exceptions.RequestException as err:
                self._logger.error(err)
                print(self._error_msg)
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

        tags: dict = self.tag().search_tag(project_id, search)
        result_data: list = []
        for x in search:
            url = f"{self._url}/projects/{project_id}/repository/branches?regex=\D{x}"
            try:
                response = requests.get(url=url, headers=self._headers)
                response.raise_for_status()
            except requests.exceptions.RequestException as err:
                print(self._error_msg)
                self._logger.error(err)
                return False
            for branch in response.json():
                branch_commit = branch['commit']['short_id']
                if tags and tags.get(branch['commit']['short_id']):
                    tag_name =  tags[branch['commit']['short_id']]['tag_name']
                    del tags[branch['commit']['short_id']]
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
                    'Ready' if self.chart().is_chart_available(commit=branch_commit) else 'Not ready'
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
                                    'Ready' if self.chart().is_chart_available(commit=tag) else 'Not ready'
                                    ])
        if not result_data:
            print("No branches were found!")
            return False
        return result_data

    def get_branch_name_using_commit(self, project_id, commit) -> list:
        """ Get branch name(s) using commit from a given repository. """

        url = f"{self._url}/projects/{project_id}/repository/commits/{commit}/refs?type=branch&per_page=100"
        try:
            response = requests.get(url=url, headers=self._headers, verify=False)
            response.raise_for_status()
            branches: list = [x['name'] for x in response.json()]
            return branches if branches else False
        except requests.exceptions.RequestException as err:
            self._logger.error(err)
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
            response = requests.get(url=url, headers=self._headers, verify=False)
            response.raise_for_status()
            jobs = response.json()
        except requests.exceptions.RequestException as err:
            self._logger.error(err)
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
            self._logger.error(f"{self.job.__qualname__} Incorrect data transferred.")
            raise TypeError("Run job function accepts project_id and job_id as a list.")
        for id in job_id:
            url = f"{self._url}/projects/{project_id}/jobs/{id}/play"
            try:
                response = requests.post(url=url, headers=self._headers, verify=False)
                response.raise_for_status()
                data = response.json()
                if response.status_code == 200:
                    print(f"Job started successfully                \
                          \nname: {data['name']}                    \
                          \npipeline id: {data['pipeline']['id']}   \
                          \nref: {data['pipeline']['ref']}          \
                          \nurl: {data['pipeline']['web_url']}      ")
            except requests.exceptions.RequestException as err:
                print(self._error_msg)
                self._logger.error(err)
                return False                
            except Exception as err:
                self._logger.error(err)
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
                response = requests.get(url=url, headers=self._headers, params=payload, verify=False)
                response.raise_for_status()
                for pipeline in response.json():
                    pipelines.append(pipeline)
            except requests.exceptions.RequestException as err:
                self._logger.error(err)
                print("Error getting pipelines. Check the log.")
                return False
        # sort pipelines by id
        pipelines = sorted(pipelines, key=lambda x: x['id'], reverse=True)
        return pipelines


class Tree(Git):

    def print_list_of_branch_files(self, project_id, branch_name):
        """ Get a list of tree. """

        url = f"{self._url}/projects/{project_id}/repository/tree?ref={branch_name}"
        try:
            response = requests.get(url=url, headers=self._headers)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as err:
            self._logger.error(err)
            print(self._error_msg)
            return False
        except Exception as err:
            self._logger.error(err)
            print(self._error_msg)
            return False
        for x in data:
            print(x['name'])


class Product_collection_file(Git):

    def get_product_collection_file_content(self, project_id, commit):
        """ Get a product-collection.yaml file content. """

        url = f"{self._url}/projects/{project_id}/repository/files/product-collections%2Eyaml?ref={commit}"
        try:
            response = requests.get(url=url, headers=self._headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(self._error_msg)
            self._logger.error(err)
            return False
        except requests.exceptions.RequestException as err:
            print(self._error_msg)
            self._logger.error(err)
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
                return False
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
                print(Fore.RED + "\n  Removed: {0}".format(db_removed))
            if db_added:
                print(Fore.GREEN + "{0}  Added: {1}".format("" if db_removed else "\n", db_added))
        else:
            print("\nDatabases: Total match!")
        if not first_commit_services == second_commit_services:
            svc_removed = first_commit_services.difference(second_commit_services)
            svc_added = second_commit_services.difference(first_commit_services)
            print("Services:", end=" ")
            if svc_removed:
                print(Fore.RED + "\n  Removed: {0}".format(svc_removed))
            if svc_added:
                print(Fore.GREEN + "{0}  Added: {1}".format("" if svc_removed else "\n", svc_added))
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
        console = Console()
        console.print(table)


    ### NOT IN USE ###
    # def get_tags(self, project_id):
    #     """ Get needed tags for provided project_id. """

    #     url = f"{self.__url}/projects/{project_id}/repository/tags"
    #     try:
    #         response = requests.get(url=url, headers=self.__headers, verify=False)
    #         response.raise_for_status()
    #         data = response.json()
    #     except requests.exceptions.RequestException as err:
    #         self.__logger.error(err)
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
    #             response = requests.get(url=url, headers=self._headers)
    #             response.raise_for_status()
    #         except requests.exceptions.RequestException as err:
    #             print(self._error_msg)
    #             self._logger.error(err)
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