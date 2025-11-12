import platform
import os
import logging
import sys


def file_logger(filepath, logLevel=logging.DEBUG):
    """ Create a custom logger with file output. """

    # Create a custom logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logLevel)

    # Prevent adding multiple handlers if the logger is already configured
    try:
        if not root_logger.handlers:
            f_handler = logging.FileHandler(filepath, mode='a', encoding='utf-8')
            f_format = logging.Formatter(fmt="%(asctime)s %(levelname)s %(module)s:%(funcName)s(line:%(lineno)d) | %(message)s",
                                        datefmt="'%Y-%m-%d %H:%M:%S'")
            f_handler.setFormatter(f_format)
            root_logger.addHandler(f_handler)
    except FileNotFoundError:
            sys.exit("Error: log file not found!")
    except PermissionError:
            print(f"Write access is not granted for '{filepath}' file.\nRemove the file and try again!")
            sys.exit()
    return root_logger


class Logs:

    def __init__(self):
        self._filepath: str = "/tmp/bimutils.log" if platform.system() == "Linux" else ".bimutils.log"

    @property
    def filepath(self):
        return self._filepath

    @property
    def err_message(self):
        return f"Error. Check the log: {self._filepath}"

    def set_full_access_to_log_file(self, filepath, mode):
        """ Perform check if file exists, and if user has access to it.
        Grant read and write permissions to all users(666) to log file.
        """

        if platform.system() == 'Windows':
            return
        try:
            if not os.access(filepath, os.F_OK): # check if file exists
                with open(filepath, 'w', encoding='utf-8'):
                    pass
                os.chmod(filepath, mode)
            if not os.access(filepath, os.W_OK):
                sys.exit(f"Write access is not granted for '{filepath}'.\nRemove the file, and try again!")
        except OSError as err:
            print(f"Error: {err}")