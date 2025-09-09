import logging
import requests
from rich.console import Console
from rich.table import Table
from tools import Tools

_logger = logging.getLogger(__name__)

class FeatureToggle:

    _api_GetFeatures: str = 'api/Features/GetFeatures'
    _api_Features: str = 'api/Features'
    headers = {'accept': '*/*', 'Content-type': 'application/json; charset=utf-8'}

    def display_features(self, url, enabled=False, disabled=False):
        """ Display list of features in pretty table. """

        try:
            response = requests.get(url=f"{url}/{self._api_GetFeatures}", headers=self.headers, verify=False)
        except Exception as err:
            _logger.error(err)
            print("Error! Couldn't get list of features. Check the logs.")
            return False
        table = Table()
        table.add_column("No.", style="cyan", no_wrap=True)
        table.add_column("Feature", style="magenta")
        table.add_column("Status", justify="center", highlight=False)
        count = Tools.counter()
        if response.status_code == 200:
            _logger.info(f"{self._api_GetFeatures} {response}")
            data: dict = response.json()
            print()
            for key,value in sorted(data.items()):
                if enabled and value:
                    table.add_row(str(count()), key.capitalize(), "[green]on[/green]")
                elif disabled and not value:
                    table.add_row(str(count()), key.capitalize(), "[red]off[/red]")
                elif not enabled and not disabled:
                    table.add_row(str(count()), key.capitalize(), "[green]on[/green]" if value else "[red]off[/red]")
        else:
            print(f"Error {response.status_code} occurred during GetFeatures request. Check the logs.")
            _logger.error(response.text)
            return False
        console = Console()
        console.print(table)

    def get_list_of_features(self, url):
        """ Get list of features. """

        try:
            response = requests.get(url=f"{url}/{self._api_GetFeatures}", headers=self.headers, verify=False)
        except Exception as err:
            _logger.error(err)
            print("Error! Couldn't get list of features. Check the logs.")
            return False
        if response.status_code == 200:
            _logger.info(f"{self._api_GetFeatures} {response}")
            data: dict = response.json()
            ft_list: list = [ft for ft in data]
        else:
            print(f"Error {response.status_code} occurred during GetFeatures request. Check the logs.")
            _logger.error(response.text)
            return False
        return ft_list

    def set_feature(self, url, bearerToken, features: list, is_enabled=True):
        """ Function to enable/disable FT. """

        ft_list = self.get_list_of_features(url)
        headers = {'Authorization': f'Bearer {bearerToken}', 'accept': '*/*', 'Content-type':'application/json; charset=utf-8'}
        json_data = is_enabled
        for feature in features:
            if feature.lower() not in ft_list:
                print(f"Incorrect FT name: {feature}")
                continue
            response = requests.put(url=f'{url}/{self._api_Features}/{feature}', json=json_data, headers=headers, verify=False)
            if response.status_code in (200, 201, 204):
                _logger.info(f"{url}/{self._api_Features}/{feature} {response}")
                response = requests.get(url=f'{url}/{self._api_Features}/{feature}', json=json_data, headers=headers, verify=False)
                ft_enabled: bool = response.json()
                print("{0}: {1}".format(feature, 'enabled' if ft_enabled else 'disabled'))
            else:
                _logger.error(response.status_code, '\n', response.text)
                print(f"{feature} wasn't enabled. Check the log. Error: {response.status_code}.")
        return
