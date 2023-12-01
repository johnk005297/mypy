#
# Script for work with license and some other small features.
import os
import sys
import time
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
from main_local import main_local
from help_menu import Help
from reports import Reports
import postgre



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
        if not user_command:    # if nothing to check, loop over.
            continue

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


            ''' =============================================================================== MAIN BLOCK =============================================================================== '''

        match user_command:

            case ['m']:
                print(AppMenu_main._main_menu)

            case ['exit'] | ['q'] | ['quit']:
                break   # Close the menu and exit from the script.


                ''' =============================================================================== LICENSE BLOCK =============================================================================== '''

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


                ''' =============================================================================== User objects BLOCK =============================================================================== '''
            
            case ['drop', 'uo']:
                User_main.delete_user_objects(url, token)
            
            case ['drop', 'uo', '-h']:
                print(User_main.delete_user_objects.__doc__)
            

                ''' =============================================================================== TRANSFER DATA BLOCK =============================================================================== '''
            
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


                ''' =============================================================================== USER =============================================================================== '''

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


                ''' =============================================================================== DOCKER =============================================================================== '''

            case ['docker', *_] if not Docker._check_docker:
                print("No docker found in the system.\nHint: Try to run bim_utils using sudo privileges.")
                continue

            case ['docker', '-h'] | ['docker', '--help']:
                print(Docker.docker_menu())

            case ['docker', 'ls']:
                Docker.display_containers(all=False)

            case ['docker', 'ls', '--all']:
                Docker.display_containers(all=True)

            case ['docker', 'logs', '-i', container_id]:
                Docker.get_container_interactive_logs(container_id)

            case ['docker', 'logs', '-f', '--all', *_]:

                if '--tail' in user_command:
                    tail_idx = user_command.index('--tail') + 1
                    try:
                        number = int(user_command[tail_idx])
                    except ValueError:
                        print("--tail must be integer!")
                        continue
                    Docker.get_all_containers_logs(tail=number)

                elif '--days' in user_command:
                    days_idx = user_command.index('--days') + 1
                    try:
                        days = int(user_command[days_idx])
                    except ValueError:
                        print("--days value must be integer!")
                        continue
                    Docker.get_all_containers_logs(days=days)
                else:
                    Docker.get_all_containers_logs()

            case ['docker', 'logs', '-f', *_] if len(user_command) > 3 and '--all' not in user_command:

                # very important to pass arguments as integer value(which comes as str). Otherwise, won't work.
                if '--tail' in user_command:
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

                elif '--days' in user_command:
                    days_idx = user_command.index('--days') + 1
                    try:
                        days = int(user_command[days_idx])
                    except ValueError:
                        print("--days value must be integer!")
                        continue
                    user_command.remove(user_command[days_idx])
                    containers_id = [x for x in user_command[3:] if not x.startswith('-') and len(x) >= 2]
                    Docker.get_container_log(*containers_id, in_file=True, days=days)

                else:
                    containers_id = [x for x in user_command[3:] if not x.startswith('-')]
                    Docker.get_container_log(*containers_id, in_file=True)

            case ['docker', 'logs', *_]:
                if '--tail' in user_command:
                    tail_idx = user_command.index('--tail') + 1
                    try:
                        number = int(user_command[tail_idx])
                    except ValueError:
                        print("--tail must be integer!")
                        continue
                    user_command.remove(user_command[tail_idx])
                    containers_id = [x for x in user_command[2:] if not x.startswith('-') and len(x) >= 2]
                    Docker.get_container_log(*containers_id, tail=number)

                elif '--days' in user_command:
                    days_idx = user_command.index('--days') + 1
                    try:
                        days = int(user_command[days_idx])
                    except ValueError:
                        print("--days value must be integer!")
                        continue
                    user_command.remove(user_command[days_idx])
                    containers_id = [x for x in user_command[2:] if not x.startswith('-') and len(x) >= 2]                        
                    Docker.get_container_log(*containers_id, days=days)

                else:
                    containers_id = [x for x in user_command[2:]]
                    Docker.get_container_log(*containers_id)

            case ['docker', 'ft', '--list']:
                ft_token = Docker.get_ft_token() if not Docker._ft_token else ft_token
                if ft_token:
                    FT.display_features(url, ft_token)

            case ['docker', 'ft'] if len(user_command) == 4:
                feature:str = user_command[2]
                FT.set_feature(url, feature, token, ft_token, is_enabled=(True if user_command[3] == '--on' else False))


                ''' =============================================================================== K8S =============================================================================== '''

            case ['kube', *_] if not K8s._check_k8s:
                print("No kubernetes found in the system.")
                continue

            case ['kube', '--help'] | ['kube', '-h']:
                print(K8s.k8s_menu())
                continue
            
            case ['kube', 'ft', *_]:

                ft_token = K8s.get_ft_token() if not K8s._ft_token else ft_token
                if ft_token:
                    if user_command == ['kube', 'ft', '--list']:
                        FT.display_features(url, ft_token)

                    elif user_command[:2] == ['kube', 'ft']:
                            feature:str = user_command[2]
                            FT.set_feature(url, feature, token, ft_token, is_enabled=(True if user_command[-1] == '--on' else False))
                    else:
                        print("\nCouldn't get FT token. Check the logs.")
                        continue


                ''' =============================================================================== REPORTS =============================================================================== '''
            
            case ['ls', 'report']:
                Repo.display_reports(url, token)

            case ['upload', 'report']:
                Repo.upload_single_report(url, token)
            
            # case ['test', 'report']:
            #     Repo.upload_report(url, token)


            # wildcard pattern if no cases before where matched
            case _:
                print("Unknown command.")






        


        #     ''' =============================================================================== K8S =============================================================================== '''
        # elif isinstance(user_command, tuple) and user_command[0][0] == 'kube':
        #     # Check for Kubernetes on server
        #     if not K8s._check_k8s:
        #         print("No kubernetes found in the system.")
        #         continue

        #     if user_command == ['quit']:
        #         break

        #     if user_command[1] == 'kube help':
        #         print(K8s.k8s_menu())
        #         continue

        #     if 'featureToggle' in user_command[1]:
        #         ft_token = K8s.get_ft_token() if not K8s._ft_token else ft_token

        #     if ft_token:
        #         if user_command[0] == ['kube', 'ft', '--list']:
        #             FT.display_features(url, ft_token)

        #         elif user_command[1] == 'kube set featureToggle':
        #             feature:str = user_command[0][2]
        #             FT.set_feature(url, feature, token, ft_token, is_enabled=(True if user_command[0][-1] == '--on' else False))

        #     else:
        #         print("\nCouldn't get FT token. Check the logs.")
        #         continue




if __name__ == '__main__':
    if len(sys.argv) == 1:
        main()
    elif sys.argv[1] == '--docker' and len(sys.argv) == 2:
        main_local()
    elif sys.argv[1] == '--help' and len(sys.argv) == 2:
        help = Help.options_menu(help)
    elif sys.argv[1] == '--sql-query':
        main_local()



        



