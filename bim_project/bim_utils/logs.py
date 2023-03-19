#

import os
import logging

class Logs:

    def __init__(self):
        self.bim_utils_log_file:str = f'{os.getcwd()}/bm_utils.log'

    
    def turn_on_logs(self):
        if not os.path.isfile(self.bim_utils_log_file):
            logging.basicConfig(filename=self.bim_utils_log_file, level=logging.DEBUG,
                                format="%(asctime)s %(levelname)s - %(message)s", filemode="w", datefmt='%d-%b-%y %H:%M:%S')
        else:
            logging.basicConfig(filename=self.bim_utils_log_file, level=logging.DEBUG,
                                format="%(asctime)s %(levelname)s - %(message)s", filemode="a", datefmt='%d-%b-%y %H:%M:%S')



def main():
    log = Logs()
    log.turn_on_logs()



if __name__ == 'logs':
    main()


