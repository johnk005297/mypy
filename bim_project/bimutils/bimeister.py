import logging
import requests
import json

import mlogger
from tools import Tools

_logs = mlogger.Logs()
_logs.set_full_access_to_log_file(_logs.filepath, 0o666)
_logger = mlogger.file_logger(_logs.filepath, logLevel=logging.INFO)


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

    @staticmethod
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

    @staticmethod
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
                    _logger.error(err)
                    print(f"404 Client Error for id: {i}")
            except Exception as err:
                _logger.error(err)
                print(_logs.err_message)
                return False

    @staticmethod
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
