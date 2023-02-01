#
# 
version = '1.20'
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
import shutil


'''   Global variables   '''
pwd = os.getcwd()
                                 
''''''''''''''''''''''''''''''''


class Logs:

    def __init__(self):
        self.bim_utils_log_file:str = f'{pwd}/bm_utils.log'
        if not os.path.isfile(self.bim_utils_log_file):
            logging.basicConfig(filename=self.bim_utils_log_file, level=logging.DEBUG,
                                format="%(asctime)s %(levelname)s - %(message)s", filemode="w", datefmt='%d-%b-%y %H:%M:%S')
        else:
            logging.basicConfig(filename=self.bim_utils_log_file, level=logging.DEBUG,
                                format="%(asctime)s %(levelname)s - %(message)s", filemode="a", datefmt='%d-%b-%y %H:%M:%S')


class Auth:

    api_Providers:str  = 'api/Providers'
    api_Auth_Login:str = 'api/Auth/Login'
    headers = {'accept': '*/*', 'Content-type':'application/json; charset=utf-8'}
    possible_request_errors:tuple = (  requests.exceptions.MissingSchema, requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout,
                                       requests.exceptions.HTTPError, requests.exceptions.InvalidHeader, requests.exceptions.InvalidURL,
                                       requests.exceptions.InvalidSchema, requests.exceptions.InvalidJSONError, requests.exceptions.JSONDecodeError  )


    def __init__(self):
        self.url      = None
        self.username = None
        self.password = None
        self.token    = None


    def establish_connection(self):
        try:
            self.url:str = input("\nEnter URL: ").lower()
            self.url     = self.url[:-1] if self.url[-1] == '/' else self.url
        except IndexError:
            message:str = 'Wrong input.'
            print(message)
            logging.info(message)
            return False
        except KeyboardInterrupt:
            logging.info('Interrupted by user')
            return False
        if not self.url_validation():
            return False
        if not self.get_providerId():
            return False
        self.get_login_password()
        return True if self.get_user_access_token(self.url, self.username, self.password, self.providerId) else False


    def url_validation(self):

        # Check both ports: 80 and 443
        for x in range(2):
            try:
                check_url_request = requests.get(url=f"{self.url}/{self.api_Providers}", verify=False, allow_redirects=False, timeout=2)
                if check_url_request.status_code == 200:
                    self.api_providers_response = check_url_request.json()
                    return True
                elif check_url_request.status_code in (301, 302):   # This part needs to fix issues if the redirect is set up.
                    self.url = self.url[:4] + self.url[5:] if self.url[4] == 's' else self.url[:4] + 's' + self.url[4:]
            except requests.exceptions.MissingSchema:
                print('Invalid URL')
                return False
            except self.possible_request_errors as err:
                logging.error(f"Connection error via '{self.url[:self.url.index(':')]}':\n{err}.")
                self.url = self.url[:4] + self.url[5:] if self.url[4] == 's' else self.url[:4] + 's' + self.url[4:]
                if x == 1:
                    message:str = "Error: Check connection to host."
                    print(message)
                    logging.error(f"{err}\n{message}")
                    return False
                continue


    def get_providerId(self):

        if len(self.api_providers_response) == 1:
            self.providerId = self.api_providers_response[0]['id']
            return True
        else:
            print('    Choose authorization type:')
            for num, obj in enumerate(self.api_providers_response, 1):
                print(f"      {str(num)}. {obj['name']} ({obj['providerTypeOption']})")
            try:
                inp = int(input('    value: '))
                self.providerId = self.api_providers_response[inp-1]['id']
                return True
            except ValueError:
                print('Wrong input.')
                return False


    def get_login_password(self):
        confirm_name = input("Enter login(default, admin): ")
        confirm_pass = input("Enter password(default, Qwerty12345!): ")
        self.username=confirm_name if confirm_name else 'admin'
        self.password=confirm_pass if confirm_pass else 'Qwerty12345!'


    def get_user_access_token(self, url, username, password, providerId):
        ''' Basically this is a login into system, after what we get an access token. '''

        payload = {
                    "username":   username,
                    "password":   password,
                    "providerId": providerId
                  }
        data = json.dumps(payload)
        auth_request = requests.post(url=f"{url}/{self.api_Auth_Login}", data=data, headers=self.headers, verify=False)
        response = auth_request.json()
        time.sleep(0.07)
        '''  
        Block is for checking authorization request. 
        Correct response of /api/Auth/Login method suppose to return a .json with 'access_token' and 'refresh_token'. 
        '''
        log = f"ProviderID: {providerId}, response: {auth_request.status_code} [{username}/{password}]\n{auth_request.text}"
        if auth_request.status_code == 401:
            if response.get('type') and response.get('type') == 'TransitPasswordExpiredBimException':
                print(f"Password for '{username}' has been expired!")
                logging.error(log)
                return False
            elif response.get('type') and response.get('type') == 'IpAddressLoginAttemptsExceededBimException':
                message = "Too many authorization attempts. IP address has been blocked!"
                print(message)
                logging.error(log)
                return False
            elif response.get('type') and response.get('type') == 'AuthCommonBimException':
                message = f"Unauthorized access. Check credentials for user: {username}."
                print(message)
                logging.error(log)
                return False
            else:
                logging.error(log)
                return False
        elif auth_request.status_code  in (200, 201, 204):
            self.token = response['access_token']
            return True
        else:
            logging.error(log)
            return False



class User:

    api_UserObjects_all:str        = "api/UserObjects/all"
    api_Users_currentUser:str      = 'api/Users/current-user'
    api_Users:str                  = 'api/Users'
    api_Users_full:str             = 'api/Users/full'
    api_SystemRoles:str            = 'api/SystemRoles'
    api_Users_AddSystemRole:str    = 'api/Users/AddSystemRole'
    api_Users_RemoveSystemRole:str = 'api/Users/RemoveSystemRole'
    superuser = Auth()

    def __init__(self):
        pass


    def delete_user_objects(self, url, token):
        '''
            UserObjects – хранилище Frontend-данных на Backend.
            Здесь хранятся всяческие кеши, черновики обходов, выбранные задачи и прочее.
            Работа с хранилищем не предполагает валидацию, миграции и прочее. Таким образом, если модели данных меняются, работа с хранилищем, 
            уже наполненным какими-то данными может привести к ошибкам. Чтобы уберечь пользователя от этого, необходимо очищать таблицу.
        '''
        
        headers = {'accept': '*/*', 'Content-type': 'text/plane', 'Authorization': f"Bearer {token}"}
        try:
            user_obj_request = requests.delete(url=f"{url}/{self.api_UserObjects_all}", headers=headers, verify=False)
            if user_obj_request.status_code == 204:
                print("\n   - bimeisterdb.UserObjects table was cleaned successfully.")
            else:
                print("Something went wrong. Check the log.")
        except auth.possible_request_errors as err:
            logging.error(err)


    def get_all_users(self, url, token):
        headers = {'accept': '*/*', 'Content-type': 'text/plain', 'Authorization': f"Bearer {token}"}
        request = requests.get(url=f"{url}/{self.api_Users_full}", headers=headers, verify=False)
        users = request.json()
        return users # list with dictionaries inside


    def get_current_user(self, url, token):
        ''' Getting info about current user. Response will provide a dictionary of values. '''

        url_get_current_user = f"{url}/{self.api_Users_currentUser}"
        headers = {'accept': '*/*', 'Content-type': 'text/plain', 'Authorization': f"Bearer {token}"}
        try:
            request = requests.get(url_get_current_user, headers=headers, verify=False)
            time.sleep(0.15)
            response = request.json()
            if request.status_code != 200:
                logging.error(request.text)
        except auth.possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")
            return False
        return response
    

    def check_user_privileges(self, url, token, username, permissions_to_check:tuple):
        ''' Function requires to pass permissions needed to be checked, along with url, token and username. '''
    
        user_system_roles_id: list = []  # list to collect user's system roles Id.

        headers = {'Content-type':'text/plane', 'Authorization': f"Bearer {token}"}
        request = requests.get(url=f"{url}/{self.api_Users}", headers=headers, verify=False)                                
        response = request.json()
        if request.status_code != 200:
            logging.error(f"{self.api_Users}: {request.text}")
            return False

        '''   Check if the user has needed permissions in his system roles already. Selecting roles from the tuple_of_needed_permissions.   '''
        # response is a nested array, list with dictionaries inside.
        for x in range(len(response)):
            if username == response[x].get('userName'):
                for role in response[x]['systemRoles']: # systemRoles is a list with dictionaries    # role is a dictionary: {'id': '679c9933-5937-4eee-b47f-1ebaec5f946b', 'name': 'admin'}
                    if role.get('name') == 'user':
                        continue
                    user_system_roles_id.append(role.get('id'))

                    ''' We're taking userName and fill our dictionary with it. In format {'userName': [systemRoles_id1, systemRoles_id2, ...}
                        Two options to create a dictionary we need. '''
                    # user_names_and_system_roles_id.setdefault(username, []).append(role.get('id'))                                    # Option one
                    # user_names_and_system_roles_id[username] = user_names_and_system_roles_id.get(username, []) + [role.get('id')]    # Option two

        # Return from this loop will close the current function.
        for id in user_system_roles_id:
            try:
                request = requests.get(url=f"{url}/{self.api_SystemRoles}/{id}", headers=headers, verify=False)
                response = request.json()
            except auth.possible_request_errors as err:
                logging.error(f"{err}\n{request.text}")

            for permission in permissions_to_check:
                if permission in response['permissions']:
                    continue
                else:
                    return False
            return True


    def create_random_name(self):
        random_name: str = ''.join(random.choice(string.ascii_letters) for x in range(20))
        return random_name


    def create_or_activate_superuser(self, url, token):
        '''  Function checks for a special user with super privileges. If there is a needed user it will pass, if there isn't or deactivated, it will be created/activated.  '''

        headers_create_user_and_system_role = {'accept': '*/*', 'Content-type': 'application/json-patch+json', 'Authorization': f"Bearer {token}"}

        self.superuser.username:str = 'johnny_mnemonic'
        self.superuser.password:str  = 'Qwerty12345!'
        payload_create_user = {
                                "firstName": "Johnny",
                                "lastName": "Mnemonic",
                                "middleName": "no_middle_name",
                                "userName": self.superuser.username,
                                "displayName": "Johnny_Mnemonic",
                                "password": self.superuser.password,
                                "phoneNumber": "+71234567890",
                                "email": "the_matrix@exists.neo",
                                "birthday": "1964-09-02T07:15:07.731Z",
                                "position": "The_one"
                              }
        data = json.dumps(payload_create_user)

        all_users:list = self.get_all_users(url, token)        
        post_user_request = requests.post(url=url + '/' + self.api_Users, headers=headers_create_user_and_system_role, data=data, verify=False)
        if post_user_request.status_code == 201:
            self.superuser_id:str = post_user_request.json()['id']
        elif post_user_request.status_code == 409 and post_user_request.json()['error']['key'] == 'Auth.AlreadyExists.User.UserAlreadyExists':
            for user in all_users:
                if user.get('userName') == self.superuser.username and (user.get('isDeleted') or user.get('isDisabled')):
                    self.superuser_id = user.get('id')
                    put_request = requests.put(url=f"{url}/{self.api_Users}/{user.get('id')}/activate", headers=headers_create_user_and_system_role)
                    if not put_request.status_code in (200, 201):
                        logging.error(f"'{self.superuser.username}' user wasn't activated")
                        return False
                elif user.get('userName') == self.superuser.username:
                    self.superuser_id = user.get('id')
                    break
        elif post_user_request.status_code == 403:
            print("Current user don't have privileges for required procedure. Also don't have permissions to create users, so it could be temporary avoided.")
            logging.error(post_user_request.text)
            return False

        '''  Create a new system role  '''
        temp_system_role_name:str = self.create_random_name()
        payload_create_system_role = {
                                        "name": temp_system_role_name,
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
            request = requests.post(url=url + '/' + self.api_SystemRoles, headers=headers_create_user_and_system_role, data=data, verify=False)
            if request.status_code == 409 and request.json()['error']['key'] == 'Auth.AlreadyExists.SystemRole':
                logging.warning("Superuser system role already exists.")
                altered_data = data.replace(temp_system_role_name, self.create_random_name())
                request = requests.post(url=url + '/' + self.api_SystemRoles, headers=headers_create_user_and_system_role, data=altered_data, verify=False)
            time.sleep(0.05)
            self.temp_system_role_id = request.json()
            logging.info("System role was created successfully.") if request.status_code == 201 else logging.error(request.text)
        except auth.possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")
            return False

        ''' Add a new system role to a superuser '''
        payload_add_system_role = {
                                    "systemRoleId": self.temp_system_role_id, 
                                    "userId": self.superuser_id
                                  }
        data = json.dumps(payload_add_system_role)
        try:
            request = requests.post(url=url + '/' + self.api_Users_AddSystemRole, headers=headers_create_user_and_system_role, data=data, verify=False)
            if request.status_code != 204:
                pass
            time.sleep(0.05)
            logging.info(f"Add a new system role to a new user. \
                          \nSystem role '{self.temp_system_role_id}' to user '{self.superuser.username}' added successfully.") if request.status_code in (201, 204) else logging.error(request.text)
        except auth.possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")

        ''' 
            Using credentianls of the superuser, up privileges for current user we are working under(default, admin).
            Need to create all we need to manipulate with roles and users.
        '''
        self.initial_user:dict = self.get_current_user(url, token)

        ''' Adding created role to current user '''
        self.superuser.get_user_access_token(url, self.superuser.username, self.superuser.password, auth.providerId) # logging in under superuser account
  
        headers_add_system_role_to_current_user = {'accept': '*/*', 'Content-type': 'application/json-patch+json', 'Authorization': f"Bearer {self.superuser.token}"}
        payload_add_system_role = {
                                    "systemRoleId": self.temp_system_role_id,
                                    "userId": self.initial_user['id']
                                  }
        data = json.dumps(payload_add_system_role)                                
        try:
            request = requests.post(f"{url}/{self.api_Users_AddSystemRole}", headers=headers_add_system_role_to_current_user, data=data, verify=False)
            time.sleep(0.05)         
            logging.info(f"Adding created role to current user. \
                            \nSystem role '{self.temp_system_role_id}' to user '{self.initial_user['userName']}' added successfully.") if request.status_code in (201, 204) else logging.error(request.text)
        except auth.possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")
            return False

        return True

    
    def delete_created_system_role_and_delete_user(self, url):

        def remove_role_from_current_user():
            ''' Remove created role from the current user. Otherwise, the role cannot be deleted. '''

            headers_remove_system_role_from_current_user = {'accept': '*/*', 'Content-type': 'application/json-patch+json', 'Authorization': f"Bearer {self.superuser.token}"}

            payload_remove_system_role = {
                                            "systemRoleId": self.temp_system_role_id,
                                            "userId": self.initial_user['id']
                                            }
            data = json.dumps(payload_remove_system_role)
            try:
                request = requests.post(url=url + '/' + self.api_Users_RemoveSystemRole, headers=headers_remove_system_role_from_current_user, data=data, verify=False)
                time.sleep(0.10)
                if request.status_code in (201, 204):
                    logging.info(f"Remove created role from the current user. \
                                 \nSystem role '{self.temp_system_role_id}' from user '{auth.username}' removed successfully.")
                    return True
                else:
                    logging.error(request.text)
            except auth.possible_request_errors as err:
                logging.error(f"{err}\n{request.text}")
                return False


        def remove_role_from_created_user():
            ''' Remove created role from superuser. '''

            # this function implements logon procedure, so we need to re-login as current user again
            auth.get_user_access_token(url, auth.username, auth.password, auth.providerId)
            headers_remove_system_role_from_created_user = {'accept': '*/*', 'Content-type': 'application/json-patch+json', 'Authorization': f"Bearer {auth.token}" }
            payload_remove_system_role = {
                                            "systemRoleId": self.temp_system_role_id,
                                            "userId": self.superuser_id
                                            }
            data = json.dumps(payload_remove_system_role)
            try:
                request = requests.post(url=auth.url + '/' + self.api_Users_RemoveSystemRole, headers=headers_remove_system_role_from_created_user, data=data, verify=False)
                time.sleep(0.15)
                if request.status_code in (201, 204):
                    logging.info(f"Remove created role from created user. \
                                 \nSystem role '{self.temp_system_role_id}' from user '{self.superuser.username}' removed successfully.")
                else:
                    logging.error(request.text)
            except auth.possible_request_errors as err:
                logging.error(f"{err}\n{request.text}")
                return False
            return True


        def delete_system_role():
            ''' Delete created system role '''

            url_delete_system_role = f"{url}/{self.api_SystemRoles}/{self.temp_system_role_id}"
            headers = {'accept': '*/*', 'Authorization': f"Bearer {auth.token}"}
            try:
                request = requests.delete(url=url_delete_system_role, headers=headers, verify=False)
                if request.status_code in (201, 204):
                    logging.info(f"Deletion created system role.   \
                                 \nNew role '{self.temp_system_role_id}' was deleted successfully.")
                else:
                    logging.error(request.text)
            except auth.possible_request_errors as err:
                logging.error(f"{err}\n{request.text}")
                return False
            return True


        def delete_user():
            ''' Delete created user '''

            headers = {'accept': '*/*', 'Authorization': f"Bearer {auth.token}"}
            url_delete_user = f"{url}/{self.api_Users}/{self.superuser_id}"
            try:
                request = requests.delete(url=url_delete_user, headers=headers, verify=False)
                if request.status_code in (201, 204):
                    logging.info(f"Delete created user  \
                                 \nNew user <{self.superuser_id}> was deleted successfully.")
                else:
                    logging.error(request.text)
            except auth.possible_request_errors as err:
                logging.error(f"{err}\n{request.text}")
                return False
            return True

        remove_role_from_current_user()
        remove_role_from_created_user()
        delete_system_role()
        delete_user()


    # def create_new_user_new_role_submit_new_role(self, url, token, password):

    #     '''  Create a new user  '''
    #     self.created_user_name:str = self.create_random_name()
    #     headers_create_user_and_system_role = {'accept': '*/*', 'Content-type': 'application/json-patch+json', 'Authorization': f"Bearer {token}"}
    #     payload_create_user = {
    #                             "firstName": "Johnny",
    #                             "lastName": "Mnemonic",
    #                             "middleName": "superuser",
    #                             "userName": self.created_user_name,
    #                             "displayName": "Johnny_Mnemonic",
    #                             "password": password,
    #                             "phoneNumber": "+71234567890",
    #                             "email": "the_matrix@exists.neo",
    #                             "birthday": "1964-09-02T07:15:07.731Z",
    #                             "position": "The_one"
    #             }
    #     data = json.dumps(payload_create_user)

    #     count = 0   # counter to protect while loop from infinite iteration
    #     request = requests.post(url=f"{url}/{self.api_Users}", headers=headers_create_user_and_system_role, data=data, verify=False)
    #     time.sleep(0.15)
    #     while True:
    #         count += 1
    #         if request.status_code == 201:
    #             response = request.json()
    #             logging.info(f"Create a new user  \
    #                          \nNew <{response['userName']}> user was created successfully.")
    #             self.created_user_name:str = response['userName']
    #             self.created_user_id:str = response['id']
    #             break
    #         elif request.status_code == 403:
    #             print("Current user don't have privileges for required procedure. Also don't have permissions to create users, so it could be temporary avoided.")
    #             return False
    #         else:
    #             if count == 10:
    #                 logging.error("No user was created! Error.")
    #                 break
    #             altered_data = data.replace(self.created_user_name, user.create_random_name())
    #             request = requests.post(url=f"{url}/{self.api_Users}", headers=headers_create_user_and_system_role, data=altered_data, verify=False)

    #     '''  Create a new system role  '''
    #     payload_create_system_role = {
    #                         "name": self.created_user_name,
    #                         "permissions": [
    #                                         'MailServerRead',
    #                                         'MailServerWrite',
    #                                         'ObjectModelsRead',
    #                                         'ObjectModelsWrite',
    #                                         'SecurityRead',
    #                                         'SecurityWrite',
    #                                         'ProcessesRead',
    #                                         'ProcessesWrite',
    #                                         'GroupsRead',
    #                                         'GroupsWrite',
    #                                         'LicensesRead',
    #                                         'LicensesWrite',
    #                                         'UsersRead',
    #                                         'UsersWrite',
    #                                         'RolesWrite',
    #                                         'RolesRead',
    #                                         'LdapRead',
    #                                         'LdapWrite',
    #                                         'OrgStructureWrite',
    #                                         'CreateProject'
    #                                         ]
    #                                 }

    #     data = json.dumps(payload_create_system_role)
    #     try:
    #         request = requests.post(url=f"{url}/{self.api_SystemRoles}", headers=headers_create_user_and_system_role, data=data, verify=False)
    #         time.sleep(0.15)
    #         response = self.created_system_role_id = request.json()
    #         if request.status_code == 201:
    #             logging.info("System role was created successfully.")
    #         else:
    #             logging.error(request.text)
    #     except auth.possible_request_errors as err:
    #         logging.error(f"{err}\n{request.text}")

    #     ''' Add a new system role to a new user '''
    #     payload_add_system_role = {
    #                                 "systemRoleId": self.created_system_role_id,
    #                                 "userId": self.created_user_id
    #                               }
    #     data = json.dumps(payload_add_system_role)
    #     try:
    #         request = requests.post(f"{url}/{self.api_Users_AddSystemRole}", headers=headers_create_user_and_system_role, data=data, verify=False)
    #         time.sleep(0.15)
    #         if request.status_code in (201, 204):
    #             logging.info(f"Add a new system role to a new user.     \
    #                          \nSystem role '{self.created_system_role_id}' to user '{self.created_user_name}' added successfully.")
    #         else:
    #             logging.error(request.text)
    #             return False
    #     except auth.possible_request_errors as err:
    #         logging.error(f"{err}\n{request.text}")

    #     ''' 
    #         Using credentianls of the new user, up privileges for current user we are working under(default, admin).
    #         Need to create all we need to manipulate with roles and users.
    #     '''
    #     self.current_user:dict = self.get_current_user(url, token)


    #     ''' Adding created role to current user '''

    #     # logging in with newly created user account
    #     self.superuser.get_user_access_token(url, self.created_user_name, password, auth.providerId)
  
    #     headers_add_system_role_to_current_user = {'accept': '*/*', 'Content-type': 'application/json-patch+json', 'Authorization': f"Bearer {self.superuser.token}"}
    #     payload_add_system_role = {
    #                                 "systemRoleId": self.created_system_role_id,
    #                                 "userId": self.current_user['id']
    #                                 }
    #     data = json.dumps(payload_add_system_role)  
                                
    #     try:
    #         request = requests.post(f"{url}/{self.api_Users_AddSystemRole}", headers=headers_add_system_role_to_current_user, data=data, verify=False)
    #         time.sleep(0.15)
    #         if request.status_code in (201, 204):
    #             logging.info(f"Adding created role to current user. \
    #                          \nSystem role '{self.created_system_role_id}' to user '{auth.username}' added successfully.")
    #         else:
    #             logging.error(request.text)
    #     except auth.possible_request_errors as err:
    #         logging.error(f"{err}\n{request.text}")
    #         return False
    #     return True



class License:

    api_License:str = "api/License"
    permissions_to_check:tuple = ('LicensesRead', 'LicensesWrite')

    def __init__(self):
        pass


    def check_permissions(self, url, token, username, password):

        is_active_license:bool = self.get_license_status(url, token, username, password)
        if is_active_license and not user.check_user_privileges(url, token, username, self.permissions_to_check):
            return False
        elif not is_active_license:
            logging.info("No active license. Can't perform privileges check.")
            return True  # Need to return True, because without an active license it isn't possible to perform any check
        else:
            return True


    def grant_privileges(self, url, token, username, password):
        return user.create_or_activate_superuser(url, token) if not self.check_permissions(url, token, username, password) else False


    def read_license_token(self):
        ''' Check if there is a license.lic file, or ask user for token. '''

        if os.path.isfile(f"{pwd}/license.lic"):
            with open("license.lic", "r", encoding="utf-8") as file:    # get license_token from the .lic file and put it into data_from_lic_file dictionary
                self.license_token = file.read().split()[0].strip("\"")        
        else:
            self.license_token = input("\nThere is no 'license.lic' file in the folder.\nEnter license token manually or 'q' for exit: ")
            if len(self.license_token) < 10 or self.license_token.lower() == 'q':
                print("\n   - no license token has been provided. Exit.")
                logging.info("No license token has been provided by the user.")
                return False
        return True


    def get_licenses(self, url, token, username, password):
        ''' Get all the licenses in the system '''

        url_get_licenses:str = f'{url}/{self.api_License}'
        headers = {'accept': '*/*', 'Content-type':'text/plane', 'Authorization': f"Bearer {token}"}
        payload = {
                    "username": username,
                    "password": password
                }
        try:
            request = requests.get(url=url_get_licenses, data=payload, headers=headers, verify=False)
            request.raise_for_status()
        except auth.possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")

        # response is a list of dictionaries with a set of keys: 'isActive', 'serverId', 'licenseID', 'until', 'activeUsers', 'activeUsersLimit'
        response = request.json()
        return response


    def get_license_status(self, url, token, username, password):
        ''' Check if there is an active license. Return True/False. '''

        licenses = self.get_licenses(url, token, username, password)
        for license in licenses:
            if license['activeUsers'] > license['activeUsersLimit'] and license['isActive']:
                logging.error(f"Users limit was exceeded! Active users: {license['activeUsers']}. Users limit: {license['activeUsersLimit']}")
                print("Users limit is exceeded!")
                return False
            elif license['licenseID'] == '00000000-0000-0000-0000-000000000000' and license['until'] > str(date.today()) + 'T' + datetime.now().strftime("%H:%M:%S"):
                return True
            elif license['isActive'] and license['licenseID'] != '00000000-0000-0000-0000-000000000000':
                return True
        return False


    def get_serverID(self, url, token, username, password):
        licenses = self.get_licenses(url, token, username, password)
        return licenses[-1]['serverId']


    def display_licenses(self, url, token, username, password):
        ''' Display the licenses '''

        licenses: list = self.get_licenses(url, token, username, password)
        if not self.get_license_status(url, token, username, password):
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
                    print(f"   - {key}: {Fore.RED + str(value)}" if not value and key == 'isActive' else f"   - {key}: {value}")

        elif self.get_license_status(url, token, username, password):
            for license in licenses:
                if license.get('isActive'):
                    print()
                    if license.get('licenseID') == '00000000-0000-0000-0000-000000000000':
                        print(f"   - trial deploy license\n   - validation period: {license['until'][:19]}")
                    else:
                        for key, value in license.items():
                            print( f"   - {key}: {Fore.GREEN + str(value)}" if value and key == 'isActive' else f"   - {key}: {value}" )
                    break
                else: continue
        else:
            logging.error("Unpredictable behaviour(license status) in License class.")


    def delete_license(self, url, token, username, password):
        '''   Delete active license, if there is one.   '''    

        headers = {'accept': '*/*', 'Content-type': 'text/plane', 'Authorization': f"Bearer {token}"}

        # Check if there are any active licenses, except system trial license if it's active. 
        # System trial license can't be deleted, so we can't use self.get_license_status function here.
        isActive:bool = False
        licenses = self.get_licenses(url, token, username, password)
        for license in licenses:
            if license.get('isActive') and license['licenseID'] != '00000000-0000-0000-0000-000000000000':
                isActive:bool = True
                break
        if not isActive:
            print("\n   - no active licenses have been found in the system.")
        else:
            ''' 
                There is a default trial license from the installation with no ID(000..00). It cannot be deactivated, so we simply ignore it.
                After new license will be applied, system trial license will disappear automatically.
            '''
            for license in licenses:
                if license['isActive'] and license['licenseID'] != '00000000-0000-0000-0000-000000000000':
                    url_delete_license = f"{url}/{self.api_License}/{license['licenseID']}" 
                    request = requests.delete(url=url_delete_license, headers=headers, verify=False)
                    if request.status_code in (200, 201, 204,):
                        print(Fore.GREEN + f"\n   - license '{license['licenseID']}' has been deactivated!")
                    else:
                        logging.error('%s', request.text)
                        print(Fore.RED + f"\n   - license '{license['licenseID']}' has not been deactivated! Check the logs.")


    def post_license(self, url, token):

        headers = {'accept': 'text/plane', 'Content-Type': 'application/json-patch+json', 
        'Authorization': f"Bearer {token}"}
        
        if self.read_license_token():
            data = json.dumps(self.license_token)
            request = requests.post(url=f'{url}/{self.api_License}', headers=headers, data=data, verify=False)
            response = request.json()
            time.sleep(0.15)
            if request.status_code in (200, 201, 204,):
                self.new_licenseId:str = response['licenseID']
                print(Fore.GREEN + f"\n   - new license has been posted successfully!")
                return True
            else:
                logging.error('%s', request.text)
                print(Fore.RED + f"\n   - new license has not been posted!")
        return False


    def put_license(self, url, token, username, password):
        
        headers = {'accept': '*/*', 'Content-type': 'text/plane', 'Authorization': f"Bearer {token}"}
        # all the active licenses will be deactivated, if user forgot to do it, and if there are any active
        for license in self.get_licenses(url, token, username, password):
            if license['isActive'] == True and license['licenseID'] != '00000000-0000-0000-0000-000000000000':
                self.delete_license(url, token, username, password)
        
        if self.post_license(url, token):
            url_put_license:str = f"{url}/{self.api_License}/active/{self.new_licenseId}"
            payload = {}
            request = requests.put(url=url_put_license, headers=headers, data=payload, verify=False)
            if request.status_code in (200, 201, 204,):
                print(Fore.GREEN + f"   - new license has been activated successfully!")
                return True
            else:
                logging.error('%s', request.text)
                print(Fore.RED + f"   - error: New license has not been activated!")
        return False



class Export_data:

    transfer_folder:str                          = f'{pwd}/transfer_files'
    transfer_workflows_folder:str                = f'{transfer_folder}/workflows'
    api_Integration_ObjectModel_Export:str       = 'api/Integration/ObjectModel/Export'
    api_WorkFlowNodes:str                        = 'api/WorkFlowNodes'
    api_WorkFlows:str                            = 'api/WorkFlows'
    api_Attachments:str                          = 'api/Attachments'
    all_workflow_nodes_file:str                  = 'all_workflow_nodes_export_server.json'
    workflows_draft_file:str                     = 'Draft_workflows_export_server.json'
    workflows_archived_file:str                  = 'Archived_workflows_export_server.json'
    workflows_active_file:str                    = 'Active_workflows_export_server.json'
    selected_workflow_nodes_file:str             = 'workflow_nodes_to_import.list'
    workflowID_bimClassID_file:str               = 'workflowID_bimClassID_export_server.json'
    object_model_file:str                        = 'object_model_export_server.json'
    workflowsID_and_names_from_export_server:str = 'workflowsID_and_names_from_export_server.list'  # Save it just in case if need to find a particular file among workflows or smth.
    export_server_info_file:str                  = 'export_server_info.txt'  # Needs for separation import procedures on export server during one session.

    def __init__(self):
        self.is_first_launch_export_data:bool = True


    def create_folder_for_transfer_procedures(self):
        try:
            if not os.path.isdir(self.transfer_folder):
                os.mkdir(self.transfer_folder)
                time.sleep(0.1)
        except (OSError, FileExistsError, FileNotFoundError) as err:
            logging.error(err)
            print(f"Smth is wrong with the {self.transfer_folder}. Check the logs.")
            return False
        self.is_first_launch_export_data = False
        return True


    def clean_transfer_files_directory(self):
        ''' Clean self.transfer folder option. '''        
        try:
            if os.path.isdir(self.transfer_folder):
                shutil.rmtree(self.transfer_folder, ignore_errors=True)
                time.sleep(0.25)
                os.mkdir(self.transfer_folder)
                time.sleep(0.1)
                print('\n   - transfer_files folder is now empty.')
            else:
                print('\n   - no transfer_files folder was found.')
        except (OSError, FileExistsError, FileNotFoundError) as err:
            logging.error(err)
            print(f"Smth is wrong with the {self.transfer_folder}. Check the logs.")
            return False
        return True


    def read_file(self, path_to_file, filename):
        ''' Read from text files. In .json case function returns a dictionary. Need to pass two arguments in str format: path and file name. '''
        try:
            with open(f"{path_to_file}/{filename}", 'r', encoding='utf-8') as file:
                if os.path.splitext(f'{path_to_file}/{filename}')[1] == '.json':    # checking extension of the file
                    try:
                        content = json.load(file)
                    except json.JSONDecodeError as err:
                        print(f"Error with the {filename} file. Check the logs.")
                        logging.error(f"Error with {filename}.\n{err}")
                        return False
                    return content
                else:
                    content = file.read()
                    return content
        except (OSError, FileExistsError, FileNotFoundError) as err:
            logging.error(err)
            return False


    def get_object_model(self, filename, url, token):    
        '''   Function gets object model from the server, and writes it into a file.   '''

        if appMenu.menu_user_command != '8':    # Don't check or ask user about confirmation in case of import procedure.
            if os.path.isfile(f"{self.transfer_folder}/{filename}"):
                confirm_to_delete = input(f"There is an {filename} file already. Do you want to overwrite it?(y/n): ").lower()
                os.remove(f'{self.transfer_folder}/{filename}') if confirm_to_delete == 'y' else False

        headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}
        url_get_object_model:str = url + '/' + self.api_Integration_ObjectModel_Export
        try:
            request = requests.get(url_get_object_model, headers=headers, verify=False)
            response = request.json()
        except auth.possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")
            print("Error: Couldn't export object model. Check the logs.")
            return False

        try:
            with open(f"{self.transfer_folder}/{filename}", "w", encoding="utf-8") as json_file:
                json.dump(response, json_file, ensure_ascii=False, indent=4)
        except (FileNotFoundError, OSError) as err:
            logging.error(err)
            print(f"'{self.transfer_folder}' folder doesn't exist.")
            return False

        logging.info(f"Object model has been exported. '{filename}' file is ready.")
        if appMenu.menu_user_command == '6':
            print(f"\n   - object model exported in '{filename}' file.")
        return True


    def create_workflows_directory(self):
        '''   Function creates a folder for workflows in parent transfer_folder directory.   '''
        try:
            if not os.path.isdir(self.transfer_workflows_folder):
                os.mkdir(self.transfer_workflows_folder)
        except (OSError, FileExistsError, FileNotFoundError) as err:
            logging.error(err)
            return False


    def select_workflow_nodes(self):
        '''   Function creates a file 'chosen_by_user_workflow_nodes_export' with chosen workflow nodes in it.   '''

        try:
            file_path = self.transfer_workflows_folder + '/' + self.selected_workflow_nodes_file
            if not os.path.isfile(file_path):
                with open(file_path, mode='w', encoding='utf-8'): pass
        except (FileNotFoundError, OSError) as err:
            print(f"'{self.transfer_workflows_folder}' folder doesn't exist.")
            logging.error(f"'{self.transfer_workflows_folder}' folder doesn't exist.\n", err)
            return

        # This self.current_workflow_node_selection will only go further through the process of export. Import procedure will use 'self.selected_workflow_nodes_file' file.
        self.current_workflow_node_selection:list = input("Choose nodes to export workflows from. Use whitespaces in-between to select more than one.  \
                                            \n(dr Draft, ar Archived, ac Active, q Quit): ").lower().split()

        # if user chose anything but ('dr', 'ar', 'ac'), func will return False, and no processes will go further
        if not [x for x in self.current_workflow_node_selection if x in ('dr', 'ar', 'ac')]:
            return False
        # Replacing user input with full names: Draft, Archived, Active
        self.current_workflow_node_selection:list = [x for x in self.current_workflow_node_selection if x in ('dr', 'ar', 'ac')]
        self.current_workflow_node_selection = ' '.join(self.current_workflow_node_selection).replace('dr', 'Draft').replace('ar', 'Archived').replace('ac', 'Active').split()

        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        with open(file_path, 'a', encoding='utf-8') as file:
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


    def get_all_workflow_nodes(self, filename, url, token):
        '''  Getting Draft, Archived and Active nodes from the server in .json file.  
             Function holds a dictionary with all the nodes in format: {"NodeName": "NodeId"}.
        '''

        # url_get_all_workflow_nodes = f"{url}/{self.api_WorkFlowNodes}"
        url_get_all_workflow_nodes = url + '/' + self.api_WorkFlowNodes
        headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}
        try:
            request = requests.get(url=url_get_all_workflow_nodes, headers=headers, verify=False)
            response = request.json()
        except auth.possible_request_errors as err:
            logging.error(f"{err}\n{request.text}") 
            print(f"Error: Couldn't export workFlow nodes. Check the logs.")
            return False

        try:
            if not os.path.isfile(f'{self.transfer_workflows_folder}/{filename}'):  # Need to keep exported file before during a single session, if it's there.
                with open(f'{self.transfer_workflows_folder}/{filename}', 'w', encoding='utf-8') as json_file:
                    json.dump(response, json_file, ensure_ascii=False, indent=4)

            # Creating a dictionary with all three nodes from the server in format: {"NodeName": "NodeId"}
            self.workflow_nodes:dict = {}
            for x in self.read_file(self.transfer_workflows_folder, self.all_workflow_nodes_file):
                self.workflow_nodes[x['name']] = x['id']

        except (FileNotFoundError, OSError) as err:
            logging.error(err)
            print(f"'{self.transfer_folder}' folder doesn't exist.")
            return False

        return True


    def get_workflows(self):
        ''' Get all workflows from the chosen node. '''

        for nodeName, nodeId in self.workflow_nodes.items():
            if nodeName not in self.current_workflow_node_selection:
                continue

            url_get_workflows = f"{auth.url}/{self.api_WorkFlowNodes}/{nodeId}/children"
            headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {auth.token}"}
            try:
                request = requests.get(url_get_workflows, headers=headers, verify=False)
                response = request.json()
            except auth.possible_request_errors as err:
                logging.error(f"{err}\n{request.text}")
                return False

            with open(f"{self.transfer_workflows_folder}/{nodeName}_workflows_export_server.json", 'w', encoding='utf-8') as json_file:
                json.dump(response, json_file, ensure_ascii=False, indent=4)       
            logging.info(f"'{nodeName}_workflows_export_server.json' file is ready.")
        return True


    def get_workflow_xml(self):
        ''' XML for every workflow will be exported from the 'workflow_nodes_filename_export' file. '''

        # Transforming nodes variable into a list with workflows*.json filenames.
        headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {auth.token}"}
        nodes = ' '.join(self.current_workflow_node_selection).replace('Draft', self.workflows_draft_file).replace('Archived', self.workflows_archived_file).replace('Active', self.workflows_active_file).split()
        for node in nodes:
            workflow_data = export_data.read_file(self.transfer_workflows_folder, node)
            for line in workflow_data['workFlows']:
                url_get_workflow_xml_export = f"{auth.url}/{self.api_Attachments}/{line['attachmentId']}"
                request = requests.get(url_get_workflow_xml_export, headers=headers, verify=False)                
                with open(f"{self.transfer_workflows_folder}/{line['originalId']}.xml", 'wb') as file:
                    file.write(request.content)
                time.sleep(0.1)

        return


    def get_workFlowId_and_bimClassId(self):
        '''
            This function does mapping between workFlow_id and bimClass_id. 
            It uses list comprehension block for transformation list of objects into dictionary with {'workFlow_id': 'bimClass_id'} pairs.
        '''
        headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {auth.token}"}

        workFlow_id_bimClass_id_export: list = []  # temp list to store data
        if not os.path.isfile(f"{self.transfer_workflows_folder}/{self.workflowsID_and_names_from_export_server}"):
            with open(f"{self.transfer_workflows_folder}/{self.workflowsID_and_names_from_export_server}", 'w', encoding='utf-8') as file:
                file.write('Workflows: name and Id\n---------------------------------\n')            

        nodes = ' '.join(self.current_workflow_node_selection).replace('Draft', self.workflows_draft_file).replace('Archived', self.workflows_archived_file).replace('Active', self.workflows_active_file).split()
        for node in nodes:
            workflow_data = export_data.read_file(f"{self.transfer_workflows_folder}", node)
            if len(workflow_data['workFlows']) == 0:
                print(f"   - No {node[:-19]}")
                continue

            for line in workflow_data['workFlows']:
                print(f"     {line['name']}")   # display the name of the process in the output
                url_get_workFlowId_and_bimClassId = f"{auth.url}/{self.api_WorkFlows}/{line['originalId']}/BimClasses"
                request = requests.get(url_get_workFlowId_and_bimClassId, headers=headers, verify=False)
                response = request.json()
                
                with open(f"{self.transfer_workflows_folder}/{line['id']}.json", 'w', encoding='utf-8') as file:
                    json.dump(response, file, ensure_ascii=False, indent=4)

                # write list with active workFlows BimClasses ID in format [workFlow_id, bimClass_id]
                workFlow_id_bimClass_id_export.append(line['originalId'])
                workFlow_id_bimClass_id_export.append(response[0]['id'])

                # saving processes name with corresponding Id
                with open(f"{self.transfer_workflows_folder}/{self.workflowsID_and_names_from_export_server}", 'a', encoding='utf-8') as file:
                    file.write(f"{line['name']}\n{line['originalId']}\n\n")

        # List comprehension block for transformation list of values into {'workFlow_id': 'bimClass_id'} pairs.
        tmp = workFlow_id_bimClass_id_export
        tmp:list = [ [tmp[x-1]] + [tmp[x]] for x in range(1, len(tmp), 2) ]       # generation list in format [ ['a', 'b'], ['c', 'd'], ['e', 'f'] ]

        workFlow_id_bimClass_id_export = dict(tmp)                                # transform tmp list from above to dictionary using dict() function in format {"workFlow_id": "bimClass_id"}
        
        if not os.path.isfile(f"{self.transfer_workflows_folder}/{self.workflowID_bimClassID_file}"):
            with open(f"{self.transfer_workflows_folder}/{self.workflowID_bimClassID_file}", 'w', encoding='utf-8') as file:
                json.dump(workFlow_id_bimClass_id_export, file, ensure_ascii=False, indent=4)
        else:
            if workFlow_id_bimClass_id_export:  # if tmp list is True(not empty), append.
                with open(f"{self.transfer_workflows_folder}/{self.workflowID_bimClassID_file}", 'a', encoding='utf-8') as file:
                    json.dump(workFlow_id_bimClass_id_export, file, ensure_ascii=False, indent=4)
            
        logging.info("Mapping between workflow_ID and bimClass_ID: done. 'workFlow_id_bimClass_id_export.json' file is ready.")
        return True


    def export_server_info(self, url, token, username, password):
        serverId:str = license.get_serverID(url, token, username, password)
        with open(f'{self.transfer_folder}/{self.export_server_info_file}', 'w', encoding='utf-8') as file:
            file.write("{0}\n".format(auth.url.split('//')[1]))
            file.write(serverId)


    def export_workflows(self, url, token):
        export_data.create_workflows_directory()
        export_data.get_all_workflow_nodes(export_data.all_workflow_nodes_file, url, token)
        if export_data.select_workflow_nodes():
            export_data.get_workflows()
            export_data.get_workflow_xml()
            export_data.get_workFlowId_and_bimClassId()
            return True
        else:
            return False



class Import_data:

    all_workflow_nodes_file:str            = 'all_workflow_nodes_import_server.json'
    object_model_file:str                  = 'object_model_import_server.json'
    modified_object_model_file:str         = 'modified_object_model.json'
    api_Integration_ObjectModel_Import:str = 'api/Integration/ObjectModel/Import'

    def __init__(self):
        pass


    def replace_str_in_file(self, filename_2read, filename_2write, find, replace):
        '''  Function takes 4 arguments: filename to read, filename to write, what to find, what to put instead of what to find.  '''

        with open(f"{export_data.transfer_folder}/{filename_2read}", 'r', encoding='utf-8') as file:
            new_json = file.read().replace(find, replace)      # find/replace vars must be string
        with open(f"{export_data.transfer_folder}/{filename_2write}", 'w', encoding='utf-8') as file:
            file.write(new_json)


    def validate_import_server(self, url, token, username, password):
        ''' Function needs to protect export server from import procedure during a single user session. '''

        check_server_info = export_data.read_file(export_data.transfer_folder, export_data.export_server_info_file)
        if check_server_info and check_server_info.split()[1] == license.get_serverID(url, token, username, password):
            return False
        elif not check_server_info:
            return False
        else:
            self.export_serverId = check_server_info.split()[1]
            return True


    def check_for_workflows_folder(self):
        return True if os.path.isdir(export_data.transfer_workflows_folder) else False


    def get_BimClassId_of_current_process(self, workflowId):
        ''' Function returns BimClass_id of provided workFlow proccess. '''

        headers_import = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {auth.token}"}
        url_get_BimClassID_of_current_process = f"{auth.url}/{export_data.api_WorkFlows}/{workflowId}/BimClasses"
        request = requests.get(url=url_get_BimClassID_of_current_process, headers=headers_import, verify=False)
        response = request.json()
        for object in range(len(response)):
            return response[object]['id']


    def post_workflows(self):
        
        url_create_workflow_import = f"{auth.url}/{export_data.api_WorkFlows}"
        headers_import = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {auth.token}"}

        # Getting the id of the Draft node on import server
        for obj in export_data.read_file(export_data.transfer_workflows_folder, self.all_workflow_nodes_file):
            if obj['name'] == 'Draft':
                import_server_draft_node_id:str = obj['id']
                break
        
        '''  BEGIN of POST request to create workFlows  '''
        nodes_for_import:list = export_data.read_file(export_data.transfer_workflows_folder, export_data.selected_workflow_nodes_file).split()
        for node_workflows in nodes_for_import:
            workflow_data = export_data.read_file(export_data.transfer_workflows_folder, node_workflows)
            for workflow in workflow_data['workFlows']:
                post_payload = {
                                "name": workflow["name"],
                                "workFlowNodeId": import_server_draft_node_id,
                                "description": str(workflow["description"]),
                                "elements": [],
                                "type": workflow["type"]
                                }
                post_payload = json.dumps(post_payload)
                try:
                    post_request = requests.post(url=url_create_workflow_import, data=post_payload, headers=headers_import, verify=False)  # verify=False to eliminate SSL check which causes Error
                    post_response = post_request.json()
                except auth.possible_request_errors as err:
                    logging.error(f"{err}\n{post_request.text}")
                    return False

                bimClass_id = self.get_BimClassId_of_current_process(post_response['originalId'])   # 
                bimClass_list_id_export = export_data.read_file(export_data.transfer_workflows_folder, export_data.workflowID_bimClassID_file)                
                time.sleep(0.2)
                '''  END of POST request to create workFlows  '''


                '''  BEGIN OF PUT REQUEST  '''
                # adding 'elements': [], data from workFlows export into newly created workFlow
                put_payload = {
                                "name": workflow["name"],
                                "workFlowNodeId": import_server_draft_node_id,    # 0: Draft; 1: Archived; 2: Active;
                                "description": str(workflow["description"]),
                                "elements": workflow['elements'],
                                "type": workflow["type"]
                                }
                put_payload = json.dumps(put_payload)

                # Replacement of workFlow_bimClass_ID from export server with bimClass_ID newly created workFlow on import server
                changed_put_payload = put_payload.replace(bimClass_list_id_export[workflow["originalId"]], bimClass_id)

                try:
                    requests.put(url=f"{url_create_workflow_import}/{post_response['originalId']}", data=changed_put_payload, headers=headers_import, verify=False)  # /api/WorkFlows/{workFlowOriginalId}  
                    time.sleep(0.2)
                except auth.possible_request_errors as err:
                    logging.error(err)
                    logging.debug("Workflow name: " + workflow["name"])
                    print(f"Error with the workflow {workflow['name']} import. Check the logs.")
                    return False
                '''  END OF PUT REQUEST  '''        

                '''  BEGIN OF XML POST REQUEST  '''
                headers_for_xml_import = {'accept': '*/*', 'Authorization': f"Bearer {auth.token}"}    # specific headers without 'Content-type' for import .xml file. Otherwise request doesn't work!
                payload={}
                files=[ ('file',(f'{workflow["originalId"]}.xml', open(f'{export_data.transfer_workflows_folder}/{workflow["originalId"]}.xml','rb'),'text/xml')) ]
                try:           
                    post_xml_request = requests.post(url=f"{url_create_workflow_import}/{post_response['originalId']}/Diagram?contentType=file", headers=headers_for_xml_import, data=payload, files=files, verify=False)
                except auth.possible_request_errors as err:
                    logging.error(f"{err}\n{post_xml_request.text}")

                print("   - " + post_response['name'] + " " + ('' if post_xml_request.status_code == 200 else "  --->  error"))
                time.sleep(0.2)
                '''  END OF XML POST REQUEST  '''
        return True


    def check_for_object_model_file(self):
        return True if os.path.isfile(f'{export_data.transfer_folder}/{export_data.object_model_file}') else False


    def prepare_object_model_file_for_import(self):
        '''
            Function finds needed data(used two tuples as pointers: big_fish and small_fish) in object_model_import_server.json file, and place it in the object_model_export_server.json file.
            Both servers use the same data structure with key-value pairs. Thus, they have identical keys and different values. We search for values we need in object_model_import_server.json file, 
            and replace with it values in object_model_export_server.json file. Needed preparation are going to be end in modified_object_model.json file, which will be used further in import process.
        '''
        # Turn both .json files into dictionaries
        data_obj_model_import = export_data.read_file(export_data.transfer_folder, self.object_model_file)
        data_obj_model_export = export_data.read_file(export_data.transfer_folder, export_data.object_model_file)
        
        # Pointers to data we need to collect from the .json file
        big_fish: tuple = ("bimPropertyTreeNodes", "bimInterfaceTreeNodes", "bimClassTreeNodes", "bimDirectoryTreeNodes", "bimStructureTreeNodes", "rootSystemBimClass", "systemBimInterfaces", 
                            "systemBimProperties","secondLevelSystemBimClasses",)
        small_fish: tuple = ("BimProperty", "BimInterface", "BimClass", "BimDirectory", "BimStructure", "FILE_INTERFACE", "WORK_DATES_INTERFACE", "COMMERCIAL_SECRET_BIM_INTERFACE","FILE_PROPERTY", 
                            "PLANNED_START_PROPERTY","PLANNED_END_PROPERTY", "ACTUAL_START_PROPERTY", "ACTUAL_END_PROPERTY", "COMMERCIAL_SECRET_BIM_PROPERTY","ACTIVE_CLASS","FOLDER_CLASS", "DOCUMENT_CLASS",
                            "WORK_CLASS", "Файл", "Даты работы", "Коммерческая тайна", "Планируемое начало", "Планируемое окончание", "Фактическое начало", "Фактическое окончание")

        insert_data: dict = {}    # data that needs to be added to object_model_export_server.json file
        replace_data: dict = {}   # data that needs to be removed from object_model_export_server.json file

        # Collecting values from import model object .json file to put in export .json
        for key in data_obj_model_import.keys():
            if key in big_fish and isinstance(data_obj_model_import[key], list):
                insert_data.setdefault(key, {})
                for obj in data_obj_model_import[key]:
                    if isinstance(obj, dict):
                        for k,v in obj.items():
                            if v in small_fish:
                                # insert_data[key][k] = v
                                # insert_data[key]['id'] = obj['id']
                                insert_data[key][v] = obj['id']

            elif key in big_fish and isinstance(data_obj_model_import[key], dict):
                insert_data.setdefault(key, {data_obj_model_import[key]['name']: data_obj_model_import[key]['id']})
       

        # Collecting data from 'object_model_export_server.json' file to replace it with data from 'object_model_import_server.json'
        for key in data_obj_model_export.keys():
            if key in big_fish and isinstance(data_obj_model_export[key], list):
                replace_data.setdefault(key, {})
                for obj in data_obj_model_export[key]:
                    if isinstance(obj, dict):
                        for k,v in obj.items():
                            if v in small_fish:
                                # replace_data[key][k] = v
                                # replace_data[key]['id'] = obj['id']
                                replace_data[key][v] = obj['id']
                               
            elif key in big_fish and isinstance(data_obj_model_export[key], dict):
                replace_data.setdefault(key, {data_obj_model_export[key]['name']: data_obj_model_export[key]['id']})

        # Making a copy of the 'object_model_export_server.json' file which we will prepare for export
        shutil.copyfile(f"{export_data.transfer_folder}/{export_data.object_model_file}", f"{export_data.transfer_folder}/{self.modified_object_model_file}")

        # Replacement of values in .json file       
        for key,value in replace_data.items():
            for key_from_export_json, value_from_export_json in value.items():
                try:
                    self.replace_str_in_file(self.modified_object_model_file, self.modified_object_model_file, value_from_export_json, insert_data[key][key_from_export_json])
                    time.sleep(0.1)
                except (KeyError, ValueError, TypeError, UnicodeError, UnicodeDecodeError, UnicodeEncodeError, SyntaxError) as err:
                    logging.error(err)
                    return False

        logging.info(f"Preparation object model file is finished. '{export_data.object_model_file}' was altered into a '{self.modified_object_model_file}' file.")
        print("\n   - preparing object model file:        done")
        return True


    def fix_defaulValues_in_object_model(self):
        '''  The function checks for 'defaultValues' keys in 'bimProperties'. If all values in the list are null, it will be replaced with an empty list [].  '''

        modified_obj_model_json = export_data.read_file(export_data.transfer_folder, self.modified_object_model_file)
        count = 0
        with open(f"{export_data.transfer_folder}/{self.modified_object_model_file}", 'w', encoding='utf-8') as file:
            for bimClasses_dict in modified_obj_model_json['bimClasses']:    # bimClasses - list with dictionaries inside
                for bimProperties_dict in bimClasses_dict['bimProperties']:  # bimProperties - list with dictionaries inside               
                    for defaultValues in bimProperties_dict.get('defaultValues'):                
                        if all(value == None for value in defaultValues.values()):                    
                            bimProperties_dict['defaultValues'] = []
                            count += 1                    

            json.dump(modified_obj_model_json, file, ensure_ascii=False, indent=4)
        if count > 0:
            print(f"   - corrupted 'defaultValues':       {count}")
        logging.info(f"Fixing defaultValues in '{self.modified_object_model_file}' file is finished. Corrupted defaulValues: {count}")
        return True


    def post_object_model(self):

        headers_import = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {auth.token}"}
        url_post_object_model:str = f'{auth.url}/{self.api_Integration_ObjectModel_Import}'
        with open(f"{export_data.transfer_folder}/{self.modified_object_model_file}", "r", encoding="utf-8") as file:
            data = file.read()
        # json_payload = json.dumps(data, ensure_ascii=False) # Doesn't work with json.dumps if read from file   
        try:
            post_request = requests.post(url=url_post_object_model, data=data.encode("utf-8"),  headers=headers_import, verify=False)
        except auth.possible_request_errors as err:
            logging.error(err)
            print("Error with POST object model. Check the logs.")
            return False

        if post_request.status_code != 200:
            logging.error(f"\n{post_request.text}")
            print("   - post object model:                  error ", post_request.status_code)
            return False
        else:
            print("   - post object model:                  done")
            return True


    def import_object_model(self, url, token, username, password):
        server_validation:bool = import_data.validate_import_server(url, token, username, password)
        object_model_file_exists:bool = import_data.check_for_object_model_file()
        if object_model_file_exists and server_validation:
            export_data.get_object_model(import_data.object_model_file, url, token)
            import_data.prepare_object_model_file_for_import()
            import_data.fix_defaulValues_in_object_model()
            import_data.post_object_model()
            return True
        else:
            print("No object_model for import." if not import_data.check_for_object_model_file() else "Can't perform import procedure on the export server.")
            return False


    def import_workflows(self, url, token, username, password):
        server_validation:bool = import_data.validate_import_server(url, token, username, password)
        workflows_folder_exists:bool = import_data.check_for_workflows_folder()
        if workflows_folder_exists and server_validation:
            export_data.get_all_workflow_nodes(import_data.all_workflow_nodes_file, url, token)
            import_data.post_workflows()
            return True
        else:
            print("No workflows for import." if not import_data.check_for_workflows_folder() else "Can't perform import procedure on the export server.")
            return False



class AppMenu:

    def welcome_info_note(self):
        ''' first note to be displayed '''
        print(f"\nv{version}    \
                \nnote: applicable with BIM version 101 and higher.")

    def define_purpose_and_menu(self):
        ''' Define what the user would like to do '''

        self.menu_user_command = input("\nCommand (m for help): ").lower()
        main_menu              =       "\n  License:                                         \
                                        \n   1  check license                                \
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
                                        \n   7 export workflows                              \
                                        \n   8 import object model                           \
                                        \n   9 import workflows                              \
                                        \n  09 clean transfer_files folder                   \
                                        \n                                                   \
                                        \n  Main:                                            \
                                        \n   m  print this menu                              \
                                        \n   c  connect to another server                    \
                                        \n   q  exit"

        if self.menu_user_command == 'm':
            print(main_menu)
        elif self.menu_user_command == '1':
            return 'check_license'
        elif self.menu_user_command == '2':
            return 'server_id'
        elif self.menu_user_command == '3':
            return 'apply_license'
        elif self.menu_user_command == '4':
            return 'delete_active_license'
        elif self.menu_user_command == '5':
            return 'truncate_user_objects'
        elif self.menu_user_command == '5i':
            return 'truncate_user_objects_info'
        elif self.menu_user_command == '6':
            return 'export_object_model'
        elif self.menu_user_command == '7':
            return 'export_workflows'
        elif self.menu_user_command == '8':
            return 'import_object_model'
        elif self.menu_user_command == '9':
            return 'import_workflows'
        elif self.menu_user_command == '09':
            return 'clean_transfer_files_directory'
        elif self.menu_user_command == 'c':
            return 'connect_to_another_server'
        elif self.menu_user_command == 'q':
            return 'q'


def main():

    if not auth.establish_connection():  # if connection was not established, do not continue
        return False

    # remember if the privileges where granted, to restore initial state after the finish
    privileges_were_granted:bool = license.grant_privileges(auth.url, auth.token, auth.username, auth.password)

    while True:
        command = appMenu.define_purpose_and_menu()

        # License
        if command == 'check_license':
            license.display_licenses(auth.url, auth.token, auth.username, auth.password)
        elif command == 'server_id':
            print(f"\n   - serverId: {license.get_serverID(auth.url, auth.token, auth.username, auth.password)}")
        elif command == 'apply_license':
            license.put_license(auth.url, auth.token, auth.username, auth.password)
        elif command == 'delete_active_license':
            license.delete_license(auth.url, auth.token, auth.username, auth.password)

        # UserObjects table
        elif command == 'truncate_user_objects':
            user.delete_user_objects(auth.url, auth.token)
        elif command == 'truncate_user_objects_info':
            print(user.delete_user_objects.__doc__)

        # Export
        elif command == 'export_object_model' or command == 'export_workflows':
            if export_data.is_first_launch_export_data:
                export_data.create_folder_for_transfer_procedures()
            if command == 'export_object_model':
                export_data.export_server_info(auth.url, auth.token, auth.username, auth.password)
                export_data.get_object_model(export_data.object_model_file, auth.url, auth.token)
            elif command == 'export_workflows':
                export_data.export_server_info(auth.url, auth.token, auth.username, auth.password)
                export_data.export_workflows(auth.url, auth.token)

        # Import
        elif command == 'import_workflows':
            import_data.import_workflows(auth.url, auth.token, auth.username, auth.password)
        elif command == 'import_object_model':
            import_data.import_object_model(auth.url, auth.token, auth.username, auth.password)

        # Generic
        elif command == 'clean_transfer_files_directory':
            export_data.clean_transfer_files_directory()
        elif command == 'q':
            if privileges_were_granted:
                user.delete_created_system_role_and_delete_user(auth.url)
            break
        elif command == 'connect_to_another_server':
            if privileges_were_granted:
                user.delete_created_system_role_and_delete_user(auth.url)
                privileges_were_granted = False
            
            if not auth.establish_connection():
                return False
            privileges_were_granted = license.grant_privileges(auth.url, auth.token, auth.username, auth.password)


if __name__=='__main__':
    # creating classes instances
    logs        = Logs()
    appMenu     = AppMenu()
    auth        = Auth()
    user        = User()
    license     = License()
    export_data = Export_data()
    import_data = Import_data()

    appMenu.welcome_info_note()
    main()

