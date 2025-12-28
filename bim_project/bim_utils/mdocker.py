import os
import sys
import gzip
import tarfile
import logging
import docker
from docker.errors import DockerException, APIError, ImageNotFound
from mlogger import Logs
from rich.console import Console
from datetime import datetime

_logger = logging.getLogger(__name__)
_logs = Logs()


class Docker:
    # _log_folder = 'docker_logs'
    _client = None

    def __init__(self):
        self.is_connected = self.check_docker()
        self.console = Console(highlight=False)

    @classmethod
    def check_docker(cls):
        """ Function to check if docker is enabled, and can be connected. """
        try:
            cls._client = docker.from_env()
            return True
        except DockerException as err:
            _logger.error(err)
            print(f"Docker connection failed: {err}")
            return False
        except APIError as err:
            _logger.error(err)
            print(f"Docker API error: {err}")
            # print("Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?")
            return False
        except Exception as err:
            _logger.error(err)
            return False

    def __getattr__(self, item):
        raise AttributeError("Docker class has no such attribute: " + item)

    def get_list_of_images(self):
        """ Function gets a list of images. """
        images: list = self._client.images.list()
        return images

    def pull_images(self, images: list) -> list:
        """ Function for pulling images on a localhost. 
            Takes a list as an argument, and returns a list of successfully pulled ones.
        """
        if not isinstance(images, list):
            raise ValueError(f"{self.pull_images.__name__}: argument images expected to be a list")
        not_pulled_images: list = []
        with self.console.status("Start pulling images", spinner='moon') as status:
            for image in images:
                try:
                    status.update(f"Pulling image: {image}")
                    self._client.images.pull(image)
                    self.console.print(f"[green]Pulled image: {image}[/green]")
                except docker.errors.APIError as err:
                    _logger.error(err)
                    self.console.print(f"[red]Failed image: {err}[/red]")
                    not_pulled_images.append(image)
                    continue
        images = [image for image in images if image not in not_pulled_images]
        return images

    def print_images(self, images: list):
        """ Function prints a list of host machine images on a screen. """
        for image in images:
            print(image)

    def save_images(self, images: list, onefile=False):
        """ Function saves docker images locally into tgz archive files, 
            or packing tgz file(s) into single tar archive.
        """

        if not images or not isinstance(images, list):
            raise ValueError(f"{self.save_images.__name__}: argument images expected to be a list")
        tgz_files: list = []
        with self.console.status("Start saving images", spinner='moon') as status:
            for name in images:
                try:
                    image = self._client.images.get(name)
                    image_arch_name = f"{name.replace('/', '^').replace(':','#')}.tgz"
                    tgz_files.append(image_arch_name)
                    status.update(f"Saving image: {name}")
                    with gzip.open(image_arch_name, 'wb') as file:
                        for chunk in image.save(named=True):
                            file.write(chunk)
                        self.console.print(f"[green]Saved image: {image_arch_name}[/green]")
                except ImageNotFound as err:
                    _logger.error(err)
                    self.console.print(f"[red]Error: Image '{name}' not found locally.[/red]")
                    continue
                except Exception as err:
                    _logger.error(err)
                    print(_logs.err_message)
                    continue
            if onefile:
                arcname: str = 'images.tar'
                if os.path.isfile(arcname):
                    arcname = datetime.today().strftime("%d.%m.%Y") + "_" + arcname
                status.update(f"Packing final archive: {arcname}")
                try:
                    with tarfile.open(arcname, 'w') as tar:
                        for file in tgz_files:
                            tar.add(file, arcname=file)
                            os.remove(file)
                    self.console.print(f"\nImages packed into: {arcname}")
                except PermissionError as err:
                    if os.path.isfile(arcname):
                        print(f"File {arcname} already exists.")
                    print("You might need to run command with elevated privileges (as an administrator/using sudo).")
                    sys.exit()
                except Exception as err:
                    print(f"Enexpected error: {err}")
                    sys.exit()

    def push_images(self, images: list):
        """ Fucntion to push docker images into registry. """
        pass