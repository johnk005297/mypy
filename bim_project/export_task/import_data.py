#
# This is linux version script!

import requests
import json
# import export_data as ex      # Data from export_data.py 
import xml.etree.ElementTree as ET
import time
import sys
import os
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
disable_warnings(InsecureRequestWarning)
# from dotenv import load_dotenv    # commented when running on linux machine which can't install load_dotenv package
# load_dotenv()

'''     GLOBAL VARIABLES    '''
pwd = os.getcwd()
# token_iktest01 = os.getenv("token_iktest01")

''''''''''''''''''''''''''''''

def ask_for_object_model():

    answer = input("Import object model(Y/N) ? ").lower()    
    if answer in ("y", "yes"):
        return True
    elif answer in ("n", "no"):
        return False
    else:
        print("No choice was made. Stop executing script!")
        sys.exit()
    


def get_token_import_server():
    token_from_import_server = input("Enter Bearer token for import: ")
    print()
    return token_from_import_server

def headers():
    headers_import = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token_import_server}"}
    headers_for_xml_import = {'accept': '*/*', 'Authorization': f"Bearer {token_import_server}"}    # specific headers without 'Content-type' for import .xml file. Otherwise request doesn't work!
    return headers_import, headers_for_xml_import 
#------------------------------------------------------------------------------------------------------------------------------#

def get_url_import():    
    url_import: str = input("Enter import server url, like('http://address.com'): ").lower()
    return url_import
#------------------------------------------------------------------------------------------------------------------------------#



def create_folders():
    try:            
        os.mkdir('Archived')
        os.mkdir('Draft')
        os.mkdir('Active')
    except FileExistsError:
        pass
    print("create_folders - done")        
    
#------------------------------------------------------------------------------------------------------------------------------#



# Read from JSON files, and provide dict in return.
# Need to pass two arguments in str format: path and file name
def read_from_json(path_to_file,file_name):
    
    if file_name[-5:] == '.json':
        pass
    else: file_name += '.json'
    with open(f'{path_to_file}/{file_name}', 'r', encoding='utf-8') as file:
        data_from_json = json.load(file)
    
    return data_from_json

#------------------------------------------------------------------------------------------------------------------------------#
  
    
def define_workFlow_node_import():
    ''' 
        Function returns a tuple of elements like ("Active", "Active_workflows_export.json") which could be accessed by index.
        The following proccesses will be oriented only with this choise, and working with the choisen workFlow node.
        example:  workflow_node("Active", "Active_workflows_export_server.json")
                workflow_node[0] - "Active"
                workflow_node[1] - "Active_workflows_export.json"          
    '''    
    count = 0    
    while count < 3:
        workflow_node_select = input("\nWhat node to import? draft(1), archived(2), active(3)\nType 'q' for exit: ").lower().capitalize()        
        count += 1

        # workflow_node_select is a tuple with two values - directory and .json file
        if workflow_node_select in ('Draft', '1'):
            # workflow_node('Draft', 'Draft_workflows_export.json', 'draft')
            return "Draft", "Draft_workflows_export_server.json"

        elif workflow_node_select in ('Archived', '2'):
            # workflow_node('Archived", 'Archived_workflows_export.json', 'archived')        
            return "Archived", "Archived_workflows_export_server.json"

        elif workflow_node_select in ('Active', '3'):
            # workflow_node('Active", 'Active_workflows_export.json', 'active'               
            return "Active", "Active_workflows_export_server.json"  

        elif count == 3 or workflow_node_select == 'Q':  
            sys.exit("\nStop import process!")          
    
#------------------------------------------------------------------------------------------------------------------------------#


def get_workflow_nodes_import():
    ''' 
        Function to write a .json file with all the workFlow nodes on import server.                        
    '''    
    url = url_import + "/api/WorkFlowNodes"
    request = requests.get(url, headers=headers()[0], verify=False)
    response = request.json()
        
    with open('workflow_nodes_import_server.json', 'w') as json_file:
        json.dump(response, json_file, ensure_ascii=False, indent=4)   
    print("get_workflow_nodes_import - done")
    
#------------------------------------------------------------------------------------------------------------------------------#


def replace_str_in_file(file_in, file_out, find, replace):
    '''
        Function takes 4 arguments: file to read, file to write, what_to_find, what_to_put_instead_of_what_to_find.
    '''
    with open(f"{file_in}", 'r', encoding='utf-8') as file:
        new_json = file.read().replace(find, replace)      # find/replace vars must be string
    with open(f"{file_out}", 'w', encoding='utf-8') as file:
        file.write(new_json)
        
#------------------------------------------------------------------------------------------------------------------------------#


def get_model_object_import():
    '''
        Function get's model object from import server, and write's it to model_object_import_server.json file.
    '''
    url = url_import + "/api/Integration/ObjectModel/Export"
    request = requests.get(url, headers=headers()[0], verify=False)
    response = request.json()

    with open("model_object_import_server.json", "w", encoding="utf-8") as json_file:
        json.dump(response, json_file, ensure_ascii=False, indent=4)
    
    print("get_model_object_import - done")


#---------------------------------------------------------------------------------------------------------------------------------

def prepare_model_object_file_for_import():
    '''
        Function finds needed data(used two tuples as pointers: big_fish and small_fish) in model_object_import_server.json file, and place it in the model_object_export_server.json file.
        Both servers use the same data structure with key-value pairs. Thus, they have identical keys and different values. We search for values we need in model_object_import_server.json file, 
        and replace with it values in model_object_export_server.json file. model_object_export_server.json file will be used further on the import server.
    '''
    data_obj_model_import = read_from_json(pwd, "model_object_import_server.json")  # read the file into dictionary
    data_obj_model_export = read_from_json(pwd, "model_object_export_server.json")  # read the file into dictionary
    
    # Pointers to data we need to collect from the .json file
    big_fish: tuple = ("bimPropertyTreeNodes", "bimInterfaceTreeNodes", "bimClassTreeNodes", "bimDirectoryTreeNodes", "bimStructureTreeNodes", "rootSystemBimClass", "systemBimInterfaces", 
                        "systemBimProperties","secondLevelSystemBimClasses",)
    small_fish: tuple = ("BimProperty", "BimInterface", "BimClass", "BimDirectory", "BimStructure", "FILE_INTERFACE", "WORK_DATES_INTERFACE", "COMMERCIAL_SECRET_BIM_INTERFACE","FILE_PROPERTY", 
                        "PLANNED_START_PROPERTY","PLANNED_END_PROPERTY", "ACTUAL_START_PROPERTY", "ACTUAL_END_PROPERTY", "COMMERCIAL_SECRET_BIM_PROPERTY","ACTIVE_CLASS","FOLDER_CLASS", "DOCUMENT_CLASS",
                        "WORK_CLASS", )
    
    insert_tuple = ()   # data will be inserted in model_objects_export.json file
    replace_tuple = ()  # data will be removed from model_objects_export.json file
    
    # Collecting values from import model object .json file with values to put in export .json
    for key in data_obj_model_import.keys():
        if key in big_fish and isinstance(data_obj_model_import[key], list):
            for obj in data_obj_model_import[key]:
                if isinstance(obj, dict):
                    for k,v in obj.items():
                        if v in small_fish:
                            insert_tuple += (obj["id"],)
                            # print(obj) # dict
                                         
        elif key in big_fish and isinstance(data_obj_model_import[key], dict):
            insert_tuple += (data_obj_model_import[key]["id"],)
    
    # Collecting values from export model object .json file with values to replace in export .json
    for key in data_obj_model_export.keys():
        if key in big_fish and isinstance(data_obj_model_export[key], list):
            for obj in data_obj_model_export[key]:                         
                if isinstance(obj, dict):
                    for k,v in obj.items():
                        if v in small_fish:
                            replace_tuple += (obj["id"],)
                            # print(obj) # dict
                                      
        elif key in big_fish and isinstance(data_obj_model_export[key], dict):
            replace_tuple += (data_obj_model_export[key]["id"],)
     
    
    # Edit model object attributes in needed file
    for x in range(len(replace_tuple)):
        if len(replace_tuple) == len(insert_tuple):
            # print(replace_tuple[x], " ---> ", insert_tuple[x])
            replace_str_in_file("model_object_export_server.json", "model_object_export_server.json", replace_tuple[x], insert_tuple[x])        
        else:             
            sys.exit("Smth is wrong. Model_object files are incorrect. Exit")


    print(f"prepare_model_object_file_for_import - done")

#------------------------------------------------------------------------------------------------------------------------------#

'''
    The function checks for 'defaultValues' keys in 'bimProperties'. If all values in the list are null, it will be replaced with an empty list [].
'''
def fix_defaulValues():

    data = read_from_json(pwd, "model_object_export_server.json")
    count = 0
    with open('model_object_export_server.json', 'w', encoding='utf-8') as file:
        for bimClasses_dict in data['bimClasses']:  # bimClasses - list with dictionaries inside
                for bimProperties_dict in bimClasses_dict['bimProperties']:  # bimProperties - list with dictionaries inside               
                    for defaultValues in bimProperties_dict.get('defaultValues'):                
                        if all(value == None for value in defaultValues.values()):                    
                            bimProperties_dict['defaultValues'] = []
                            count += 1
                    

        json.dump(data, file, ensure_ascii=False, indent=4)

    print(f"Fixed model object's null 'defaultValues': {count}")


#------------------------------------------------------------------------------------------------------------------------------#



def post_model_object_import():

    url = url_import + "/api/Integration/ObjectModel/Import"    
    with open("model_object_export_server.json", "r", encoding="utf-8") as file:
        # data = file.read().replace('\n', '')   # backup line
        data = file.read()
    # json_payload = json.dumps(data, ensure_ascii=False) # Doesn't work with json.dumps if read from file    
    mod_odj_request = requests.post(url, data=data.encode("utf-8"),  headers=headers()[0], verify=False)

    print(f"post_model_object_import - done {mod_odj_request.status_code}" if mod_odj_request.status_code in (201, 200, 204) else f"post_model_object_import - {mod_odj_request.text} - error")


#------------------------------------------------------------------------------------------------------------------------------#


# data takes {workFlowOriginId} as an argument
def get_BimClassID_of_current_process_import(data):  # /api/WorkFlows/{workFlowOriginId}/BimClasses
    ''' Function returns BimClass_id of provided workFlow proccess. '''
    
    url = f"{url_import}/api/WorkFlows/{data}/BimClasses"
    request = requests.get(url, headers=headers()[0], verify=False)
    response = request.json()    
    for object in range(len(response)):
        return response[object]['id']
    

#------------------------------------------------------------------------------------------------------------------------------#


def create_workflow_import():    
    '''
    workflow_node tuple comes from define_workFlow_node_import() function. It provides a selection of two components ex.("Draft", "Draft_workflows_export.json")
    which can be accessed by index.
       example:  workflow_node[0] - "Draft"
                 workflow_node[1] - "Draft_workflows_export.json"
    '''
    url = url_import + "/api/WorkFlows"  # POST request to create workFlow

    workflows_from_export_server = read_from_json(f"{pwd}/{workflow_node[0]}",workflow_node[1])
    workflow_nodes_import = read_from_json(pwd,'workflow_nodes_import_server.json')     # Contains imported workflows
    
    '''  BEGIN of POST request to create workFlows  '''
    for workflow in workflows_from_export_server['workFlows']:
        post_payload = {
                        "name": workflow["name"],
                        "workFlowNodeId": workflow_nodes_import[0]['id'],    # 0: Draft; 1: Archived; 2: Active;
                        "description": str(workflow["description"]),
                        "elements": [],
                        "type": workflow["type"]
                        }
        json_post_payload = json.dumps(post_payload)
        post_request = requests.post(url, data=json_post_payload, headers=headers()[0], verify=False)     # /api/WorkFlows/{workFlowOriginalId}   # verify=False to eliminate SSL check which causes Error
        post_response = post_request.json()
        
        bimClass_id_import = get_BimClassID_of_current_process_import(post_response['originalId'])    # reference workFlow_original_ID on import server
        bimClass_list_id_export = read_from_json(f"{pwd}/{workflow_node[0]}", 'workFlow_id_bimClass_id_export.json')
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
        requests.put(url + "/" + post_response['originalId'], data=changed_put_payload, headers=headers()[0], verify=False)   # /api/WorkFlows/{workFlowOriginalId}  
        time.sleep(0.25)
        '''  END OF PUT REQUEST  '''        

        '''  BEGIN OF XML POST REQUEST  '''      
        xml_path = pwd + "/" + workflow_node[0]

        payload={}
        files=[ ('file',(f'{workflow["originalId"]}.xml',open(f'{xml_path}/{workflow["originalId"]}.xml','rb'),'text/xml'))  ]
                        
        post_xml_request = requests.post(f"{url}/{post_response['originalId']}/Diagram?contentType=file", headers=headers()[1], data=payload, files=files, verify=False)
        # print(f"{post_xml_request.status_code}")
        print(f"Name of process: {post_response['name']}",end=' ')
        print(f"{post_xml_request.status_code} - done" if post_xml_request.status_code == 200 else f"{post_xml_request.status_code} - error")
        time.sleep(0.25)
        '''  END OF XML POST REQUEST  '''
    
        # print(f"create_workflow - done" if post_request.status_code == 201 else f"create_workflow - {post_request.status_code} - error")
    print("create_workflow - done")
    
#------------------------------------------------------------------------------------------------------------------------------#



def get_workflows_import():
    ''' Function collects all workFlows from all three nodes on import server. '''
    
    data = read_from_json(pwd, 'workflow_nodes_export_server.json')
    for obj in range(len(data)):
        key = data[obj]['name']
        value = data[obj]['id']

        url = f"{url_import}/api/WorkFlowNodes/{value}/children"
        request = requests.get(url, headers=headers()[0], verify=False)
        response = request.json()

        with open(f"{pwd}/{key}/{key}_workflows_import_server.json", 'w', encoding='utf-8') as json_file:
            json.dump(response, json_file, ensure_ascii=False, indent=4)

    print("get_workflows_import - done\n\n")
    os.system('pause')

#------------------------------------------------------------------------------------------------------------------------------#



if __name__ == "__main__":
    # ex.get_token()    # function from export_task.py, which isn't ready yet.
    ask = ask_for_object_model()
    token_import_server = get_token_import_server()
    url_import = get_url_import()
    create_folders()
    workflow_node = define_workFlow_node_import()  
    get_workflow_nodes_import()
    if ask:
        get_model_object_import()
        prepare_model_object_file_for_import()
        fix_defaulValues()
        post_model_object_import()    
    create_workflow_import()
    get_workflows_import()
    
    
