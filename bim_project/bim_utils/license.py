import os
import json
import requests
import base64
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

class License:

    __api_License:str              = "api/License"
    __api_License_serverId:str     = "api/License/serverId"
    _permissions_to_check:tuple    = ('LicensesRead', 'LicensesWrite')

    # This SUID and UPP licenses are actually two parts of one license. Have know idea why it was designed that way.
    __UPP_SUID_lic:tuple = ('Платформа BIMeister, Bimeister УПП', 'Платформа BIMeister, Bimeister СУИД')
    possible_request_errors:tuple  = auth.Auth().possible_request_errors
    privileges_granted:bool = False
    privileges_checked:bool = False


    def __init__(self):
        pass


    def __getattr__(self, item):
        raise AttributeError('License class has no such attribute: ' + item)


    def decode_base64(self, encoded_string):
        ''' Function decodes base64 encoded string and returns dictionary of values. Current version example of license data: 
            {
             'version': '1', 'LicenseID': 'a7bfd7df-6b90-4ca1-b40e-07d99f38308f', 'ServerID': 'eeaa4ad2-28b7-4eb7-8bfb-3fdd40d257a5', 'From': '10.03.2023 00:00:01', 
             'Until': '25.12.2023 23:59:59', 'NumberOfUsers': '100', 'NumberOfIpConnectionsPerUser': '0', 'Product': 'BimeisterEDMS', 'LicenceType': 'Trial', 
             'ActivationType': 'Offline', 'Client': 'Rupert Pupkin', 'ClientEmail': 'Rupert.Pupkin@fun.org', 'Organisation': 'sandbox-3.imp.bimeister.io',
             'IsOrganisation': 'False', 'OrderId': 'Стенд для демо', 'CrmOrderId': 'IMSD-604', 'sign': '<activation_key>'
            }
        '''
        decoded_string = base64.b64decode(encoded_string).decode('utf-8')
        return dict([ [x.split('=', 1)[0].strip(), x.split('=', 1)[1].strip()] for x in decoded_string ])


    def read_license_token(self, filename=''):
        ''' Check if there is a license.lic file, or ask user for token. '''

        if os.path.isfile(f"{os.getcwd()}/{filename}"):
            with open(filename, "r", encoding="utf-8") as file:    # get license_token from the .lic file and put it into data_from_lic_file dictionary
                self.license_token = file.read().split()[0].strip("\"")
        else:
            self.license_token = input("\nThere is no 'license.lic' file in the folder. \
                                        \nEnter license token manually or 'q' for exit: ")
            if len(self.license_token) < 10 or self.license_token.lower() == 'q':
                print("\nNo license token has been provided. Exit.")
                logging.info("No license token has been provided by the user.")
                return False
        return True


    def get_licenses(self, url, token, username, password):
        ''' Get all the licenses in the system '''

        url_get_licenses:str = f'{url}/{self.__api_License}'
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


    def serverId_validation(self, url, token, username, password):
        ''' Check for a known bag with different serverId in serverInfo in Minio. ServerId should be the same in all licenses.'''

        licenses = self.get_licenses(url, token, username, password)
        serverId = self.get_serverID(url, token)
        for license in licenses:
            if serverId != license['serverId']:
                return False
        return True       


    def get_license_status(self, url, token, username, password):
        ''' Check if there is an active license. Return True/False. '''

        licenses = self.get_licenses(url, token, username, password)
        current_date:str = str(date.today()) + 'T' + datetime.now().strftime("%H:%M:%S")
        for license in licenses:
            if license['activeUsers'] > license['activeUsersLimit'] and license['isActive'] and license['until'] > current_date:
                logging.error(f"Users limit was exceeded! Active users: {license['activeUsers']}. Users limit: {license['activeUsersLimit']}")
                print("Users limit is exceeded!")
                return False
            elif license['isActive'] and license['licenseID'] != '00000000-0000-0000-0000-000000000000' and license['until'] > current_date:
                return True
            elif license['licenseID'] == '00000000-0000-0000-0000-000000000000' and license['until'] > current_date:
                return True
            else:
                continue
        return False


    def get_serverID(self, url, token):

        headers = {'accept': '*/*', 'Content-type':'text/plane', 'Authorization': f"Bearer {token}"}
        url_get_serverId:str = url + '/' + self.__api_License_serverId
        request = requests.get(url=url_get_serverId, data="", headers=headers, verify=False)
        message:str = "Current user don't have sufficient privileges."
        return request.text if request.status_code == 200 else message


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

                else: continue
        else:
            logging.error("Unpredictable behaviour(license status) in License class.")


    def delete_license(self, url, token, username, password):
        '''   Delete active license, if there is one.   '''    

        headers = {'accept': '*/*', 'Content-type': 'text/plane', 'Authorization': f"Bearer {token}"}
        licenses = self.get_licenses(url, token, username, password)
        active_licenses = dict()
        ''' 
            There is a default trial license from the installation with no ID(000..00). It cannot be deactivated, so we simply ignore it.
            After new license will be applied, system trial license will disappear automatically.
        '''
        for license in licenses:
            if license.get('isActive') and license['licenseID'] != '00000000-0000-0000-0000-000000000000':
                active_licenses.setdefault(license['name'], license['licenseID'])

        if not active_licenses:
            print("\n   - no active licenses have been found in the system.")
        else:
            for lic in self.__UPP_SUID_lic:
                if active_licenses.get(lic):
                    request = requests.delete(url=f"{url}/{self.__api_License}/{active_licenses[lic]}", headers=headers, verify=False)
                    if request.status_code in (200, 201, 204):
                        print(Fore.GREEN + f"   - license '{lic}': {active_licenses.pop(lic)} has been deactivated!")
                    else:
                        logging.error('%s', request.text)
                        print(Fore.RED + f"   - license '{lic}' has not been deactivated! Check the logs.")

            if not active_licenses:
                return
            for name, id in active_licenses.items():
                url_delete_license = f"{url}/{self.__api_License}/{id}"
                request = requests.delete(url=url_delete_license, headers=headers, verify=False)
                if request.status_code in (200, 201, 204):
                    print(Fore.GREEN + f"   - license '{name}': {id} has been deactivated!")
                else:
                    logging.error('%s', request.text)
                    print(Fore.RED + f"   - license '{name}': {id} has not been deactivated! Check the logs.")


    def post_license(self, url, token):
        ''' Function returns a tuple of license id and license name if post was successful. '''

        headers = {'accept': 'text/plane', 'Content-Type': 'application/json-patch+json', 
        'Authorization': f"Bearer {token}"}

        if self.read_license_token():
            data = json.dumps(self.license_token)
            request = requests.post(url=f'{url}/{self.__api_License}', headers=headers, data=data, verify=False)
            response = request.json()
            time.sleep(0.15)
            if request.status_code in (200, 201, 204,):
                print(Fore.GREEN + f"\n   - new license {response['product']} has been posted successfully!")
                # {'product': 'BimeisterEDMS', 'licenseID': '', 'serverID': '', 'isActive': True, 'until': '2023-12-25T23:59:59', 'numberOfUsers': 50, 'numberOfIpConnectionsPerUser': 0}
                return response['licenseID'], response['product']
            else:
                logging.error('%s', request.text)
                print(Fore.RED + f"\n   - new license has not been posted!")
                return False


    def put_license(self, url, token, license_id=''):

        headers = {'accept': '*/*', 'Content-type': 'text/plane', 'Authorization': f"Bearer {token}"}
        # all the active licenses will be deactivated, if user forgot to do it, and if there are any active
        # for license in self.get_licenses(url, token, username, password):
        #     if license['isActive'] == True and license['licenseID'] != '00000000-0000-0000-0000-000000000000':
                # print("There is an active license. You should deactivate it first.")
                # return
                # self.delete_license(url, token, username, password)
                # pass

        url_put_license:str = f"{url}/{self.__api_License}/active/{license_id}"
        payload = {}
        request = requests.put(url=url_put_license, headers=headers, data=payload, verify=False)
        if request.status_code in (200, 201, 204,):
            print(Fore.GREEN + f"   - new license has been activated successfully!")
            return True
        else:
            logging.error('%s', request.text)
            print(Fore.RED + f"   - error: New license has not been activated!")
        return False



