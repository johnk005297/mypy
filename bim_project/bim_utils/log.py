#
import os
import logging
import sys




class Logs:

    def __init__(self):
        self._log_folder:str = "bimUtils_logs"
        self._bimeister_log_folder:str = "bimeister_logs"
        if not os.path.isdir(self._log_folder):
            try:
                os.mkdir(self._log_folder)
            except PermissionError as err:
                print(f"Not enough permissions to create log folder in: {os.getcwd()}\n{err}")
                sys.exit()
            except Exception as err:
                print(f"Couldn't create bimUtils_logs folder in: {os.getcwd()}\n{err}")
                sys.exit()


    def connection_log(self, msg, url=None, method=None, path_url=None, status_code=None):
        message:str = msg
        def return_message(self):
            return message
        return return_message


    def http_connect(self):
        def log_message(self, url):
            message:str = f"Starting new HTTP connection: {url}"
            return message
        return log_message


    def http_response(self):
        def log_message(self, url, method, path_url, status_code):
            message:str = f"{url} \"{method} {path_url} \" {status_code}"
            return message
        return log_message


    def f_logger(self, module_name, logLevel=logging.DEBUG):
        ''' Create a custom logger with file output. '''

        log_file:str = f'{self._log_folder}/{module_name}.log'

        # Create a custom logger
        logger = logging.getLogger(module_name)
        logger.setLevel(logLevel)

        # Create handlers
        f_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        # f_handler.setLevel(logging.DEBUG)

        # Create formatters and add it to handlers
        f_format = logging.Formatter(fmt="%(asctime)s %(levelname)s %(funcName)s(line:%(lineno)d) - %(message)s", datefmt="%d-%b-%y %H:%M:%S")
        f_handler.setFormatter(f_format)

        # Add handlers to the logger
        logger.addHandler(f_handler)

        return logger


    def set_full_access_to_logs(self):
        ''' Need to make bimUtils_logs folder accessible for all users to escape errors at launch. '''

        logs:str = 'bimUtils_logs'
        if os.path.isdir(logs):
            try:
                os.chmod(logs, mode=0o777)
                [os.chmod(f"{logs}/{file}", mode=0o777) for file in os.listdir(logs) if file]
            except PermissionError:
                pass        


# class Logs:   # default configuration for logging

#     def __init__(self):
#         self.bim_utils_log_file:str = f'{os.getcwd()}/bm_utils.log'

    
#     def turn_on_logs(self):

#         logging.basicConfig(filename=self.bim_utils_log_file, level=logging.DEBUG,
#                             format="%(asctime)s %(levelname)s - %(message)s", filemode="a", datefmt='%d-%b-%y %H:%M:%S')



# def main():
#     log = Logs()
#     log.turn_on_logs()


# if __name__ == 'log':
#     main()

