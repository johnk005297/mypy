#


class AppMenu:
    version = '1.34f'

    def __init__(self):
        self._main_menu = self.main_menu()


    def __getattr__(self, item):
        raise AttributeError("AppMenu class has no such attribute: " + item)


    def welcome_info_note(self):
        ''' first note to be displayed '''
        print(f"\nv{self.version}    \
                \nnote: applicable with BIM version 101 and higher.")

    def main_menu(self):
        ''' Help menu of user commands. '''

        _main_menu      = "\nHelp:                                                                    \
                                \n                                                                    \
                                \n   License                                                          \
                                \n      1                   check license                             \
                                \n      2                   get serverId                              \
                                \n      apply new lic       apply new license                         \
                                \n      delete lic          delete active license                     \
                                \n      activate lic        activate already uploaded license         \
                                \n                                                                    \
                                \n   Databases                                                        \
                                \n      drop uo             clean bimeisterdb.UserObjects table       \
                                \n      drop uo -h          info about UserObjects table              \
                                \n                                                                    \
                                \n   Transfer data                                                    \
                                \n      export om           export object model                       \
                                \n      export wf           export workflows                          \
                                \n      import om           import object model                       \
                                \n      import wf           import workflows                          \
                                \n      list wf             display workflows(name: id)               \
                                \n      delete wf           delete workflows                          \
                                \n      rm files            clean bim_utils transfer files            \
                                \n                                                                    \
                                \n   User                                                             \
                                \n      token               get user access token                     \
                                \n      sh                  run terminal command(current host)        \
                                \n      ssh connect         run terminal command(remote host)         \
                                \n      ls -l               list current folder content               \
                                \n                                                                    \
                                \n   Docker                                                           \
                                \n      docker -h           get a list of available commands          \
                                \n                                                                    \
                                \n   Main                                                             \
                                \n      m                   print this menu                           \
                                \n      q                   exit"
                                # \n   c  connect to another server                    \  # Need to figure out the way to add connect to another server without re-running the script
        return _main_menu


    def get_user_command(self):
        ''' Define what the user would like to do '''

        user_command = input("\nCommand (m for help): ").strip().lower().split()

        if not user_command:
            return False

        # License
        if user_command == ['1']:
            return ['check_license']
        elif user_command == ['2']:
            return ['server_id']
        elif user_command == ['apply', 'new', 'lic']:
            return ['apply_license']
        elif user_command == ['delete', 'lic']:
            return ['delete_active_license']
        elif user_command == ['activate', 'lic']:
            return ['activate_license']

        # Databases
        elif user_command == ['drop', 'uo']:
            return user_command
        elif user_command == ['drop', 'uo', '-h']:
            return user_command
        
        # Transfer data
        elif user_command == ['export', 'om']:
            return user_command
        elif user_command == ['export', 'wf']:
            return user_command
        elif user_command == ['import', 'om']:
            return user_command
        elif user_command == ['import', 'wf']:
            return user_command
        elif user_command == ['list', 'wf']:
            return user_command
        elif user_command == ['delete', 'wf']:
            return user_command
        elif user_command == ['rm', 'files']:
            return user_command

        # User
        elif user_command == ['token']:
            return user_command
        elif user_command == ['sh']:
            return user_command
        elif user_command == ['ls', '-l']:
            return user_command
        elif user_command == ['ssh', 'connect']:
            return user_command

        # Docker
        elif user_command[0] == 'docker' and len(user_command) > 1:             # if user command starts with docker and has minimum one more argument
            if user_command[1] == '-h':
                return (user_command, 'docker help')

            elif user_command[1:] == ['ls', '--all']:
                return (user_command, 'docker container ls -a')

            elif user_command[1] == 'ls':
                return (user_command, 'docker container ls')

            elif user_command[1] == 'logs' and len(user_command) > 2:           # if user command starts with 'docker logs'

                if user_command[2] == '-i' and len(user_command) == 4:          # if user command starts with 'docker logs -i'
                    return (user_command, 'docker logs -i')

                elif user_command[2] == '-f' and len(user_command) > 3:         # if user command starts with 'docker logs -f'
                    if '--all' in user_command:                                 
                        return (user_command, 'docker logs -f --all')
                    else:
                        return (user_command, 'docker logs -f')
                else:                                                           # if user command is 'docker logs' + further arguments
                    return (user_command, 'docker logs')

        # Main
        elif user_command == ['m']:
            return ['main_menu']
        elif user_command == ['q']:
            return ['quit']
        
        # Exceptions
        else:
            print('Unknown command.')
            return False



        ### To do list ###
        # ssh -o StrictHostKeyChecking=no localadmin@std-h5.dev.bimeister.io <command>
        # elif user_command == 'c':
        #     return 'connect_to_another_server'
