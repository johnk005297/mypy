#
from kubernetes.client.rest import ApiException
from kubernetes import client, config
from kubernetes.stream import stream
from tools import Tools, File
import json
import base64
import requests
# import logging
import os


class K8S:

    _api_GetFeatures:str                        = 'api/Features/GetFeatures'
    _api_enterpriseassetmanagementisenabled:str = 'api/Features/enterpriseassetmanagementisenabled'
    _api_documentworkflowtasksreport:str        = 'api/Features/documentworkflowtasksreport'
    _api_testfeature:str                        = 'api/Features/testfeature'
    _api_maintenanceplanning:str                = 'api/Features/maintenanceplanning'
    _api_graphdbstorage:str                     = 'api/Features/graphdbstorage'
    _api_spatium:str                            = 'api/Features/spatium'
    _api_constructioncontrol:str                = 'api/Features/constructioncontrol'

    
    def __init__(self, namespace='bimeister'):
        self.namespace        = namespace
        # self.v1               = self.get_CoreV1Api()  # this line does not work.
        try:
            config.load_kube_config()
            self._check_k8s:bool = True
        except config.ConfigException as config_err:
            self._check_k8s:bool = False
            # logging.error(config_err)
        except ApiException as client_api_err:
            self._check_k8s:bool = False
            # logging.error(client_api_err)
        except:
            self._check_k8s:bool = False


    def k8s_menu(self):
        ''' Appearance of docker commands menu. '''

        _k8s_menu = "Kubernets options:                                                                  \
                          \n                                                                             \
                          \n   Feature toggle                                                            \
                          \n      kube get ft                        display list of features            \
                          \n      kube spatium ft     --enable       enable spatium feature toggle       \
                          \n      kube spatium ft     --disable      disable spatium feature toggle      \
                          \n      kube enterprise ft  --enable       enable enterprise feature toggle    \
                          \n      kube enterprise ft  --disable      disable enterprise feature toggle   \
                          \n      kube maintenance ft --enable       enable maintenance feature toggle   \
                          \n      kube maintenance ft --disable      disable maintenance feature toggle  \
                          \n                                                                             \
                          \n   Main                                                                      \
                          \n      q                                  exit"


        return _k8s_menu


    def get_CoreV1Api(self):
        
        try:
            v1 = client.CoreV1Api()
        except ApiException as err:
            # logging.error(err)
            print("Error occured. Check the logs.")
            return False
        return v1
        

    def get_ft_pod(self):
        ''' Get feature toggle pod. In current version we are checking for redis or keydb.'''

        v1 = self.get_CoreV1Api()
        pods = v1.list_pod_for_all_namespaces(watch=False)

        possible_ft_pods:list = ['redis', 'keydb']
        count = Tools.counter()
        for item in pods.items:
            count()
            # if item.metadata.namespace == self.namespace and (item.spec.containers[0].name == 'redis' or item.spec.containers[0].name == 'keydb') and item.status.phase == 'Running':
            if item.metadata.namespace == self.namespace and item.spec.containers[0].name in possible_ft_pods and item.status.phase == 'Running':
                ft_pod:str = item.metadata.name
                return ft_pod
            elif count() == len(pods.items):
                print("No feature toggle pod was found. Check for needed pod.")        
        return False


    def get_ft_secret_pass(self, secret_name):
        ''' Get password from the k8s secret of the pod. '''

        v1 = self.get_CoreV1Api()
        try:
            secret:dict = v1.read_namespaced_secret(secret_name, self.namespace).data
        except ApiException as err:
            # logging.error(err)
            return False

        passwd = base64.b64decode(list(secret.values())[0]).decode('utf-8')
        return passwd if passwd else False


    def get_ft_secret(self):
        ''' Get a list of all secrets in the cluster. '''


        v1 = self.get_CoreV1Api()
        secrets_list:list = v1.list_namespaced_secret(self.namespace).items  # Getting a list of all the secrets

        # Getting a needed secret for FT activation
        possible_ft_secrets:list = ['{}-redis'.format(self.namespace), '{}-keydb'.format(self.namespace)]
        count = Tools.counter()
        for item in secrets_list:
            count()
            # if item.metadata.name == self.namespace + '-' + 'redis':
            if item.metadata.name in possible_ft_secrets:
                return item.metadata.name
            elif count() == len(secrets_list):
                return False


    def get_ft_token(self):
        ''' Function get's FT token into token variable. During process it creates tmp file after kubectl command, read token from the file into var, and delete the file. '''
        
        ft_pod = self.get_ft_pod()
        ft_secret = self.get_ft_secret()

        if ft_pod and ft_secret:
            ft_secret_pass = self.get_ft_secret_pass(ft_secret)
        else:
            return False
        
        tmp_file:str = 'ft_token'
        exec_command:str = f"kubectl exec -n {self.namespace} {ft_pod} -- /bin/bash -c 'redis-cli -a {ft_secret_pass} GET FEATURE_ACCESS_TOKEN' 2> /dev/null > {tmp_file}"
        os.system(exec_command)
        file = File.read_file(os.getcwd(), tmp_file)
        token = json.loads(file)['Token']
        os.remove(tmp_file)

        return token


    def display_features(self, url, FeatureAccessToken):
        ''' Get list of features. '''

        headers = {'FeatureToggleAuthorization': f'FeatureAccessToken {FeatureAccessToken}' }
        request = requests.get(url=f"{url}/{self._api_GetFeatures}", headers=headers, verify=False)

        if request.status_code == 200:
            response:dict = request.json()
            # pretty = json.dumps(response, indent=4)
            # return pretty
            for k,v in response.items():
                print(" {0}:  {1}".format(k.capitalize(), v))

        else:
            print(f"Error {request.status_code} occurred during GetFeatures request. Check the logs.")
            # logging.error(request.text)
            return False


    def set_feature(self, url, feature, bearerToken, FeatureAccessToken, is_enabled=True):
        ''' Function to enable/disable FT. '''

        headers = {'FeatureToggleAuthorization': f'FeatureAccessToken {FeatureAccessToken}', 'Authorization': f'Bearer {bearerToken}', 'accept': '*/*', 'Content-type':'application/json; charset=utf-8'}
        json_data = is_enabled
        result:str = 'enabled' if is_enabled else 'disabled'

        request = requests.put(url=f'{url}/{feature}', json=json_data, headers=headers, verify=False)
        
        if request.status_code in (200, 201, 204):
            print(f"Feature: {feature.split('/')[2]} {result} successfully.")
            return True
        else:
            # logging.error(request.status_code, '\n', request.text)
            print(f"Feature: {feature.split('/')[2]} wasn't enabled. Check the log. Error: {request.status_code}.")
            return False



