#
import docker
from prettytable import PrettyTable
from tools import Folder, Tools
import os
import json
# import logging
from log import Logs


class Docker:

    __logger = Logs().f_logger(__name__)
    _bimeister_log_folder = Logs()._bimeister_log_folder + '_docker'


    def __init__(self):
        self._ft_token:bool        = False
        self._permissions:bool     = False


    @classmethod
    def __check_docker(cls):
        try:
            docker.from_env()
            return True
        except docker.errors.DockerException as err:
            cls.__logger.error(err)
            return False
        except Exception as err:
            cls.__logger.error(err)
            return False


    def get_docker_client(self):
        if self.__check_docker():
            self.__client = docker.from_env()

            # check if user has a docker group
            if not Tools.is_windows() and not Tools.is_user_in_group('docker'):
                print("Current user doesn't have privileges to run docker commands. Use sudo or add user to docker group.")
                return False
            return True
        else:
            return False


    def __getattr__(self, item):
        raise AttributeError("Docker class has no such attribute: " + item)


    def docker_menu(self):
        ''' Appearance of docker commands menu. '''

        _docker_menu = "Docker options(runs locally on a host):                                                                                                  \
                          \n                                                                                                                                     \
                          \n   Containers                                                                                                                        \
                          \n      docker ls                                         display running containers                                                   \
                          \n      docker ls --all                                   display all containers                                                       \
                          \n                                                                                                                                     \
                          \n   Logs                                                                                                                              \
                          \n      docker logs <container_id container_id ...>     display logs from the specific container(s)                                  \
                          \n      docker logs -f --all                              get all containers logs in files                                             \
                          \n      docker logs -f <container_id container_id ...>  get logs in the file                                                         \
                          \n      <optional keys>:                                                                                                               \
                          \n            --days(optional)                            exact period to get logs for. Not applicable with '-i' flag.                 \
                          \n            --tail(optional)                            amount of lines from the end of the log. Not applicable with '-i' flag.      \
                          \n      docker logs -i <container_id>                     get logs from specific container interactively                               \
                          \n                                                                                                                                     \
                          \n   Main                                                                                                                              \
                          \n      q                                                 exit"

        return _docker_menu



    def check_permissions(self):
        ''' Function to check needed permissions to work with docker. '''

        pass


    def get_containers(self, all=False):
        ''' Get a dictionary of all docker containers on the server. '''

        try:
            if all:
                containers:dict = {x.name: [x.id, x.short_id, x.status] for x in self.__client.containers.list(all)}
                return containers
            else:
                containers:dict = {x.name: [x.id, x.short_id, x.status] for x in self.__client.containers.list()}
                return containers
        except:
            return False


    def display_containers(self, all=False):
        ''' Function to display containers in format 'id  name'. '''

        containers = self.get_containers(all=True) if all else self.get_containers()

        if not containers:
            print("No docker containers have been found." if all else "No running docker containers have been found.")
            return
        
        table = PrettyTable()
        table.field_names = ['ID', 'NAME', 'STATUS']
        table.align = 'l'
        try:
            for name, value in containers.items():
                table.add_row([value[1], name, value[2]])
        except NameError:
            print("Error: NameError.")
        print(table)


    def get_container_interactive_logs(self, id):
        ''' Turn on logs of the specific container in interactive mode. '''

        try:
            container = self.__client.containers.get(id)
            log = container.logs(stream=True, tail=10, timestamps=False)
        except docker.errors.NotFound:
            print("No such docker container: ", id)
            return False
        except docker.errors.APIError as err:
            self.__logger.error(err)
            print("Server error. Check the log.")
            return False

        try:
            while next(log):
                print(next(log).decode())
        except KeyboardInterrupt:
            print('\nInterrupted by the user.')

        return True


    def get_container_log(self, *args, in_file=False, tail=5000, days=None):
        ''' Get log from a single container. '''

        if in_file:
            Folder.create_folder(os.getcwd(), self._bimeister_log_folder)

        if days:
            delta:int = Tools.calculate_timedelta(days)

        try:
            for id in args:
                if not days:
                    log = self.__client.containers.get(id).logs(tail=tail, timestamps=False).decode()
                else:
                    log = self.__client.containers.get(id).logs(since=delta, timestamps=False).decode()

                filename = self.__client.containers.get(id).name + '.log'
                if in_file:
                    with open(self._bimeister_log_folder + '/' + filename, 'w', encoding='utf-8') as file:
                        file.write(log)
                        print(self._bimeister_log_folder + '/' + filename)
                else:
                    print(log)

        except docker.errors.NotFound as err:
            self.__logger.error(err)
            print("No such docker container.")
            pass
        except docker.errors.APIError as err:
            self.__logger.error(err)
            print("Server error. Check the log.")
            pass
        return True


    def get_all_containers_logs(self, tail=5000, days=None):
        ''' Get logs from all containers in files. '''

        Folder.create_folder(os.getcwd(), self._bimeister_log_folder)
        containers = self.get_containers(all=True)
        if days:
            delta:int = Tools.calculate_timedelta(days)
        for name, value in containers.items():

            try:
                if not days:
                    log = self.__client.containers.get(value[1]).logs(tail=tail, timestamps=False).decode()
                else:
                    log = self.__client.containers.get(value[1]).logs(since=delta, timestamps=False).decode()
                
                filename = name + '.log'
                with open(self._bimeister_log_folder + '/' + filename, 'w', encoding='utf-8') as file:
                    file.write(log)
                    print(self._bimeister_log_folder + '/' + filename)

            except docker.errors.APIError as err:
                self.__logger.error(err)
                print("Server error. Check the log.")

            except:
                print("Error occured.")
                return False
                
        Tools.zip_files_in_dir(self._bimeister_log_folder, self._bimeister_log_folder)    # pack logs in zip archive
        Folder.clean_folder(self._bimeister_log_folder, remove=True)                      # delete folder with *.log files

        return True


    ################# Feature Toggle block #################

    def get_ft_container(self):
        ''' Function finds needed container for FT. Returns tuple of container id and name. '''

        ft_pods:tuple = ('keydb', 'redis')
        containers = self.__client.containers.list()
        for container in containers:
            if container.labels.get('com.docker.compose.service', False) in ft_pods and container.status == 'running':
                return (container.id, container.name)
        
        message:str = f"No {ft_pods} were found with Running status among containers. Check for it."
        self.__logger.error(message)
        print(message)
        return False
            


    def get_ft_secret_pass(self):
        ''' Function gets secret from docker container inspectation. '''

        try:
            client = docker.APIClient(base_url='unix://var/run/docker.sock')
        except:
            print("Smth is wrong with the docker. Couldn't run docker.APIClient.")
            return False
        
        id = self.get_ft_container()[0]
        container = dict(client.inspect_container(id))

        if '--requirepass' in container['Args']:
            idx = container['Args'].index('--requirepass')
            ft_secret = container['Args'][idx + 1]

            return ft_secret
        
        else:
            return False
        

    def get_ft_token(self):
        ''' Function provides ft token. '''
        
        try:
            ft_containerId = self.get_ft_container()[0]
        except TypeError as err:
            self.__logger.error(err)
            return False
        except Exception as err:
            self.__logger.error(err)
            return False

        ft_secret_pass = self.get_ft_secret_pass()
        cli = 'keydb-cli'
        exec_command:str = f"{cli} -a {ft_secret_pass} GET FEATURE_ACCESS_TOKEN"

        ft_container = self.__client.containers.get(ft_containerId)
        get_ft = ft_container.exec_run(exec_command, stderr=False)
        result = get_ft[1].decode('utf-8')
        try:
            ft_token = json.loads(result)['Token']  # json.loads performs a dictionary from the result var, and then ask for it's 'Token' key value.            
            self.__logger.info(f"Received FT: {ft_token}")
        except json.decoder.JSONDecodeError as err:
            self.__logger.error(err)
            print("No FT token was received. Check the logs!")
            return False


        self._ft_token = True if ft_token else False
        return ft_token
      