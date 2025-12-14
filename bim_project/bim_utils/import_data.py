import logging
import os
import argparse
import json
import requests
import time
# import export_data
import auth
from license import License
from tools import File, Tools
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
disable_warnings(InsecureRequestWarning)
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

    def post_object_model(self, url, token, filepath):

        headers = {'accept': '*/*', 'Content-type':'application/json', 'Authorization': f"Bearer {token}"}
        url += '/api/Integration/ObjectModel/Import'

        if not os.path.isfile(filepath) or not url or not token:
            return None
        with open(filepath, "r", encoding="utf-8") as file:
            data = file.read()
        # json_payload = json.dumps(data, ensure_ascii=False) # Doesn't work with json.dumps if read from file

        # If the import server object model file is already exists, need to delete it. Case, when user already made attempts to perform import.
        obj_model_file_path: str = f"{self._transfer_folder}/{self._object_model_folder}/{self._object_model_file}"
        if os.path.isfile(obj_model_file_path):
            os.remove(obj_model_file_path)
        response = _tools.make_request('POST', url, data=data.encode("utf-8"),  headers=headers, verify=False, return_err_response=True)
        if response.status_code not in range(200, 205):
            _logger.error(response.text)
            print(f"Status: {response.status_code}. {_logs.err_message}.")
            return False
        else:
            print(f"Status: {response.status_code}. Object model successfully imported.")
            return True

    def import_object_model(self, url, token):
        pass
        # server_validation: bool = self.validate_import_server(url, token)
        object_model_file_exists: bool = os.path.isfile(f'{self._transfer_folder}/{self.Export_data._object_model_folder}/{self.Export_data._object_model_file}')
        # if object_model_file_exists and server_validation:
            # Check if the import server object model file is already exists. Need to delete it. Case, when user already made attempts to make import.
            # In order to avoid message about the file is already there from Export_data.get_object_model function, need to remove it first.
            # if os.path.isfile(f'{self._transfer_folder}/{self._object_model_folder}/{self._object_model_file}'):
                # os.remove(f'{self._transfer_folder}/{self._object_model_folder}/{self._object_model_file}')
            # self.Export_data.get_object_model(self._object_model_file, url, token)
            # self.prepare_object_model_file_for_import()
            # self.fix_defaulValues_in_object_model()
        #     self.post_object_model(url, token)
        #     return True
        # else:
        #     print("No object_model for import." if not os.path.isfile(f'{self._transfer_folder}/{self.Export_data._object_model_folder}/{self.Export_data._object_model_file}') else "")
        #     return False


class Workflows:
    pass

class Import_data:

    __api_WorkFlows: str = 'api/WorkFlows'
    __api_Integration_ObjectModel_Import: str = 'api/Integration/ObjectModel/Import'
    __api_Integration_WorkFlow_Import: str = 'api/Integration/WorkFlow/Import'
    _transfer_folder: str = 'transfer_files'
    _workflows_folder: str = 'workflows'
    _all_workflow_nodes_file: str = 'all_workflow_nodes_import_server.json'
    _object_model_folder: str = 'object_model'
    _object_model_file: str = 'object_model_import_server.json'
    _modified_object_model_file: str = 'modified_object_model.json'
    # Export_data = export_data.Export_data()
    # License = license.License()
    possible_request_errors = auth.Auth().possible_request_errors

    def __init__(self):
        self.export_serverId = None

    def post_workflows(self, url, token):
        ''' Function to post workflows using .zip archives data from the export procedure.
            Workflows IDs' are taken from exported_workflows.list file.
        '''

        url_import = f'{url}/{self.__api_Integration_WorkFlow_Import}'
        headers = {'accept': '*/*', 'Authorization': f"Bearer {token}"}

        # Read the file with workflows in the list without blank lines
        workflows = [x for x in File.read_file(f'{self._transfer_folder}/{self._workflows_folder}/{self.Export_data._exported_workflows_list}',).split('\n') if x.split()]
        count = Tools.counter()
        for workflow in workflows:
            # workflow format: <status>  <id>  <name>
            id = workflow.split(' '*2, maxsplit=2)[1].strip()
            name = workflow.split(' '*2, maxsplit=2)[2].strip()
            try:
                with open(f'{self._transfer_folder}/{self._workflows_folder}/{id}.zip', mode='rb') as file:
                    response = requests.post(url=url_import, headers=headers, files={'file': file}, verify=False)
                    time.sleep(0.1)
                    if response.status_code != 200:
                        print(f"  {count()}) ERROR {response.status_code} >>> {name}, id: {id}.")
                        _logger.error(response.text)
                        continue

                    _logger.debug(f'{response.request.method} "{name}: {id}" {response.status_code}')
                    print(f"   {count()}) {name}.")   # display the name of the process in the output
            except FileNotFoundError:
                print(f"Process not found: {name}")
                continue
            except:
                _logger.error()
                continue
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