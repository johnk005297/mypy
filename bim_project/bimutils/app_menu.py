import logging
logger = logging.getLogger(__name__)


def main_menu():
    """ Help menu of user commands. """

    _main_menu = "\nHelp:                                                                                               \
                            \n                                                                                          \
                            \n   License                                                                                \
                            \n      check lic                           check license                                   \
                            \n      get sid                             get serverId                                    \
                            \n      apply lic                           apply new license                               \
                            \n      delete lic                          delete active license                           \
                            \n      activate lic                        activate already uploaded license               \
                            \n                                                                                          \
                            \n   Transfer data                                                                          \
                            \n      export om                           export object model                             \
                            \n      import om                           import object model                             \
                            \n      export workflows                    export workflows massively                      \
                            \n      import workflows                    import workflows                                \
                            \n      ls workflows                        display workflows(name: id)                     \
                            \n      rm workflows                        delete workflows                                \
                            \n      rm files                            clean bim_utils transfer files                  \
                            \n                                                                                          \
                            \n   User                                                                                   \
                            \n      ptoken                              get private token                               \
                            \n      token                               get user access token(Bearer)                   \
                            \n      ls                                  list current folder content                     \
                            \n      basic-auth --set                    set basic authentication                        \
                            \n                                                                                          \
                            \n   Feature Toggle                                                                         \
                            \n      ft --list                           display list of features                        \
                            \n        optional: [--enabled/--disabled]  display only enabled/disabled FT                \
                            \n      ft [ft_name] [--on/--off]           turn on/off features                            \
                            \n        example:                                                                          \
                            \n        ft Spatium Bim2d Importbcf --on                                                   \
                            \n                                                                                          \
                            \n   ABAC                                                                                   \
                            \n      abac import                         import attribute-based access control file(s)   \
                            \n                                                                                          \
                            \n   Custom UI                                                                              \
                            \n      apply UI -f [filename]              apply custom user interface                     \
                            \n                                                                                          \
                            \n   Recalculate paths                      perform methods that recalculates               \
                            \n                                          paths for technical objects                     \
                            \n      recalc-paths                                                                        \
                            \n                                                                                          \
                            \n   Templates                                                                              \
                            \n      ls templates                        get list of tempaltes                           \
                            \n      export templates --id \"id1 id2 ...\" export template(s) using id                   \
                            \n      risk-ass -f <file>                  import risk assessment template                 \
                            \n                                                                                          \
                            \n                                                                                          \
                            \n      m                                   print this menu                                 \
                            \n      q                                   exit"

    return _main_menu


class AppMenu:
    __slots__ = ('_main_menu',)
    __version__ = '1.78.96'

    def __init__(self):
        self._main_menu = main_menu()

    def __getattr__(self, item):
        raise AttributeError("AppMenu class has no such attribute: " + item)

    def welcome_info_note(self):
        """ first note to be displayed """
        print(f"v{self.__version__}")

    def get_user_command(self):
        """ Define what the user would like to do """

        exit_command = ['q']
        try:
            user_command = input("\nCommand (m for help): ").strip().rstrip(';').strip().split()
        except KeyboardInterrupt:
            print('\nKeyboardInterrupt')
            return exit_command
        except Exception as err:
            logger.error(err)
            return exit_command
        else:
            return False if not user_command else user_command
