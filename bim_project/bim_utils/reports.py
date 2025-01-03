## DEPRECATED MODULE ##

import requests
from log import Logs
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
disable_warnings(InsecureRequestWarning)
import auth


class Reports:

    __logger                      = Logs().f_logger(__name__)
    __start_connection            = Logs().http_connect()
    __check_response              = Logs().http_response()
    __api_Reports_Template        = "api/Reports/Template"
    possible_request_errors:tuple = auth.Auth().possible_request_errors

    def __init__(self):
        pass


    def __getattr__(self, item):
        raise AttributeError('License class has no such attribute: ' + item)


    def display_reports(self, url, token):
        ''' Display a list of existing reports on a screen. '''

        headers = {'accept': '*/*', 'Content-type':'text/plain', 'Authorization': f"Bearer {token}"}
        try:
            self.__logger.info(self.__start_connection(url))
            response = requests.get(url=f"{url}/{self.__api_Reports_Template}", headers=headers, verify=False)
            self.__logger.debug(self.__check_response(url, response.request.method, response.request.path_url, response.status_code))

        except self.possible_request_errors as err:
            self.__logger.error(err)
            return False

        if not response.status_code == 200:
            return False

        print()
        for obj in response.json():
            print(f"{obj['id']}: {obj['name']}")

  