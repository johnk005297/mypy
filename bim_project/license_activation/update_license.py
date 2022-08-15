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


'''   Global variables   '''
pwd = os.getcwd()
possible_request_errors: tuple = (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout, 
                                      requests.exceptions.HTTPError, requests.exceptions.InvalidHeader, requests.exceptions.InvalidURL,)
''''''''''''''''''''''''''''''''


def define_purpose():
    
    purpose = input("\nCheck the licenses(1) || Get server ID(2) || Apply license(3) || Delete active license(4) || Exit(q)\nSelect one of the options: ").lower()
    if purpose in ("1", "check",):
        return 'check'
    elif purpose in ("3", "update", "apply"):
        return 'update'
    elif purpose in ("4", "delete"):
        return 'delete'
    elif purpose in ("2", "id"):
        return 'server_id'
    else:
        sys.exit("Exit.")

def get_data_from_license_file():

    data_from_lic_file: dict = {}

    # Check if the *.lic file is in place
    if os.path.isfile(f"{pwd}/license.lic"):

        with open("license.lic", "r", encoding="utf-8") as file:    # get license_token from the .lic file and put it into data_from_lic_file dictionary
            data_from_lic_file['license_token'] = file.read().split()[0].strip("\"")
            
        return data_from_lic_file
    
    else:
        logging.error("No license.lic file in the folder. Exit.")
        sys.exit("No license.lic file in the folder. Exit.")


def creds():

    logging.basicConfig(filename=f"{pwd}/license_log.txt", level=logging.DEBUG,
                        format="%(asctime)s %(levelname)s - %(message)s", filemode="w", datefmt='%d-%b-%y %H:%M:%S')


    url = input("\nEnter URL: ").lower()
    if url[-1:] == '/':
        url = url[:-1]
    else: pass

    username = input("Enter login: ")
    password = input("Enter password: ")
    data_for_connect: dict = {
                    "url": url,
                    "username": username,
                    "password": password
                  }
    return data_for_connect



'''  Get bearer token from the server   '''
def get_token():

    list_of_providersID: list = []
    headers = {'accept': '*/*', 'Content-type':'application/json; charset=utf-8'}
    url_get_providers = f"{data_for_connect['url']}/api/Providers"

    try:
        id_request = requests.get(url_get_providers, headers=headers, verify=False)
        response = id_request.json()
    except possible_request_errors as err:
        logging.error(f"{err}")
        sys.exit(f"Connection error: {err}")
    
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

        if auth_request.status_code in (200, 201, 204):
            token = response['access_token']
            break
        else:
            logging.error(f"ProviderID: {id}, response: {auth_request.status_code} [{data_for_connect['username']}/{data_for_connect['password']}]\n{auth_request.text}")

    return token



'''   Show all the licenses in the system   '''
def show_licenses():
    print()
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
    print("========================= Current licenses ==========================================\n")
    # for license in response:
    #     print(license,"\n")
    count = 1
    for license in response:
        print(f"\nLicense {count}:")
        count+=1
        for k, v in license.items():
            print(f" - {k}: {v}")
        
    print("=====================================================================================\n")



'''   Get server ID   '''
def get_serverID():

    url = f"{data_for_connect['url']}/api/License"
    headers = {'Content-type':'text/plane', 'Authorization': f"Bearer {token}"}
    payload = {
                "username": data_for_connect['username'],
                "password": data_for_connect['password']
              }
    
    try:
        request = requests.get(url, data=payload, headers=headers, verify=False)
        request.raise_for_status()
    except possible_request_errors as err:
        logging.error(f"{possible_request_errors}")

    # response is a list of dictionaries with a set of keys: 'isActive', 'serverId', 'licenseID', 'until', 'activeUsers', 'activeUsersLimit'
    response = request.json()

    print(f"\nServer ID: {response[0]['serverId']}")



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

    # Check if there are any active licenses
    count = 0
    for dct in get_license():
        if dct.get('isActive'):
            count += 1
    
    if count == 0:
        print("No active licenses have been found in the system.")
    else:
        for license in get_license():
            if license['isActive'] == True and license['licenseID'] != '00000000-0000-0000-0000-000000000000':
                url = f"{data_for_connect['url']}/api/License/{license['licenseID']}" 
                request = requests.delete(url, headers=headers, verify=False)
                if request.status_code in (200, 201, 204,):
                    print(f"License '{license['licenseID']}' has been deactivated!")
                else:
                    logging.error('%s', request.text)
                    print(f"Error with deactivation: {request.status_code}")
            



def post_license():

    headers = {'accept': 'text/plane', 'Content-Type': 'application/json-patch+json', 'Authorization': f"Bearer {token}"}
    url = f"{data_for_connect['url']}/api/License/"

    license_token = get_data_from_license_file()['license_token']
    
    data = json.dumps(license_token)

    request = requests.post(url, headers=headers, data=data, verify=False)
    for license in get_license():
        if license['isActive'] == True:
            licenseID = license['licenseID']

    if request.status_code in (200, 201, 204,):
        print(f"====== License {licenseID} has been posted! ======")
    else:
        logging.error('%s', request.text)
        print(f"====== License {licenseID} has not been posted! ======")



def put_license():
    
    headers = {'accept': '*/*', 'Content-type': 'text/plane', 'Authorization': f"Bearer {token}"}

    for license in get_license():
        if license['isActive'] == True:
            licenseID = license['licenseID']

    url = f"{data_for_connect['url']}/api/License/active/{licenseID}"
    data = json.dumps('no_need_to_put_anything')
    request = requests.put(url, headers=headers, data=data, verify=False)

    if request.status_code in (200, 201, 204,):
        print(f"====== License has been activated. ======")
    else:
        logging.error('%s', request.text)
        print(f"====== License has not been activated.======")
            
            

    

if __name__ == "__main__":
    data_for_connect = creds()
    token = get_token()
    while True:
        goal = define_purpose()
        if goal == 'update':
            post_license()
            put_license()
        elif goal == 'check':
            show_licenses()
        elif goal == 'delete':
            delete_license()
        elif goal == 'server_id':
            get_serverID()                
        else:            
            sys.exit()

