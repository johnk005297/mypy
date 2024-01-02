#
from kubernetes.client.rest import ApiException
from kubernetes import client, config
from kubernetes.stream import stream
from tools import Tools, File, Folder
import json
import base64
import os
from log import Logs
from prettytable import PrettyTable
from colorama import init, Fore
init(autoreset=True)


class K8S:

    __logger = Logs().f_logger(__name__)
    _bimeister_log_folder = Logs()._bimeister_log_folder + '_k8s'


    def __init__(self, namespace:str=None):
        self.__namespace     = namespace
        self._ft_token:bool  = False


    @classmethod
    def __check_kube_config(cls):
        try:
            config.load_kube_config()
            return True
        except config.ConfigException as err:
            cls.__logger.error(err)
            return False
        except ApiException as err:
            cls.__logger.error(err)
            return False
        except Exception as err:
            cls.__logger.error(err)
            return False


    def get_kube_config(self):
        return True if self.__check_kube_config() else False


    def k8s_menu(self):
        ''' Appearance of docker commands menu. '''

        _k8s_menu = "Kubernets options(requires access to kube API):                                                        \
                          \n                                                                                                \
                          \n   Pods/Namespaces                                                                              \
                          \n      kube ns                            display cluster namespaces                             \
                          \n      kube pods                          display the list of pods                               \
                          \n                                                                                                \
                          \n    Logs                                                                                        \
                          \n       kube logs -f --all                                                                       \
                          \n       <optional keys>:                                                                         \
                          \n               -n <namespace>           default value: bimeister                                \
                          \n               --tail <number of lines>  defines the amount of lines in the log from the end    \
                          \n   Main                                                                                         \
                          \n      q                                  exit"


        return _k8s_menu


    def get_CoreV1Api(self):

        try:
            v1 = client.CoreV1Api()
        except ApiException as err:
            self.__logger.error(err)
            print("Error occured. Check the logs.")
            return False
        except Exception as err:
            self.__logger.error(err)
            print("Couldn't connect to kubernetes API. Check the log.")
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
            # if item.metadata.namespace == self.__namespace and (item.spec.containers[0].name == 'redis' or item.spec.containers[0].name == 'keydb') and item.status.phase == 'Running':
            if item.metadata.namespace == self.__namespace and item.spec.containers[0].name in possible_ft_pods and item.status.phase == 'Running':
                ft_pod:str = item.metadata.name
                return ft_pod
            elif count == len(pods.items):
                print("No feature toggle pod was found. Check for needed pod.")
        return False


    def get_ft_secret(self):
        ''' Get a list of all secrets in the cluster. '''

        v1 = self.get_CoreV1Api()
        secrets_list:list = v1.list_namespaced_secret(self.__namespace).items  # Getting a list of all the secrets

        # Getting a needed secret for FT activation
        possible_ft_secrets:list = ['redis', 'keydb']
        counter = Tools.counter()
        for item in secrets_list:
            count = counter()
            secret = item.metadata.name.split('-')
            if secret[0] == self.__namespace and secret[1] in possible_ft_secrets:
                return item.metadata.name
            elif count == len(secrets_list):
                return False


    def get_ft_secret_pass(self, secret_name):
        ''' Get password from the k8s secret of the pod. '''

        v1 = self.get_CoreV1Api()
        try:
            if secret_name.split('-')[1] == 'redis':
                secret:dict = v1.read_namespaced_secret(secret_name, self.__namespace).data
                passwd:str = base64.b64decode(secret['REDIS_PASSWORD']).decode('utf-8')

            else:
                # keydb secret is encoded. Need to decode it first, then extract the password.
                secret:dict = v1.read_namespaced_secret(secret_name, self.__namespace).data
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

        exec_command:str = f"kubectl exec -n {self.__namespace} {ft_pod} -- /bin/bash -c '{cli} -a {ft_secret_pass} GET FEATURE_ACCESS_TOKEN' 2> /dev/null > {tmp_file}"
        os.system(exec_command)
        file = File.read_file(os.getcwd(), tmp_file)
        try:
            ft_token = json.loads(file)['Token']
            self.__logger.info(f"Received FT: {ft_token}")
        except json.decoder.JSONDecodeError as err:
            self.__logger.error(err)
            self.__logger.debug(f"GET FEATURE_ACCESS_TOKEN response: {file}")
            print("No FT token was received. Check the logs!")
            os.remove(tmp_file)
            return False
        os.remove(tmp_file)

        self._ft_token = True if ft_token else False
        return ft_token


    def get_namespaces(self):
        ''' Get collection of namespaces in a cluster. '''

        v1 = self.get_CoreV1Api()
        try:
            ns:list = [ns.metadata.name for ns in v1.list_namespace().items]
        except Exception as err:
            self.__logger.error(err)
            print("Couldn't get namespaces. Check the log.")
            return False
        return ns


    def display_namespaces(self):
        ''' Display cluster namespaces. '''

        ns = self.get_namespaces()
        if not ns:
            return False
        table = PrettyTable()
        table.field_names = ['Namespace']
        table.align = 'l'
        for namespace in ns:
            table.add_row([namespace])
        print(table)


    def get_pods(self, namespace='bimeister'):
        ''' Collect dictionary of pods with attributes: ready, status, restarts, namespace. '''

        v1 = self.get_CoreV1Api()
        try:
            pods = v1.list_pod_for_all_namespaces(watch=False, field_selector=f"metadata.namespace={namespace}")
        except Exception as err:
            self.__logger.error(err)
            return False

        # pods:dict = {pod.metadata.name: [pod.status.phase, pod.status.container_statuses[0].ready, pod.status.container_statuses[0].restart_count] for pod in pods.items if pod.metadata.labels['app.kubernetes.io/name'] == pod.status.container_statuses[0].name}
        pods:dict = {pod.metadata.name: [pod.status.phase, pod.status.container_statuses[0].ready, pod.status.container_statuses[0].restart_count, pod.metadata.namespace] for pod in pods.items}
        return pods


    def display_pods(self, namespace='bimeister'):
        ''' Display list of pods in a pretty table. '''

        pods = self.get_pods(namespace=namespace)
        table = PrettyTable()
        table.field_names = ['NAME', 'READY', 'STATUS', 'RESTARTS', 'NAMESPACE']
        table.align = 'l'
        try:
            for name, value in pods.items():
                table.add_row([name, value[1], value[0], value[2], value[3]] if value[1] else [Fore.RED + str(name), str(value[1]), str(value[0]), str(value[2]), str(value[3]) + Fore.RESET])
        except NameError as err:
            print(f"Error: {err}")
        print(table)


    # Function isn't finished
    def get_all_pods_log(self, namespace='bimeister', tail=5000):
        ''' Function get logs from all the pods in a given namespace. '''

        v1 = self.get_CoreV1Api()
        # check for bimeister namespace
        ns:list = self.get_namespaces()
        if namespace not in ns:
            print("Error: Non-existing namespace.")
            return False

        Folder.create_folder(os.getcwd(), self._bimeister_log_folder)
        pods = self.get_pods(namespace=namespace)
        for pod in pods:
            try:
                pod_log = v1.read_namespaced_pod_log(name=pod, namespace=namespace, pretty=True, tail_lines=tail, timestamps=True)
                filename:str = pod + ".log"
                with open(self._bimeister_log_folder + '/' + filename, 'w', encoding='utf-8') as file:
                    file.write(pod_log)
                    print(self._bimeister_log_folder + '/' + filename)
                self.__logger.info(f"Pod log uploaded: {pod}")
            except ApiException as err:
                self.__logger.error(err)
                print(f"Error occurred. Check the log.")
                return False
            except Exception as err:
                self.__logger.error(err)
                print(f"Error occurred. Check the log.")
                return False
        
        # packing to zip archive and remove original log folder
        Tools.zip_files_in_dir(self._bimeister_log_folder, self._bimeister_log_folder)
        Folder.clean_folder(self._bimeister_log_folder, remove=True)

        return True




