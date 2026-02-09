import argparse
import requests
import textwrap
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
disable_warnings(InsecureRequestWarning)
from rich.console import Console

import logging
import os
import json
import time

from license import License
from tools import File, Tools
from mrich import ScrollablePanel
from mlogger import Logs

_logger = logging.getLogger(__name__)
_logs = Logs()
_tools = Tools()



def validate_import_server(url: str, token: str, filepath: str):
    ''' Function needs to protect export server from import procedure during a single user session. '''

    server_info = File.read_file(filepath)
    is_serverId_received, server_id = License.get_serverID(License, url, token)
    if not is_serverId_received:
        return None
    if server_info and server_info.split()[1] == server_id:
        ask_for_confirmation: bool = input('This is an export server. Wish to import here?(Y/N): ').lower()
        return True if ask_for_confirmation in ('y', 'yes') else False
    elif not server_info:
        _logger.error(f"Can't detect server info ID in {filepath} file.")
        return False
    else:
        return True


class Object_model:

    _transfer_folder: str = 'transfer_files'
    _object_model_folder: str = 'object_model'
    _object_model_file: str = 'object_model_import_server.json'

    def __init__(self):
        self.console = Console()

    def import_object_model(self, url, token, filepath):
        """ Function takes full path to object model file, and perform POST method. """

        headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}
        url += '/api/Integration/ObjectModel/Import'
        if not os.path.isfile(filepath) or not url or not token:
            print(f"Error: {filepath} file not found")
            return None
        with open(filepath, "r", encoding="utf-8") as file:
            data = file.read()
        # json_payload = json.dumps(data, ensure_ascii=False) # Doesn't work with json.dumps if read from file

        with self.console.status("Importing object model...", spinner="earth"):
            response = _tools.make_request('POST', url, data=data.encode("utf-8"),  headers=headers, verify=False, return_err_response=True)
            if response.status_code not in range(200, 205):
                _logger.error(response.text)
                print(f"Status: {response.status_code}. {_logs.err_message}.")
                return False
            else:
                print(f"Status: {response.status_code} Object model successfully imported.")
                return True


class Workflows:
    __api_Integration_WorkFlow_Import: str = 'api/Integration/WorkFlow/Import'
    _workflows_folder: str = 'workflows'
    _transfer_folder: str = 'transfer_files'

    def __init__(self):
        self.console = Console()
        self.tools = Tools()

    def import_workflows(self, url: str, token: str, filepath: str):
        ''' Function to post workflows using .zip archives data from the export procedure.
            Takes full path to exported_workflows.list file, and takes workflows' IDs from it.
        '''

        url += f'/{self.__api_Integration_WorkFlow_Import}'
        headers = {'accept': '*/*', 'Authorization': f"Bearer {token}"}

        if not os.path.isfile(filepath) or not url or not token:
            print(f"Error: {filepath} file not found")
            return None

        # Read the file with workflows in the list without blank lines
        workflows = [x for x in File.read_file(filepath).split('\n') if x.split()]
        failed_workflows: list = []
        imported_workflows: list = []
        with self.console.status("Importing workflows...", spinner="earth"):
            for workflow in workflows:
                # workflow format: <status>  <id>  <name>
                id = workflow.split(' '*2, maxsplit=2)[1].strip()
                name = workflow.split(' '*2, maxsplit=2)[2].strip()
                wf_title: str = textwrap.shorten("{0}".format(name), width=84, placeholder="...")
                try:
                    with open(f'{self._transfer_folder}/{self._workflows_folder}/{id}.zip', mode='rb') as file:
                        response = self.tools.make_request('POST', url, headers=headers, files={'file': file}, verify=False, return_err_response=True, custom_log_msg=name)
                        if response.status_code not in range(200, 205):
                            _logger.error(response.text)
                            failed_workflows.append("Error {0}: {1})".format(response.status_code, wf_title))
                            continue
                        imported_workflows.append(wf_title)
                        time.sleep(0.03)
                        _logger.debug(f'{response.request.method} "{name}: {id}" {response.status_code}')
                except FileNotFoundError:
                    print(f"Process not found: {name}")
                    continue
                except:
                    _logger.error()
                    continue
        successful_workflows: int = len(imported_workflows)
        imported_workflows.extend(failed_workflows)
        for x in imported_workflows:
            print(x)
        panel = ScrollablePanel(imported_workflows, title="Imported workflows", height=10, width=115)
        panel.auto_scroll(delay=0.07)
        print(f"Successful: {successful_workflows} Failed: {len(failed_workflows)}")
        return


class Users_attributes:

    def __init__(self):
        pass

    def set_user_attributes_code(self, url, token, codes: list):
        """ Set users attributes codes """
        
        headers = {'accept': '*/*', 'Authorization': f"Bearer {token}"}
        if not codes or not isinstance(codes, list):
            return None
        for code in codes:
            try:
                response = _tools.make_request('PUT', f'{url}/api/public/user-attributes/{code}', return_err_response=True, headers=headers, verify=False)
                if response.status_code in range(200, 205):
                    print(f"{code}: attribute applied successfully")
                else:
                    print(f"Error: {response.status_code} - {code}. Check logs: {_logs.filepath}")
            except Exception as err:
                _logger.error(err)
                print(_logs.err_message)
                return None

class Abac:

    def __init__(self):
        pass

    def export_abac_and_events(self, url, token):
        """ Export ABAC files and notifications. """

        pass

    def collect_abac_data(self, **kwargs):
        """ Collect data needed for abac import. """

        data: dict = {}
        for key in kwargs:
            if key and kwargs.get('permissionObjects_file'):
                data.update({'Permission_Objects': {'url': kwargs['url_permission'], 'file': kwargs['permissionObjects_file']}})
            if key and kwargs.get('roles_file'):
                data.update({'Roles': {'url': kwargs['url_roles'], 'file': kwargs['roles_file']}})
            if key and kwargs.get('rolesMapping_file'):
                data.update({'Roles_Mapping': {'url': kwargs['url_roles_mapping'], 'file': kwargs['rolesMapping_file']}})
            if key and kwargs.get('notification_file'):
                data.update({'Notifications': {'url': kwargs['url_events'], 'file': kwargs['notification_file']}})
            if key and kwargs.get('common_file'):
                data.update({'Common': {'url': kwargs['url_common'], 'file': kwargs['common_file']}})
            if key and kwargs.get('auth_file'):
                data.update({'Auth': {'url': kwargs['url_rules'], 'file': kwargs['auth_file']}})
        return data

    def import_abac_and_events(self, token, data: dict, svc_name):
        """ Import data from collect_abac_data function. """

        if not isinstance(data, dict):
            return None
        headers = {'accept': '*/*', 'Authorization': f"Bearer {token}"}
        for key,value in data.items():
            try:
                with open(value['file'], mode='rb') as file:
                    response = _tools.make_request('POST', value['url'], files={'file': file}, return_err_response=True, headers=headers, verify=False)
                    if response.status_code in range(200, 205):
                        print(f"{svc_name}: {key} configuration uploaded successfully")
                    else:
                        print(f"Error: {response.status_code} - {svc_name}. Check logs: {_logs.filepath}")
                        _logger.error(f"HEADERS RECEIVED:\n{response.headers}")
                        _logger.error(f"TEXT:\n{response.text}")
                        _logger.error(f"HEADERS SENT:\n{response.request.headers}")
            except FileNotFoundError as err:
                _logger.error(err)
                print(err)
                return None
            except Exception as err:
                _logger.error(err)
                print(_logs.err_message)
                return None

    def get_parser(self):
        """ Parse user's input arguments. """

        parser = argparse.ArgumentParser(description="Service with method for ABAC files upload to", exit_on_error=False, add_help=False)
        subparser = parser.add_subparsers(dest='command', required=False)

        data_sync_parser = subparser.add_parser('data-sync',  help="Data-synchronizer-api service", add_help=False, exit_on_error=False)
        data_sync_parser.add_argument('-h', '--help', required=False, action="store_true")
        data_sync_parser.add_argument('-po', '--permission-objects', required=False)
        data_sync_parser.add_argument('--roles', required=False)
        data_sync_parser.add_argument('-rmap', '--roles-mapping', required=False)
        data_sync_parser.add_argument('--common', required=False)

        maintenance_parser = subparser.add_parser('maint', add_help=False, exit_on_error=False)
        maintenance_parser.add_argument('-h', '--help', required=False, action="store_true")
        maintenance_parser.add_argument('-po', '--permission-objects', required=False)
        maintenance_parser.add_argument('--roles', required=False)
        maintenance_parser.add_argument('-rmap', '--roles-mapping', required=False)
        maintenance_parser.add_argument('--events', required=False)

        asset_parser = subparser.add_parser('asset', add_help=False, exit_on_error=False)
        asset_parser.add_argument('-h', '--help', required=False, action="store_true")
        asset_parser.add_argument('-po', '--permission-objects', required=False)
        asset_parser.add_argument('--roles', required=False)
        asset_parser.add_argument('-rmap', '--roles-mapping', required=False)
        asset_parser.add_argument('--events', required=False)
        asset_parser.add_argument('--common', required=False)

        work_permits_parser = subparser.add_parser('wpm', add_help=False, exit_on_error=False)
        work_permits_parser.add_argument('-h', '--help', required=False, action="store_true")
        work_permits_parser.add_argument('-po', '--permission-objects', required=False)
        work_permits_parser.add_argument('--roles', required=False)
        work_permits_parser.add_argument('-rmap', '--roles-mapping', required=False)

        fmeca_parser = subparser.add_parser('fmeca', add_help=False, exit_on_error=False)
        fmeca_parser.add_argument('-h', '--help', required=False, action="store_true")
        fmeca_parser.add_argument('-po', '--permission-objects', required=False)
        fmeca_parser.add_argument('--roles', required=False)
        fmeca_parser.add_argument('-rmap', '--roles-mapping', required=False)

        rca_parser = subparser.add_parser('rca', add_help=False, exit_on_error=False)
        rca_parser.add_argument('-h', '--help', required=False, action="store_true")
        rca_parser.add_argument('-po', '--permission-objects', required=False)
        rca_parser.add_argument('--roles', required=False)
        rca_parser.add_argument('-rmap', '--roles-mapping', required=False)

        rbi_parser = subparser.add_parser('rbi', add_help=False, exit_on_error=False)
        rbi_parser.add_argument('-h', '--help', required=False, action="store_true")
        rbi_parser.add_argument('-po', '--permission-objects', required=False)
        rbi_parser.add_argument('--roles', required=False)
        rbi_parser.add_argument('-rmap', '--roles-mapping', required=False)

        rcm_parser = subparser.add_parser('rcm', add_help=False, exit_on_error=False)
        rcm_parser.add_argument('-h', '--help', required=False, action="store_true")
        rcm_parser.add_argument('-po', '--permission-objects', required=False)
        rcm_parser.add_argument('--roles', required=False)
        rcm_parser.add_argument('-rmap', '--roles-mapping', required=False)

        rm_parser = subparser.add_parser('rm', add_help=False, exit_on_error=False)
        rm_parser.add_argument('-h', '--help', required=False, action="store_true")
        rm_parser.add_argument('-po', '--permission-objects', required=False)
        rm_parser.add_argument('--roles', required=False)
        rm_parser.add_argument('-rmap', '--roles-mapping', required=False)

        auth_parser = subparser.add_parser('auth', add_help=False, exit_on_error=False)
        auth_parser.add_argument('-h', '--help', required=False, action="store_true")
        auth_parser.add_argument('--rules', required=False)

        return parser

    def print_help(self, message):
        """ Provide help info for the user. """

        main_msg: str = """usage: abac import [--help] [data-sync] [asset] [maintenance] [--permission-objects <file>] [--roles-mapping <file>] [--roles <file>] [--events <file>]
example: abac import asset --permission-objects permissionObjects.json --roles roles.json data-sync roles.json --roles-mapping rolesMapping.json maintenance --events Events.json

options:
  -h, --help            Show this help message
  data-sync             Data-synchronizer-api service
  asset                 Asset-performance-management service
  maint                 Maintenance-planning service
  wpm                   Work-permits-management service
  fmeca                 Fmeca service
  rcm                   reliability-centered-maintenance service
  rca                   root-cause-analysis service
  rbi                   risk-based-inspections service
  rm                    recommendation-management service
  auth                  auth access rules file
"""
        standart_options: str = """
options:
  -po FILE, --permission-objects FILE
                        file with permission objects configuration
  -rmap FILE, --roles-mapping FILE
                        file with roles mapping configuration
  --roles FILE          file with roles configuration
"""

        data_sync_msg: str = standart_options.rstrip() + """
  --common FILE         file with common configuration
"""
        maintenance_msg: str = standart_options.rstrip() + """
  --events FILE         file with notifications configuration
"""
        asset_msg: str = standart_options.rstrip() + """
  --events FILE         file with notifications configuration
  --common FILE         file with common configuration
"""
        auth_msg: str = """
opions:
  --rules FILE          access rules file
"""
        work_permits_msg: str = standart_options
        fmeca_msg: str = standart_options
        rca_msg: str = standart_options
        rbi_msg: str = standart_options
        rcm_msg: str = standart_options
        rm_msg: str = standart_options

        match message:
            case 'main-msg':
                print(main_msg)
            case 'data-sync-msg':
                print(data_sync_msg)
            case 'asset-msg':
                print(asset_msg)
            case 'maintenance-msg':
                print(maintenance_msg)
            case 'work-permits-msg':
                print(work_permits_msg)
            case 'fmeca-msg':
                print(fmeca_msg)
            case 'rcm-msg':
                print(rcm_msg)
            case 'rca-msg':
                print(rca_msg)
            case 'rbi-msg':
                print(rbi_msg)
            case 'rm-msg':
                print(rm_msg)
            case 'auth-msg':
                print(auth_msg)        


class Mdmconnector:

    export_url = "/mdmconnector-api/v1/AutoSetup/export"
    import_url = "/mdmconnector-api/v1/AutoSetup/file"

    def __init__(self):
        pass

    def check_url(self, url):
        """ Check if there is 'https' in the provided url. """

        url = url[:-1] if url[-1] == '/' else url
        if not url.startswith("http"):
            url = "https://" + url
        else:
            if url[4] != 's':
                url = url[:4] + 's' + url[4:]
        return url

    def import_mdm_config(self, url, file):
        """ Import mdm config file for mdm connector. """

        headers = {'accept': 'text/plain'}
        url = url + self.import_url
        try:
            with open(file, mode='rb') as f:
                response = requests.patch(url=url, files={'file': f}, headers=headers, verify=False)
                if response.status_code in (200, 204):
                    _logger.debug(f"{url}: {response.status_code}")
                    print(f"{file} file uploaded successfully")
                else:
                    _logger.error(response.text)
                    print(f"Error: {response.status_code}. Check logs!")
        except FileNotFoundError as err:
            _logger.error(err)
            print(f"File not found: {file}")
            return False
        except Exception as err:
            _logger.error(err)
            print("Error! Check the log.")
            return False

    def export_mdm_config(self, url):
        """ Import mdm config file for mdm connector. """

        headers = {'accept': 'text/plain'}
        url = url + self.export_url
        try:
            response = requests.patch(url=url, headers=headers, verify=False)
            if response.status_code in (200, 204):
                data = response.json()
                with open("mdm-connector-setup.json", mode='w') as file:
                    file.write(json.dumps(data, indent=2))
                _logger.info(f"{url}: {response.status_code}")
                print(f"Config file 'mdm-connector-setup.json' uploaded successfully")
            else:
                _logger.error(response.text)
                print(f"Error: {response.status_code}. Check logs!")
        except Exception as err:
            _logger.error(err)
            print("Error! Check the log.")
            return False


class RiskAssesment:

    __api_templates: str = "/api/risk-assessment/templates/multi-category-template"

    def __init__(self):
        pass

    def import_risk_assessment_template(self, url, token, filepath):
        """ Import risk assessment template to bimeister. """

        url: str = url + self.__api_templates
        headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}
        if not os.path.isfile(filepath):
            print(f"No such file: {filepath}")
            return False
        with open(filepath, 'r', encoding='utf-8') as file:
            data = json.load(file)
        try:
            response = requests.post(url=url, headers=headers, data=json.dumps(data))
            if response.status_code in (200, 204):
                data = response.json()
                _logger.info(f"{response.text}: {response.status_code}")
                print("Template uploaded successfully!")
            else:
                _logger.error(response)
                print(f"Error: {response.status_code}. Check logs!")
        except Exception as err:
            _logger.error(err)
            print("Error! Check the log.")
            return False