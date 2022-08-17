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
import time


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
    

def get_license_token():

    # Check if the *.lic file is in place
    if os.path.isfile(f"{pwd}/license.lic"):

        with open("license.lic", "r", encoding="utf-8") as file:    # get license_token from the .lic file and put it into data_from_lic_file dictionary
            license_token = file.read().split()[0].strip("\"")
            
        return license_token
    
    else:
        # logging.error("No license.lic file in the folder. Exit.")
        # sys.exit("No license.lic file in the folder. Exit.")
        license_token = input("There is no license.lic file in the folder.\nEnter license token manually or 'q' for exit: ")
        if license_token == 'q':
            logging.debug("No license token has been provided by the user.")
            sys.exit()
        return license_token

def creds(username='admin', password='Qwerty12345!'):

    logging.basicConfig(filename=f"{pwd}/license_log.txt", level=logging.DEBUG,
                        format="%(asctime)s %(levelname)s - %(message)s", filemode="w", datefmt='%d-%b-%y %H:%M:%S')

    url = input("\nEnter URL: ").lower()
    if url[-1:] == '/':
        url = url[:-1]
    else: pass

    confirm_name = input("Enter login(default, admin): ")
    confirm_pass = input("Enter password(default, Qwerty12345!): ")
    if confirm_name:
        username=confirm_name
    if confirm_pass:
        password=confirm_pass
    
    data_for_connect: dict = {
                    "url": url,
                    "username": username,
                    "password": password
                  }
    
    return data_for_connect
    


'''  Get bearer token from the server   '''
def get_token(username, password):

    list_of_providersID: list = []
    headers = {'accept': '*/*', 'Content-type':'application/json; charset=utf-8'}
    url_get_providers = f"{data_for_connect['url']}/api/Providers"

    try:
        id_request = requests.get(url_get_providers, headers=headers, verify=False)
        response = id_request.json()
    except possible_request_errors as err:
        logging.error(err)
        sys.exit(f"Connection error: {err}")
    
    for dict in response:
        list_of_providersID.append(dict['id'])

    url_auth = f"{data_for_connect['url']}/api/Auth/Login"

    for id in list_of_providersID:
        payload = {
                    "username": username,
                    "password": password,
                    "providerId": id
                }
        data = json.dumps(payload)

        auth_request = requests.post(url_auth, data=data, headers=headers, verify=False)
        time.sleep(0.15)
        response = auth_request.json()       

        if auth_request.status_code in (200, 201, 204):
            token = response['access_token']
            break
        else:
            logging.error(f"ProviderID: {id}, response: {auth_request.status_code} [{data_for_connect['username']}/{data_for_connect['password']}]\n{auth_request.text}")
    
    return token

def get_current_user():

    ''' Getting info about current user. Response will provide a dictionary of values. '''
    url_get_current_user = f"{data_for_connect['url']}/api/Users/current-user"
    headers_get_currect_user = {'accept': '*/*', 'Content-type': 'text/plain', 'Authorization': f"Bearer {token}"}

    try:
        request = requests.get(url_get_current_user, headers=headers_get_currect_user, verify=False)
        time.sleep(0.15)
        response = request.json()
        if request.status_code != 200:
            logging.error(request.text)
    except possible_request_errors as err:
        logging.error(f"{err}\n{request.text}")
    
    return response



'''   Check user privileges   '''
def check_user_privileges():
    
    '''  Users aren't authorized to create or edit their own system roles. Thus, need to check for {'name': 'Licenses', 'operation': 'Write'} privileges in system role.
         If user doesn't have it, create another user, so we could be able to grant all privileges in system role for our current user.         
    '''
    url_users = f"{data_for_connect['url']}/api/Users"
    def check_user():        
        '''   Check if the user has needed permissions in his system roles already. # {'name': 'Licenses', 'operation': 'Write'}   '''

        # user_names_and_system_roles_id: dict = {}    # dictionary to collect user's permissions.
        user_system_roles_id: list = []         # list to collect user's permissions

        headers_get_users = {'Content-type':'text/plane', 'Authorization': f"Bearer {token}"}
        request = requests.get(url_users, headers=headers_get_users, verify=False)
        response = request.json()
        
        for x in range(len(response)):
            if data_for_connect['username'] == response[x].get('userName'):
                for role in response[x]['systemRoles']:
                    user_system_roles_id.append(role.get('id'))

                    ''' We're taking userName and fill our dictionary with it. In format {'userName': [systemRoles_id1, systemRoles_id2, ...}
                        Two options to create a dictionary we need. '''
                    # user_names_and_system_roles_id.setdefault(data_for_connect['username'], []).append(role.get('id'))     # Option one                                                                                                            
                    # user_names_and_system_roles_id[data_for_connect['username']] = user_names_and_system_roles_id.get(data_for_connect['username'], []) + [role.get('id')]    # Option two

        for id in user_system_roles_id:
            url_check_system_role = f"{data_for_connect['url']}/api/SystemRoles/{id}"
            try:
                request = requests.get(url_check_system_role, headers=headers_get_users, verify=False)
                response = request.json()
            except possible_request_errors as err:
                logging.error(err)

            for dct in response.get('permissions', False):
                if dct.get('name') == 'Licenses' and dct.get('operation') == 'Write':
                    return True

        return False           

    
    if not check_user():
        
        ''' If the user doesn't have required permissions -> create another user and assing him a system role. '''
        
        headers_create_user_and_system_role = {'accept': '*/*', 'Content-type': 'application/json-patch+json', 'Authorization': f"Bearer {token}"}    
        payload_create_user = {
                                "firstName": "Johnny",
                                "lastName": "Mnemonic",
                                "middleName": "superuser",
                                "userName": "137438691328",     # the seventh number in the series of perfect numbers 137438691328
                                "displayName": "Johnny_Mnemonic",
                                "password": "Qwerty12345!",
                                "phoneNumber": "+71234567890",
                                "email": "the_matrix@exists.neo",
                                "birthday": "2000-08-16T07:15:07.731Z",
                                "position": "The_one"
                }
        data = json.dumps(payload_create_user)
        try:
            request = requests.post(url_users, headers=headers_create_user_and_system_role, data=data, verify=False)
            time.sleep(0.15)
            response = request.json()
            if request.status_code == 201:
                logging.debug(f"'{response['userName']}' user was created successfully.")
                created_user_name: str = response['userName']
                created_user_id: str = response['id']

            # in case if userName already exists, try another userName. Which is the eighth number in the series of perfect numbers by the way.
            elif request.status_code == 409:
                altered_data = data.replace('137438691328', '2305843008139952128')
                request = requests.post(url_users, headers=headers_create_user_and_system_role, data=altered_data, verify=False)
                response = request.json()
                time.sleep(0.15)
                if request.status_code == 201:
                    logging.debug(f"'{response['userName']}' user was created successfully.")
                    created_user_name: str = response['userName']
                    created_user_id: str = response['id']
                else:
                    logging.error(request.text)
        except possible_request_errors as err:            
            logging.error(f"{err}\n{request.text}")

        ''' Create a new system role '''
        payload_create_system_role = {
                            "name": created_user_name,
                            "permissions": [
                                                {'name': 'CreateProject', 'operation': 'Write'},
                                                {'name': 'ObjectModels', 'operation': 'Write'},
                                                {'name': 'Roles', 'operation': 'Write'},
                                                {'name': 'Security', 'operation': 'Write'},
                                                {'name': 'Licenses', 'operation': 'Write'},
                                                {'name': 'Processes', 'operation': 'Write'},
                                                {'name': 'Ldap', 'operation': 'Write'},
                                                {'name': 'Groups', 'operation': 'Write'},
                                                {'name': 'MailServer', 'operation': 'Write'},
                                                {'name': 'Users', 'operation': 'Write'},
                                                {'name': 'Logs', 'operation': 'Read'}
                                            ]
                            }

        url_create_system_role = f"{data_for_connect['url']}/api/SystemRoles"
        data = json.dumps(payload_create_system_role)
        try:
            request = requests.post(url_create_system_role, headers=headers_create_user_and_system_role, data=data, verify=False)
            time.sleep(0.15)
            response = created_system_role_id = request.json()
            if request.status_code == 201:
                logging.debug("System role was created successfully.")
            else:
                logging.error(request.text)
        except possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")


        ''' Add new system role to a new user '''        
        url_add_system_role_to_user = f"{data_for_connect['url']}/api/Users/AddSystemRole"
        payload_add_system_role = {
                                    "systemRoleId": created_system_role_id,
                                    "userId": created_user_id
                                }
        data = json.dumps(payload_add_system_role)
        try:
            request = requests.post(url_add_system_role_to_user, headers=headers_create_user_and_system_role, data=data, verify=False)
            time.sleep(0.15)
            if request.status_code in (201, 204):
                logging.debug(f"System role '{created_system_role_id}' to user '{created_user_name}' added successfully.")
            else:
                logging.error(request.text)
        except possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")


        ''' Using credentianls of the new user, up privileges for current user we are working(default, admin). '''
        url_get_current_user = f"{data_for_connect['url']}/api/Users/current-user"
        headers_get_currect_user = {'accept': '*/*', 'Content-type': 'text/plain', 'Authorization': f"Bearer {token}"}

        # Getting info about current user. Response will provide a dictionary of values.
        try:
            request = requests.get(url_get_current_user, headers=headers_get_currect_user, verify=False)
            response = request.json()
        except possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")
        
        
        ''' Adding created role to current user '''     # this block could be skipped actually. Since we have a new user with full privileges, we could use it.
        headers_add_system_role_to_current_user = {'accept': '*/*', 'Content-type': 'application/json-patch+json', 'Authorization': f"Bearer {get_token(username=created_user_name, password='Qwerty12345!')}"}
        payload_add_system_role = {
                                    "systemRoleId": created_system_role_id,
                                    "userId": response['id']
                                    }
        data = json.dumps(payload_add_system_role)                                    
        try:
            request = requests.post(url_add_system_role_to_user, headers=headers_add_system_role_to_current_user, data=data, verify=False)
            time.sleep(0.15)
            if request.status_code in (201, 204):
                logging.debug(f"System role '{created_system_role_id}' to user '{response['userName']}' added successfully.")
            else:
                logging.error(request.text)
        except possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")

        created_userName_userId_systemRoleId: dict = {"userName": created_user_name, "userId": created_user_id, "systemRoleId": created_system_role_id}

        return created_userName_userId_systemRoleId   # this dictionary returns only if 'admin' user has no privileges to work with licenses. Need to be deleted afterwards.

    else:
        return True


def delete_created_system_role_and_user(created_userName_userId_systemRoleId):

    def remove_role_from_current_user():
        ''' Remove created role from the current user. Otherwise, the role cannot be deleted. '''

        headers_remove_system_role_from_current_user = \
        {'accept': '*/*', 'Content-type': 'application/json-patch+json', 'Authorization': f"Bearer {get_token(username=created_userName_userId_systemRoleId['userName'], password='Qwerty12345!')}"}
        url_remove_system_role_from_user = f"{data_for_connect['url']}/api/Users/RemoveSystemRole"
        current_user = get_current_user()
        payload_remove_system_role = {
                                        "systemRoleId": created_userName_userId_systemRoleId['systemRoleId'],
                                        "userId": current_user['id']
                                        }
        data = json.dumps(payload_remove_system_role)
        try:
            request = requests.post(url_remove_system_role_from_user, headers=headers_remove_system_role_from_current_user, data=data, verify=False)
            time.sleep(0.15)
            if request.status_code in (201, 204):
                logging.debug(f"System role '{created_userName_userId_systemRoleId['systemRoleId']}' from user '{current_user['userName']}' removed successfully.")
            else:
                logging.error(request.text)
        except possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")



    def remove_role_from_created_user():
        ''' Remove created role from created user. '''

        headers_remove_system_role_from_created_user = \
        {'accept': '*/*', 'Content-type': 'application/json-patch+json', 'Authorization': f"Bearer {get_token(username=data_for_connect['username'], password=data_for_connect['password'])}"}
        url_remove_system_role_from_user = f"{data_for_connect['url']}/api/Users/RemoveSystemRole"
        payload_remove_system_role = {
                                        "systemRoleId": created_userName_userId_systemRoleId['systemRoleId'],
                                        "userId": created_userName_userId_systemRoleId['userId']
                                        }
        data = json.dumps(payload_remove_system_role)
        try:
            request = requests.post(url_remove_system_role_from_user, headers=headers_remove_system_role_from_created_user, data=data, verify=False)
            time.sleep(0.15)
            if request.status_code in (201, 204):
                logging.debug(f"System role '{created_userName_userId_systemRoleId['systemRoleId']}' from user '{created_userName_userId_systemRoleId['userName']}' removed successfully.")
            else:
                logging.error(request.text)
        except possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")



    ''' Delete created system role and created user '''
    def delete_system_role():

        url_delete_system_role = f"{data_for_connect['url']}/api/SystemRoles/{created_userName_userId_systemRoleId['systemRoleId']}"
        headers = {'accept': '*/*', 'Authorization': f"Bearer {get_token(username=data_for_connect['username'], password=data_for_connect['password'])}"}

        try:
            request = requests.delete(url_delete_system_role, headers=headers, verify=False)
            if request.status_code in (201, 204):
                logging.debug(f"New role '{created_userName_userId_systemRoleId['systemRoleId']}' was deleted successfully.")
            else:
                logging.error(request.text)
        except possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")

    def delete_user():

        headers = {'accept': '*/*', 'Authorization': f"Bearer {get_token(username=data_for_connect['username'], password=data_for_connect['password'])}"}
        url_delete_user = f"{data_for_connect['url']}/api/Users/{created_userName_userId_systemRoleId['userId']}"
        # deleting user
        try:
            request = requests.delete(url_delete_user, headers=headers, verify=False)
            if request.status_code in (201, 204):
                logging.debug(f"New user '{created_userName_userId_systemRoleId['userId']}' was deleted successfully.")
            else:
                logging.error(request.text)
        except possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")

    remove_role_from_current_user()
    remove_role_from_created_user()
    delete_system_role()
    delete_user()



def show_licenses():
    ''' Show all the licenses in the system '''

    print()
    url = f"{data_for_connect['url']}/api/License"
    headers = {'accept': '*/*', 'Content-type':'text/plane', 'Authorization': f"Bearer {token}"}
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
        logging.error(err)

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
    
    data = json.dumps(get_license_token())

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
    token = get_token(username=data_for_connect['username'], password=data_for_connect['password'])   
    check_privelege = check_user_privileges()
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
            break
    if check_privelege != True:
        delete_created_system_role_and_user(check_privelege)
        sys.exit()
    else:
        sys.exit()

