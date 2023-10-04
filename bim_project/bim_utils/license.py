import os
import json
import requests
import base64
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
disable_warnings(InsecureRequestWarning)
import time
import binascii
from colorama import init, Fore
init(autoreset=True)
from datetime import date
from datetime import datetime
import auth
from tools import Tools
# import logging
from log import Logs




class License:

    __api_License:str              = "api/License"
    __api_License_serverId:str     = "api/License/serverId"
    _permissions_to_check:tuple    = ('LicensesRead', 'LicensesWrite')

    # This SUID and UPP licenses are actually two parts of one license. Have know idea why it was designed that way.
    __UPP_SUID_lic:tuple = ('Платформа BIMeister, Bimeister УПП', 'Платформа BIMeister, Bimeister СУИД')
    __logger                      = Logs().f_logger(__name__)
    __start_connection            = Logs().http_connect()
    __check_response              = Logs().http_response()
    start_connection = Logs().http_connect()
    possible_request_errors:tuple = auth.Auth().possible_request_errors
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
             'IsOrganisation': 'False', 'OrderId': 'Стенд для демо', 'CrmOrderId': 'IMSD-604', 'sign': '<activation_key>', 'base64_token':'<base64_encoded_token>'
            }
        '''
        decoded_string = base64.b64decode(encoded_string).decode('utf-8')
        data = dict([ [x.split('=', 1)[0].strip(), x.split('=', 1)[1].strip()] for x in tuple(x for x in decoded_string.split('\n') if x) ])
        return data


    def read_license_token(self):
        ''' Check if there is a license.lic file, or ask user for a token. Function returns a list of dictionaries with license data, if everything is correct. '''

        data = input('Enter the filename(should have .lic extension) containing token or token itself: ').strip()
        if len(data) < 4:
            print('Incorrect input data.')
            return False
        err_message:str = 'Error with decoding the string. Check the log.'
        list_of_lic_data:list = [] # list where to put all the decoded token data
        is_file:bool = os.path.splitext(data)[1] == '.lic'
        is_file_in_place:bool = os.path.isfile(f"{os.getcwd()}/{data}")
        count = Tools.counter()

        if is_file and not is_file_in_place:
            no_file_message:str = f"Error: No such file '{data}' in the current folder. Check for it."
            self.__logger.error(no_file_message)
            print(no_file_message)
            return False

        elif is_file and is_file_in_place:
            with open(data, "r", encoding="utf-8") as file:    # get license_token from the .lic file and put it into data_from_lic_file dictionary
                content = [line for line in file.read().split('\n') if line]
            for x in content:
                is_present:bool = False
                try:
                    data = self.decode_base64(x)
                except (binascii.Error, ValueError):
                    continue
                for obj in list_of_lic_data:
                    if obj.get('LicenseID') == data['LicenseID']:
                        is_present = True
                if not is_present:
                    list_of_lic_data.append(data)
                    list_of_lic_data[count() - 1]['base64_token'] = x

        else:
            try:
                list_of_lic_data.append(self.decode_base64(data))
                list_of_lic_data[0]['base64_token'] = data
            except binascii.Error:
                self.__logger.error(f"Binascii error with decoding the string: {binascii.Error}")
                print(err_message)
                return False
            except ValueError:
                self.__logger.error(f"Value error with decoding the string: {ValueError}")
                print(err_message)
                return False
        
        ### Since EDMS and EPMM license could be applied in strict order, we need to make that order correct.
        EDMS:int = -1
        EPMM:int = -1
        for lic in range(len(list_of_lic_data)):
            if list_of_lic_data[lic]['Product'] == 'BimeisterEDMS':
                EDMS = lic
                continue
            elif list_of_lic_data[lic]['Product'] == 'BimeisterEPMM':
                EPMM = lic
                continue
        if (EDMS >= 0 and EPMM >= 0) and (EDMS > EPMM):
            list_of_lic_data[EDMS], list_of_lic_data[EPMM] = list_of_lic_data[EPMM], list_of_lic_data[EDMS]

        return list_of_lic_data


    def get_licenses(self, url, token, username, password):
        ''' Get all the licenses in the system '''

        url_get_licenses:str = f'{url}/{self.__api_License}'
        headers = {'accept': '*/*', 'Content-type':'text/plain', 'Authorization': f"Bearer {token}"}
        payload = {
                    "username": username,
                    "password": password
                 }
        try:
            self.__logger.info(self.__start_connection(url))
            response = requests.get(url=url_get_licenses, data=payload, headers=headers, verify=False)
            self.__logger.debug(self.__check_response(url, response.request.method, response.request.path_url, response.status_code))
            response.raise_for_status()
        except self.possible_request_errors as err:
            self.__logger.error(f"{err}\n{response.text}")

        # response is a list of dictionaries with a set of keys: 'isActive', 'serverId', 'licenseID', 'until', 'activeUsers', 'activeUsersLimit'
        return response.json()


    def get_license_status(self, url, token, username, password):
        ''' Check if there is an active license. Return True/False. '''

        self.__logger.info("Check license status...")
        licenses = self.get_licenses(url, token, username, password)
        current_date:str = str(date.today()) + 'T' + datetime.now().strftime("%H:%M:%S")
        for license in licenses:
            if license['activeUsers'] > license['activeUsersLimit'] and license['isActive'] and license['until'] > current_date:
                self.__logger.error(f"Users limit was exceeded! Active users: {license['activeUsers']}. Users limit: {license['activeUsersLimit']}")
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

        headers = {'accept': '*/*', 'Content-type':'text/plain', 'Authorization': f"Bearer {token}"}
        url_get_serverId:str = url + '/' + self.__api_License_serverId
        self.__logger.info(self.__start_connection(url))
        response = requests.get(url=url_get_serverId, data="", headers=headers, verify=False)
        self.__logger.debug(self.__check_response(url, response.request.method, response.request.path_url, response.status_code))
        message:str = "Current user don't have sufficient privileges."
        return response.text if response.status_code == 200 else message


    def display_licenses(self, url, token, username, password):
        ''' Display the list of licenses. '''

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
                # if license.get('isActive'):   # if we want to display only active licenses
                print()
                if license.get('licenseID') == '00000000-0000-0000-0000-000000000000':
                    print(f"   - trial deploy license\n   - validation period: {license['until'][:19]}")
                else:
                    for key, value in license.items():
                        print( f"   - {key}: {Fore.GREEN + str(value)}" if value and key == 'isActive' else f"   - {key}: {value}" )

        else:
            self.__logger.error("Unpredictable behaviour(license status) in License class.")


    def delete_license(self, url, token, username, password):
        '''   Delete active license, if there is one.   '''    

        headers = {'accept': '*/*', 'Content-type': 'text/plain', 'Authorization': f"Bearer {token}"}
        self.__logger.info("Delete license:")
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
                    response = requests.delete(url=f"{url}/{self.__api_License}/{active_licenses[lic]}", headers=headers, verify=False)
                    self.__logger.debug(self.__check_response(url, response.request.method, response.request.path_url, response.status_code))
                    if response.status_code in (200, 201, 204):
                        print(Fore.GREEN + f"   - license '{lic}': {active_licenses.pop(lic)} has been deactivated!")
                    else:
                        self.__logger.error('%s', response.text)
                        print(Fore.RED + f"   - license '{lic}' has not been deactivated! Check the logs.")

            if not active_licenses:
                return
            for name, id in active_licenses.items():
                url_delete_license = f"{url}/{self.__api_License}/{id}"
                response = requests.delete(url=url_delete_license, headers=headers, verify=False)
                self.__logger.debug(self.__check_response(url, response.request.method, response.request.path_url, response.status_code))
                response_data = bool(response.text) if not response.text else response.json()

                if response.status_code in (200, 201, 204):
                    print(Fore.GREEN + f"   - license '{name}': {id} has been deactivated!")

                else:
                    if response_data and response_data['type'] and response_data['type'] == 'ForbiddenException':
                        print(f"User '{username}' does not have sufficient privileges to do that!")
                    else:
                        self.__logger.error('%s', response.text)
                        print(Fore.RED + f"   - license '{name}': {id} has not been deactivated! Check the logs.")


    def post_license(self, url, token, username, password):

        headers = {'accept': 'text/plain', 'Content-Type': 'application/json-patch+json', 'Authorization': f"Bearer {token}"}
        self.__logger.info("Posting a license:")
        licenses_id = tuple(x.get('licenseID', False) for x in self.get_licenses(url, token, username, password))
        new_license_data:list = self.read_license_token()
        if not new_license_data:
            return False

        for license in new_license_data:
            if license['LicenseID'] in licenses_id:
                self.put_license(url, token, username, password, license['LicenseID'])
            else:
                data = json.dumps(license['base64_token'])
                response = requests.post(url=f'{url}/{self.__api_License}', headers=headers, data=data, verify=False)
                self.__logger.debug(self.__check_response(url, response.request.method, response.request.path_url, response.status_code))
                response_data = response.json()
                time.sleep(0.15)
                if response.status_code in (200, 201, 204,):
                    print(Fore.GREEN + f"\n   - new license '{response_data['product']}' has been posted successfully!")
                    self.put_license(url, token, username, password, license['LicenseID'])
                    self.__logger.debug(self.__check_response(url, response.request.method, response.request.path_url, response.status_code))
                    time.sleep(0.15)

                elif response_data['type'] and response_data['type'] == 'ForbiddenException':
                    print(f"User '{username}' does not have sufficient privileges to do that!")
                    return False

                else:
                    self.__logger.error('%s', response.text)
                    print(Fore.RED + f"\n   - new license has not been posted!")
                    return False
        
        return True


    def put_license(self, url:str, token:str, username, password, license_id:str):

        headers = {'accept': '*/*', 'Content-type': 'text/plain', 'Authorization': f"Bearer {token}"}
        # all the active licenses will be deactivated, if user forgot to do it, and if there are any active
        # for license in self.get_licenses(url, token, username, password):
        #     if license['isActive'] == True and license['licenseID'] != '00000000-0000-0000-0000-000000000000':
        #         print("There is an active license. You should deactivate it first.")
        #         return
        #         self.delete_license(url, token, username, password)
        #         pass
        check_id:bool = False
        self.__logger.info("Putting a license:")
        for license in self.get_licenses(url, token, username, password):
            if license['licenseID'] == license_id:
                check_id = True
                break
        if not check_id:
            print('Incorrect license ID.')
            return False
        url_put_license:str = f"{url}/{self.__api_License}/active/{license_id}"
        payload = {}
        response = requests.put(url=url_put_license, headers=headers, data=payload, verify=False)
        self.__logger.debug(self.__check_response(url, response.request.method, response.request.path_url, response.status_code))
        response_data = bool(response.text) if not response.text else response.json()
        err_message:str = Fore.RED + f"   - error: license '{license_id}' has not been activated!"

        if response.status_code in (200, 201, 204):
            print(Fore.GREEN + f"   - license '{license_id}' has been activated successfully!")
            return True

        else:
            if response_data and response_data['type'] and response_data['type'] == 'ForbiddenException':
                self.__logger.error('%s', response.text)
                print(f"\nUser '{username}' does not have sufficient privileges to do that!")
            elif response_data and response_data['type'] and response_data['type'] == 'BadRequestException' and response_data['message'] == 'ServerIdDoesntMatch':
                self.__logger.error('%s', response.text)
                print("\n   ServerID doesn't match!")
                print(err_message)
            else:
                self.__logger.error('%s', response.text)
                print(err_message)

        return False



