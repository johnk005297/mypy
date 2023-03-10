#
# Script for work with license and some other small features.
import os
import time
from pathlib import Path
import app_menu
import auth
import user
import license
import export_data
import import_data
from tools import Folder, File
import logging
import logs # activates with import


def main():

    AppMenu_main     = app_menu.AppMenu()
    Auth_main        = auth.Auth()
    User_main        = user.User()
    License_main     = license.License()
    Export_data_main = export_data.Export_data()
    Import_data_main = import_data.Import_data()


    AppMenu_main.welcome_info_note()
    if not Auth_main.establish_connection():  # if connection was not established, do not continue
        return False

    url, token, username, password = Auth_main.url, Auth_main.token, Auth_main.username, Auth_main.password
# ---------------------------------------------------------
#   TEST ZONE
# ---------------------------------------------------------

    # {'product': 'BimeisterEDMS', 'licenseID': '', 'serverID': '', 'isActive': True, 'until': '2023-12-25T23:59:59', 'numberOfUsers': 50, 'numberOfIpConnectionsPerUser': 0}
# ---------------------------------------------------------
# http://10.168.23.161
# ---------------------------------------------------------

    while True:
        command = AppMenu_main.define_purpose_and_menu()

        ''' Check user privileges for everything related in the tuple below. '''
        if command in (
                        'check_license'
                        ,'server_id'
                        ,'check_serverId_validation'
                        ,'apply_license'
                        ,'delete_active_license'
                        ,'export_workflows'
                        ,'export_object_model'
                        ,'display_workflows'
                        ,'import_workflows'
                        'import_object_model'
                      ):            
            if not License_main.privileges_checked and not User_main.check_user_permissions(Auth_main.url, Auth_main.token, Auth_main.username, Auth_main.password, License_main._permissions_to_check):
                
                ''' Create user with all the privileges. '''

                # Create/activate user
                Auth_superuser = auth.Auth(username='johnny_mnemonic', password='Qwerty12345!') # Create Auth class instance for new user
                try:
                    License_main.privileges_granted, superuser = User_main.create_or_activate_superuser(Auth_main.url, Auth_main.token, Auth_superuser.username, Auth_superuser.password)
                except TypeError:
                    continue
                # Create system role
                su_system_role_id = User_main.create_system_role(Auth_main.url, Auth_main.token)
                # Add system role to created user
                User_main.add_system_role_to_user(Auth_main.url, Auth_main.token, superuser['id'], superuser['userName'], su_system_role_id)
                # Save data about current user we are working under
                initial_user = User_main.get_current_user(Auth_main.url, Auth_main.token)
                # Add created role to current user
                Auth_superuser.providerId = Auth_main.get_local_providerId(Auth_main.url)  # getting provider id for created user for logon
                Auth_superuser.get_user_access_token(Auth_main.url, Auth_superuser.username, Auth_superuser.password, Auth_superuser.providerId) # logging in under superuser account
                # Add system role to initial user we connected
                User_main.add_system_role_to_user(Auth_main.url, Auth_superuser.token, initial_user['id'], Auth_main.username, su_system_role_id)


        
        if command == 'main_menu':
            print(AppMenu_main._main_menu)
        elif command in ('q', 'connect_to_another_server'): # connect to another server isn't realized yet

            ''' Delete created user with privileges. '''
            if License_main.privileges_granted:
                User_main.remove_system_role_from_user(Auth_main.url, Auth_superuser.token, initial_user['id'], initial_user['userName'], su_system_role_id)
                Auth_main.get_user_access_token(Auth_main.url, Auth_main.username, Auth_main.password, Auth_main.providerId)
                User_main.remove_system_role_from_user(Auth_main.url, Auth_main.token, superuser['id'], superuser['userName'], su_system_role_id)
                User_main.delete_system_role(Auth_main.url, su_system_role_id, Auth_main.token)
                User_main.delete_user(Auth_main.url, Auth_main.token, superuser['id'], superuser['userName'])


            if command == 'q':
                break   # Close the menu and exit from the script.
            else:
                License_main.privileges_granted = False
                License_main.privileges_checked = False
                if not Auth_main.establish_connection():
                    return False

            ''' === LICENSE BLOCK === '''

        elif command == 'check_license':
            License_main.display_licenses(Auth_main.url, Auth_main.token, Auth_main.username, Auth_main.password)
        elif command == 'server_id':
            response = License_main.get_serverID(Auth_main.url, Auth_main.token)
            print("\n   - serverId:", response)
        elif command == 'apply_license':
            license_id:str = License_main.post_license(url, token)
            License_main.put_license(url, token, license_id=license_id[0]) if license_id else print("Post license wasn't successful. Check the logs.")
        elif command == 'delete_active_license':
            License_main.delete_license(Auth_main.url, Auth_main.token, Auth_main.username, Auth_main.password)
        elif command == 'check_serverId_validation':
            if License_main.serverId_validation(Auth_main.url, Auth_main.token, Auth_main.username, Auth_main.password):
                print("ServerId is correct.")
            else:
                print("System has licenses with different server_id. Need to report to administrator.")


            ''' === User objects BLOCK === '''

        elif command == 'truncate_user_objects':
            User_main.delete_user_objects(Auth_main.url, Auth_main.token)
        elif command == 'truncate_user_objects_info':
            print(User_main.delete_user_objects.__doc__)


            ''' === TRANSFER DATA BLOCK === '''

            # Export data
        elif command in ('export_object_model', 'export_workflows', 'display_workflows', 'delete_workflows'):
            if Export_data_main.is_first_launch_export_data:
                Folder.create_folder(os.getcwd(), Export_data_main._transfer_folder)
                time.sleep(0.1)
                Folder.create_folder(os.getcwd() + '/' + Export_data_main._transfer_folder, Export_data_main._workflows_folder)
                time.sleep(0.1)
                Folder.create_folder(os.getcwd() + '/' + Export_data_main._transfer_folder, Export_data_main._object_model_folder)
                time.sleep(0.1)
                Export_data_main.is_first_launch_export_data = False
            if command == 'export_object_model':
                Export_data_main.export_server_info(Auth_main.url, Auth_main.token)
                Export_data_main.get_object_model(Export_data_main._object_model_file, Auth_main.url, Auth_main.token)
            elif command == 'export_workflows':
                Export_data_main.export_server_info(Auth_main.url, Auth_main.token)
                Export_data_main.export_workflows(Auth_main.url, Auth_main.token)
            elif command == 'display_workflows':
                Export_data_main.display_list_of_workflowsName_and_workflowsId(Auth_main.url, Auth_main.token)
            elif command == 'delete_workflows':
                Export_data_main.delete_workflows(Auth_main.url, Auth_main.token)

            # Import data
        elif command == 'import_workflows':
            Import_data_main.import_workflows(Auth_main.url, Auth_main.token)
        elif command == 'import_object_model':
            Import_data_main.import_object_model(Auth_main.url, Auth_main.token)

            # Clean transfer data storage
        elif command == 'clean_transfer_files_directory':
            Folder.clean_folder(f"{os.getcwd()}/{Export_data_main._transfer_folder}/{Export_data_main._object_model_folder}")
            Folder.clean_folder(f"{os.getcwd()}/{Export_data_main._transfer_folder}/{Export_data_main._workflows_folder}")
            File.remove_file(f"{os.getcwd()}/{Export_data_main._transfer_folder}/export_server.info")

        # --------Transfer data END-------------

        # User
        elif command == 'user_access_token':
            print(Auth_main.token)


if __name__ == '__main__':
    main()

