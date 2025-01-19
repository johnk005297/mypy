#
import os
import sys
import app_menu
import auth
import user
import license
from arg_parser import Parser
import export_data
import import_data
import postgre
import featureToggle
import mdocker
import mk8s
import vsphere
import git
import re
import time
from tools import Folder, File, Tools
from log import Logs
from rich.console import Console
from rich.table import Table


def main(local=False):

    AppMenu_main = app_menu.AppMenu()
    Auth = auth.Auth()
    User_main = user.User()
    License_main = license.License()
    Export_data = export_data.Export_data()
    Import_data_main = import_data.Import_data()
    Abac = import_data.Abac()
    Docker = mdocker.Docker()
    K8s = mk8s.K8S(namespace='bimeister')
    FT = featureToggle.FeatureToggle()


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
    if not License_main.get_license_status(url, token, username, password):
        print("Warning!!! Incorrect license detected! Please check!".upper())
    while True:
        user_command = AppMenu_main.get_user_command()

        match user_command:
            case False: # if nothing to check, loop over
                continue

            case ['m'] if not local:
                print(AppMenu_main._main_menu)
            
            case ['m'] if local:
                print(AppMenu_main._local_menu)

            case ['exit'|'q'|'quit']:  # close the menu and exit from the script
                break

            #    ''' =============================================================================== LICENSE BLOCK ==================================================================================== '''

            case ['check', 'lic'] if not local:
                License_main.display_licenses(url, token, username, password)

            case ['get', 'sid'] if not local:
                response = License_main.get_serverID(url, token)
                print("\n   - serverId:", response)

            case ['apply', 'lic'] if not local:
                License_main.post_license(url, token, username, password)

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
                    Export_data.print_help(ls=True)
                    continue
                if user_command == ['export', 'workflows', '--help'] or user_command == ['export', 'workflows', '-h']:
                    Export_data.print_help(export=True)
                    continue
                if user_command == ['rm', 'workflows', '--help'] or user_command == ['rm', 'workflows', '-h']:
                    Export_data.print_help(remove=True)
                    continue
                if Export_data.is_first_launch_export_data:
                    Export_data.create_folders_for_export_files()
                args = user_command[2:]

                # at the beginning and at the end of the line we cut the quotation marks with slicing
                startswith = re.search('--startswith=".+"', ' '.join(args)).group().split('=')[1][1:-1] if re.search('--startswith=".+"', ' '.join(args)) else ''
                search_for = re.search('--search=".+"', ' '.join(args)).group().split('=')[1][1:-1] if re.search('--search=".+"', ' '.join(args)) else ''
                wf_id_array = re.search('--id=".+"', ' '.join(args)).group().split('=')[1] if re.search('--id=".+"', ' '.join(args)) else ''
                wf_id_array = re.sub(r"\"", "", wf_id_array).split()
                wf_type = re.search('--type=".+"', ' '.join(args)).group().split('=')[1].lower() if re.search('--type=".+"', ' '.join(args)) else ''
                wf_type = re.sub(r"\"", "", wf_type)

                if wf_id_array and user_command[:2] == ['export', 'workflows']:
                    Export_data.export_server_info(url, token)
                    Export_data.export_workflows_by_choice(url, token, wf_id_array)
                    continue
                workflows = Export_data.define_needed_workflows(url, token, args, startswith=startswith, search_for=search_for, type=wf_type)
                if not workflows:
                    continue
                if user_command[:2] == ['export', 'workflows']:
                    Export_data.export_server_info(url, token)
                    Export_data.export_workflows_at_once(url, token, workflows)
                elif user_command[:2] == ['ls', 'workflows']:
                    Export_data.display_list_of_workflowsName_and_workflowsId(workflows)
                elif user_command[:2] == ['rm', 'workflows']:
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
            
            case ['ls', *_]:
                if len(user_command) == 1:
                    Tools.run_terminal_command(Folder.get_content())
                else:
                    Tools.run_terminal_command(Folder.get_content(user_command[1]))
            
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
            case ['ft', _, *_] if not local:                
                if ' '.join(user_command).startswith('ft --list'):
                    if user_command == ['ft', '--list']:
                        FT.display_features(url)
                    elif user_command == ['ft', '--list', '--enabled']:
                        FT.display_features(url, enabled=True)
                    elif user_command == ['ft', '--list', '--disabled']:
                        FT.display_features(url, disabled=True)                        
                elif '--on' in user_command or '--off' in user_command:
                    features: list = [x for x in user_command if x not in ('--on', '--off', 'ft')]
                    try:
                        FT.set_feature(url, token, features, is_enabled=(True if '--on' in user_command else False))
                    except UnboundLocalError as err:
                        print(err)
                        continue
                    except Exception as err:
                        print(err)
                        print("Unpredictable behaviour in k8s set feature.")
                        continue

            #    ''' =============================================================================== ABAC ============================================================================================= '''
            case ['abac', 'import', *_]:
                if user_command == ['abac', 'import', '-h'] or user_command == ['abac', 'import', '--help']:
                    Abac.print_help()
                    continue
                args = user_command[2:]
                # accessible services and keys
                svc = ('data-sync', 'asset', 'maintenance', 'work-permits')
                keys= ('--roles', '--roles-mapping', '--permission-objects', '--events')
                incorrect_keys = [x for x in args if x.startswith('--') and x not in keys]
                if incorrect_keys:
                    print("Attention! Incorrect key provided!")
                parsed_args = dict()
                for x in range(len(args)):
                    if args[x] in svc and args[x] not in parsed_args.keys():
                        parsed_args[args[x]] = {}
                        for y in range(x+1, len(args)):
                            if args[y] not in svc:
                                if args[y] in keys:
                                    try:
                                        parsed_args[args[x]].update({args[y]: args[y+1]})
                                    except IndexError:
                                        print("Incorrect input! Check for the filename after the --[key]")
                            else:
                                break
                if parsed_args.get('maintenance'):
                    data: dict = Abac.collect_maintenance_planning_data(
                                                                        url,
                                                                        permissionObjects_file=parsed_args['maintenance'].get('--permission-objects'),
                                                                        roles_file=parsed_args['maintenance'].get('--roles'),
                                                                        rolesMapping_file=parsed_args['maintenance'].get('--roles-mapping'),
                                                                        notification_file=parsed_args['maintenance'].get('--events')
                                                                        )
                    Abac.import_abac(token, data, 'maintenance-planning')
                if parsed_args.get('asset'):
                    data: dict = Abac.collect_asset_performance_management_data(
                                                                                url,
                                                                                permissionObjects_file=parsed_args['asset'].get('--permission-objects'),
                                                                                roles_file=parsed_args['asset'].get('--roles'),
                                                                                rolesMapping_file=parsed_args['asset'].get('--roles-mapping'),
                                                                                notification_file=parsed_args['asset'].get('--events')                        
                                                                                )
                    Abac.import_abac(token, data, 'asset-performance-management')
                if parsed_args.get('data-sync'):
                    data: dict = Abac.collect_data_synchronizer_data(
                                                                    url,
                                                                    permissionObjects_file=parsed_args['data-sync'].get('--permission-objects'),
                                                                    roles_file=parsed_args['data-sync'].get('--roles'),
                                                                    rolesMapping_file=parsed_args['data-sync'].get('--roles-mapping')
                                                                    )
                    Abac.import_abac(token, data, 'data-synchronizer-api')
                if parsed_args.get('work-permits'):
                    data: dict = Abac.collect_work_permits_management_data(
                                                                    url,
                                                                    permissionObjects_file=parsed_args['work-permits'].get('--permission-objects'),
                                                                    roles_file=parsed_args['work-permits'].get('--roles'),
                                                                    rolesMapping_file=parsed_args['work-permits'].get('--roles-mapping')
                                                                    )
                    Abac.import_abac(token, data, 'work-permits-management')

            #    ''' =============================================================================== Custom UI ======================================================================================== '''
            case ['apply', 'UI', *_]:
                if '-f' not in user_command:
                    print("Unknown command")
                    continue
                try:
                    file = user_command[2:][1]
                except IndexError as err:
                    print("Incorrect command. No file pointed out.")
                Tools.apply_bimeister_customUI(url, token, file)

            # wildcard pattern if no cases before where matched
            case _:
                print("Unknown command")


def enable_history_input():
    ''' Function provides an opportunity to have access of input history. '''
    if Tools.is_windows():
        import pyreadline3
    else:
        import readline    


if __name__ == '__main__':
    enable_history_input()
    args = Parser().parse_args()
    try:
        if args.version:
            print(app_menu.AppMenu.__version__)
        elif args.command == 'git':
            g = git.Git()
            project_id = g.get_bimeister_project_id()
            if not project_id:
                sys.exit()
            if args.search_branch:
                g.search_branches(project_id, args.search_branch)
            elif args.commit:
                file_content: dict = g.get_product_collection_file_content(project_id, args.commit)
                if not file_content:
                    sys.exit()
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
            elif args.search_tag:
                g.search_tag(project_id, args.search_tag)
        elif args.command == 'drop-UO':
            postgre.DB.drop_userObjects(args.url, username=args.user, password=args.password)
        elif args.command == 'sql':
            pg = postgre.DB()
            q = postgre.Queries()
            conn = pg.connect_to_db(db=args.db, host=args.host, user=args.user, password=args.password, port=args.port)
            if not conn:
                sys.exit()
            if args.file:
                pg.exec_query(conn, sql_file=args.file, out=args.out)
            elif args.list_matviews:
                pg.exec_query(conn, query=q.get_matviews_list(args.list_matviews))
            elif args.drop_matviews:                
                pg.exec_query(conn, query=q.drop_materialized_view(args.drop_matviews))
            elif args.refresh_matviews:
                pg.exec_query(conn, query=q.refresh_materialized_view())
            elif args.mdm_prod:
                pg.exec_query(conn, query=q.swith_externalKey_for_mdm_connector(value='Prod'))
            elif args.mdm_test:
                pg.exec_query(conn, query=q.swith_externalKey_for_mdm_connector(value='Test'))
            elif args.list_db:
                pg.exec_query(conn, query=q.get_list_of_all_db())
        elif args.command == 'vsphere':
            subcommand = sys.argv[2]
            v = vsphere.Vsphere()
            headers = v.get_headers(args.user, args.password)
            if not headers:
                sys.exit()
            elif subcommand == 'list-vm':
                exclude_vm: list = args.exclude.split() if args.exclude else []
                vm_array = v.get_array_of_vm(headers, exclude_vm, args.filter, args.powered_on)
                v.print_list_of_vm(vm_array)
            elif subcommand == 'restart-vm':
                if args.all:
                    confirm: bool = True if input("YOU ARE ABOUT TO RESTART ALL VM's IN THE CLUSTER!!! ARE YOU SURE?(YES|NO) ").lower() == 'yes' else False
                    if not confirm:
                        print("Restart procedure aborted!")
                        sys.exit()
                    exclude_vm: list = args.exclude.split() if args.exclude else []
                    vm_array = v.get_array_of_vm(headers, exclude_vm, powered_on=True)
                    v.restart_os(headers, vm_array)
                else:
                    exclude_vm: list = args.exclude.split() if args.exclude else []
                    vm_array = v.get_array_of_vm(headers, exclude_vm, args.filter, powered_on=True)
                    v.restart_os(headers, vm_array)
            elif subcommand == 'start-vm':
                exclude_vm: list = args.exclude.split() if args.exclude else []
                vm_array: dict = v.get_array_of_vm(headers, exclude_vm, args.filter)
                for value in vm_array.values():
                    v.start_vm(headers, value["moId"], value["name"])
            elif subcommand == 'stop-vm':
                exclude_vm: list = args.exclude.split() if args.exclude else []
                vm_array: dict = v.get_array_of_vm(headers, exclude_vm, args.filter)
                for value in vm_array.values():
                    v.stop_vm(headers, value["moId"], value["name"])
            elif subcommand == 'show-snap':
                exclude_vm: list = args.exclude.split() if args.exclude else []
                vm_array: dict = v.get_array_of_vm(headers, exclude_vm, args.filter)
                for value in vm_array.values():
                    snapshots: dict = v.get_vm_snapshots(headers, value["moId"], value["name"])
                    v.print_vm_snapshots(value["name"], snapshots)
            elif subcommand in ('take-snap', 'revert-snap', 'remove-snap'):
                # Logic of taking/revering snaps procedure:
                # get needed VMs -> power OFF -> take/revert snaps -> restore power state
                exclude_vm: list = args.exclude.split() if args.exclude else []
                vm_array: dict = v.get_array_of_vm(headers, exclude_vm, args.filter)
                if not vm_array:
                    sys.exit("No VM were matched. Exit!")
                for vm in vm_array:
                    print(vm_array[vm]['name'])
                confirm = input("\nIs it correct VM list? (Y/N): ").lower()
                if confirm not in ('y', 'yes'):
                    sys.exit("Abort procedure!")
                for value in vm_array.values():
                    v.stop_vm(headers, value["moId"], value["name"])
                count = 0
                while True:
                    time.sleep(5)
                    count += 1
                    vm_powered_on_count = 0
                    for value in vm_array.values():
                        power_status = v.get_vm_power_state(headers, value["moId"])
                        if power_status != "POWERED_OFF":
                            vm_powered_on = value["name"]
                            vm_powered_on_count += 1
                    if count == 120:
                        print("Couldn't stop VM within 10 minutes. Check VM status in vCenter!")
                        break
                    elif vm_powered_on_count > 0:
                        time.sleep(5)
                        print(f"Awaiting guest OS shutdown: {vm_powered_on}")
                        continue
                    else:
                        # create table for output
                        table = Table(show_lines=True)
                        table.add_column("Task Name", justify="left", no_wrap=True)
                        table.add_column("Target", justify="left")
                        table.add_column("Snapshot Name", justify="left")
                        table.add_column("Status", justify="center")
                        for value in vm_array.values():
                            if subcommand == 'take-snap':
                                v.take_snapshot(headers, value['moId'], value['name'], snap_name=args.name.strip(), description=args.desc)
                            elif subcommand == 'revert-snap':
                                snapshots: dict = v.get_vm_snapshots(headers, value['moId'], value['name'])
                                snap_id = None
                                for snap in snapshots.values():
                                    if snap['snapName'].strip() == args.name.strip():
                                        snap_id = snap['snapId']
                                        break
                                if snap_id:
                                  v.revert_to_snapshot(headers, snap_id, value['name'])  
                                else:
                                    print(f"Incorrect snapshot name for vm: {value['name']}")
                            elif subcommand == 'remove-snap':
                                snapshots: dict = v.get_vm_snapshots(headers, value['moId'], value['name'])
                                match = False
                                for snap in snapshots.values():
                                    if snap['snapName'].strip() == args.name.strip():
                                        match = True
                                        remove_snap_status = v.remove_vm_snapshot(headers, snap['snapId'])
                                        time.sleep(1.5)
                                        table.add_row(
                                                    "Remove snapshot",
                                                    value['name'],
                                                    snap['snapName'].strip(),
                                                    "[green]✅[/green]" if remove_snap_status else "[red]❌[/red]", style="magenta"
                                                    )
                                if not match:    
                                    print(f"Incorrect snapshot name for vm: {value['name']}")
                        break
                console = Console()
                console.print(table)                
                # Restoring power state
                for value in vm_array.values():
                    if value["power_state"] == "POWERED_ON":
                        v.start_vm(headers, value["moId"], value["name"])
        elif args.command == 'bim-version':
            Tools.print_bim_version(args.url)
        elif args.local:
            main(local=True)
        else:
            main()
    except KeyboardInterrupt:
        print('\nKeyboardInterrupt')
    finally:
        Logs().set_full_access_to_logs()

