# load credentials from .env file

from dotenv import load_dotenv
from bimutils.common.utils import File

def initialize():
    load_dotenv(dotenv_path=File.get_env_file_path())