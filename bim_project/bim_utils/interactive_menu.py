import os
import app_menu
import auth
import user
import argparse
import license
import export_data
import import_data
import featureToggle
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
                        continue

            #    ''' =============================================================================== ABAC ============================================================================================= '''
            case ['abac', 'export', *_]:
                pass

            case ['abac', 'import', *_]:
                if user_command == ['abac', 'import', '-h'] or user_command == ['abac', 'import', '--help']:
                    Abac.print_help('main-msg')
                    continue
                parser = Abac.get_parser()
                try:
                    args = parser.parse_args(user_command[2:])
                except argparse.ArgumentError:
                    continue
                except SystemExit:
                    continue
                if args.command == 'data-sync':
                    if args.help:
                        Abac.print_help('data-sync-msg')
                        continue
                    data: dict = Abac.collect_abac_data(
                                                        url_permission=f"{url}/api/data-synchronizer/AbacConfiguration/UploadPermissionObjectsConfiguration"
                                                        ,url_roles=f"{url}/api/data-synchronizer/AbacConfiguration/UploadRolesConfiguration"
                                                        ,url_roles_mapping=f"{url}/api/data-synchronizer/AbacConfiguration/UploadRolesMappingConfiguration"
                                                        ,url_common=f"{url}/api/data-synchronizer/AbacConfiguration/UploadCommonConfiguration"
                                                        ,permissionObjects_file=args.permission_objects
                                                        ,roles_file=args.roles
                                                        ,rolesMapping_file=args.roles_mapping
                                                        ,common_file=args.common
                                                        )
                    Abac.import_abac_and_events(token, data, 'data-synchronizer-api')
                if args.command == 'maint':
                    if args.help:
                        Abac.print_help('maintenance-msg')
                        continue
                    data: dict = Abac.collect_abac_data(
                                                        url_permission=f"{url}/api/maintenance-planning/AbacConfiguration/UploadPermissionObjectsConfiguration"
                                                        ,url_roles=f"{url}/api/maintenance-planning/AbacConfiguration/UploadRolesConfiguration"
                                                        ,url_roles_mapping=f"{url}/api/maintenance-planning/AbacConfiguration/UploadRolesMappingConfiguration"
                                                        ,url_events=f"{url}/api/EnterpriseAssetManagementNotificationHub/upload-event-rules"
                                                        ,permissionObjects_file=args.permission_objects
                                                        ,roles_file=args.roles
                                                        ,rolesMapping_file=args.roles_mapping
                                                        ,notification_file=args.events
                                                        )
                    Abac.import_abac_and_events(token, data, 'maintenance-planning')
                if args.command == 'asset':
                    if args.help:
                        Abac.print_help('asset-msg')
                    data: dict = Abac.collect_abac_data(
                                                        url_permission=f"{url}/api/asset-performance-management/AbacConfiguration/UploadPermissionObjectsConfiguration"
                                                        ,url_roles=f"{url}/api/asset-performance-management/AbacConfiguration/UploadRolesConfiguration"
                                                        ,url_roles_mapping=f"{url}/api/asset-performance-management/AbacConfiguration/UploadRolesMappingConfiguration"
                                                        ,url_events=f"{url}/api/asset-performance-management/NotificationHub/upload-event-rules"
                                                        ,url_common=f"{url}/api/asset-performance-management/AbacConfiguration/UploadCommonConfiguration"
                                                        ,permissionObjects_file=args.permission_objects
                                                        ,roles_file=args.roles
                                                        ,rolesMapping_file=args.roles_mapping
                                                        ,notification_file=args.events
                                                        ,common_file=args.common
                                                        )
                    Abac.import_abac_and_events(token, data, 'asset-performance-management')
                if args.command == 'wpm':
                    if args.help:
                        Abac.print_help('work-permits-msg')
                    data: dict = Abac.collect_abac_data(
                                                        url_permission=f"{url}/api/work-permits-management/AbacConfiguration/UploadPermissionObjectsConfiguration"
                                                        ,url_roles=f"{url}/api/work-permits-management/AbacConfiguration/UploadRolesConfiguration"
                                                        ,url_roles_mapping=f"{url}/api/work-permits-management/AbacConfiguration/UploadRolesMappingConfiguration"
                                                        ,permissionObjects_file=args.permission_objects
                                                        ,roles_file=args.roles
                                                        ,rolesMapping_file=args.roles_mapping
                                                        )
                    Abac.import_abac_and_events(token, data, 'work-permits-management')
                if args.command == 'fmeca':
                    if args.help:
                        Abac.print_help('fmeca-msg')
                    data: dict = Abac.collect_abac_data(
                                                        url_permission=f"{url}/api/fmeca/AbacConfiguration/UploadPermissionObjectsConfiguration"
                                                        ,url_roles=f"{url}/api/fmeca/AbacConfiguration/UploadRolesConfiguration"
                                                        ,url_roles_mapping=f"{url}/api/fmeca/AbacConfiguration/UploadRolesMappingConfiguration"
                                                        ,permissionObjects_file=args.permission_objects
                                                        ,roles_file=args.roles
                                                        ,rolesMapping_file=args.roles_mapping
                                                        )
                    Abac.import_abac_and_events(token, data, 'fmeca')
                if args.command == 'rca':
                    if args.help:
                        Abac.print_help('rca-msg')
                    data: dict = Abac.collect_abac_data(
                                                        url_permission=f"{url}/api/root-cause-analysis/AbacConfiguration/UploadPermissionObjectsConfiguration"
                                                        ,url_roles=f"{url}/api/root-cause-analysis/AbacConfiguration/UploadRolesConfiguration"
                                                        ,url_roles_mapping=f"{url}/api/root-cause-analysis/AbacConfiguration/UploadRolesMappingConfiguration"
                                                        ,permissionObjects_file=args.permission_objects
                                                        ,roles_file=args.roles
                                                        ,rolesMapping_file=args.roles_mapping
                                                        )
                    Abac.import_abac_and_events(token, data, 'root-cause-analysis')
                if args.command == 'rbi':
                    if args.help:
                        Abac.print_help('rbi-msg')
                    data: dict = Abac.collect_abac_data(
                                                        url_permission=f"{url}/api/risk-based-inspections/AbacConfiguration/UploadPermissionObjectsConfiguration"
                                                        ,url_roles=f"{url}/api/risk-based-inspections/AbacConfiguration/UploadRolesConfiguration"
                                                        ,url_roles_mapping=f"{url}/api/risk-based-inspections/AbacConfiguration/UploadRolesMappingConfiguration"
                                                        ,permissionObjects_file=args.permission_objects
                                                        ,roles_file=args.roles
                                                        ,rolesMapping_file=args.roles_mapping
                                                        )
                    Abac.import_abac_and_events(token, data, 'risk-based-inspections')
                if args.command == 'rcm':
                    if args.help:
                        Abac.print_help('rcm-msg')
                    data: dict = Abac.collect_abac_data(
                                                        url_permission=f"{url}/api/reliability-centered-maintenance/AbacConfiguration/UploadPermissionObjectsConfiguration"
                                                        ,url_roles=f"{url}/api/reliability-centered-maintenance/AbacConfiguration/UploadRolesConfiguration"
                                                        ,url_roles_mapping=f"{url}/api/reliability-centered-maintenance/AbacConfiguration/UploadRolesMappingConfiguration"
                                                        ,permissionObjects_file=args.permission_objects
                                                        ,roles_file=args.roles
                                                        ,rolesMapping_file=args.roles_mapping
                                                        )
                    Abac.import_abac_and_events(token, data, 'reliability-centered-maintenance')
                if args.command == 'rm':
                    if args.help:
                        Abac.print_help('rm-msg')
                    data: dict = Abac.collect_abac_data(
                                                        url_permission=f"{url}/api/recommendation-management/AbacConfiguration/UploadPermissionObjectsConfiguration"
                                                        ,url_roles=f"{url}/api/recommendation-management/AbacConfiguration/UploadRolesConfiguration"
                                                        ,url_roles_mapping=f"{url}/api/recommendation-management/AbacConfiguration/UploadRolesMappingConfiguration"
                                                        ,permissionObjects_file=args.permission_objects
                                                        ,roles_file=args.roles
                                                        ,rolesMapping_file=args.roles_mapping
                                                        )
                    Abac.import_abac_and_events(token, data, 'recommendation-management')
                if args.command == 'auth':
                    if args.help:
                        Abac.print_help('auth-msg')
                    data: dict = Abac.collect_abac_data(
                                                        url_rules=f"{url}/api/abac/rules/import"
                                                        ,auth_file=args.rules
                                                        )
                    Abac.import_abac_and_events(token, data, 'auth')

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
