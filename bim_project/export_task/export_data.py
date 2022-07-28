#
# This is linux version script!

import requests
import json
import os
import xml.etree.ElementTree as ET
import sys
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
disable_warnings(InsecureRequestWarning)
# from dotenv import load_dotenv    # commented when running on linux machine which/if can't install load_dotenv package
# load_dotenv()





'''     GLOBAL VARIABLES    '''
pwd = os.getcwd()

''''''''''''''''''''''''''''''

def token_export_server():
    token_from_export_server = input("Enter Bearer token for export: ")
    print()
    return token_from_export_server


headers_export = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token_export_server()}"}

#------------------------------------------------------------------------------------------------------------------------------#



def get_url_export():
    
    export_site_url: str = input("Enter export server url, like('http://address.com'): ").lower()
    return export_site_url
#------------------------------------------------------------------------------------------------------------------------------#

def get_token():
    pass
    '''
        Need to create a function to get Bearer token
    '''


#------------------------------------------------------------------------------------------------------------------------------#

def create_folders():
    try:        
        os.mkdir('files')
    except FileExistsError:
        pass

    if os.path.isdir(f"{pwd}/files"):        
        print("create_folders - done")
    else:
        print("Folder 'files' wasn't created. Exit.")     
    
#------------------------------------------------------------------------------------------------------------------------------#


def define_workFlow_node_export():
    ''' 
        Function creates a file 'workflow_nodes.txt' with chosen workFlow nodes in it.
        And returns a tuple of elements like ("Active", "Active_workflows_export.json") which could be accessed by index. And 
        example: workflow_node[0] - "Active"    # workFlow node
                 workflow_node[1] - "Active_workflows_export.json"  # .json file with all the workFlows from the chosen node                 
    '''
    if os.path.isfile(f"{pwd}/files/workflow_nodes.txt") == False:
        with open(f"{pwd}/files/workflow_nodes.txt", mode='w',encoding='utf-8'): pass

    count = 0    
    while count < 3:
        workflow_node_select = input("\nWhat node to export? draft(1), archived(2), active(3)\nType 'q' for exit: ").lower().capitalize()        
        count += 1

        # workflow_node_select is a tuple with two values - directory and .json file
        if workflow_node_select in ('Draft', '1'):
            # workflow_node('Draft', 'Draft_workflows_export.json', 'draft')
            with open(f"{pwd}/files/workflow_nodes.txt", 'r+', encoding='utf-8') as file:                
                if "Draft_workflows_export_server.json" not in file.read():                   
                    file.write("Draft_workflows_export_server.json\n")                                
            return "Draft", "Draft_workflows_export_server.json"

        elif workflow_node_select in ('Archived', '2'):
            # workflow_node('Archived", 'Archived_workflows_export.json', 'archived')
            with open(f"{pwd}/files/workflow_nodes.txt", 'r+', encoding='utf-8') as file:
                if "Archived_workflows_export_server.json" not in file.read():                             
                    file.write("Archived_workflows_export_server.json\n")                
            return "Archived", "Archived_workflows_export_server.json"

        elif workflow_node_select in ('Active', '3'):
            # workflow_node('Active", 'Active_workflows_export.json', 'active'
            with open(f"{pwd}/files/workflow_nodes.txt", 'r+', encoding='utf-8') as file:
                if "Active_workflows_export_server.json" not in file.read():                
                    file.write("Active_workflows_export_server.json\n")                           
            return "Active", "Active_workflows_export_server.json"  

        elif count == 3 or workflow_node_select == 'Q':
            sys.exit("\nStop export process!")
        
                        

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


def get_workflow_nodes_export():       
    '''
        Getting Draft, Archived and Active nodes Ids.
    '''
    try:
        url = url_export + "/api/WorkFlowNodes"
        request = requests.get(url, headers=headers_export, verify=False)
        response = request.json()
    except Exception as err:
        print("No connection established.")
        print("Type:", type(err))
        print("Error:", err)      
        sys.exit()

    with open(f'{pwd}/files/workflow_nodes_export_server.json', 'w', encoding='utf-8') as json_file:
        json.dump(response, json_file, ensure_ascii=False, indent=4)  
    
    print("get_workflow_nodes_export - done")
    
#------------------------------------------------------------------------------------------------------------------------------#


def get_model_object_export():    
    ''' 
        Function gets model object from export server, and writes it in model_object_export_server.json file.
        /api/Integration/ObjectModel/Export  - api service
    '''
    ask_model_object = input("Shall we export object model? (Y/N): ").lower()

    if ask_model_object in ("yes", "y", "1"):

        url = url_export + "/api/Integration/ObjectModel/Export"
        request = requests.get(url, headers=headers_export, verify=False)
        response = request.json()

        with open(f"{pwd}/files/model_object_export_server.json", "w", encoding="utf-8") as json_file:
            json.dump(response, json_file, ensure_ascii=False, indent=4)


    elif ask_model_object in ("n", "no", "0"):
        pass
    else:
        print("No choice was made. Stop executing script!")
        sys.exit()
    
    
    print("get_model_object_export - done")


#------------------------------------------------------------------------------------------------------------------------------#


def get_workflows_export():
    '''
        Get all workFlows from the chosen node.
    '''
    data = read_from_json(f"{pwd}/files", "workflow_nodes_export_server.json")
    for obj in range(len(data)):
        key = data[obj]['name']
        value = data[obj]['id']
        
        url = f"{url_export}/api/WorkFlowNodes/{value}/children"
        request = requests.get(url, headers=headers_export, verify=False)
        response = request.json()

        with open(f"{pwd}/files/{key}_workflows_export_server.json", 'w', encoding='utf-8') as json_file:
            json.dump(response, json_file, ensure_ascii=False, indent=4)
    
    print("get_workflows_export - done")

#------------------------------------------------------------------------------------------------------------------------------#


def get_workflow_xml_export():    
    '''  
        XML will be exported from the workFlow_node based on input above - [Draft, Archived, Active]
        example: workflow_node('Archived", 'Archived_workflows_export.json')  - each element in tuple can be accessed by index
    '''
    
    workFlow_data = read_from_json(f"{pwd}/files", workflow_node[1])

    for line in workFlow_data['workFlows']:
        url = f"{url_export}/api/Attachments/{line['attachmentId']}"
        request = requests.get(url, headers=headers_export, verify=False)        
        with open(f"{pwd}/files/{line['originalId']}.xml", 'wb') as file:
            file.write(request.content)

    print("get_workflow_xml_export - done")

#------------------------------------------------------------------------------------------------------------------------------


def get_workFlowId_and_bimClassId_from_export_server():   # /api/WorkFlows/{workFlowOriginId}/BimClasses
    
    workFlow_id_bimClass_id_export: list = []  # temp list to get data
    '''
        This function does mapping between workFlow_id and bimClass_id. 
        It uses list comprehension block for transformation list of values into dictionary with {'workFlow_id': 'bimClass_id'} pairs.
    '''

    workflow_nodes: list = []
    if os.path.isfile(f"{pwd}/files/workflow_nodes.txt"):
        with open(f"{pwd}/files/workflow_nodes.txt", 'r', encoding='utf-8') as file:
            for line in file:
                workflow_nodes.append(line[:-1])
    else:
        print("No workflow_nodes.txt file. Check files folder. Exit.")
        sys.exit()
    

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
    workFlow_id_bimClass_id_export = dict(tmp)                          # transform tmp list from above to dictionary using dict() function in format {"workFlow_id": "bimClass_id"}
        

    with open(f"{pwd}/files/workFlow_id_bimClass_id_export.json", 'w', encoding='utf-8') as file:
        json.dump(workFlow_id_bimClass_id_export, file, ensure_ascii=False, indent=4)


    print("get_workFlows_bimClass_export - done\n\n")    
    os.system('pause')

#------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------------------------------------------------#



if __name__ == "__main__":    
    url_export = get_url_export()
    # get_token()   # function hasn't been written yet.    
    create_folders()
    get_model_object_export()
    workflow_node = define_workFlow_node_export()    
    get_workflow_nodes_export()    
    get_workflows_export()
    get_workflow_xml_export()   
    get_workFlowId_and_bimClassId_from_export_server()
    
