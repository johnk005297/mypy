#
import json
import requests
from dotenv import load_dotenv
import os

load_dotenv()
url = "http://std-h5.dev.bimeister.io/api/Geometries/Statistics/Similar"

# headers = {'Accept': 'application/json'}
token = os.getenv("token")
headers = {'Authorization': f'Bearer {token}'}


response = requests.get(url, headers=headers)

print(response.json())



