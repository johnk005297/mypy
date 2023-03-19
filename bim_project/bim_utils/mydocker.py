#
import docker
from prettytable import PrettyTable

class Docker:


    def __init__(self):
        try:
            self.__client = docker.from_env()
            self._check_docker = True
            self._commands:list = [['docker', '-h'], ['docker', 'ls'], ['docker', 'ls', '--all'], ['docker', 'logs', '-i']]
        except docker.errors.DockerException:
            self._check_docker:bool = False


    def __getattr__(self, item):
        raise AttributeError("Docker class has no such attribute: " + item)


    def docker_menu(self):
        ''' Appearance of docker commands menu. '''

        _docker_menu = "Docker options:                                                                                \
                          \n                                                                                           \
                          \n   Containers                                                                              \
                          \n      docker ls                        display running containers                          \
                          \n      docker ls --all                  display all containers                              \
                          \n                                                                                           \
                          \n   Logs                                                                                    \
                          \n      docker logs --all                get all containers logs                             \
                          \n      docker logs <container_id>       get logs from specific container                    \
                          \n      docker logs -i <container_id>    get logs from specific container interactively "


        return _docker_menu


    def display_containers(self, all=False):
        ''' Function to display containers in format 'id  name'. '''

        if all:
            containers:dict = {x.name: [x.id, x.short_id, x.status] for x in self.__client.containers.list(all)}
        else:
            containers:dict = {x.name: [x.id, x.short_id, x.status] for x in self.__client.containers.list()}

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
        except:
            print("Incorrect container id.")
            return False
        
        try:
            while next(log):
                print(next(log).decode())
        except KeyboardInterrupt:
            print('\nInterrupted by the user.')


    def get_container_log(self, id, tail=500, in_file=False):
        ''' Get log from a single container. '''

        log = self.__client.containers.get(id).logs(tail=tail, timestamps=False).decode()
        print(log)
