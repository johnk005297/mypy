#
import requests
import json
import os
import export_data as ex      # Data from export_data.py 


'''     GLOBAL VARIABLES    '''


''''''''''''''''''''''''''''''

def get_workflow_nodes_import():   # Getting Draft, Archived and Active processes.
    
    url = ex.site_import_url + "/api/WorkFlowNodes"
    request = requests.get(url, headers=ex.headers_import)
    response = request.json()
        
    with open('workflow_nodes_import.json', 'w') as json_file:
        json.dump(response, json_file, ensure_ascii=False, indent=4)

    
    print("get_workflow_nodes_import - \033[;38;5;34mdone\033[0;0m")
    
#------------------------------------------------------------------------------------------------------------------------------#
'''  TEST BLOCK  '''

## For future needs ##
def to_do():   # /api/WorkFlows/{workFlowOriginId}/BimClasses
    check = ex.read_from_json(f'{ex.pwd}\\draft_json', 'Арина_bimClass.json')
    print(check[0]['id'])



def replace_str_in_file(file_in, file_out, find, replace):
    '''   THE FIRTS WAY   '''
    
    # fin = open("Draft_workflows_export.json", "rt", encoding='utf-8')   #input file    
    # fout = open("changed.json", "wt", encoding='utf-8') #output file to write the result to    
    # for line in fin:    #for each line in the input file         
    #     fout.write(line.replace(find, replace))       # find, replace vars must be string
    # fin.close()
    # fout.close()
    
    '''   THE SECOND WAY   '''
    with open(f"{file_in}", 'r', encoding='utf-8') as file:
        new_json = file.read().replace(find, replace)      # find, replace vars must be string
    with open(f"{file_out}", 'w', encoding='utf-8') as file:
        file.write(new_json)
        


'''   END OF TEST BLOCK     '''
#------------------------------------------------------------------------------------------------------------------------------#

# data takes {workFlowOriginId} as an argument
def get_BimClassID_of_current_process_import(data):  # /api/WorkFlows/{workFlowOriginId}/BimClasses
    
    url = f"{ex.site_import_url}/api/WorkFlows/{data}/BimClasses"
    request = requests.get(url, headers=ex.headers_import)
    response = request.json()

    return response[0]['id']

#------------------------------------------------------------------------------------------------------------------------------#



def create_workflow_import():

    url = ex.site_import_url + "/api/WorkFlows"    
    
    draft_workflows_export_server = ex.read_from_json(ex.pwd,'Draft_workflows_export.json')
    workflow_nodes_import = ex.read_from_json(ex.pwd,'workflow_nodes_import.json')     # Contains imported workflows
    
    for workflow in draft_workflows_export_server['workFlows']:      
        payload = {
                    "name": workflow["name"],
                    "workFlowNodeId": workflow_nodes_import[0]['id'],    # 0: Draft; 1: Archived; 2: Active;
                    "description": str(workflow["description"]),
                    "elements": [],
                    "type": workflow["type"]
                    }
        json_payload = json.dumps(payload)
        post_request = requests.post(url, data=json_payload, headers=ex.headers_import)
        response = post_request.json()     
        bimClass_id_import = get_BimClassID_of_current_process_import(response['originalId'])    # reference workFlow_original_ID
        bimClass_id_export = ex.read_from_json(ex.pwd, 'bimClass_id_draft_workFlows_export.json')
        print(bimClass_id_export[workflow]['name'])
        print(workflow['name'])
        
        # replace_str_in_file('Draft_workflows_export.json', 'Draft_workflows_changed.json', find, bimClass_id_import)
        
        break
    return
        
        
    
    print(f"create_workflow \033[;38;5;34mdone\033[0;0m" if post_request.status_code == 201 else f"create_workflow \033[;38;5;9m{request}\033[0;0m")
    
#------------------------------------------------------------------------------------------------------------------------------#


def get_workflows_import():    # Creating .json only Draft workFlows

    workflow_nodes_import = ex.read_from_json(ex.pwd,'workflow_nodes_import.json')  


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
    # ex.create_folders()
    # ex.get_workflow_nodes_export()
    # ex.get_workflows_export()    
    # ex.workflow_xml_export()     
    # ex.get_workFlows_bimClass_export()
    # get_workflow_nodes_import()
    create_workflow_import()
    # get_workflows_import()
    # to_do()
    # replace_str_in_file()


