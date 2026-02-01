
import requests

import logging
import time
import json

import license
from tools import Tools

logger = logging.getLogger(__name__)

class User:

    __api_UserObjects_all: str = 'api/UserObjects/all'
    __api_Users_currentUser: str = 'api/Users/current-user'
    __api_Users: str = 'api/Users'
    __api_Users_full: str = 'api/Users/full'
    __api_SystemRoles: str = 'api/SystemRoles'
    __api_Users_AddSystemRole: str = 'api/Users/AddSystemRole'
    __api_Users_RemoveSystemRole: str = 'api/Users/RemoveSystemRole'
    License = license.License()
    _License_server_exception: bool = False


    def __init__(self):
        pass

    def __getattr__(self, item):
        raise AttributeError("User class has no such attribute: " + item)

    def delete_user_objects(self, url, token):
        """ UserObjects – хранилище Frontend-данных на Backend.
            Здесь хранятся всяческие кеши, черновики обходов, выбранные задачи и прочее.
            Работа с хранилищем не предполагает валидацию, миграции и прочее. Таким образом, если модели данных меняются, работа с хранилищем, 
            уже наполненным какими-то данными может привести к ошибкам. Чтобы уберечь пользователя от этого, необходимо очищать таблицу.
        """

        headers = {'accept': '*/*', 'Content-type': 'text/plain', 'Authorization': f"Bearer {token}"}
        try:
            response = requests.delete(url=f"{url}/{self.__api_UserObjects_all}", headers=headers, verify=False)
            if response.status_code == 204:
                logger.info(response)
                print("\n   - bimeisterdb.UserObjects table was cleaned successfully.")
            else:
                print("Something went wrong. Check the log.")
        except Exception as err:
            logger.error(err)

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
                logger.error(request.text)
        except Exception as err:
            logger.error(f"{err}\n{request.text}")
            return False
        return response

    def check_user_permissions(self, url, token, username, password, permissions_to_check:tuple):
        ''' Function requires to pass permissions needed to be checked, along with url, token and username. '''

        self.License.privileges_checked = True
        # If there is no active license on the server, no privileges checks could be made.
        if not self.License.get_license_status(url, token, username, password):
            message = "No active license on the server. Can't perform privileges check."
            logger.info(message)
            return True # Can't perform check, so need to return True

        user_system_roles_id: list = []  # list to collect user's system roles Id.

        headers = {'Content-type':'text/plain', 'Authorization': f"Bearer {token}"}
        request = requests.get(url=f"{url}/{self.__api_Users}", headers=headers, verify=False)
        response = request.json()
        if  request.status_code == 500:
            logger.error(f"{self.__api_Users}: {request.text}")
            self._License_server_exception = True
            if json.loads(request.text)['type'] == 'LicenseServiceClientException':
                print(f"Error: {request.status_code}. LicenseServiceClientException. Check the logs. ")
                self._License_server_exception = True
            return False
        elif request.status_code != 200:
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
            except Exception as err:
                logger.error(f"{err}\n{request.text}")

            for permission in permissions_to_check:
                if permission in response['permissions']:
                    continue
                else:
                    return False
            return True

    def create_or_activate_superuser(self, url, token, username, password):
        '''  Function checks for a special user with super privileges. If there is a needed user it will pass, if there isn't or deactivated, it will be created/activated.  '''

        headers = {'accept': '*/*', 'Content-type': 'application/json-patch+json', 'Authorization': f"Bearer {token}"}

        ''' Create a new user or Activate if already exists '''
        payload = {
                    "firstName": "Johnny"
                    ,"lastName": "Mnemonic"
                    ,"middleName": "no_middle_name"
                    ,"userName": username
                    ,"displayName": "Johnny_Mnemonic"
                    ,"password": password
                    ,"phoneNumber": "+71234567890"
                    ,"email": "the_matrix@exists.neo"
                    ,"birthday": "1964-09-02T07:15:07.731Z"
                    ,"position": "The_one"
                  }
        data = json.dumps(payload)

        all_users:list = self.get_all_users(url, token)
        post_superuser_request = requests.post(url=url + '/' + self.__api_Users, headers=headers, data=data, verify=False)
        if post_superuser_request.status_code == 201:
            superuser = post_superuser_request.json()
        elif post_superuser_request.status_code == 409 and post_superuser_request.json()['error']['key'] == 'Auth.AlreadyExists.User.UserAlreadyExists':
            for user in all_users:
                if user.get('userName') == username and (user.get('isDeleted') or user.get('isDisabled')):
                    superuser = user
                    put_request = requests.put(url=f"{url}/{self.__api_Users}/{user.get('id')}/activate", headers=headers, verify=False)
                    if not put_request.status_code in (200, 201):
                        logger.error(f"'{username}' user wasn't activated")
                        return False
                elif user.get('userName') == username:
                    superuser = user
                    break
        elif post_superuser_request.status_code == 403:
            print("Current user don't have sufficient privileges.")
            logger.error(post_superuser_request.text)
            return False
        return superuser

    def create_system_role(self, url, token):
        '''  Create a new system role  '''

        headers = {'accept': '*/*', 'Content-type': 'application/json-patch+json', 'Authorization': f"Bearer {token}"}
        system_role_name: str = Tools.create_random_name()
        payload = {
                    "name": system_role_name,
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
        data = json.dumps(payload)
        try:
            request = requests.post(url=url + '/' + self.__api_SystemRoles, headers=headers, data=data, verify=False)
            if request.status_code == 409 and request.json()['error']['key'] == 'Auth.AlreadyExists.SystemRole':
                logger.warning("System role already exists.")
                altered_data = data.replace(system_role_name, Tools.create_random_name())
                request = requests.post(url=url + '/' + self.__api_SystemRoles, headers=headers, data=altered_data, verify=False)
            time.sleep(0.05)
            system_role_id = request.json()
            logger.info("System role was created successfully.") if request.status_code == 201 else logger.error(request.text)
        except Exception as err:
            logger.error(f"{err}\n{request.text}")
            return False
        return system_role_id

    def add_system_role_to_user(self, url, token, user_id, username, system_role_id):
        ''' Add system role to a user. '''

        headers = {'accept': '*/*', 'Content-type': 'application/json-patch+json', 'Authorization': f"Bearer {token}"}
        payload = {
                    "systemRoleId": system_role_id, 
                    "userId": user_id
                  }
        data = json.dumps(payload)
        try:
            request = requests.post(url=url + '/' + self.__api_Users_AddSystemRole, headers=headers, data=data, verify=False)
            time.sleep(0.05)
            logger.info(f"System role '{system_role_id}' to user '{username}' added successfully.")
        except Exception as err:
            logger.error(f"{err}\n{request.text}")
            return False
        
        return True

    def remove_system_role_from_user(self, url, token, user_id, username, system_role_id):
        ''' Remove role from provided user. '''

        headers = {'accept': '*/*', 'Content-type': 'application/json-patch+json', 'Authorization': f"Bearer {token}"}
        payload = {
                    "systemRoleId": system_role_id,
                    "userId": user_id
                  }
        data = json.dumps(payload)
        try:
            request = requests.post(url=url + '/' + self.__api_Users_RemoveSystemRole, headers=headers, data=data, verify=False)
            time.sleep(0.10)
        except Exception as err:
            logger.error(f'{err}\n{request.text}')
            return False
        if request.status_code in (200, 201, 204):
            logger.info(f"System role '{system_role_id}' from user '{username}' removed successfully.")
        return True

    def delete_system_role(self, url, system_role_id, token):
        ''' Delete created system role '''

        url_delete_system_role = f"{url}/{self.__api_SystemRoles}/{system_role_id}"
        headers = {'accept': '*/*', 'Authorization': f"Bearer {token}"}
        try:
            request = requests.delete(url=url_delete_system_role, headers=headers, verify=False)
        except Exception as err:
            logger.error(f"{err}\n{request.text}")
            return False
        logger.info(f"New role '{system_role_id}' was deleted successfully.") if request.status_code in (200, 201, 204) else False
        return True

    def delete_user(self, url, token, user_id, username):
        ''' Delete created user '''

        headers = {'accept': '*/*', 'Authorization': f"Bearer {token}"}
        url_delete_user = f"{url}/{self.__api_Users}/{user_id}"
        try:
            request = requests.delete(url=url_delete_user, headers=headers, verify=False)
        except Exception as err:
            logger.error(f"{err}\n{request.text}")
            return False
        logger.info(f"Created user <{username}> was deleted successfully.") if request.status_code in (200, 201, 204) else False
        return True
