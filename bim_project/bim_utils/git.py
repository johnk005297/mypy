import os
import yaml
import base64
import requests
from log import Logs
from prettytable import PrettyTable
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

class Git:
    token = os.getenv("PRIVATE_TOKEN")
    __headers = {"PRIVATE-TOKEN": token}
    __url = "https://git.bimeister.io/api/v4"
    __logger = Logs().f_logger(__name__)
    __error_msg = "Unexpected error. Check the logs!"

    def get_bimeister_project_id(self):
        """ Get from Gitlab ID of the project bimeister. """

        url = f"{self.__url}/search?scope=projects&search=bimeister"
        try:
            response = requests.get(url=url, headers=self.__headers)
        except requests.exceptions.ConnectionError as err:
            self.__logger.error(err)
            print("No connection to gitlab. Check the logs. Exit!")
            return False
        except Exception as err:
            print(self.__error_msg)
            self.__logger.error(err)
            return False
        data: dict = [x for x in response.json() if x['name'] == 'bimeister'][0]
        return data['id']

    def get_commit(self, project_id, commit):
        """ Get needed commit from a given repository. """

        url = f"{self.__url}/projects/{project_id}/repository/commits/{commit}"
        try:
            response = requests.get(url=url, headers=self.__headers)
            data = response.json()
            return data
        except Exception as err:
            print(self.__error_msg)
            self.__logger.error(err)
            return False

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
        except Exception as err:
            print(self.__error_msg)
            self.__logger.error(err)
            return False
        data = response.json()
        for x in data:
            print(x['name'])

    def list_branches(self, project_id, search):
        """ Get a list of branches with there commits. """

        url = f"{self.__url}/projects/{project_id}/repository/branches?regex={search}"
        try:
            response = requests.get(url=url, headers=self.__headers)
        except Exception as err:
            print(self.__error_msg)
            self.__logger.error(err)
            return False
        data = response.json()
        table = PrettyTable()
        table.field_names = ['Branch', 'Commit']
        table.align = 'l'
        for dct in data:
            table.add_row([dct['name'], dct['commit']['short_id']])
        print(table)

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
        except Exception as err:
            print(self.__error_msg)
            self.__logger.error(err)
            return False
        data_base64 = response.json()['content']
        data_bytes = data_base64.encode('utf-8')
        decode_bytes = base64.b64decode(data_bytes)
        decode_string = decode_bytes.decode('utf-8')
        data: dict = yaml.safe_load(decode_string)
        return(data)


def parse_product_collection_yaml(data):
    """ Function returns two lists with services and DB for a chosen project. """

    if not data:
        return False
    for num, project in enumerate(data['collections'], 1):
        print(f"{num}. {project}")
    try:
        inp = int(input('Choose number of the project: '))
        project = list(data['collections'])[inp - 1]
    except ValueError:
        print("Wrong input.")
        return False

    modules_and_services: dict = data['modules']
    modules = set(data['collections'][project]['modules'])
    services_list: list = []
    for module in modules:
        if module not in modules_and_services:
            print(f"<{module}> module does not exist in the global modules list!")
            continue
        for service in modules_and_services[module]:
            if service not in services_list:
                services_list.append(service)
    services_list = sorted(services_list)

    db_list: list = []
    for svc in services_list:
        if data['services'][svc].get('db') and data['services'][svc]['db']['key'] == 'db':
            db_list.append('bimeisterdb')
        elif data['services'][svc].get('db'):
            db_list.append(data['services'][svc]['db']['key'])
    db_list = sorted(list(set(db_list)))
    return services_list, db_list

def print_services_and_db(svc, db):
    """ Function for displaying collection on a screen. """

    if not svc or not db:
        return False
    print("\nDatabases:")
    for x in db:
        print('  ' + x)
    print("Total: {0}".format(len(db)))
    print("\nServices:")
    for x in svc:
        print('  ' + x)
    print("Total: {0}".format(len(svc)))
