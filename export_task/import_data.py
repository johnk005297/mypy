#
import requests
import json
import os
import export_data as ex      # Data from export_data.py 


'''     GLOBAL VARIABLES    '''
imported_workFlows: list = []       # workFlows of IMPORTED processes 

''''''''''''''''''''''''''''''

def get_workflow_nodes_import():   # Getting Draft, Archived and Active processes.
    
    url = ex.site_import_url + "/api/WorkFlowNodes"
    request = requests.get(url, headers=ex.headers_import)
    response = request.json()
        
    with open('workflow_nodes_import.json', 'w') as json_file:
        json.dump(response, json_file, ensure_ascii=False, indent=4)

    
    print("get_workflow_nodes_import - \033[;38;5;34mdone\033[0;0m")
    
#------------------------------------------------------------------------------------------------------------------------------#

## For future needs ##
def need_to_create():   # /api/WorkFlows/{workFlowOriginId}/BimClasses
    
    pass


#------------------------------------------------------------------------------------------------------------------------------#

def create_workflow_import():

    url = ex.site_import_url + "/api/WorkFlows"    
    
    data_workflows_export_server = ex.read_from_json('Draft_workflows_export.json')
    workflow_nodes_import = ex.read_from_json('workflow_nodes_import.json')     # Contains imported workflows
    
    for workflow in data_workflows_export_server['workFlows']:      
        payload = {
                    "name": workflow["name"],
                    "workFlowNodeId": workflow_nodes_import[0]['id'],    # 0: Draft; 1: Archived; 2: Active;
                    "description": str(workflow["description"]),
                    "elements": [],
                    "type": workflow["type"]
                    }
        json_payload = json.dumps(payload)

        request = requests.post(url, data=json_payload, headers=ex.headers_import)
        response = request.json()
        
        imported_workFlows.append(response)    
    
    print(f"create_workflow \033[;38;5;34mdone\033[0;0m" if request.status_code == 201 else f"create_workflow \033[;38;5;9m{request}\033[0;0m")
    
#------------------------------------------------------------------------------------------------------------------------------#


def get_workflows_import():    # Creating .json only Draft workFlows

    workflow_nodes_import = ex.read_from_json('workflow_nodes_import.json')  


    for obj in range(len(workflow_nodes_import)):
        if workflow_nodes_import[obj]['name'] == "Draft":
            draft_id = workflow_nodes_import[obj]['id']
            draft_name = workflow_nodes_import[obj]['name']           
    
    
    url = f"{ex.site_import_url}/api/WorkFlowNodes/{draft_id}/children"
    request = requests.get(url, headers=ex.headers_import)        
    response = request.json()

    with open(f"{draft_name}_workflows_import.json", 'w', encoding='utf-8') as json_file:
        json.dump(response, json_file, ensure_ascii=False, indent=4)

    print("get_workflows_import - \033[;38;5;34mdone\033[0;0m")

#------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------------------------------------------------#




if __name__ == "__main__":
    ex.create_folders()
    ex.get_workflow_nodes_export()
    ex.get_workflows_export()    
    ex.workflow_xml_export()     
    ex.get_workFlows_bimClass_export()
    get_workflow_nodes_import()
    create_workflow_import()
    get_workflows_import()
    



