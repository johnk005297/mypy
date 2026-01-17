import logging
import requests
import base64
import time
import json
import re
import binascii
import os
from getpass import getpass
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
disable_warnings(InsecureRequestWarning)
from rich.console import Console
from rich.tree import Tree
from rich import print as rprint
from tools import Tools
from mlogger import Logs


logger = logging.getLogger(__name__)
logs = Logs()

class Vsphere:

    url: str = "https://vcenter.bimeister.io"
    connection_err_msg: str = "Connection error. Check the log."
    _vsphere_release_schema: str = "8.0.3.0"

    def __init__(self):
        self.tools = Tools()
        self.console = Console()

    def get_credentials(self, username=None, password=None):
        """ Function prompts user's credentials and encode it into base64 proper format. """

        username: list = input("Enter username: ").split("@") if not username else username.split("@")
        password: str = getpass("Enter password: ") if not password else password

        if username and password:
            creds: str = username[0] + '@bimeister.com' + ':' + password
        else:
            logger.error("No correct credentials were provided.")
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
            if (os.environ.get('DOMAIN_USER') or os.getenv("DOMAIN_USER")) and not username:
                username_utf_encoded = os.environ.get('DOMAIN_USER').encode("utf-8")
                username_b64_decoded = base64.b64decode(username_utf_encoded)
                username = username_b64_decoded.decode("utf-8").strip() # username utf decoded
            if (os.environ.get('DOMAIN_PASSWORD') or os.getenv("DOMAIN_PASSWORD")) and not password:
                password_utf_encoded = os.environ.get('DOMAIN_PASSWORD').encode("utf-8")
                password_b64_decoded = base64.b64decode(password_utf_encoded)
                password = password_b64_decoded.decode("utf-8").strip() # password utf decoded
        except binascii.Error as err:
            logger.error(err)
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
                logger.info(f"{response.status_code}")
                data: dict = response.json()
                return data['value']
            else:
                logger.error(response.text)
                print(f"Error: {response.json()['value']['error_type']}\nCheck the logs!")
                return False
        except requests.exceptions.RequestException as err:
            logger.error(err)
            print(self.connection_err_msg)
            return False
        except:
            logger.error(response.text)
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
            logger.error(err)
            print(self.connection_err_msg)
            return False
        data = response.json()
        group_id: list = [x['folder'] for x in data if x['type'] == 'VIRTUAL_MACHINE' and x['name'] in folders]
        return group_id

    def get_vm_power_state(self, headers, vm):
        """ Check for power state for provided VMs. """

        url: str = f"{self.url}/api/vcenter/vm/{vm}/power"
        response = self.tools.make_request('GET', url, headers=headers, verify=False, print_err=True)
        if not response:
            return None
        try:
            data = response.json()
            return data['state']
        except Exception as err:
            logger.error(err)
            return None

    def get_array_of_vm(self, headers, search_for_exclude='', search_for='', powered_on=False) -> dict:
        """ Function returns an array of VM in vSphere's cluster in format {'vm-moId': 'vm-name'}. """

        url = f"{self.url}/api/vcenter/vm"
        response = self.tools.make_request('GET', url, headers=headers, verify=False, print_err=True)
        if not response:
            return None
        try:
            data = response.json()
        except Exception as err:
            logger.error(err)
            return None

        exclude_vm: list = [vm['name'] for vm in data if search_for_exclude and re.search(search_for_exclude.replace('*', '.*'), vm['name'])]
        if not search_for:
            if powered_on:
                vm_array: dict = { vm['vm']: {'name': vm['name'], 'moId': vm['vm'], 'power_state': vm['power_state']} for vm in data if vm['power_state'] == 'POWERED_ON' and vm['name'] and vm['name'] not in exclude_vm }
            else:
                vm_array: dict = { vm['vm']: {'name': vm['name'], 'moId': vm['vm'], 'power_state': vm['power_state']} for vm in data if vm['name'] and vm['name'] not in exclude_vm }
        else:
            if powered_on:
                vm_array: dict = {
                                    vm['vm']: {'name': vm['name'], 'moId': vm['vm'], 'power_state': vm['power_state']}
                                    for vm in data if vm['power_state'] == 'POWERED_ON' and vm['name'] and re.search(search_for.replace('*', '.*'), vm['name']) and vm['name'] not in exclude_vm
                                    }
            else:
                vm_array: dict = {
                                    vm['vm']: {'name': vm['name'], 'moId': vm['vm'], 'power_state': vm['power_state']}
                                    for vm in data if vm['name'] and re.search(search_for.replace('*', '.*'), vm['name']) and vm['name'] not in exclude_vm
                                    }
        return vm_array

    def restart_os(self, headers, vm_array):
        """ Function performs OS restart for a given array. """

        if not isinstance(vm_array, dict):
            print("Provided array should be a dictionary.")
            return False
        for value in vm_array.values():
            reboot_vm_msg: str = f"[bold magenta]Reboot guest OS: {value['name']}[/bold magenta]  [green]✅[/green]"
            url_reboot: str = f"{self.url}/api/vcenter/vm/{value['moId']}/guest/power?action=reboot"
            url_reset: str = f"{self.url}/api/vcenter/vm/{value['moId']}/power?action=reset"
            if self.get_vm_power_state(headers=headers, vm=value['moId']) == 'POWERED_ON':
                response = self.tools.make_request('POST', url_reboot, headers=headers, verify=False)
                time.sleep(0.15)
                if not response:
                    response = self.tools.make_request('POST', url_reset, headers=headers, return_err_response=True, verify=False)
                    if not response:
                        self.console.log(f"[red]No connection to {value['name']}. Check VM in vCenter![/red]")
                        continue
                if response and response.status_code in range(200, 205):
                    self.console.print(reboot_vm_msg, overflow="ellipsis")
            else: continue

    def start_vm(self, headers, moId, name):
        """ Start provided VM in vSphere. """

        url: str = f"{self.url}/rest/vcenter/vm/{moId}/power/start"
        power_on_msg: str = f"[bold magenta]Power On VM: {name}[/bold magenta]"

        with self.console.status(power_on_msg, spinner="earth") as status:
            if self.get_vm_power_state(headers, moId) == "POWERED_ON":
                self.console.print(power_on_msg + "  [green]✅[/green]", overflow="ellipsis")
                return True
            response = self.tools.make_request('POST', url, headers=headers, verify=False, return_err_response=True)
            if response.status_code not in (200, 204):
                self.console.log(f"[red]No connection to {name}. Check VM in vCenter![/red]")
                return False
            count = 0
            while count < 650:
                count += 1
                power_status = self.get_vm_power_state(headers, moId)
                status.update(power_on_msg + "  [green]✅[/green]")
                time.sleep(0.5)
                if power_status == "POWERED_ON":
                    self.console.print(power_on_msg + "  [green]✅[/green]", overflow="ellipsis")
                    return True
                elif power_status != "POWERED_ON":
                    continue
            else:
                self.console.log(f"[red]Error on start {name} within 10 minutes. Check VM status in vCenter![/red]")
                return False

    def stop_vm(self, headers, moId, name):
        """ Stop provided VM in vSphere. """

        url_shutdown: str = f"{self.url}/sdk/vim25/{self._vsphere_release_schema}/VirtualMachine/{moId}/ShutdownGuest"
        url_stop: str = f"{self.url}/api/vcenter/vm/{moId}/power?action=stop"
        shutdown_msg: str = f"[bold magenta]Shutdown guest OS: {name}[bold magenta]  [green]✅[/green]"
        shutting_down_msg: str = f"[bold magenta]Shutdown guest OS: {name}[/bold magenta]"

        with self.console.status(shutting_down_msg, spinner="earth") as status:
            if self.get_vm_power_state(headers, moId) == "POWERED_OFF":
                self.console.print(shutdown_msg, overflow="ellipsis")
                return True
            power_off: bool = False
            response = self.tools.make_request('POST', url_shutdown, headers=headers, return_err_response=True, verify=False)
            if response.status_code not in (200, 204):
                response = self.tools.make_request('POST', url_stop, headers=headers, return_err_response=True, verify=False)
                if response.status_code not in (200, 204):
                    self.console.log(f"[red]No connection to {name}. Check VM in vCenter![/red]")
                    return False
                elif response.status_code in (200, 204):
                    power_off = True
            count = 0
            while count < 900:
                count += 1
                power_status = self.get_vm_power_state(headers, moId)
                status.update(shutting_down_msg)
                time.sleep(0.5)
                if power_status != "POWERED_OFF":
                    continue
                elif power_status == "POWERED_OFF":
                    if power_off:
                        self.console.print(f"[bold magenta]Power Off VM: {name}[/bold magenta]  [green]✅[/green]", overflow="ellipsis")
                    else:
                        self.console.print(shutdown_msg, overflow="ellipsis")
                    return True
            else:
                self.console.log(f"[red]Error on stop {name} within 15 minutes. Check VM status in vCenter![/red]")
                return False

    def take_snapshot(self, headers, moId, vm_name, snap_name='', description=''):
        """ Function takes snapshot of a given VM. Requires moId of the VM."""

        url: str = f"{self.url}/sdk/vim25/{self._vsphere_release_schema}/VirtualMachine/{moId}/CreateSnapshotEx_Task"
        payload = {
                    "description": description,
                    "memory": False,
                    "name": snap_name
                    }
        response = self.tools.make_request('POST', url, headers=headers, data=json.dumps(payload), verify=False, return_err_response=True)
        if not response:
            return False
        if response.status_code == 200:
            logger.info(f"Created snapshot for VM: {vm_name}")
            return True
        else:
            print(f"Error with {vm_name}. Check logs: {logs.filepath}")
            return False
    
    def get_vm_snapshots(self, headers, moId, vm_name) -> dict:
        """ Get snapshot Id, virtual machine Id, snapshot name for a given VM. """

        url: str = f"{self.url}/sdk/vim25/{self._vsphere_release_schema}/VirtualMachine/{moId}/snapshot"
        try:
            response = requests.get(url=url, headers=headers, verify=False)
            if response.status_code == 200:
                data = response.json() if bool(response.text) else False
                logger.info(f"Get list of snapshots VM: {vm_name}")
        except requests.exceptions.HTTPError as err:
            logger.error(err)
            print("Error. Check the log!")
            return False
        except Exception as err:
            logger.error(err)
            print("Error. Check the log!")
            return False
        snapshots: dict = {}
        snapId, vmId, snapName = [], [], []
        def collect_snapshot_names(data, depth=0, count=1):
            for x in data:
                for k,v in x.items():
                    if k == 'snapshot':
                        snapId.append(v['value'])
                    if k == 'vm':
                        vmId.append(v['value'])
                    if k == 'name':
                        snapName.append(' '*depth + v)
                    if isinstance(v, list):
                        collect_snapshot_names(v, depth+2, count+1) # recursion to loop through nested lists with dictionaries and get snapshot names
        if data:
            collect_snapshot_names(data['rootSnapshotList'])
        # add result data into snapshots dictionary
        result = list(zip(snapId, vmId, snapName))
        for num, x in enumerate(result, 1):
            snapshots[num] = {'snapId': x[0], 'vmId': x[1], 'snapName': x[2]}
        return snapshots

    def print_vm_snapshots(self, vm_name, snapshots: dict):
        """ Print VM snapshots. """

        tree = Tree(vm_name)
        for snap in snapshots.values():
            if snap['snapName']:
                tree.add(snap['snapName'])
        rprint(tree)

    def revert_to_snapshot(self, headers, moId, vm_name, print_msg=True):
        """ Revert chosen VM(s) to a given snapshot. """

        url: str = f"{self.url}/sdk/vim25/{self._vsphere_release_schema}/VirtualMachineSnapshot/{moId}/RevertToSnapshot_Task"
        try:
            payload = {
                        "suppressPowerOn": True
                        }
            response = requests.post(url=url, headers=headers, data=json.dumps(payload), verify=False)
            if response.status_code == 200:
                msg: str = f"Revert to snapshot VM: {vm_name}"
                if print_msg:
                    print(msg)
                logger.info(msg)
                return True
            elif response.status_code == 500:
                data = response.json() if bool(response.text) else False
                logger.error(data)
                return False
        except requests.exceptions.HTTPError as err:
            logger.error(err)
            print("Error. Check the log!")
            return False
        except Exception as err:
            logger.error(err)
            print("Error. Check the log!")
            return False            

    def remove_vm_snapshot(self, headers, moId, print_msg=True):
        """ Remove snapshots for a given VM. """

        url: str = f"{self.url}/sdk/vim25/{self._vsphere_release_schema}/VirtualMachineSnapshot/{moId}/RemoveSnapshot_Task"
        try:
            payload = {
                        "removeChildren": False
                        }
            response = requests.post(url=url, headers=headers, data=json.dumps(payload), verify=False)
            if response.status_code in (200, 204):
                if print_msg:
                    print(f"Remove snapshot: {moId}")
                logger.info(f"Remove snapshot: {moId}")
                return True
        except requests.exceptions.HTTPError as err:
            logger.error(err)
            print("Error. Check the log!")
            return False
        except Exception as err:
            logger.error(err)
            print("Error. Check the log!")
            return False

    def is_has_snap(self, headers, vm_name, snap_name) -> bool:
        """ Function tries to find a snapshot in vSphere for a given VM.
            Returns True if object was found, false otherwise.
            Basically, it's a workaround to get task status.
        """

        # getting first key from the dictionary
        vm_moId = next(iter(self.get_array_of_vm(headers, [], vm_name)))
        snapshots = [snap['snapName'].strip() for snap in self.get_vm_snapshots(headers, vm_moId, vm_name).values()]
        if snap_name in snapshots:
            return True
        else:
            return False

    def get_tasks(self, headers):
        """ Function not in use, because of that piece of shit vSphere API documentation.

        """
        import json
        tools = Tools()
        # url: str = f"{self.url}/api/cis/tasks?action=list"
        # url: str = f"{self.url}/rest/cis/tasks"
        url: str = f"{self.url}/api/vcenter/tasks"
        headers.update({'Content-type': 'application/json'})
        # payload = {
        #     "filter_spec": {
        #         "tasks": ['task-1360811'],
        #         "services": ["com.vmware.vcenter.VM"]
        #     }
        # }
        # response = self.tools.make_request('GET', url, return_err_response=True, data=json.dumps(payload), verify=False, headers=headers)
        response = self.tools.make_request('GET', url, return_err_response=True, verify=False, headers=headers)
        # print(response.status_code)
        # print(response.json())

