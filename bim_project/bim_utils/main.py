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


# ---------------------------------------------------------
#   TEST ZONE
# ---------------------------------------------------------

    
    






# ---------------------------------------------------------
# http://10.168.23.161
# ---------------------------------------------------------

    while True:
        command = AppMenu_main.define_purpose_and_menu()

        # check privileges for everything related in tuple below
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
            License_main.privileges_check_count += 1
            if License_main.privileges_check_count == 1 and not User_main.check_permissions(Auth_main.url, Auth_main.token, Auth_main.username, Auth_main.password, License_main._permissions_to_check):
                License_main.privileges_granted = User_main.create_or_activate_superuser(Auth_main.url, Auth_main.token)


        # ----------Generic BEGIN---------------
        if command == 'main_menu':
            print(AppMenu_main._main_menu)
        elif command in ('q', 'connect_to_another_server'): # connect to another server isn't realized yet
            if License_main.privileges_granted:
                User_main.delete_superuser_system_role_and_delete_superuser(Auth_main.url, Auth_main.username, Auth_main.password, Auth_main.providerId)
            if command == 'q':
                break   # Close the menu and exit from the script.
            else:
                License_main.privileges_granted = False
                License_main.privileges_check_count = 0
                if not Auth_main.establish_connection():
                    return False
        # ----------Generic END-----------------


        # ----------License BEGIN---------------
        elif command == 'check_license':
            License_main.display_licenses(Auth_main.url, Auth_main.token, Auth_main.username, Auth_main.password)
        elif command == 'server_id':
            print(f"\n   - serverId: {License_main.get_serverID(Auth_main.url, Auth_main.token)}")
        elif command == 'apply_license':
            License_main.put_license(Auth_main.url, Auth_main.token, Auth_main.username, Auth_main.password)
        elif command == 'delete_active_license':
            License_main.delete_license(Auth_main.url, Auth_main.token, Auth_main.username, Auth_main.password)
        elif command == 'check_serverId_validation':
            if License_main.serverId_validation(Auth_main.url, Auth_main.token, Auth_main.username, Auth_main.password):
                print("ServerId is correct.")
            else:
                print("System has licenses with different server_id. Need to report to administrator.")
        # ----------License END-----------------


        # ----------User objects BEGIN----------
        elif command == 'truncate_user_objects':
            User_main.delete_user_objects(Auth_main.url, Auth_main.token)
        elif command == 'truncate_user_objects_info':
            print(User_main.delete_user_objects.__doc__)
        # ----------User objects END------------


        # --------Transfer data BEGIN-----------

            # Export data
        elif command == 'export_object_model' or command == 'export_workflows' or command == 'display_workflows':
            if Export_data_main.is_first_launch_export_data:
                Folder.create_folder(os.getcwd(), Export_data_main._transfer_folder)
                Folder.create_folder(os.getcwd() + '/' + Export_data_main._transfer_folder, Export_data_main._workflows_folder)
                Folder.create_folder(os.getcwd() + '/' + Export_data_main._transfer_folder, Export_data_main._object_model_folder)
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
            Folder.clean_folder(os.getcwd() + '/' + Export_data_main._transfer_folder)
        # --------Transfer data END-------------

        # User
        elif command == 'user_access_token':
            print(Auth_main.token)




if __name__=='__main__':
    main()

