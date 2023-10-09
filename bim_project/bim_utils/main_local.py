#

import argparse
import mdocker
import app_menu
import postgre

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
    menu_main_local = app_menu.AppMenu()

    while True:
        user_command = menu_main_local.get_user_command()

        if not user_command:    # if nothing to check, loop over.
            continue
        elif isinstance(user_command, tuple) and user_command[0][0] == 'docker':
            if not Docker._check_docker:
                print("No docker found in the system.")
                return False

        if user_command == ['quit']:
            break

        elif user_command == ['main_menu']:
            print(Docker.docker_menu())

        elif user_command[1] == 'docker container ls -a':
            Docker.display_containers(all=True)

        elif user_command[1] == 'docker container ls':
            Docker.display_containers(all=False)

        elif user_command[1] == 'docker logs -i':
            container_id = user_command[0][3]
            Docker.get_container_interactive_logs(container_id)

        elif user_command[1] == 'docker logs -f':

            # very important to pass arguments as integer value(which comes as str). Otherwise, won't work.
            if '--tail' in user_command[0]:
                containers_id = [x for x in user_command[0][3:] if not x.startswith('-') and len(x) > 3]        # getting a list of container id to pass in Docker.get_container_log function.
                tail_idx = user_command[0].index('--tail') + 1
                Docker.get_container_log(*containers_id, in_file=True, tail=int(user_command[0][tail_idx]))

            elif '--days' in user_command[0]:
                containers_id = [x for x in user_command[0][3:] if not x.startswith('-') and len(x) > 3]
                days_idx = user_command[0].index('--days') + 1
                Docker.get_container_log(*containers_id, in_file=True, days=int(user_command[0][days_idx]))

            else:
                containers_id = [x for x in user_command[0][3:]]
                Docker.get_container_log(*containers_id, in_file=True)

        elif user_command[1] == 'docker logs -f --all':
            if '--tail' in user_command[0]:
                containers_id = [x for x in user_command[0][3:] if not x.startswith('-') and len(x) > 3]        # getting a list of container id to pass in Docker.get_container_log function.
                tail_idx = user_command[0].index('--tail') + 1
                Docker.get_all_containers_logs(*containers_id, tail=int(user_command[0][tail_idx]))

            elif '--days' in user_command[0]:
                containers_id = [x for x in user_command[0][3:] if not x.startswith('-') and len(x) > 3]
                days_idx = user_command[0].index('--days') + 1
                Docker.get_all_containers_logs(*containers_id, days=int(user_command[0][days_idx]))

            else:
                Docker.get_all_containers_logs()

        elif user_command[1] == 'docker logs':
            if '--tail' in user_command[0]:
                containers_id = [x for x in user_command[0][2:] if not x.startswith('-') and len(x) > 3]        # getting a list of container id to pass in Docker.get_container_log function.
                tail_idx = user_command[0].index('--tail') + 1
                Docker.get_container_log(*containers_id, tail=int(user_command[0][tail_idx]))

            elif '--days' in user_command[0]:
                containers_id = [x for x in user_command[0][2:] if not x.startswith('-') and len(x) > 3]
                days_idx = user_command[0].index('--days') + 1
                Docker.get_container_log(*containers_id, days=int(user_command[0][days_idx]))

            else:
                containers_id = [x for x in user_command[0][2:]]
                Docker.get_container_log(*containers_id)


def run_sql():
    
    pg = postgre.DB()
    pg.exec_query_from_file()




def main_local():

    run_sql()
    

    # if "condition for docker":
    #     run_docker()

    # elif "condition for sql":
    #     run_sql()

    # else:
    #     pass