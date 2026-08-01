import typer

import sys
import platform
import logging

from git_tools import git_app
from postgre_tools.cli import sql_app
from bimeister.feature_toggles import ft_app
from docker_tools import docker_app
from bimeister.cli import lic_app
from vsphere_tools import vsphere_app
from bimeister.cli import auth_app
from __init__ import __version__

app = typer.Typer(
    add_completion=False,
    pretty_exceptions_enable=False,
    context_settings={"help_option_names": ["-h", "--help"]}
    )

def version_callback(value: bool):
    if value:
        print(f"version: {__version__}")
        raise typer.Exit()

@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(None, "-V", "--version",
                                 callback=version_callback,
                                 help="Show bimutils version."),
    url: str = typer.Option(None, "--url", help="Check bimeister version.")
        ):
        if url:
            import bimeister.bimeister_tools as bt
            bt.print_bim_version(url)
            raise typer.Exit()

app.add_typer(git_app, name="git")
app.add_typer(sql_app, name="sql")
app.add_typer(ft_app, name="ft")
app.add_typer(docker_app, name="image")
app.add_typer(lic_app, name="license")
app.add_typer(vsphere_app, name="vsphere")
app.add_typer(auth_app)


if __name__ == '__main__':
    if platform.system() == 'Linux':
        import readline # opportunity to have access of input history

    from bimeister.interactive.dispatcher import launch_menu
    from common import utils, mlogger
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=utils.get_resourse_path(".env"))

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
            launch_menu()
        except KeyboardInterrupt:
            print('\nKeyboardInterrupt')