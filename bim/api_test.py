#
#
# 
import requests
import json
import os
from dotenv import load_dotenv
import xml.etree.ElementTree as ET



load_dotenv()
token_std_h5 = os.getenv("token_std_h5")
headers = {'accept': '*/*','Content-type':'application/json-patch+json', 'Authorization': f"Bearer {token_std_h5}"}

site_url: str = "http://std-h5.dev.bimeister.io"

'''
    List of global variables to access
'''
workflow_nodes: dict = {}               # dict of workFlow_nodes in format {"Name": "Id"}
draft_workflows: dict = {}              # dict of draft workFlows
archived_workflows: dict = {}           # dict of archived workFlows
active_workflows: dict = {}             # dict of active workFlows
draft_name_and_attachementId: dict = {}              
archived_name_and_attachementId: dict = {}
active_name_and_attachementId: dict = {}


def check_type(data):
    return type(data)
#------------------------------------------------------------------------------------------------------------------------------


def get_workflow_nodes():   # Getting Draft, Archived and Active processes.
    
    url = site_url + "/api/WorkFlowNodes"
    response = requests.get(url, headers=headers)
    data = response.json()

    # workflow_nodes: dict = {}   # dict of id_workflow_nodes
    for x in data:
        workflow_nodes[x['name']] = x['id']
    
    with open('workflow_nodes.json', 'w') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)  
    
    
    return workflow_nodes    # {'Draft': '8a30f7cc-907e-4415-bd90-fae2d4535361', 'Archived': '141c4c23-9067-4ec0-ae8c-2c954a73d1a6', 'Active': '1fb65c29-d79b-4ce7-9e31-84853f8abe92'}
#------------------------------------------------------------------------------------------------------------------------------




def get_workflows():    # Getting a list of processes id in three workflow_nodes.

    for key,value in workflow_nodes.items():      

        url = f"{site_url}/api/WorkFlowNodes/{value}/children"                    
        response = requests.get(url, headers=headers)
        data = response.json()      
        
        if key == 'Draft':
            for line in data:
                draft_workflows[line] = data[line]
        elif key == 'Archived':
            for line in data:
                archived_workflows[line] = data[line]
        elif key == 'Active':
            for line in data:
                active_workflows[line] = data[line]
        else:
            print('Smth is wrong! Exit')
            break        

        with open(f'{key}_workflows.json', 'w',encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
    
    
    return draft_workflows
#------------------------------------------------------------------------------------------------------------------------------



def get_attachement_id():
    
    
    # Collect attachment_ID of every process in dict format: {"process_name:" "Id"}
    list_of_workflow_nodes = [archived_workflows, draft_workflows, active_workflows]  # dictionaries with data already
    list_of_attachment_id = [archived_name_and_attachementId, draft_name_and_attachementId, active_name_and_attachementId]  # empty dictionaries so far
       
    try:
        # Create target Directory        
        os.mkdir('archive_xml')
        os.mkdir('draft_xml')
        os.mkdir('active_xml')      
          
    except FileExistsError:        
        pass

    for workflow in range(len(list_of_workflow_nodes)):        
        for elem in list_of_workflow_nodes[workflow]['workFlows']:            
            key = elem['name']
            value = elem['attachmentId']            
            list_of_attachment_id[workflow][key] = value

        for key,value in list_of_attachment_id[workflow].items():
            url = f"{site_url}/api/Attachments/{value}"
            response = requests.get(url, headers=headers)
            
            
        # saving the xml file
            if workflow == 0:            
                with open(f'{os.getcwd()}\\archive_xml\\{key}.xml', 'wb') as file:
                    file.write(response.content)
            elif workflow == 1:
                with open(f'{os.getcwd()}\\draft_xml\\{key}.xml', 'wb') as file:
                    file.write(response.content)
            elif workflow == 2:
                with open(f'{os.getcwd()}\\active_xml\\{key}.xml', 'wb') as file:
                    file.write(response.content)

    

#------------------------------------------------------------------------------------------------------------------------------




''' NEED TO FINISH THIS FUNC'''

def get_bimClasses():   # Getting a list of ID's: "Draft", "Archived" and "Active" processes.
    
    url = site_url + "/api/WorkFlows/f8309244-cff2-4a42-9171-d87ed6e1bb64/BimClasses"
    response = requests.get(url, headers=headers)   
    data = response.json()

    

#------------------------------------------------------------------------------------------------------------------------------



def read_from_json(file_name):    
    
    file_name += '.json' if file_name[-5:] != '.json' else file_name

    with open(file_name, 'r', encoding='utf-8') as file:
        data_from_json = json.load(file)
    
    return data_from_json

#------------------------------------------------------------------------------------------------------------------------------



def create_workflow():

    url = site_url + "/api/WorkFlows"
    
    data = read_from_json('workflow_nodes')    
    payload = {
                "name": "Crash test",
                "workFlowNodeId": data[0]['id'], # 0: Draft; 1: Archived; 2: Active;
                "description": "test req",
                "elements": [],
                "type": "Task"
                }    
    json_payload = json.dumps(payload)        
    
    response = requests.post(url, data=json_payload, headers=headers)
    print(response.status_code)
    
#------------------------------------------------------------------------------------------------------------------------------



############################## IMPORT #####################################
'''
URL for workflow with *.xml file:
    http://std-h5.dev.bimeister.io/api/WorkFlows/3c088ed3-6386-4b99-8d13-1a397e79ce5e/Diagram?contentType=file
'''

def import_workflow():  ## Need to fix. Not working!

    url = "http://std-h5.dev.bimeister.io/api/WorkFlows/cfbf150e-21d0-4534-899c-a52a0d685e64/Diagram"
    
    read_xml = os.getcwd() + "\\" + "exportedWorkflow.xml"
    payload={}
    # files=[ ('file',('exportedWorkflow.xml',open('C:\Users\ivan.kutuzov\Downloads\exportedWorkflow.xml','rb'),'text/xml')) ]    
    
    with open(read_xml, 'r', encoding='utf-8') as xml:        
        response = requests.post(url, headers=headers, data=xml)   # Original from Postman
    # response = requests.post(url, headers=headers, data=payload, files=files)
    print(response.text)
    


#########################################################################################################


if __name__ == "__main__":    
    get_workflow_nodes()
    get_workflows()
    get_attachement_id()     
    # get_bimClasses()
    # read_from_json(file.json)
    create_workflow()    
    # import_workflow()
    


    
    
    
        


