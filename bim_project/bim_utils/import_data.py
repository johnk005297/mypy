import os
import json
import requests
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
disable_warnings(InsecureRequestWarning)
import logging
import time
import shutil
import export_data
from tools import File
import auth
import license

class Import_data:

    __api_WorkFlows:str                        = 'api/WorkFlows'
    __api_Integration_ObjectModel_Import:str   = 'api/Integration/ObjectModel/Import'
    __transfer_folder:str                      = 'transfer_files'
    __workflows_folder:str                     = 'workflows'
    __all_workflow_nodes_file:str              = 'all_workflow_nodes_import_server.json'
    __object_model_folder:str                  = 'object_model'
    __object_model_file:str                    = 'object_model_import_server.json'
    __modified_object_model_file:str           = 'modified_object_model.json'
    Export_data                                = export_data.Export_data()
    License                                    = license.License()
    possible_request_errors                    = auth.Auth().possible_request_errors


    def __init__(self):
        self.export_serverId = None


    def validate_import_server(self, url, token):
        ''' Function needs to protect export server from import procedure during a single user session. '''

        check_server_info = File.read_file(self.__transfer_folder, self.Export_data._export_server_info_file)
        if check_server_info and check_server_info.split()[1] == self.License.get_serverID(url, token):
            ask_for_confirmation:bool = input('This is an export server. Wish to import here?(Y/N): ').lower()
            return True if ask_for_confirmation == 'y' else False
        elif not check_server_info:
            return False
        else:
            self.export_serverId = check_server_info.split()[1]
            return True


    def get_BimClassId_of_current_process(self, workflowId, url, token):
        ''' Function returns BimClass_id of provided workFlow proccess. '''

        headers_import = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}
        url_get_BimClassID_of_current_process = f"{url}/{self.__api_WorkFlows}/{workflowId}/BimClasses"
        request = requests.get(url=url_get_BimClassID_of_current_process, headers=headers_import, verify=False)
        response = request.json()
        for object in range(len(response)):
            return response[object]['id']


    def post_workflows(self, url, token):
        ''' Function to make a post request from exported files. '''

        # vars to work within this function
        workflows_folder = self.__transfer_folder + '/' + self.__workflows_folder

        url_create_workflow_import = f"{url}/{self.__api_WorkFlows}"
        headers_import = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}

        # Getting the id of the Draft node on import server
        for obj in File.read_file(workflows_folder, self.__all_workflow_nodes_file):
            if obj['name'] == 'Draft':
                import_server_draft_node_id:str = obj['id']
                break
        
        '''  BEGIN of POST request to create workFlows  '''
        nodes_for_import:list = File.read_file(workflows_folder, self.Export_data._selected_workflow_nodes_file).split()
        for node_workflows in nodes_for_import:
            workflow_data = File.read_file(workflows_folder, node_workflows)
            for workflow in workflow_data['workFlows']:
                post_payload = {
                                "name": workflow["name"],
                                "workFlowNodeId": import_server_draft_node_id,
                                "description": str(workflow["description"]),
                                "elements": [],
                                "type": workflow["type"]
                                }
                post_payload = json.dumps(post_payload)
                try:
                    post_request = requests.post(url=url_create_workflow_import, data=post_payload, headers=headers_import, verify=False)  # verify=False to eliminate SSL check which causes Error
                    post_response = post_request.json()
                except self.possible_request_errors as err:
                    logging.error(f"{err}\n{post_request.text}")
                    return False

                bimClass_id = self.get_BimClassId_of_current_process(post_response['originalId'], url, token)   # 
                bimClass_list_id_export = File.read_file(workflows_folder, self.Export_data._workflowID_bimClassID_file)                
                time.sleep(0.2)
                '''  END of POST request to create workFlows  '''


                '''  BEGIN OF PUT REQUEST  '''
                # adding 'elements': [], data from workFlows export into newly created workFlow
                put_payload = {
                                "name": workflow["name"],
                                "workFlowNodeId": import_server_draft_node_id,    # 0: Draft; 1: Archived; 2: Active;
                                "description": str(workflow["description"]),
                                "elements": workflow['elements'],
                                "type": workflow["type"]
                                }
                put_payload = json.dumps(put_payload)

                # Replacement of workFlow_bimClass_ID from export server with bimClass_ID newly created workFlow on import server
                changed_put_payload = put_payload.replace(bimClass_list_id_export[workflow["originalId"]], bimClass_id)

                try:
                    requests.put(url=f"{url_create_workflow_import}/{post_response['originalId']}", data=changed_put_payload, headers=headers_import, verify=False)  # /api/WorkFlows/{workFlowOriginalId}  
                    time.sleep(0.2)
                except self.possible_request_errors as err:
                    logging.error(err)
                    logging.debug("Workflow name: " + workflow["name"])
                    print(f"Error with the workflow {workflow['name']} import. Check the logs.")
                    return False
                '''  END OF PUT REQUEST  '''        

                '''  BEGIN OF XML POST REQUEST  '''
                headers_for_xml_import = {'accept': '*/*', 'Authorization': f"Bearer {token}"}    # specific headers without 'Content-type' for import .xml file. Otherwise request doesn't work!
                payload={}
                files=[ ('file',(f'{workflow["originalId"]}.xml', open(f'{workflows_folder}/{workflow["originalId"]}.xml','rb'),'text/xml')) ]
                try:           
                    post_xml_request = requests.post(url=f"{url_create_workflow_import}/{post_response['originalId']}/Diagram?contentType=file", headers=headers_for_xml_import, data=payload, files=files, verify=False)
                except self.possible_request_errors as err:
                    logging.error(f"{err}\n{post_xml_request.text}")

                print("   - " + post_response['name'] + " " + ('' if post_xml_request.status_code == 200 else "  --->  error"))
                time.sleep(0.2)
                '''  END OF XML POST REQUEST  '''
        return True


    def prepare_object_model_file_for_import(self):
        '''
            Function finds needed data(used two tuples as pointers: big_fish and small_fish) in object_model_import_server.json file, and place it in the object_model_export_server.json file.
            Both servers use the same data structure with key-value pairs. Thus, they have identical keys and different values. We search for values we need in object_model_import_server.json file, 
            and replace with it values in object_model_export_server.json file. Needed preparation are going to be end in modified_object_model.json file, which will be used further in import process.
        '''
        # Turn both .json files into dictionaries
        data_obj_model_import = File.read_file(self.__transfer_folder + '/' + self.__object_model_folder, self.__object_model_file)
        data_obj_model_export = File.read_file(self.__transfer_folder + '/' + self.Export_data._object_model_folder, self.Export_data._object_model_file)
        
        # Pointers to data we need to collect from the .json file
        big_fish: tuple = ("bimPropertyTreeNodes", "bimInterfaceTreeNodes", "bimClassTreeNodes", "bimDirectoryTreeNodes", "bimStructureTreeNodes", "rootSystemBimClass", "systemBimInterfaces", 
                            "systemBimProperties","secondLevelSystemBimClasses",)
        small_fish: tuple = ("BimProperty", "BimInterface", "BimClass", "BimDirectory", "BimStructure", "FILE_INTERFACE", "WORK_DATES_INTERFACE", "COMMERCIAL_SECRET_BIM_INTERFACE","FILE_PROPERTY", 
                            "PLANNED_START_PROPERTY","PLANNED_END_PROPERTY", "ACTUAL_START_PROPERTY", "ACTUAL_END_PROPERTY", "COMMERCIAL_SECRET_BIM_PROPERTY","ACTIVE_CLASS","FOLDER_CLASS", "DOCUMENT_CLASS",
                            "WORK_CLASS", "Файл", "Даты работы", "Коммерческая тайна", "Планируемое начало", "Планируемое окончание", "Фактическое начало", "Фактическое окончание")

        insert_data: dict = {}    # data that needs to be added to object_model_export_server.json file
        replace_data: dict = {}   # data that needs to be removed from object_model_export_server.json file

        if data_obj_model_import:
            # Collecting values from import model object .json file to put in export .json
            for key in data_obj_model_import.keys():
                if key in big_fish and isinstance(data_obj_model_import[key], list):
                    insert_data.setdefault(key, {})
                    for obj in data_obj_model_import[key]:
                        if isinstance(obj, dict):
                            for k,v in obj.items():
                                if v in small_fish:
                                    # insert_data[key][k] = v
                                    # insert_data[key]['id'] = obj['id']
                                    insert_data[key][v] = obj['id']

                elif key in big_fish and isinstance(data_obj_model_import[key], dict):
                    insert_data.setdefault(key, {data_obj_model_import[key]['name']: data_obj_model_import[key]['id']})
        else:
            print('No object model file for import was found.')
            return

        if data_obj_model_export:
            # Collecting data from 'object_model_export_server.json' file to replace it with data from 'object_model_import_server.json'
            for key in data_obj_model_export.keys():
                if key in big_fish and isinstance(data_obj_model_export[key], list):
                    replace_data.setdefault(key, {})
                    for obj in data_obj_model_export[key]:
                        if isinstance(obj, dict):
                            for k,v in obj.items():
                                if v in small_fish:
                                    # replace_data[key][k] = v
                                    # replace_data[key]['id'] = obj['id']
                                    replace_data[key][v] = obj['id']
                                
                elif key in big_fish and isinstance(data_obj_model_export[key], dict):
                    replace_data.setdefault(key, {data_obj_model_export[key]['name']: data_obj_model_export[key]['id']})
        else:
            print('No object model file for export was found.')
            return

        # Making a copy of the 'object_model_export_server.json' file which we will prepare for export
        shutil.copyfile(f"{self.__transfer_folder}/{self.__object_model_folder}/{self.Export_data._object_model_file}", f"{self.__transfer_folder}/{self.__object_model_folder}/{self.__modified_object_model_file}")

        # Replacement of values in .json file
        modified_OM_file:str = f'{self.__transfer_folder}/{self.__object_model_folder}/{self.__modified_object_model_file}'
        for key,value in replace_data.items():
            for key_from_export_json, value_from_export_json in value.items():
                try:
                    File.replace_str_in_file(modified_OM_file, modified_OM_file, value_from_export_json, insert_data[key][key_from_export_json])
                    time.sleep(0.1)
                except (KeyError, ValueError, TypeError, UnicodeError, UnicodeDecodeError, UnicodeEncodeError, SyntaxError) as err:
                    logging.error(err)
                    return False

        logging.info(f"Preparation object model file is finished. '{self.Export_data._object_model_file}' was altered into a '{self.__modified_object_model_file}' file.")
        print("\n   - preparing object model file:        done")
        return True


    def fix_defaulValues_in_object_model(self):
        '''  The function checks for 'defaultValues' keys in 'bimProperties'. If all values in the list are null, it will be replaced with an empty list [].  '''

        modified_obj_model_json = File.read_file(self.__transfer_folder + '/' + self.__object_model_folder, self.__modified_object_model_file)

        if modified_obj_model_json:
            count = 0
            with open(f"{self.__transfer_folder}/{self.__object_model_folder}/{self.__modified_object_model_file}", 'w', encoding='utf-8') as file:
                for bimClasses_dict in modified_obj_model_json['bimClasses']:    # bimClasses - list with dictionaries inside
                    for bimProperties_dict in bimClasses_dict['bimProperties']:  # bimProperties - list with dictionaries inside               
                        for defaultValues in bimProperties_dict.get('defaultValues'):                
                            if all(value == None for value in defaultValues.values()):                    
                                bimProperties_dict['defaultValues'] = []
                                count += 1                    

                json.dump(modified_obj_model_json, file, ensure_ascii=False, indent=4)
            if count > 0:
                print(f"   - corrupted 'defaultValues':       {count}")
            logging.info(f"Fixing defaultValues in '{self.__modified_object_model_file}' file is finished. Corrupted defaulValues: {count}")
            return True
        else:
            return False


    def post_object_model(self, url, token):

        headers_import = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}
        url_post_object_model:str = f'{url}/{self.__api_Integration_ObjectModel_Import}'
        with open(f"{self.__transfer_folder}/{self.__object_model_folder}/{self.__modified_object_model_file}", "r", encoding="utf-8") as file:
            data = file.read()
        # json_payload = json.dumps(data, ensure_ascii=False) # Doesn't work with json.dumps if read from file   
        try:
            post_request = requests.post(url=url_post_object_model, data=data.encode("utf-8"),  headers=headers_import, verify=False)
        except self.possible_request_errors as err:
            logging.error(err)
            print("Error with POST object model. Check the logs.")
            return False

        if post_request.status_code != 200:
            logging.error(f"\n{post_request.text}")
            print("   - post object model:                  error ", post_request.status_code)
            return False
        else:
            print("   - post object model:                  done")
            return True


    def import_object_model(self, url, token):
        server_validation:bool = self.validate_import_server(url, token)
        object_model_file_exists:bool = os.path.isfile(f'{self.__transfer_folder}/{self.Export_data._object_model_folder}/{self.Export_data._object_model_file}')
        if object_model_file_exists and server_validation:
            self.Export_data.get_object_model(self.__object_model_file, url, token)
            self.prepare_object_model_file_for_import()
            self.fix_defaulValues_in_object_model()
            self.post_object_model(url, token)
            return True
        else:
            print("No object_model for import." if not os.path.isfile(f'{self.__transfer_folder}/{self.Export_data._object_model_folder}/{self.Export_data._object_model_file}') else "Can't perform import procedure on the export server.")
            return False


    def import_workflows(self, url, token):
        server_validation:bool = self.validate_import_server(url, token)
        workflows_folder_exists:bool = os.path.isdir(self.__transfer_folder + '/' + self.__workflows_folder)
        if workflows_folder_exists and server_validation:
            self.Export_data.get_all_workflow_nodes(self.__all_workflow_nodes_file, url, token)
            self.post_workflows(url, token)
            return True
        else:
            print("No workflows for import." if not os.path.isdir(f'{self.__transfer_folder}/{self.__workflows_folder}') else "Can't perform import procedure on the export server.")
            return False