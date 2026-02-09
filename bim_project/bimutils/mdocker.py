import docker
import typer
from docker.errors import DockerException, APIError, ImageNotFound, NotFound
from rich.console import Console

import os
import sys
import gzip
import tarfile
import logging
from pathlib import Path

from mlogger import Logs
from tools import File

_logger = logging.getLogger(__name__)
_logs = Logs()


class Docker:
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
        if not isinstance(images, list) or not images:
            raise ValueError(f"{self.pull_images.__name__}: argument images expected to be a list")
        not_pulled_images: list = []
        with self.console.status("Start pulling images", spinner='moon') as status:
            for image in images:
                try:
                    status.update(f"Pulling image: {image}")
                    self._client.images.pull(image)
                    self.console.print(f"[green]Pulled: {image}[/green]")
                except NotFound as err:
                    self.console.print(f"ImageNotFound: {err}")
                    not_pulled_images.append(image)
                    continue
                except APIError as err:
                    _logger.error(err)
                    self.console.print(f"[red]Failed image: {err}[/red]")
                    not_pulled_images.append(image)
                    continue
                except Exception as err:
                    _logger.error(err)
                    print(_logs.err_message)
                    continue
        images = [image for image in images if image not in not_pulled_images]
        return images if images else None

    def print_images(self, images: list):
        """ Function prints a list of host machine images on a screen. """
        for image in images:
            print(image)

    def save_images(self, images: list, purge: bool=True, output: str=None):
        """ Function saves docker images locally into tgz archive files, 
            or packing tgz file(s) into single tar archive.
        """

        if not images:
            _logger.error(f"{self.save_images.__name__}: empty list of images")
            return None
        elif not isinstance(images, list):
            _logger.error(f"{self.save_images.__name__}: argument images expected to be a list")
            return None
        tgz_files: list = []
        with self.console.status("Start saving images", spinner='moon') as status:
            if len(images) == 1 and output:
                image_arch_name = output
            for image_ref in images:
                try:
                    image = self._client.images.get(image_ref)
                    if output and len(images) == 1:
                        image_arch_name = output[:-len(Path(output).suffix)] + '.tgz' if Path(output).suffix else output + '.tgz'
                    else:
                        image_arch_name = f"{image_ref.replace('/', '^').replace(':','#')}.tgz"
                    tgz_files.append(image_arch_name)
                    status.update(f"Saving image: {image_ref}")
                    with gzip.open(image_arch_name, 'wb') as file:
                        for chunk in image.save(named=True):
                            file.write(chunk)
                        self.console.print(f"[green]Saved: {image_arch_name}[/green]")
                    if purge:
                        self._client.images.remove(image=image_ref, force=True)
                except ImageNotFound as err:
                    _logger.error(err)
                    self.console.print(f"[red]Error: Image '{image_ref}' not found locally.[/red]")
                    continue
                except Exception as err:
                    _logger.error(err)
                    print(_logs.err_message)
                    continue
            if len(images) > 1 and output:
                arcname: str = output if output else 'images.tar'
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



# docker_app CLI
docker_app = typer.Typer(help="Perform operations with docker images.")

@docker_app.callback()
def docker_callback(): # validate docker engine connection
    d = Docker()
    if not d.is_connected:
        sys.exit()

@docker_app.command(name="save", help="Save compressed docker images locally, or pack it into a single tar archive.")
def save_images(
    file: str = typer.Option(None, "-f", "--file", help="Full path to a text file with a list of images."),
    images: list[str] = typer.Option(None, "-i", "--image", help="Image reference(s). Usage: docker save -i \"image_ref\" -i \"image_ref\" "),
    purge: bool = typer.Option("True", "--purge/--no-purge", help="Do not purge images from docker engine after saving."),
    output: str = typer.Option(None, "-o", "--output", help="Output filename without extension, because file is compressed in tgz.")
            ):
    d = Docker()
    if images and file:
        typer.echo("Error: Cannot use --file and --image together.")
        raise typer.Abort()
    if file:
        if not os.path.isfile(f"{os.getcwd()}/{file}"):
            print(f"{file}: file not found!")
            raise typer.Abort()
        data = File.read_file(file)
        images = [image for image in data.split()]
    pulled_images = d.pull_images(images)
    d.save_images(pulled_images, purge=purge, output=output)

@docker_app.command(name="list", help="Show current images on localhost. (aliases: ls)")
@docker_app.command(name="ls", hidden=True)
def print_images():
    d = Docker()
    images = d.get_list_of_images()
    d.print_images(images)


    # def push_images(self, **kwargs):
    #     """ Fucntion to push docker images to registry. """

    #     registry_url = kwargs['repo_url']
    #     repo_name = kwargs['repo_name']
    #     username = kwargs['user']
    #     password = kwargs['password']
    #     tag = kwargs['tag']
    #     image_ref = kwargs['image_ref']

    # def check_registry_access(self, registry_url, username, password):
    #     """ Check access to a private container registry. """

    #     try:
    #         self._client.login(
    #             registry = registry_url,
    #             username = username,
    #             password = password
    #         )
    #     except APIError as err:
    #         _logger.error(err)
    #         print("Login to registry failed.")
    #         sys.exit()