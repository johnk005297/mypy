import logging
import os
import base64
from tools import Tools

tools = Tools()
logger = logging.getLogger(__name__)


class Passwork:

    api_key: str = os.getenv("PASSWORK_API_KEY")
    url: str = "https://pass.bimeister.io/api/v4"
    url_login: str = "auth/login"
    url_vaults_list: str = "vaults/list"
    url_search_pass_by_url: str = "passwords/searchByUrl"

    def __init__(self):
        self.vaults = Vaults
        self.token = Token
        self.passwords = Passwords
        # pass
    
    @classmethod
    def is_passwork_available(cls):
        """ Check if passwork URL is available. """

        url = cls.url.split('/api')[0]
        response = tools.make_request('HEAD', url, allow_redirects=True, timeout=2)
        return True if response.status_code in range(200, 300) else False


class Token(Passwork):

    def get_token(self):
        """ Fetch session token by API key. """

        url: str = f"{self.url}/{self.url_login}/{self.api_key}"
        headers =  {'Accept': 'application/json'}
        response = tools.make_request('POST', url, headers=headers, verify=False)
        if not response:
            return response
        if response.status_code == 200:
                logger.info(f"{self.__class__} {self.get_token.__name__}: {response.status_code}")
                data = response.json()
                return data['data']['token']


class Vaults(Passwork):

    def get_vaults(self, token):
        """ Get list of vaults from passwork. """

        if not token:
            return False
        url: str = f"{self.url}/{self.url_vaults_list}"
        headers = {
            "Accept": "application/json",
            "Passwork-Auth": token
        }
        response = tools.make_request('GET', url, headers=headers, verify=False)
        if not response:
            return False
        data = response.json()
        return data

    def get_impl_vault_id(self):
        """ Get 'IMPL' vault Id from the passwork. """

        data = self.get_vaults()
        impl_vault_id: int = 0
        for dict in data['data']:
            for value in dict.values():
                if value == 'IMPL':
                    impl_vault_id = dict['id']
                    break
            if impl_vault_id:
                break
        return impl_vault_id


class Passwords(Passwork):

    def search_passwords_by_url(self, search_url, token) -> list:
        """ Get a password(s) from the vault. """

        url = f"{self.url}/{self.url_search_pass_by_url}"
        try:
            if not search_url:
                print("Error: no URL was provided.")
                return None
            if search_url.startswith('http'):
                search_url = search_url.split('://')[1]
        except IndexError as err:
            logger.error(err)
            print("Error: incorrect URL provided.")
            return None
        except AttributeError as err:
            logger.error(err)
            print(f"Error: {err}")
            return None
        headers = {
            "Accept": "application/json",
            "Passwork-Auth": token,
            "Content-Type": "application/json"
        }
        payload = {"url": search_url}
        response = tools.make_request('POST', url, headers=headers, json=payload, verify=False)
        passwords: list = []
        if not response:
            return response
        if response.status_code == 200:
            data = response.json()
            if not data['data']:
                return None
            for pw in data['data']:
                passwords.append({'id': pw['id'], 'name': pw['name'], 'url': pw['url']})
            return passwords

    def get_credentials(self, id_list, token):
        """ Function takes a list of Ids, and returns a list of dictionarie(s) with 'login' and 'password' from the Passwork.
        Example: [{'John': 'password123'}, {'Kate': 'Qwerty123'}]
        """

        headers = {
            "Accept": "application/json",
            "Passwork-Auth": token
        }
        creds: list = []
        for id in id_list:
            url = f"{self.url}/passwords/{id}"
            response = tools.make_request('GET', url, headers=headers, verify=False)
            if not response:
                return None
            data = response.json()
            password = data['data']['cryptedPassword'].encode('utf-8')
            password = base64.b64decode(password)
            password = password.decode('utf-8')
            # Check if the key-value pair exists in any dictionary
            found: bool = any(d.get(data['data']['login']) == password for d in creds)
            if not found:
                creds.append({data['data']['login']: password})

        # Convert each dictionary to a frozenset of items, ensuring hashable representation
        # and removing duplicate login/passwords from the credentials list
        # creds = [dict(d) for d in {frozenset(d.items()) for d in creds}]
        return creds
        
