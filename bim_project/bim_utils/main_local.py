#

import argparse
import mdocker
import app_menu
import postgre
import featureToggle

# def main_local():

#     parser = argparse.ArgumentParser(prog="bim_utils", description="This local version designed for getting logs from the containers.")

#     # create sub-parser
#     sub_parser = parser.add_subparsers(help='Sub-command help')   

#     # create the parser for the 'docker' sub-command
#     parser_docker = sub_parser.add_parser('docker', help='Getting available commands for docker containers.')

#     # create the sub-parser for the 'docker' sub-command
#     docker_sub_parser = parser_docker.add_parser('logs', help='Getting logs from the docker container[s].')
#     docker_sub_parser.add_argument('-f', )






#     # subcommand = parser.add_mutually_exclusive_group()
#     docker.add_argument('-f', '--file', help='save logs in a file', action='store_true')
#     docker.add_argument('-ls', '--list', help='display running containers', action='store_true')
#     args = parser.parse_args()
#     print(args)






def run_docker():

    Docker = mdocker.Docker()
    menu   = app_menu.AppMenu()

    while True:    
        user_command = menu.get_user_command()
        match user_command:

            # if nothing to check, loop over.
            case False:
                continue

            # Close the menu and exit from the script.
            case ['exit'] | ['q'] | ['quit']:
                break

            case ['m']:
                print(Docker.docker_menu_local())

            case ['docker', *_] if not Docker._check_docker:
                print("No docker found in the system.\nHint: Try to run bim_utils using sudo privileges.")
                continue

            case ['docker', 'ls']:
                Docker.display_containers(all=False)

            case ['docker', 'ls', '--all']:
                Docker.display_containers(all=True)

            case ['docker', 'logs', '-i', container_id]:
                Docker.get_container_interactive_logs(container_id)

            case ['docker', 'logs', '-f', '--all', *_] if '--tail' in user_command:
                tail_idx = user_command.index('--tail') + 1
                try:
                    number = int(user_command[tail_idx])
                except ValueError:
                    print("--tail must be integer!")
                    continue
                Docker.get_all_containers_logs(tail=number)

            case ['docker', 'logs', '-f', '--all', *_] if '--days' in user_command:
                days_idx = user_command.index('--days') + 1
                try:
                    days = int(user_command[days_idx])
                except ValueError:
                    print("--days value must be integer!")
                    continue
                Docker.get_all_containers_logs(days=days)

            case ['docker', 'logs', '-f', '--all', *_]:
                Docker.get_all_containers_logs()

            case ['docker', 'logs', '-f', _, *_] if '--all' not in user_command and '--tail' in user_command:
                # very important to pass arguments as integer value(which comes as str). Otherwise, won't work.
                tail_idx = user_command.index('--tail') + 1
                try:
                    number = int(user_command[tail_idx])
                except ValueError:
                    print("--tail must be integer!")
                    continue
                # remove tail value so it won't be added to containers_id list.
                user_command.remove(user_command[tail_idx])
                # getting a list of container id to pass in Docker.get_container_log function.                        
                containers_id = [x for x in user_command[3:] if not x.startswith('-') and len(x) >= 2]
                Docker.get_container_log(*containers_id, in_file=True, tail=number)

            case ['docker', 'logs', '-f', _, *_] if '--all' not in user_command and '--days' in user_command:
                days_idx = user_command.index('--days') + 1
                try:
                    days = int(user_command[days_idx])
                except ValueError:
                    print("--days value must be integer!")
                    continue
                user_command.remove(user_command[days_idx])
                containers_id = [x for x in user_command[3:] if not x.startswith('-') and len(x) >= 2]
                Docker.get_container_log(*containers_id, in_file=True, days=days)

            case ['docker', 'logs', '-f', _, *_] if '--all' not in user_command:
                    containers_id = [x for x in user_command[3:] if not x.startswith('-')]
                    Docker.get_container_log(*containers_id, in_file=True)

            case ['docker', 'logs', *_] if '--tail' in user_command:
                tail_idx = user_command.index('--tail') + 1
                try:
                    number = int(user_command[tail_idx])
                except ValueError:
                    print("--tail must be integer!")
                    continue
                user_command.remove(user_command[tail_idx])
                containers_id = [x for x in user_command[2:] if not x.startswith('-') and len(x) >= 2]
                Docker.get_container_log(*containers_id, tail=number)

            case ['docker', 'logs', *_] if '--days' in user_command:
                days_idx = user_command.index('--days') + 1
                try:
                    days = int(user_command[days_idx])
                except ValueError:
                    print("--days value must be integer!")
                    continue
                user_command.remove(user_command[days_idx])
                containers_id = [x for x in user_command[2:] if not x.startswith('-') and len(x) >= 2]                        
                Docker.get_container_log(*containers_id, days=days)

            case ['docker', 'logs', *_]:
                containers_id = [x for x in user_command[2:]]
                Docker.get_container_log(*containers_id)

            case _:
                print("Unknown command.")
                continue

# Function isn't ready.
def run_sql():
    
    pg = postgre.DB()
    pg.exec_query_from_file()




def main_local():
    run_docker()


