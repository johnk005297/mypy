#
import requests
import json
import export_data as ex      # Data from export_data.py 
import xml.etree.ElementTree as ET
import time
import sys


'''     GLOBAL VARIABLES    '''


''''''''''''''''''''''''''''''

def get_workflow_nodes_import():   # Getting Draft, Archived and Active processes.
    
    url = ex.site_import_url + "/api/WorkFlowNodes"
    request = requests.get(url, headers=ex.headers_import)
    response = request.json()
        
    with open('workflow_nodes_import_server.json', 'w') as json_file:
        json.dump(response, json_file, ensure_ascii=False, indent=4)   
    print("get_workflow_nodes_import - \033[;38;5;34mdone\033[0;0m")
    
#------------------------------------------------------------------------------------------------------------------------------#

# Function needs for work on line replacement in files
def replace_str_in_file(file_in, file_out, find, replace):    
   
    with open(f"{file_in}", 'r', encoding='utf-8') as file:
        new_json = file.read().replace(find, replace)      # find, replace vars must be string
    with open(f"{file_out}", 'w', encoding='utf-8') as file:
        file.write(new_json)
        
#------------------------------------------------------------------------------------------------------------------------------#


# data takes {workFlowOriginId} as an argument
def get_BimClassID_of_current_process_import(data):  # /api/WorkFlows/{workFlowOriginId}/BimClasses
    
    url = f"{ex.site_import_url}/api/WorkFlows/{data}/BimClasses"
    request = requests.get(url, headers=ex.headers_import)
    response = request.json()    
    for object in range(len(response)):
        return response[object]['id']
    

#------------------------------------------------------------------------------------------------------------------------------#


def create_workflow_import():

    url = ex.site_import_url + "/api/WorkFlows"  # POST request to create workFlow
    '''
    workflow_node tuple comes from ex.define_workFlow_node() function. It provides a selection of three components ex.("\\Draft", "Draft_workflows_export.json", "draft")
    which can be accessed by index.
       example:  workflow_node[0] - "\\Draft"
                 workflow_node[1] - "Draft_workflows_export.json"
                 workflow_node[2] - "active"
    '''
    
    workflows_export_server = ex.read_from_json(f'{ex.pwd}{ex.workflow_node[0]}',ex.workflow_node[1])    
    workflow_nodes_import = ex.read_from_json(ex.pwd,'workflow_nodes_import_server.json')     # Contains imported workflows    
    
    '''  BEGIN of POST request to create workFlows  '''
    for workflow in workflows_export_server['workFlows']:
        post_payload = {
                        "name": workflow["name"],
                        "workFlowNodeId": workflow_nodes_import[0]['id'],    # 0: Draft; 1: Archived; 2: Active;
                        "description": str(workflow["description"]),
                        "elements": [],
                        "type": workflow["type"]
                        }
        json_post_payload = json.dumps(post_payload)
        post_request = requests.post(url, data=json_post_payload, headers=ex.headers_import)     # /api/WorkFlows/{workFlowOriginalId}
        post_response = post_request.json()
        
        bimClass_id_import = get_BimClassID_of_current_process_import(post_response['originalId'])    # reference workFlow_original_ID on import server        
        bimClass_list_id_export = ex.read_from_json(ex.pwd, 'workFlow_id_bimClass_id_export.json')                 
        time.sleep(0.25)
        '''  END of POST request  '''
        
        '''  BEGIN OF PUT REQUEST  
            adding 'elements': [], data from workFlows export into newly created workFlow
        '''            
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
        requests.put(url+"/"+post_response['originalId'], data=changed_put_payload, headers=ex.headers_import)   # /api/WorkFlows/{workFlowOriginalId}  
        time.sleep(0.25)
        '''  END OF PUT REQUEST  '''
        

        '''  BEGIN OF XML POST REQUEST  '''      
        xml_path = ex.pwd + ex.workflow_node[0]

        payload={}
        files=[ ('file',(f'{workflow["originalId"]}.xml',open(f'{xml_path}\\{workflow["originalId"]}.xml','rb'),'text/xml'))  ]
                        
        post_xml_request = requests.post(f"{url}/{post_response['originalId']}/Diagram?contentType=file", headers=ex.headers_for_xml_import, data=payload, files=files)
        # print(f"{post_xml_request.status_code}")
        print(f"Name of process: {post_response['name']}",end=' ')
        print(f"\033[;38;5;34m{post_xml_request.status_code}\033[0;0m" if post_xml_request.status_code == 200 else f"\033[;38;5;9m{post_xml_request.status_code}\033[0;0m")
        time.sleep(0.25)
        '''  END OF XML POST REQUEST  '''
    
    print(f"create_workflow - \033[;38;5;34mdone\033[0;0m" if post_request.status_code == 201 else f"create_workflow - \033[;38;5;9m{post_request.status_code}\033[0;0m")
    
#------------------------------------------------------------------------------------------------------------------------------#



def get_workflows_import():    # Creating .json only Draft workFlows

    # workflow_nodes_import = ex.read_from_json(ex.pwd,'workflow_nodes_import_server.json')
    data = ex.read_from_json(ex.pwd, 'workflow_nodes_export_server.json')
    for obj in range(len(data)):
        key = data[obj]['name']
        value = data[obj]['id']
            
        url = f"{ex.site_import_url}/api/WorkFlowNodes/{value}/children"
        request = requests.get(url, headers=ex.headers_import)        
        response = request.json()

        with open(f"{ex.pwd}\{key}\{key}_workflows_import_server.json", 'w', encoding='utf-8') as json_file:
            json.dump(response, json_file, ensure_ascii=False, indent=4)


    print("get_workflows_import - \033[;38;5;34mdone\033[0;0m")

#------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------------------------------------------------#


if __name__ == "__main__":
    ex.create_folders()
    ex.workflow_node = ex.define_workFlow_node()
    ex.get_workflow_nodes_export()
    ex.get_workflows_export()    
    ex.workflow_xml_export()     
    ex.get_workFlows_bimClass_export()
    get_workflow_nodes_import()
    create_workflow_import()    
    get_workflows_import()

