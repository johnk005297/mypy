#
import requests
from prettytable import PrettyTable
from colorama import init, Fore
init(autoreset=True)


class FeatureToggle:

    _api_GetFeatures:str = 'api/Features/GetFeatures'
    _api_Features:str    = 'api/Features'


    def ft_menu(self):
        ''' Menu of FT options. '''

        menu:str = "Feature Toggle                                                                                                                   \
            \n        [docker/kube] ft [feature toggle name] --[on/off]                                                                              \
            \n          usage:                                                                                                                       \
            \n            kube ft spatium --on                                                                                                       \
            \n            docker ft spatium --off                                                                                                    \
            \n                                                                                                                                       \
            \n        [docker/kube] ft --list                                 display the list of features                                           \
            \n                                                                                                                                       \
            \n   Main                                                                                                                                \
            \n      q                                                 exit"


    def display_features(self, url, FeatureAccessToken):
        ''' Get list of features. '''

        headers = {'FeatureToggleAuthorization': f'FeatureAccessToken {FeatureAccessToken}' }
        request = requests.get(url=f"{url}/{self._api_GetFeatures}", headers=headers, verify=False)

        table = PrettyTable()
        table.field_names = ['FEATURE', 'STATUS']
        table.align = 'l'
        if request.status_code == 200:
            response:dict = request.json()
            print()
            for key,value in sorted(response.items()):
                # print(" {0}:  {1}".format(k.capitalize(), v))
                table.add_row([key.capitalize(), Fore.GREEN + str(value) + Fore.RESET if value else Fore.RED + str(value) + Fore.RESET])
        else:
            print(f"Error {request.status_code} occurred during GetFeatures request. Check the logs.")
            # logging.error(request.text)
            return False
        print(table)


    def set_feature(self, url, feature, bearerToken, FeatureAccessToken, is_enabled=True):
        ''' Function to enable/disable FT. '''

        headers = {'FeatureToggleAuthorization': f'FeatureAccessToken {FeatureAccessToken}', 'Authorization': f'Bearer {bearerToken}', 'accept': '*/*', 'Content-type':'application/json; charset=utf-8'}
        json_data = is_enabled
        result:str = 'enabled' if is_enabled else 'disabled'

        request = requests.put(url=f'{url}/{self._api_Features}/{feature}', json=json_data, headers=headers, verify=False)
        
        if request.status_code in (200, 201, 204):
            print(f"Result: {feature} {result} successfully.")
            return True
        else:
            # logging.error(request.status_code, '\n', request.text)
            print(f"Result: {feature} wasn't enabled. Check the log. Error: {request.status_code}.")
            return False