#

class Test:
    def get_user_command(self):
            ''' Define what the user would like to do '''

            user_command = input("\nCommand (m for help): ").strip().lower().split()

            if not user_command:
                return False

            match user_command:

                # License
                case ['1']:
                    print(['check_license'])
                case ['2']:
                    print(['server_id'])
                case ['apply', 'new', 'lic']:
                    print(['apply_license'])
                case ['delete', 'lic']:
                    print(['delete_active_license'])
                case ['activate', 'lic']:
                    print(['activate_license'])

                # Databases
                case ['drop', 'uo']:
                    print(user_command)
                case ['drop', 'uo', '-h']:
                    print(user_command)
            
                # Transfer data
                case ['exp', 'om']:
                    print(user_command)
                case ['exp', 'wf']:
                    print(user_command)
                case ['imp', 'om']:
                    print(user_command)
                case ['imp', 'wf']:
                    print(user_command)
                case ['list', 'wf']:
                    print(user_command)
                case ['del', 'wf']:
                    print(user_command)
                case ['rm', 'files']:
                    print(user_command)

                # User
                case ['token']:
                    print(user_command)
                case ['sh']:
                    print(user_command)
                case ['ls', '-l']:
                    print(user_command)
                case ['ssh', 'connect']:
                    print(user_command)



                case ['docker', '-h']:
                    print(user_command, 'docker help')                
                case ['docker', 'ls', '--all']:
                    print(user_command, 'docker container ls -a')
                case ['docker', 'ls']:
                    print(user_command, 'docker container ls')
                case ['docker', 'logs', '-f', '--all']:
                    print(user_command, 'docker logs -f --all')
                case ['docker', 'logs', *value] if value and value != ['--all']:
                    print(user_command, 'docker logs')

                
                



            # # Docker
            # if user_command[0] == 'docker' and len(user_command) > 1:             # if user command starts with docker and has minimum one more argument
            #     if user_command[1] == '-h':
            #         print (user_command, 'docker help')

            #     elif user_command[1:] == ['ls', '--all']:
            #         print (user_command, 'docker container ls -a')

            #     elif user_command[1] == 'ls':
            #         print (user_command, 'docker container ls')

            #     elif user_command[1] == 'logs' and len(user_command) > 2:           # if user command starts with 'docker logs'

            #         if user_command[2] == '-i' and len(user_command) == 4:          # if user command starts with 'docker logs -i'
            #             print (user_command, 'docker logs -i')

            #         elif user_command[2] == '-f' and len(user_command) > 3:         # if user command starts with 'docker logs -f'
            #             if '--all' in user_command:                                 
            #                 print (user_command, 'docker logs -f --all')
            #             else:
            #                 print (user_command, 'docker logs -f')
            #         else:                                                           # if user command is 'docker logs' + further arguments
            #             print (user_command, 'docker logs')

                # Main
                case ['m']:
                    print (['main_menu'])
                case ['q']:
                    print (['quit'])
                
                # Exceptions
                case _:
                    print('Unknown command.')
                    return False
            

T = Test()


T.get_user_command()