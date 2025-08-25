import logging
import os
import json
import requests
import time
import app_menu
import auth
import license
from urllib3.exceptions import InsecureRequestWarning
from tools import File, Tools, Folder
from urllib3 import disable_warnings
disable_warnings(InsecureRequestWarning)

logger = logging.getLogger(__name__)

class Export_data:

    __api_Integration_ObjectModel_Export: str = 'api/Integration/ObjectModel/Export'
    __api_WorkFlowNodes: str = 'api/WorkFlowNodes'
    __api_WorkFlows: str = 'api/WorkFlows'
    _transfer_folder: str = 'transfer_files'
    _workflows_folder: str = 'workflows'
    _workflows_folder_path: str = f'{_transfer_folder}/{_workflows_folder}'
    _object_model_folder: str = 'object_model'
    _all_workflow_nodes_file: str = 'all_workflow_nodes_export_server.json'
    _workflows_draft_file: str = 'Draft_workflows_export_server.json'
    _workflows_archived_file: str = 'Archived_workflows_export_server.json'
    _workflows_active_file: str = 'Active_workflows_export_server.json'
    _selected_workflow_nodes_file: str = 'workflow_nodes_to_import.list'
    _workflowID_bimClassID_file: str = 'workflowID_bimClassID_export_server.json'
    _object_model_file: str = 'object_model_export_server.json'
    _exported_workflows_list: str = 'exported_workflows.list'

    # Needs for separation import procedures on export server during one session.
    _export_server_info_file: str = 'export_server.info'
    AppMenu = app_menu.AppMenu()
    possible_request_errors = auth.Auth().possible_request_errors
    License = license.License()

    def __init__(self):
        self.is_first_launch_export_data: bool = True


    def get_object_model(self, filename, url, token):
        """   Function gets object model from the server, and writes it into a file.   """

        path_to_file = f'{self._transfer_folder}/{self._object_model_folder}/{filename}'
        if os.path.isfile(path_to_file):
            confirm_to_delete = input(f'There is an {filename} file already. Do you want to overwrite it?(y/n): ').lower()
            if confirm_to_delete == 'y':
                os.remove(path_to_file)
            else: return

        headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}
        url_get_object_model: str = url + '/' + self.__api_Integration_ObjectModel_Export
        try:
            response = requests.get(url_get_object_model, headers=headers, verify=False)
            if response.status_code != 200:
                logger.error(f"{self.get_object_model.__name__}\n{response.text}")
            data = response.json()
        except self.possible_request_errors as err:
            logger.error(f"{err}")
            print("Error: Couldn't export object model. Check the logs.")
            return False

        try:
            with open(f"{self._transfer_folder}/{self._object_model_folder}/{filename}", "w", encoding="utf-8") as json_file:
                json.dump(data, json_file, ensure_ascii=False, indent=4)
                logger.info(f"Object model has been exported. '{filename}' file is ready.")
                if filename != 'object_model_import_server.json':
                    print(f"\n   - object model exported in '{filename}' file.")
        except (FileNotFoundError, OSError) as err:
            logger.error(err)
            print('Error occurred. Check the logs.')
            return False
        return True

    def get_workflow_nodes_id(self, url, token):
        """ Function returns a dictionary with all the nodes in format: {"NodeName": "NodeId"}. """

        url_get_all_workflow_nodes = url + '/' + self.__api_WorkFlowNodes
        headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}
        try:
            response = requests.get(url=url_get_all_workflow_nodes, headers=headers, verify=False)
            data = response.json()
        except self.possible_request_errors as err:
            logger.error(f"{err}\n{response.text}") 
            print(f"Error: Couldn't export workFlow nodes. Check the logs.")
            return False

        # Creating a dictionary with all three nodes from the server in format: {"NodeName": "NodeId"}        
        workflow_nodes:dict = {x['name']: x['id'] for x in data}
        return workflow_nodes

    def remove_duplicate_workflows_id(self, wf_id_array):
        """ Check if exported_workflows.list has something from the current exported workflows already. If so, delete them. """

        if os.path.isfile(f"{self._workflows_folder_path}/{self._exported_workflows_list}"):
            tmp_file = "temp.list"
            with open(f"{self._workflows_folder_path}/{self._exported_workflows_list}", 'r', encoding='utf-8') as fr, \
                 open(f"{self._workflows_folder_path}/{tmp_file}", 'w', encoding='utf-8') as fw:
                for line in fr:
                    id = line.strip('\n').split()[1]
                    if id not in wf_id_array:
                        fw.write(line)
            os.replace(f"{self._workflows_folder_path}/{tmp_file}", f"{self._workflows_folder_path}/{self._exported_workflows_list}")

    def export_workflows_at_once(self, url, token, workflows: dict):
        """ Function to export workflows at once.
            api/Integration/WorkFlow/{workflow_id}/Export method's response needs to be saved as a zip file for each process.
        """

        count = Tools.counter()
        headers = {'accept': '*/*', 'Authorization': f"Bearer {token}"}
        nodes_to_remove = [node for node in workflows if not workflows[node]]
        {workflows.__delitem__(node) for node in nodes_to_remove}
        workflows_id = [id for node in workflows.values() for id in node]
        self.remove_duplicate_workflows_id(workflows_id)
        with open(f"{self._workflows_folder_path}/{self._exported_workflows_list}", mode='a', encoding='utf-8') as file:
            for node in workflows:
                for id, name in workflows[node].items():
                    try:
                        url_export = f"{url}/api/Integration/WorkFlow/{id}/Export"
                        response = requests.get(url=url_export, headers=headers, verify=False)
                    except self.possible_request_errors as err:
                        logger.error(f"{err}\n{response.text}")
                    print(f"   {count()}){node}: {name}")   # display the name of the process in the output
                    time.sleep(0.1)
                    try:
                        with open(f"{self._workflows_folder_path}/{id}.zip", mode='wb') as zip_file:
                            zip_file.write(response.content)
                        file.write("{0}  {1}  {2}\n".format(node, id, name))
                    except OSError as err:
                        logger.error(err)
                        continue
        return True

    def export_workflows_by_choice(self, url, token, wf_id_array):
        """ Function to export only specified workflows. """

        count = Tools.counter()
        headers = {'accept': '*/*', 'Authorization': f"Bearer {token}"}
        nodes: dict = self.get_workflow_nodes_id(url, token)
        self.remove_duplicate_workflows_id(wf_id_array)
        with open(f"{self._workflows_folder_path}/{self._exported_workflows_list}", mode='a', encoding='utf-8') as file:
            for id in wf_id_array:
                issue_message = lambda wf_id: print("Error: WorkFlow <{0}> wasn't exported. Check the logs.".format(wf_id))
                try:
                    url_export = f"{url}/api/WorkFlows/{id}"
                    response = requests.get(url=url_export, headers=headers, verify=False)
                    data = response.json()
                    workflow_name, node_id = data['name'], data['workFlowNodeId']
                except self.possible_request_errors as err:
                    logger.error(f"{err} {response.status_code}\n{response.text}")
                    issue_message(id)
                    continue
                except Exception as err:
                    logger.error(f"{err} {response.status_code}\n{data}")
                    if response.status_code == 400 and data['type']:
                        print("InvalidInfoModelException. WorkFlow ID is incorrect. Check the logs.")
                    elif response.status_code == 404:
                        print(f"NotFoundDataException. WorkFlow: <{id}> wasn't found. Check the logs.")
                    continue
                else:
                    url_export = f"{url}/api/Integration/WorkFlow/{id}/Export"
                    try:
                        response = requests.get(url=url_export, headers=headers, verify=False)
                        node_name: set = {key for key in nodes if nodes[key] == node_id}
                        with open(f"{self._workflows_folder_path}/{id}.zip", mode='wb') as zip_file:
                            zip_file.write(response.content)
                        file.write("{0}  {1}  {2}\n".format(*node_name, id, workflow_name))
                        time.sleep(0.1)
                        print("   {0}){1}: {2}".format(count(), *node_name, workflow_name))
                    except self.possible_request_errors as err:
                        logger.error(f"{err} {response.status_code}\n{response.text}")
                        issue_message(workflow_name)
                        continue
                    except OSError as err:
                        logger.error(err)
                        issue_message(workflow_name)
                        continue
                    except Exception as err:
                        logger.error(err)
                        issue_message(workflow_name)
                        continue
        return True

    def define_needed_workflows(self, url, token, *args, **kwargs):
        """ Define a dictionary with needed workflows. """

        headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}
        workflows: dict = {'Draft': {}, 'Active': {}, 'Archived': {}}
        workflow_nodes = self.get_workflow_nodes_id(url, token)
        if len(args) < 1:
            print("At least one of the arguments must be provided: --draft --active --archived --all")
            return
        if kwargs['startswith'] and kwargs['search_for']:
            print("Can't use both arguments '--startswith' and '--search' together")
            return
        selected_nodes = [x for x in args[0] if x in ('--draft', '--active', '--archived', '--all')]
        if '--all' not in selected_nodes:
            nodes_to_remove = [node for node in workflow_nodes.keys() if ''.join(('--', node)).lower() not in selected_nodes and len(selected_nodes) > 0]
            {workflow_nodes.__delitem__(node) for node in nodes_to_remove}
        if not selected_nodes:
            print("At least one of the nodes must be provided: --draft, --active, --archived, --all")
            return False
        for name, id in workflow_nodes.items():
                url_get_workflows = f"{url}/{self.__api_WorkFlowNodes}/{id}/children"
                try:
                    response = requests.get(url_get_workflows, headers=headers, verify=False)
                    data = response.json()
                except self.possible_request_errors as err:
                    logger.error(f"{err}\n{response.text}")
                for workflow in data['workFlows']:
                    if kwargs['type'] and kwargs['type'] != self.get_workflow_type(url, token, workflow['id']):
                        continue
                    if kwargs['startswith'] and workflow['name'].startswith(kwargs['startswith']):
                        workflows[name][workflow['id']] = workflow['name']
                    elif kwargs['search_for'] and workflow['name'].find(kwargs['search_for']) != -1:
                        workflows[name][workflow['id']] = workflow['name']
                    elif not kwargs['startswith'] and not kwargs['search_for']:
                        workflows[name][workflow['id']] = workflow['name']
        return False if (not workflows['Active'] and not workflows['Draft'] and not workflows['Archived']) else workflows

    def display_list_of_workflowsName_and_workflowsId(self, workflows: dict):
        """ Function to display workFlows on the screen and save that info to a file. """

        count = Tools.counter()
        for node in workflows:
            for id, name in workflows[node].items():
                time.sleep(0.03)
                print(f'   {count()}){node}: {id}  {name}')

    def delete_workflows(self, url, token, workflows: dict):
        """ Function to delete workFlows from a certain node, or all at once. """

        count = Tools.counter()
        headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}
        nodes_to_remove = [node for node in workflows if not workflows[node]]
        {workflows.__delitem__(node) for node in nodes_to_remove}
        for node in workflows:
            for id, name in workflows[node].items():
                try:
                    url_delete_workflow = f"{url}/{self.__api_WorkFlows}/{id}"
                    response = requests.delete(url_delete_workflow, headers=headers, verify=False)
                    if response.status_code != 204:
                        print(f"Error: {name} wasn't removed. Status code: {response.status_code}. Check the log.")
                        logger.error(f"{id}: {response.status_code}\n{response.text}")
                    print(f'   {count()}){node}: {name}')
                except self.possible_request_errors as err:
                    logger.error(f"{err}\n{response.text}")
        return True    

    def export_server_info(self, url, token):
        response = self.License.get_serverID(url, token)
        success: bool = response[0]
        message: str = response[1]
        if not success:
            print(f"Error: {message}")
        else:
            serverId: str = message
        with open(f'{self._transfer_folder}/{self._export_server_info_file}', 'w', encoding='utf-8') as file:
            file.write("{0}\n".format(url.split('//')[1]))
            file.write(serverId)

    def create_folders_for_export_files(self):
        """ Create transfer files catalog. """

        Folder.create_folder(os.getcwd(), self._transfer_folder)
        time.sleep(0.1)
        Folder.create_folder(os.getcwd() + '/' + self._transfer_folder, self._workflows_folder)
        time.sleep(0.1)
        Folder.create_folder(os.getcwd() + '/' + self._transfer_folder, self._object_model_folder)
        time.sleep(0.1)
        self.is_first_launch_export_data = False

    def get_workflow_type(self, url, token, id):
        """ Get information about workflow """

        headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}
        url = f"{url}/{self.__api_WorkFlows}/{id}"
        try:
            response = requests.get(url=url, headers=headers, verify=False)
            if response.status_code != 200:
                logger.error(f"{id}: {response.status_code}\n{response.text}")
                print(f"Error: check the log!")
            data = response.json()
            return data['type'].lower()
        except self.possible_request_errors as err:
            logger.error(f"{err}\n{response.text}")
            return False


    def print_help(self, ls=False, export=False, remove=False):
        """ Provide help info for the user. """

        ls_workflows: str = """usage: ls workflows [--help] [--startswith \"TEXT TO FIND\" | --search \"TEXT TO FIND\"] [--draft] [--active] [--archived] [--all]

options:
  -h, --help    Show this help message
  --startswith  Pattern to search from the beginning of the line
  --search      Pattern to search at any place of the line
  --draft       Draft node of workflows
  --active      Active node of workflows
  --archived    Archived node of workflows
  --all         All three nodes
  --type        Workflows type
"""
        export_workflows: str = """usage: export workflows [--help] [--startswith \"TEXT TO FIND\" | --search \"TEXT TO FIND\" | --id="WORKFLOW(S) ID"] [--draft] [--active] [--archived] [--all]

options:
  -h, --help    Show this help message
  --startswith  Pattern to search from the beginning of the line
  --search      Pattern to search at any place of the line
  --id          One or more workflow ID separated with whitespace
  --draft       Draft node of workflows
  --active      Active node of workflows
  --archived    Archived node of workflows
  --all         All three nodes
"""
        remove_workflows: str = """usage: rm workflows [--help] [--draft] [--active] [--archived] [--all]

options:
  -h, --help    Show this help message
  --draft       Draft node of workflows
  --active      Active node of workflows
  --archived    Archived node of workflows
  --all         All three nodes
"""

        if ls: print(ls_workflows)
        elif export: print(export_workflows)
        elif remove: print(remove_workflows)
