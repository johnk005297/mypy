#
import docker
import platform


class Docker:

    def __init__(self):
        if not platform.system() == 'Linux':
            return
        self.__client = docker.from_env()


    def display_containers(self):
        ''' Function to display containers in format 'id  name'. '''

        all_cont:bool = input("Display only running containers? (Y/N): ").strip().lower() == 'y'
        all_containers = dict([[x.name, x.short_id] for x in self.__client.containers.list(all)])
        running_containers = dict([[x.name, x.short_id] for x in self.__client.containers.list()])
        result = all_containers if all_cont else running_containers
        
        for name, id in result.items():
            print(f"{id}  {name}")


    def get_container_interactive_logs(self, id):
        ''' Turn on logs of the specific container in interactive mode. '''

        container = self.__client.containers.get(id)
        log = container.logs(stream=True)
        try:
            while next(log):
                print(next(log).decode())
        except KeyboardInterrupt:
            print('\nInterrupted by the user.')


    def get_log_from_single_container(self, id, in_file=False):
        ''' Get log from a single container. '''

        log = self.__client.containers.get(id).logs(tail=500, timestamps=True).decode()
        print(log)



