import platform
import os
import logging
import sys



# logging.basicConfig(
#      filename=".bimctl.log",
#      encoding="utf-8",
#      filemode="a",
#      format="{asctime} - {levelname} - {message}",
#      style="{",
#      datefmt="%Y-%m-%d %H:%M",
#  )


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
        self.filepath: str = "/tmp/.bimctl.log"
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


    # Temporary not in use. Require to finish setup
    # def set_full_access_to_logs(self, path, mode):
    #     """
    #     Creates a folder if it doesn't exist and sets its permissions and the
    #     permissions of its contents to 777.
    #     Need to make log folder accessible for all users to escape errors at launch.

    #     Args:
    #         folder_path (str): The path to the folder.
    #     """
    #     try:
    #         os.mkdir(path)
    #     except FileExistsError:
    #         pass
    #     except PermissionError:
    #         print(f"Permission denied: Unable to create '{path}'.")
    #         sys.exit()
    #     except Exception as e:
    #         print(f"An error occurred: {err}")
    #         sys.exit()
    #     if platform.system() == 'Windows':
    #         return
    #     try:
    #         # Traverse the directory tree starting from 'path' to top
    #         for root, dirs, files in os.walk(path, topdown=False):

    #             # Iterate over the directories in the 'root' directory
    #             for dir in [os.path.join(root, d) for d in dirs]:
    #                 os.chmod(dir, mode)

    #             # Iterate over the files in the 'root' directory
    #             for file in [os.path.join(root, f) for f in files]:
    #                 os.chmod(file, mode)
    #     except OSError as err:
    #         print(f"Error: {err}")
    #         sys.exit()  

