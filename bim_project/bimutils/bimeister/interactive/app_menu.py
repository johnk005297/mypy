import logging
logger = logging.getLogger(__name__)

from __init__ import __version__
from .help_text import HELP_TEXT

class AppMenu:

    def __init__(self):
        self._main_menu = HELP_TEXT

    def __getattr__(self, item):
        raise AttributeError("AppMenu class has no such attribute: " + item)

    def welcome_info_note(self):
        """ first note to be displayed """
        print(f"v{__version__}")

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
