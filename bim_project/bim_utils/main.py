#
# Script for work with license and some other small features.

from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
disable_warnings(InsecureRequestWarning)
import app_menu
import auth
import user
import license
import export_data
import import_data
from tools import Folder
import logs # activates with import
import os

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



    while True:
        command = AppMenu_main.define_purpose_and_menu()

        # check privileges for everything related in tuple below
        if command in ('check_license', 'server_id', 'apply_license', 'delete_active_license', 'export_workflows', 'export_object_model', 'import_workflows', 'import_object_model'):
            License_main.privileges_check_count += 1
            if License_main.privileges_check_count == 1 and not License_main.check_permissions(Auth_main.url, Auth_main.token, Auth_main.username, Auth_main.password):
                License_main.privileges_granted = User_main.create_or_activate_superuser(Auth_main.url, Auth_main.token)

        ### LICENSE BLOCK BEGIN ###
        if command == 'check_license':
            License_main.display_licenses(Auth_main.url, Auth_main.token, Auth_main.username, Auth_main.password)
        elif command == 'server_id':
            print(f"\n   - serverId: {License_main.get_serverID(Auth_main.url, Auth_main.token)}")
        elif command == 'apply_license':
            License_main.put_license(Auth_main.url, Auth_main.token, Auth_main.username, Auth_main.password)
        elif command == 'delete_active_license':
            License_main.delete_license(Auth_main.url, Auth_main.token, Auth_main.username, Auth_main.password)
        ### THE END OF LICENSE BLOCK ###

        ### USER OBJECTS TABLE BEGIN ###
        elif command == 'truncate_user_objects':
            User_main.delete_user_objects(Auth_main.url, Auth_main.token)
        elif command == 'truncate_user_objects_info':
            print(User_main.delete_user_objects.__doc__)
        ### THE END OF USER OBJECTS ###

        ### EXPORT BEGIN###
        elif command == 'export_object_model' or command == 'export_workflows':
            if Export_data_main.is_first_launch_export_data:
                Folder.create_folder(os.getcwd(), Export_data_main.transfer_folder)
                Export_data_main.is_first_launch_export_data = False
            if command == 'export_object_model':
                Folder.create_folder(os.getcwd() + '/' + Export_data_main.transfer_folder, Export_data_main.object_model_folder)
                Export_data_main.export_server_info(Auth_main.url, Auth_main.token)
                Export_data_main.get_object_model(Export_data_main.object_model_file, Auth_main.url, Auth_main.token)
            elif command == 'export_workflows':
                Folder.create_folder(os.getcwd() + '/' + Export_data_main.transfer_folder, Export_data_main.workflows_folder)
                Export_data_main.export_server_info(Auth_main.url, Auth_main.token)
                Export_data_main.export_workflows(Auth_main.url, Auth_main.token)
        ### THE END OF EXPORT ###

        ### IMPORT BEGIN ###
        elif command == 'import_workflows':
            Import_data_main.import_workflows(Auth_main.url, Auth_main.token)
        elif command == 'import_object_model':
            Import_data_main.import_object_model(Auth_main.url, Auth_main.token)
        ### THE END OF IMPORT ###

        ### GENERIC ###
        elif command == 'clean_transfer_files_directory':
            Folder.clean_folder(os.getcwd() + '/' + Export_data_main.transfer_folder)        
        elif command in ('q', 'connect_to_another_server'):
            if License_main.privileges_granted:
                User_main.delete_superuser_system_role_and_delete_superuser(Auth_main.url, Auth_main.username, Auth_main.password, Auth_main.providerId)
            if command == 'q':
                break
            else:
                License_main.privileges_granted = False
                if not Auth_main.establish_connection():
                    return False




if __name__=='__main__':
    main()

