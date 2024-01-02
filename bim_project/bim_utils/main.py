#
# Script for work with license and some other small features.
import os
import sys
import time
from typing import Any
import app_menu
import auth
import user
import license
import export_data
import import_data
from tools import Folder, File, Tools
import featureToggle
import mdocker
import mk8s
import main_local
from help_menu import Help
from reports import Reports
import postgre
from log import Logs



def main():

    AppMenu_main     = app_menu.AppMenu()
    Auth             = auth.Auth()
    User_main        = user.User()
    License_main     = license.License()
    Export_data_main = export_data.Export_data()
    Import_data_main = import_data.Import_data()
    Docker           = mdocker.Docker()
    K8s              = mk8s.K8S(namespace='bimeister')
    FT               = featureToggle.FeatureToggle()
    Repo             = Reports()



# ---------------------------------------------------------
#   TEST ZONE       LOBBY
# ---------------------------------------------------------

    




# ---------------------------------------------------------
#
# ---------------------------------------------------------


    AppMenu_main.welcome_info_note()
    if not Auth.establish_connection():  # if connection was not established, do not continue
        return False

    url, token, username, password = Auth.url, Auth.token, Auth.username, Auth.password


    while True:
        user_command = AppMenu_main.get_user_command()

        # ''' Check user privileges for everything related in the tuple below. '''
        # if user_command in (
        #                  ['check_license']
        #                 ,['server_id']
        #                 ,['apply_license']
        #                 ,['delete_active_license']
        #                 ,['activate_license']
        #                 ,['export', 'wf']                   # export workFlows
        #                 ,['export', 'om']                   # export object model
        #                 ,['list', 'wf']                     # display workFlows
        #                 ,['delete', 'wf']                   # delete workFlows
        #                 ,['import', 'wf']                   # import workFlows
        #                 ,['import', 'om']                   # import object model
        #                 ):
        #     if not License_main.privileges_checked and not User_main.check_user_permissions(url, token, username, password, License_main._permissions_to_check) and not User_main._License_server_exception:

        #         # Create/activate user
        #         Auth_superuser = auth.Auth(username='johnny_mnemonic', password='Qwerty12345!') # Create Auth class instance for new user
        #         try:
        #             # License_main.privileges_granted, superuser = User_main.create_or_activate_superuser(url, token, Auth_superuser.username, Auth_superuser.password)
        #             superuser = User_main.create_or_activate_superuser(url, token, Auth_superuser.username, Auth_superuser.password)
        #             License_main.privileges_granted = True
        #         except TypeError:
        #             continue
        #         # Create system role
        #         su_system_role_id = User_main.create_system_role(url, token)
        #         # Add system role to created user
        #         User_main.add_system_role_to_user(url, token, superuser['id'], superuser['userName'], su_system_role_id)
        #         # Save data about current user we are working under
        #         initial_user = User_main.get_current_user(url, token)
        #         # Add created role to current user
        #         Auth_superuser.providerId = Auth.get_local_providerId(url)  # getting provider id for created user for logon
        #         Auth_superuser.get_user_access_token(url, Auth_superuser.username, Auth_superuser.password, Auth_superuser.providerId) # logging in under superuser account  
        #         # Add system role to initial user we connected
        #         User_main.add_system_role_to_user(url, Auth_superuser.token, initial_user['id'], username, su_system_role_id)


            #    ''' =============================================================================== MAIN BLOCK ======================================================================================= '''

        match user_command:

            # if nothing to check, loop over.
            case False:
                continue

            case ['m']:
                print(AppMenu_main._main_menu)

            # Close the menu and exit from the script.
            case ['exit'] | ['q'] | ['quit']:
                break


            #    ''' =============================================================================== LICENSE BLOCK ==================================================================================== '''

            case ['check', 'lic']:
                License_main.display_licenses(url, token, username, password)

            case ['get', 'sid']:
                response = License_main.get_serverID(url, token)
                print("\n   - serverId:", response)

            case ['apply', 'lic']:
                License_main.post_license(url, token, username, password)
                # license_id:str = License_main.post_license_new(url, token, username, password)
                # License_main.put_license(url, token, license_id=license_id[0]) if license_id else print("Post license wasn't successful. Check the logs.")

            case  ['delete', 'lic']:
                License_main.delete_license(url, token, username, password)

            case ['activate', 'lic']:
                license_id:str = input("Enter license id: ").strip()
                License_main.put_license(url, token, username, password, license_id)


            #    ''' =============================================================================== User objects BLOCK =============================================================================== '''
            
            case ['drop', 'uo']:
                User_main.delete_user_objects(url, token)
            
            case ['drop', 'uo', '-h']:
                print(User_main.delete_user_objects.__doc__)
            

            #    ''' =============================================================================== TRANSFER DATA BLOCK ============================================================================== '''
            
            # Export data
            case ['export', 'om'] | ['ls', 'workflow'] | ['rm', 'workflow'] | ['export', 'workflow', *_]:

                if Export_data_main.is_first_launch_export_data:
                    Folder.create_folder(os.getcwd(), Export_data_main._transfer_folder)
                    time.sleep(0.1)
                    Folder.create_folder(os.getcwd() + '/' + Export_data_main._transfer_folder, Export_data_main._workflows_folder)
                    time.sleep(0.1)
                    Folder.create_folder(os.getcwd() + '/' + Export_data_main._transfer_folder, Export_data_main._object_model_folder)
                    time.sleep(0.1)
                    Export_data_main.is_first_launch_export_data = False

                
                if user_command == ['export', 'om']:
                    Export_data_main.export_server_info(url, token)
                    Export_data_main.get_object_model(Export_data_main._object_model_file, Auth.url, Auth.token)

                elif user_command[:2] == ['export', 'workflow']:

                    Export_data_main.export_server_info(url, token)
                    if len(user_command) == 2:
                        Export_data_main.export_workflows(url, token, at_once=True)
                    else:
                        args = user_command[2:]
                        Export_data_main.export_workflows(url, token, *args, at_once=False)

                elif user_command == ['ls', 'workflow']:
                    Export_data_main.display_list_of_workflowsName_and_workflowsId(url, token)
                elif user_command == ['rm', 'workflow']:
                    Export_data_main.delete_workflows(url, token)                

            # Import data
            case ['import', 'workflow']:
                Import_data_main.import_workflows(url, token)

            case ['import', 'om']:
                Import_data_main.import_object_model(url, token)

            case ['rm', 'files']:
                Folder.clean_folder(f"{os.getcwd()}/{Export_data_main._transfer_folder}/{Export_data_main._object_model_folder}")
                Folder.clean_folder(f"{os.getcwd()}/{Export_data_main._transfer_folder}/{Export_data_main._workflows_folder}")
                File.remove_file(f"{os.getcwd()}/{Export_data_main._transfer_folder}/export_server.info")                


            #    ''' =============================================================================== USER =============================================================================== '''

            case ['ptoken']:
                private_token = Auth.get_private_token(url, token)
                print(f"\n{private_token}")

            case ['token']:
                user_access_token = Auth.get_user_access_token(url, username, password, Auth.providerId)
                print(f"\n{user_access_token}")

            case ['sh']:
                Tools.run_terminal_command()
            
            case ['ls', '-l']:
                Tools.run_terminal_command(Folder.get_content())
            
            case ['ssh', 'connect']:
                connection_data:list = input("Enter 'remote host' and 'username' separated by a space: ").strip().split()
                try:
                    Tools.connect_ssh(connection_data[0], connection_data[1])
                except IndexError:
                    print("Incorrect data. Can't connect.")
                    continue


            #    ''' =============================================================================== DOCKER =============================================================================== '''

            case ['docker', *_] if not Docker.get_docker_client():
                print("No docker found in the system.\nHint: Try to run this tool using sudo privileges, or check for 'docker' group of the current user.")
                continue

            case ['docker', '-h'|'--help']:
                print(Docker.docker_menu())

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


            #    ''' =============================================================================== K8S ============================================================================================== '''

            case ['kube', *_] if not K8s.get_kube_config():
                print("Couldn't locate K8S config file. No access to kube API. Check the log.")
                continue

            case ['kube', '-h'|'--help']:
                print(K8s.k8s_menu())
            
            case ['kube', 'ns']:
                K8s.display_namespaces()
            
            case ['kube', 'pods'|'po'|'pod']:
                K8s.display_pods()
            
            case ['kube', 'logs', '-f', '--all', *_] if '--tail' in user_command:
                namespace = False
                if '-n' in user_command:
                    namespace_idx = user_command.index('-n') + 1
                    namespace = user_command[namespace_idx]
                tail_idx = user_command.index('--tail') + 1
                try:
                    number = int(user_command[tail_idx])
                except ValueError:
                    print("--tail must be integer!")
                    continue
                K8s.get_all_pods_log(tail=number) if not namespace else K8s.get_all_pods_log(namespace=namespace, tail=number)
            
            case ['kube', 'logs', '-f', '--all', *_]:
                namespace = False
                if '-n' in user_command:
                    namespace_idx = user_command.index('-n') + 1
                    namespace = user_command[namespace_idx]
                K8s.get_all_pods_log() if not namespace else K8s.get_all_pods_log(namespace=namespace)


            #    ''' =============================================================================== Feature Toggle =================================================================================== '''

            case ['ft', *_] if not K8s.get_kube_config() and not Docker.get_docker_client():
                print("No Kubernets or Docker has been found on the localhost. Check the logs.")
                continue

            case ['ft', _, *_]:
                COS = FT.define_COS()

                if COS == 'K8S':
                    ft_token = K8s.get_ft_token() if not K8s._ft_token else ft_token
                    if ft_token:
                        if user_command == ['ft', '--list']:
                            FT.display_features(url, ft_token)
                        elif len(user_command) == 3 and user_command[-1] in ('--on', '--off'):
                            feature:str = user_command[1]
                            ft_list:list = FT.get_features(url, ft_token)
                            if feature in ft_list:
                                try:
                                    FT.set_feature(url, feature, token, ft_token, is_enabled=(True if user_command[-1] == '--on' else False))
                                except UnboundLocalError as err:
                                    print(err)
                                    continue
                                except Exception:
                                    print("Unpredictable behaviour in k8s set feature.")
                            else:
                                print("Incorrect FT name.")
                elif COS == 'Docker':
                    ft_token = Docker.get_ft_token() if not Docker._ft_token else ft_token
                    if ft_token:
                        if user_command == ['ft', '--list']:
                            FT.display_features(url, ft_token)
                        elif len(user_command) == 3 and user_command[-1] in ('--on', '--off'):
                            feature:str = user_command[1]
                            ft_list:list = FT.get_features(url, ft_token)
                            if feature in ft_list:
                                try:
                                    FT.set_feature(url, feature, token, ft_token, is_enabled=(True if user_command[-1] == '--on' else False))
                                except UnboundLocalError as err:
                                    print(err)
                                    continue
                                except Exception:
                                    print("Unpredictable behaviour in docker set feature.")
                            else:
                                print("Incorrect FT name.")

                else:
                    print("Unexpected error occured. Check the logs.")


            #    ''' =============================================================================== REPORTS ========================================================================================== '''
            
            case ['ls', 'report']:
                Repo.display_reports(url, token)


            # wildcard pattern if no cases before where matched
            case _:
                print("Unknown command.")


def enable_history_input():
    # Block for users input. Need for ability to have history of user's inputs.
    if Tools.is_windows():
        import pyreadline3
    else:
        import readline



if __name__ == '__main__':

    enable_history_input()
    if len(sys.argv) == 1:
        main()
    elif sys.argv[1] == '--docker' and len(sys.argv) == 2:
        main_local.run_docker()
    elif sys.argv[1] == '--help' and len(sys.argv) == 2:
        help = Help.options_menu(help)
    elif sys.argv[1] == '--sql-query':
        main_local()
    Logs().set_full_access_to_logs()


        



