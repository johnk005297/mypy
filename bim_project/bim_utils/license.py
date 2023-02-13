import os
import json
import requests
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
disable_warnings(InsecureRequestWarning)
import logging
import time
from colorama import init, Fore
init(autoreset=True)
from datetime import date
from datetime import datetime
import auth
import user

class License:

    api_License:str               = "api/License"
    api_License_serverId:str      = "api/License/serverId"
    permissions_to_check:tuple    = ('LicensesRead', 'LicensesWrite')
    possible_request_errors:tuple = auth.Auth().possible_request_errors
    User                          = user.User()


    def __init__(self):
        self.privileges_granted:bool    = False
        self.privileges_check_count:int = 0


    def __getattr__(self, item):
        print("License class instance has no such attribute: " + item)
        return False


    def check_permissions(self, url, token, username, password):

        is_active_license:bool = self.get_license_status(url, token, username, password)
        if is_active_license and not self.User.check_user_privileges(url, token, username, self.permissions_to_check):
            return False
        elif not is_active_license:
            logging.info("No active license. Can't perform privileges check.")
            return True  # Need to return True, because without an active license it isn't possible to perform any check
        else:
            return True


    def read_license_token(self):
        ''' Check if there is a license.lic file, or ask user for token. '''

        if os.path.isfile(f"{os.getcwd()}/license.lic"):
            with open("license.lic", "r", encoding="utf-8") as file:    # get license_token from the .lic file and put it into data_from_lic_file dictionary
                self.license_token = file.read().split()[0].strip("\"")
        else:
            self.license_token = input("\nThere is no 'license.lic' file in the folder.\nEnter license token manually or 'q' for exit: ")
            if len(self.license_token) < 10 or self.license_token.lower() == 'q':
                print("\nNo license token has been provided. Exit.")
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
        except self.possible_request_errors as err:
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
            elif license['isActive'] and license['licenseID'] != '00000000-0000-0000-0000-000000000000':
                return True
            elif license['licenseID'] == '00000000-0000-0000-0000-000000000000' and license['until'] > str(date.today()) + 'T' + datetime.now().strftime("%H:%M:%S"):
                return True
            else:
                logging.warning('Unknown case in get_license_status module.')
                return False
        return False


    def get_serverID(self, url, token):

        headers = {'accept': '*/*', 'Content-type':'text/plane', 'Authorization': f"Bearer {token}"}
        url_get_serverId:str = url + '/' + self.api_License_serverId
        request = requests.get(url=url_get_serverId, data="", headers=headers, verify=False)
        return request.text
        


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