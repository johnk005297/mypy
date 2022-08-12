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
    print()
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

    for dct in get_license():
        if dct['isActive'] == True and dct['licenseID'] != '00000000-0000-0000-0000-000000000000':
            url = f"{data_for_connect['url']}/api/License/{dct['licenseID']}" 
            request = requests.delete(url, headers=headers, verify=False)
            # response = request.text
            if request.status_code == 204:
                print(f"License has been deactivated: {dct['licenseID']}")
            else:
                print(request.status_code)



def post_license():

    headers = {'accept': 'text/plane', 'Content-Type': 'application/json-patch+json', 'Authorization': f"Bearer {token}"}
    url = f"{data_for_connect['url']}/api/License/"

    data = json.dumps(data_for_connect['license_token'])

    request = requests.post(url, headers=headers, data=data, verify=False)
    if request.status_code == 200:
        print("License has been posted!")
    else:
        print("License has not been posted!")



def put_license():
    
    headers = {'accept': '*/*', 'Content-type': 'text/plane', 'Authorization': f"Bearer {token}"}

    # {'isActive': True, 'serverId': '6e71c225-bb65-4ff7-b831-bc0d1894396b', 'licenseID': '309d6c41-1f4b-41b2-938d-b2069e54b12a', 'until': '2022-08-25T23:59:59', 'activeUsers': 1, 'activeUsersLimit': 1500}
    for dct in get_license():
        if dct['isActive'] == True:
            url = f"{data_for_connect['url']}/api/License/active/{dct['licenseID']}"
            data = json.dumps('no_need_to_put_anything')
            request = requests.put(url, headers=headers, data=data, verify=False)
            if request.status_code == 204:
                print(f"License has been activated: {dct['licenseID']}")
            else:
                print(f"License has not been activated: {dct['licenseID']}")            
            break

    

# http://192.168.87.66
# http://std-p7.bimeister.io
# https://bim-class.bimeister.io
# Qwerty12345!

if __name__ == "__main__":
    data_for_connect = creds()
    token = get_token()
    delete_license()
    post_license()
    put_license()
