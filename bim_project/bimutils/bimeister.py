import logging
import requests
import json
import argparse

import mlogger
from tools import Tools

_logs = mlogger.Logs()
_logs.set_full_access_to_log_file(_logs.filepath, 0o666)
_logger = mlogger.file_logger(_logs.filepath, logLevel=logging.INFO)
_tools = Tools()



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
                _logger.info(f"{url} | {response.status_code}")
                print("Files uploaded successfully.")
    except FileNotFoundError as err:
        _logger.error(err)
        print(err)
    except requests.RequestException as err:
        _logger.error(err)
        print(_logs.err_message)
    except Exception as err:
        _logger.error(err)
        print(_logs.err_message)

def print_bim_version(url: str) -> bool:
    """ Get bimeister commit version. """

    if not url.startswith('http'):
        url = 'https://' + url
    url = url[:-len('/products')] if url.endswith('/products') else url
    url = url[:-len('/auth')] if url.endswith('/auth') else url
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
            _logger.error(err)
            if count > 0:
                print("Connection error: Check URL address.")
                return False
        except json.JSONDecodeError as err:
            print("JSONDecodeError: Check URL address.")
            _logger.error(err)
            return False
        except requests.exceptions.MissingSchema as err:
            print(f"Invalid URL. MissingSchema.")
            _logger.error(err)
            return False
        except Exception as err:
            _logger.error(err)
            print(_logs.err_message)
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
        _logger.error(err)
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
            _logger.info(f"{url} {response.status_code}")
            print("Paths recalculated successfully!")
        return True
    except Exception as err:
        _logger.error(err)
        print(_logs.err_message)
        return False

def get_list_of_templates(url, token) -> list:
    """ Get list of templates from reports service. """

    url = url + '/api/Templates'
    headers = {'Content-Type': 'application/json', 'Authorization': f"Bearer {token}"}
    try:
        response = requests.get(url=url, headers=headers, verify=False)
        response.raise_for_status()
        if response.status_code == 200:
            _logger.info(f"{url} {response.status_code}")
            data = response.json()
            return data
    except Exception as err:
        print(err)
        return False

def print_list_of_templates(templates: list):
    """ Function prints the list of provided templates. """

    if not templates:
        print("No data was provided.")
        return False
    count = Tools.counter()
    for template in templates:
        print(f"{count()})Name: {template['name']}  Id: {template['id']}  TypeName: {template['typeName']}")

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
                _logger.error(err)
                print(f"404 Client Error for id: {i}")
        except Exception as err:
            _logger.error(err)
            print(_logs.err_message)
            return False

def basic_auth(url, token, username, password, set=False):
    """ Check basic auth for a given user. """

    if not url or not token or not username or not password:
        return None
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json-patch+json',
        'Authorization': f'Bearer {token}',
        'X-Swagger-Cluster-Id': 'auth'
        }
    data: dict = {
        "name": username,
        "password": password
    }
    if set:
        url: str = f"{url}/api/Users/set-user-basic-auth"
    else:
        url: str = f"{url}/api/Users/check-user-basic-auth"
    try:
        response = Tools.make_request('POST', url, json=data, return_err_response=True, headers=headers, verify=False)
        if response.status_code in range(200, 205):
            print(f"Username: {username}\nStatus: True")
        else:
            print(f"Username: {username}\nStatus: False")
    except Exception as err:
        _logger.error(err)
        print(_logs.err_message)
        return None

def import_activity_collector(url: str, token: str, x_imui_key: str ="ce090efa0262d185e3ea3b12c9565d66f6d30e06", filepath: str = None) -> requests.Response:
    """ Import  activity collector configuration file to bimeister. """

    if not url or not token or not filepath:
        print("No url, token or file were provided.")
        return None
    headers = {
        'accept': '*/*',
        'X-IMUI-Key': x_imui_key,
        'Authorization': f'Bearer {token}'
        }
    url: str = f"{url.rstrip('/')}/api/activity-collector/configuration/tasks/upload"
    try:
        with open(filepath, mode='rb') as file:
            response = Tools.make_request('POST', url, headers=headers, files={'file': file}, verify=False, return_err_response=True)
            if response.status_code in range(200, 205):
                print("Configuration uploaded successfully.")
            else:
                _logger.error(response.text)
                print(_logs.err_message)
    except FileNotFoundError as err:
        print(err)
        return None
    except Exception as err:
        _logger.error(err)
        print(_logs.err_message)
        return None

def export_activity_collector(url: str, token: str) -> requests.Response:
    """ Import  activity collector configuration file to bimeister. """

    if not url or not token:
        _logger.error("No url or token were provided.")
        return None
    headers = {
        'accept': '*/*',
        'Authorization': f'Bearer {token}'
        }
    url: str = f"{url.rstrip('/')}/api/activity-collector/configuration/tasks/download"
    try:
        response = _tools.make_request('GET', url, headers=headers, verify=False, return_err_response=True)
        if response.status_code in range(200, 205):
            data: dict = response.json()
            filename: str = 'ActivityCollectorConfiguration.json'
            with open(filename, mode='w', encoding='utf-8') as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
            print(f"Configuration file downloaded: {filename}")
        else:
            _logger.error(response.text)
            print(_logs.err_message)
    except Exception as err:
        _logger.error(err)
        print(_logs.err_message)
        return None


class Abac:

    def __init__(self):
        pass

    def collect_abac_data_export(self, **kwargs):
        """ Collect data needed for abac export. """

        data: dict = {}
        for key in kwargs:
            if key and kwargs.get('all'):
                break
            if key and kwargs.get('permission_objects'):
                data.update({'Permission_Objects': kwargs['url_permission']})
            if key and kwargs.get('roles'):
                data.update({'Roles': kwargs['url_roles']})
            if key and kwargs.get('roles_mapping'):
                data.update({'Roles_Mapping': kwargs['url_roles_mapping']})
            if key and kwargs.get('notification'):
                data.update({'Notifications': kwargs['url_events']})
            if key and kwargs.get('common'):
                data.update({'Common': kwargs['url_common']})
        return data

    def export_abac_and_events(self, token: str, data: dict, svc_name: str):
        """ Export ABAC files and notifications. """

        if not token:
            _logger.error("No token was provided.")
            return None
        if not isinstance(data, dict):
            return None
        headers = {'accept': '*/*', 'Authorization': f"Bearer {token}"}
        for object_name, url in data.items():
            try:
                if object_name == "Rules":
                    response = _tools.make_request('POST', url, return_err_response=True, headers=headers, verify=False)
                else:
                    response = _tools.make_request('GET', url, return_err_response=True, headers=headers, verify=False)
                if response.status_code in range(200, 205):
                    data: dict = response.json()
                    with open(f"{svc_name}_{object_name}.json", mode="w", encoding="utf-8") as file:
                        json.dump(data, file, indent=2, ensure_ascii=False)
                    print(f"{svc_name}: {object_name} configuration downloaded successfully")
                else:
                    print(f"Error: {response.status_code} - {svc_name}. Check logs: {_logs.filepath}")
                    _logger.error(f"{response.text}")
            except Exception as err:
                _logger.error(err)
                print(_logs.err_message)
                return None

    def get_auth_parser(self):
        """ Parse user's input arguments. """

        parser = argparse.ArgumentParser(prog='auth', description="Service with methods for operations with Auth", exit_on_error=False)
        subparser = parser.add_subparsers(dest='command', required=False)

        rules_parser = subparser.add_parser('rules', aliases=['rule'], exit_on_error=False)
        rules_parser.add_argument('--export', dest="export_rule", action="store_true", required=False, help='Export auth access rules .json file')
        rules_parser.add_argument('--import', dest="import_rule", action="store_true", required=False, help='Import auth access rules .json file')

        modules_parser = subparser.add_parser('modules', aliases=['module'], exit_on_error=False)
        modules_parser.add_argument('--get', required=False, action="store_true", help='Print AbacRules modules.')
        modules_parser.add_argument('--set', required=False, action='append', type=str, help='Set AbacRules modules. Flag requires value to set.')

        return parser

    def export_auth_rules(self, token: str, url: str):
        """ Export auth access rules .json file. """

        if not token:
            _logger.error("No token was provided.")
            return None
        headers = {'accept': '*/*', 'Authorization': f"Bearer {token}"}
        filename: str = "auth_Rules.json"
        url += '/api/abac/rules/export'
        try:
            response = _tools.make_request('POST', url, return_err_response=True, headers=headers, verify=False)
            data: dict = response.json()
            with open(filename, mode="w", encoding="utf-8") as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
            print(f"Abac rules exported successfully: {filename}")
        except Exception as err:
            _logger.error(err)
            print(_logs.err_message)
            return None

    def import_auth_rules(self, token: str, url: str, filepath: str):
        """ Import auth access rules .json file. """

        if not token:
            _logger.error("No token was provided.")
            return None
        headers = {'accept': '*/*', 'Authorization': f"Bearer {token}"}
        url += '/api/abac/rules/import'
        try:
            with open(filepath, mode='rb') as file:
                response = _tools.make_request('POST', url, files={'file': file}, return_err_response=True, headers=headers, verify=False)
                if response.status_code in range(200, 205):
                    print(f"{filepath} imported successfully.")
                else:
                    print(_logs.err_message)
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

    def print_abac_allowed_modules(self, token: str, url: str):
        """ Print available AbacRules modules. """

        if not token:
            _logger.error("No token was provided.")
            return None
        headers = {'accept': '*/*', 'Authorization': f"Bearer {token}"}
        url += '/api/abac/rules/allowed-modules'
        try:
            response = _tools.make_request('GET', url, return_err_response=True, headers=headers, verify=False)
            print(response.json())
        except Exception as err:
            _logger.error(err)
            print(_logs.err_message)
            return None

    def set_abac_allowed_modules(self, token: str, url: str, modules: list):
        """ Print available AbacRules modules. """

        if not token:
            _logger.error("No token was provided.")
            return None
        headers = {'accept': '*/*', 'Content-Type': 'application/json-patch+json', 'Authorization': f"Bearer {token}"}
        url += '/api/abac/rules/allowed-modules'
        try:
            response = _tools.make_request('PUT', url, data=json.dumps(modules), return_err_response=True, headers=headers, verify=False)
            if response.status_code in range(200, 205):
                print(f"{response.status_code}: OK.")
            else:
                _logger.error(response.text)
                print(_logs.err_message)
        except Exception as err:
            _logger.error(err)
            print(_logs.err_message)
            return None

    def get_parser_export(self):
        """ Parse user's input arguments. """

        parser = argparse.ArgumentParser(description="Service with method for ABAC export files", exit_on_error=False, add_help=False)
        subparser = parser.add_subparsers(dest='command', required=False)

        data_sync_parser = subparser.add_parser('data-sync',  help="Data-synchronizer service", add_help=False, exit_on_error=False)
        data_sync_parser.add_argument('-h', '--help', required=False, action="store_true")
        data_sync_parser.add_argument('-po', '--permission-objects', action="store_true", required=False)
        data_sync_parser.add_argument('--roles', action="store_true", required=False)
        data_sync_parser.add_argument('-rmap', '--roles-mapping', action="store_true", required=False)
        data_sync_parser.add_argument('--common', action="store_true", required=False)
        data_sync_parser.add_argument('--all', action="store_true", required=False)

        maintenance_parser = subparser.add_parser('maint', add_help=False, exit_on_error=False)
        maintenance_parser.add_argument('-h', '--help', required=False, action="store_true")
        maintenance_parser.add_argument('-po', '--permission-objects', action="store_true", required=False)
        maintenance_parser.add_argument('--roles', action="store_true", required=False)
        maintenance_parser.add_argument('-rmap', '--roles-mapping',action="store_true",  required=False)
        maintenance_parser.add_argument('--events', action="store_true", required=False)
        maintenance_parser.add_argument('--all', action="store_true", required=False)

        asset_parser = subparser.add_parser('asset', add_help=False, exit_on_error=False)
        asset_parser.add_argument('-h', '--help', required=False, action="store_true")
        asset_parser.add_argument('-po', '--permission-objects', action="store_true", required=False)
        asset_parser.add_argument('--roles', action="store_true", required=False)
        asset_parser.add_argument('-rmap', '--roles-mapping', action="store_true", required=False)
        asset_parser.add_argument('--events', action="store_true", required=False)
        asset_parser.add_argument('--common', action="store_true", required=False)
        asset_parser.add_argument('--all', action="store_true", required=False)

        work_permits_parser = subparser.add_parser('wpm', add_help=False, exit_on_error=False)
        work_permits_parser.add_argument('-h', '--help', required=False, action="store_true")
        work_permits_parser.add_argument('-po', '--permission-objects', action="store_true", required=False)
        work_permits_parser.add_argument('--roles', action="store_true", required=False)
        work_permits_parser.add_argument('-rmap', '--roles-mapping', action="store_true", required=False)
        work_permits_parser.add_argument('--all', action="store_true", required=False)

        fmeca_parser = subparser.add_parser('fmeca', add_help=False, exit_on_error=False)
        fmeca_parser.add_argument('-h', '--help', required=False, action="store_true")
        fmeca_parser.add_argument('-po', '--permission-objects', action="store_true", required=False)
        fmeca_parser.add_argument('--roles', action="store_true", required=False)
        fmeca_parser.add_argument('-rmap', '--roles-mapping', action="store_true", required=False)
        fmeca_parser.add_argument('--all', action="store_true", required=False)

        rca_parser = subparser.add_parser('rca', add_help=False, exit_on_error=False)
        rca_parser.add_argument('-h', '--help', required=False, action="store_true")
        rca_parser.add_argument('-po', '--permission-objects', action="store_true", required=False)
        rca_parser.add_argument('--roles', action="store_true", required=False)
        rca_parser.add_argument('-rmap', '--roles-mapping', action="store_true", required=False)
        rca_parser.add_argument('--all', action="store_true", required=False)

        rbi_parser = subparser.add_parser('rbi', add_help=False, exit_on_error=False)
        rbi_parser.add_argument('-h', '--help', required=False, action="store_true")
        rbi_parser.add_argument('-po', '--permission-objects', action="store_true", required=False)
        rbi_parser.add_argument('--roles', action="store_true", required=False)
        rbi_parser.add_argument('-rmap', '--roles-mapping', action="store_true", required=False)
        rbi_parser.add_argument('--all', action="store_true", required=False)

        rcm_parser = subparser.add_parser('rcm', add_help=False, exit_on_error=False)
        rcm_parser.add_argument('-h', '--help', required=False, action="store_true")
        rcm_parser.add_argument('-po', '--permission-objects', action="store_true", required=False)
        rcm_parser.add_argument('--roles', action="store_true", required=False)
        rcm_parser.add_argument('-rmap', '--roles-mapping', action="store_true", required=False)
        rcm_parser.add_argument('--all', action="store_true", required=False)

        rm_parser = subparser.add_parser('rm', add_help=False, exit_on_error=False)
        rm_parser.add_argument('-h', '--help', required=False, action="store_true")
        rm_parser.add_argument('-po', '--permission-objects', action="store_true", required=False)
        rm_parser.add_argument('--roles', action="store_true", required=False)
        rm_parser.add_argument('-rmap', '--roles-mapping', action="store_true", required=False)
        rm_parser.add_argument('--all', action="store_true", required=False)


        return parser

    def collect_abac_data_import(self, **kwargs):
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

    def import_abac_and_events(self, token: str, data: dict, svc_name: str):
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

    def get_parser_import(self):
        """ Parse user's input arguments. """

        parser = argparse.ArgumentParser(description="Service with method for ABAC files upload to", exit_on_error=False, add_help=False)
        subparser = parser.add_subparsers(dest='command', required=False)

        data_sync_parser = subparser.add_parser('data-sync',  help="Data-synchronizer service", add_help=False, exit_on_error=False)
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

    def print_abac_help_import(self, message):
        """ Provide help info for the user. """

        main_msg: str = """usage: abac import [--help] [data-sync] [asset] [maintenance] [--permission-objects <file>] [--roles-mapping <file>] [--roles <file>] [--events <file>]
example: abac import asset --permission-objects permissionObjects.json --roles roles.json data-sync roles.json --roles-mapping rolesMapping.json maintenance --events Events.json

options:
  -h, --help            Show this help message
  data-sync             Data-synchronizer service
  asset                 Asset-performance-management service
  maint                 Maintenance-planning service
  wpm                   Work-permits-management service
  fmeca                 Fmeca service
  rcm                   reliability-centered-maintenance service
  rca                   root-cause-analysis service
  rbi                   risk-based-inspections service
  rm                    recommendation-management service
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

    def print_abac_help_export(self, message):
        """ Provide help info for the user. """

        main_msg: str = """usage: abac export [--help] [data-sync|asset|maintenance] [--permission-objects] [--roles-mapping] [--roles] [--events] [--all]
example: abac export asset --permission-objects --roles data-sync--roles-mapping maintenance --events
         abac export asset --all

options:
  -h, --help            Show this help message
  data-sync             Data-synchronizer service
  asset                 Asset-performance-management service
  maint                 Maintenance-planning service
  wpm                   Work-permits-management service
  fmeca                 Fmeca service
  rcm                   reliability-centered-maintenance service
  rca                   root-cause-analysis service
  rbi                   risk-based-inspections service
  rm                    recommendation-management service
"""
        standart_options: str = """
options:
  -po, --permission-objects
  -rmap, --roles-mapping
  --roles
  --all
"""

        data_sync_msg: str = standart_options.rstrip() + """
  --common         common configuration
"""
        maintenance_msg: str = standart_options.rstrip() + """
  --events         notifications configuration
"""
        asset_msg: str = standart_options.rstrip() + """
  --events         notifications configuration
  --common         common configuration
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