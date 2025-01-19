import requests
import base64
import time
import json
import re
import binascii
from os import environ
from log import Logs
from getpass import getpass
from dotenv import load_dotenv
load_dotenv()
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
disable_warnings(InsecureRequestWarning)


class Vsphere:

    __logger = Logs().f_logger(__name__)
    url: str = "https://vcenter.bimeister.io"
    connection_err_msg: str = "Connection error. Check the log."
    vsphere_release_schema: str = "8.0.3.0"

    def __init__(self):
        pass

    def get_credentials(self, username=None, password=None):
        """ Function prompts user's credentials and encode it into base64 proper format. """

        username: list = input("Enter username: ").split("@") if not username else username.split("@")
        password: str = getpass("Enter password: ") if not password else password

        if username and password:
            creds: str = username[0] + '@bimeister.com' + ':' + password
        else:
            self.__logger.error("No correct credentials were provided.")
            return False
        creds_bytes = creds.encode("utf-8")
        creds_encoded = base64.b64encode(creds_bytes)
        creds_base64 = creds_encoded.decode("utf-8")
        return creds_base64

    def get_headers(self, username=None, password=None):
        """ Form expected headers for vCenter API. """

        token: str = self.get_session_token(username=username, password=password)
        if not token:
            return False
        headers = {'vmware-api-session-id': token}
        return headers

    def get_session_token(self, username='', password=''):
        """ Function to get token for execution requests. """

        try:
            if environ.get('VCENTER_USER') and not username:
                username_utf_encoded = environ.get('VCENTER_USER').encode("utf-8")
                username_b64_decoded = base64.b64decode(username_utf_encoded)
                username = username_b64_decoded.decode("utf-8").strip() # username utf decoded
            if environ.get('VCENTER_PASSWORD') and not password:
                password_utf_encoded = environ.get('VCENTER_PASSWORD').encode("utf-8")
                password_b64_decoded = base64.b64decode(password_utf_encoded)
                password = password_b64_decoded.decode("utf-8").strip() # password utf decoded
        except binascii.Error as err:
            self.__logger.error(err)
            print("Invalid base64-encoded string. Check the logs. Exit!")
            return False

        creds = self.get_credentials(username=username, password=password)
        if not creds:
            return False
        headers = {'Authorization': 'Basic {}'.format(creds)}
        payload = {}
        try:
            response = requests.post(url=f"{self.url}/rest/com/vmware/cis/session", headers=headers, data=payload, verify=False)
            if response.status_code == 200:
                self.__logger.info(f"{response.status_code}")
                data: dict = response.json()
                return data['value']
            else:
                self.__logger.error(response.text)
                print(f"Error: {response.json()['value']['error_type']}\nCheck the logs!")
                return False
        except requests.exceptions.RequestException as err:
            self.__logger.error(err)
            print(self.connection_err_msg)
            return False
        except:
            self.__logger.error(response.text)
            print(self.connection_err_msg)
            return False

    def print_list_of_vm(self, vm_array):
        """ Print all VM names from the dictionary. """

        if not vm_array:
            return False
        vm_list = sorted([vm_array[vm]['name'] for vm in vm_array])
        for vm in vm_list:
            print(vm)

    def get_folders_group_id(self, headers, folders: tuple = ()):
        """ Get group's ID needed to be excluded from the reboot list. """

        try:
            response = requests.get(url=f"{self.url}/api/vcenter/folder", headers=headers, verify=False)
        except requests.exceptions.ConnectionError as err:
            self.__logger.error(err)
            print(self.connection_err_msg)
            return False
        data = response.json()
        group_id: list = [x['folder'] for x in data if x['type'] == 'VIRTUAL_MACHINE' and x['name'] in folders]
        return group_id

    def get_vm_power_state(self, headers, vm):
        """ Check for power state for provided VMs. """

        url: str = f"{self.url}/rest/vcenter/vm/{vm}/power"
        try:
            response = requests.get(url=url, headers=headers, verify=False)
            data = response.json()
            return data['value']['state']
        except Exception as err:
            self.__logger.error(err)
            print("Couldn't get VM power state status. Check the log!")
            return False

    def get_array_of_vm(self, headers, exclude: list, search_for='', powered_on=False):
        """ Function returns an array of VM in vSphere's cluster in format {'vm-moId': 'vm-name'}. """

        try:
            response = requests.get(url=f"{self.url}/api/vcenter/vm", headers=headers, verify=False)
        except ConnectionError as err:
            self.__logger.error(err)
            print(self.connection_err_msg)
            return False
        if response.status_code == 200:
            self.__logger.info(response.status_code)
            data = response.json()
            if not search_for:
                if powered_on:
                    vm_array: dict = { vm['vm']: {'name': vm['name'], 'moId': vm['vm'], 'power_state': vm['power_state']} for vm in data if vm['power_state'] == 'POWERED_ON' and vm['name'] and vm['name'] not in exclude }
                else:
                    vm_array: dict = { vm['vm']: {'name': vm['name'], 'moId': vm['vm'], 'power_state': vm['power_state']} for vm in data if vm['name'] and vm['name'] not in exclude }
            else:
                if powered_on:
                    vm_array: dict = { vm['vm']: {'name': vm['name'], 'moId': vm['vm'], 'power_state': vm['power_state']} for vm in data if vm['power_state'] == 'POWERED_ON' and vm['name'] and re.search(search_for.replace('*', '.*'), vm['name']) and vm['name'] not in exclude }
                else:
                    vm_array: dict = { vm['vm']: {'name': vm['name'], 'moId': vm['vm'], 'power_state': vm['power_state']} for vm in data if vm['name'] and re.search(search_for.replace('*', '.*'), vm['name']) and vm['name'] not in exclude }
        else:
            self.__logger.error(response.text)
            print("Error of getting list of VMs. Check the logs!")
            return False
        return vm_array

    def restart_os(self, headers, vm_array):
        """ Function performs OS restart for a given array. """

        if not isinstance(vm_array, dict):
            print("Provided array should be a dictionary.")
            return False
        for value in vm_array.values():
            url: str = f"{self.url}/api/vcenter/vm/{value['moId']}/guest/power?action=reboot"
            if self.get_vm_power_state(headers=headers, vm=value['moId']) == 'POWERED_ON':
                response = requests.post(url=url, headers=headers, verify=False)
                if response.status_code in (200, 204):
                    self.__logger.info(f"{value['name']} {response.status_code}")
                    print(f"Initiate guest OS reboot: {value['name']}")
                    time.sleep(0.15)
                else:
                    self.__logger.error(response)
                    print(f"Error: {value['name']}")
            else:
                continue
    
    def start_vm(self, headers, moId, name):
        """ Start provided VM in vSphere. """

        url: str = f"{self.url}/rest/vcenter/vm/{moId}/power/start"
        power_state = self.get_vm_power_state(headers, moId)
        if power_state == "POWERED_ON":
            return True
        try:
            response = requests.post(url=url, headers=headers, verify=False)
            if response.status_code != 200:
                self.__logger.error(f"{name}: {response.text}")
                return False            
            print(f"Power On virtual machine: {name}")
        except requests.exceptions.RequestException as err:
            self.__logger.error(err)
            print(f"{name}: Error. Status code: {response.status_code}")
            return False
        except Exception as err:
            self.__logger.error(err)
            print(f"{name}: Error. Status code: {response.status_code}")
            return False
        return True

    def stop_vm(self, headers, moId, name):
        """ Stop provided VM in vSphere. """

        url_shutdown: str = f"{self.url}/rest/vcenter/vm/{moId}/guest/power?action=shutdown"
        url_stop: str = f"{self.url}/api/vcenter/vm/{moId}/power?action=stop"
        power_state = self.get_vm_power_state(headers, moId)
        if power_state == "POWERED_OFF":
            return True
        try:
            response = requests.post(url=url_shutdown, headers=headers, verify=False)
            if response.status_code not in (200, 204):
                response = requests.post(url=url_stop, headers=headers, verify=False)
                if response.status_code not in (200, 204):
                    return False
                else:
                    print(f"Power Off virtual machine: {name}")
                    return True
            print(f"Initiate guest OS shutdown: {name}")
        except requests.exceptions.RequestException as err:
            self.__logger.error(err)
            print(f"{name}: Error. Status code: {response.status_code}")
        except Exception as err:
            self.__logger.error(err)
            print(f"{name}: Error. Status code: {response.status_code}")
        return True

    def take_snapshot(self, headers, moId, vm_name, snap_name='', description=''):
        """ Function takes snapshot of a given VM. Requires moId of the VM."""

        url: str = f"{self.url}/sdk/vim25/{self.vsphere_release_schema}/VirtualMachine/{moId}/CreateSnapshotEx_Task"
        payload = {
                    "description": description,
                    "memory": False,
                    "name": snap_name
                    }
        data = json.dumps(payload)
        try:        
            response = requests.post(url=url, data=data, headers=headers, verify=False)
            if response.status_code == 200:
                data = response.json()
                self.__logger.info(f"Created snapshot for VM: {vm_name}")
                self.__logger.debug(data)
                print(f"Create virtual machine snapshot: {vm_name}")
                return True
            elif str(response.status_code).startswith('5'):
                self.__logger.debug(response.text)
                print("Take snapshot request status: 500. Check the log!")
                return False
        except requests.exceptions.HTTPError:
            self.__logger.error(err)
            print("Error. Check the log!")
            return False
        except Exception as err:
            self.__logger.error(err)
            print("Error. Check the log!")
            return False
    
    def get_vm_snapshots(self, headers, moId, vm_name):
        """ Get snapshot Id, virtual machine Id, snapshot name for a given VM. """

        url: str = f"{self.url}/sdk/vim25/{self.vsphere_release_schema}/VirtualMachine/{moId}/snapshot"
        snapshots: dict = {}
        try:
            response = requests.get(url=url, headers=headers, verify=False)
            if response.status_code == 200:
                data = response.json() if bool(response.text) else False
                self.__logger.info(f"Get list of snapshots VM: {vm_name}")                
        except requests.exceptions.HTTPError as err:
            self.__logger.error(err)
            print("Error. Check the log!")
            return False
        except Exception as err:
            self.__logger.error(err)
            print("Error. Check the log!")
            return False

        # recursion to loop through nested lists with dictionaries and get snapshot names
        def collect_snapshot_name(data, depth=0, count=1):
            for x in data:
                snapshots[count] = {'snapId': x['snapshot']['value'], 'vmId': x['vm']['value'], 'snapName': ' '*depth + x['name']}
                if x.get('childSnapshotList'):
                    collect_snapshot_name(x['childSnapshotList'], depth+2, count+1)
        if isinstance(data, dict) and data.get('rootSnapshotList'):
            collect_snapshot_name(data['rootSnapshotList'])
        else:
            return False
        return snapshots

    def print_vm_snapshots(self, vm_name, snapshots: dict):
        print(f"{vm_name} snapshots:")
        for snap in snapshots.values(): print(snap['snapName'])

    def revert_to_snapshot(self, headers, moId, vm_name):
        """ Revert chosen VM(s) to a given snapshot. """

        url: str = f"{self.url}/sdk/vim25/{self.vsphere_release_schema}/VirtualMachineSnapshot/{moId}/RevertToSnapshot_Task"
        try:
            payload = {
                        "suppressPowerOn": True
                        }
            response = requests.post(url=url, headers=headers, data=json.dumps(payload), verify=False)
            if response.status_code == 200:
                data = response.json() if bool(response.text) else False
                msg: str = f"Revert to snapshot VM: {vm_name}"
                self.__logger.info(msg)
                print(msg)
                return data
            elif response.status_code == 500:
                data = response.json() if bool(response.text) else False
                self.__logger.error(data)
                return False
        except requests.exceptions.HTTPError as err:
            self.__logger.error(err)
            print("Error. Check the log!")
            return False
        except Exception as err:
            self.__logger.error(err)
            print("Error. Check the log!")
            return False            

    def remove_vm_snapshot(self, headers, moId):
        """ Remove snapshots for a given VM. """

        url: str = f"{self.url}/sdk/vim25/{self.vsphere_release_schema}/VirtualMachineSnapshot/{moId}/RemoveSnapshot_Task"
        try:
            payload = {
                        "removeChildren": False
                        }
            response = requests.post(url=url, headers=headers, data=json.dumps(payload), verify=False)
            if response.status_code in (200, 204):
                return True
        except requests.exceptions.HTTPError as err:
            self.__logger.error(err)
            print("Error. Check the log!")
            return False
        except Exception as err:
            self.__logger.error(err)
            print("Error. Check the log!")
            return False

