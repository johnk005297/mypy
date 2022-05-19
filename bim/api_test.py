#
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

    print(response.json())