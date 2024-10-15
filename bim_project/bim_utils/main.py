#
# Script for work with license and some other small features.
import os
import sys
import app_menu
import auth
import user
import license
import argparse
import export_data
import import_data
import postgre
import featureToggle
import mdocker
import mk8s
import vsphere
import git
import re
from tools import Folder, File, Tools
from reports import Reports
from log import Logs


def main(local=False):

    AppMenu_main     = app_menu.AppMenu()
    Auth             = auth.Auth()
    User_main        = user.User()
    License_main     = license.License()
    Export_data = export_data.Export_data()
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
    if not local and not Auth.establish_connection():  # if connection was not established, do not continue
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

            case ['m'] if not local:
                print(AppMenu_main._main_menu)
            
            case ['m'] if local:
                print(AppMenu_main._local_menu)

            # Close the menu and exit from the script.
            case ['exit'|'q'|'quit']:
                break

            #    ''' =============================================================================== LICENSE BLOCK ==================================================================================== '''

            case ['check', 'lic'] if not local:
                License_main.display_licenses(url, token, username, password)

            case ['get', 'sid'] if not local:
                response = License_main.get_serverID(url, token)
                print("\n   - serverId:", response)

            case ['apply', 'lic'] if not local:
                License_main.post_license(url, token, username, password)
                # license_id:str = License_main.post_license_new(url, token, username, password)
                # License_main.put_license(url, token, license_id=license_id[0]) if license_id else print("Post license wasn't successful. Check the logs.")

            case  ['delete', 'lic'] if not local:
                License_main.delete_license(url, token, username, password)

            case ['activate', 'lic'] if not local:
                license_id:str = input("Enter license id: ").strip()
                License_main.put_license(url, token, username, password, license_id)


            #    ''' =============================================================================== User objects BLOCK =============================================================================== '''
            
            case ['drop', 'uo'] if not local:
                User_main.delete_user_objects(url, token)
            
            case ['drop', 'uo', '-h'] if not local:
                print(User_main.delete_user_objects.__doc__)
            

            #    ''' =============================================================================== TRANSFER DATA BLOCK ============================================================================== '''

            # Export data
            case ['export', 'om'] if not local:
                if Export_data.is_first_launch_export_data:
                    Export_data.create_folders_for_export_files()
                if user_command == ['export', 'om']:
                    Export_data.export_server_info(url, token)
                    Export_data.get_object_model(Export_data._object_model_file, Auth.url, Auth.token)                

            case ['ls', 'workflows', *_] | ['export', 'workflows', *_] | ['rm', 'workflows', *_] if not local:
                if user_command == ['ls', 'workflows', '--help'] or user_command == ['ls', 'workflows', '-h']:
                    Export_data.help_function(ls=True)
                    continue
                if user_command == ['export', 'workflows', '--help'] or user_command == ['export', 'workflows', '-h']:
                    Export_data.help_function(export=True)
                    continue
                if user_command == ['rm', 'workflows', '--help'] or user_command == ['rm', 'workflows', '-h']:
                    Export_data.help_function(remove=True)
                    continue                
                if Export_data.is_first_launch_export_data:
                    Export_data.create_folders_for_export_files()
                args = user_command[2:]
                # at the beginning and at the end of the line we cut the quotation marks with slicing
                startswith = re.search('--startswith=".+"', ' '.join(args)).group().split('=')[1][1:-1] if re.search('--startswith=".+"', ' '.join(args)) else ''
                search_for = re.search('--search=".+"', ' '.join(args)).group().split('=')[1][1:-1] if re.search('--search=".+"', ' '.join(args)) else ''
                wf_id_array = re.search('--id=".+"', ' '.join(args)).group().split('=')[1] if re.search('--id=".+"', ' '.join(args)) else ''
                wf_id_array = re.sub(r"\"", "", wf_id_array).split()

                if wf_id_array and user_command[:2] == ['export', 'workflows']:
                    Export_data.export_workflows_by_choice(url, token, wf_id_array)
                    continue             
                workflows = Export_data.define_needed_workflows(url, token, args, startswith=startswith, search_for=search_for)
                if not workflows:
                    continue
                if user_command[:2] == ['export', 'workflows']:
                    Export_data.export_server_info(url, token)
                    Export_data.export_workflows_at_once(url, token, workflows)
                elif user_command[:2] == ['ls', 'workflows']:
                    Export_data.display_list_of_workflowsName_and_workflowsId(workflows)

                elif user_command[:2] == ['rm', 'workflows']:
                    workflows = Export_data.define_needed_workflows(url, token, args, startswith=startswith, search_for=search_for)
                    Export_data.delete_workflows(url, token, workflows)

            # Import data
            case ['import', 'workflows'] if not local:
                Import_data_main.import_workflows(url, token)

            case ['import', 'om'] if not local:
                Import_data_main.import_object_model(url, token)

            case ['rm', 'files'] if not local:
                Folder.clean_folder(f"{os.getcwd()}/{Export_data._transfer_folder}/{Export_data._object_model_folder}")
                Folder.clean_folder(f"{os.getcwd()}/{Export_data._transfer_folder}/{Export_data._workflows_folder}")
                File.remove_file(f"{os.getcwd()}/{Export_data._transfer_folder}/export_server.info")


            #    ''' =============================================================================== USER =============================================================================== '''

            case ['ptoken'] if not local:
                private_token = Auth.get_private_token(url, token)
                print(f"\n{private_token}")

            case ['token'] if not local:
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

            case ['docker', *_] if not Docker.check_docker():
                print("Error: No docker found in the system, or current user doesn't have accesss to it.")
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
                namespace = K8s.check_args_for_namespace(user_command[3:])
                tail_idx = user_command.index('--tail') + 1
                try:
                    number = int(user_command[tail_idx])
                except ValueError:
                    print("--tail must be integer!")
                    continue
                K8s.get_all_pods_log(tail=number) if not namespace else K8s.get_all_pods_log(namespace=namespace, tail=number)

            case ['kube', 'logs', '-f', '--all', *_]:
                namespace = K8s.check_args_for_namespace(user_command[3:])
                K8s.get_all_pods_log() if not namespace else K8s.get_all_pods_log(namespace=namespace)
            
            case ['kube', 'logs', '-f', *_] if '--all' not in user_command and '--pods' in user_command:
                namespace = K8s.check_args_for_namespace(user_command[3:])
                if namespace:
                    ns_idx = user_command.index('-n') + 1
                    user_command.remove(user_command[ns_idx])
                if '--tail' in user_command:
                    tail_idx = user_command.index('--tail') + 1
                    try:
                        number = int(user_command[tail_idx])
                        user_command.remove(user_command[tail_idx])
                    except ValueError:
                        print("--tail must be integer!")
                        continue
                    pods = tuple(pod for pod in user_command[3:] if not pod.startswith('-'))
                    K8s.get_pod_log(*pods, tail=number) if not namespace else K8s.get_pod_log(*pods, namespace=namespace, tail=number)
                else:
                    pods = tuple(pod for pod in user_command[3:] if not pod.startswith('-'))
                    K8s.get_pod_log(*pods) if not namespace else K8s.get_pod_log(*pods, namespace=namespace)                    


            #    ''' =============================================================================== Feature Toggle =================================================================================== '''

            case ['ft', *_] if not local and not K8s.get_kube_config() and not Docker.check_docker():
                print("No Kubernets or Docker has been found on the localhost. Check the logs.")
                continue

            case ['ft', _, *_] if not local:
                COS = FT.define_COS()

                if COS == 'K8S':
                    ft_token = K8s.get_ft_token() if not K8s._ft_token else ft_token
                    if ft_token:
                        if user_command == ['ft', '--list']:
                            FT.display_features(url, ft_token)
                        elif len(user_command) == 3 and user_command[-1] in ('--on', '--off'):
                            feature: str = user_command[1].lower()
                            ft_list: list = FT.get_features(url, ft_token)
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
                            feature: str = user_command[1].lower()
                            ft_list: list = FT.get_features(url, ft_token)
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

            case ['ls', 'report'] if not local:
                Repo.display_reports(url, token)

            # wildcard pattern if no cases before where matched
            case _:
                print("Unknown command.")


def enable_history_input():
    ''' Function provides an opportunity to have access of input history. '''
    if Tools.is_windows():
        import pyreadline3
    else:
        import readline


if __name__ == '__main__':
    enable_history_input()
    parser = argparse.ArgumentParser(prog='bim_utils', description='\'Frankenstein\' CLI for work with licenses, workflows, featureToggles, K8S/Docker logs, etc.')
    parser.add_argument('--version', required=False, action="store_true")
    subparser = parser.add_subparsers(dest='command', help='Run without arguments for standart use.')
    parser.add_argument('--local', required=False, action="store_true", help='Execute script with locally available options on the current host.')
    vcenter = subparser.add_parser('vsphere', help='Performing operations with vSphere API.')
    vcenter.add_argument('-u', '--user', required=False)
    vcenter.add_argument('-p', '--password', required=False)
    vcenter.add_argument('--startswith', required=False, help='Filter VM by first letters of the name.')
    vcenter.add_argument('--exclude-vm', type=str, nargs='+', required=False, help='A list of VMs to be excluded from the reboot OS.')
    vcenter_options = vcenter.add_mutually_exclusive_group(required=True)
    vcenter_options.add_argument('--restart-all-vm', required=False, action="store_true")
    vcenter_options.add_argument('--list-vm', required=False, action="store_true")
    user_obj = subparser.add_parser('drop-UO', help='Truncate bimeisterdb.UserObjects table.')
    user_obj.add_argument('--url', help='Provide full URL to the web.', required=True)
    user_obj.add_argument('-u', '--user', required=False)
    user_obj.add_argument('-p', '--password', required=False)
    sql = subparser.add_parser('sql', help='Execute sql query provided in a *.sql file.')
    sql.add_argument('-s', '--host', help='DB hostname or IP address.', required=True)
    sql.add_argument('-d', '--db', help='DB name.', required=True)
    sql.add_argument('-u', '--user', help='Username with access to db.', required=True)
    sql.add_argument('-pw', '--password', help='DB user password', required=False)
    sql.add_argument('-p', '--port', help='DB port', required=True)
    sql.add_argument('-f', '--file', help='Sql filename containing the query', required=False)
    sql_matviews = sql.add_mutually_exclusive_group(required=False)
    sql_matviews.add_argument('-lmv', '--list-matviews', action='store_true', help='Get list of materialized views created by implementation department.', required=False)
    sql_matviews.add_argument('-cmv', '--create-matviews', action='store_true', help='Create materialized views created by implementation department.', required=False)
    sql_matviews.add_argument('-dmv', '--drop-matviews', action='store_true', help='Delete materialized views created by implementation department.', required=False)
    sql_matviews.add_argument('-rmv', '--refresh-matviews', action='store_true', help='Delete materialized views created by implementation department.', required=False)
    product_list = subparser.add_parser('product-list', help='Get list of services and DB for a specific project from product-collection.yaml.')
    product_list.add_argument('-lbf', '--list-branch-folder', required=False, help='Prints the list of files and folders for a given branch.')
    product_list.add_argument('-p', '--project-name', required=False, help='Provide project name from the product-collection.yaml without prompt.')
    product_list_group = product_list.add_mutually_exclusive_group(required=False)
    product_list_group.add_argument('-sb', '--search-branch', required=False, nargs='+', help='Get a list of branch names from GitLab.')
    product_list_group.add_argument('--commit', required=False, help='Get info from the product-collection.yaml file for a specific commit.')
    product_list_group.add_argument('--compare', required=False, nargs=2, help='Compare two commits for difference in product-collection.yaml in DBs list and services list.')
    bim_version = subparser.add_parser('bim-version', help='Get bimeister version information.')
    bim_version.add_argument('-u', '--url', required=True)
    args = parser.parse_args()
    try:
        if args.version:
            print(app_menu.AppMenu.__version__)
        elif args.command == 'product-list':
            g = git.Git()
            project_id = g.get_bimeister_project_id()
            if not project_id:
                sys.exit()
            if args.search_branch:
                g.list_branches(project_id, args.search_branch)
            elif args.commit:
                file_content: dict = g.get_product_collection_file_content(project_id, args.commit)
                if not file_content:
                    sys.exit()
                # project_name, services, db = git.parse_product_collection_yaml(file_content)
                data = git.parse_product_collection_yaml(file_content, project_name=args.project_name)
                if not data:
                    sys.exit()
                else:
                    project_name, services, db = data
                if not services or not db:
                    sys.exit()
                git.print_services_and_db(services, db)
            elif args.compare:
                first_commit, second_commit = args.compare[0], args.compare[1]
                first_commit_data: dict = g.get_product_collection_file_content(project_id, first_commit)
                second_commit_data: dict = g.get_product_collection_file_content(project_id, second_commit)
                if not first_commit_data or not second_commit_data:
                    sys.exit()
                first_commit_project_name, first_commit_services, first_commit_db = git.parse_product_collection_yaml(first_commit_data)
                second_commit_project_name, second_commit_services, second_commit_db = git.parse_product_collection_yaml(second_commit_data, project_name=first_commit_project_name)
                git.compare_two_commits(first_commit_services, first_commit_db, second_commit_services, second_commit_db)
            elif args.list_branch_folder:
                g.get_tree(project_id, args.list_branch_folder)
        elif args.command == 'drop-UO':
            postgre.DB.drop_userObjects(args.url, username=args.user, password=args.password)
        elif args.command == 'sql':
            pg = postgre.DB()
            q = postgre.Queries()
            conn = pg.connect_to_db(db=args.db, host=args.host, user=args.user, password=args.password, port=args.port)
            if not conn:
                sys.exit()
            if args.file:
                pg.exec_query_from_file(db=args.db, host=args.host, user=args.user, password=args.password, port=args.port, file=args.file)
            elif args.list_matviews:
                pg.exec_query(conn, query=q.get_matviews_list())
            elif args.create_matviews:
                pg.exec_query(conn, query=q.create_sf_materialized_view())
            elif args.drop_matviews:
                pg.exec_query(conn, query=q.drop_sf_materialized_view())
            elif args.refresh_matviews:
                pg.exec_query(conn, query=q.refresh_sf_materialized_view())
        elif args.command == 'vsphere':
            v = vsphere.Vsphere()
            headers = v.get_headers(args.user, args.password)
            vm_array = v.get_array_of_vm(headers, args.startswith)
            if not headers or not vm_array:
                sys.exit()
            if args.list_vm:
                v.print_list_of_vm(vm_array)
            elif args.restart_all_vm:
                v.restart_os(headers, vm_array, args.exclude_vm)
        elif args.command == 'bim-version':
            Tools.print_bim_version(args.url)
            sys.exit()
        elif args.local:
            main(local=True)
        else:
            main()
    except KeyboardInterrupt:
        print('\nKeyboardInterrupt')

    Logs().set_full_access_to_logs()

