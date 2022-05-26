#


from importlib.resources import path
from itertools import count
import json
import requests
from dotenv import load_dotenv
import os
import re

load_dotenv()

def std_p7_call():

    token_std_p7 = os.getenv("token_std_p7")
    headers = {'Authorization': f"Bearer {token_std_p7}"}
    url_std_p7 = "http://std-p7.bimeister.io/api/Geometries/Statistics/Similar"
    # headers = {'Accept': 'application/json'}    
    
    response = requests.get(url_std_p7, headers=headers)

    return(response.headers)



def string_search():

    # lst: list = []
    s = str()
    path_to_file = r'C:\Users\ivan.kutuzov\Desktop\docker-compose.yml'
    
    with open(path_to_file, 'r') as reader:
        s = reader.read()
    with open(path_to_file, 'r') as reader:
        lst = reader.readlines()
    
    l = s.split()
    
    # for line in range(len(l)):
    #     if re.search(r"^db:", l[line]):
    #         l.insert(line + 1, 'ports:\n- "0.0.0.0:5432:5432"')

    with open(path_to_file, 'w') as f:
        for line in s.split():
            
            if re.search(r"^db:", line):
                print(line+1)
                break
                f.write("%s\n" % line.replace('db:', 'db:\n ports:\n   - "5432:5432"'))
            elif re.search(r"^minio:", line):
                f.write("%s\n" % line.replace('minio:', 'minio:\n ports:\n   - "9000:9000"'))
            elif re.search(r"^auth:", line):                
                f.write("%s\n" % line.replace('auth:', 'auth:\n ports:\n   - "5000:80"'))
            elif re.search(r"^authdb:", line):                
                f.write("%s\n" % line.replace('auth:', 'auth:\n ports:\n   - "5433:5432"'))           
            else:
                f.write("%s\n" % line)

    
    
    
    
    # for line in data:
    #     if re.search(r"\s+db:", line):
    #         print(line)

    
    
    
        
string_search()

