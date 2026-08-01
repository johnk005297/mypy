import typer

import sys
import os

from docker_tools import Docker
from common.utils import File


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
    output: str = typer.Option("images.tar", "-o", "--output", help="Output filename.")
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

@docker_app.command(name="list", help="Show current images on localhost \[aliases: ls]")
@docker_app.command(name="ls", hidden=True)
def print_images():
    d = Docker()
    images = d.get_list_of_images()
    d.print_images(images)