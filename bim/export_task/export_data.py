#

import requests
import json
import os
from dotenv import load_dotenv
import xml.etree.ElementTree as ET


load_dotenv()
token_std_h5 = os.getenv("token_std_h5")
token_study = os.getenv("token_study")


headers_export = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token_std_h5}"}
headers_import = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token_study}"}
headers_for_xml_import = {'accept': '*/*', 'Authorization': f"Bearer {token_study}"}


site_export_url: str = "http://std-h5.dev.bimeister.io"
site_import_url: str = "http://study.bimeister.io"


'''     GLOBAL VARIABLES    '''
pwd = os.getcwd()
bimClass_id_draft_workFlows_export: dict = {}

''''''''''''''''''''''''''''''

#------------------------------------------------------------------------------------------------------------------------------#
def check_type(data):
    print(type(data))
#------------------------------------------------------------------------------------------------------------------------------#
def create_folders():
    try:            
        os.mkdir('Archived')
        os.mkdir('Draft')
        os.mkdir('Active')

    except FileExistsError:        
        pass
    print("create_folders - \033[;38;5;34mdone\033[0;0m")
#------------------------------------------------------------------------------------------------------------------------------#

def define_workFlow_node():
    workflow_node_select = input("\nWhat node to export[draft, archived, active]?\nType q for exit: ")
    
    # workflow_node_select is a tuple with two values - directory and .json file
    if workflow_node_select == 'draft':
        # workflow_node('Draft', 'Draft_workflows_export.json', 'draft')        
        return "\\\\Draft", 'Draft_workflows_export.json', 'draft'

    elif workflow_node_select == 'archived':
        # workflow_node('Archived", 'Archived_workflows_export.json', 'archived')        
        return "\\\\Archived", 'Archived_workflows_export.json', 'archived' 

    elif workflow_node_select == 'active':
        # workflow_node('Active", 'Active_workflows_export.json', 'active'               
        return "\\\\Active", 'Active_workflows_export.json', 'active'

    elif workflow_node_select == 'q':
        print("\nStop import process!")
        return


# Read from JSON files, and dict in return. pwd - current working directory
# Need to pass two arguments in str: path and file name
def read_from_json(path_to_file,file_name):
    
    if file_name[-5:] == '.json':
        pass
    else: file_name += '.json'
    with open(f'{path_to_file}\\{file_name}', 'r', encoding='utf-8') as file:
        data_from_json = json.load(file)
    
    return data_from_json

#------------------------------------------------------------------------------------------------------------------------------#


def get_workflow_nodes_export():   # Getting Draft, Archived and Active processes.    
    
    url = site_export_url + "/api/WorkFlowNodes"
    request = requests.get(url, headers=headers_export)
    response = request.json()
        
    with open('workflow_nodes_export.json', 'w') as json_file:
        json.dump(response, json_file, ensure_ascii=False, indent=4)  
    
    print("get_workflow_nodes_export - \033[;38;5;34mdone\033[0;0m")    
    
#------------------------------------------------------------------------------------------------------------------------------#


def get_workflows_export():    

    data = read_from_json(pwd, 'workflow_nodes_export.json')
    for obj in range(len(data)):
        key = data[obj]['name']
        value = data[obj]['id']

        url = f"{site_export_url}/api/WorkFlowNodes/{value}/children"
        request = requests.get(url, headers=headers_export)        
        response = request.json()

        with open(f"{pwd}\{key}\{key}_workflows_export.json", 'w', encoding='utf-8') as json_file:
            json.dump(response, json_file, ensure_ascii=False, indent=4)

    print("get_workflows_export - \033[;38;5;34mdone\033[0;0m")

#------------------------------------------------------------------------------------------------------------------------------#


def workflow_xml_export():
    
    '''  XML will be exported from the workFlow_node based on input above - [draft, archived, active]  
         example: workflow_node('\\Archived", 'Archived_workflows_export.json', 'archived')  - each element in tuple can be accessed by index
    '''
    
    if workflow_node[2] == 'draft':                
        draft_workFlows_export = read_from_json(f'{pwd}{workflow_node[0]}', workflow_node[1])
        for line in draft_workFlows_export['workFlows']:
            url = f"{site_export_url}/api/Attachments/{line['attachmentId']}"
            request = requests.get(url, headers=headers_export)        
            with open(f"{pwd}{workflow_node[0]}\\{line['originalId']}.xml", 'wb') as file:
                file.write(request.content)
    
    elif workflow_node[2] == 'archived':        
        archived_workFlows_export = read_from_json(f'{pwd}{workflow_node[0]}', workflow_node[1])
        for line in archived_workFlows_export['workFlows']:
            url = f"{site_export_url}/api/Attachments/{line['attachmentId']}"
            request = requests.get(url, headers=headers_export)        
            with open(f"{pwd}{workflow_node[0]}\\{line['originalId']}.xml", 'wb') as file:
                file.write(request.content)
    
    elif workflow_node[2] == 'active':        
        active_workFlows_export = read_from_json(f'{pwd}{workflow_node[0]}', workflow_node[1])
        for line in active_workFlows_export['workFlows']:
            url = f"{site_export_url}/api/Attachments/{line['attachmentId']}"
            request = requests.get(url, headers=headers_export)        
            with open(f"{pwd}{workflow_node[0]}\\{line['originalId']}.xml", 'wb') as file:  
                file.write(request.content)


    print("workflow_xml_export - \033[;38;5;34mdone\033[0;0m")

#------------------------------------------------------------------------------------------------------------------------------


def get_workFlows_bimClass_export():   # /api/WorkFlows/{workFlowOriginId}/BimClasses
    
    workFlow_id_bimClass_id_export: list = []  # temp list to get data

    '''  XML will be exported from the workFlow_node based on input above - [draft, archived, active]  
         example: workflow_node('\\Archived', 'Archived_workflows_export.json', 'archived')  - each element in tuple can be accessed by index
    '''
    
    if workflow_node[2] == 'draft':
        draft_workFlows_export = read_from_json(f'{pwd}{workflow_node[0]}', {workflow_node[1]})
        for line in draft_workFlows_export['workFlows']:
            url = f"{site_export_url}/api/WorkFlows/{line['originalId']}/BimClasses"
            request = requests.get(url, headers=headers_export)
            response = request.json()            
            with open(f"{pwd}{workflow_node[0]}\\{line['id']}.json", 'w', encoding='utf-8') as file:
                json.dump(response, file, ensure_ascii=False, indent=4)

    # write dict with draft workFlows BimClasses ID in format {"workFlow_name": "bimClass_ID"}        
        workFlow_id_bimClass_id_export.append(line['originalId'])        
        workFlow_id_bimClass_id_export.append(response[0]['id'])
    
    elif workflow_node[2] == 'archived':
        archived_workFlows_export = read_from_json(f'{pwd}{workflow_node[0]}', {workflow_node[1]})
        for line in archived_workFlows_export['workFlows']:
            url = f"{site_export_url}/api/WorkFlows/{line['originalId']}/BimClasses"
            request = requests.get(url, headers=headers_export)
            response = request.json()
            with open(f"{pwd}{workflow_node[0]}\\{line['id']}.json", 'w', encoding='utf-8') as file:
                json.dump(response, file, ensure_ascii=False, indent=4)
            
            # write dict with draft workFlows BimClasses ID in format {"workFlow_name": "bimClass_ID"}        
            workFlow_id_bimClass_id_export.append(line['originalId'])        
            workFlow_id_bimClass_id_export.append(response[0]['id'])

    elif workflow_node[2] == 'active':
        active_workFlows_export = read_from_json(f'{pwd}{workflow_node[0]}', {workflow_node[1]})
        for line in active_workFlows_export['workFlows']:
            url = f"{site_export_url}/api/WorkFlows/{line['originalId']}/BimClasses"
            request = requests.get(url, headers=headers_export)
            response = request.json()
            with open(f"{pwd}{workflow_node[0]}\\{line['id']}.json", 'w', encoding='utf-8') as file:
                json.dump(response, file, ensure_ascii=False, indent=4)   
            
            # write dict with draft workFlows BimClasses ID in format {"workFlow_name": "bimClass_ID"}
            workFlow_id_bimClass_id_export.append(line['originalId'])        
            workFlow_id_bimClass_id_export.append(response[0]['id'])


    # List comprehension block for transformation list of values into {'workFlow_id': 'bimClass_id'} pairs.
    b = workFlow_id_bimClass_id_export
    b: list = [ [b[x-1]] + [b[x]] for x in range(1, len(b), 2) ]      # generation list in format [ ['a', 'b'], ['c', 'd'], ['e', 'f'] ]
    workFlow_id_bimClass_id_export = dict(b)                          # transform b list from above to dictionary using dict() function in format {"workFlow_id": "bimClass_id"}
    
    with open("workFlow_id_bimClass_id_export.json", 'w', encoding='utf-8')as file:
        json.dump(workFlow_id_bimClass_id_export, file, ensure_ascii=False, indent=4)


    print("get_workFlows_bimClass_export - \033[;38;5;34mdone\033[0;0m")
    

#------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------------------------------------------------#



if __name__ == "__main__":
    workflow_node = define_workFlow_node()
    create_folders()
    get_workflow_nodes_export()
    get_workflows_export()    
    workflow_xml_export()     
    # get_workFlows_bimClass_export()
    
    
    


