import yaml
import base64
import requests
from log import Logs
from prettytable import PrettyTable
from colorama import init, Fore
init(autoreset=True)
from rich.console import Console
from rich.table import Table

class Git:
    __headers = {"PRIVATE-TOKEN": "my_token"}
    __url = "https://git.bimeister.io/api/v4"
    __logger = Logs().f_logger(__name__)
    __error_msg = "Unexpected error. Check the logs!"


    def get_pipelines(self, project_id):
        """ Get a list of pipelines. """

        url = f"{self.__url}/projects/{project_id}/pipelines"
        response = requests.get(url=url, headers=self.__headers)
        data = response.json()
        print(data)

    def get_tree(self, project_id, branch_name):
        """ Get a list of tree. """

        url = f"{self.__url}/projects/{project_id}/repository/tree?ref={branch_name}"
        try:
            response = requests.get(url=url, headers=self.__headers)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as err:
            print(self.__error_msg)
            self.__logger.error(err)
            return False
        for x in data:
            print(x['name'])

    def get_branch_name_using_commit(self, project_id, commit):
        """ Get needed commit from a given repository. """

        url = f"{self.__url}/projects/{project_id}/repository/commits/{commit}/refs?type=branch"
        try:
            response = requests.get(url=url, headers=self.__headers)
            response.raise_for_status()
            data = response.json()
            return data[0]['name'] if data else "-"
        except requests.exceptions.RequestException as err:
            self.__logger.error(err)
            print(self.__error_msg)
            return False

    def get_bimeister_project_id(self):
        """ Get from Gitlab ID of the project bimeister. """

        url = f"{self.__url}/search?scope=projects&search=bimeister"
        try:
            response = requests.get(url=url, headers=self.__headers)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.ConnectionError as err:
            self.__logger.error(err)
            print("No connection to gitlab. Check the logs. Exit!")
            return False
        except requests.exceptions.RequestException as err:
            print(self.__error_msg)
            self.__logger.error(err)
            return False
        project: dict = [x for x in data if x['name'] == 'bimeister'][0]
        return project['id']

    ### Need to rebuild ##
    def get_tags(self, project_id):
        """ Get needed tags for provided project_id. """

        url = f"{self.__url}/projects/{project_id}/repository/tags"
        try:
            response = requests.get(url=url, headers=self.__headers)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as err:
            self.__logger.error(err)
            print(self.__error_msg)
            return False
        return data

    def search_tag(self, project_id, search: list):
        """ Search for needed tags. """

        url = f"{self.__url}/projects/{project_id}/repository/tags"
        tag_data = dict()
        for x in search:
            try:
                payload = {'search': x}
                response = requests.get(url=url, headers=self.__headers, params=payload, verify=False)
                response.raise_for_status()
                data = response.json()
            except requests.exceptions.RequestException as err:
                self.__logger.error(err)
                print(self.__error_msg)
                return False
            for tag in data:
                branch = self.get_branch_name_using_commit(project_id, tag['commit']['short_id'])
                tag_data[tag['commit']['short_id']] = {'tag_name': tag['name'], 'branch_name': branch}
        if not tag_data:
            return False
        else:
            return tag_data

    def search_branches(self, project_id, search: list):
        """ Search and print list of branches with their commits and tags. """

        tags: dict = self.search_tag(project_id, search)
        branches: list = []
        table = Table(show_lines=False)
        table.add_column("Branch", justify="left", no_wrap=True, style="#875fff")
        table.add_column("Commit", justify="left", style="#875fff")
        table.add_column("Tag", justify="left", style="#875fff")
        for x in search:
            url = f"{self.__url}/projects/{project_id}/repository/branches?regex=\D{x}"
            try:
                response = requests.get(url=url, headers=self.__headers)
                response.raise_for_status()
            except requests.exceptions.RequestException as err:
                print(self.__error_msg)
                self.__logger.error(err)
                return False
            for branch in response.json():
                if tags and tags.get(branch['commit']['short_id']):
                    branches.append([branch['name'], branch['commit']['short_id'], tags[branch['commit']['short_id']]['tag_name']])
                    tags.pop(branch['commit']['short_id'], None)
                else:
                    branches.append([branch['name'], branch['commit']['short_id'], '-'])
            if tags:
                for tag in tags:
                    branches.append([tags[tag]['branch_name'], tag, tags[tag]['tag_name']])
        if not branches:
            print("No branches were found!")
            return True
        result_data = list(map(list,set(map(tuple, branches)))) # remove duplicates from the final result search
        for x in result_data:
            table.add_row(x[0], x[1], x[2])
        console = Console()
        console.print(table)

    def get_product_collection_file_content(self, project_id, commit):
        """ Get a product-collection.yaml file content. """

        url = f"{self.__url}/projects/{project_id}/repository/files/product-collections%2Eyaml?ref={commit}"
        try:
            response = requests.get(url=url, headers=self.__headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(self.__error_msg)
            self.__logger.error(err)
            return False
        except requests.exceptions.RequestException as err:
            print(self.__error_msg)
            self.__logger.error(err)
            return False
        data_base64 = response.json()['content']
        data_bytes = data_base64.encode('utf-8')
        decode_bytes = base64.b64decode(data_bytes)
        decode_string = decode_bytes.decode('utf-8')
        data: dict = yaml.safe_load(decode_string)
        return(data)

def parse_product_collection_yaml(data: dict, project_name=''):
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
            print("Wrong input.")
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


# def compare_two_commits(first_commit_services: list, first_commit_db: list, second_commit_services: list, second_commit_db: list):
#     """ Compare to commits with each other. Search for the difference in DBs lists and services lists. """

#     first_commit_services: set = set(first_commit_services)
#     first_commit_db: set = set(first_commit_db)
#     second_commit_services: set = set(second_commit_services)
#     second_commit_db: set = set(second_commit_db)

#     if not first_commit_db == second_commit_db:
#         db_removed = first_commit_db.difference(second_commit_db)
#         db_added = second_commit_db.difference(first_commit_db)
#         print("\nDatabases:", end=" ")
#         if db_removed:
#             print(Fore.RED + "\n  Removed: {0}".format(db_removed))
#         if db_added:
#             print(Fore.GREEN + "{0}  Added: {1}".format("" if db_removed else "\n", db_added))
#     else:
#         print("\nDatabases: Total match!")
#     if not first_commit_services == second_commit_services:
#         svc_removed = first_commit_services.difference(second_commit_services)
#         svc_added = second_commit_services.difference(first_commit_services)
#         print("Services:", end=" ")
#         if svc_removed:
#             print(Fore.RED + "\n  Removed: {0}".format(svc_removed))
#         if svc_added:
#             print(Fore.GREEN + "{0}  Added: {1}".format("" if svc_removed else "\n", svc_added))
#     else:
#         print("Services: Total match!")

def compare_two_commits(first_commit_services: list, first_commit_db: list, second_commit_services: list, second_commit_db: list):
    """ Compare to commits with each other. Search for the difference in DBs lists and services lists. """

    first_commit_services: set = set(first_commit_services)
    first_commit_db: set = set(first_commit_db)
    second_commit_services: set = set(second_commit_services)
    second_commit_db: set = set(second_commit_db)
    table = Table()
    table.add_column("Services", justify="left", no_wrap=True, style="magenta")
    table.add_column("Databases", justify="left", style="magenta")
    if not first_commit_services == second_commit_services:
        svc_removed = first_commit_services.difference(second_commit_services)
        svc_added = second_commit_services.difference(first_commit_services)
    else:
        table.add_row("Total match!")
    if not first_commit_db == second_commit_db:
        db_removed = first_commit_db.difference(second_commit_db)
        db_added = second_commit_db.difference(first_commit_db)
    else:
        table.add_row("Total match!")
    console = Console()
    console.print(table)

def print_services_and_db(svc: list, db: list, project_name=''):
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
