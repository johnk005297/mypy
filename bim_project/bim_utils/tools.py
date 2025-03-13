#
# Tool modules to work with folders and files
import os
import platform
import json
import shutil
import time
import random
import string
import pathlib
import zipfile
import requests
from datetime import datetime
from log import Logs
logger = Logs().f_logger(__name__)


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
            command = "dir" if Tools.is_windows() else "ls -lha"
        else:
            command = f"dir {folder}" if Tools.is_windows() else f"ls -lha {folder}"
        return command


class File:

    def read_file(path_to_file, filename):
        """ Read from text files. In .json case function returns a dictionary. Need to pass two arguments in str format: a path and a file name. """
        try:
            with open(f"{path_to_file}/{filename}", 'r', encoding='utf-8') as file:
                if os.path.splitext(f'{path_to_file}/{filename}')[1] == '.json':    # checking extension of the file
                    try:
                        content = json.load(file)
                    except json.JSONDecodeError as err:
                        print(f"Error with the {filename} file. Check the logs.")
                        logger.error(f"Error with {filename}.\n{err}")
                        return False
                    return content
                else:
                    content = file.read()
                    return content
        except OSError as err:
            logger.error(err)
            return False


    def replace_str_in_file(filepath_2read, filepath_2write, find, replace):
        """  Function takes 4 arguments: full path for filename to read, full path for filename to write, what to find, what to put instead of what to find.  """

        with open(filepath_2read, 'r', encoding='utf-8') as file:
            new_json = file.read().replace(find, replace)      # find/replace vars must be string
        with open(filepath_2write, 'w', encoding='utf-8') as file:
            file.write(new_json)


    def remove_file(path_to_file):
        if os.path.isfile(path_to_file):
            os.remove(path_to_file)
            return True
        return False



class Tools:

    # Function closure
    def counter(start=0):
        def start_count():
            nonlocal start
            start += 1

            # two ways(both correct) to format counter, filling first nine digits to two symbols with zero as the first one.
            # return str(start).zfill(2)
            return int("{0:02d}".format(start))
        return start_count


    def is_windows():
        """ Check if OS is windows or not. """
        return True if platform.system() == 'Windows' else False

    def create_random_name():
        """ Create random string of 20 characters. """

        random_name: str = ''.join(random.choice(string.ascii_letters) for x in range(20))
        return random_name

    def run_terminal_command(command=''):
        """ Function for execution OS command in shell. """        

        os_name = 'Windows' if Tools.is_windows() else 'Linux'
        command = input("{0} shell: ".format(os_name)).strip() if not command else command
        os.system(command)

    def connect_ssh(host='', username=''):
        """ Establish remote ssh connection. """

        command = f"ssh -o StrictHostKeyChecking=no {username}@{host}"
        try:
            os.system(command)
        except OSError as err:
            logger.error(err)
            return False

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

    def calculate_timedelta(days):
        """ Function gets days as input data, and provides the amount of epoch seconds by subtracting provided days from current time. """

        epoch_time:int = int(datetime.now().timestamp())
        days:int = days * 86400      # 86400 is the amount of seconds in 24 hours
        delta:int = epoch_time - days
        return delta

    def is_user_in_group(group):
        """ Check user groups in linux. Function receives an argument which is a group name, and checks if there is such a group in the list. """
        import grp
        lst = [grp.getgrgid(group).gr_name for group in os.getgroups()]
        return True if group in lst else False

    def is_user_root():
        """ Get current user id. """
        user_id = os.getuid()
        return True if user_id == 0 else False


class Bimeister:

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
                print(f"name: {data['BRANCH_NAME']}\nversion: {data['BUILD_FULL_VERSION']}")
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

    def recalculate_path(url, token):
        """ Function to call recalculate API method for different services. """

        services: dict = {
                        "data-synchronizer": {"api_path": "/api/data-synchronizer/technical-objects-registry/recalculate-paths", "id": ""},
                        "maintenance": {"api_path": "/api/EnterpriseAssetManagementTechnicalObjects/RecalculatePaths", "id": ""}
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