import requests
import logging
import inspect
import os
import sys
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
import re
from datetime import datetime

from mlogger import Logs


_logger = logging.getLogger(__name__)
_logs = Logs()


class Folder:
    @staticmethod
    def create_folder(path, folder_name):
        try:
            if not os.path.isdir(path + '/' + folder_name):
                os.mkdir(path + '/' + folder_name)
        except OSError as err:
            _logger.error(err)
            print(_logs.err_message)
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
                    print(f'{filename} folder is empty')
            else:
                print(f'no {filename} folder was found')
        except OSError as err:
            _logger.error(err)
            print(_logs.err_message)
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
        import pandas as pd
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                if os.path.splitext(filepath)[1] == '.json':    # checking extension of the file
                    try:
                        content = json.load(file)
                    except json.JSONDecodeError as err:
                        _logger.error(err)
                        print(_logs.err_message)
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
            _logger.error(err)
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
            _logger.error(err)
            return False

    @staticmethod
    def zip_files_in_dir(dirName, archName):
        """ Arhive files into zip format. """

        directory = pathlib.Path(dirName + '/')
        with zipfile.ZipFile(archName + '.zip', mode='w') as archive:
            try:
                for file_path in directory.iterdir():
                    archive.write(file_path, arcname=file_path.name)
            except Exception as err:
                _logger.error(err)
                print(_logs.err_message)
                return False
        return True

    @staticmethod
    def calculate_timedelta(days):
        """ Function gets days as input data, and provides the amount of epoch seconds by subtracting provided days from current time. """

        epoch_time: int = int(datetime.now().timestamp())
        days: int = days * 86400      # 86400 is the amount of seconds in 24 hours
        delta: int = epoch_time - days
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
        """ From a given list of args find needed argument and take its value(s). """

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
            _logger.error(err)
            return False
        except ConnectionRefusedError:
            # Connection was actively refused by the target
            _logger.error(err)
            return False
        except OSError as err:
            # Catch other socket-related errors (e.g., host not found)
            _logger.error(err)
            return False
        except Exception as err:
            # Catch any other unexpected errors
            _logger.error(err)
            return False

    @staticmethod
    def is_url_available(url):
        """ Check if URL is available. """
        response = Tools.make_request('HEAD', url, allow_redirects=True, verify=False)
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
            _logger.error("No credentials were found in .env file.")
            return None, None
        username_utf_encoded = username.encode("utf-8")
        username_b64_decoded = base64.b64decode(username_utf_encoded)
        username = username_b64_decoded.decode("utf-8")
        password_utf_encoded = password.encode("utf-8")
        password_b64_decoded = base64.b64decode(password_utf_encoded)
        password = password_b64_decoded.decode("utf-8")
        return username, password

    @staticmethod
    def make_request(method: str, url: str, print_err=False, return_err_response=False, custom_log_msg=None, **kwargs):
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
            if custom_log_msg:
                _logger.info(f"{caller_func} {response.status_code} {custom_log_msg}")
            else:
                _logger.info(f"{caller_func} {response.status_code} {method} {url}")
            return response
        except requests.exceptions.HTTPError as err:
            _logger.error(f"{caller_func} {err}")
            if print_err: print(f"HTTP Error: {err}")
            return response if return_err_response else None
        except requests.exceptions.ConnectionError as err:
            _logger.error(f"{caller_func} {err}")
            if print_err: print(f"Connection Error: {err}")
            return response if return_err_response else None
        except requests.exceptions.Timeout as err:
            _logger.error(f"{caller_func} {err}")
            if print_err: print(f"Timeout Error: {err}")
            return response if return_err_response else None
        except requests.exceptions.MissingSchema as err:
            _logger.error(f"{caller_func} {err}")
            if print_err: print(f"MissingSchema Error: {err}")
            return response if return_err_response else None
        except requests.exceptions.RequestException as err:
            _logger.error(f"{caller_func} {err}")
            if print_err: print(f"An unexpected Requests error occurred: {err}")
            return response if return_err_response else None
        except Exception as err:
            _logger.error(f"{caller_func} {err}")
            return response if return_err_response else None

    @staticmethod
    def get_resourse_path(relative_path):
        """Get the absolute path to folder with sql files.
        Currently used to bundle the application into one file
        with access to sql_queries folder, .env file, etc.
        """
        try:
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)



