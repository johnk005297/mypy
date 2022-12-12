#
# This module provides necessary credentials for work with API. 
# We get URL, username, password, token with it.

import logging
import os, sys
import time
import requests
import json



'''   Global variables   '''
headers = {'accept': '*/*', 'Content-type':'application/json; charset=utf-8'}
pwd = os.getcwd()
possible_request_errors: tuple = (  requests.exceptions.MissingSchema, requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout, 
                                    requests.exceptions.HTTPError, requests.exceptions.InvalidHeader, requests.exceptions.InvalidURL, requests.JSONDecodeError  )
''''''''''''''''''''''''''''''

def get_credentials():
    '''  1. Function prompts for login and password. It returns dictionary with creds. Ex: {"url": 'http://my-bimeister.io', "username": admin, "password": mypassword}.
         2. Provides provider ID for get_token() function.
    '''

    # Enable logging
    logging.basicConfig(filename=f"{pwd}/license_log.txt", level=logging.DEBUG,
                        format="%(asctime)s %(levelname)s - %(message)s", filemode="w", datefmt='%d-%b-%y %H:%M:%S')
                        
    url = input("\nEnter URL: ").lower()
    url = url[:-1] if url[-1] == '/' else url

    confirm_name = input("Enter login(default, admin): ")
    confirm_pass = input("Enter password(default, Qwerty12345!): ")
    username=confirm_name if confirm_name else 'admin'
    password=confirm_pass if confirm_pass else 'Qwerty12345!'

    credentials:dict = {"url": url, "username": username, "password": password}
    
    ''' block to check both ports: 80 and 443 '''  # Added fix if url is set with redirect to another source
    for x in range(2):
        try:            
            check_url_request = requests.get(url=url+'/api/Providers', headers=headers, verify=False, allow_redirects=False, timeout=2)
            if check_url_request.status_code == 200:
                break
            elif check_url_request.status_code in (301, 302):   # This part needs to fix issues if the redirect had been set up.
                url = url[:4] + url[5:] if url[4] == 's' else url[:4] + 's' + url[4:]

        except possible_request_errors as err:
            logging.error(f"Connection error via '{url[:url.index(':')]}':\n{err}.")
            url = url[:4] + url[5:] if url[4] == 's' else url[:4] + 's' + url[4:]
            if x == 1:
                logging.error(f"Check host connection to {url}.")
            continue

    response = check_url_request.json()
    list_of_providersID: list = [dct['id'] for dct in response]     # This list with id's will be provided to get_token() function. It needs to receive a token.

    credentials['url'] = url    # Apply correct value to credentials['url'] variable after all checks.
    return credentials, list_of_providersID


def get_token(url:str, username:str, password:str, provider_id:list):
    '''  Function to get bearer token from the server   '''
    
    url_auth = f"{url}/api/Auth/Login"

    for id in provider_id:
        payload = {
                    "username": username,
                    "password": password,
                    "providerId": id
                }
        data = json.dumps(payload)
        auth_request = requests.post(url_auth, data=data, headers=headers, verify=False)
        time.sleep(0.15)
        response = auth_request.json()

        '''  
        Block is for checking authorization request. 
        Correct response of /api/Auth/Login method suppose to return a .json with 'access_token' and 'refresh_token'. 
        '''
        log_text = f"ProviderID: {id}, response: {auth_request.status_code} [{username}/{password}]\n{auth_request.text}"
        if auth_request.status_code  in (200, 201, 204):
            token = response['access_token']
            break
        elif auth_request.status_code == 401:
            def logging_error():
                print(f"--- {message} ---",'\n' if message != "Message for the log only." else '401 Error. Check the log file.')
                logging.error(f"{message}" if message != "Message for the log only." else '')
                logging.error(log_text)
                if sys.platform == 'win32':
                    os.system('pause')
                sys.exit()
            if response.get('type') and response.get('type') == 'TransitPasswordExpiredBimException':
                message = f"Password for [{username}] has been expired!"
                logging_error()
            elif response.get('type') and response.get('type') == 'IpAddressLoginAttemptsExceededBimException':
                message = "Too many authorization attempts. IP address has been blocked!"
                logging_error()
            elif response.get('type') and response.get('type') == 'AuthCommonBimException':
                message = f"Unauthorized access. Check credentials: {username}/{password}"
                logging_error()
            else:
                message = "Message for the log only."
                logging_error()
        else:
            logging.error(log_text)
    
    return token


if __name__ == "auth_data":
    credentials, provider_id = get_credentials()
    token = get_token(credentials['url'], credentials['username'], credentials['password'], provider_id)
