import requests
import os
import sys
from tools import Tools
from log import Logs

# block for correct build with pyinstaller, to add .env file
from dotenv import load_dotenv
extDataDir = os.getcwd()
if getattr(sys, 'frozen', False):
    extDataDir = sys._MEIPASS
load_dotenv(dotenv_path=os.path.join(extDataDir, '.env'))

logger = Logs().f_logger(__name__)

class Passwork:

    api_key: str = os.getenv("passwork_api_key")
    api_url: str = "https://pass.bimeister.io/api/v4"

    def get_token(self):
        """ Fetch session token by API key. """

        url: str = f"{self.api_url}/auth/login/{self.api_key}"
        headers =  {'Accept': 'application/json'}
        try:
            response = requests.post(url=url, headers=headers, verify=False)
            if response.status_code == 200:
                logger.info(f"{self.__class__} {self.get_token.__name__}: {response.status_code}")
                data = response.json()
                return data['data']['token']
            elif response.status_code == 401:
                logger.error(response.text)
                print("Error 401: Unauthorized. Please check your authentication credentials.")
                return False
            else:
                logger.error(response.text)
                print(f"Request failed with status code: {response.status_code}. Check the log!")
                return False
        except requests.exceptions.ConnectionError as err:
            logger.error(err)
            print(f"Connection error: {err}")
            return False
        except requests.exceptions.Timeout as err:
            logger.error(err)
            print(f"Timeout error: {err}")
            return False
        except requests.exceptions.RequestException as err:
            logger.error(err)
            print(f"An unexpected request error occurred: {err}")
            return False
        except Exception as err:
            logger.error(err)
            print("Error getting token. Check the log!")
            return False
    
    def get_vaults(self):
        """ Get list of vaults from passwork. """

        token = self.get_token()
        if not token:
            return False
        url: str = f"{self.api_url}/vaults/list"
        headers = {
            "Accept": "application/json",
            "Passwork-Auth": token
        }
        tools = Tools()
        response = tools.make_request('GET', url, headers=headers, verify=False)
        if not response:
            return False
        data = response.json()
        return data
    
    def get_password(self, id):
        """ Get a password from the vault. """

        pass

    
