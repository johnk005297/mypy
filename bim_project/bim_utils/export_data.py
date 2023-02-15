import os
import json
import requests
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
disable_warnings(InsecureRequestWarning)
import logging
import time
import app_menu
import auth
import license
from tools import File


class Export_data:

    __api_Integration_ObjectModel_Export:str       = 'api/Integration/ObjectModel/Export'
    __api_WorkFlowNodes:str                        = 'api/WorkFlowNodes'
    __api_WorkFlows:str                            = 'api/WorkFlows'
    __api_Attachments:str                          = 'api/Attachments'
    _transfer_folder:str                           = 'transfer_files'
    _workflows_folder:str                          = 'workflows'
    _object_model_folder:str                       = 'object_model'
    _all_workflow_nodes_file:str                   = 'all_workflow_nodes_export_server.json'
    _workflows_draft_file:str                      = 'Draft_workflows_export_server.json'
    _workflows_archived_file:str                   = 'Archived_workflows_export_server.json'
    _workflows_active_file:str                     = 'Active_workflows_export_server.json'
    _selected_workflow_nodes_file:str              = 'workflow_nodes_to_import.list'
    _workflowID_bimClassID_file:str                = 'workflowID_bimClassID_export_server.json'
    _object_model_file:str                         = 'object_model_export_server.json'
    _exported_workflows_list:str                   = 'exported_workflows.list'  # Save it just in case if need to find a particular file among workflows or smth.
    _export_server_info_file:str                   = 'export_server.info'  # Needs for separation import procedures on export server during one session.
    AppMenu                                        = app_menu.AppMenu()
    possible_request_errors                        = auth.Auth().possible_request_errors
    License                                        = license.License()

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
            request = requests.get(url_get_object_model, headers=headers, verify=False)
            response = request.json()
        except self.possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")
            print("Error: Couldn't export object model. Check the logs.")
            return False

        try:
            with open(f"{self._transfer_folder}/{self._object_model_folder}/{filename}", "w", encoding="utf-8") as json_file:
                json.dump(response, json_file, ensure_ascii=False, indent=4)
                logging.info(f"Object model has been exported. '{filename}' file is ready.")
                if filename != 'object_model_import_server.json':
                    print(f"\n   - object model exported in '{filename}' file.")
        except (FileNotFoundError, OSError) as err:
            logging.error(err)
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
            logging.error("select_workflow_nodes function error:\n", err)
            return

        # This self.current_workflow_node_selection will only go further through the process of export. Import procedure will use 'self._selected_workflow_nodes_file' file.
        self.current_workflow_node_selection:list = input("Choose nodes to export workflows from. Use whitespaces in-between to select more than one.  \
                                            \n(dr Draft, ar Archived, ac Active, q Quit): ").lower().split()

        # if user chose anything but ('dr', 'ar', 'ac'), func will return False, and no processes will go further
        if not [x for x in self.current_workflow_node_selection if x in ('dr', 'ar', 'ac')]:
            return False
        else:
            # In case if smth else with valid request was provided. Clean everything except 'dr', 'ar', 'ac'.
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
                elif node =='Active':
                    if self._workflows_active_file not in content:
                        file.write(f"{self._workflows_active_file}\n")
                else:
                    continue
        return True


    def get_all_workflow_nodes(self, filename, url, token):
        '''  Getting Draft, Archived and Active nodes from the server in .json file.  
             Function holds a dictionary with all the nodes in format: {"NodeName": "NodeId"}.
        '''

        url_get_all_workflow_nodes = url + '/' + self.__api_WorkFlowNodes
        headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}
        try:
            request = requests.get(url=url_get_all_workflow_nodes, headers=headers, verify=False)
            response = request.json()
        except self.possible_request_errors as err:
            logging.error(f"{err}\n{request.text}") 
            print(f"Error: Couldn't export workFlow nodes. Check the logs.")
            return False

        try:
            path = f'{self._transfer_folder}/{self._workflows_folder}/{filename}'
            with open(path, mode='w', encoding='utf-8') as json_file:
                json.dump(response, json_file, ensure_ascii=False, indent=4)

            # Creating a dictionary with all three nodes from the server in format: {"NodeName": "NodeId"}
            self.workflow_nodes:dict = {}
            for x in File.read_file(self._transfer_folder + '/' + self._workflows_folder, self._all_workflow_nodes_file):
                self.workflow_nodes[x['name']] = x['id']

        except OSError as err:
            logging.error(err)
            print('Error occured. Check the logs.')
            return False
        return True


    def get_workflows(self, url, token):
        ''' Get all workflows from the chosen node. '''

        for nodeName, nodeId in self.workflow_nodes.items():
            if nodeName not in self.current_workflow_node_selection:
                continue

            url_get_workflows = f"{url}/{self.__api_WorkFlowNodes}/{nodeId}/children"
            headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}
            try:
                request = requests.get(url_get_workflows, headers=headers, verify=False)
                response = request.json()
                time.sleep(0.1)
            except self.possible_request_errors as err:
                logging.error(f"{err}\n{request.text}")
                return False

            with open(f"{self._transfer_folder}/{self._workflows_folder}/{nodeName}_workflows_export_server.json", 'w', encoding='utf-8') as json_file:
                json.dump(response, json_file, ensure_ascii=False, indent=4)       
            logging.info(f"'{nodeName}_workflows_export_server.json' file is ready.")
        return True


    def display_list_of_workflowsName_and_workflowsId(self, url, token):
        ''' Function to display workFlows on the screen and save that info to a file. '''

        self.get_all_workflow_nodes(self._all_workflow_nodes_file, url, token) # getting list of nodes in self.workflow_nodes variable
        headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}

        draftNode_id, activeNode_id, archivedNode_id = self.workflow_nodes['Draft'], self.workflow_nodes['Active'], self.workflow_nodes['Archived']
        selected_node:list = list(map(str, input("Choose nodes to display workflows from. Use whitespaces in-between to select more than one.\ndr Draft, ac, Active, ar Archived, all: ").split()))
        selected_node = [x for x in selected_node if x in ('dr', 'ac', 'ar', 'all')] # drop anything except 0, 1, 2, 3 values from the selected node list

        # creating a file workFlows.list
        with open(f'{self._transfer_folder}/{self._workflows_folder}/workFlows.list', mode='a', encoding='utf-8') as file:
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
            print()
            count = 1 # count for workflows
            for id in selected_node:
                if id == draftNode_id:
                    node_name = 'Draft'
                elif id == activeNode_id:
                    node_name = 'Active'
                elif id == archivedNode_id:
                    node_name = 'Archived'

                url_get_workflows = f"{url}/{self.__api_WorkFlowNodes}/{id}/children"
                try:
                    request = requests.get(url_get_workflows, headers=headers, verify=False)
                    response = request.json()
                except self.possible_request_errors as err:
                    logging.error(f"{err}\n{request.text}")
                if not response['workFlows']:
                    print(f'No workflows in {node_name}')
                    continue
                for workflow in response['workFlows']:
                    result = f"{node_name}: {workflow['name']}  id: {workflow['id']}"
                    print(f'{count}){result}')
                    count+=1
                    file.write(result + '\n')


    def delete_workflows(self, url, token):
        ''' Function to delete workFlows from a certain node, or all at once. '''

        ### Function isn't finished yet ###
        self.get_all_workflow_nodes(self._all_workflow_nodes_file, url, token) # getting list of nodes in self.workflow_nodes variable
        headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}

        draftNode_id, activeNode_id, archivedNode_id = self.workflow_nodes['Draft'], self.workflow_nodes['Active'], self.workflow_nodes['Archived']
        selected_node:list = list(map(str, input("Choose nodes to delete workflows from. Use whitespaces in-between to select more than one.\ndr Draft, ac, Active, ar Archived, all: ").split()))
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
                request = requests.get(url_get_workflows, headers=headers, verify=False)
                response = request.json()
            except self.possible_request_errors as err:
                logging.error(f"{err}\n{request.text}")

            if not response['workFlows']:
                print(f'No workflows in {node_name}')
                continue
            for workflow in response['workFlows']:
                workflows_to_delete.append([node_name, workflow['name'], workflow['id']])
        print()
        for number, workflow in enumerate(workflows_to_delete, 1):
            try:
                url_delete_workflow = f"{url}/{self.__api_WorkFlows}/{workflow[2]}"
                request = requests.delete(url_delete_workflow, headers=headers, verify=False)
                logging.info(f'Deleted workflow: {workflow[0]}: {workflow[2]}')
                print(f'{number}) {workflow[0]}: {workflow[1]}')
            except self.possible_request_errors as err:
                logging.error(f"{err}\n{request.text}")
        workflows_to_delete.clear()


    def get_workflow_xml(self, url, token):
        ''' XML for every workflow will be exported from the current_workflow_node_selection list. '''

        # Transforming nodes variable into a list with workflows*.json filenames.
        headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}
        nodes = ' '.join(self.current_workflow_node_selection).replace('Draft', self._workflows_draft_file).replace('Archived', self._workflows_archived_file).replace('Active', self._workflows_active_file).split()
        for node in nodes:
            workflow_data = File.read_file(self._transfer_folder + '/' + self._workflows_folder, node)
            for line in workflow_data['workFlows']:
                url_get_workflow_xml_export = f"{url}/{self.__api_Attachments}/{line['attachmentId']}"
                request = requests.get(url_get_workflow_xml_export, headers=headers, verify=False)                
                with open(f"{self._transfer_folder}/{self._workflows_folder}/{line['originalId']}.xml", 'wb') as file:
                    file.write(request.content)
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

            for line in workflow_data['workFlows']:
                print(f"     {line['name']}")   # display the name of the process in the output
                url_get_workFlowId_and_bimClassId = f"{url}/{self.__api_WorkFlows}/{line['originalId']}/BimClasses"
                request = requests.get(url_get_workFlowId_and_bimClassId, headers=headers, verify=False)
                response = request.json()

                with open(f"{self._transfer_folder}/{self._workflows_folder}/{line['id']}.json", 'w', encoding='utf-8') as file:
                    json.dump(response, file, ensure_ascii=False, indent=4)

                # write list with active workFlows BimClasses ID in format [workFlow_id, bimClass_id]
                workFlow_id_bimClass_id_export.append(line['originalId'])
                workFlow_id_bimClass_id_export.append(response[0]['id'])

                # saving processes name with corresponding Id
                with open(f"{self._transfer_folder}/{self._workflows_folder}/{self._exported_workflows_list}", 'a', encoding='utf-8') as file:
                    file.write(f"{line['name']}\n{line['originalId']}\n\n")

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
            
        logging.info("Mapping between workflow_ID and bimClass_ID: done. 'workFlow_id_bimClass_id_export.json' file is ready.")
        return True


    def export_server_info(self, url, token):
        serverId:str = self.License.get_serverID(url, token)
        with open(f'{self._transfer_folder}/{self._export_server_info_file}', 'w', encoding='utf-8') as file:
            file.write("{0}\n".format(url.split('//')[1]))
            file.write(serverId)


    def export_workflows(self, url, token):
        self.get_all_workflow_nodes(self._all_workflow_nodes_file, url, token)
        if self.select_workflow_nodes():
            self.get_workflows(url, token)
            self.get_workflow_xml(url, token)
            self.get_workFlowId_and_bimClassId(url, token)
            return True
        else:
            return False