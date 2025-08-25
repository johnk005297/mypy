import os
import app_menu
import auth
import user
import license
import export_data
import import_data
import featureToggle
import mdocker
import mk8s
from passwork import *
from tools import *

def launch_menu():

    AppMenu_main = app_menu.AppMenu()
    Auth = auth.Auth()
    User_main = user.User()
    License_main = license.License()
    Export_data = export_data.Export_data()
    Import_data_main = import_data.Import_data()
    Risk_assessment = import_data.RiskAssesment()
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
    if not Auth.establish_connection():  # if connection was not established, do not continue
        return False

    url, token, username, password = Auth.url, Auth.token, Auth.username, Auth.password
    if not License_main.get_license_status(url, token, username, password):
        print("Warning!!! Incorrect license detected! Please check!".upper())
    while True:
        user_command = AppMenu_main.get_user_command()
        match user_command:
            case False: # if nothing to check, loop over
                continue

            case ['m']:
                print(AppMenu_main._main_menu)

            case ['exit'|'q'|'quit']:  # close the menu and exit from the script
                break

            #    ''' =============================================================================== LICENSE BLOCK ==================================================================================== '''

            case ['check', 'lic']:
                License_main.display_licenses(url, token, username, password)

            case ['get', 'sid']:
                response = License_main.get_serverID(url, token)
                success: bool = response[0]
                message: str = response[1]
                print(f"Error: {message}" if not success else f"\n   - serverId: {message}")

            case ['apply', 'lic']:
                License_main.apply_license(url, token, username, password)

            case  ['delete', 'lic']:
                License_main.delete_license(url, token, username, password)

            case ['activate', 'lic']:
                license_id:str = input("Enter license id: ").strip()
                License_main.activate_license(url, token, username, password, license_id) # type: ignore

            #    ''' =============================================================================== User objects BLOCK =============================================================================== '''

            case ['drop', 'uo']:
                User_main.delete_user_objects(url, token)

            case ['drop', 'uo', '-h']:
                print(User_main.delete_user_objects.__doc__)

            #    ''' =============================================================================== TRANSFER DATA BLOCK ============================================================================== '''

            # Export data
            case ['export', 'om']:
                if Export_data.is_first_launch_export_data:
                    Export_data.create_folders_for_export_files()
                if user_command == ['export', 'om']:
                    Export_data.export_server_info(url, token)
                    Export_data.get_object_model(Export_data._object_model_file, Auth.url, Auth.token)

            case ['ls', 'workflows', *_] | ['export', 'workflows', *_] | ['rm', 'workflows', *_]:
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
                startswith: str = Tools.get_flag_values_from_args_str(args, '--startswith')
                search_for: str = Tools.get_flag_values_from_args_str(args, '--search')
                wf_id_array: list = Tools.get_flag_values_from_args_str(args, '--id').split()
                wf_type: str = Tools.get_flag_values_from_args_str(args, '--type')

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
            case ['import', 'workflows']:
                Import_data_main.import_workflows(url, token)

            case ['import', 'om']:
                Import_data_main.import_object_model(url, token)

            case ['rm', 'files']:
                Folder.clean_folder(f"{os.getcwd()}/{Export_data._transfer_folder}/{Export_data._object_model_folder}")
                Folder.clean_folder(f"{os.getcwd()}/{Export_data._transfer_folder}/{Export_data._workflows_folder}")
                File.remove_file(f"{os.getcwd()}/{Export_data._transfer_folder}/export_server.info")

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
            case ['ft', _, *_]:
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
            case ['abac', 'export', *_]:
                pass

            case ['abac', 'import', *_]:
                if user_command == ['abac', 'import', '-h'] or user_command == ['abac', 'import', '--help']:
                    Abac.print_help()
                    continue
                args = user_command[2:]
                # accessible services and keys
                svc: list = ['data-sync', 'asset', 'maintenance', 'work-permits', 'fmeca', 'rca', 'rbi', 'rcm', 'rm', 'ra']
                check_svc = [x for x in args if x in svc]
                if not check_svc:
                    print(f"Incorrect service was provided! Available options: {svc}")
                keys: list = ['--roles', '--roles-mapping', '--permission-objects', '--events']
                incorrect_keys = [x for x in args if x.startswith('--') and x not in keys]
                if incorrect_keys:
                    print(f"Incorrect key provided! Available options: {keys}")
                parsed_args = dict()
                for x in range(len(args)):
                    if args[x] in svc and args[x] not in parsed_args.keys():
                        parsed_args[args[x]] = {}
                        for y in range(x + 1, len(args)):
                            if args[y] not in svc:
                                if args[y] in keys:
                                    if args[y + 1].startswith('"'):
                                        second_quotes_idx: int = ' '.join(args[y + 1:]).find('"', 1)
                                        if second_quotes_idx == -1:
                                            print(f"Missing quotes in file name for {args[y]} key!")
                                        else:
                                            filename: str = ' '.join(args[y + 1:])[1:second_quotes_idx]
                                    else: 
                                        filename: str = args[y + 1]
                                    try:
                                        parsed_args[args[x]].update({args[y]: filename})
                                    except IndexError:
                                        print("Incorrect input! Check for the filename after the [--key]")
                            else:
                                break
                if parsed_args.get('maintenance'):
                    data: dict = Abac.collect_abac_data(
                                                        url_permission=f"{url}/api/maintenance-planning/AbacConfiguration/UploadPermissionObjectsConfiguration",
                                                        url_roles=f"{url}/api/maintenance-planning/AbacConfiguration/UploadRolesConfiguration",
                                                        url_roles_mapping=f"{url}/api/maintenance-planning/AbacConfiguration/UploadRolesMappingConfiguration",
                                                        url_events=f"{url}/api/EnterpriseAssetManagementNotificationHub/upload-event-rules",
                                                        permissionObjects_file=parsed_args['maintenance'].get('--permission-objects'),
                                                        roles_file=parsed_args['maintenance'].get('--roles'),
                                                        rolesMapping_file=parsed_args['maintenance'].get('--roles-mapping'),
                                                        notification_file=parsed_args['maintenance'].get('--events')
                                                        )
                    Abac.import_abac_and_events(token, data, 'maintenance-planning')
                if parsed_args.get('asset'):
                    data: dict = Abac.collect_abac_data(
                                                        url_permission=f"{url}/api/asset-performance-management/AbacConfiguration/UploadPermissionObjectsConfiguration",
                                                        url_roles=f"{url}/api/asset-performance-management/AbacConfiguration/UploadRolesConfiguration",
                                                        url_roles_mapping=f"{url}/api/asset-performance-management/AbacConfiguration/UploadRolesMappingConfiguration",
                                                        url_events=f"{url}/api/asset-performance-management/NotificationHub/upload-event-rules",
                                                        permissionObjects_file=parsed_args['asset'].get('--permission-objects'),
                                                        roles_file=parsed_args['asset'].get('--roles'),
                                                        rolesMapping_file=parsed_args['asset'].get('--roles-mapping'),
                                                        notification_file=parsed_args['asset'].get('--events')
                                                                                )
                    Abac.import_abac_and_events(token, data, 'asset-performance-management')
                if parsed_args.get('data-sync'):
                    data: dict = Abac.collect_abac_data(
                                                        url_permission=f"{url}/api/data-synchronizer/AbacConfiguration/UploadPermissionObjectsConfiguration",
                                                        url_roles=f"{url}/api/data-synchronizer/AbacConfiguration/UploadRolesConfiguration",
                                                        url_roles_mapping=f"{url}/api/data-synchronizer/AbacConfiguration/UploadRolesMappingConfiguration",
                                                        permissionObjects_file=parsed_args['data-sync'].get('--permission-objects'),
                                                        roles_file=parsed_args['data-sync'].get('--roles'),
                                                        rolesMapping_file=parsed_args['data-sync'].get('--roles-mapping'),
                                                        notification_file=None
                                                        )
                    Abac.import_abac_and_events(token, data, 'data-synchronizer-api')
                if parsed_args.get('work-permits'):
                    data: dict = Abac.collect_abac_data(
                                                        url_permission=f"{url}/api/work-permits-management/AbacConfiguration/UploadPermissionObjectsConfiguration",
                                                        url_roles=f"{url}/api/work-permits-management/AbacConfiguration/UploadRolesConfiguration",
                                                        url_roles_mapping=f"{url}/api/work-permits-management/AbacConfiguration/UploadRolesMappingConfiguration",
                                                        permissionObjects_file=parsed_args['work-permits'].get('--permission-objects'),
                                                        roles_file=parsed_args['work-permits'].get('--roles'),
                                                        rolesMapping_file=parsed_args['work-permits'].get('--roles-mapping'),
                                                        notification_file=None
                                                        )
                    Abac.import_abac_and_events(token, data, 'work-permits-management')
                if parsed_args.get('fmeca'):
                    data: dict = Abac.collect_abac_data(
                                                        url_permission=f"{url}/api/fmeca/AbacConfiguration/UploadPermissionObjectsConfiguration",
                                                        url_roles=f"{url}/api/fmeca/AbacConfiguration/UploadRolesConfiguration",
                                                        url_roles_mapping=f"{url}/api/fmeca/AbacConfiguration/UploadRolesMappingConfiguration",
                                                        permissionObjects_file=parsed_args['fmeca'].get('--permission-objects'),
                                                        roles_file=parsed_args['fmeca'].get('--roles'),
                                                        rolesMapping_file=parsed_args['fmeca'].get('--roles-mapping'),
                                                        notification_file=None
                                                        )
                    Abac.import_abac_and_events(token, data, 'fmeca')
                if parsed_args.get('rca'):
                    data: dict = Abac.collect_abac_data(
                                                        url_permission=f"{url}/api/root-cause-analysis/AbacConfiguration/UploadPermissionObjectsConfiguration",
                                                        url_roles=f"{url}/api/root-cause-analysis/AbacConfiguration/UploadRolesConfiguration",
                                                        url_roles_mapping=f"{url}/api/root-cause-analysis/AbacConfiguration/UploadRolesMappingConfiguration",
                                                        permissionObjects_file=parsed_args['rca'].get('--permission-objects'),
                                                        roles_file=parsed_args['rca'].get('--roles'),
                                                        rolesMapping_file=parsed_args['rca'].get('--roles-mapping'),
                                                        notification_file=None
                                                        )
                    Abac.import_abac_and_events(token, data, 'root-cause-analysis')
                if parsed_args.get('rbi'):
                    data: dict = Abac.collect_abac_data(
                                                        url_permission=f"{url}/api/risk-based-inspections/AbacConfiguration/UploadPermissionObjectsConfiguration",
                                                        url_roles=f"{url}/api/risk-based-inspections/AbacConfiguration/UploadRolesConfiguration",
                                                        url_roles_mapping=f"{url}/api/risk-based-inspections/AbacConfiguration/UploadRolesMappingConfiguration",
                                                        permissionObjects_file=parsed_args['rbi'].get('--permission-objects'),
                                                        roles_file=parsed_args['rbi'].get('--roles'),
                                                        rolesMapping_file=parsed_args['rbi'].get('--roles-mapping'),
                                                        notification_file=None
                                                        )
                    Abac.import_abac_and_events(token, data, 'risk-based-inspections')
                if parsed_args.get('rcm'):
                    data: dict = Abac.collect_abac_data(
                                                        url_permission=f"{url}/api/reliability-centered-maintenance/AbacConfiguration/UploadPermissionObjectsConfiguration",
                                                        url_roles=f"{url}/api/reliability-centered-maintenance/AbacConfiguration/UploadRolesConfiguration",
                                                        url_roles_mapping=f"{url}/api/reliability-centered-maintenance/AbacConfiguration/UploadRolesMappingConfiguration",
                                                        permissionObjects_file=parsed_args['rcm'].get('--permission-objects'),
                                                        roles_file=parsed_args['rcm'].get('--roles'),
                                                        rolesMapping_file=parsed_args['rcm'].get('--roles-mapping'),
                                                        notification_file=None
                                                        )
                    Abac.import_abac_and_events(token, data, 'reliability-centered-maintenance')
                if parsed_args.get('rm'):
                    data: dict = Abac.collect_abac_data(
                                                        url_permission=f"{url}/api/recommendation-management/AbacConfiguration/UploadPermissionObjectsConfiguration",
                                                        url_roles=f"{url}/api/recommendation-management/AbacConfiguration/UploadRolesConfiguration",
                                                        url_roles_mapping=f"{url}/api/recommendation-management/AbacConfiguration/UploadRolesMappingConfiguration",
                                                        permissionObjects_file=parsed_args['rm'].get('--permission-objects'),
                                                        roles_file=parsed_args['rm'].get('--roles'),
                                                        rolesMapping_file=parsed_args['rm'].get('--roles-mapping'),
                                                        notification_file=None
                                                        )
                    Abac.import_abac_and_events(token, data, 'recommendation-management')
            
            case ['risk-ass', '-f', *_]:
                path_to_file: str = user_command[2]
                Risk_assessment.import_risk_assessment_template(url, token, path_to_file)

            #    ''' =============================================================================== Custom UI ======================================================================================== '''
            case ['apply', 'UI', *_]:
                if '-f' not in user_command:
                    print("Unknown command")
                    continue
                try:
                    file = user_command[2:][1]
                except IndexError as err:
                    print("Incorrect command. No file pointed out.")
                Bimeister.apply_bimeister_customUI(url, token, file)
            
            #    ''' =============================================================================== Recalculate path ================================================================================= '''
            case ['recalc-paths', *_]:
                Bimeister.recalculate_path(url, token)
            
            #    ''' =============================================================================== Templates ======================================================================================== '''
            case ['ls', 'templates']:
                templates: list = Bimeister.get_list_of_templates(url, token)
                Bimeister.print_list_of_templates(templates)
            
            case ['export', 'template' | 'templates', *_]:
                args = user_command[2:]
                id: list = Tools.get_flag_values_from_args_str(args, '--id').split()
                data = Bimeister.export_templates(url, token, id)

            #    ''' =============================================================================== Tools ============================================================================================ '''
            case ['ptoken']:
                private_token = Auth.get_private_token(url, token)
                print(f"\n{private_token}")

            case ['token']:
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

            # wildcard pattern if no cases before where matched
            case _:
                print("Unknown command")


# check username and password in Passwork vaults
# p = Passwork()
# t = p.token()
# pw = p.passwords()
# is_passwork_available = p.is_passwork_available()
# if is_passwork_available:
#     token = t.get_token()
#     passwords: list = pw.search_passwords_by_url(args.url, token)
# else:
#     passwords = None
# if not is_passwork_available or not passwords:
#     username = input("Enter login(default, admin): ")
#     password = getpass("Enter password(default, Qwerty12345!): ")
#     username = username if username else args.user
#     password = password if password else args.password
# else:
#     passwords_id: list = [x['id'] for x in passwords]
#     creds = pw.get_credentials(passwords_id, token)