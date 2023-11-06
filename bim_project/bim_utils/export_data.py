import os
import json
import requests
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
disable_warnings(InsecureRequestWarning)
import time
import app_menu
import auth
import license
from tools import File
from tools import Tools
from log import Logs



class Export_data:

    __api_Integration_ObjectModel_Export:str       = 'api/Integration/ObjectModel/Export'
    __api_WorkFlowNodes:str                        = 'api/WorkFlowNodes'
    __api_WorkFlows:str                            = 'api/WorkFlows'
    __api_Attachments:str                          = 'api/Attachments'
    _transfer_folder:str                           = 'transfer_files'
    _workflows_folder:str                          = 'workflows'
    _workflows_folder_path:str                     = f'{_transfer_folder}/{_workflows_folder}'
    _object_model_folder:str                       = 'object_model'
    _all_workflow_nodes_file:str                   = 'all_workflow_nodes_export_server.json'
    _workflows_draft_file:str                      = 'Draft_workflows_export_server.json'
    _workflows_archived_file:str                   = 'Archived_workflows_export_server.json'
    _workflows_active_file:str                     = 'Active_workflows_export_server.json'
    _selected_workflow_nodes_file:str              = 'workflow_nodes_to_import.list'
    _workflowID_bimClassID_file:str                = 'workflowID_bimClassID_export_server.json'
    _object_model_file:str                         = 'object_model_export_server.json'
    _exported_workflows_list:str                   = 'exported_workflows.list'
    _export_server_info_file:str                   = 'export_server.info'  # Needs for separation import procedures on export server during one session.
    AppMenu                                        = app_menu.AppMenu()
    possible_request_errors                        = auth.Auth().possible_request_errors
    License                                        = license.License()
    __logger                                       = Logs().f_logger(__name__)
    # __start_connection                             = Logs().http_connect()
    # __check_response                               = Logs().http_response()


    def __init__(self):
        self.is_first_launch_export_data:bool = True


    def get_object_model(self, filename, url, token):    
        '''   Function gets object model from the server, and writes it into a file.   '''

        path_to_file = f'{self._transfer_folder}/{self._object_model_folder}/{filename}'
        if os.path.isfile(path_to_file):
            confirm_to_delete = input(f'There is an {filename} file already. Do you want to overwrite it?(y/n): ').lower()
            if confirm_to_delete == 'y':
                os.remove(path_to_file)
            else: return

        headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}
        url_get_object_model:str = url + '/' + self.__api_Integration_ObjectModel_Export
        try:
            response = requests.get(url_get_object_model, headers=headers, verify=False)
            # self.__logger.debug(self.__check_response(url, response.request.method, response.request.path_url, response.status_code))
            data = response.json()
        except self.possible_request_errors as err:
            self.__logger.error(f"{err}\n{response.text}")
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
            print('Erorr occured. Check the logs.')
            return False
        return True


    def select_workflow_nodes(self):
        '''   Function creates a file 'chosen_by_user_workflow_nodes_export' with chosen workflow nodes in it.   '''

        try:
            file_path = self._transfer_folder + '/' + self._workflows_folder + '/' + self._selected_workflow_nodes_file
            if not os.path.isfile(file_path):
                with open(file_path, mode='w', encoding='utf-8'): pass
        except OSError as err:
            print(f"Error occured. Check the logs.")
            self.__logger.error("select_workflow_nodes function error:\n", err)
            return

        # This self.current_workflow_node_selection will only go further through the process of export. Import procedure will use 'self._selected_workflow_nodes_file' file.
        self.current_workflow_node_selection:list = input("Choose nodes to export workflows from. Use whitespaces in-between to select more than one.  \
                                            \n(dr Draft, ar Archived, ac Active, q Quit): ").lower().split()

        # if user chose anything but ('dr', 'ar', 'ac'), func will return False, and no processes will go further
        if not [x for x in self.current_workflow_node_selection if x in ('dr', 'ar', 'ac')]:
            return False
        else:
            # In case if smth else with valid request was provided. Clean everything except 'dr', 'ar', 'ac', 'all'.
            self.current_workflow_node_selection:list = [x for x in self.current_workflow_node_selection if x in ('dr', 'ar', 'ac')]

        # Replacing user input with full names: Draft, Archived, Active
        self.current_workflow_node_selection = ' '.join(self.current_workflow_node_selection).replace('dr', 'Draft').replace('ar', 'Archived').replace('ac', 'Active').split()

        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        with open(file_path, 'a', encoding='utf-8') as file:
            for node in self.current_workflow_node_selection:                
                if node == 'Draft':
                    if self._workflows_draft_file not in content:
                        file.write(f"{self._workflows_draft_file}\n")
                elif node == 'Archived':
                    if self._workflows_archived_file not in content:
                        file.write(f"{self._workflows_archived_file}\n")
                elif node == 'Active':
                    if self._workflows_active_file not in content:
                        file.write(f"{self._workflows_active_file}\n")
                else:
                    continue
        return True


    def get_workflow_nodes_id(self, url, token):
        ''' Function returns a dictionary with all the nodes in format: {"NodeName": "NodeId"}. '''

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
        workflow_nodes:dict = {obj['name']: obj['id'] for obj in data}

        return workflow_nodes


    def get_workflows(self, url, token):
            ''' Get all workflows from the chosen node. '''

            workflow_nodes = self.get_workflow_nodes_id(url, token)
            for nodeName, nodeId in workflow_nodes.items():
                if nodeName not in self.current_workflow_node_selection:
                    continue

                url_get_workflows = f"{url}/{self.__api_WorkFlowNodes}/{nodeId}/children"
                headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}
                try:
                    # self.__logger.info(self.__start_connection(url))
                    response = requests.get(url_get_workflows, headers=headers, verify=False)
                    data = response.json()
                    time.sleep(0.1)
                except self.possible_request_errors as err:
                    self.__logger.error(f"{err}\n{response.text}")
                    return False

                with open(f"{self._workflows_folder_path}/{nodeName}_workflows_export_server.json", 'w', encoding='utf-8') as json_file:
                    json.dump(data, json_file, ensure_ascii=False, indent=4)       
                self.__logger.info(f"'{nodeName}_workflows_export_server.json' file is ready.")
            return True


    def save_workflows_at_once(self, url, token):
        '''  
            Function to export workflows at once.
            api/Integration/WorkFlow/{workflow_id}/Export method's response needs to be saved as a zip file for each process.
        '''

        count = Tools.counter()
        headers = {'accept': '*/*', 'Authorization': f"Bearer {token}"}

        for nodeName in self.current_workflow_node_selection:
            workflow_data = File.read_file(f'{self._workflows_folder_path}', f'{nodeName}_workflows_export_server.json')
            for workflow in workflow_data['workFlows']:
                try:
                    url_export = f"{url}/api/Integration/WorkFlow/{workflow['id']}/Export"
                    response = requests.get(url=url_export, headers=headers, verify=False)
                except self.possible_request_errors as err:
                    self.__logger.error(f"{err}\n{response.text}")
                print(f"   {count()}){nodeName}: {workflow['name']}")   # display the name of the process in the output
                time.sleep(0.1)
                try:
                    with open(f"{self._workflows_folder_path}/{workflow['id']}.zip", mode='wb') as zip_file, \
                         open(f"{self._workflows_folder_path}/{self._exported_workflows_list}", mode='a', encoding='utf-8') as wf_id_name:
                         zip_file.write(response.content)
                         wf_id_name.write("{0}  {1}\n".format(workflow['id'], workflow['name']))
                except OSError as err:
                    self.__logger.error(err)
                    continue

        return True


    def save_workflows_by_choice(self, url, token, *args):
        ''' Function to export only specified workflows. '''

        headers = {'accept': '*/*', 'Authorization': f"Bearer {token}"}
        nodes:dict = self.get_workflow_nodes_id(url, token)
        for id in args:
            issue_message = lambda wf_id: print("Error: WorkFlow [{0}] wasn't exported. Check the logs.".format(wf_id))
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
                    print(f"NotFoundDataException. WorkFlow: [{id}] wasn't found. Check the logs.")
                continue
            else:
                url_export = f"{url}/api/Integration/WorkFlow/{id}/Export"
                try:
                    response = requests.get(url=url_export, headers=headers, verify=False)
                    with open(f"{self._workflows_folder_path}/{id}.zip", mode='wb') as zip_file, \
                         open(f"{self._workflows_folder_path}/{self._exported_workflows_list}", mode='a', encoding='utf-8') as wf_id_name:
                         zip_file.write(response.content)
                         wf_id_name.write("{0}  {1}\n".format(id, workflow_name))
                    time.sleep(0.1)
                    node_name:set = {key for key in nodes if nodes[key] == node_id}
                    print("{0}: {1} successfully saved.".format(*node_name, workflow_name))
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


    def get_workflow_xml(self, url, token):
        ''' XML for every workflow will be exported from the current_workflow_node_selection list. '''

        # Transforming nodes variable into a list with workflows*.json filenames.
        headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}
        nodes = ' '.join(self.current_workflow_node_selection).replace('Draft', self._workflows_draft_file).replace('Archived', self._workflows_archived_file).replace('Active', self._workflows_active_file).split()
        for node in nodes:
            workflow_data = File.read_file(self._transfer_folder + '/' + self._workflows_folder, node)
            for line in workflow_data['workFlows']:
                url_get_workflow_xml_export = f"{url}/{self.__api_Attachments}/{line['attachmentId']}"
                response = requests.get(url_get_workflow_xml_export, headers=headers, verify=False)
                # self.__logger.debug(self.__check_response(url, response.request.method, response.request.path_url, response.status_code))
                with open(f"{self._transfer_folder}/{self._workflows_folder}/{line['originalId']}.xml", 'wb') as file:
                    file.write(response.content)
                time.sleep(0.15)
        return


    def get_workFlowId_and_bimClassId(self, url, token):
        '''
            This function does mapping between workFlow_id and bimClass_id. 
            It uses list comprehension block for transformation list of objects into dictionary with {'workFlow_id': 'bimClass_id'} pairs.
        '''
        headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}

        workFlow_id_bimClass_id_export: list = []  # temp list to store data
        if not os.path.isfile(f"{self._transfer_folder}/{self._workflows_folder}/{self._exported_workflows_list}"):
            with open(f"{self._transfer_folder}/{self._workflows_folder}/{self._exported_workflows_list}", 'w', encoding='utf-8') as file:
                file.write('Workflows: name and Id\n---------------------------------\n')

        nodes = ' '.join(self.current_workflow_node_selection).replace('Draft', self._workflows_draft_file).replace('Archived', self._workflows_archived_file).replace('Active', self._workflows_active_file).split()
        for node in nodes:
            workflow_data = File.read_file(f"{self._transfer_folder}/{self._workflows_folder}", node)
            if len(workflow_data['workFlows']) == 0:
                print(f"   - No {node[:-19]}")
                continue

            for workflow in workflow_data['workFlows']:
                print(f"     {workflow['name']}")   # display the name of the process in the output
                url_get_workFlowId_and_bimClassId = f"{url}/{self.__api_WorkFlows}/{workflow['originalId']}/BimClasses"
                response = requests.get(url_get_workFlowId_and_bimClassId, headers=headers, verify=False)
                # self.__logger.debug(self.__check_response(url, response.request.method, response.request.path_url, response.status_code))
                data = response.json()

                with open(f"{self._transfer_folder}/{self._workflows_folder}/{workflow['originalId']}.json", 'w', encoding='utf-8') as file:
                    json.dump(data, file, ensure_ascii=False, indent=4)

                # write list with active workFlows BimClasses ID in format [workFlow_id, bimClass_id]
                workFlow_id_bimClass_id_export.append(workflow['originalId'])
                workFlow_id_bimClass_id_export.append(data[0]['originalId'])

                # saving processes name with corresponding Id
                with open(f"{self._transfer_folder}/{self._workflows_folder}/{self._exported_workflows_list}", 'a', encoding='utf-8') as file:
                    file.write(f"{workflow['name']}\n{workflow['originalId']}\n\n")

        # List comprehension block for transformation list of values into {'workFlow_id': 'bimClass_id'} pairs.
        tmp = workFlow_id_bimClass_id_export
        tmp:list = [ [tmp[x-1]] + [tmp[x]] for x in range(1, len(tmp), 2) ]       # generation list in format [ ['a', 'b'], ['c', 'd'], ['e', 'f'] ]

        workFlow_id_bimClass_id_export = dict(tmp)                                # transform tmp list from above to dictionary using dict() function in format {"workFlow_id": "bimClass_id"}
        
        if not os.path.isfile(f"{self._transfer_folder}/{self._workflows_folder}/{self._workflowID_bimClassID_file}"):
            with open(f"{self._transfer_folder}/{self._workflows_folder}/{self._workflowID_bimClassID_file}", 'w', encoding='utf-8') as file:
                json.dump(workFlow_id_bimClass_id_export, file, ensure_ascii=False, indent=4)
        else:
            if workFlow_id_bimClass_id_export:  # if tmp list is True(not empty), append.
                with open(f"{self._transfer_folder}/{self._workflows_folder}/{self._workflowID_bimClassID_file}", 'a', encoding='utf-8') as file:
                    json.dump(workFlow_id_bimClass_id_export, file, ensure_ascii=False, indent=4)
            
        self.__logger.info("Mapping between workflow_ID and bimClass_ID: done. 'workFlow_id_bimClass_id_export.json' file is ready.")
        return True


    def display_list_of_workflowsName_and_workflowsId(self, url, token):
        ''' Function to display workFlows on the screen and save that info to a file. '''

        headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}

        workflow_nodes = self.get_workflow_nodes_id(url, token)
        draftNode_id, activeNode_id, archivedNode_id = workflow_nodes['Draft'], workflow_nodes['Active'], workflow_nodes['Archived']
        selected_node:list = list(map(str, input("Choose nodes to display workflows from. Use whitespaces in-between to select more than one.\ndr Draft, ac, Active, ar Archived, all: ").strip().lower().split()))
        selected_node = [x for x in selected_node if x in ('dr', 'ac', 'ar', 'all')] # drop anything except 0, 1, 2, 3 values from the selected node list

        # creating a file workFlows.list
        count = Tools.counter()
        with open(f'{self._workflows_folder_path}/workFlows.list', mode='a', encoding='utf-8') as file:
            # replacing selected values with correspondent id's in selected node list
            for x in range(len(selected_node)):
                if selected_node[x] == 'dr':
                    selected_node[x] = draftNode_id
                elif selected_node[x] == 'ac':
                    selected_node[x] = activeNode_id
                elif selected_node[x] == 'ar':
                    selected_node[x] = archivedNode_id
                else:
                    selected_node = [draftNode_id, activeNode_id, archivedNode_id]
                    break
            if selected_node:
                print()
            for id in selected_node:
                if id == draftNode_id:
                    node_name = 'Draft'
                elif id == activeNode_id:
                    node_name = 'Active'
                elif id == archivedNode_id:
                    node_name = 'Archived'

                url_get_workflows = f"{url}/{self.__api_WorkFlowNodes}/{id}/children"
                try:
                    response = requests.get(url_get_workflows, headers=headers, verify=False)
                    # self.__logger.debug(self.__check_response(url, response.request.method, response.request.path_url, response.status_code))
                    data = response.json()
                except self.possible_request_errors as err:
                    self.__logger.error(f"{err}\n{response.text}")
                if not data['workFlows']:
                    print(f'   No workflows in {node_name}')
                    continue
                for workflow in data['workFlows']:
                    # result = f"{node_name}: {workflow['name']}  id: {workflow['id']}"
                    result = f"{node_name}: {workflow['id']}  {workflow['name']}"
                    time.sleep(0.05)
                    print(f'   {count()}){result}')
                    file.write(result + '\n')


    def delete_workflows(self, url, token):
        ''' Function to delete workFlows from a certain node, or all at once. '''

        workflow_nodes = self.get_workflow_nodes_id(url, token) # getting list of nodes in self.workflow_nodes variable
        headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}

        draftNode_id, activeNode_id, archivedNode_id = workflow_nodes['Draft'], workflow_nodes['Active'], workflow_nodes['Archived']
        selected_node = list(map(str, input("Choose nodes to delete workflows from. Use whitespaces in-between to select more than one.\ndr Draft, ac, Active, ar Archived, all: ").strip().lower().split()))
        selected_node = [x for x in selected_node if x in ('dr', 'ac', 'ar', 'all')] # drop anything except 0, 1, 2, 3 values from the selected node list

        # replacing selected values with correspondent id's in selected node list
        for x in range(len(selected_node)):
            if selected_node[x] == 'dr':
                selected_node[x] = draftNode_id
            elif selected_node[x] == 'ac':
                selected_node[x] = activeNode_id
            elif selected_node[x] == 'ar':
                selected_node[x] = archivedNode_id
            else:
                selected_node = [draftNode_id, activeNode_id, archivedNode_id]
                break
        if selected_node:
            print()
        workflows_to_delete:list = []
        for id in selected_node:
            if id == draftNode_id:
                node_name = 'Draft'
            elif id == activeNode_id:
                node_name = 'Active'
            elif id == archivedNode_id:
                node_name = 'Archived'

            url_get_workflows = f"{url}/{self.__api_WorkFlowNodes}/{id}/children"
            try:
                response = requests.get(url_get_workflows, headers=headers, verify=False)
                data = response.json()
            except self.possible_request_errors as err:
                self.__logger.error(f"{err}\n{response.text}")

            if not data['workFlows']:
                print(f'No workflows in {node_name}')
                continue
            for workflow in data['workFlows']:
                workflows_to_delete.append([node_name, workflow['name'], workflow['id']])

        for number, workflow in enumerate(workflows_to_delete, 1):

            try:
                url_delete_workflow = f"{url}/{self.__api_WorkFlows}/{workflow[2]}"
                response = requests.delete(url_delete_workflow, headers=headers, verify=False)
                # self.__logger.debug(self.__check_response(url, response.request.method, response.request.path_url, response.status_code))
                if response.status_code != 204:
                    print(f"Error: {workflow[0]} wasn't removed. Status code: {response.status_code}. Check the log.")
                    self.__logger.error(f"{workflow[0]}: {response.status_code}\n{response.text}")
                # self.__logger.info(f'{workflow[0]}: "{workflow[1]}"')
                print(f'{number}) {workflow[0]}: {workflow[1]}')
            except self.possible_request_errors as err:
                self.__logger.error(f"{err}\n{response.text}")

        workflows_to_delete.clear()
        return True


    def export_server_info(self, url, token):
        serverId:str = self.License.get_serverID(url, token)
        with open(f'{self._transfer_folder}/{self._export_server_info_file}', 'w', encoding='utf-8') as file:
            file.write("{0}\n".format(url.split('//')[1]))
            file.write(serverId)


    def export_workflows(self, url, token, *args, at_once=True):
        if not at_once:
            self.save_workflows_by_choice(url, token, *args)
            return True
        if self.select_workflow_nodes():
            self.get_workflows(url, token)
            self.save_workflows_at_once(url, token)

            ### Need to disable this block to test another API method for transferring process ###
            # self.get_workflow_xml(url, token)
            # self.get_workFlowId_and_bimClassId(url, token)
            return True
        else:
            return False