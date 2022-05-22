#
from email import contentmanager
import json
import requests
from dotenv import load_dotenv
import os

load_dotenv()

def std_p7_call():

    token_std_p7 = os.getenv("token_std_p7")
    headers = {'Authorization': f"Bearer {token_std_p7}"}
    url_std_p7 = "http://std-p7.bimeister.io/api/Geometries/Statistics/Similar"
    # headers = {'Accept': 'application/json'}    
    
    response = requests.get(url_std_p7, headers=headers)

    return(response.headers)



def string_search():
    with open(r'C:\Users\ivan.kutuzov\YandexDisk\job_bimeister\BIM\sprints\94_local_deploy_lite.yml', 'r') as reader:
        content = reader.readlines()
        if 'db:' in content:
            print("YES!")
    
    
        
string_search()

