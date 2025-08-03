import os
import sys
import json
import requests
import base64
import auth
import time
import binascii
from dateutil.relativedelta import relativedelta
from rich.console import Console
from rich.table import Table
from datetime import date, datetime, timedelta
from termcolor import colored, cprint
from log import Logs
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
disable_warnings(InsecureRequestWarning)
from colorama import init, Fore
init(autoreset=True)
from tools import Tools

logger = Logs().f_logger(__name__)
tools = Tools()

class License:

    __api_License: str = "api/License"
    __api_License_serverId: str = "api/License/serverId"
    _permissions_to_check: tuple = ('LicensesRead', 'LicensesWrite')

    # This SUID and UPP licenses are actually two parts of one license. Have know idea why it was designed that way.
    __UPP_SUID_lic: tuple = ('Платформа BIMeister, Bimeister УПП', 'Платформа BIMeister, Bimeister СУИД')
    # __logger = Logs().f_logger(__name__)
    __start_connection = Logs().http_connect()
    __check_response = Logs().http_response()
    start_connection = Logs().http_connect()
    possible_request_errors: tuple = auth.Auth().possible_request_errors
    privileges_granted: bool = False
    privileges_checked: bool = False

    def __init__(self):
        pass

    def __getattr__(self, item):
        raise AttributeError('License class has no such attribute: ' + item)

    def decode_base64(self, encoded_string) -> dict:
        """ Function decodes base64 encoded string and returns dictionary of values. Current version example of license data:
            {
             'version': '1', 'LicenseID': 'a7bfd7df-6b90-4ca1-b40e-07d99f38308f', 'ServerID': 'eeaa4ad2-28b7-4eb7-8bfb-3fdd40d257a5', 'From': '10.03.2023 00:00:01',
             'Until': '25.12.2023 23:59:59', 'NumberOfUsers': '100', 'NumberOfIpConnectionsPerUser': '0', 'Product': 'BimeisterEDMS', 'LicenceType': 'Trial',
             'ActivationType': 'Offline', 'Client': 'Rupert Pupkin', 'ClientEmail': 'Rupert.Pupkin@fun.org', 'Organisation': 'sandbox-3.imp.bimeister.io',
             'IsOrganisation': 'False', 'OrderId': 'Стенд для демо', 'CrmOrderId': 'IMSD-604', 'sign': '<activation_key>'
            }
        """
        decoded_string = base64.b64decode(encoded_string).decode('utf-8')
        data = dict([ [x.split('=', 1)[0].strip(), x.split('=', 1)[1].strip()] for x in tuple(x for x in decoded_string.split('\n') if x) ])
        return data

    def read_license_token(self, data=None) -> list:
        """ Function checks if there is a license.lic file. If not, ask user for a token.
            To the dictionary in the final list of licenses we add 'base64_encoded_license' key with all the encoded line from the license file.
            This key 'base64_encoded_license' is used to post and activate license.
            Returns a list of dictionaries with license data, if everything is correct. 
        """

        if not data:
            data = input('Enter the filename(should have .lic extension) containing token or provide token itself: ').strip()
            if len(data) < 4:
                print('Incorrect input data.')
                return False
        err_message: str = 'Error with decoding the string. Check the log.'
        list_of_licenses: list = []

        is_file: bool = os.path.splitext(data)[1] == '.lic'
        is_file_exists: bool = False if not is_file else os.path.isfile(f"{os.getcwd()}/{data}")
        if is_file and not is_file_exists:
            no_file_message: str = f"Error: No such file '{data}' in the current folder. Check for it."
            logger.error(no_file_message)
            print(no_file_message)
            return False
        elif is_file and is_file_exists:
            with open(data, "r", encoding="utf-8") as file:    # get license_token from the .lic file and put it into data_from_lic_file dictionary
                content = [line for line in file.read().split('\n') if line]
            for line in content:
                is_present: bool = False
                try:
                    data = self.decode_base64(line)
                except (binascii.Error, ValueError) as err:
                    logger.error(err)
                    continue
                except Exception as err:
                    logger.error(err)
                    continue
                for license in list_of_licenses:
                    if license.get('LicenseID') == data['LicenseID']:
                        is_present = True
                        break
                if not is_present:
                    list_of_licenses.append(data)
                    list_of_licenses[-1]['base64_encoded_license'] = line
        else:
            try:
                list_of_licenses.append(self.decode_base64(data))
                list_of_licenses[0]['base64_encoded_license'] = data
            except binascii.Error:
                logger.error(f"Binascii error with decoding the string: {binascii.Error}")
                print(err_message)
                return False
            except ValueError:
                logger.error(f"Value error with decoding the string: {ValueError}")
                print(err_message)
                return False

        # Since EDMS and EPMM license could be only applied in strict order, we need to make that order correct.
        EDMS: int = -1
        EPMM: int = -1
        for lic in range(len(list_of_licenses)):
            if list_of_licenses[lic]['Product'] == 'BimeisterEDMS':
                EDMS = lic
                continue
            elif list_of_licenses[lic]['Product'] == 'BimeisterEPMM':
                EPMM = lic
                continue
        if (EDMS >= 0 and EPMM >= 0) and (EDMS > EPMM):
            list_of_licenses[EDMS], list_of_licenses[EPMM] = list_of_licenses[EPMM], list_of_licenses[EDMS]    
        return list_of_licenses

    def get_licenses(self, url, token, username, password) -> list:
        """ Function gets all the licenses in the system,
            and returns a list of dictionaries: 
            [{'name': value, 'isActive': value, 'serverId': value, 'licenseID': value, 'until': value, 'activeUsers': value, 'activeUsersLimit': value}]
        """

        url_get_licenses: str = f'{url}/{self.__api_License}'
        headers = {'accept': '*/*', 'Content-type':'text/plain', 'Authorization': f"Bearer {token}"}
        payload = {
                    "username": username,
                    "password": password
                  }
        try:
            logger.info(self.__start_connection(url))
            response = requests.get(url=url_get_licenses, data=payload, headers=headers, verify=False)
            logger.debug(self.__check_response(url, response.request.method, response.request.path_url, response.status_code))
            response.raise_for_status()
        except self.possible_request_errors as err:
            logger.error(f"{err}\n{response.text}")

        return response.json()

    def get_license_status(self, url, token, username, password):
        """ Check if there is an active license. Return True/False. """

        logger.info("Check license status...")
        licenses = self.get_licenses(url, token, username, password)
        current_date: str = str(date.today()) + 'T' + datetime.now().strftime("%H:%M:%S")
        for license in licenses:
            if license['activeUsers'] > license['activeUsersLimit'] and license['isActive'] and license['until'] > current_date:
                logger.error(f"Users limit was exceeded! Active users: {license['activeUsers']}. Users limit: {license['activeUsersLimit']}")
                cprint(colored("Users limit is exceeded!".upper(), "red", attrs=["reverse", "blink"]))
                return False
            elif license['isActive'] and license['licenseID'] != '00000000-0000-0000-0000-000000000000' and license['until'] > current_date:
                return True
            elif license['licenseID'] == '00000000-0000-0000-0000-000000000000' and license['until'] > current_date:
                return True
            else:
                continue
        return False

    def get_serverID(self, url, token) -> tuple:
        """ Function returns a tuple of two values: (True/False, serverId/error message)
            Example: (True, '89606922-2e08-4095-ade8-db25766e81f6'), (False, 'Current user does not have sufficient privileges.')
        """

        headers = {
            'accept': '*/*',
            'Content-type':'text/plain',
            'Authorization': f"Bearer {token}"
        }
        url: str = url + '/' + self.__api_License_serverId
        # response = requests.get(url=url, data="", headers=headers, verify=False)
        # logger.debug(self.__check_response(url, response.request.method, response.request.path_url, response.status_code))
        response = tools.make_request('GET', url=url, module=__name__, return_response=True, headers=headers, verify=False)
        message: str = "Current user does not have sufficient privileges."
        return (True, response.text) if response and response.status_code == 200 else (False, message)

    def display_licenses(self, url, token, username, password):
        """ Display the list of licenses. """

        licenses: list = self.get_licenses(url, token, username, password)
        if len(licenses) > 10:
            licenses = licenses[:10]
        table = Table(show_lines=True)
        table.add_column("Name", justify="left", no_wrap=True)
        table.add_column("Server Id", justify="left")
        table.add_column("Users", justify="left")
        table.add_column("Expiration date", justify="left")
        table.add_column("Status", justify="center")
        current_date: str = str(date.today()) + 'T' + datetime.now().strftime("%H:%M:%S")
        for license in licenses:
            # convert str format of expiration date to datetime format
            format = "%Y-%m-%dT%H:%M:%S"
            expiration_date = datetime.strptime(license["until"], format).strftime("%d %B %Y")
            table.add_row(
                          license["name"],
                          license["serverId"],
                          f"{license['activeUsers']}/{license['activeUsersLimit']}",
                          f"[red]{expiration_date}[/red]" if license["until"] < current_date and license["isActive"] else expiration_date,
                        "[green]Active[/green]" if license["isActive"] else "[red]Inactive[/red]", style="cyan" if license["isActive"] else "dim cyan"
                          )
        console = Console()
        console.print(table)

    def delete_license(self, url, token, username, password):
        """   Delete active license, if there is one.   """    

        headers = {'accept': '*/*', 'Content-type': 'text/plain', 'Authorization': f"Bearer {token}"}
        logger.info("Delete license:")
        licenses = self.get_licenses(url, token, username, password)
        active_licenses = dict()
        """ 
            There is a default trial license from the installation with no ID(000..00). It cannot be deactivated, so we simply ignore it.
            After new license will be applied, system trial license will disappear automatically.
        """
        for license in licenses:
            if license.get('isActive') and license['licenseID'] != '00000000-0000-0000-0000-000000000000':
                active_licenses.setdefault(license['name'], license['licenseID'])

        if not active_licenses:
            print("\n   - no active licenses have been found in the system.")
        else:
            for lic in self.__UPP_SUID_lic:
                if active_licenses.get(lic):
                    response = requests.delete(url=f"{url}/{self.__api_License}/{active_licenses[lic]}", headers=headers, verify=False)
                    logger.debug(self.__check_response(url, response.request.method, response.request.path_url, response.status_code))
                    if response.status_code in (200, 201, 204):
                        print(Fore.GREEN + f"   - license '{lic}': {active_licenses.pop(lic)} has been deactivated!")
                    else:
                        logger.error('%s', response.text)
                        print(Fore.RED + f"   - license '{lic}' has not been deactivated! Check the logs.")

            if not active_licenses:
                return
            for name, id in active_licenses.items():
                url_delete_license = f"{url}/{self.__api_License}/{id}"
                response = requests.delete(url=url_delete_license, headers=headers, verify=False)
                logger.debug(self.__check_response(url, response.request.method, response.request.path_url, response.status_code))
                response_data = bool(response.text) if not response.text else response.json()

                if response.status_code in (200, 201, 204):
                    print(Fore.GREEN + f"   - license '{name}': {id} has been deactivated!")
                else:
                    if response_data and response_data['type'] and response_data['type'] == 'ForbiddenException':
                        print(f"User '{username}' does not have sufficient privileges to do that!")
                    else:
                        logger.error('%s', response.text)
                        print(Fore.RED + f"   - license '{name}': {id} has not been deactivated! Check the logs.")

    def apply_license(self, url, token, username, password, license=None):
        """ Upload and activate license into Bimeister platform. """

        headers = {'accept': 'text/plain', 'Content-Type': 'application/json-patch+json', 'Authorization': f"Bearer {token}"}
        logger.info("Posting a license:")
        # create a tuple to check if license is already presents in Bimeister
        licenses_id = tuple(dict.get('licenseID', False) for dict in self.get_licenses(url, token, username, password))
        new_license_data: list = self.read_license_token(data=license)
        if not new_license_data:
            return False
        for license in new_license_data:
            if license['LicenseID'] in licenses_id:
                self.activate_license(url, token, username, password, license['LicenseID'])
            else:
                data = json.dumps(license['base64_encoded_license'])
                response = requests.post(url=f'{url}/{self.__api_License}', headers=headers, data=data, verify=False)
                logger.debug(self.__check_response(url, response.request.method, response.request.path_url, response.status_code))
                response_data = response.json()
                time.sleep(0.15)
                if response.status_code in (200, 201, 204,):
                    print(Fore.GREEN + f"\n   - new license '{response_data['product']}' has been posted successfully!")
                    self.activate_license(url, token, username, password, license['LicenseID'])
                    logger.debug(self.__check_response(url, response.request.method, response.request.path_url, response.status_code))
                    time.sleep(0.15)
                elif response_data['type'] and response_data['type'] == 'ForbiddenException':
                    print(f"User '{username}' does not have sufficient privileges!")
                    return False
                else:
                    logger.error('%s', response.text)
                    print(Fore.RED + f"\n   - new license has not been posted!")
                    return False
        return True

    def activate_license(self, url: str, token: str, username, password, license_id: str):
        """ Activate license which is already uploaded in Bimeister platform. """

        headers = {'accept': '*/*', 'Content-type': 'text/plain', 'Authorization': f"Bearer {token}"}
        # all the active licenses will be deactivated, if user forgot to do it, and if there are any active
        # for license in self.get_licenses(url, token, username, password):
        #     if license['isActive'] == True and license['licenseID'] != '00000000-0000-0000-0000-000000000000':
        #         print("There is an active license. You should deactivate it first.")
        #         return
        #         self.delete_license(url, token, username, password)
        #         pass
        check_id: bool = False
        logger.info("Activating a license:")
        for license in self.get_licenses(url, token, username, password):
            if license['licenseID'] == license_id:
                check_id = True
                break
        if not check_id:
            print('Incorrect license ID.')
            return False
        url_activate_license: str = f"{url}/{self.__api_License}/active/{license_id}"
        payload = {}
        response = requests.put(url=url_activate_license, headers=headers, data=payload, verify=False)
        logger.debug(self.__check_response(url, response.request.method, response.request.path_url, response.status_code))
        response_data = bool(response.text) if not response.text else response.json()
        err_message: str = Fore.RED + f"   - error: license '{license_id}' has not been activated!"

        if response.status_code in (200, 201, 204):
            print(Fore.GREEN + f"   - license '{license_id}' has been activated successfully!")
            return True
        else:
            if response_data and response_data['type'] and response_data['type'] == 'ForbiddenException':
                logger.error('%s', response.text)
                print(f"\nUser '{username}' does not have sufficient privileges to do that!")
            elif response_data and response_data['type'] and response_data['type'] == 'BadRequestException' and response_data['message'] == 'ServerIdDoesntMatch':
                logger.error('%s', response.text)
                print("\n   ServerID doesn't match!")
                print(err_message)
            else:
                logger.error('%s', response.text)
                print(err_message)
        return False


class Issue:

    __api_license_login: str = "api/auth/login"
    __api_license_sign: str = "api/licenses/sign"
    _license_server: str = "10.168.23.42"
    _license_server_port: int = 5502
    _providerId: str = "ffb8c280-13a0-4c0d-8636-8aeee82c6e1d"

    def __init__(self):
        pass

    def get_token_to_issue_license(self, username='', password=''):
        """ Get token to issue a new bimeister license. """

        url = f'http://{self._license_server}:{self._license_server_port}/{self.__api_license_login}'
        headers = {'Content-Type': 'application/json'}

        if not username or not password:
            print("Username and password must be provided. Exit.")
            return False
        payload = json.dumps({
            "username": username,
            "password": password,
            "providerId": self._providerId
        })
        try:
            response = requests.post(url, headers=headers, data=payload, timeout=2, verify=False)
            data = response.json()
            err_message: str = "Unexpected error. Check the log!"
            if response.status_code in (200, 201, 204):
                access_token: str = response.json()['access_token']
                return access_token
            elif response.status_code == 400:
                if isinstance(data, dict) and 'errors' in data.keys() and 'providerId' in data['errors'].keys() and data['errors']['providerId'][0].startswith('Error converting value'):
                    logger.error(response.text)
                    print(f"Error: providerId {self._providerId} isn't correct!")
                    sys.exit()
                else:
                    print(err_message)
                    sys.exit()
            elif response.status_code == 500:
                if isinstance(data, dict) and 'type' in data.keys() and data['type'] == 'UnauthorizedAccessClientException':
                    logger.error(response.text)
                    print("Error: Authorization error. Check username or password for a license token!")
                    sys.exit()
                else:
                    print(err_message)
                    sys.exit()
            else:
                logger.error(response.text)
                print(err_message)
                sys.exit()
        except requests.ConnectTimeout as err:
            print("Error: Check connection to host.")
            logger.error(err)
            sys.exit()
        except requests.exceptions.RequestException as err:
            print(err)

    def issue_license(self, token, **kwagrs):
        """ Issue a new license from the license server. """

        url = f'http://{self._license_server}:{self._license_server_port}/{self.__api_license_sign}'
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f"Bearer {token}"}

        period = 3 if not kwagrs['period'] else int(kwagrs['period']) # license period in months
        iso_yesterday: str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S%z")
        dt_object: datetime = datetime.fromisoformat(iso_yesterday)
        new_dt_object: datetime = dt_object + relativedelta(months=period)
        iso_new_date: str = new_dt_object.strftime("%Y-%m-%dT%H:%M:%S%z")
        params = {
            "version": kwagrs['version'],
            "product": kwagrs['product'],
            "licenceType": kwagrs['licenceType'],
            "activationType": kwagrs['activationType'],
            "client": kwagrs['url'] if kwagrs['url'] else kwagrs['client'],
            "clientEmail": kwagrs['clientEmail'],
            "organisation": kwagrs['organization'],
            "isOrganisation": kwagrs['isOrganization'],
            "numberOfUsers": kwagrs['numberOfUsers'],
            "numberOfIpConnectionsPerUser": kwagrs['numberOfIpConnectionsPerUser'],
            "serverID": kwagrs['serverId'],
            "from": iso_yesterday,
            "until": iso_new_date,
            "orderId": "",
            "crmOrderId": ""
        }
        payload = json.dumps(params)
        try:
            response = requests.post(url, headers=headers, data=payload, verify=False)
            license = response.json()
            if kwagrs['save']:
                # remove protocol to the left and slash sign to the right in URL string
                license_filename: str = '' if not kwagrs['url'] else kwagrs['url'].split('//')[1].rstrip('/')
                with open(license_filename + '.lic' if license_filename else kwagrs['serverId'] + '.lic', 'w', encoding='utf-8') as file:
                    file.write(license)
            if kwagrs['print']:
                print(license)
            return license
        except Exception as err:
            logger.error(err)
            print("Error. Check the log!")
            sys.exit()
