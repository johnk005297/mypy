#
from kubernetes.client.rest import ApiException
from kubernetes import client, config
from kubernetes.stream import stream
from tools import Tools, File
import json
import base64
import os
from log import Logs


class K8S:

    __logger = Logs().f_logger(__name__)
    
    def __init__(self, namespace:str=None):
        self.namespace = namespace
        self._ft_token:bool = False           
        try:
            config.load_kube_config()
            self._check_k8s:bool = True
        except config.ConfigException as config_err:
            self._check_k8s:bool = False
            self.__logger.error(config_err)
            self.__logger.info("Check out the kube config file, or try to run script under 'root' user.")
        except ApiException as client_api_err:
            self._check_k8s:bool = False
            self.__logger.error(client_api_err)
        except Exception as err:
            self.__logger.error(err)
            self._check_k8s:bool = False


    def k8s_menu(self):
        ''' Appearance of docker commands menu. '''

        _k8s_menu = "Kubernets options(runs locally on a host):                                       \
                          \n                                                                          \
                          \n   Feature toggle                                                         \
                          \n      kube ft --list                     display list of features         \
                          \n      kube ft [ft_name] [--on/--off]     turn on/off feature              \
                          \n        usage:                                                            \
                          \n          kube ft Spatium --on                                            \
                          \n                                                                          \
                          \n   Main                                                                   \
                          \n      q                                  exit"


        return _k8s_menu


    def get_CoreV1Api(self):
        
        try:
            v1 = client.CoreV1Api()
        except ApiException as err:
            self.__logger.error(err)
            print("Error occured. Check the logs.")
            return False
        return v1
        

    def get_ft_pod(self):
        ''' Get feature toggle pod. In current version we are checking for redis or keydb.'''

        v1 = self.get_CoreV1Api()
        pods = v1.list_pod_for_all_namespaces(watch=False)

        possible_ft_pods:list = ['redis', 'keydb']
        counter = Tools.counter()
        for item in pods.items:
            count = counter()
            # if item.metadata.namespace == self.namespace and (item.spec.containers[0].name == 'redis' or item.spec.containers[0].name == 'keydb') and item.status.phase == 'Running':
            if item.metadata.namespace == self.namespace and item.spec.containers[0].name in possible_ft_pods and item.status.phase == 'Running':
                ft_pod:str = item.metadata.name
                return ft_pod
            elif count == len(pods.items):
                print("No feature toggle pod was found. Check for needed pod.")
        return False


    def get_ft_secret(self):
        ''' Get a list of all secrets in the cluster. '''

        v1 = self.get_CoreV1Api()
        secrets_list:list = v1.list_namespaced_secret(self.namespace).items  # Getting a list of all the secrets

        # Getting a needed secret for FT activation
        possible_ft_secrets:list = ['redis', 'keydb']
        counter = Tools.counter()
        for item in secrets_list:
            count = counter()
            secret = item.metadata.name.split('-')
            if secret[0] == self.namespace and secret[1] in possible_ft_secrets:
                return item.metadata.name
            elif count == len(secrets_list):
                return False


    def get_ft_secret_pass(self, secret_name):
        ''' Get password from the k8s secret of the pod. '''

        v1 = self.get_CoreV1Api()

        try:
            if secret_name.split('-')[1] == 'redis':
                secret:dict = v1.read_namespaced_secret(secret_name, self.namespace).data
                passwd:str = base64.b64decode(secret['REDIS_PASSWORD']).decode('utf-8')

            else:
                # keydb secret is encoded. Need to decode it first, then extract the password.
                secret:dict = v1.read_namespaced_secret(secret_name, self.namespace).data
                decode:str = base64.b64decode(secret['server.sh']).decode('utf-8')
                for string in range(len(decode.split())):
                    if 'requirepass' in decode.split()[string]:
                        passwd = decode.split()[string + 1].strip("\"")

        except ApiException as err:
            self.__logger.error(err)
            return False

        # passwd = base64.b64decode(list(secret.values())[0]).decode('utf-8')
        return passwd if passwd else False


    def get_ft_token(self):
        ''' Function get's FT token into token variable. During process it creates tmp file after kubectl command, read token from the file into var, and delete the file. '''
        
        ft_pod = self.get_ft_pod()
        ft_secret = self.get_ft_secret()

        if ft_pod and ft_secret:
            ft_secret_pass = self.get_ft_secret_pass(ft_secret)
        else:
            return False

        # define what cli we need to use: redis or keydb
        cli = 'redis-cli' if ft_secret.split('-')[1] == 'redis' else 'keydb-cli'
        tmp_file:str = 'ft_token'

        exec_command:str = f"kubectl exec -n {self.namespace} {ft_pod} -- /bin/bash -c '{cli} -a {ft_secret_pass} GET FEATURE_ACCESS_TOKEN' 2> /dev/null > {tmp_file}"
        os.system(exec_command)
        file = File.read_file(os.getcwd(), tmp_file)
        try:
            ft_token = json.loads(file)['Token']
            self.__logger.info(f"Received FT: {ft_token}")
        except json.decoder.JSONDecodeError as err:
            self.__logger.error(err)
            print("No FT token was received. Check the logs!")
            return False
        os.remove(tmp_file)

        self._ft_token = True if ft_token else False
        return ft_token




