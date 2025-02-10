import sys
import json
import requests
import time
from urllib.error import HTTPError
from getpass import getpass
from log import Logs
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
disable_warnings(InsecureRequestWarning)


class Auth:
    __slots__ = ('url', 'username', 'password', 'token', 'providerId', 'privateToken')
    __api_Providers: str = 'api/Providers'
    __api_Auth_Login: str = 'api/Auth/Login'
    __api_PrivateToken: str = 'api/PrivateToken'
    __logger = Logs().f_logger(__name__)
    __start_connection = Logs().http_connect()
    __check_response = Logs().http_response()
    headers = {'accept': '*/*', 'Content-type': 'application/json; charset=utf-8'}
    possible_request_errors: tuple = (
        requests.exceptions.MissingSchema, requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout,
        requests.exceptions.HTTPError, requests.exceptions.InvalidHeader, requests.exceptions.InvalidURL,
        requests.exceptions.InvalidSchema, requests.exceptions.InvalidJSONError, requests.exceptions.JSONDecodeError)

    def __init__(self, url=None, username=None, password=None):
        self.url = url
        self.username = username
        self.password = password
        self.token = None
        self.privateToken = None
        self.providerId = None

    def __getattr__(self, item):
        raise AttributeError("Auth class instance has no such attribute: " + item)

    def establish_connection(self):
        try:
            self.url = input("\nEnter URL: ").strip().lower()
            self.url = self.url[:-1] if self.url.endswith('/') else self.url
            self.url = self.url[:-5] if self.url.endswith('auth') else self.url
        except IndexError:
            message: str = 'Incorrect input.'
            print(message)
            return False
        except KeyboardInterrupt:
            print('\nKeyboardInterrupt')
            return False
        if not self.url_validation(self.url):
            return False
        if not self.get_providerId(self.url):
            return False
        self.get_credentials()
        return True if self.get_user_access_token(self.url, self.username, self.password, self.providerId) else False

    def url_validation(self, url):

        if not url.startswith('http'):
            url = 'http://' + url
        # Check both ports: 80 and 443
        for x in range(2):
            self.__logger.info(self.__start_connection(url))
            try:
                response = requests.get(url=url, verify=False, allow_redirects=False, timeout=2)
                self.__logger.debug(self.__check_response(url, response.request.method, response.request.path_url,
                                                          response.status_code))
                if response.status_code == 200:
                    self.url = url
                    return url
                # this part needs to fix issues if the redirect is set up
                elif response.status_code in (301, 302, 308):
                    url = url[:4] + url[5:] if url[4] == 's' else url[:4] + 's' + url[4:]

                # Can't catch 502 error with except. Temporary need to add this block
                elif x == 1 and response.status_code == 500:
                    message: str = 'Error 500: Check connection to host.'
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
                message: str = "Check connection to host."
                if x == 1:
                    print(message)
                self.__logger.error(f"{message}\n{err}")
                return False
            except self.possible_request_errors as err:
                self.__logger.error(f"Connection error via '{url[:url.index(':')]}':\n{err}.")
                url = url[:4] + url[5:] if url[4] == 's' else url[:4] + 's' + url[4:]
                if x == 1:
                    message: str = "Check connection to host."
                    self.__logger.error(f"{message}")
                    print(message)
                    return False
                continue
            continue

    def get_providerId(self, url):

        response = requests.get(url=f"{url}/{self.__api_Providers}", verify=False, allow_redirects=False,
                                timeout=2)
        if response.status_code == 200:
            api_providers: list = response.json()
        elif response.status_code != 200:
            print("Couldn't establish connection. Check the logs!")
            Auth.__logger.error(response.text)
            return False
        if len(api_providers) == 1:
            self.providerId = api_providers[0]['id']
            return self.providerId
        else:
            print('    Choose authorization type:')
            for num, obj in enumerate(api_providers, 1):
                print(f"      {str(num)}. {obj['name']} ({obj['providerTypeOption']})")
            try:
                inp = int(input('    value: '))
                if inp > len(api_providers):
                    print("Incorrect input")
                    return False
                self.providerId = api_providers[inp - 1]['id']
                return self.providerId
            except ValueError:
                print('Input should be a number')
                return False

    def get_credentials(self):
        try:
            confirm_name = input("Enter login(default, admin): ")
            confirm_pass = getpass("Enter password(default, Qwerty12345!): ")
            self.username = confirm_name if confirm_name else 'admin'
            self.password = confirm_pass if confirm_pass else 'Qwerty12345!'
        except KeyboardInterrupt:
            print('\nKeyboardInterrupt')
            return False
        except Exception:
            sys.exit()

    def get_user_access_token(self, url, username, password, providerId):
        """ Basically this is a login into system, after what we get an access token. """

        payload = {
            "username": username,
            "password": password,
            "providerId": providerId
        }
        data = json.dumps(payload)
        try:
            response = requests.post(url=f"{url}/{self.__api_Auth_Login}", data=data, headers=self.headers, verify=False)
            self.__logger.debug(f"username: {self.username}")
            self.__logger.debug(
                self.__check_response(url, response.request.method, response.request.path_url, response.status_code))
            data = response.json()
        except self.possible_request_errors as err:
            self.__logger.error(err)
            print(f"Login attempt failed. Repsonse code: {response.status_code}. Check services are running!")
        time.sleep(0.07)
        """ Block is for checking authorization request.
        Correct response of /api/Auth/Login method suppose to return a .json with 'access_token' and 'refresh_token'.
        """
        if response.status_code == 401:
            if data.get('type') and data.get('type') == 'TransitPasswordExpiredBimException':
                message: str = f"Password for '{username}' has been expired!"
                self.__logger.error(response.text)
                print(message)
                return False
            elif data.get('type') and data.get('type') == 'IpAddressLoginAttemptsExceededBimException':
                message = "Too many authorization attempts. IP address has been blocked!"
                self.__logger.error(response.text)
                print(message)
                return False
            elif data.get('type') and data.get('type') == 'AuthCommonBimException':
                message = f"Unauthorized access. Check credentials for user: {username}."
                self.__logger.error(response.text)
                print(message)
                return False
            elif data.get('type') and data.get('type') == 'UserPasswordValidationBimException':
                message = "The password does not match the password policy. Need to create a new password."
                self.__logger.error(response.text)
                print(message)
            elif data.get('type') and data.get('type') == 'UserLoginAttemptsExceededBimException':
                message = "Login attempts exceeded. User was blocked."
                self.__logger.error(response.text)
                print(message)
            else:
                self.__logger.error(response.text)
                return False
        elif response.status_code in (200, 201, 204):
            self.token = data['access_token']
            return self.token
        else:
            return False

    def get_private_token(self, url, token):
        """ Function provides user private token. """

        headers = {'accept': 'text/plain', 'Authorization': f"Bearer {token}"}
        url = f"{url}/{self.__api_PrivateToken}"
        try:
            response = requests.get(url=url, headers=headers, verify=False)
            self.__logger.info("Getting private token:")
            self.__logger.debug(self.__check_response(self.url, response.request.method, response.request.path_url,
                                                      response.status_code))
            if response.status_code == 204:
                self.__logger.info(self.__start_connection(url))
                response = requests.post(url=url, headers=headers, verify=False)
            data = response.json()
            self.privateToken: str = data['privateToken']

        except self.possible_request_errors as err:
            self.__logger.error(err)
            return False
        return self.privateToken
