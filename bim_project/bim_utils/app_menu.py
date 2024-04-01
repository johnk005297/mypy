#
from log import Logs

class AppMenu:
    __VERSION__ = '1.42e'
    __logger    = Logs().f_logger(__name__)

    def __init__(self):
        self._main_menu  = self.main_menu()
        self._local_menu = self.local_menu()


    def __getattr__(self, item):
        raise AttributeError("AppMenu class has no such attribute: " + item)


    def welcome_info_note(self):
        ''' first note to be displayed '''
        print(f"v{self.__VERSION__}")

    def main_menu(self):
        ''' Help menu of user commands. '''

        _main_menu      = "\nHelp:                                                                                \
                                \n                                                                                \
                                \n   License                                                                      \
                                \n      check lic                       check license                             \
                                \n      get sid                         get serverId                              \
                                \n      apply lic                       apply new license                         \
                                \n      delete lic                      delete active license                     \
                                \n      activate lic                    activate already uploaded license         \
                                \n                                                                                \
                                \n   Databases                                                                    \
                                \n      drop uo                         clean bimeisterdb.UserObjects table       \
                                \n      drop uo -h                      info about UserObjects table              \
                                \n                                                                                \
                                \n   Transfer data                                                                \
                                \n      export om                       export object model                       \
                                \n      import om                       import object model                       \
                                \n      export workflow                 export workflows massively                \
                                \n      export workflow <id1 id2 ...>   export specific workflows only            \
                                \n      import workflow                 import workflows                          \
                                \n      ls workflow                     display workflows(name: id)               \
                                \n      rm workflow                     delete workflows                          \
                                \n      rm files                        clean bim_utils transfer files            \
                                \n                                                                                \
                                \n   User                                                                         \
                                \n      ptoken                          get private token                         \
                                \n      token                           get user access token(Bearer)             \
                                \n      sh                              run terminal command(current host)        \
                                \n      ssh connect                     run terminal command(remote host)         \
                                \n      ls -l                           list current folder content               \
                                \n                                                                                \
                                \n   Docker                                                                       \
                                \n      docker -h                       get a list of available commands          \
                                \n                                                                                \
                                \n   K8S                                                                          \
                                \n      kube -h                         get a list of available commands          \
                                \n                                                                                \
                                \n   Feature Toggle                                                               \
                                \n      ft --list                       display list of features                  \
                                \n      ft [ft_name] [--on/--off]       turn on/off feature                       \
                                \n        example:                                                                \
                                \n        ft Spatium --on                                                         \
                                \n                                                                                \
                                \n   Reports                                                                      \
                                \n      ls report                       get a list of current reports             \
                                \n                                                                                \
                                \n   Main                                                                         \
                                \n      m                               print this menu                           \
                                \n      q                               exit"

        return _main_menu
    

    def local_menu(self):
        ''' Local menu of options which could be executed without authorization procedure. '''

        _local_menu      = "\nHelp:                                                                           \
                                \n                                                                            \
                                \n   User                                                                     \
                                \n      sh                          run terminal command(current host)        \
                                \n      ssh connect                 run terminal command(remote host)         \
                                \n      ls -l                       list current folder content               \
                                \n                                                                            \
                                \n   Docker                                                                   \
                                \n      docker -h                   get a list of available commands          \
                                \n                                                                            \
                                \n   K8S                                                                      \
                                \n      kube -h                     get a list of available commands          \
                                \n                                                                            \
                                \n   Main                                                                     \
                                \n      m                           print this menu                           \
                                \n      q                           exit"        

        return _local_menu


    def get_user_command(self):
        ''' Define what the user would like to do '''

        exit_command = ['q']
        try:
            user_command = input("\nCommand (m for help): ").strip().lower().split()
        except KeyboardInterrupt:
            print('\nKeyboardInterrupt')
            return exit_command
        except Exception as err:
            self.__logger.error(err)
            return exit_command
        else:
            return False if not user_command else user_command
