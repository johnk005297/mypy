import sys
import json
import requests
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
disable_warnings(InsecureRequestWarning)
from urllib.error import HTTPError
import logging
import time
from getpass import getpass
# import maskpass


class Auth:

    __api_Providers:str  = 'api/Providers'
    __api_Auth_Login:str = 'api/Auth/Login'
    headers = {'accept': '*/*', 'Content-type':'application/json; charset=utf-8'}
    possible_request_errors:tuple = (  requests.exceptions.MissingSchema, requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout,
                                       requests.exceptions.HTTPError, requests.exceptions.InvalidHeader, requests.exceptions.InvalidURL,
                                       requests.exceptions.InvalidSchema, requests.exceptions.InvalidJSONError, requests.exceptions.JSONDecodeError  )


    def __init__(self, url=None, username=None, password=None):
        self.url        = url
        self.username   = username
        self.password   = password
        self.token      = None
        self.providerId = None


    def __getattr__(self, item):
        raise AttributeError("Auth class instance has no such attribute: " + item)


    def establish_connection(self):
        try:
            self.url = input("\nEnter URL: ").strip().lower()
            self.url = self.url[:-1] if self.url[-1] == '/' else self.url
            self.url = self.url[:-5] if self.url[-4:] == 'auth' else self.url
        except IndexError:
            message:str = 'Wrong input.'
            print(message)
            logging.info(message)
            return False
        except KeyboardInterrupt:
            print('\nInterrupted by the user.')
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
                check_url_request = requests.get(url=f"{self.url}/{self.__api_Providers}", verify=False, allow_redirects=False, timeout=2)
                if check_url_request.status_code == 200:
                    self.api_providers_response = check_url_request.json()
                    return True
                elif check_url_request.status_code in (301, 302):   # This part needs to fix issues if the redirect is set up.
                    self.url = self.url[:4] + self.url[5:] if self.url[4] == 's' else self.url[:4] + 's' + self.url[4:]
                
                # Cant' catch 502 error with except. Temporary need to add this block
                elif x == 1 and check_url_request.status_code == 500:
                    message = 'Error 500: Check connection to host.'
                    logging.error(f"{check_url_request.text}\n{message}")
                    print(message)
                    return False
                elif x == 1 and check_url_request.status_code == 502:
                    message = "Error 502. Check web interface."
                    logging.error(f"{check_url_request.text}\n{message}")
                    print(message)
                    return False
                
            except requests.exceptions.MissingSchema:
                print('Invalid URL')
                return False

            except self.possible_request_errors as err:
                logging.error(f"Connection error via '{self.url[:self.url.index(':')]}':\n{err}.")
                self.url = self.url[:4] + self.url[5:] if self.url[4] == 's' else self.url[:4] + 's' + self.url[4:]
                if x == 1:
                    message:str = "Error: Check connection to host."
                    logging.error(f"{err}\n{message}")
                    print(message)
                    return False
                continue

            continue


    def get_local_providerId(self, url):
        api_providers_response = requests.get(url=f"{url}/{self.__api_Providers}", verify=False)
        providers:list = api_providers_response.json()
        for provider in providers:
            if provider.get('name') == 'Local':
                return provider['id']


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
        try:
            confirm_name = input("Enter login(default, admin): ")
            confirm_pass = getpass("Enter password(default, Qwerty12345!): ") # first option to conceal the password
            # confirm_pass = maskpass.askpass(prompt="Enter password(default, Qwerty12345!): ", mask='*')  # have some issues with installing it on linux python3.6.8
            self.username=confirm_name if confirm_name else 'admin'
            self.password=confirm_pass if confirm_pass else 'Qwerty12345!'
        except KeyboardInterrupt:
            print('\nInterrupted by the user.')
            sys.exit()


    def get_user_access_token(self, url, username, password, providerId):
        ''' Basically this is a login into system, after what we get an access token. '''

        payload = {
                    "username":   username,
                    "password":   password,
                    "providerId": providerId
                  }
        data = json.dumps(payload)
        auth_request = requests.post(url=f"{url}/{self.__api_Auth_Login}", data=data, headers=self.headers, verify=False)
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
            return self.token
        else:
            logging.error(log)
            return False