#
import requests
import mdocker
import mk8s
from prettytable import PrettyTable
from log import Logs
from colorama import init, Fore
init(autoreset=True)



class FeatureToggle:

    _api_GetFeatures: str = 'api/Features/GetFeatures'
    _api_Features: str = 'api/Features'
    __logger = Logs().f_logger(__name__)
    Docker = mdocker.Docker()
    K8s = mk8s.K8S(namespace='bimeister')
    COS = False


    def define_COS(self):
        """ Define which container orchestration system(K8S or Docker) is used. """

        if self.K8s.get_kube_config():
            self.COS: str = "K8S"
            return self.COS
        elif self.Docker.check_docker():
            self.COS: str = "Docker"
            return self.COS
        else:
            self.__logger.debug("No K8S or Docker has been found on localhost. As well as no connection to the API's could be established.")
            return False

    def get_features(self, url, FeatureAccessToken):
        """ Get list of features. """

        headers = {'FeatureToggleAuthorization': f'FeatureAccessToken {FeatureAccessToken}' }
        request = requests.get(url=f"{url}/{self._api_GetFeatures}", headers=headers, verify=False)

        if request.status_code == 200:
            self.__logger.info(f"{self._api_GetFeatures} {request}")
            response: dict = request.json()
            ft_list: list = [ft for ft in response]
        else:
            print(f"Error {request.status_code} occurred during GetFeatures request. Check the logs.")
            self.__logger.error(request.text)
            return False

        return ft_list

    def display_features(self, url, FeatureAccessToken):
        """ Display list of features in pretty table. """

        headers = {'FeatureToggleAuthorization': f'FeatureAccessToken {FeatureAccessToken}' }
        request = requests.get(url=f"{url}/{self._api_GetFeatures}", headers=headers, verify=False)

        table = PrettyTable()
        table.field_names = ['FEATURE', 'STATUS']
        table.align = 'l'
        if request.status_code == 200:
            self.__logger.info(f"{self._api_GetFeatures} {request}")
            response: dict = request.json()
            print()
            for key,value in sorted(response.items()):
                # print(" {0}:  {1}".format(k.capitalize(), v))
                table.add_row([key.capitalize(), Fore.GREEN + str(value) + Fore.RESET if value else Fore.RED + str(value) + Fore.RESET])
        else:
            print(f"Error {request.status_code} occurred during GetFeatures request. Check the logs.")
            self.__logger.error(request.text)
            return False
        print(table)

    def set_feature(self, url, features: list, bearerToken, FeatureAccessToken, is_enabled=True):
        """ Function to enable/disable FT. """

        ft_list = self.get_features(url, FeatureAccessToken)
        headers = {'FeatureToggleAuthorization': f'FeatureAccessToken {FeatureAccessToken}', 'Authorization': f'Bearer {bearerToken}', 'accept': '*/*', 'Content-type':'application/json; charset=utf-8'}
        json_data = is_enabled
        for feature in features:
            if feature.lower() not in ft_list:
                print(f"Incorrect FT name: {feature}")
                continue
            request = requests.put(url=f'{url}/{self._api_Features}/{feature}', json=json_data, headers=headers, verify=False)
            if request.status_code in (200, 201, 204):
                self.__logger.info(f"{url}/{self._api_Features}/{feature} {request}")
                print("Result: {0} {1} successfully.".format(feature, 'enabled' if is_enabled else 'disabled'))
            else:
                self.__logger.error(request.status_code, '\n', request.text)
                print(f"Result: {feature} wasn't enabled. Check the log. Error: {request.status_code}.")
        return