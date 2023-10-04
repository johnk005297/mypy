#
import os
import logging




class Logs:


    def __init__(self):
        self.log_folder:str = "bimUtils_logs"
        if not os.path.isdir(self.log_folder):
            os.mkdir(self.log_folder)


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

        log_file:str = f'{self.log_folder}/{module_name}.log'

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

