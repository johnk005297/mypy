import typer

import logging
import sys
import platform

import mlogger
import app_menu
import interactive_menu
from tools import Tools
from dotenv import load_dotenv
load_dotenv(dotenv_path=Tools.get_resourse_path(".env"))

from git import git_app
from postgre import sql_app
from featureToggle import ft_app
from mdocker import docker_app
from license import lic_app
from vsphere import vsphere_app
from auth import auth_app

# opportunity to have access of input history
if platform.system() == 'Linux':
    import readline


app = typer.Typer()

def version_callback(value: bool):
    if value:
        print(f"version: {app_menu.AppMenu.__version__}")
        raise typer.Exit()

@app.callback()
def main(
    version: bool = typer.Option(None, "--version", "-v", callback=version_callback, help="Show CLI version.")):
    pass

app.add_typer(git_app, name="git")
app.add_typer(sql_app, name="sql")
app.add_typer(ft_app, name="ft")
app.add_typer(docker_app, name="docker")
app.add_typer(lic_app, name="license")
app.add_typer(vsphere_app, name="vsphere")
app.add_typer(auth_app)


if __name__ == '__main__':
    logs = mlogger.Logs()
    logs.set_full_access_to_log_file(logs.filepath, 0o666)
    logger = mlogger.file_logger(logs.filepath, logLevel=logging.INFO)
    if len(sys.argv) > 1:
        try:
            app()
        except typer.Abort:
            sys.exit(1)
    else:
        try:    
            interactive_menu.launch_menu()
        except KeyboardInterrupt:
            print('\nKeyboardInterrupt')
