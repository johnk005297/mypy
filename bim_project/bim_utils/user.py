#
#
import logging
import time
import requests
import json
import random
import string
import auth
import license


class User:

    __api_UserObjects_all:str        = 'api/UserObjects/all'
    __api_Users_currentUser:str      = 'api/Users/current-user'
    __api_Users:str                  = 'api/Users'
    __api_Users_full:str             = 'api/Users/full'
    __api_SystemRoles:str            = 'api/SystemRoles'
    __api_Users_AddSystemRole:str    = 'api/Users/AddSystemRole'
    __api_Users_RemoveSystemRole:str = 'api/Users/RemoveSystemRole'
    Auth_superuser                   = auth.Auth(username='johnny_mnemonic', password='Qwerty12345!') # Create Auth class instance for new user
    License                          = license.License()
    possible_request_errors          = Auth_superuser.possible_request_errors
    _su_system_role_id               = None
    _su_system_role_name             = None


    def __init__(self):
        # superuser needs for granting privileges, in cases where initial user doesn't have them.
        self.initial_user               = None # will be assigned to dict from the get_current_user method
        self.superuser                  = None # will be assigned to dict from the get_current_user method
        self.token                      = None # this variable will be assigned in cases when we need to re-login


    def __getattr__(self, item):
        raise AttributeError("User class has no such attribute: " + item)


    def check_permissions(self, url, token, username, password, permissions_to_check):

        is_active_license:bool = self.License.get_license_status(url, token, username, password)
        if is_active_license and not self.check_user_privileges(url, token, username, permissions_to_check):
            return False
        elif not is_active_license:
            logging.info("No active license. Can't perform privileges check.")
            return True  # Need to return True, because without an active license it isn't possible to perform any check
        else:
            return True


    def delete_user_objects(self, url, token):
        '''
            UserObjects – хранилище Frontend-данных на Backend.
            Здесь хранятся всяческие кеши, черновики обходов, выбранные задачи и прочее.
            Работа с хранилищем не предполагает валидацию, миграции и прочее. Таким образом, если модели данных меняются, работа с хранилищем, 
            уже наполненным какими-то данными может привести к ошибкам. Чтобы уберечь пользователя от этого, необходимо очищать таблицу.
        '''
        
        headers = {'accept': '*/*', 'Content-type': 'text/plane', 'Authorization': f"Bearer {token}"}
        try:
            user_obj_request = requests.delete(url=f"{url}/{self.__api_UserObjects_all}", headers=headers, verify=False)
            if user_obj_request.status_code == 204:
                print("\n   - bimeisterdb.UserObjects table was cleaned successfully.")
            else:
                print("Something went wrong. Check the log.")
        except self.possible_request_errors as err:
            logging.error(err)


    def get_all_users(self, url, token):
        headers = {'accept': '*/*', 'Content-type': 'text/plain', 'Authorization': f"Bearer {token}"}
        request = requests.get(url=f"{url}/{self.__api_Users_full}", headers=headers, verify=False)
        users = request.json()
        return users # list with dictionaries inside


    def get_current_user(self, url, token):
        ''' Getting info about current user. Response will provide a dictionary of values. '''

        url_get_current_user = f"{url}/{self.__api_Users_currentUser}"
        headers = {'accept': '*/*', 'Content-type': 'text/plain', 'Authorization': f"Bearer {token}"}
        try:
            request = requests.get(url_get_current_user, headers=headers, verify=False)
            time.sleep(0.15)
            response = request.json()
            if request.status_code != 200:
                logging.error(request.text)
        except self.possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")
            return False
        return response


    def check_user_privileges(self, url, token, username, permissions_to_check:tuple):
        ''' Function requires to pass permissions needed to be checked, along with url, token and username. '''
    
        user_system_roles_id: list = []  # list to collect user's system roles Id.

        headers = {'Content-type':'text/plane', 'Authorization': f"Bearer {token}"}
        request = requests.get(url=f"{url}/{self.__api_Users}", headers=headers, verify=False)                                
        response = request.json()
        if request.status_code != 200:
            logging.error(f"{self.__api_Users}: {request.text}")
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
                request = requests.get(url=f"{url}/{self.__api_SystemRoles}/{id}", headers=headers, verify=False)
                response = request.json()
            except self.possible_request_errors as err:
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

        ''' Create a new user or Activate if already exists '''
        payload_create_user = {
                                "firstName": "Johnny",
                                "lastName": "Mnemonic",
                                "middleName": "no_middle_name",
                                "userName": self.Auth_superuser.username,
                                "displayName": "Johnny_Mnemonic",
                                "password": self.Auth_superuser.password,
                                "phoneNumber": "+71234567890",
                                "email": "the_matrix@exists.neo",
                                "birthday": "1964-09-02T07:15:07.731Z",
                                "position": "The_one"
                              }
        data = json.dumps(payload_create_user)

        all_users:list = self.get_all_users(url, token)
        post_superuser_request = requests.post(url=url + '/' + self.__api_Users, headers=headers_create_user_and_system_role, data=data, verify=False)
        if post_superuser_request.status_code == 201:
            self.superuser = post_superuser_request.json()
        elif post_superuser_request.status_code == 409 and post_superuser_request.json()['error']['key'] == 'Auth.AlreadyExists.User.UserAlreadyExists':
            for user in all_users:
                if user.get('userName') == self.Auth_superuser.username and (user.get('isDeleted') or user.get('isDisabled')):
                    self.superuser = user
                    put_request = requests.put(url=f"{url}/{self.__api_Users}/{user.get('id')}/activate", headers=headers_create_user_and_system_role, verify=False)
                    if not put_request.status_code in (200, 201):
                        logging.error(f"'{self.Auth_superuser.username}' user wasn't activated")
                        return False
                elif user.get('userName') == self.Auth_superuser.username:
                    self.superuser = user
                    break
        elif post_superuser_request.status_code == 403:
            print("Current user don't have privileges for required procedure. Also don't have permissions to create users, so it could be temporary avoided.")
            logging.error(post_superuser_request.text)
            return False

        '''  Create a new system role  '''
        self.su_system_role_name:str = self.create_random_name()
        payload_create_system_role = {
                                        "name": self.su_system_role_name,
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
            request = requests.post(url=url + '/' + self.__api_SystemRoles, headers=headers_create_user_and_system_role, data=data, verify=False)
            if request.status_code == 409 and request.json()['error']['key'] == 'Auth.AlreadyExists.SystemRole':
                logging.warning("Superuser system role already exists.")
                altered_data = data.replace(self.su_system_role_name, self.create_random_name())
                request = requests.post(url=url + '/' + self.__api_SystemRoles, headers=headers_create_user_and_system_role, data=altered_data, verify=False)
            time.sleep(0.05)
            self.su_system_role_id = request.json()
            logging.info("System role was created successfully.") if request.status_code == 201 else logging.error(request.text)
        except self.possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")
            return False

        ''' Add a new system role to a superuser '''
        payload_add_system_role = {
                                    "systemRoleId": self.su_system_role_id, 
                                    "userId": self.superuser['id']
                                  }
        data = json.dumps(payload_add_system_role)
        try:
            request = requests.post(url=url + '/' + self.__api_Users_AddSystemRole, headers=headers_create_user_and_system_role, data=data, verify=False)
            if request.status_code != 204:
                pass
            time.sleep(0.05)
            logging.info(f"Add a new system role to a new user. \
                          \nSystem role '{self.su_system_role_id}' to user '{self.Auth_superuser.username}' added successfully.") if request.status_code in (201, 204) else logging.error(request.text)
        except self.possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")

        ''' 
            Using credentianls of the superuser, up privileges for current user we are working under(default, admin).
            Need to create all we need to manipulate with roles and users.
        '''

        ''' Adding created role to current user '''
        # need to save initial user's data whom we need to up privileges
        self.initial_user = self.get_current_user(url, token)

        # logging in under superuser account
        self.Auth_superuser.providerId = self.Auth_superuser.get_local_providerId(url) # getting 'Local' Provider Id for superUser(new user)
        self.Auth_superuser.get_user_access_token(url, self.Auth_superuser.username, self.Auth_superuser.password, self.Auth_superuser.providerId)

        # adding system role to initial user we connected
        headers_add_system_role_to_current_user = {'accept': '*/*', 'Content-type': 'application/json-patch+json', 'Authorization': f"Bearer {self.Auth_superuser.token}"}
        payload_add_system_role = {
                                    "systemRoleId": self.su_system_role_id,
                                    "userId": self.initial_user['id']
                                  }
        data = json.dumps(payload_add_system_role)                                
        try:
            request = requests.post(f"{url}/{self.__api_Users_AddSystemRole}", headers=headers_add_system_role_to_current_user, data=data, verify=False)
            time.sleep(0.05)         
            logging.info(f"Adding created role to current user. \
                            \nSystem role '{self.su_system_role_id}' to user '{self.initial_user['userName']}' added successfully.") if request.status_code in (201, 204) else logging.error(request.text)
        except self.possible_request_errors as err:
            logging.error(f"{err}\n{request.text}")
            return False

        return True
    

    def delete_superuser_system_role_and_delete_superuser(self, url, username, password, providerId): # args are passing from the main module


        def remove_role_from_user(user_id, username, system_role_id, token):
            ''' Remove role from provided user. '''

            headers_remove_role_from_user = {'accept': '*/*', 'Content-type': 'application/json-patch+json', 'Authorization': f"Bearer {token}"}
            payload_remove_role_from_user = {
                                                "systemRoleId": system_role_id,
                                                "userId": user_id
                                            }
            data = json.dumps(payload_remove_role_from_user)
            try:
                request = requests.post(url=url + '/' + self.__api_Users_RemoveSystemRole, headers=headers_remove_role_from_user, data=data, verify=False)
                time.sleep(0.10)
                if request.status_code in (201, 204):
                    logging.info(f"System role '{system_role_id}' from user '{username}' removed successfully.")
            except self.possible_request_errors as err:
                logging.error(f'{err}\n{request.text}')
                return False


        def delete_system_role():
            ''' Delete created system role '''

            url_delete_system_role = f"{url}/{self.__api_SystemRoles}/{self.su_system_role_id}"
            headers = {'accept': '*/*', 'Authorization': f"Bearer {self.token}"}
            try:
                request = requests.delete(url=url_delete_system_role, headers=headers, verify=False)
                if request.status_code in (201, 204):
                    logging.info(f"Deletion created system role.   \
                                    \nNew role '{self.su_system_role_id}' was deleted successfully.")
                else:
                    logging.error(request.text)
            except self.possible_request_errors as err:
                logging.error(f"{err}\n{request.text}")
                return False
            return True


        def delete_user():
            ''' Delete created user '''

            headers = {'accept': '*/*', 'Authorization': f"Bearer {self.token}"}
            url_delete_user = f"{url}/{self.__api_Users}/{self.superuser['id']}"
            try:
                request = requests.delete(url=url_delete_user, headers=headers, verify=False)
                if request.status_code in (201, 204):
                    logging.info(f"Created user <{self.superuser['userName']}> was deleted successfully.")
                else:
                    logging.error(request.text)
            except self.possible_request_errors as err:
                logging.error(f"{err}\n{request.text}")
                return False
            return True


        remove_role_from_user(self.initial_user['id'], self.initial_user['userName'], self.su_system_role_id, self.Auth_superuser.token)
        self.token = auth.Auth().get_user_access_token(url, username, password, providerId) # login back as initial user to delete both created: system role and user
        remove_role_from_user(self.superuser['id'], self.Auth_superuser.username, self.su_system_role_id, self.token)
        delete_system_role()
        delete_user()