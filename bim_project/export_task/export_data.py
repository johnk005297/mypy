#
# version: 1.1

import requests
import json
import os
import xml.etree.ElementTree as ET
import sys
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
disable_warnings(InsecureRequestWarning)
import logging
import shutil



'''     GLOBAL VARIABLES    '''
pwd = os.getcwd()
possible_request_errors: tuple = (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout, 
                                      requests.exceptions.HTTPError, requests.exceptions.InvalidHeader, requests.exceptions.InvalidURL,)

''''''''''''''''''''''''''''''

#------------------------------------------------------------------------------------------------------------------------------#


def get_url_export():
    
    url_export_server: str = input("Enter export server URL: ").lower()    
    if url_export_server[-1:] == '/':
        return url_export_server[:-1]
    else:
        return url_export_server

#------------------------------------------------------------------------------------------------------------------------------#

def get_token(username='admin', password='Qwerty12345!'):
    
    list_of_providersID: list = []
    headers = {'accept': '*/*', 'Content-type':'application/json; charset=utf-8'}
    url_get_providers = f'{url_export}/api/Providers'

    try:
        id_request = requests.get(url_get_providers, headers=headers, verify=False)
        response = id_request.json()
    except possible_request_errors as err:
        logging.error(err)
        sys.exit(f"Connection error: {err}")

    for dict in response:
        list_of_providersID.append(dict['id'])

    url_auth = f'{url_export}/api/Auth/Login'
    confirm_name = input("Enter login(default, admin): ")
    confirm_pass = input("Enter password(default, Qwerty12345!): ")

    if confirm_name:
        username=confirm_name
    if confirm_pass:
        password=confirm_pass

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
            logging.error('%s', auth_request.status_code)

    return token

#------------------------------------------------------------------------------------------------------------------------------#

def get_headers():
    token = get_token()
    headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}
    return headers

#------------------------------------------------------------------------------------------------------------------------------#




def create_folder_for_files_and_logs():

    # if 'files' folder from previous export procedure exists, it will be deleted to create a new one.
    if os.path.isdir('files'):
        shutil.rmtree('files')
    else: pass

    os.mkdir('files')
    os.mkdir(f'{pwd}/files/logs')    

    if os.path.isdir(f"{pwd}/files") == False:     
        print("Folder 'files' wasn't created. Exit.")
        sys.exit()
    elif os.path.isdir(f"{pwd}/files/logs") == False:
        print("Folder 'logs' wasn't created. Exit.")
        sys.exit()
    else:
        pass

    logging.basicConfig(filename=f"{pwd}/files/logs/export_log.txt", level=logging.DEBUG,
                        format="%(asctime)s %(levelname)s - %(message)s", filemode="w", datefmt='%d-%b-%y %H:%M:%S')



#------------------------------------------------------------------------------------------------------------------------------#



def define_workFlow_node_export():
    
    '''    Function creates a file 'workflow_nodes.txt' with chosen workflow nodes in it.   '''    
    
    with open(f"{pwd}/files/workflow_nodes.txt", mode='w',encoding='utf-8'): pass
    
    # Check if the 'workflow_nodes.txt' was created
    if os.path.isfile(f"{pwd}/files/workflow_nodes.txt"):
        pass
    else:
        logging.error("File 'workflow_nodes.txt' hasn't been created. Exit.")
        sys.exit("File 'workflow_nodes.txt' hasn't been created. Exit.")

    workflow_node_selected: list = input("\nChose nodes to export workflows from. Use whitespaces in-between. \nDraft(1) || Archived(2) || Active(3)\n\nType 'q' for exit: ").lower().split()   

    if 'q' in workflow_node_selected:
        sys.exit("\nStop export process!")

    if '1' in workflow_node_selected or 'draft' in workflow_node_selected:        
        with open(f"{pwd}/files/workflow_nodes.txt", 'a', encoding='utf-8') as file:                           
            file.write("Draft_workflows_export_server.json\n")        

    if '2' in workflow_node_selected or 'archived' in workflow_node_selected:
        with open(f"{pwd}/files/workflow_nodes.txt", 'a', encoding='utf-8') as file:            
            file.write("Archived_workflows_export_server.json\n")        

    if '3' in workflow_node_selected or 'active' in workflow_node_selected:
        with open(f"{pwd}/files/workflow_nodes.txt", 'a', encoding='utf-8') as file:            
            file.write("Active_workflows_export_server.json\n")  
        


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


def get_workflow_nodes_export():       
    ''' Getting Draft, Archived and Active nodes Ids.  '''   

    url = url_export + "/api/WorkFlowNodes"
    try:
        request = requests.get(url, headers=headers_export, verify=False)
        response = request.json()
    except possible_request_errors as err:
        logging.error(f"{err}\n{request.text}") 
        sys.exit(f"Error: Couldn't export workFlow nodes. Exit.\n\n{err}")

    with open(f'{pwd}/files/workflow_nodes_export_server.json', 'w', encoding='utf-8') as json_file:
        json.dump(response, json_file, ensure_ascii=False, indent=4)

    print("  - Get workflow nodes:                          done")
    
#------------------------------------------------------------------------------------------------------------------------------#


def get_model_object_export():    
    ''' 
        Function gets model object from export server, and writes it in model_object_export_server.json file.
        /api/Integration/ObjectModel/Export  - api service
    '''
    ask_model_object = input("Need to export object model? (Y/N): ").lower()
    
    print("\n================== Starting export procedure ==================\n")

    if ask_model_object in ("yes", "y", "1"):

        url = url_export + "/api/Integration/ObjectModel/Export"
        try:
            request = requests.get(url, headers=headers_export, verify=False)
            response = request.json()
        except possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")
            sys.exit(f"Error: Couldn't export object model. Exit.\n\n{err}")

        with open(f"{pwd}/files/model_object_export_server.json", "w", encoding="utf-8") as json_file:
            json.dump(response, json_file, ensure_ascii=False, indent=4)


        print("  - Get object model:                            done")

    elif ask_model_object in ("n", "no", "0"):
        pass
    else:
        sys.exit("No choice was made. Stop executing script!")
    
    

#------------------------------------------------------------------------------------------------------------------------------#


def get_workflows_export():
    ''' Get all workFlows from the chosen node. '''

    data = read_from_json(f"{pwd}/files", "workflow_nodes_export_server.json")
    for obj in range(len(data)):
        key = data[obj]['name']
        value = data[obj]['id']
        
        url = f"{url_export}/api/WorkFlowNodes/{value}/children"
        try:
            request = requests.get(url, headers=headers_export, verify=False)
            response = request.json()
        except possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")

        with open(f"{pwd}/files/{key}_workflows_export_server.json", 'w', encoding='utf-8') as json_file:
            json.dump(response, json_file, ensure_ascii=False, indent=4)
    
    logging.info(f"'{key}_workflows_export_server.json' file is ready.")
    print("  - Get workflows:                               done")


#------------------------------------------------------------------------------------------------------------------------------#


def get_workflow_xml_export():
    ''' XML for every workflow will be exported from the 'workFlow_nodes.txt' file. '''
    
    workflow_nodes: list = []    
    with open(f"{pwd}/files/workflow_nodes.txt", 'r', encoding='utf-8') as file:
        for line in file:
            workflow_nodes.append(line[:-1])
    
    for node in workflow_nodes:
        workFlow_data = read_from_json(f"{pwd}/files", node)

        for line in workFlow_data['workFlows']:
            url = f"{url_export}/api/Attachments/{line['attachmentId']}"
            request = requests.get(url, headers=headers_export, verify=False)  

            with open(f"{pwd}/files/{line['originalId']}.xml", 'wb') as file:
                file.write(request.content)

    print("  - Get workflows XML:                           done")

#------------------------------------------------------------------------------------------------------------------------------


def get_workFlowId_and_bimClassId_from_export_server():   # /api/WorkFlows/{workFlowOriginId}/BimClasses
    '''
        This function does mapping between workFlow_id and bimClass_id. 
        It uses list comprehension block for transformation list of values into dictionary with {'workFlow_id': 'bimClass_id'} pairs.
    '''

    workFlow_id_bimClass_id_export: list = []  # temp list to store data

    workflow_nodes: list = []   # append all workflow nodes from the workflow_nodes.txt
    if os.path.isfile(f"{pwd}/files/workflow_nodes.txt"):
        with open(f"{pwd}/files/workflow_nodes.txt", 'r', encoding='utf-8') as file:
            for line in file:
                workflow_nodes.append(line[:-1])    # it removes the last symbol, because 'workflow_nodes.txt' always has '\n' - newline, as a last symbol
    else:
        sys.exit("No workflow_nodes.txt file. Check files folder. Exit.")

    for node in workflow_nodes:

        workFlow_data = read_from_json(f"{pwd}/files", node)
        for line in workFlow_data['workFlows']:
                url = f"{url_export}/api/WorkFlows/{line['originalId']}/BimClasses"
                request = requests.get(url, headers=headers_export, verify=False)
                response = request.json()
                with open(f"{pwd}/files/{line['id']}.json", 'w', encoding='utf-8') as file:
                    json.dump(response, file, ensure_ascii=False, indent=4)

                # write list with active workFlows BimClasses ID in format [workFlow_id, bimClass_id]
                workFlow_id_bimClass_id_export.append(line['originalId'])
                workFlow_id_bimClass_id_export.append(response[0]['id'])
        

    # List comprehension block for transformation list of values into {'workFlow_id': 'bimClass_id'} pairs.
    tmp = workFlow_id_bimClass_id_export
    tmp: list = [ [tmp[x-1]] + [tmp[x]] for x in range(1, len(tmp), 2) ]      # generation list in format [ ['a', 'b'], ['c', 'd'], ['e', 'f'] ]
    workFlow_id_bimClass_id_export = dict(tmp)                                # transform tmp list from above to dictionary using dict() function in format {"workFlow_id": "bimClass_id"}
        

    with open(f"{pwd}/files/workFlow_id_bimClass_id_export.json", 'w', encoding='utf-8') as file:
        json.dump(workFlow_id_bimClass_id_export, file, ensure_ascii=False, indent=4)
    
    logging.info("Mapping between workflow_ID and bimClass_ID: done. 'workFlow_id_bimClass_id_export.json' file is ready.")
    print("  - Mapping between workflow_ID and bimClass_ID: done\n")
    print("================== Export procedure finished ==================\n")
    
    if sys.platform == 'win32':
        os.system('pause')

#------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------------------------------------------------#

define_procedure = input("Export(1) || Import(2): ").lower()

if define_procedure in ('1', 'export'):    
    create_folder_for_files_and_logs()
    url_export = get_url_export()
    headers_export = get_headers()
    workflow_node = define_workFlow_node_export()
    get_model_object_export()
    get_workflow_nodes_export()
    get_workflows_export()
    get_workflow_xml_export()   
    get_workFlowId_and_bimClassId_from_export_server()
elif define_procedure in ('2', 'import'):
    import import_data
        
else: print("Nothing was chosen. Exit.")
