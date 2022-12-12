#
# 
version = '1.9'
'''
    Script for work with license on the server. Activation, deactivation, check licenses, get serverID.
    version for windows OS with colors.
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
import random
import string
from colorama import init, Fore
init(autoreset=True)
from datetime import date
from datetime import datetime
# import auth_data    # local module for authentication procedure



'''   Global variables   '''
pwd = os.getcwd()
                                 
''''''''''''''''''''''''''''''''


def define_purpose():
    ''' Define what the user would like to do '''

    purpose = input("\nCheck licenses(1) || Get server ID(2) || Apply license(3) || Delete active license(4) || Exit(q)\nSelect one of the options: ").lower()
    if purpose in ("1", "check",):
        return 'check'
    elif purpose in ("3", "update", "apply"):
        return 'update'
    elif purpose in ("4", "delete"):
        return 'delete'
    elif purpose in ("2", "id"):
        return 'server_id'
    elif purpose in ("q", "Q"):
        return 'q'


def get_license_token():
    ''' Check if the *.lic file is in place '''

    if os.path.isfile(f"{pwd}/license.lic"):
        with open("license.lic", "r", encoding="utf-8") as file:    # get license_token from the .lic file and put it into data_from_lic_file dictionary
            license_token = file.read().split()[0].strip("\"")
        return license_token
    else:
        license_token = input("\nThere is no 'license.lic' file in the folder.\nEnter license token manually or 'q' for exit: ")
        if license_token == 'q':
            logging.info("No license token has been provided by the user.")
            sys.exit()
        return license_token


def get_current_user():
    ''' Getting info about current user. Response will provide a dictionary of values. '''

    url_get_current_user = f"{url}/api/Users/current-user"
    headers_get_currect_user = {'accept': '*/*', 'Content-type': 'text/plain', 'Authorization': f"Bearer {auth_data.token}"}

    try:
        request = requests.get(url_get_current_user, headers=headers_get_currect_user, verify=False)
        time.sleep(0.15)
        response = request.json()
        if request.status_code != 200:
            logging.error(request.text)
    except auth_data.possible_request_errors as err:
        logging.error(f"{err}\n{request.text}")
    
    return response


def check_active_license():
    ''' Get the list of licenses '''

    url_check_license = f"{url}/api/License"
    headers = {'Content-type':'text/plane', 'Authorization': f"Bearer {auth_data.token}"}
    payload = {
                "username": auth_data.credentials['username'],
                "password": auth_data.credentials['password']
              }
    
    request = requests.get(url_check_license, data=payload, headers=headers, verify=False)
    request.raise_for_status()

    # response is a list of dictionaries with a set of keys: 'isActive', 'serverId', 'licenseID', 'until', 'activeUsers', 'activeUsersLimit'
    response = request.json()
    for license in response:
        if license['licenseID'] == '00000000-0000-0000-0000-000000000000' and license['until'] > str(date.today()) + 'T' + datetime.now().strftime("%H:%M:%S"):
            return True

    for license in response:          
        if license['isActive'] == True and license['licenseID'] != '00000000-0000-0000-0000-000000000000':
            return True
    
    print("\n--- No active license on the server! Need to activate! ---")
    return False

def check_user_privileges():
    '''
        Users aren't authorized to create or edit their own system roles. Thus, need to check for {'name': 'Licenses', 'operation': 'Write'} privileges in system role.
        If user doesn't have it, create another user, so we could be able to grant all privileges in system role for our current user.  
    '''

    
    url_users = f"{url}/api/Users"

    def check_user():
        '''   Check if the user has needed permissions in his system roles already. # {'name': 'Licenses', 'operation': 'Write'}   '''

        # user_names_and_system_roles_id: dict = {}    # dictionary to collect user's permissions.
        user_system_roles_id: list = []         # list to collect user's permissions

        headers_get_users = {'Content-type':'text/plane', 'Authorization': f"Bearer {auth_data.token}"}
        request = requests.get(url_users, headers=headers_get_users, verify=False)                                
        response = request.json()
        if request.status_code != 200:
            logging.error(f"/api/Users: {request.text}")
        
        # response is a nested array, list with dictionaries inside.
        for x in range(len(response)):
            if auth_data.credentials['username'] == response[x].get('userName'):
                for role in response[x]['systemRoles']: # systemRoles is a list with dictionaries    # role is a dictionary: {'id': '679c9933-5937-4eee-b47f-1ebaec5f946b', 'name': 'admin'}
                    user_system_roles_id.append(role.get('id'))

                    ''' We're taking userName and fill our dictionary with it. In format {'userName': [systemRoles_id1, systemRoles_id2, ...}
                        Two options to create a dictionary we need. '''
                    # user_names_and_system_roles_id.setdefault(auth_data.credentials['username'], []).append(role.get('id'))     # Option one                                                                                                            
                    # user_names_and_system_roles_id[auth_data.credentials['username']] = user_names_and_system_roles_id.get(auth_data.credentials['username'], []) + [role.get('id')]    # Option two

        for id in user_system_roles_id:
            url_check_system_role = f"{url}/api/SystemRoles/{id}"
            try:
                request = requests.get(url_check_system_role, headers=headers_get_users, verify=False)
                response = request.json()
            except auth_data.possible_request_errors as err:
                logging.error(f"{err}\n{request.text}")
            
            if 'LicensesWrite' in response['permissions']:
                return True

        return False          

    
    if not check_user():        
        ''' Create a random name for a new user '''

        def create_name_for_new_user():            
            user_name: str = ''.join(random.choice(string.ascii_letters) for x in range(15))
            return user_name

        created_user_name: str = create_name_for_new_user()
        ''' If the user doesn't have required permissions -> create another user and assing him a system role. '''        
        headers_create_user_and_system_role = {'accept': '*/*', 'Content-type': 'application/json-patch+json', 'Authorization': f"Bearer {auth_data.token}"}    
        payload_create_user = {
                                "firstName": "Johnny",
                                "lastName": "Mnemonic",
                                "middleName": "superuser",
                                "userName": created_user_name,
                                "displayName": "Johnny_Mnemonic",
                                "password": "Qwerty12345!",
                                "phoneNumber": "+71234567890",
                                "email": "the_matrix@exists.neo",
                                "birthday": "1964-09-02T07:15:07.731Z",
                                "position": "The_one"
                }
        data = json.dumps(payload_create_user)

        count = 0   # counter to protect while loop from infinite iteration
        request = requests.post(url_users, headers=headers_create_user_and_system_role, data=data, verify=False)
        time.sleep(0.15)
        while True:
            count += 1
            if request.status_code == 201:
                response = request.json()
                logging.debug(f"New <{response['userName']}> user was created successfully.")
                created_user_name: str = response['userName']
                created_user_id: str = response['id']
                break
            else:
                if count == 10:
                    logging.error("No USERs were created! Error.")
                    break
                altered_data = data.replace(created_user_name, create_name_for_new_user())
                request = requests.post(url_users, headers=headers_create_user_and_system_role, data=altered_data, verify=False)                


        ''' Create a new system role '''
        payload_create_system_role = {
                            "name": created_user_name,
                            "permissions": [
                                            'MailServerRead',
                                            'MailServerWrite',
                                            'ObjectModelsRead',
                                            'ObjectModelsWrite',
                                            'SecurityRead',
                                            'SecurityWrite',
                                            'ProcessesRead',
                                            'ProcessesWrite',
                                            'GroupsRead',
                                            'GroupsWrite',
                                            'LicensesRead',
                                            'LicensesWrite',
                                            'UsersRead',
                                            'UsersWrite',
                                            'RolesWrite',
                                            'RolesRead',
                                            'LdapRead',
                                            'LdapWrite',
                                            'OrgStructureWrite',
                                            'CreateProject'
                                            ]
                                    }

        url_create_system_role = f"{url}/api/SystemRoles"
        data = json.dumps(payload_create_system_role)
        try:
            request = requests.post(url_create_system_role, headers=headers_create_user_and_system_role, data=data, verify=False)
            time.sleep(0.15)
            response = created_system_role_id = request.json()
            if request.status_code == 201:
                logging.debug("System role was created successfully.")
            else:
                logging.error(request.text)
        except auth_data.possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")


        ''' Add new system role to a new user '''
        url_add_system_role_to_user = f"{url}/api/Users/AddSystemRole"
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
        except auth_data.possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")


        ''' Using credentianls of the new user, up privileges for current user we are working(default, admin). '''
        url_get_current_user = f"{url}/api/Users/current-user"
        headers_get_currect_user = {'accept': '*/*', 'Content-type': 'text/plain', 'Authorization': f"Bearer {auth_data.token}"}

        # Getting info about current user. Response will provide a dictionary of values.
        try:
            request = requests.get(url_get_current_user, headers=headers_get_currect_user, verify=False)
            response = request.json()
        except auth_data.possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")
        
        
        ''' Adding created role to current user '''     # this block could be skipped actually. Since we have a new user with full privileges, we could use it.
        headers_add_system_role_to_current_user = {'accept': '*/*', 'Content-type': 'application/json-patch+json', 
                                                'Authorization': f"Bearer {auth_data.get_token(url, created_user_name, 'Qwerty12345!', auth_data.provider_id)}"}
        payload_add_system_role = {
                                    "systemRoleId": created_system_role_id,
                                    "userId": response['id']
                                    }
        data = json.dumps(payload_add_system_role)                                    
        try:
            request = requests.post(url_add_system_role_to_user, headers=headers_add_system_role_to_current_user, data=data, verify=False)
            time.sleep(0.15)
            if request.status_code in (201, 204):
                logging.debug(f"System role '{created_system_role_id}' to user <{response['userName']}> added successfully.")
            else:
                logging.error(request.text)
        except auth_data.possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")

        created_userName_userId_systemRoleId: dict = {"userName": created_user_name, "userId": created_user_id, "systemRoleId": created_system_role_id}

        return created_userName_userId_systemRoleId   # this dictionary returns only if 'admin' user has no privileges to work with licenses. Need to be deleted afterwards.

    else:
        return True


def delete_created_system_role_and_user(created_userName_userId_systemRoleId):

    def remove_role_from_current_user():
        ''' Remove created role from the current user. Otherwise, the role cannot be deleted. '''

        headers_remove_system_role_from_current_user = \
        {'accept': '*/*', 'Content-type': 'application/json-patch+json', 'Authorization': f"Bearer {auth_data.get_token(url, created_userName_userId_systemRoleId['userName'], 'Qwerty12345!', auth_data.provider_id)}"}
        url_remove_system_role_from_user = f"{url}/api/Users/RemoveSystemRole"
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
                logging.info(f"System role '{created_userName_userId_systemRoleId['systemRoleId']}' from user <{current_user['userName']}> removed successfully.")
            else:
                logging.error(request.text)
        except auth_data.possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")


    def remove_role_from_created_user():
        ''' Remove created role from created user. '''

        headers_remove_system_role_from_created_user = \
        {'accept': '*/*', 'Content-type': 'application/json-patch+json', 
         'Authorization': f"Bearer {auth_data.get_token(auth_data.credentials['url'], auth_data.credentials['username'], auth_data.credentials['password'], auth_data.provider_id)}" }
        url_remove_system_role_from_user = f"{url}/api/Users/RemoveSystemRole"
        payload_remove_system_role = {
                                        "systemRoleId": created_userName_userId_systemRoleId['systemRoleId'],
                                        "userId": created_userName_userId_systemRoleId['userId']
                                        }
        data = json.dumps(payload_remove_system_role)
        try:
            request = requests.post(url_remove_system_role_from_user, headers=headers_remove_system_role_from_created_user, data=data, verify=False)
            time.sleep(0.15)
            if request.status_code in (201, 204):
                logging.info(f"System role '{created_userName_userId_systemRoleId['systemRoleId']}' from user <{created_userName_userId_systemRoleId['userName']}> removed successfully.")
            else:
                logging.error(request.text)
        except auth_data.possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")


    ''' Delete created system role and created user '''
    def delete_system_role():

        url_delete_system_role = f"{url}/api/SystemRoles/{created_userName_userId_systemRoleId['systemRoleId']}"
        headers = {'accept': '*/*', 'Authorization': f"Bearer {auth_data.get_token(auth_data.credentials['url'], auth_data.credentials['username'], auth_data.credentials['password'], auth_data.provider_id)}"}

        try:
            request = requests.delete(url_delete_system_role, headers=headers, verify=False)
            if request.status_code in (201, 204):
                logging.info(f"New role '{created_userName_userId_systemRoleId['systemRoleId']}' was deleted successfully.")
            else:
                logging.error(request.text)
        except auth_data.possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")


    def delete_user():

        headers = {'accept': '*/*', 'Authorization': f"Bearer {auth_data.get_token(auth_data.credentials['url'], auth_data.credentials['username'], auth_data.credentials['password'], auth_data.provider_id)}"}
        url_delete_user = f"{url}/api/Users/{created_userName_userId_systemRoleId['userId']}"
        # deleting user
        try:
            request = requests.delete(url_delete_user, headers=headers, verify=False)
            if request.status_code in (201, 204):
                logging.info(f"New user <{created_userName_userId_systemRoleId['userName']}> was deleted successfully.")
            else:
                logging.error(request.text)
        except auth_data.possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")

    remove_role_from_current_user()
    remove_role_from_created_user()
    delete_system_role()
    delete_user()



def display_licenses():
    ''' Show all the licenses in the system '''

    print()
    url_show_license = f"{url}/api/License"
    headers = {'accept': '*/*', 'Content-type':'text/plane', 'Authorization': f"Bearer {auth_data.token}"}
    payload = {
                "username": auth_data.credentials['username'],
                "password": auth_data.credentials['password']
              }
    
    request = requests.get(url_show_license, data=payload, headers=headers, verify=False)
    if request.status_code != 200:
        logging.error(f"{request.text}")
    request.raise_for_status()

    # response is a list of dictionaries with a set of keys: 'isActive', 'serverId', 'licenseID', 'until', 'activeUsers', 'activeUsersLimit'
    response = request.json()
    print("========================= Current licenses ==========================================")
    
    count = 0
    for license in response:
        count+=1
        print(f"\nLicense {count}:")
        if license['licenseID'] == '00000000-0000-0000-0000-000000000000':
            if license['until'] < str(date.today()) + 'T' + datetime.now().strftime("%H:%M:%S"):
                print(f" - System license from deploy\n - validation period: expired")
                continue
            else:
                print(f" - System license from deploy\n - validation period: {license['until'][:19]}")
                continue

        for key, value in license.items():
            # Ternary operator. Made it just for exercise. It's hard to read, so we should aviod to use such constructions. 
            # Commented "if-elif-else" block below provides the same result, but way more readable.
            print(f" - {key}: {Fore.GREEN + str(value)}" if value == True and key != 'activeUsers'
                        else (f" - {key}: {Fore.RED + str(value)}" if value == False else f" - {key}: {value}"))

            # if value == True and key != 'activeUsers':
            #     print(f" - {key}: {Fore.GREEN + str(value)}")
            # elif value == False:
            #     print(f" - {key}: {Fore.RED + str(value)}")
            # else:
            #     print(f" - {key}: {value}")

    print("=====================================================================================\n")


def get_licenses():
    ''' Get all the licenses in the system '''

    url_show_license = f"{url}/api/License"
    headers = {'accept': '*/*', 'Content-type':'text/plane', 'Authorization': f"Bearer {auth_data.token}"}
    payload = {
                "username": auth_data.credentials['username'],
                "password": auth_data.credentials['password']
              }
    
    request = requests.get(url_show_license, data=payload, headers=headers, verify=False)
    if request.status_code != 200:
        logging.error(f"{request.text}")
    request.raise_for_status()

    # response is a list of dictionaries with a set of keys: 'isActive', 'serverId', 'licenseID', 'until', 'activeUsers', 'activeUsersLimit'
    response = request.json()
    return response


def get_serverID():
    ''' Get server ID '''

    url_get_serverID = f"{url}/api/License"
    headers = {'Content-type':'text/plane', 'Authorization': f"Bearer {auth_data.token}"}
    payload = {
                "username": auth_data.credentials['username'],
                "password": auth_data.credentials['password']
              }
    
    try:
        request = requests.get(url_get_serverID, data=payload, headers=headers, verify=False)
        request.raise_for_status()
    except auth_data.possible_request_errors as err:
        logging.error(f"{err}\n{request.text}")

    # response is a list of dictionaries with a set of keys: 'isActive', 'serverId', 'licenseID', 'until', 'activeUsers', 'activeUsersLimit'
    response = request.json()
    print(f"\nServer ID: {response[-1]['serverId']}") 


def delete_license():
    '''   Delete active license, if there is one.   '''    

    headers = {'accept': '*/*', 'Content-type': 'text/plane', 'Authorization': f"Bearer {auth_data.token}"}

    # Check if there are any active licenses
    count = 0
    for license in get_licenses():
        if license.get('isActive') and license['licenseID'] != '00000000-0000-0000-0000-000000000000':
            count += 1

    if count == 0:
        print("No active licenses have been found in the system.")
    else:
        ''' 
            There is a default license from the installation with no ID(000..00). It cannot be deactivated, so we simply ignore it.
            After new license will be applied, default lic will disappear automatically.
        '''
        for license in get_licenses():
            if license['isActive'] == True and license['licenseID'] != '00000000-0000-0000-0000-000000000000':
                url_delete_license = f"{url}/api/License/{license['licenseID']}" 
                request = requests.delete(url_delete_license, headers=headers, verify=False)
                if request.status_code in (200, 201, 204,):
                    print(Fore.GREEN + f"====== License '{license['licenseID']}' has been deactivated! ======")
                else:
                    logging.error('%s', request.text)
                    print(Fore.RED + f"====== License '{license['licenseID']}' has not been deactivated! ======")
                    print(f"Error with deactivation: {request.status_code}")
            

def post_license():

    headers = {'accept': 'text/plane', 'Content-Type': 'application/json-patch+json', 'Authorization': f"Bearer {auth_data.token}"}
    url_post_license = f"{url}/api/License/"
    
    data = json.dumps(get_license_token())
    request = requests.post(url_post_license, headers=headers, data=data, verify=False)
    response = request.json()
    time.sleep(0.15)
    if request.status_code in (200, 201, 204,):
        print(Fore.GREEN + f"====== New license has been posted successfully! =========")
    else:
        logging.error('%s', request.text)
        print(Fore.RED + f"====== New license has not been posted! ======")

    return response['licenseID']


def put_license():
    
    put_license_result = False
    headers = {'accept': '*/*', 'Content-type': 'text/plane', 'Authorization': f"Bearer {auth_data.token}"}

    # all the active licenses will be deactivated, if user forgot to do it, and if there are any active
    for license in get_licenses():
        if license['isActive'] == True and license['licenseID'] != '00000000-0000-0000-0000-000000000000':
            delete_license()
    
    licenseID = post_license()   # function will post provided license, and return posted licenses ID
    url_put_license = f"{url}/api/License/active/{licenseID}"
    payload = {}
    request = requests.put(url_put_license, headers=headers, data=payload, verify=False)

    if request.status_code in (200, 201, 204,):
        put_license_result = True
        print(Fore.GREEN + f"====== New license has been activated successfully! ======")
    else:
        logging.error('%s', request.text)
        print(Fore.RED + f"====== New license has not been activated! ======")

    return put_license_result



if __name__ == "__main__":
    print(f"v{version}\nnote: applicable with BIM version 101 and higher.")
    import auth_data    # local module for authentication procedure
    url = auth_data.credentials['url']
    check_active_lic = check_active_license()    
    if check_active_lic:
        check_privelege = check_user_privileges()
    else:
        print("Warning: There is no active license. Can't check users' permissions!")
    
    while True:
        goal = define_purpose()
        if goal == 'update':
            put_license()
        elif goal == 'check':
            display_licenses()
        elif goal == 'delete':
            delete_license()
        elif goal == 'server_id':
            get_serverID()                
        elif goal == 'q':            
            break
    
    if check_active_lic:
        if check_privelege != True:                                 # If user initially had no privileges to work with licenses, new user will be created, and check_user_privileges() never returns True.
            delete_created_system_role_and_user(check_privelege)    # It will always return {created_userName_userId_systemRoleId} dictionary instead.
            sys.exit()                                              # Thus, we need to remove newely created user and role after we done.
    else:
        sys.exit()
