#


class AppMenu:
    __VERSION__ = '1.39'

    def __init__(self):
        self._main_menu = self.main_menu()


    def __getattr__(self, item):
        raise AttributeError("AppMenu class has no such attribute: " + item)


    def welcome_info_note(self):
        ''' first note to be displayed '''
        print(f"v{self.__VERSION__}")

    def main_menu(self):
        ''' Help menu of user commands. '''

        _main_menu      = "\nHelp:                                                                    \
                                \n                                                                    \
                                \n   License                                                          \
                                \n      1                   check license                             \
                                \n      2                   get serverId                              \
                                \n      apply lic           apply new license                         \
                                \n      delete lic          delete active license                     \
                                \n      activate lic        activate already uploaded license         \
                                \n                                                                    \
                                \n   Databases                                                        \
                                \n      drop uo             clean bimeisterdb.UserObjects table       \
                                \n      drop uo -h          info about UserObjects table              \
                                \n                                                                    \
                                \n   Transfer data                                                    \
                                \n      om export           export object model                       \
                                \n      om import           import object model                       \
                                \n      workflow export     export workflows                          \
                                \n      workflow import     import workflows                          \
                                \n      workflow ls         display workflows(name: id)               \
                                \n      workflow remove     delete workflows                          \
                                \n      files remove        clean bim_utils transfer files            \
                                \n                                                                    \
                                \n   User                                                             \
                                \n      ptoken              get private token                         \
                                \n      token               get user access token(Bearer)             \
                                \n      sh                  run terminal command(current host)        \
                                \n      ssh connect         run terminal command(remote host)         \
                                \n      ls -l               list current folder content               \
                                \n                                                                    \
                                \n   Docker                                                           \
                                \n      docker -h           get a list of available commands          \
                                \n                                                                    \
                                \n   K8S                                                              \
                                \n      kube -h             get a list of available commands          \
                                \n                                                                    \
                                \n                                                                    \
                                \n   Main                                                             \
                                \n      m                   print this menu                           \
                                \n      q                   exit"
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
            return ['quit']

        if not user_command:
            return False

        # License
        if user_command == ['1']:
            return ['check_license']
        elif user_command == ['2']:
            return ['server_id']
        elif user_command == ['apply', 'lic']:
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
        elif user_command == ['om', 'export']:
            return user_command
        elif user_command == ['workflow', 'export']:
            return user_command
        elif user_command == ['om', 'import']:
            return user_command
        elif user_command == ['workflow', 'import']:
            return user_command
        elif user_command == ['workflow', 'ls']:
            return user_command
        elif user_command == ['workflow', 'remove']:
            return user_command
        elif user_command == ['files', 'remove']:
            return user_command

        # User
        elif user_command == ['token']:
            return user_command
        elif user_command == ['ptoken']:
            return user_command
        elif user_command == ['sh']:
            return user_command
        elif user_command == ['ls', '-l']:
            return user_command
        elif user_command == ['ssh', 'connect']:
            return user_command

        # Docker
        elif user_command[0] == 'docker' and len(user_command) > 1:             # if user command starts with docker and has minimum one more argument
            if user_command == ['docker', '-h'] or user_command == ['docker', '--help']:
                return (user_command, 'docker help')

            elif user_command == ['docker', 'ls', '--all']:
                return (user_command, 'docker container ls -a')

            elif user_command == ['docker', 'ls']:
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
            
            elif user_command == ['docker', 'ft', '--list']:
                return(user_command, 'docker list featureToggle')
            
            elif len(user_command) == 4 and user_command[1] == 'ft':
                return (user_command, 'docker set featureToggle')

        # K8S
        elif user_command[0] == 'kube' and len(user_command) > 1:
            if user_command == ['kube', '-h'] or user_command == ['kube', '--help']:
                return (user_command, 'kube help')

            elif user_command == ['kube', 'ft', '--list']:
                return (user_command, 'kube list featureToggle')

            elif len(user_command) == 4 and user_command[1] == 'ft':
                return (user_command, 'kube set featureToggle')
        
        # Reports
        elif user_command == ['report', 'ls'] and len(user_command) == 2:
            return(user_command, 'report ls')
        elif user_command == ['report', 'upload'] and len(user_command) == 2:
            return(user_command, 'report upload')
        elif user_command == ['report', 'test'] and len(user_command) == 2:
            return(user_command, 'report test')


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
