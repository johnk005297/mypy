import sys
import json
import requests
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
disable_warnings(InsecureRequestWarning)
from urllib.error import HTTPError
import time
from getpass import getpass
from log import Logs


class Auth:

    __api_Providers:str           = 'api/Providers'
    __api_Auth_Login:str          = 'api/Auth/Login'
    __api_PrivateToken:str        = 'api/PrivateToken'
    __logger                      = Logs().f_logger(__name__)
    __start_connection            = Logs().http_connect()
    __check_response              = Logs().http_response()
    headers                       = {'accept': '*/*', 'Content-type':'application/json; charset=utf-8'}
    possible_request_errors:tuple = (  requests.exceptions.MissingSchema, requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout,
                                       requests.exceptions.HTTPError, requests.exceptions.InvalidHeader, requests.exceptions.InvalidURL,
                                       requests.exceptions.InvalidSchema, requests.exceptions.InvalidJSONError, requests.exceptions.JSONDecodeError  )


    def __init__(self, url=None, username=None, password=None):
        self.url          = url
        self.username     = username
        self.password     = password
        self.token        = None
        self.providerId   = None
        self.privateToken = None


    def __getattr__(self, item):
        raise AttributeError("Auth class instance has no such attribute: " + item)


    def establish_connection(self):

        try:
            self.url = input("\nEnter URL: ").strip().lower()
            self.url = self.url[:-1] if self.url[-1] == '/' else self.url
            self.url = self.url[:-5] if self.url[-4:] == 'auth' else self.url
        except IndexError:
            message:str = 'Incorrect input.'
            print(message)
            return False
        except KeyboardInterrupt:
            print('\nKeyboardInterrupt')
            return False
        if not self.url_validation():
            return False
        if not self.get_providerId():
            return False
        self.get_credentials()
        return True if self.get_user_access_token(self.url, self.username, self.password, self.providerId) else False

    
    def url_validation(self):


        if self.url[:4] != 'http':
            self.url = 'http://' + self.url

        # Check both ports: 80 and 443
        for x in range(2):
            self.__logger.info(self.__start_connection(self.url))
            try:
                response = requests.get(url=f"{self.url}/{self.__api_Providers}", verify=False, allow_redirects=False, timeout=2)
                self.__logger.debug(self.__check_response(self.url, response.request.method, response.request.path_url, response.status_code))
                if response.status_code == 200:
                    self.api_providers:list = response.json()
                    return True
                elif response.status_code in (301, 302, 308):   # This part needs to fix issues if the redirect is set up.
                    self.url = self.url[:4] + self.url[5:] if self.url[4] == 's' else self.url[:4] + 's' + self.url[4:]

                # Cant' catch 502 error with except. Temporary need to add this block
                elif x == 1 and response.status_code == 500:
                    message:str = 'Error 500: Check connection to host.'
                    self.__logger.error(f"{response.text}\n{message}")
                    print(message)
                    return False
                elif x == 1 and response.status_code == 502:
                    message = f"Error {response.status_code}. Check web interface."
                    self.__logger.error(f"{response.text}\n{message}")
                    print(message)
                    return False
                else:
                    self.__logger.error(response.text)
                    return False

            except requests.exceptions.MissingSchema as err:
                self.__logger.error(err)
                if x == 1:
                    print('Invalid URL')
                return False
            
            except requests.exceptions.ReadTimeout as err:
                message:str = "Check connection to host."
                if x == 1:
                    print(message)
                self.__logger.error(f"{message}\n{err}")
                return False

            except self.possible_request_errors as err:
                self.__logger.error(f"Connection error via '{self.url[:self.url.index(':')]}':\n{err}.")
                self.url = self.url[:4] + self.url[5:] if self.url[4] == 's' else self.url[:4] + 's' + self.url[4:]
                if x == 1:
                    message:str = "Check connection to host."
                    self.__logger.error(f"{message}")
                    print(message)
                    return False
                continue
            continue


    def get_local_providerId(self, url):    # temporary disabled. Function needs to check the user's privileges.
        api_providers_response = requests.get(url=f"{url}/{self.__api_Providers}", verify=False)
        providers:list = api_providers_response.json()
        for provider in providers:
            if provider.get('name') == 'Local':
                return provider['id']


    def get_providerId(self):

        if len(self.api_providers) == 1:
            self.providerId = self.api_providers[0]['id']
            return True
        else:
            print('    Choose authorization type:')
            for num, obj in enumerate(self.api_providers, 1):
                print(f"      {str(num)}. {obj['name']} ({obj['providerTypeOption']})")
            try:
                inp = int(input('    value: '))
                self.providerId = self.api_providers[inp-1]['id']
                return True
            except ValueError:
                print('Wrong input.')
                return False


    def get_credentials(self):
        try:
            confirm_name = input("Enter login(default, admin): ")
            confirm_pass = getpass("Enter password(default, Qwerty12345!): ") # first option to conceal the password
            # confirm_pass = maskpass.askpass(prompt="Enter password(default, Qwerty12345!): ", mask='*')  # have some issues with installing it on linux python3.6.8
            self.username=confirm_name if confirm_name else 'admin'
            self.password=confirm_pass if confirm_pass else 'Qwerty12345!'
        except KeyboardInterrupt:
            print('\nKeyboardInterrupt')
            return False
        except Exception:
            sys.exit()


    def get_user_access_token(self, url, username, password, providerId):
        ''' Basically this is a login into system, after what we get an access token. '''

        payload = {
                    "username":   username,
                    "password":   password,
                    "providerId": providerId
                  }
        data = json.dumps(payload)
        response = requests.post(url=f"{url}/{self.__api_Auth_Login}", data=data, headers=self.headers, verify=False)
        self.__logger.debug(self.__check_response(self.url, response.request.method, response.request.path_url, response.status_code))
        data = response.json()

        time.sleep(0.07)
        '''
        Block is for checking authorization request.
        Correct response of /api/Auth/Login method suppose to return a .json with 'access_token' and 'refresh_token'.
        '''

        if response.status_code == 401:
            if data.get('type') and data.get('type') == 'TransitPasswordExpiredBimException':
                message:str = f"Password for '{username}' has been expired!"
                print(message)
                self.__logger.warning(message)
                return False
            elif data.get('type') and data.get('type') == 'IpAddressLoginAttemptsExceededBimException':
                message = "Too many authorization attempts. IP address has been blocked!"
                print(message)
                self.__logger.warning(message)
                return False
            elif data.get('type') and data.get('type') == 'AuthCommonBimException':
                message = f"Unauthorized access. Check credentials for user: {username}."
                print(message)
                self.__logger.warning(message)
                return False
            elif data.get('type') and data.get('type') == 'UserPasswordValidationBimException':
                message = "The password does not match the password policy. Need to create a new password."
                print(message)
                self.__logger.warning(message)
            else:
                self.__logger.error(response.text)
                return False
        elif response.status_code  in (200, 201, 204):
            self.token = data['access_token']
            return self.token
        else:
            self.__logger.error(response.text)
            return False


    def get_private_token(self, url, token):
        ''' Function provides user private token. '''

        headers = {'accept': 'text/plain', 'Authorization': f"Bearer {token}"}
        url=f"{url}/{self.__api_PrivateToken}"
        try:
            response = requests.get(url=url, headers=headers, verify=False)
            self.__logger.info("Getting private token:")
            self.__logger.debug(self.__check_response(self.url, response.request.method, response.request.path_url, response.status_code))
            if response.status_code == 204:
                self.__logger.info(self.__start_connection(url))
                response = requests.post(url=url, headers=headers, verify=False)
            data = response.json()
            self.privateToken:str = data['privateToken']

        except self.possible_request_errors as err:
            self.__logger.error(err)
            return False

        return self.privateToken