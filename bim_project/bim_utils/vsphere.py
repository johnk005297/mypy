import requests
import base64
import time
import os
from log import Logs
from tools import Tools
from getpass import getpass
from dotenv import load_dotenv
load_dotenv()
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
disable_warnings(InsecureRequestWarning)


class Vsphere:

    __logger = Logs().f_logger(__name__)
    url_session_id: str = "https://vcenter.bimeister.io/rest/com/vmware/cis/session"
    url: str = "https://vcenter.bimeister.io/api/vcenter"

    def __init__(self):
        self.username: str = ''
        self.password: str = ''

    def get_credentials(self, username=None, password=None):
        """ Function prompts user's credentials and encode it into base64 proper format. """

        self.username: list = input("Enter username: ").split("@") if not username else username.split("@")
        self.password: str = getpass("Enter password: ") if not password else password

        if self.username and self.password:
            creds: str = self.username[0] + '@bimeister.com' + ':' + self.password
        else:
            self.__logger.error("No correct credentials were provided.")
            return False
        creds_bytes = creds.encode("utf-8")
        creds_encoded = base64.b64encode(creds_bytes)
        creds_base64 = creds_encoded.decode("utf-8")
        return creds_base64

    def get_headers(self, username=None, password=None):
        token: str = self.get_session_token(username=username, password=password)
        if not token:
            return False
        headers = {'vmware-api-session-id': token}
        return headers

    def get_session_token(self, username, password):
        """ Function to get token for execution requests. """

        ## for tests only
        # username = os.getenv('user')
        # password = os.getenv('password')
        # username_bytes = username.encode("utf-8")
        # username_encoded = base64.b64decode(username_bytes)
        # username = username_encoded.decode("utf-8").strip()
        # password_bytes = password.encode("utf-8")
        # password_encoded = base64.b64decode(password_bytes)
        # password = password_encoded.decode("utf-8").strip()

        creds = self.get_credentials(username, password)
        if not creds:
            return False
        headers = {'Authorization': 'Basic {}'.format(creds)}
        payload = {}
        try:
            response = requests.post(url=self.url_session_id, headers=headers, data=payload, verify=False)
            if response.status_code == 200:
                self.__logger.info(f"{response.status_code}")
                data: dict = response.json()
                return data['value']
            else:
                self.__logger.error(response.text)
                print(f"Error: {response.json()['value']['error_type']}\nCheck the logs!")
                return False
        except requests.exceptions.RequestException as err:
            print("Connection error. Check the log.")
            self.__logger.error(err)
            return False

    def print_list_of_vm(self, headers):
        """ Print all VM names from the list. """

        vm_dict = self.get_array_of_vm(headers)
        if not vm_dict:
            return False
        for value in vm_dict.values():
            print(value)

    def get_folders_group_id(self, headers, folders: tuple = ()):
        """ Get group's ID needed to be excluded from the reboot list. """

        response = requests.get(url=f"{self.url}/folder", headers=headers, verify=False)
        if response.status_code != 200:
            self.__logger.error(response.text)
            return False
        data = response.json()
        group_id: list = [x['folder'] for x in data if x['type'] == 'VIRTUAL_MACHINE' and x['name'] in folders]
        return group_id

    def get_array_of_vm(self, headers):
        """ Get an array of VM in vSphere's cluster with POWERED_ON state. """

        # Getting a pool of VMs to be excluded from the reboot list.
        folders = ('Implementation', 'Infrastructure')
        groups_to_exclude = self.get_folders_group_id(headers, folders)
        exclude_list: list = []
        for group in groups_to_exclude:
            url = f"https://vcenter.bimeister.io/rest/vcenter/vm?filter.folders={group}"
            response = requests.get(url=url, headers=headers, verify=False)
            if response.status_code != 200:
                self.__logger.error(response.text)
                return False
            data = response.json()
            for vm in data['value']:
                exclude_list.append(vm['name'])

        response = requests.get(url=f"{self.url}/vm", headers=headers, verify=False)
        if response.status_code == 200:
            self.__logger.info(response.status_code)
            data = response.json()
            vm_dict: dict = { vm['vm']: vm['name'] for vm in data if vm['power_state'] == 'POWERED_ON' and vm['name'] not in exclude_list}
            vm_dict = dict(sorted(vm_dict.items(), key=lambda item: item[1]))
        else:
            self.__logger.error(response.text)
            print("Error of getting list of VMs. Check the logs!")
            return False
        return vm_dict

    def restart_os(self, headers, vm_array, exclude_list):
        """ Function performs OS restart for a given array. """

        if not isinstance(vm_array, dict):
            print("Provided array should be a dictionary.")
            return False
        confirm: bool = True if input("YOU ARE ABOUT TO RESTART ALL VM's IN THE CLUSTER!!! ARE YOU SURE?(YES|NO) ").lower() == 'yes' else False
        if not confirm:
            print("Abort restart procedure!")
            return False
        counter, number = Tools.counter(), 0
        for key, value in vm_array.items():
            if value in exclude_list:
                continue
            url: str = f"{self.url}/vm/{key}/guest/power?action=reboot"
            response = requests.post(url=url, headers=headers, verify=False)
            if response.status_code == 200:
                number = counter()
                self.__logger.info(f"{value} {response.status_code}")
                time.sleep(0.15)
            else:
                self.__logger.error(response)
            print(f"Restart OS: {value}  {response.status_code}")
        print(f"\nAmount of restarted VMs: {number}")
