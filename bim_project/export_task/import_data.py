#
# version: 1.3

import requests
import json
import xml.etree.ElementTree as ET
import time
import sys
import os
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
disable_warnings(InsecureRequestWarning)
import logging
import shutil
# from export_data import ex.possible_request_errors
import export_data as ex




'''     GLOBAL VARIABLES    '''
pwd = os.getcwd()
# ex.possible_request_errors: tuple = (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout, 
                                    #   requests.exceptions.HTTPError, requests.exceptions.InvalidHeader, requests.exceptions.InvalidURL,)
''''''''''''''''''''''''''''''



def check_folder_with_files_and_logs():

    if os.path.isdir(f"{pwd}/files") == False:
        logging.error("Folder 'files' is missing.")
        sys.exit("Folder 'files' is missing. Exit.")
    elif os.path.isdir(f"{pwd}/files/logs") == False:
        os.mkdir(f"{pwd}/files/logs")
    else:
        pass

    logging.basicConfig(filename=f"{pwd}/files/logs/import_log.txt", level=logging.DEBUG,
                        format="%(asctime)s %(levelname)s - %(message)s", filemode="w", datefmt='%d-%b-%y %H:%M:%S')

#------------------------------------------------------------------------------------------------------------------------------#


def check_for_object_model():

    return True if os.path.isfile(f"{pwd}/files/model_object_export_server.json") else False
#------------------------------------------------------------------------------------------------------------------------------#


def check_for_process():

    return True if os.path.isfile(f"{pwd}/files/workflow_nodes.txt") else False
#------------------------------------------------------------------------------------------------------------------------------#


def get_server_url():

    server_url: str = input("Enter server URL: ").lower().strip()
    return server_url[:-1] if server_url[-1:]=='/' else server_url
#------------------------------------------------------------------------------------------------------------------------------#


def get_token(username='admin', password='Qwerty12345!'):
    
    list_of_providersID: list = []
    headers = {'accept': '*/*', 'Content-type':'application/json; charset=utf-8'}
    url_get_providers = f'{server_url}/api/Providers'

    try:
        id_request = requests.get(url_get_providers, headers=headers, verify=False)
        response = id_request.json()    
    except ex.possible_request_errors as err:
        logging.error(err)
        sys.exit(f"Connection error: {err}")
    
    for dict in response:
        list_of_providersID.append(dict['id'])

    url_auth = f'{server_url}/api/Auth/Login'
    confirm_username = input("Enter login(default, admin): ")
    confirm_password = input("Enter password(default, Qwerty12345!): ")

    if confirm_username:
        username = confirm_username
    if confirm_password:
        password = confirm_password

    for id in list_of_providersID:
        payload = {
                    "username": username,
                    "password": password,
                    "providerId": id
                }
        data = json.dumps(payload)
    
        auth_request = requests.post(url_auth, data=data, headers=headers, verify=False)
        response = auth_request.json()

        if auth_request.status_code == 200:
            token = response['access_token']
            break
        else:
            logging.error(f"{auth_request.status_code}\n{auth_request.text}")

    return token

#------------------------------------------------------------------------------------------------------------------------------#

def get_headers():
    
    token = get_token()
    headers_import = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}
    headers_for_xml_import = {'accept': '*/*', 'Authorization': f"Bearer {token}"}    # specific headers without 'Content-type' for import .xml file. Otherwise request doesn't work!

    return headers_import, headers_for_xml_import


#------------------------------------------------------------------------------------------------------------------------------#


def read_from_json(path_to_file,file_name):
    ''' Read from JSON files, and provide dict in return. Need to pass two arguments in str format: path and file name. '''

    if file_name[-5:] == '.json':
        pass
    else: file_name += '.json'
    with open(f'{path_to_file}/{file_name}', 'r', encoding='utf-8') as file:
        data_from_json = json.load(file)
    
    return data_from_json

    
#------------------------------------------------------------------------------------------------------------------------------#


def get_workflow_nodes_import():
    ''' 
        Function to write a .json file with all the workFlow nodes on import server.                        
    '''    
    url = server_url + "/api/WorkFlowNodes"
    try:
        request = requests.get(url, headers=headers_import[0], verify=False)        
        response = request.json()
    except ex.possible_request_errors as err:
        logging.error(f"{err}\n{request.text}")
        sys.exit()
    
    with open(f'{pwd}/files/workflow_nodes_import_server.json', 'w', encoding='utf-8') as json_file:
        json.dump(response, json_file, ensure_ascii=False, indent=4)

    logging.info("Workflow nodes function is finished. 'workflow_nodes_import_server.json' file is ready.")

    print("  - Get workflow nodes:                 done")
#------------------------------------------------------------------------------------------------------------------------------#


def replace_str_in_file(file_in, file_out, find, replace):
    '''
        Function takes 4 arguments: file to read, file to write, what_to_find, what_to_put_instead_of_what_to_find.
    '''
    with open(f"{pwd}/files/{file_in}", 'r', encoding='utf-8') as file:
        new_json = file.read().replace(find, replace)      # find/replace vars must be string
    with open(f"{pwd}/files/{file_out}", 'w', encoding='utf-8') as file:
        file.write(new_json)
        
#------------------------------------------------------------------------------------------------------------------------------#


def get_model_object_import():
    '''
        Function get's model object from import server, and write's it to model_object_import_server.json file.
    '''
    
    url = server_url + "/api/Integration/ObjectModel/Export"
    try:
        request = requests.get(url, headers=headers_import[0], verify=False)
        response = request.json()    
    except ex.possible_request_errors as err:
        logging.error(f"{err}\n{request.text}")

    with open(f"{pwd}/files/model_object_import_server.json", "w", encoding="utf-8") as json_file:
        json.dump(response, json_file, ensure_ascii=False, indent=4)
    
    logging.info("Object model function is finished. 'model_object_import_server.json' file is ready.")
    print("  - Get object model:                   done")
    

#---------------------------------------------------------------------------------------------------------------------------------

def prepare_model_object_file_for_import():
    '''
        Function finds needed data(used two tuples as pointers: big_fish and small_fish) in model_object_import_server.json file, and place it in the model_object_export_server.json file.
        Both servers use the same data structure with key-value pairs. Thus, they have identical keys and different values. We search for values we need in model_object_import_server.json file, 
        and replace with it values in model_object_export_server.json file. model_object_export_server.json file will be used further on the import server.
    '''


    data_obj_model_import = read_from_json(f"{pwd}/files", "model_object_import_server.json")  # read the file into dictionary
    data_obj_model_export = read_from_json(f"{pwd}/files", "model_object_export_server.json")  # read the file into dictionary
    
    # Pointers to data we need to collect from the .json file
    big_fish: tuple = ("bimPropertyTreeNodes", "bimInterfaceTreeNodes", "bimClassTreeNodes", "bimDirectoryTreeNodes", "bimStructureTreeNodes", "rootSystemBimClass", "systemBimInterfaces", 
                        "systemBimProperties","secondLevelSystemBimClasses",)
    small_fish: tuple = ("BimProperty", "BimInterface", "BimClass", "BimDirectory", "BimStructure", "FILE_INTERFACE", "WORK_DATES_INTERFACE", "COMMERCIAL_SECRET_BIM_INTERFACE","FILE_PROPERTY", 
                        "PLANNED_START_PROPERTY","PLANNED_END_PROPERTY", "ACTUAL_START_PROPERTY", "ACTUAL_END_PROPERTY", "COMMERCIAL_SECRET_BIM_PROPERTY","ACTIVE_CLASS","FOLDER_CLASS", "DOCUMENT_CLASS",
                        "WORK_CLASS", "Файл", "Даты работы", "Коммерческая тайна", "Планируемое начало", "Планируемое окончание", "Фактическое начало", "Фактическое окончание")
    
    
    
    insert_data: dict = {}    # data that needs to be added to model_objects_export.json file
    replace_data: dict = {}   # data that needs to be removed from model_objects_export.json file

    # Collecting values from import model object .json file with values to put in export .json
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
            
    
    # Collecting data from 'model_object_export_server.json' file to replace it with data from 'model_object_import_server.json'
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


    # Making a copy of the 'model_object_export_server.json' file which we will prepare for export
    shutil.copyfile(f"{pwd}/files/model_object_export_server.json", f"{pwd}/files/modified_object_model.json")

    # Replacement values in .json file       
    for key,value in replace_data.items():
        for key_from_export_json, value_from_export_json in value.items():
            try:
                replace_str_in_file('modified_object_model.json', 'modified_object_model.json', value_from_export_json, insert_data[key][key_from_export_json])
                time.sleep(0.1)
            except (KeyError, ValueError, TypeError, UnicodeError, UnicodeDecodeError, UnicodeEncodeError, SyntaxError) as err:
                logging.error(err)
    

    logging.info("Preparation object model file is finished. 'model_object_export_server.json' was altered.")
    print("  - Preparation object model file:      done")


#------------------------------------------------------------------------------------------------------------------------------#

'''
    The function checks for 'defaultValues' keys in 'bimProperties'. If all values in the list are null, it will be replaced with an empty list [].
'''
def fix_defaulValues():

    data = read_from_json(f"{pwd}/files", "modified_object_model.json")
    count = 0
    with open(f"{pwd}/files/modified_object_model.json", 'w', encoding='utf-8') as file:
        for bimClasses_dict in data['bimClasses']:  # bimClasses - list with dictionaries inside
            for bimProperties_dict in bimClasses_dict['bimProperties']:  # bimProperties - list with dictionaries inside               
                for defaultValues in bimProperties_dict.get('defaultValues'):                
                    if all(value == None for value in defaultValues.values()):                    
                        bimProperties_dict['defaultValues'] = []
                        count += 1                    

        json.dump(data, file, ensure_ascii=False, indent=4)

    logging.info(f"Fixing defaultValues in object model finished. Corrupted defaulValues: {count}")
    return count
#------------------------------------------------------------------------------------------------------------------------------#


def post_model_object_import():

    url = server_url + "/api/Integration/ObjectModel/Import"
    with open(f"{pwd}/files/modified_object_model.json", "r", encoding="utf-8") as file:
        # data = file.read().replace('\n', '')   # backup line
        data = file.read()
    # json_payload = json.dumps(data, ensure_ascii=False) # Doesn't work with json.dumps if read from file   
    try: 
        model_odject_request = requests.post(url, data=data.encode("utf-8"),  headers=headers_import[0], verify=False)
    except ex.possible_request_errors as err:
        logging.error(f"{err}")
        # sys.exit("  - Post object model:                  error. Check out the 'import_data.log' file. Exit.")
    if model_odject_request.status_code != 200:
        logging.error(f"\n{model_odject_request.text}")
        print("  - Post object model:                  error ", model_odject_request.status_code)
    else:
        print("  - Post object model:                  done")

    

#------------------------------------------------------------------------------------------------------------------------------#


# data takes {workFlowOriginId} as an argument
def get_BimClassID_of_current_process_import(data):  # /api/WorkFlows/{workFlowOriginId}/BimClasses
    ''' Function returns BimClass_id of provided workFlow proccess. '''
    
    url = f"{server_url}/api/WorkFlows/{data}/BimClasses"
    request = requests.get(url, headers=headers_import[0], verify=False)
    response = request.json()
    for object in range(len(response)):
        return response[object]['id']
#------------------------------------------------------------------------------------------------------------------------------#


def create_workflow_import():    
    '''
    
    '''
    url = server_url + "/api/WorkFlows"  # POST request to create workFlow
    workflow_nodes: list = []
    if os.path.isfile(f"{pwd}/files/workflow_nodes.txt"):
        with open(f"{pwd}/files/workflow_nodes.txt", 'r', encoding='utf-8') as file:
            for line in file:
                workflow_nodes.append(line[:-1])    # it removes the last symbol, because 'workflow_nodes.txt' always has '\n' - newline, as a last symbol
    else:
        print("No workflow_nodes.txt file. Check 'files' folder. Exit.")
        sys.exit()
            
    workflow_nodes_import = read_from_json(f"{pwd}/files", "workflow_nodes_import_server.json")     # Contains imported workflows

    
    '''  BEGIN of POST request to create workFlows  '''
    print("  - Created processes: ")
    for node in range(len(workflow_nodes)):
        workFlow_data = read_from_json(f"{pwd}/files", workflow_nodes[node])
        
        for workflow in workFlow_data['workFlows']:
            post_payload = {
                            "name": workflow["name"],
                            "workFlowNodeId": workflow_nodes_import[0]['id'],    # 0: Draft; 1: Archived; 2: Active;
                            "description": str(workflow["description"]),
                            "elements": [],
                            "type": workflow["type"]
                            }
            json_post_payload = json.dumps(post_payload)
            try:
                post_request = requests.post(url, data=json_post_payload, headers=headers_import[0], verify=False)     # verify=False to eliminate SSL check which causes Error
                post_response = post_request.json()
            except ex.possible_request_errors as err:
                logging.error(f"{err}\n{post_request.text}")

            bimClass_id_import = get_BimClassID_of_current_process_import(post_response['originalId'])    # reference workFlow_original_ID on import server
            bimClass_list_id_export = read_from_json(f"{pwd}/files", 'workFlow_id_bimClass_id_export.json')
            time.sleep(0.25)
            '''  END of POST request to create workFlows  '''
            
            '''  BEGIN OF PUT REQUEST  '''
            # adding 'elements': [], data from workFlows export into newly created workFlow
            put_payload = {
                            "name": workflow["name"],
                            "workFlowNodeId": workflow_nodes_import[0]['id'],    # 0: Draft; 1: Archived; 2: Active;
                            "description": str(workflow["description"]),
                            "elements": workflow['elements'],
                            "type": workflow["type"]
                            }
            json_put_payload = json.dumps(put_payload)
            
            # Replacement of workFlow_bimClass_ID from export server with bimClass_ID newly created workFlow on import server
            changed_put_payload = json_put_payload.replace(bimClass_list_id_export[workflow["originalId"]], bimClass_id_import)
            try:
                requests.put(url + "/" + post_response['originalId'], data=changed_put_payload, headers=headers_import[0], verify=False)   # /api/WorkFlows/{workFlowOriginalId}  
                time.sleep(0.25)
            except ex.possible_request_errors as err:
                logging.error(err)
                logging.debug("Workflow name: " + workflow["name"])
                sys.exit("  - Put workflow got error. Check out the 'import_data.log' file. Exit.")
            '''  END OF PUT REQUEST  '''        

            '''  BEGIN OF XML POST REQUEST  '''
            xml_path = pwd + "/files"

            payload={}
            files=[ ('file',(f'{workflow["originalId"]}.xml', open(f'{xml_path}/{workflow["originalId"]}.xml','rb'),'text/xml'))  ]

            try:           
                post_xml_request = requests.post(f"{url}/{post_response['originalId']}/Diagram?contentType=file", headers=headers_import[1], data=payload, files=files, verify=False)
            except ex.possible_request_errors as err:
                logging.error(f"{err}\n{post_xml_request.text}")

            print("      " + post_response['name'] + " " + ('' if post_xml_request.status_code == 200 else "  --->  error"))
            time.sleep(0.25)
            '''  END OF XML POST REQUEST  '''
#------------------------------------------------------------------------------------------------------------------------------#


def get_workflows_import():
    ''' Function collects all workFlows from all three nodes on import server. '''
    
    data = read_from_json(f"{pwd}/files", 'workflow_nodes_import_server.json')
    for obj in range(len(data)):
        key = data[obj]['name']
        value = data[obj]['id']

        url = f"{server_url}/api/WorkFlowNodes/{value}/children"
        try:
            request = requests.get(url, headers=headers_import[0], verify=False)
            response = request.json()
        except ex.possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")

        with open(f"{pwd}/files/{key}_workflows_import_server.json", 'w', encoding='utf-8') as json_file:
            json.dump(response, json_file, ensure_ascii=False, indent=4)

    logging.info(f"Get workflows for {key} is finished. '{key}_workflows_import_server.json' file is ready.")
    print("  - Get workflows:                      done")


def mark_begin():
    print("\n================== BEGIN import procedure ==================\n")


def mark_finish():
    print("\n================== END import procedure ====================\n")
    if sys.platform == 'win32':
        os.system('pause')


if __name__ == "import_data":           # current module will be executed only if it is imported
    check_folder_with_files_and_logs()
    server_url = get_server_url()
    headers_import = get_headers()
    mark_begin()
    if check_for_process():
        get_workflow_nodes_import()
        create_workflow_import()
        get_workflows_import()
    if check_for_object_model():
        get_model_object_import()
        prepare_model_object_file_for_import()
        fix_defaulValues()
        post_model_object_import()
    mark_finish()
