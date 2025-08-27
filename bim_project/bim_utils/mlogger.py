import platform
import os
import logging
import sys


def file_logger(log_file, logLevel=logging.DEBUG):
    """ Create a custom logger with file output. """
    
    # Create a custom logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logLevel)

    # Prevent adding multiple handlers if the logger is already configured
    if not root_logger.handlers:
        f_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        f_format = logging.Formatter(fmt="%(asctime)s %(levelname)s %(module)s:%(funcName)s(line:%(lineno)d) | %(message)s",
                                     datefmt="'%Y-%m-%d %H:%M:%S'")
        f_handler.setFormatter(f_format)
        root_logger.addHandler(f_handler)
    return root_logger


class Logs:

    def __init__(self):
        self.filepath: str = "/tmp/bimutils.log" if platform.system() == "Linux" else ".bimutils.log"
        self.set_full_access_to_log_file(self.filepath, 0o777)

    def set_full_access_to_log_file(self, filepath, mode):
        """ Provide full access(777) to log file. """

        if platform.system() == 'Windows':
            return
        try:
            os.chmod(filepath, mode)
        except FileExistsError:
            pass
        except PermissionError:
            print(f"Permission denied: Unable to create '{filepath}'.")
            sys.exit()
        except FileNotFoundError as err:
            with open(filepath, 'x', encoding='utf-8'):
                pass
        except Exception as err:
            print(f"An error occurred: {err}")
            sys.exit()
