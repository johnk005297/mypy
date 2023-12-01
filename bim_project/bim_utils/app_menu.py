#


class AppMenu:
    __VERSION__ = '1.40d'

    def __init__(self):
        self._main_menu = self.main_menu()


    def __getattr__(self, item):
        raise AttributeError("AppMenu class has no such attribute: " + item)


    def welcome_info_note(self):
        ''' first note to be displayed '''
        print(f"v{self.__VERSION__}")

    def main_menu(self):
        ''' Help menu of user commands. '''

        _main_menu      = "\nHelp:                                                                            \
                                \n                                                                            \
                                \n   License                                                                  \
                                \n      check lic                   check license                             \
                                \n      get sid                     get serverId                              \
                                \n      apply lic                   apply new license                         \
                                \n      delete lic                  delete active license                     \
                                \n      activate lic                activate already uploaded license         \
                                \n                                                                            \
                                \n   Databases                                                                \
                                \n      drop uo                     clean bimeisterdb.UserObjects table       \
                                \n      drop uo -h                  info about UserObjects table              \
                                \n                                                                            \
                                \n   Transfer data                                                            \
                                \n      export om                   export object model                       \
                                \n      import om                   import object model                       \
                                \n      export workflow             export workflows massively                \
                                \n      export workflow <id...>     export specific workflows only            \
                                \n      import workflow             import workflows                          \
                                \n      ls workflow                 display workflows(name: id)               \
                                \n      rm workflow                 delete workflows                          \
                                \n      rm files                    clean bim_utils transfer files            \
                                \n                                                                            \
                                \n   User                                                                     \
                                \n      ptoken                      get private token                         \
                                \n      token                       get user access token(Bearer)             \
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
                                \n   Reports                                                                  \
                                \n      report ls                   get a list of current reports             \
                                \n                                                                            \
                                \n   Main                                                                     \
                                \n      m                           print this menu                           \
                                \n      q                           exit"
                                # \n   Reports                                                          \
                                # \n      report ls           get a list of current reports             \
                                # \n      report upload       upload report template                    \
                                # \n      report test         test option(do not use)                   \
        return _main_menu


    def get_user_command(self):
        ''' Define what the user would like to do '''

        try:
            user_command = input("\nCommand (m for help): ").strip().lower().split()
        except KeyboardInterrupt:
            print('\nInterrupted by the user.')
            return ['q']
        except Exception:
            return ['q']
        else:
            return False if not user_command else user_command
