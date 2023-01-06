#
# 
version = '1.12'
'''
    Script for work with license and some other small features.
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
import xml.etree.ElementTree as ET
import shutil


'''   Global variables   '''
pwd = os.getcwd()
                                 
''''''''''''''''''''''''''''''''


class Logs:

    def __init__(self):
        self.bim_utils_log_file:str = f'{pwd}/bim_utils.log'    
        logging.basicConfig(filename=self.bim_utils_log_file, level=logging.DEBUG,
                            format="%(asctime)s %(levelname)s - %(message)s", filemode="w", datefmt='%d-%b-%y %H:%M:%S')


class Auth:

    def __init__(self):
        self.headers = {'accept': '*/*', 'Content-type':'application/json; charset=utf-8'}
        self.possible_request_errors: tuple = ( requests.exceptions.MissingSchema, requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout, 
                                                requests.exceptions.HTTPError, requests.exceptions.InvalidHeader, requests.exceptions.InvalidURL, 
                                                requests.exceptions.InvalidJSONError, requests.exceptions.JSONDecodeError  
                                              )
        self.api_Providers: str  = 'api/Providers'
        self.api_Auth_Login: str = 'api/Auth/Login'


    def get_credentials(self):
        '''  1. Function prompts for login and password. It returns dictionary with creds. Ex: {"url": 'http://my-bimeister.io', "username": admin, "password": mypassword}.
             2. Provides provider ID for get_user_access_token() function.
        '''

        self.url = input("\nEnter URL: ").lower()
        if len(self.url)==0:
            print("Incorrect URL.")
            if sys.platform == 'win32':
                os.system('pause')            
            sys.exit()

        self.url = self.url[:-1] if self.url[-1] == '/' else self.url

        confirm_name = input("Enter login(default, admin): ")
        confirm_pass = input("Enter password(default, Qwerty12345!): ")
        self.username=confirm_name if confirm_name else 'admin'
        self.password=confirm_pass if confirm_pass else 'Qwerty12345!'
        
        ''' block to check both ports: 80 and 443 '''  # Added fix if url is set with redirect to another source
        for x in range(2):
            try:            
                check_url_request = requests.get(url=f"{self.url}/{self.api_Providers}", headers=self.headers, verify=False, allow_redirects=False, timeout=2)
                if check_url_request.status_code == 200:
                    break
                elif check_url_request.status_code in (301, 302):   # This part needs to fix issues if the redirect is set up.
                    self.url = self.url[:4] + self.url[5:] if self.url[4] == 's' else self.url[:4] + 's' + self.url[4:]

            except self.possible_request_errors as err:
                logging.error(f"Connection error via '{self.url[:self.url.index(':')]}':\n{err}.")
                self.url = self.url[:4] + self.url[5:] if self.url[4] == 's' else self.url[:4] + 's' + self.url[4:]
                if x == 1:
                    logging.error(f"Check host connection to {self.url}.")
                continue

        response = check_url_request.json()
        self.providerId: list = [dct['id'] for dct in response]     # This list of id's will be provided to get_user_access_token() function. It needs to receive a token.
        return self.url, self.username, self.password, self.providerId


    def get_user_access_token(self, url:str, username:str, password:str, providerId:list):
        '''  Function to get bearer token from the server   '''

        for id in providerId:
            payload = {
                        "username": username,
                        "password": password,
                        "providerId": id
                    }
            data = json.dumps(payload)
            auth_request = requests.post(url=f"{url}/{self.api_Auth_Login}", data=data, headers=self.headers, verify=False)
            time.sleep(0.15)
            response = auth_request.json()

            '''  
            Block is for checking authorization request. 
            Correct response of /api/Auth/Login method suppose to return a .json with 'access_token' and 'refresh_token'. 
            '''
            log_text = f"ProviderID: {id}, response: {auth_request.status_code} [{username}/{password}]\n{auth_request.text}"
            if auth_request.status_code  in (200, 201, 204):
                self.token = response['access_token']
                break
            elif auth_request.status_code == 401:
                def logging_error():
                    print(f"--- {message} ---",'\n' if message != "Message for the log only." else '401 Error. Check the log file.')
                    logging.error(f"{message}" if message != "Message for the log only." else '')
                    logging.error(log_text)
                    if sys.platform == 'win32':
                        os.system('pause')
                    sys.exit()
                if response.get('type') and response.get('type') == 'TransitPasswordExpiredBimException':
                    message = f"Password for [{username}] has been expired!"
                    logging_error()
                elif response.get('type') and response.get('type') == 'IpAddressLoginAttemptsExceededBimException':
                    message = "Too many authorization attempts. IP address has been blocked!"
                    logging_error()
                elif response.get('type') and response.get('type') == 'AuthCommonBimException':
                    message = f"Unauthorized access. Check credentials: {username}/{password}"
                    logging_error()
                else:
                    message = "Message for the log only."
                    logging_error()
            else:
                logging.error(log_text)
                return False
        
        return self.token


class User:

    def __init__(self):
        self.api_UserObjects_all: str        = "api/UserObjects/all"
        self.api_Users_currentUser: str      = 'api/Users/current-user'
        self.api_Users: str                  = 'api/Users'
        self.api_SystemRoles: str            = 'api/SystemRoles'
        self.api_Users_AddSystemRole: str    = 'api/Users/AddSystemRole'
        self.api_Users_RemoveSystemRole: str = 'api/Users/RemoveSystemRole'


    def delete_user_objects(self):
        '''
            UserObjects – хранилище Frontend-данных на Backend.
            Здесь хранятся всяческие кеши, черновики обходов, выбранные задачи и прочее.
            Работа с хранилищем не предполагает валидацию, миграции и прочее. Таким образом, если модели данных меняются, работа с хранилищем, 
            уже наполненным какими-то данными может привести к ошибкам. Чтобы уберечь пользователя от этого, необходимо очищать таблицу.
        '''
        
        headers = {'accept': '*/*', 'Content-type': 'text/plane', 'Authorization': f"Bearer {auth.token}"}
        try:
            user_obj_request = requests.delete(url=f"{auth.url}/{self.api_UserObjects_all}", headers=headers, verify=False)
            if user_obj_request.status_code == 204:
                print("\n   - bimeisterdb.UserObjects table was cleaned successfully.")
            else:
                print("Something went wrong. Check the log.")
        except auth.possible_request_errors as err:
            logging.error(err)


    def get_current_user(self, token):
        ''' Getting info about current user. Response will provide a dictionary of values. '''

        url_get_current_user = f"{auth.url}/{self.api_Users_currentUser}"
        headers_get_currect_user = {'accept': '*/*', 'Content-type': 'text/plain', 'Authorization': f"Bearer {token}"}
        try:
            request = requests.get(url_get_current_user, headers=headers_get_currect_user, verify=False)
            time.sleep(0.15)
            response = request.json()
            if request.status_code != 200:
                logging.error(request.text)
        except auth.possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")
            return False
        return response
    

    def check_user_privileges(self):
        '''
            There is a tuple of needed permissions. Need to uncomment wanted of them to check the appropriate permissions.
            If the user doesn't have required permissions -> create another user and assing him a system role.
        '''

        tuple_of_needed_permissions:tuple = (
                                                # 'MailServerRead',
                                                # 'MailServerWrite',
                                                # 'ObjectModelsRead',
                                                # 'ObjectModelsWrite',
                                                # 'SecurityRead',
                                                # 'SecurityWrite',
                                                # 'ProcessesRead',
                                                # 'ProcessesWrite',
                                                # 'GroupsRead',
                                                # 'GroupsWrite',
                                                'LicensesRead',
                                                'LicensesWrite',
                                                # 'UsersRead',
                                                # 'UsersWrite',
                                                # 'RolesWrite',
                                                # 'RolesRead',
                                                # 'LdapRead',
                                                # 'LdapWrite',
                                                # 'OrgStructureWrite',
                                                # 'CreateProject'
                                            )
    
        # user_names_and_system_roles_id: dict = {}    # dictionary to collect user's permissions.
        user_system_roles_id: list = []         # list to collect user's permissions

        headers_get_users = {'Content-type':'text/plane', 'Authorization': f"Bearer {auth.token}"}
        request = requests.get(url=f"{auth.url}/{self.api_Users}", headers=headers_get_users, verify=False)                                
        response = request.json()
        if request.status_code != 200:
            logging.error(f"{self.api_Users}: {request.text}")
        
        '''   Check if the user has needed permissions in his system roles already. # {'name': 'Licenses', 'operation': 'Write'}   '''
        # response is a nested array, list with dictionaries inside.
        for x in range(len(response)):
            if auth.username == response[x].get('userName'):
                for role in response[x]['systemRoles']: # systemRoles is a list with dictionaries    # role is a dictionary: {'id': '679c9933-5937-4eee-b47f-1ebaec5f946b', 'name': 'admin'}
                    user_system_roles_id.append(role.get('id'))

                    ''' We're taking userName and fill our dictionary with it. In format {'userName': [systemRoles_id1, systemRoles_id2, ...}
                        Two options to create a dictionary we need. '''
                    # user_names_and_system_roles_id.setdefault(username, []).append(role.get('id'))                                                   # Option one                                                                                                            
                    # user_names_and_system_roles_id[username] = user_names_and_system_roles_id.get(username, []) + [role.get('id')]    # Option two

        for id in user_system_roles_id:
            try:
                request = requests.get(url=f"{auth.url}/{self.api_SystemRoles}/{id}", headers=headers_get_users, verify=False)
                response = request.json()
            except auth.possible_request_errors as err:
                logging.error(f"{err}\n{request.text}")

            for needed_permission in tuple_of_needed_permissions:
                if needed_permission in response['permissions']:
                    continue
                else:
                    return False
        return True


    def create_name_for_new_user(self):
        ''' Create a random name for a new user '''            
        new_username: str = ''.join(random.choice(string.ascii_letters) for x in range(15))
        return new_username


    def create_new_user_new_role_and_submitting_roles(self):

        '''  Create a new user  '''
        self.created_user_name: str = user.create_name_for_new_user()
        headers_create_user_and_system_role = {'accept': '*/*', 'Content-type': 'application/json-patch+json', 'Authorization': f"Bearer {auth.token}"}    
        payload_create_user = {
                                "firstName": "Johnny",
                                "lastName": "Mnemonic",
                                "middleName": "superuser",
                                "userName": self.created_user_name,
                                "displayName": "Johnny_Mnemonic",
                                "password": auth.password,
                                "phoneNumber": "+71234567890",
                                "email": "the_matrix@exists.neo",
                                "birthday": "1964-09-02T07:15:07.731Z",
                                "position": "The_one"
                }
        data = json.dumps(payload_create_user)

        count = 0   # counter to protect while loop from infinite iteration
        request = requests.post(url=f"{auth.url}/{self.api_Users}", headers=headers_create_user_and_system_role, data=data, verify=False)
        time.sleep(0.15)
        while True:
            count += 1
            if request.status_code == 201:
                response = request.json()
                logging.info(f"Create a new user  \
                             \nNew <{response['userName']}> user was created successfully.")
                self.created_user_name: str = response['userName']
                self.created_user_id: str = response['id']
                break
            elif request.status_code == 403:
                print("Current user don't have privileges for required procedure. Also don't have permissions to create users, so it could be temporary avoided.")
                return False
            else:
                if count == 10:
                    logging.error("No USERs were created! Error.")
                    break
                altered_data = data.replace(self.created_user_name, user.create_name_for_new_user())
                request = requests.post(url=f"{auth.url}/{self.api_Users}", headers=headers_create_user_and_system_role, data=altered_data, verify=False)                

        '''  Create a new system role  '''
        payload_create_system_role = {
                            "name": self.created_user_name,
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

        data = json.dumps(payload_create_system_role)
        try:
            request = requests.post(url=f"{auth.url}/{self.api_SystemRoles}", headers=headers_create_user_and_system_role, data=data, verify=False)
            time.sleep(0.15)
            response = self.created_system_role_id = request.json()
            if request.status_code == 201:
                logging.info("System role was created successfully.")
            else:
                logging.error(request.text)
        except auth.possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")

        ''' Add a new system role to a new user '''
        payload_add_system_role = {
                                    "systemRoleId": self.created_system_role_id,
                                    "userId": self.created_user_id
                                  }
        data = json.dumps(payload_add_system_role)
        try:
            request = requests.post(f"{auth.url}/{self.api_Users_AddSystemRole}", headers=headers_create_user_and_system_role, data=data, verify=False)
            time.sleep(0.15)
            if request.status_code in (201, 204):
                logging.info(f"Add a new system role to a new user.     \
                             \nSystem role '{self.created_system_role_id}' to user '{self.created_user_name}' added successfully.")
            else:
                logging.error(request.text)
        except auth.possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")

        ''' 
            Using credentianls of the new user, up privileges for current user we are working(default, admin). 
            Need to create all we need to manipulate with roles and users.
        '''
        self.current_user:dict = self.get_current_user(auth.token)

        ''' Adding created role to current user '''
        headers_add_system_role_to_current_user = {'accept': '*/*', 'Content-type': 'application/json-patch+json', 
                    'Authorization': f"Bearer {auth.get_user_access_token(auth.url, self.created_user_name, auth.password, auth.providerId)}"}
        payload_add_system_role = {
                                    "systemRoleId": self.created_system_role_id,
                                    "userId": self.current_user['id']
                                    }
        data = json.dumps(payload_add_system_role)  
        
        # This call for token needs to switch back return auth.token value to current user. Very important!
        auth.get_user_access_token(auth.url, auth.username, auth.password, auth.providerId)                                  
        try:
            request = requests.post(f"{auth.url}/{self.api_Users_AddSystemRole}", headers=headers_add_system_role_to_current_user, data=data, verify=False)
            time.sleep(0.15)
            if request.status_code in (201, 204):
                logging.info(f"Adding created role to current user. \
                             \nSystem role '{self.created_system_role_id}' to user <{auth.username}> added successfully.")
            else:
                logging.error(request.text)
        except auth.possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")
            return False

        return True
    

    def delete_created_system_role_and_user(self):

        def remove_role_from_current_user():
            ''' Remove created role from the current user. Otherwise, the role cannot be deleted. '''

            headers_remove_system_role_from_current_user = {'accept': '*/*', 'Content-type': 'application/json-patch+json', 
                                    'Authorization': f"Bearer {auth.get_user_access_token(auth.url, self.created_user_name, auth.password, auth.providerId)}"}

            # This call for token needs to switch back return auth.token value to current user. Very important!
            auth.get_user_access_token(auth.url, auth.username, auth.password, auth.providerId)

            payload_remove_system_role = {
                                            "systemRoleId": self.created_system_role_id,
                                            "userId": self.current_user['id']
                                            }
            data = json.dumps(payload_remove_system_role)
            try:
                request = requests.post(url=f"{auth.url}/{self.api_Users_RemoveSystemRole}", headers=headers_remove_system_role_from_current_user, data=data, verify=False)
                time.sleep(0.10)
                if request.status_code in (201, 204):
                    logging.info(f"Remove created role from the current user. \
                                 \nSystem role '{self.created_system_role_id}' from user <{auth.username}> removed successfully.")
                    return True
                else:
                    logging.error(request.text)
                    return False
            except auth.possible_request_errors as err:
                logging.error(f"{err}\n{request.text}")
                return False


        def remove_role_from_created_user():
            ''' Remove created role from created user. '''

            headers_remove_system_role_from_created_user = {'accept': '*/*', 'Content-type': 'application/json-patch+json',
                                        'Authorization': f"Bearer {auth.get_user_access_token(auth.url, auth.username, auth.password, auth.providerId)}" }
            payload_remove_system_role = {
                                            "systemRoleId": self.created_system_role_id,
                                            "userId": self.created_user_id
                                            }
            data = json.dumps(payload_remove_system_role)
            try:
                request = requests.post(url=f"{auth.url}/{self.api_Users_RemoveSystemRole}", headers=headers_remove_system_role_from_created_user, data=data, verify=False)
                time.sleep(0.15)
                if request.status_code in (201, 204):
                    logging.info(f"Remove created role from created user. \
                                 \nSystem role '{self.created_system_role_id}' from user <{self.created_user_name}> removed successfully.")
                else:
                    logging.error(request.text)
            except auth.possible_request_errors as err:
                logging.error(f"{err}\n{request.text}")


        def delete_system_role():
            ''' Delete created system role '''

            url_delete_system_role = f"{auth.url}/{self.api_SystemRoles}/{self.created_system_role_id}"
            headers = {'accept': '*/*', 'Authorization': f"Bearer {auth.get_user_access_token(auth.url, auth.username, auth.password, auth.providerId)}"}
            try:
                request = requests.delete(url=url_delete_system_role, headers=headers, verify=False)
                if request.status_code in (201, 204):
                    logging.info(f"Deletion created system role.   \
                                 \nNew role '{self.created_system_role_id}' was deleted successfully.")
                else:
                    logging.error(request.text)
            except auth.possible_request_errors as err:
                logging.error(f"{err}\n{request.text}")


        def delete_user():
            ''' Delete created user '''

            headers = {'accept': '*/*', 'Authorization': f"Bearer {auth.get_user_access_token(auth.url, auth.username, auth.password, auth.providerId)}"}
            url_delete_user = f"{auth.url}/{self.api_Users}/{self.created_user_id}"
            try:
                request = requests.delete(url=url_delete_user, headers=headers, verify=False)
                if request.status_code in (201, 204):
                    logging.info(f"Delete created user  \
                                 \nNew user <{self.created_user_name}> was deleted successfully.")
                else:
                    logging.error(request.text)
            except auth.possible_request_errors as err:
                logging.error(f"{err}\n{request.text}")

        remove_role_from_current_user()
        remove_role_from_created_user()
        delete_system_role()
        delete_user()



class License:

    def get_license_token(self):
        ''' Check if the *.lic file is in place '''

        if os.path.isfile(f"{pwd}/license.lic"):
            with open("license.lic", "r", encoding="utf-8") as file:    # get license_token from the .lic file and put it into data_from_lic_file dictionary
                license_token = file.read().split()[0].strip("\"")
            return license_token
        else:
            license_token = input("\nThere is no 'license.lic' file in the folder.\nEnter license token manually or 'q' for exit: ")
            if len(license_token) < 10 or license_token.lower() == 'q':
                print("No license token has been provided. Exit.\n")
                logging.info("No license token has been provided by the user.")
                if sys.platform == 'win32':
                    os.system('pause')
                sys.exit()

            return license_token

    def get_licenses(self):
        ''' Get all the licenses in the system '''

        url_get_license = f"{auth.url}/api/License"
        headers = {'accept': '*/*', 'Content-type':'text/plane', 'Authorization': f"Bearer {auth.token}"}
        payload = {
                    "username": auth.username,
                    "password": auth.password
                }   
        try:
            request = requests.get(url_get_license, data=payload, headers=headers, verify=False)
            request.raise_for_status()
        except auth.possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")

        # response is a list of dictionaries with a set of keys: 'isActive', 'serverId', 'licenseID', 'until', 'activeUsers', 'activeUsersLimit'
        response = request.json()
        return response


    def check_active_license(self):
        ''' Check if there is an active license. Return True/False '''

        licenses = self.get_licenses()
        for license in licenses:
            if license['licenseID'] == '00000000-0000-0000-0000-000000000000' and license['until'] > str(date.today()) + 'T' + datetime.now().strftime("%H:%M:%S"):
                return True
            elif license['isActive'] and license['licenseID'] != '00000000-0000-0000-0000-000000000000':
                return True
        return False
    

    def get_serverID(self):
        licenses = self.get_licenses()
        return licenses[-1]['serverId']


    def display_licenses(self):
        ''' Display the licenses '''

        licenses: list = self.get_licenses()
        if not self.check_active_license():
            for number, license in enumerate(licenses, 1):
                print(f"\n  License {number}:")
                if license['licenseID'] == '00000000-0000-0000-0000-000000000000':
                    if license['until'] < str(date.today()) + 'T' + datetime.now().strftime("%H:%M:%S"):
                        print(f"   - trial deploy license\n   - validation period: expired")
                        continue
                    else:
                        print(f"   - trial deploy license\n   - validation period: {license['until'][:19]}")
                        continue

                for key, value in license.items():
                    # Ternary operator. Made it just for exercise. It's hard to read, so we should aviod to use such constructions. 
                    # Commented "if-elif-else" block below provides the same result, but way more readable.
                    print(f"   - {key}: {Fore.GREEN + str(value)}" if value and key == 'isActive'   # "if value" by default means "if value is True"
                                else (f"   - {key}: {Fore.RED + str(value)}" if not value else f"   - {key}: {value}"))

                    # if value and key == 'isActive':
                    #     print(f" - {key}: {Fore.GREEN + str(value)}")
                    # elif not value:
                    #     print(f" - {key}: {Fore.RED + str(value)}")
                    # else:
                    #     print(f" - {key}: {value}")
        else:
            for license in licenses:
                if license.get('isActive'):
                    print()
                    for key, value in license.items():
                        print( f"   - {key}: {Fore.GREEN + str(value)}" if key == 'isActive' else f"   - {key}: {value}" )
                    break


    def delete_license(self):
        '''   Delete active license, if there is one.   '''    

        headers = {'accept': '*/*', 'Content-type': 'text/plane', 'Authorization': f"Bearer {auth.token}"}

        # Check if there are any active licenses
        isActive:bool = False
        licenses = self.get_licenses()
        for license in licenses:
            if license.get('isActive') and license['licenseID'] != '00000000-0000-0000-0000-000000000000':
                isActive:bool = True
                break

        if not isActive:
            print("\n   - no active licenses have been found in the system.")
        else:
            ''' 
                There is a default license from the installation with no ID(000..00). It cannot be deactivated, so we simply ignore it.
                After new license will be applied, default lic will disappear automatically.
            '''
            for license in licenses:
                if license['isActive'] == True and license['licenseID'] != '00000000-0000-0000-0000-000000000000':
                    url_delete_license = f"{auth.url}/api/License/{license['licenseID']}" 
                    request = requests.delete(url_delete_license, headers=headers, verify=False)
                    if request.status_code in (200, 201, 204,):
                        print(Fore.GREEN + f"   License '{license['licenseID']}' has been deactivated!")
                    else:
                        logging.error('%s', request.text)
                        print(Fore.RED + f"   License '{license['licenseID']}' has not been deactivated!")
                        print(f"Error with deactivation: {request.status_code}")


    def post_license(self):

        headers = {'accept': 'text/plane', 'Content-Type': 'application/json-patch+json', 
        'Authorization': f"Bearer {auth.token}"}
        url_post_license = f"{auth.url}/api/License/"
        
        data = json.dumps(self.get_license_token())
        request = requests.post(url_post_license, headers=headers, data=data, verify=False)
        response = request.json()
        time.sleep(0.15)
        if request.status_code in (200, 201, 204,):
            print(Fore.GREEN + f"   New license has been posted successfully!")
        else:
            logging.error('%s', request.text)
            print(Fore.RED + f"   Error: New license has not been posted!")

        return response['licenseID']    


    def put_license(self):
        
        put_license_result = False
        headers = {'accept': '*/*', 'Content-type': 'text/plane', 'Authorization': f"Bearer {auth.token}"}

        # all the active licenses will be deactivated, if user forgot to do it, and if there are any active
        for license in self.get_licenses():
            if license['isActive'] == True and license['licenseID'] != '00000000-0000-0000-0000-000000000000':
                self.delete_license()
        
        licenseID = self.post_license()   # function will post provided license, and return posted licenses ID
        url_put_license = f"{auth.url}/api/License/active/{licenseID}"
        payload = {}
        request = requests.put(url_put_license, headers=headers, data=payload, verify=False)

        if request.status_code in (200, 201, 204,):
            put_license_result = True
            print(Fore.GREEN + f"   New license has been activated successfully!")
        else:
            logging.error('%s', request.text)
            print(Fore.RED + f"   Error: New license has not been activated!")

        return put_license_result



class Export_data:

    def __init__(self):
        self.transfer_files_folder:str                = f'{pwd}/transfer_files'
        self.transfer_processes_folder:str            = f'{self.transfer_files_folder}/processes'
        self.is_first_launch_export_data:bool         = True
        self.api_Integration_ObjectModel_Export:str   = 'api/Integration/ObjectModel/Export'
        self.api_WorkFlowNodes:str                    = 'api/WorkFlowNodes'
        self.api_WorkFlows:str                        = 'api/WorkFlows'
        self.api_Attachments:str                      = 'api/Attachments'
        self.workflows_draft_file:str                 = 'Draft_workflows_export_server.json'
        self.workflows_archived_file:str              = 'Archived_workflows_export_server.json'
        self.workflows_active_file:str                = 'Active_workflows_export_server.json'
        self.object_model_file:str                    = 'object_model_export_server.json'
        self.exported_workflow_nodes_by_user_file:str = 'workflow_nodes_from_export.txt'
        self.list_of_all_workflow_nodes_file:str      = 'list_of_all_workflow_nodes_export_server.json'
        self.workflow_id_bimClass_id_file:str         = 'workflow_id_bimClass_id_export_server.json'


    def create_folder_for_export_procedures(self):
        ''' transfer_files_folder folder should be recreated only after first attempt to work with export procedure.
            Afterwards, the directory should stay untouched.
        '''
        self.headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {auth.token}"}
        try:
            if os.path.isdir(self.transfer_files_folder):
                shutil.rmtree(self.transfer_files_folder)
                time.sleep(0.15)
                os.mkdir(self.transfer_files_folder)
            elif not os.path.isdir(self.transfer_files_folder):
                os.mkdir(self.transfer_files_folder)
        except (OSError, FileExistsError, FileNotFoundError) as err:
            logging.error(err)
            print(f"Smth is wrong with the {self.transfer_files_folder}. Check the logs.")
            return False

        self.is_first_launch_export_data = False
        return True 


    def read_from_json(self, path_to_file, file_name):
        ''' Read from JSON files, and provide dictionary in return. Need to pass two arguments in str format: path and file name. '''

        file_name = file_name + '.json' if file_name[-5:] != '.json' else file_name
        try:
            with open(f'{path_to_file}/{file_name}', 'r', encoding='utf-8') as file:
                data_from_json = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as err:
            print(f"{file_name} file wasn't found. Check for it.")
            logging.error(f"Error with {file_name}.\n{err}")
            return False
        return data_from_json


    def get_object_model_export(self):    
        '''   Function gets model object from export server, and writes it in model_object_export_server.json file   '''

        # Need to delete object model file every time, if user have chosen 'export' from the menu.
        if os.path.isfile(f"{self.transfer_files_folder}/{self.object_model_file}"):
            confirm_to_delete = input("There is an model_object_export_server.json file already. Do you want to delete before export?(y/n): ").lower()
            if confirm_to_delete == 'y':
                os.remove(f'{self.transfer_files_folder}/{self.object_model_file}')
            else:
                print(f"First need to delete present {self.object_model_file}")
                return False

        url_get_object_model_export = f"{auth.url}/{self.api_Integration_ObjectModel_Export}"
        try:
            request = requests.get(url_get_object_model_export, headers=self.headers, verify=False)
            response = request.json()
        except auth.possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")
            print("Error: Couldn't export object model. Check the logs.")
            return False

        try:
            with open(f"{self.transfer_files_folder}/{self.object_model_file}", "w", encoding="utf-8") as json_file:
                json.dump(response, json_file, ensure_ascii=False, indent=4)
        except (FileNotFoundError, OSError) as err:
            logging.error(err)
            print(f"'{self.transfer_files_folder}' folder doesn't exist.")
            return False

        logging.info(f"Object model has been exported. '{self.object_model_file}' file is ready.")
        print(f"\n   - object model exported in '{self.object_model_file}' file.")
        return True


    def create_folder_for_processes(self):
        '''   Function creates a folder for processes in parent transfer_files_folder directory.   '''
        try:
            if not os.path.isdir(self.transfer_processes_folder):
                os.mkdir(self.transfer_processes_folder)
        except (OSError, FileExistsError, FileNotFoundError) as err:
            logging.error(err)
            return False


    def define_workflow_node_export(self):
        '''   Function creates a file 'chosen_by_user_workflow_nodes_export' with chosen workflow nodes in it.   '''

        try:
            if not os.path.isfile(f"{self.transfer_processes_folder}/{self.exported_workflow_nodes_by_user_file}"):
                with open(f"{self.transfer_processes_folder}/{self.exported_workflow_nodes_by_user_file}", mode='w', encoding='utf-8'): pass
        except (FileNotFoundError, OSError) as err:
            print(f"'{self.transfer_processes_folder}' folder doesn't exist.")
            logging.error(f"'{self.transfer_processes_folder}' folder doesn't exist.\n", err)
            return
        # Check if the 'workflow_nodes_filename_export' was created
        if not os.path.isfile(f"{self.transfer_processes_folder}/{self.exported_workflow_nodes_by_user_file}"):
            logging.error(f"File '{self.exported_workflow_nodes_by_user_file}' hasn't been created.")
            print(f" File '{self.exported_workflow_nodes_by_user_file}' hasn't been created. Check logs.")
            return

        # This self.current_workflow_node_selection will only go further through the process of export. Import procedure will use 'self.exported_workflow_nodes_by_user_file' file.
        self.current_workflow_node_selection: list = input("Choose nodes to export workflows from. Use whitespaces in-between to select more than one.  \
                                            \n(dr Draft, ar Archived, ac Active, q Quit): ").lower().split()

        # if user chose anything but ('d', 'ar', 'ac'), func will return False, and no processes will be provided further
        if not [x for x in self.current_workflow_node_selection if x in ('dr', 'ar', 'ac')]:
            return False
        # Replacing user input to full names: Draft, Archived, Active
        self.current_workflow_node_selection:list = [x for x in self.current_workflow_node_selection if x in ('dr', 'ar', 'ac')]
        self.current_workflow_node_selection = ' '.join(self.current_workflow_node_selection).replace('dr', 'Draft').replace('ar', 'Archived').replace('ac', 'Active').split()

        with open(f"{self.transfer_processes_folder}/{self.exported_workflow_nodes_by_user_file}", 'r', encoding='utf-8') as file:
            content = file.read()
        with open(f"{self.transfer_processes_folder}/{self.exported_workflow_nodes_by_user_file}", 'a', encoding='utf-8') as file:
            for node in self.current_workflow_node_selection:
                if node == 'Draft':
                    if self.workflows_draft_file not in content:
                        file.write(f"{self.workflows_draft_file}\n")
                elif node == 'Archived':
                    if self.workflows_archived_file not in content:
                        file.write(f"{self.workflows_archived_file}\n")
                elif node =='Active':
                    if self.workflows_active_file not in content:
                        file.write(f"{self.workflows_active_file}\n")
                else:
                    continue

        return True


    def get_all_workflow_nodes_export(self):
        '''  Getting Draft, Archived and Active nodes Id from 'list_of_workflow_nodes_export.json' file.  '''

        url_get_all_workflow_nodes_export = f"{auth.url}/{self.api_WorkFlowNodes}"
        try:
            request = requests.get(url_get_all_workflow_nodes_export, headers=self.headers, verify=False)
            response = request.json()
        except auth.possible_request_errors as err:
            logging.error(f"{err}\n{request.text}") 
            print(f"Error: Couldn't export workFlow nodes. Check the logs.")
            return False

        try:
            if not os.path.isfile(f'{self.transfer_processes_folder}/{self.list_of_all_workflow_nodes_file}'):
                with open(f'{self.transfer_processes_folder}/{self.list_of_all_workflow_nodes_file}', 'w', encoding='utf-8') as json_file:
                    json.dump(response, json_file, ensure_ascii=False, indent=4)
        except (FileNotFoundError, OSError) as err:
            logging.error(err)
            print(f"'{self.transfer_files_folder}' folder doesn't exist.")
            return False
        return True


    def get_workflows_export(self):
        ''' Get workflows from the chosen node. '''

        try:
            all_workflow_nodes = export_data.read_from_json(self.transfer_processes_folder, self.list_of_all_workflow_nodes_file)
        except FileNotFoundError:
            print(f"File wasn't found. Check '{self.transfer_files_folder}' folder.")
            return False

        for obj in range(len(all_workflow_nodes)):
            node_name = all_workflow_nodes[obj]['name']
            nodeId = all_workflow_nodes[obj]['id']            
            if node_name not in self.current_workflow_node_selection:
                continue
            url_get_workflows_export = f"{auth.url}/{self.api_WorkFlowNodes}/{nodeId}/children"
            try:
                request = requests.get(url_get_workflows_export, headers=self.headers, verify=False)
                response = request.json()
            except auth.possible_request_errors as err:
                logging.error(f"{err}\n{request.text}")
                return False

            with open(f"{self.transfer_processes_folder}/{node_name}_workflows_export_server.json", 'w', encoding='utf-8') as json_file:
                json.dump(response, json_file, ensure_ascii=False, indent=4)       
            logging.info(f"'{node_name}_workflows_export_server.json' file is ready.")
        return True


    def get_workflow_xml_from_export_server(self):
        ''' XML for every workflow will be exported from the 'workflow_nodes_filename_export' file. '''

        # Transforming nodes variable into a list with workflows*.json filenames.
        nodes = ' '.join(self.current_workflow_node_selection).replace('Draft', self.workflows_draft_file).replace('Archived', self.workflows_archived_file).replace('Active', self.workflows_active_file).split()
        for node in nodes:
            workflow_data = export_data.read_from_json(self.transfer_processes_folder, node)
            for line in workflow_data['workFlows']:
                url_get_workflow_xml_export = f"{auth.url}/{self.api_Attachments}/{line['attachmentId']}"
                request = requests.get(url_get_workflow_xml_export, headers=self.headers, verify=False)                
                with open(f"{self.transfer_processes_folder}/{line['originalId']}.xml", 'wb') as file:
                    file.write(request.content)
                time.sleep(0.1)

        return


    def get_workFlowId_and_bimClassId_from_export_server(self):
        '''
            This function does mapping between workFlow_id and bimClass_id. 
            It uses list comprehension block for transformation list of objects into dictionary with {'workFlow_id': 'bimClass_id'} pairs.
        '''

        workFlow_id_bimClass_id_export: list = []  # temp list to store data
        if not os.path.isfile(f"{self.transfer_processes_folder}/processes_names_with_id.txt"):
            with open(f"{self.transfer_processes_folder}/processes_names_with_id.txt", 'w', encoding='utf-8') as file:
                file.write('Process name and Id\n---------------------------------\n')            

        nodes = ' '.join(self.current_workflow_node_selection).replace('Draft', self.workflows_draft_file).replace('Archived', self.workflows_archived_file).replace('Active', self.workflows_active_file).split()
        for node in nodes:
            workflow_data = export_data.read_from_json(f"{self.transfer_processes_folder}", node)
            if len(workflow_data['workFlows']) == 0:
                print(f"   - No {node[:-19]}")
                continue

            for line in workflow_data['workFlows']:
                print(f"     {line['name']}")   # display the name of the process in the output
                url_get_workFlowId_and_bimClassId_from_export_server = f"{auth.url}/{self.api_WorkFlows}/{line['originalId']}/BimClasses"
                request = requests.get(url_get_workFlowId_and_bimClassId_from_export_server, headers=self.headers, verify=False)
                response = request.json()
                
                with open(f"{self.transfer_processes_folder}/{line['id']}.json", 'w', encoding='utf-8') as file:
                    json.dump(response, file, ensure_ascii=False, indent=4)

                # write list with active workFlows BimClasses ID in format [workFlow_id, bimClass_id]
                workFlow_id_bimClass_id_export.append(line['originalId'])
                workFlow_id_bimClass_id_export.append(response[0]['id'])

                # saving processes name with corresponding Id
                with open(f"{self.transfer_processes_folder}/processes_names_with_id.txt", 'a', encoding='utf-8') as file:
                    file.write(f"{line['name']}\n{line['originalId']}\n\n")

        # List comprehension block for transformation list of values into {'workFlow_id': 'bimClass_id'} pairs.
        tmp = workFlow_id_bimClass_id_export
        tmp:list = [ [tmp[x-1]] + [tmp[x]] for x in range(1, len(tmp), 2) ]       # generation list in format [ ['a', 'b'], ['c', 'd'], ['e', 'f'] ]

        workFlow_id_bimClass_id_export = dict(tmp)                                # transform tmp list from above to dictionary using dict() function in format {"workFlow_id": "bimClass_id"}
        
        if not os.path.isfile(f"{self.transfer_processes_folder}/{self.workflow_id_bimClass_id_file}"):
            with open(f"{self.transfer_processes_folder}/{self.workflow_id_bimClass_id_file}", 'w', encoding='utf-8') as file:
                json.dump(workFlow_id_bimClass_id_export, file, ensure_ascii=False, indent=4)
        else:
            if workFlow_id_bimClass_id_export:  # if tmp list is True(not empty), append.
                with open(f"{self.transfer_processes_folder}/{self.workflow_id_bimClass_id_file}", 'a', encoding='utf-8') as file:
                    json.dump(workFlow_id_bimClass_id_export, file, ensure_ascii=False, indent=4)
            
        logging.info("Mapping between workflow_ID and bimClass_ID: done. 'workFlow_id_bimClass_id_export.json' file is ready.")
        return True



class Import_data: # NEED TO DO THIS BLOCK

    def create_folder_for_files_and_logs_import(self):
        self.export_files_folder = 'transfer_files_folder'
        if os.path.isdir(f"{pwd}/{self.export_files_folder}") is False:
            logging.error("Folder 'files' for transferring data is missing.")
            if sys.platform == 'win32':
                os.system('pause')
            sys.exit("Folder 'files' is missing. Exit.")
        elif os.path.isdir(f"{pwd}/{self.export_files_folder}/logs") is False:
            os.mkdir(f"{pwd}/{self.export_files_folder}/logs")
        else: pass

        # Enable logs
        logging.basicConfig(filename=f"{pwd}/{self.export_files_folder}/logs/import_log.txt", level=logging.DEBUG,
                            format="%(asctime)s %(levelname)s - %(message)s", filemode="w", datefmt='%d-%b-%y %H:%M:%S')



class AppMenu:

    def welcome_info_note(self):
        ''' first note to be displayed '''
        print(f"\nv{version}    \
                \nnote: applicable with BIM version 101 and higher.")

    def define_purpose_and_menu(self):
        ''' Define what the user would like to do '''

        command = input("\nCommand (m for help): ").lower()
        main_menu =   "\n  License:                                         \
                       \n   1  get list of licenses                         \
                       \n   2  get serverId                                 \
                       \n   3  apply new license                            \
                       \n   4  delete active license                        \
                       \n                                                   \
                       \n  Databases:                                       \
                       \n   5  clean bimeisterdb.UserObjects table          \
                       \n   5i info about UserObjects table                 \
                       \n                                                   \
                       \n  Transfer data:                                   \
                       \n   6 export object model                           \
                       \n   7 export processes                              \
                       \n   8 import object model (not finished yet)        \
                       \n   9 import processes    (not finished yet)        \
                       \n  89 import all          (not finished yet)        \
                       \n                                                   \
                       \n  Main:                                            \
                       \n   m  print this menu                              \
                       \n   q  exit"

        if command == 'm':
            print(main_menu)
        elif command == '1':
            return 'check_license'
        elif command == '2':
            return 'server_id'
        elif command == '3':
            return 'apply_license'
        elif command == '4':
            return 'delete_active_license'
        elif command == '5':
            return 'truncate_user_objects'
        elif command == '5i':
            return 'truncate_user_objects_info'
        elif command == '6':
            return 'export_object_model'
        elif command == '7':
            return 'export_processes'
        elif command == '8':
            return 'import_object_model'
        elif command == '9':
            return 'import_processes'
        elif command == '89':
            return 'import_object_model_and_processes'
        elif command == 'q':
            return 'q'



def main():    

    appMenu.welcome_info_note()
    auth.get_credentials()
    auth.get_user_access_token(auth.url, auth.username, auth.password, auth.providerId)

    # checking if there is an active license on the server and user privileges needed for operation
    user_was_created:bool = False
    active_license:bool = license.check_active_license()
    if active_license:
        # if there is a license, need to check user's privileges
        if not user.check_user_privileges():
            user_was_created = user.create_new_user_new_role_and_submitting_roles()
    else:
        print("\nWARN: No active license on the server!")

    while True:
        goal = appMenu.define_purpose_and_menu()
        if goal == 'check_license':
            license.display_licenses()
        elif goal == 'server_id':
            print(f"\n   - serverId: {license.get_serverID()}")
        elif goal == 'apply_license':
            license.put_license()
        elif goal == 'delete_active_license':
            license.delete_license()
        elif goal == 'truncate_user_objects':
            user.delete_user_objects()
        elif goal == 'truncate_user_objects_info':
            print(user.delete_user_objects.__doc__)
        elif goal == 'export_object_model' or goal == 'export_processes':
            if export_data.is_first_launch_export_data:
                export_data.create_folder_for_export_procedures()
            if goal == 'export_object_model':
                export_data.get_object_model_export()
            elif goal == 'export_processes':
                export_data.create_folder_for_processes()
                export_data.get_all_workflow_nodes_export()
                if export_data.define_workflow_node_export():
                    export_data.get_workflows_export()
                    export_data.get_workflow_xml_from_export_server()
                    export_data.get_workFlowId_and_bimClassId_from_export_server()
        elif goal == 'import':
            pass
        elif goal == 'q':            
            break

    if user_was_created:
        user.delete_created_system_role_and_user()


if __name__=='__main__':
    # creating classes instances
    logs        = Logs()
    auth        = Auth()
    user        = User()
    license     = License()
    appMenu     = AppMenu()
    export_data = Export_data()
    import_data = Import_data()

    main()
    
'''   Need to finish: 1. Import   '''    
