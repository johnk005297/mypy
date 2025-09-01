# Tool modules to work with folders and files
import logging
import inspect
import os
import socket
import base64
import platform
import json
import shutil
import time
import random
import string
import pathlib
import zipfile
import requests
import re
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


class Folder:
    @staticmethod
    def create_folder(path, folder_name):
        try:
            if not os.path.isdir(path + '/' + folder_name):
                os.mkdir(path + '/' + folder_name)
        except OSError as err:
            print("ERROR in create folder function.")
            logger.error(err)
            return False

    @staticmethod
    def clean_folder(path_to_folder:str, remove=False):
        """ Function removes everything in provided directory. """

        filename:str = path_to_folder.split('/')[-1]
        try:
            if os.path.isdir(path_to_folder):
                shutil.rmtree(path_to_folder, ignore_errors=True)
                time.sleep(0.10)
                if not remove:
                    os.mkdir(path_to_folder)
                    time.sleep(0.10)
                    print(f'\n   - {filename} folder is now empty.')
            else:
                print(f'   - no {filename} folder was found.')
        except OSError as err:
            logger.error(err)
            print("Error occured. Check the logs.")
            return False
        return True

    @staticmethod
    def get_content(folder=None):
        """ Function provides current directory content. """

        if not folder:
            command = "dir" if platform.system == "Windows" else "ls -lha"
        else:
            command = f"dir {folder}" if platform.system == "Windows" else f"ls -lha {folder}"
        return command


class File:

    @staticmethod
    def read_file(filepath):
        """ Read from text files. Function recognizes .json, .csv, .yaml file separately. """

        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                if os.path.splitext(filepath)[1] == '.json':    # checking extension of the file
                    try:
                        content = json.load(file)
                    except json.JSONDecodeError as err:
                        print(f"Error with the {filepath} file. Check the logs.")
                        logger.error(f"Error with {filepath}.\n{err}")
                        return False
                    return content
                elif os.path.splitext(filepath)[1] == '.csv':
                    df = pd.read_csv(filepath)
                    return df
                elif os.path.splitext(filepath)[1] in ['.yaml', '.yml']:
                    pass #TO-DO
                else:
                    content = file.read()
                    return content
        except OSError as err:
            logger.error(err)
            return False

    @staticmethod
    def replace_str_in_file(filepath_2read, filepath_2write, find, replace):
        """  Function takes 4 arguments: full path for filename to read, full path for filename to write, what to find, what to put instead of what to find.  """

        with open(filepath_2read, 'r', encoding='utf-8') as file:
            new_json = file.read().replace(find, replace)      # find/replace vars must be string
        with open(filepath_2write, 'w', encoding='utf-8') as file:
            file.write(new_json)

    @staticmethod
    def remove_file(path_to_file):
        if os.path.isfile(path_to_file):
            os.remove(path_to_file)
            return True
        return False


class Tools:

    @staticmethod
    def counter(start=0):
        """ Function closure for counter. """
        def start_count():
            nonlocal start
            start += 1
            return int("{0:02d}".format(start)) # make two digits minimum to display
        return start_count

    @staticmethod
    def create_random_name():
        """ Create random string of 20 characters. """

        random_name: str = ''.join(random.choice(string.ascii_letters) for x in range(20))
        return random_name

    @staticmethod
    def run_terminal_command(command=''):
        """ Function for execution OS command in shell. """        

        os_name = 'Windows' if platform.system == "Windows" else 'Linux'
        command = input("{0} shell: ".format(os_name)).strip() if not command else command
        os.system(command)

    @staticmethod
    def connect_ssh(host='', username=''):
        """ Establish remote ssh connection. """

        command = f"ssh -o StrictHostKeyChecking=no {username}@{host}"
        try:
            os.system(command)
        except OSError as err:
            logger.error(err)
            return False

    @staticmethod
    def zip_files_in_dir(dirName, archName):
        """ Arhive files into zip format. """

        directory = pathlib.Path(dirName + '/')
        with zipfile.ZipFile(archName + '.zip', mode='w') as archive:
            try:
                for file_path in directory.iterdir():
                    archive.write(file_path, arcname=file_path.name)
            except Exception:
                print("Error occured while zipping logs.")
                return False
        return True

    @staticmethod
    def calculate_timedelta(days):
        """ Function gets days as input data, and provides the amount of epoch seconds by subtracting provided days from current time. """

        epoch_time:int = int(datetime.now().timestamp())
        days:int = days * 86400      # 86400 is the amount of seconds in 24 hours
        delta:int = epoch_time - days
        return delta

    @staticmethod
    def is_user_in_group(group):
        """ Check user groups in linux. Function receives an argument which is a group name, and checks if there is such a group in the list. """
        import grp
        lst = [grp.getgrgid(group).gr_name for group in os.getgroups()]
        return True if group in lst else False

    @staticmethod
    def is_user_root():
        """ Get current user id. """
        user_id = os.getuid()
        return True if user_id == 0 else False

    @staticmethod
    def get_flag_values_from_args_str(args: list, search_arg: str) -> str:
        """ From a given list of args find needed argument and take it's value(s). """

        find_str: str = '{0}(=|\s)"(.*?)"'.format(search_arg)
        search = re.search(find_str, ' '.join(args))
        if search:
            result: str = search.group(2)
        else:
            result = ''
        return result

    @staticmethod
    def is_socket_available(host: str, port: int, timeout: int=1):
        """
        Checks if a TCP socket is available (open) on a remote host and port.

        Args:
            host (str): The hostname or IP address of the target.
            port (int): The port number to check.
            timeout (int, optional): The timeout in seconds for the connection attempt.
                                    Defaults to 1.

        Returns:
            bool: True if the socket is available, False otherwise.
        """
        try:
            # Create a socket object
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Set a timeout for the connection attempt
            s.settimeout(timeout)
            # Attempt to connect to the host and port
            s.connect((host, port))
            # If connection is successful, close the socket and return True
            s.shutdown(socket.SHUT_RDWR) # Ensures clean shutdown
            s.close()
            return True
        except socket.timeout as err:
            logger.error(err)
            return False
        except ConnectionRefusedError:
            # Connection was actively refused by the target
            logger.error(err)
            return False
        except OSError as err:
            # Catch other socket-related errors (e.g., host not found)
            logger.error(err)
            return False
        except Exception as err:
            # Catch any other unexpected errors
            logger.error(err)
            return False

    @staticmethod
    def is_url_available(url):
        """ Check if URL is available. """

        response = Tools.make_request('HEAD', url, allow_redirects=True)
        if response and response.status_code in range(200, 299):
            return response.url.rstrip('/')
        else:
            return False

    @staticmethod
    def get_creds_from_env(user_varname='', password_varname='') -> tuple:
        """ Function returns a tuple of username and password. """

        env_user: str = user_varname
        env_pass: str = password_varname
        if os.getenv(env_user) and os.getenv(env_pass):
            username = os.getenv(env_user)
            password = os.getenv(env_pass)
        else:
            logger.error("No credentials were found in .env file.")
            return None, None
        username_utf_encoded = username.encode("utf-8")
        username_b64_decoded = base64.b64decode(username_utf_encoded)
        username = username_b64_decoded.decode("utf-8")
        password_utf_encoded = password.encode("utf-8")
        password_b64_decoded = base64.b64decode(password_utf_encoded)
        password = password_b64_decoded.decode("utf-8")
        return username, password

    @staticmethod
    def make_request(method, url, print_err=False, return_err_response=False, **kwargs):
        """
        A wrapper function to make http requests with centralized exception handling.
        Args:
            method (str): The HTTP method (e.g., 'GET', 'POST', 'PUT', 'DELETE').
            url (str): The URL to send the request to.
            **kwargs: Additional keyword arguments to pass to the requests method
                    (e.g., params, data, json, headers, timeout, auth).

        Returns:
            requests.Response: The response object from the HTTP request.

        Raises:
            ValueError: If an unsupported HTTP method is provided.
        """
        if not url.startswith('http'):
            url = 'https://' + url
        caller_func = inspect.currentframe().f_back.f_code.co_name
        try:
            if method == 'GET':
                response = requests.get(url, **kwargs)
            elif method == 'POST':
                response = requests.post(url, **kwargs)
            elif method == 'PUT':
                response = requests.put(url, **kwargs)
            elif method == 'DELETE':
                response = requests.delete(url, **kwargs)
            elif method == 'HEAD':
                response = requests.head(url, **kwargs)
            elif method == 'OPTIONS':
                response = requests.options(url, **kwargs)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            logger.info(f"{caller_func} {response.status_code} {method} {url}")
            return response
        except requests.exceptions.HTTPError as err:
            logger.error(f"{caller_func} {err}")
            if print_err: print(f"HTTP Error: {err}")
            return response if return_err_response else None
        except requests.exceptions.ConnectionError as err:
            logger.error(f"{caller_func} {err}")
            if print_err: print(f"Connection Error: {err}")
            return response if return_err_response else None
        except requests.exceptions.Timeout as err:
            logger.error(f"{caller_func} {err}")
            if print_err: print(f"Timeout Error: {err}")
            return response if return_err_response else None
        except requests.exceptions.MissingSchema as err:
            logger.error(f"{caller_func} {err}")
            if print_err: print(f"MissingSchema Error: {err}")
            return response if return_err_response else None
        except requests.exceptions.RequestException as err:
            logger.error(f"{caller_func} {err}")
            if print_err: print(f"An unexpected Requests error occurred: {err}")
            return response if return_err_response else None


class Bimeister:

    @staticmethod
    def apply_bimeister_customUI(url, token, file):
        """ Function to upload custom user intreface files. """

        url = f"{url}/api/Settings/CustomUI"
        headers = {'accept': '*/*', 'Authorization': f"Bearer {token}"}
        try:
            with open(file, mode='rb') as file:
                response = requests.post(url=url, headers=headers, files={'file': file}, verify=False)
                if response.status_code == 403:
                    print(response.status_code)
                    print("User doesn't have sufficient privileges!")
                elif response.status_code == 404:
                    print(response.status_code)
                    print("No API route was found!")
                elif response.status_code == 204:
                    print("Files uploaded successfully.")
        except FileNotFoundError as err:
            logger.error(err)
            print(err)
        except requests.RequestException as err:
            logger.error(err)
            print("Error! Check the log.")
        except Exception as err:
            logger.error(err)
            print("Error! Check the log.")

    @staticmethod
    def print_bim_version(url):
        """ Get bimeister commit version. """

        if not url.startswith('http'):
            url = 'https://' + url
        url = url + '/assets/version.json' if not url[-1] == '/' else url + 'assets/version.json'
        count = 0
        while True:
            try:
                response = requests.get(url, verify=False, timeout=1)
                response.raise_for_status()
                data = response.json()
                print(f"commit: {data['GIT_COMMIT']}\nversion: {data['BUILD_FULL_VERSION']}")
                return True
            except requests.exceptions.ConnectionError as err:
                logger.error(err)
                if count > 0: 
                    print("Connection error: Check URL address.")
                    return False
            except json.JSONDecodeError as err:
                print("JSONDecodeError: Check URL address.")
                logger.error(err)
                return False
            except requests.exceptions.MissingSchema as err:
                print(f"Invalid URL. MissingSchema.")
                logger.error(err)
                return False
            except Exception as err:
                print("Unexpected error. Check the logs.")
                logger.error(err)
                return False
            count += 1
            if count == 1:
                url = url.split(':')
                url = 'http:' + url[1] if url[0] == 'https' else 'https:' + url[1]
            elif count > 1:
                return False

    @staticmethod
    def recalculate_path(url, token):
        """ Function to call recalculate API method for different services. """

        services: dict = {
                        "data-synchronizer": {"api_path": "/api/data-synchronizer/technical-objects-registry/recalculate-paths", "id": ""},
                        "maintenance": {"api_path": "/api/EnterpriseAssetManagementTechnicalObjects/RecalculatePaths", "id": ""},
                        "work-permits-management": {"api_path": "/api/work-permits-management/technical-objects/recalculate-paths", "id": ""}
                        }
        for num, service in enumerate(services, 1):
            print(f"{num}. {service}")
            services[service]["id"] = num
        try:
            user_input = int(input("Select number: "))
        except KeyboardInterrupt:
            print('\nKeyboardInterrupt')
            return False
        except ValueError as err:
            print("Invalid input. Has to be a number.")
            return False
        except Exception as err:
            print("Some error occured. Check the log.")
            logger.error(err)
            return False   

        headers = {'accept': '*/*', 'Authorization': f"Bearer {token}"}
        for service in services:
            if services[service]["id"] == user_input:
                url = url + services[service]["api_path"]
                break
        try:
            response = requests.patch(url, headers=headers, verify=False)
            response.raise_for_status()
            if response.status_code in [200, 201, 204]:
                logger.info(f"{url} {response.status_code}")
                print("Paths recalculated successfully!")
            return True
        except Exception as err:
            print(f"Error occurred. Check the log. Response code: {response.status_code}")
            logger.error(err)
            return False
    
    @staticmethod
    def get_list_of_templates(url, token) -> list:
        """ Get list of templates from reports service. """

        url = url + '/api/Templates'
        headers = {'Content-Type': 'application/json', 'Authorization': f"Bearer {token}"}
        try:
            response = requests.get(url=url, headers=headers, verify=False)
            response.raise_for_status()
            if response.status_code == 200:
                logger.info(f"{url} {response.status_code}")
                data = response.json()
                return data
        except Exception as err:
            print(err)
            return False
    
    @staticmethod
    def print_list_of_templates(templates: list):
        """ Function prints the list of provided templates. """

        if not templates:
            print("No data was provided.")
            return False
        count = Tools.counter()
        for template in templates:
            print(f"{count()})Name: {template['name']}  Id: {template['id']}  TypeName: {template['typeName']}")

    @staticmethod
    def export_templates(url, token, id: list):
        """ Export templates for a given list of id's. """

        if not id:
            print("No template id was provided.")
            return False
        headers = {'Content-Type': 'text/plain', 'Authorization': f"Bearer {token}"}
        for i in id:
            _url = f"{url}/api/Templates/{i}/TemplateContent"
            try:
                response = requests.get(url=_url, headers=headers, verify=False)
                response.raise_for_status()
                if response.status_code == 200:
                    data = response.json()
                    with open(f"{i}.json", mode='w', encoding='utf-8') as file:
                        file.write(json.dumps(data, indent=2))
                        print(f"File exported successfully: {i}.json")
            except requests.exceptions.HTTPError as err:
                if err.response.status_code == 404:
                    logger.error(err)
                    print(f"404 Client Error for id: {i}")
            except Exception as err:
                logger.error(err)
                print("Error occured. Read the log! ")
                return False
