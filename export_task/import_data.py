#
import requests
import json
import os
import export_data as ex      # Data from export_data.py 
import xml.etree.ElementTree as ET
import time



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


def replace_str_in_file(file_in, file_out, find, replace):  # Need for bimClass_id replacement. From workFlows_export_server to workFlows_import_server

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

    url = ex.site_import_url + "/api/WorkFlows"
     
    
    draft_workflows_export_server = ex.read_from_json(ex.pwd,'Draft_workflows_export.json')
    workflow_nodes_import = ex.read_from_json(ex.pwd,'workflow_nodes_import.json')     # Contains imported workflows    
    
    for workflow in draft_workflows_export_server['workFlows']:      
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
        bimClass_list_id_export = ex.read_from_json(ex.pwd, 'bimClass_id_draft_workFlows_export.json')      
        
        # replacing bimClass_ID in 'Draft_workflows_export.json' with bimClass_ID newly created workFlow
        replace_str_in_file('Draft_workflows_export.json', 'Draft_workflows_export.json', bimClass_list_id_export[workflow["originalId"]], bimClass_id_import)      
        time.sleep(0.5)
                
        # for workflow in draft_workflows_export_server['workFlows']:    
        put_payload = {
                        "name": workflow["name"],
                        "workFlowNodeId": workflow_nodes_import[0]['id'],    # 0: Draft; 1: Archived; 2: Active;
                        "description": str(workflow["description"]),
                        "elements": workflow['elements'],
                        "type": workflow["type"]
                        }
        json_put_payload = json.dumps(put_payload)

        # Replacement of workFlow_bimClass_ID from export server to workFlow_bimClass_ID on import server
        changed_put_payload = json_put_payload.replace(bimClass_list_id_export[workflow["originalId"]], bimClass_id_import)

        requests.put(url+"/"+post_response['originalId'], data=changed_put_payload, headers=ex.headers_import)   # /api/WorkFlows/{workFlowOriginalId}  

        '''  BEGIN OF XML POST REQUEST'''
       
        # xml_path = ex.pwd+"\\draft_xml"           
        # # for file in os.listdir(xml_path):
        # #     if file[:-4] == workflow['name']:
        # #         my_xml = file
        # # with open(f'{xml_path}\\{workflow["name"]}.xml', 'rb') as file: 
        # #     xml_file = file.read() # Записываем содержимое в переменную       
            
        # payload={}
        # files=[
        #         ('file',(f'{workflow["name"]}.xml',open(f'{xml_path}\\{workflow["name"]}.xml','rb'),'text/xml'))
        #         ]
        # post_xml_request = requests.post(f"{url}/{post_response['originalId']}/Diagram?contentType=file", headers=ex.headers_import, data=payload, files=files)
        # post_xml_response = post_xml_request.json()

        '''  END OF XML POST REQUEST'''         
    
    print(f"create_workflow \033[;38;5;34mdone\033[0;0m" if post_request.status_code == 201 else f"create_workflow \033[;38;5;9m{post_request.status_code}\033[0;0m")
    
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
    ex.create_folders()
    ex.get_workflow_nodes_export()
    ex.get_workflows_export()    
    ex.workflow_xml_export()     
    ex.get_workFlows_bimClass_export()
    get_workflow_nodes_import()
    create_workflow_import()    
    get_workflows_import()
    
    


