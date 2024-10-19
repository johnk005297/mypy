#
import base64
import os
import re
from log import Logs
from prettytable import PrettyTable
from kubernetes.client.rest import ApiException
from kubernetes import client, config
from kubernetes.stream import stream
from tools import Tools, File, Folder
from colorama import init, Fore
init(autoreset=True)


class K8S:
    __slots__ = ('__namespace', '_ft_token')
    __logger = Logs().f_logger(__name__)
    _bimeister_log_folder = Logs()._bimeister_log_folder + '_k8s'

    def __init__(self, namespace:str=None):
        self.__namespace = namespace
        self._ft_token: bool = False

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
        """ Appearance of docker commands menu. """

        _k8s_menu = "Kubernets options(requires access to kube API):                                                                    \
                          \n                                                                                                            \
                          \n   Pods/Namespaces                                                                                          \
                          \n      kube ns                                       display cluster namespaces                              \
                          \n      kube pods                                     display the list of pods                                \
                          \n                                                                                                            \
                          \n    Logs                                                                                                    \
                          \n       kube logs -f --all                                                                                   \
                          \n       <optional keys>:                                                                                     \
                          \n             -n <namespace>                         default value: bimeister                                \
                          \n             --tail <number of lines>               defines the amount of lines to capture from the end     \
                          \n       kube logs -f --pods <pod_name pod_name ...>  save log in file for specific pod(s)                    \
                          \n                                                                                                            \
                          \n   Main                                                                                                     \
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
        """ Get feature toggle pod. In current version we are checking for redis or keydb."""

        v1 = self.get_CoreV1Api()
        pods = v1.list_pod_for_all_namespaces(watch=False)

        possible_ft_pods: list = ['redis', 'keydb']
        counter = Tools.counter()
        for item in pods.items:
            count = counter()
            # if item.metadata.namespace == self.__namespace and (item.spec.containers[0].name == 'redis' or item.spec.containers[0].name == 'keydb') and item.status.phase == 'Running':
            if item.metadata.namespace == self.__namespace and item.spec.containers[0].name in possible_ft_pods and item.status.phase == 'Running':
                ft_pod: str = item.metadata.name
                return ft_pod
            elif count == len(pods.items):
                print("No feature toggle pod was found. Check for needed pod.")
        return False

    def get_secret_with_ft_token(self):
        """ Function returns a k8s secret name from the cluster. """

        v1 = self.get_CoreV1Api()
        secrets_list: list = v1.list_namespaced_secret(self.__namespace).items  # Getting a list of all the secrets

        # Getting a needed secret for FT activation
        possible_ft_secrets: list = ['redis', 'keydb']
        counter = Tools.counter()
        for item in secrets_list:
            count = counter()
            secret = item.metadata.name.split('-')
            if secret[0] == self.__namespace and secret[1] in possible_ft_secrets:
                return item.metadata.name
            elif count == len(secrets_list):
                return False

    def get_ft_secret_pass(self, secret_name):
        """ Get password from the k8s secret of the pod. """

        v1 = self.get_CoreV1Api()
        try:
            secret: dict = v1.read_namespaced_secret(secret_name, self.__namespace).data
            if secret_name.split('-')[1] == 'redis':
                passwd: str = base64.b64decode(secret['REDIS_PASSWORD']).decode('utf-8')

            else:
                # keydb secret is encoded. Need to decode it first, then extract the password.
                decode: str = base64.b64decode(secret['server.sh']).decode('utf-8')
                for string in range(len(decode.split())):
                    if 'requirepass' in decode.split()[string]:
                        passwd = decode.split()[string + 1].strip("\"")

        except ApiException as err:
            self.__logger.error(err)
            return False
        
        except Exception as err:
            self.__logger.error(err)
            return False

        # passwd = base64.b64decode(list(secret.values())[0]).decode('utf-8')
        return passwd if passwd else False

    def get_ft_token(self):
        """ Function get's FT token into token variable. During process it creates tmp file after kubectl command, 
        read token from the file into var, and delete the file.
        """
        
        ft_pod = self.get_ft_pod()
        ft_secret = self.get_secret_with_ft_token()
        if ft_pod and ft_secret:
            ft_secret_pass = self.get_ft_secret_pass(ft_secret)
        else:
            return False

        # define what cli we need to use: redis or keydb
        cli = 'redis-cli' if ft_secret.split('-')[1] == 'redis' else 'keydb-cli'

        v1 = self.get_CoreV1Api()
        exec_command: str = f"{cli} -a '{ft_secret_pass}' GET FEATURE_ACCESS_TOKEN"
        data = self.exec_cmd_in_pod(ft_pod, ft_secret.split('-')[1], exec_command, self.__namespace, v1)
        if not data:
            self.__logger.error(f"No FT token was received from {cli}. Check the logs!")
            return False

        # search for token in data's sting, and convert string '{"Token":"<token>}"' into dictionary using eval
        ft_token = eval(re.search('.*\{.*\}', data).group())['Token']
        self._ft_token = True if ft_token else False
        return ft_token

    def get_ft_token_from_webapi_logs(self):
        """ Function get's FT token from webapi pod logs. """

        v1 = self.get_CoreV1Api()
        pods = v1.list_pod_for_all_namespaces(watch=False, field_selector=f"metadata.namespace={self.__namespace}")
        counter = Tools.counter()
        webapi_pods = list()
        ft_token = str()
        for item in pods.items:
            count = counter()
            if item.spec.containers[0].name == 'webapi' and item.status.phase == 'Running':
                webapi_pod: str = item.metadata.name
                webapi_pods.append(webapi_pod)
            elif count == len(pods.items) and not webapi_pods:
                print("Running webapi pod wasn't found. Check for needed pod.")
                return False
        for pod in webapi_pods:
            pod_log = v1.read_namespaced_pod_log(name=pod, namespace=self.__namespace)
            index = pod_log.find('FEATURE_ACCESS_TOKEN')
            if index != -1:
                ft_token = pod_log[index:].split()[1]
        if not ft_token:
            self.__logger.error("No FT token was received from webapi logs. Check the logs!")
            return False
        return ft_token

    def exec_cmd_in_pod(self, pod, container, command, namespace, api_instance):   # Need to test this function!
        """ Execute command in pod. """

        exec_command = ["sh", "-c", command]
        try:
            # response from stream operation is a string
            resp = stream(api_instance.connect_get_namespaced_pod_exec,
                        pod,
                        namespace,
                        container=container,
                        command=exec_command,
                        stderr=True, stdin=False,
                        stdout=True, tty=False,
                        _preload_content=True)
            
            self.__logger.info(resp)
        except Exception as err:
            self.__logger.error(err)
            return False
        return resp

    def get_namespaces(self):
        """ Get collection of namespaces in a cluster. """

        v1 = self.get_CoreV1Api()
        try:
            ns:list = [ns.metadata.name for ns in v1.list_namespace().items]
        except Exception as err:
            self.__logger.error(err)
            print("Couldn't get namespaces. Check the log.")
            return False
        return ns


    def display_namespaces(self):
        """ Display cluster namespaces. """

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
        """ Collect dictionary of pods with attributes: ready, status, restarts, namespace. """

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
        """ Display list of pods in a pretty table. """

        pods = self.get_pods(namespace=namespace)
        table = PrettyTable()
        table.field_names = ['NAME', 'READY', 'STATUS', 'NAMESPACE', 'RESTARTS']
        table.align = 'l'
        try:
            for name, value in pods.items():
                table.add_row([name, value[1], value[0], value[3], value[2]] if value[1] else [Fore.RED + str(name), str(value[1]), str(value[0]), str(value[3]), str(value[2]) + Fore.RESET])
        except NameError as err:
            print(f"Error: {err}")
        print(table)


    # Function isn't finished
    def get_all_pods_log(self, namespace='bimeister', tail=5000):
        """ Function get logs from all the pods in a given namespace. """

        v1 = self.get_CoreV1Api()
        # check namespace if it exists
        ns:list = self.get_namespaces()
        if namespace not in ns:
            print("Error: Non-existing namespace.")
            return False

        Folder.create_folder(os.getcwd(), self._bimeister_log_folder)
        pods = self.get_pods(namespace=namespace)
        for pod in pods:
            try:
                pod_log = v1.read_namespaced_pod_log(name=pod, namespace=namespace, pretty=True, tail_lines=tail)
                filename:str = pod + ".log"
                with open(self._bimeister_log_folder + '/' + filename, 'w', encoding='utf-8') as file:
                    file.write(pod_log)
                    print(self._bimeister_log_folder + '/' + filename)
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

    def get_pod_log(self, *args, namespace='bimeister', tail=5000):
        """ Function gets logs from the specific pods. """

        v1 = self.get_CoreV1Api()
        # check namespace if it exists
        ns:list = self.get_namespaces()
        if namespace not in ns:
            print("Error: Non-existing namespace.")
            return False

        Folder.create_folder(os.getcwd(), self._bimeister_log_folder)
        for pod in args:
            try:
                pod_log = v1.read_namespaced_pod_log(name=pod, namespace=namespace, pretty=True, tail_lines=tail)
                filename:str = pod + '.log'
                with open(self._bimeister_log_folder + '/' + filename, 'w', encoding='utf-8') as file:
                    file.write(pod_log)
                    print(self._bimeister_log_folder + '/' + filename)
            except ApiException as err:
                self.__logger.error(err)
                print(f"Couldn't fetch logs for pod: {pod}. Check the log.")
            except Exception as err:
                self.__logger.error(err)
                print(f"Couldn't fetch logs for pod: {pod}. Check the log.")
        return True

    def check_args_for_namespace(self, user_command):
        """ Function checks if -n flag was provided by user. """

        namespace = False
        if '-n' in user_command:
            namespace_idx = user_command.index('-n') + 1
            namespace = user_command[namespace_idx]
        return namespace