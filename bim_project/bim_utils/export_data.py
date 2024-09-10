import os
import json
import requests
import time
import app_menu
import auth
import license
from urllib3.exceptions import InsecureRequestWarning
from tools import File, Tools, Folder

from log import Logs
from urllib3 import disable_warnings
disable_warnings(InsecureRequestWarning)




class Export_data:

    __api_Integration_ObjectModel_Export: str = 'api/Integration/ObjectModel/Export'
    __api_WorkFlowNodes: str = 'api/WorkFlowNodes'
    __api_WorkFlows: str = 'api/WorkFlows'
    __api_Attachments: str = 'api/Attachments'
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
    __logger = Logs().f_logger(__name__)

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
                self.__logger.error(f"{self.get_object_model.__name__}\n{response.text}")
            # self.__logger.debug(self.__check_response(
            # url, response.request.method, response.request.path_url, response.status_code))
            data = response.json()
        except self.possible_request_errors as err:
            self.__logger.error(f"{err}")
            print("Error: Couldn't export object model. Check the logs.")
            return False

        try:
            with open(f"{self._transfer_folder}/{self._object_model_folder}/{filename}", "w", encoding="utf-8") as json_file:
                json.dump(data, json_file, ensure_ascii=False, indent=4)
                self.__logger.info(f"Object model has been exported. '{filename}' file is ready.")
                if filename != 'object_model_import_server.json':
                    print(f"\n   - object model exported in '{filename}' file.")
        except (FileNotFoundError, OSError) as err:
            self.__logger.error(err)
            print('Error occurred. Check the logs.')
            return False
        return True

    def get_workflow_nodes_id(self, url, token):
        """ Function returns a dictionary with all the nodes in format: {"NodeName": "NodeId"}. """

        url_get_all_workflow_nodes = url + '/' + self.__api_WorkFlowNodes
        headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}
        try:
            # self.__start_connection(url)
            response = requests.get(url=url_get_all_workflow_nodes, headers=headers, verify=False)
            data = response.json()
        except self.possible_request_errors as err:
            self.__logger.error(f"{err}\n{response.text}") 
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
                        self.__logger.error(f"{err}\n{response.text}")
                    print(f"   {count()}){node}: {name}")   # display the name of the process in the output
                    time.sleep(0.1)
                    try:
                        with open(f"{self._workflows_folder_path}/{id}.zip", mode='wb') as zip_file:
                            zip_file.write(response.content)
                        file.write("{0}  {1}  {2}\n".format(node, id, name))
                    except OSError as err:
                        self.__logger.error(err)
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
                    self.__logger.error(f"{err} {response.status_code}\n{response.text}")
                    issue_message(id)
                    continue
                except Exception as err:
                    self.__logger.error(f"{err} {response.status_code}\n{data}")
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
                        self.__logger.error(f"{err} {response.status_code}\n{response.text}")
                        issue_message(workflow_name)
                        continue
                    except OSError as err:
                        self.__logger.error(err)
                        issue_message(workflow_name)
                        continue
                    except Exception as err:
                        self.__logger.error(err)
                        issue_message(workflow_name)
                        continue
        return True

    def define_needed_workflows(self, url, token, *args, **kwargs):
        """ Define a dictionary with needed workflows. """

        headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}
        workflows: dict = {'Draft': {}, 'Active': {}, 'Archived': {}}
        workflow_nodes = self.get_workflow_nodes_id(url, token)
        if len(args) < 1:
            print("At least one of the arguments must be provided: --draft, --active, --archived, --all")
            return
        if kwargs['startswith'] and kwargs['search_for']:
            print("Can't use both arguments '--startswith' and '--search' together")
            return
        selected_nodes = [x for x in args[0] if x in ('--draft', '--active', '--archived', '--all')] # drop anything except 0, 1, 2, 3 values from the selected node list
        if '--all' not in selected_nodes:
            nodes_to_remove = [node for node in workflow_nodes.keys() if ''.join(('--', node)).lower() not in selected_nodes and len(selected_nodes) > 0]
            {workflow_nodes.__delitem__(node) for node in nodes_to_remove}
        if not selected_nodes:
            print("At least one of the arguments of the node must be provided: --draft, --active, --archived, --all")
            return False
        for name, id in workflow_nodes.items():
                url_get_workflows = f"{url}/{self.__api_WorkFlowNodes}/{id}/children"
                try:
                    response = requests.get(url_get_workflows, headers=headers, verify=False)
                    data = response.json()
                except self.possible_request_errors as err:
                    self.__logger.error(f"{err}\n{response.text}")
                for workflow in data['workFlows']:
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
                        self.__logger.error(f"{id}: {response.status_code}\n{response.text}")
                    print(f'   {count()}){node}: {name}')
                except self.possible_request_errors as err:
                    self.__logger.error(f"{err}\n{response.text}")
        return True    

    def export_server_info(self, url, token):
        serverId:str = self.License.get_serverID(url, token)
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



#####  RUDIMENTARY SUBROUTINES  #####
    # def get_workflow_xml(self, url, token):
    #     """ XML for every workflow will be exported from the current_workflow_node_selection list. """

    #     # Transforming nodes variable into a list with workflows*.json filenames.
    #     headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}
    #     nodes = ' '.join(self.current_workflow_node_selection).replace('Draft', self._workflows_draft_file).replace('Archived', self._workflows_archived_file).replace('Active', self._workflows_active_file).split()
    #     for node in nodes:
    #         workflow_data = File.read_file(self._transfer_folder + '/' + self._workflows_folder, node)
    #         for line in workflow_data['workFlows']:
    #             url_get_workflow_xml_export = f"{url}/{self.__api_Attachments}/{line['attachmentId']}"
    #             response = requests.get(url_get_workflow_xml_export, headers=headers, verify=False)
    #             with open(f"{self._transfer_folder}/{self._workflows_folder}/{line['originalId']}.xml", 'wb') as file:
    #                 file.write(response.content)
    #             time.sleep(0.15)
    #     return

    # def get_workFlowId_and_bimClassId(self, url, token): ## Function currently is not un use.
    #     """
    #         This function does mapping between workFlow_id and bimClass_id. 
    #         It uses list comprehension block for transformation list of objects into dictionary with {'workFlow_id': 'bimClass_id'} pairs.

    #     """
    #     headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}

    #     workFlow_id_bimClass_id_export: list = []  # temp list to store data
    #     if not os.path.isfile(f"{self._transfer_folder}/{self._workflows_folder}/{self._exported_workflows_list}"):
    #         with open(f"{self._transfer_folder}/{self._workflows_folder}/{self._exported_workflows_list}", 'w', encoding='utf-8') as file:
    #             file.write('Workflows: name and Id\n---------------------------------\n')

    #     nodes = ' '.join(self.current_workflow_node_selection).replace('Draft', self._workflows_draft_file).replace('Archived', self._workflows_archived_file).replace('Active', self._workflows_active_file).split()
    #     for node in nodes:
    #         workflow_data = File.read_file(f"{self._transfer_folder}/{self._workflows_folder}", node)
    #         if len(workflow_data['workFlows']) == 0:
    #             print(f"   - No {node[:-19]}")
    #             continue

    #         for workflow in workflow_data['workFlows']:
    #             print(f"     {workflow['name']}")   # display the name of the process in the output
    #             url_get_workFlowId_and_bimClassId = f"{url}/{self.__api_WorkFlows}/{workflow['originalId']}/BimClasses"
    #             response = requests.get(url_get_workFlowId_and_bimClassId, headers=headers, verify=False)
    #             # self.__logger.debug(self.__check_response(url, response.request.method, response.request.path_url, response.status_code))
    #             data = response.json()

    #             with open(f"{self._transfer_folder}/{self._workflows_folder}/{workflow['originalId']}.json", 'w', encoding='utf-8') as file:
    #                 json.dump(data, file, ensure_ascii=False, indent=4)

    #             # write list with active workFlows BimClasses ID in format [workFlow_id, bimClass_id]
    #             workFlow_id_bimClass_id_export.append(workflow['originalId'])
    #             workFlow_id_bimClass_id_export.append(data[0]['originalId'])

    #             # saving processes name with corresponding Id
    #             with open(f"{self._transfer_folder}/{self._workflows_folder}/{self._exported_workflows_list}", 'a', encoding='utf-8') as file:
    #                 file.write(f"{workflow['name']}\n{workflow['originalId']}\n\n")

    #     # List comprehension block for transformation list of values into {'workFlow_id': 'bimClass_id'} pairs.
    #     tmp = workFlow_id_bimClass_id_export
    #     tmp:list = [ [tmp[x-1]] + [tmp[x]] for x in range(1, len(tmp), 2) ]       # generation list in format [ ['a', 'b'], ['c', 'd'], ['e', 'f'] ]

    #     workFlow_id_bimClass_id_export = dict(tmp)                                # transform tmp list from above to dictionary using dict() function in format {"workFlow_id": "bimClass_id"}
        
    #     if not os.path.isfile(f"{self._transfer_folder}/{self._workflows_folder}/{self._workflowID_bimClassID_file}"):
    #         with open(f"{self._transfer_folder}/{self._workflows_folder}/{self._workflowID_bimClassID_file}", 'w', encoding='utf-8') as file:
    #             json.dump(workFlow_id_bimClass_id_export, file, ensure_ascii=False, indent=4)
    #     else:
    #         if workFlow_id_bimClass_id_export:  # if tmp list is True(not empty), append.
    #             with open(f"{self._transfer_folder}/{self._workflows_folder}/{self._workflowID_bimClassID_file}", 'a', encoding='utf-8') as file:
    #                 json.dump(workFlow_id_bimClass_id_export, file, ensure_ascii=False, indent=4)
            
    #     self.__logger.info("Mapping between workflow_ID and bimClass_ID: done. 'workFlow_id_bimClass_id_export.json' file is ready.")
    #     return True

        # def get_workflows(self, url, token):
    #         """ Get all workflows from the chosen node. """

    #         workflow_nodes = self.get_workflow_nodes_id(url, token)
    #         for nodeName, nodeId in workflow_nodes.items():
    #             if nodeName not in self.current_workflow_node_selection:
    #                 continue

    #             url_get_workflows = f"{url}/{self.__api_WorkFlowNodes}/{nodeId}/children"
    #             headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}
    #             try:
    #                 response = requests.get(url_get_workflows, headers=headers, verify=False)
    #                 data = response.json()
    #                 time.sleep(0.1)
    #             except self.possible_request_errors as err:
    #                 self.__logger.error(f"{err}\n{response.text}")
    #                 return False

    #             with open(f"{self._workflows_folder_path}/{nodeName}_workflows_export_server.json", 'w', encoding='utf-8') as json_file:
    #                 json.dump(data, json_file, ensure_ascii=False, indent=4)       
    #             self.__logger.info(f"'{nodeName}_workflows_export_server.json' file is ready.")
    #         return True

    # def select_workflow_nodes(self):
    #     """   Function creates a file 'chosen_by_user_workflow_nodes_export' with chosen workflow nodes in it.   """

    #     try:
    #         file_path = self._transfer_folder + '/' + self._workflows_folder + '/' + self._selected_workflow_nodes_file
    #         if not os.path.isfile(file_path):
    #             with open(file_path, mode='w', encoding='utf-8'): pass
    #     except OSError as err:
    #         print(f"Error occured. Check the logs.")
    #         self.__logger.error("select_workflow_nodes function error:\n", err)
    #         return

    #     # This self.current_workflow_node_selection will only go further through the process of export. Import procedure will use 'self._selected_workflow_nodes_file' file.
    #     self.current_workflow_node_selection: list = input("Choose nodes to export workflows from. Use whitespaces in-between to select more than one.  \
    #                                         \n(dr Draft, ar Archived, ac Active, q Quit): ").lower().split()

    #     # if user chose anything but ('dr', 'ar', 'ac'), func will return False, and no processes will go further
    #     if not [x for x in self.current_workflow_node_selection if x in ('dr', 'ar', 'ac')]:
    #         return False
    #     else:
    #         # In case if smth else with valid request was provided. Clean everything except 'dr', 'ar', 'ac', 'all'.
    #         self.current_workflow_node_selection: list = [x for x in self.current_workflow_node_selection if x in ('dr', 'ar', 'ac')]

    #     # Replacing user input with full names: Draft, Archived, Active
    #     self.current_workflow_node_selection = ' '.join(self.current_workflow_node_selection).replace('dr', 'Draft').replace('ar', 'Archived').replace('ac', 'Active').split()

    #     with open(file_path, 'r', encoding='utf-8') as file:
    #         content = file.read()
    #     with open(file_path, 'a', encoding='utf-8') as file:
    #         for node in self.current_workflow_node_selection:                
    #             if node == 'Draft':
    #                 if self._workflows_draft_file not in content:
    #                     file.write(f"{self._workflows_draft_file}\n")
    #             elif node == 'Archived':
    #                 if self._workflows_archived_file not in content:
    #                     file.write(f"{self._workflows_archived_file}\n")
    #             elif node == 'Active':
    #                 if self._workflows_active_file not in content:
    #                     file.write(f"{self._workflows_active_file}\n")
    #             else:
    #                 continue
    #     return True    