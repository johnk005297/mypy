##
'''
    Script for license activation on the server
'''
import os
import json
import requests
import sys
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
disable_warnings(InsecureRequestWarning)
import logging


pwd = os.getcwd()




def creds():

    logging.basicConfig(filename=f"{pwd}/license_log.txt", level=logging.DEBUG,
                        format="%(asctime)s %(levelname)s - %(message)s", filemode="w", datefmt='%d-%b-%y %H:%M:%S')

    # Check if the *.lic file is in place
    if os.path.isfile(f"{pwd}/license.lic"):    
        with open("license.lic", "r", encoding="utf-8") as file:        
            license_token = file.read().split()[0].strip("\"")
    else:
        sys.exit("No .lic file in the folder. Exit.")


    url = input("Enter URL: ").lower()
    if url[-1:] == '/':
        url = url[:-1]
    else: pass

    username = input("Enter login: ")
    password = input("Enter password: ")
    data_for_connect: dict = {
                    "url": url,
                    "username": username,
                    "password": password,
                    "license_token": license_token
                  }

    return data_for_connect



'''  Get bearer token from the server   '''
def get_token():

    list_of_providersID: list = []
    headers = {'accept': '*/*', 'Content-type':'application/json; charset=utf-8'}
    url_get_providers = f"{data_for_connect['url']}/api/Providers"

    
    id_request = requests.get(url_get_providers, headers=headers, verify=False)
    response = id_request.json() 

    for dict in response:
        list_of_providersID.append(dict['id'])

    url_auth = f"{data_for_connect['url']}/api/Auth/Login"

    for id in list_of_providersID:
        payload = {
                    "username": data_for_connect['username'],
                    "password": data_for_connect['password'],
                    "providerId": id
                }
        data = json.dumps(payload)
    
        auth_request = requests.post(url_auth, data=data, headers=headers, verify=False)
        response = auth_request.json()

        if auth_request.status_code == 200:
            token = response['access_token']
            break
        else:
            logging.error("%s", auth_request.status_code)
            continue

    return token


'''   Get the list of licenses   '''
def get_license():
    
    url = f"{data_for_connect['url']}/api/License"
    headers = {'Content-type':'text/plane', 'Authorization': f"Bearer {token}"}
    payload = {
                "username": data_for_connect['username'],
                "password": data_for_connect['password']
              }
    
    request = requests.get(url, data=payload, headers=headers, verify=False)
    request.raise_for_status()

    # response is a list of dictionaries with a set of keys: 'isActive', 'serverId', 'licenseID', 'until', 'activeUsers', 'activeUsersLimit'
    response = request.json()    
    return response



'''   Delete active license, if there is one.   '''
def delete_license():

    headers = {'accept': '*/*', 'Content-type': 'text/plane', 'Authorization': f"Bearer {token}"}

    for dct in server_data:
        if dct['isActive'] == True:
            url = f"{data_for_connect['url']}/api/License/{dct['licenseID']}" 
            request = requests.delete(url, headers=headers, verify=False)
            response = request.text
            if request.status_code == 204:
                print('License has been deactivated')
                return dct['licenseID']
            else:
                print(request.status_code)



def post_license():

    headers = {'accept': 'text/plane', 'Content-Type': 'application/json-patch+json', 'Authorization': f"Bearer {token}"}
    url = f"{data_for_connect['url']}/api/License/"

    data = json.dumps(data_for_connect['license_token'])

    request = requests.post(url, headers=headers, data=data, verify=False)
    print(request.status_code)


# http://192.168.87.66
# http://std-p7.bimeister.io
# https://bim-class.bimeister.io
# Qwerty12345!

if __name__ == "__main__":
    data_for_connect = creds()
    token = get_token()
    server_data = get_license()
    # for x in server_data:
    #     print(x)
    delete_license()
    # post_license()