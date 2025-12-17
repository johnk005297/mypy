import logging
import os
import json
import time
from license import License
import textwrap
from rich.console import Console
from urllib3.exceptions import InsecureRequestWarning
from tools import Tools, Folder, ScrollablePanel
from mlogger import Logs
from urllib3 import disable_warnings
disable_warnings(InsecureRequestWarning)

_logger = logging.getLogger(__name__)
_logs = Logs()



def export_server_info(url: str, token: str, filepath: str) -> str:
    """
    Processes data(received server ID) and writes it to a file on disk.
    Returns the absolute path to the generated text file.
    """
    response = License.get_serverID(License, url, token)
    success: bool = response[0]
    message: str = response[1]
    if not success:
        print(f"Error: {message}")
        return None
    else:
        serverId: str = message
    try:
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write("{0}\n".format(url.split('//')[1]))
            file.write(serverId)
    except FileNotFoundError as err:
        print(err)
        return None
    return filepath


class Object_model:

    __api_Integration_ObjectModel_Export: str = 'api/Integration/ObjectModel/Export'
    _transfer_folder: str = 'transfer_files'
    _object_model_folder: str = 'object_model'
    _object_model_file: str = 'object_model_export_server.json'
    _om_export_server_info_file: str = '_object_model_export_server.info' # needs for separation import procedures on export server during one session

    def __init__(self):
        self.failed_workflows: list = []
        self.exported_workflows: list = []
        self.tools = Tools()
        self.console = Console()

    def is_export_obj_model_file_exists(self):
        """ Check if the exported object model file already exists.
            Need to figurate if it's the first launch of export operation or not.
        """


    def create_folders_to_export_om(self):
        """ Function creates transfer_files/object_model catalogs at the current user location. """

        Folder.create_folder(os.getcwd(), self._transfer_folder)
        time.sleep(0.1)
        Folder.create_folder(os.getcwd() + '/' + self._transfer_folder, self._object_model_folder)
        time.sleep(0.1)

    def export_object_model(self, filename, url, token):
        """   Function gets object model from the server, and writes it into a file.   """

        path_to_file = f'{self._transfer_folder}/{self._object_model_folder}/{filename}'
        if os.path.isfile(path_to_file):
            confirm_to_delete = input('File already exists. Do you want to overwrite it?(Y/N): ').lower()
            if confirm_to_delete in ('y', 'yes'):
                os.remove(path_to_file)
            else: return
        headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}
        url += '/' + self.__api_Integration_ObjectModel_Export
        with self.console.status("Exporting object model...", spinner="earth"):
            response = self.tools.make_request('GET', url, headers=headers, verify=False, return_err_response=True)
            if response.status_code not in range(200, 205):
                _logger.error(response.text)
                print(_logs.err_message)
                return None
            else:
                data = response.json()
        try:
            with open(f"{self._transfer_folder}/{self._object_model_folder}/{filename}", "w", encoding="utf-8") as json_file:
                json.dump(data, json_file, ensure_ascii=False, indent=4)
                _logger.info(f"Object model has been exported. '{filename}' file is ready.")
                print(f"Successfully exported to: {self._transfer_folder}/{self._object_model_folder}/{filename}")
        except (FileNotFoundError, OSError) as err:
            _logger.error(err)
            print(_logs.err_message)
            return None
        return True


class Workflows:

    __api_WorkFlowNodes: str = 'api/WorkFlowNodes'
    __api_WorkFlows: str = 'api/WorkFlows'
    _transfer_folder: str = 'transfer_files'
    _workflows_folder: str = 'workflows'
    _workflows_folder_path: str = f'{_transfer_folder}/{_workflows_folder}'
    _all_workflow_nodes_file: str = 'all_workflow_nodes_export_server.json'
    _workflows_draft_file: str = 'Draft_workflows_export_server.json'
    _workflows_archived_file: str = 'Archived_workflows_export_server.json'
    _workflows_active_file: str = 'Active_workflows_export_server.json'
    _selected_workflow_nodes_file: str = 'workflow_nodes_to_import.list'
    _exported_workflows_list: str = 'exported_workflows.list'
    _wf_export_server_info_file: str = '_wf_export_server.info' # needs for separation import procedures on export server during one session

    def __init__(self):
        self.issue_message = lambda status_code, wf: print("Error {0}: {1}.".format(status_code, wf))
        self.tools = Tools()
        self.console = Console()

    def create_folders_to_export_wf(self):
        """ Function creates transfer_files/workflows catalogs at the current user location. """

        Folder.create_folder(os.getcwd(), self._transfer_folder)
        time.sleep(0.1)
        Folder.create_folder(os.getcwd() + '/' + self._transfer_folder, self._workflows_folder)
        time.sleep(0.1)

    def get_workflow_nodes_id(self, url, token):
        """ Function returns a dictionary with all the nodes in format: {"NodeName": "NodeId"}. """

        url += '/' + self.__api_WorkFlowNodes
        headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}
        response = self.tools.make_request('GET', url, headers=headers, verify=False)
        try:
            data = response.json()
        except Exception as err:
            _logger.error(err)
            print(_logs.err_message)
            return None
        # Creating a dictionary with all three nodes from the server in format: {"NodeName": "NodeId"}
        workflow_nodes:dict = {x['name']: x['id'] for x in data}
        return workflow_nodes

    def define_needed_workflows(self, url, token, *args, **kwargs) -> dict:
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
                response = self.tools.make_request('GET', url_get_workflows, headers=headers, verify=False)
                try:
                    data = response.json()
                except Exception as err:
                    _logger.error(err)
                    print(_logs.err_message)
                    return None
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

    def get_workflow_type(self, url, token, id):
        """ Get information about workflow """

        headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}
        url += f"/{self.__api_WorkFlows}/{id}"
        response = self.tools.make_request('GET', url, headers=headers, verify=False)
        try:
            data = response.json()
        except Exception as err:
            _logger.error(err)
            print(_logs.err_message)
            return None
        return data['type'].lower()

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

    def export_workflows_at_once(self, url: str, token: str, workflows: dict):
        """ Function to export workflows at once.
            api/Integration/WorkFlow/{workflow_id}/Export method response needs to be saved as a zip file for each process.
        """

        # with self.console.status(power_on_msg, spinner="earth") as status:
        headers = {'accept': '*/*', 'Authorization': f"Bearer {token}"}
        failed_workflows = []
        exported_workflows = []
        nodes_to_remove = [node for node in workflows if not workflows[node]]
        {workflows.__delitem__(node) for node in nodes_to_remove}
        workflows_id: list = [id for node in workflows.values() for id in node]
        self.remove_duplicate_workflows_id(workflows_id)
        with self.console.status("Collecting workflows...", spinner="earth") as status:
            with open(f"{self._workflows_folder_path}/{self._exported_workflows_list}", mode='a', encoding='utf-8') as file:
                for node in workflows:
                    status.update("Collecting {} workflows...".format(node))
                    for id, name in workflows[node].items():
                        wf_title: str = textwrap.shorten("{0}: {1}".format(node, name), width=75, placeholder="...")
                        url_export = f"{url}/api/Integration/WorkFlow/{id}/Export"
                        response = self.tools.make_request('GET', url_export, headers=headers, verify=False, return_err_response=True)
                        if response.status_code not in range(200, 205):
                            _logger.error(response.text)
                            failed_workflows.append("Error {0}: {1})".format(response.status_code, name))
                            continue
                        exported_workflows.append(wf_title)
                        time.sleep(0.003)
                        try:
                            with open(f"{self._workflows_folder_path}/{id}.zip", mode='wb') as zip_file:
                                zip_file.write(response.content)
                            file.write("{0}  {1}  {2}\n".format(node, id, name))
                        except OSError as err:
                            _logger.error(err)
                            continue
        successful_workflows: int = len(exported_workflows)
        exported_workflows.extend(failed_workflows)
        panel = ScrollablePanel(exported_workflows, title="Exported workflows", height=10, width=95)
        panel.auto_scroll(delay=0.07)
        print(f"Successful: {successful_workflows} Failed: {len(failed_workflows)}")
        return True

    def export_workflows_by_choice(self, url, token, wf_id_array):
        """ Function to export only specified workflows. """

        headers = {'accept': '*/*', 'Authorization': f"Bearer {token}"}
        nodes: dict = self.get_workflow_nodes_id(url, token)
        count = self.tools.counter()
        self.remove_duplicate_workflows_id(wf_id_array)
        failed_workflows = []
        with open(f"{self._workflows_folder_path}/{self._exported_workflows_list}", mode='a', encoding='utf-8') as file:
            for id in wf_id_array:
                url_export = f"{url}/api/WorkFlows/{id}"
                response = self.tools.make_request('GET', url_export, headers=headers, verify=False, return_err_response=True)
                if response.status_code not in range(200, 205):
                    _logger.error(response.text)
                    if response.status_code == 400 and data['type']:
                        print("InvalidInfoModelException. WorkFlow ID is incorrect. Check the logs.")
                    elif response.status_code == 404:
                        print(f"NotFoundDataException: <{id}> wasn't found. Check the logs.")
                    continue
                try:
                    data = response.json()
                    workflow_name, node_id = data['name'], data['workFlowNodeId']
                except Exception as err:
                    _logger.error(err)
                    print(_logs.err_message)
                    continue
                else:
                    url_export = f"{url}/api/Integration/WorkFlow/{id}/Export"
                    try:
                        response = self.tools.make_request('GET', url_export, headers=headers, verify=False, return_err_response=True)
                        node_name: set = {key for key in nodes if nodes[key] == node_id}
                        if response.status_code not in range(200, 205):
                            _logger.error(response.text)
                            failed_workflows.append("Error {0}: {1})".format(response.status_code, workflow_name))
                            continue
                        with open(f"{self._workflows_folder_path}/{id}.zip", mode='wb') as zip_file:
                            zip_file.write(response.content)
                        file.write("{0}  {1}  {2}\n".format(*node_name, id, workflow_name))
                        time.sleep(0.05)
                        print("{0}){1}: {2}".format(count(), *node_name, workflow_name))
                    except OSError as err:
                        _logger.error(err)
                        self.issue_message(response.status_code, workflow_name)
                        continue
                    except Exception as err:
                        _logger.error(err)
                        self.issue_message(response.status_code, workflow_name)
                        continue
        list(map(lambda x: print(x), (failed_workflows)))
        return True

    def display_list_of_workflowsName_and_workflowsId(self, workflows: dict):
        """ Function to display workFlows on the screen and save that info to a file. """

        count = Tools.counter()
        for node in workflows:
            for id, name in workflows[node].items():
                time.sleep(0.01)
                print(f'   {count()}){node}: {id}  {name}')

    def delete_workflows(self, url, token, workflows: dict):
        """ Function to delete workFlows from a certain node, or all at once. """

        count = Tools.counter()
        headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}
        nodes_to_remove = [node for node in workflows if not workflows[node]]
        {workflows.__delitem__(node) for node in nodes_to_remove}
        for node in workflows:
            for id, name in workflows[node].items():
                url_delete_workflow = f"{url}/{self.__api_WorkFlows}/{id}"
                response = self.tools.make_request('DELETE', url_delete_workflow, headers=headers, verify=False, return_err_response=True)
                if response.status_code != 204:
                    _logger.error(response.text)
                    self.issue_message(response.status_code, name)
                print(f'   {count()}){node}: {name}')
        return True

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
  --type        Workflows type(Task, DocumentFlow, AcceptanceInspection, IncomingInspection, WorkPermit)
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
  --type        Workflows type(Task, DocumentFlow, AcceptanceInspection, IncomingInspection, WorkPermit)
"""
        remove_workflows: str = """usage: rm workflows [--help] [--draft] [--active] [--archived] [--all]

options:
  -h, --help    Show this help message
  --draft       Draft node of workflows
  --active      Active node of workflows
  --archived    Archived node of workflows
  --all         All three nodes
  --type        Workflows type(Task, DocumentFlow, AcceptanceInspection, IncomingInspection, WorkPermit)
"""

        if ls: print(ls_workflows)
        elif export: print(export_workflows)
        elif remove: print(remove_workflows)