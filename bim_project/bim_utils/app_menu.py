#
class AppMenu:
    version = '1.28'


    def __getattr__(self, item):
        raise AttributeError("AppMenu class has no such attribute: " + item)


    def welcome_info_note(self):
        ''' first note to be displayed '''
        print(f"\nv{self.version}    \
                \nnote: applicable with BIM version 101 and higher.")

    def define_purpose_and_menu(self):
        ''' Define what the user would like to do '''

        self.menu_user_command = input("\nCommand (m for help): ").lower().strip()
        self._main_menu        =       "\nHelp:                                                    \
                                        \n                                                         \
                                        \n   License                                               \
                                        \n       1   check license                                 \
                                        \n       2   get serverId                                  \
                                        \n       3   apply new license                             \
                                        \n       4   delete active license                         \
                                        \n     112   check_serverId_consistency                    \
                                        \n                                                         \
                                        \n   Databases                                             \
                                        \n       5   clean bimeisterdb.UserObjects table           \
                                        \n      5i   info about UserObjects table                  \
                                        \n                                                         \
                                        \n   Transfer data                                         \
                                        \n       6   export object model                           \
                                        \n       7   export workflows                              \
                                        \n       8   import object model                           \
                                        \n       9   import workflows                              \
                                        \n   dsp_w   display workflows(name, id)                   \
                                        \n   del_w   delete workflows                              \
                                        \n      09   clean transfer_files folder                   \
                                        \n                                                         \
                                        \n   User:                                                 \
                                        \n       t   get user access token                         \
                                        \n                                                         \
                                        \n   Main:                                                 \
                                        \n       m   print this menu                               \
                                        \n       q   exit"
                                      # \n   c  connect to another server                    \  # Need to figure out the way to add connect to another server without re-running the script


        # License
        if self.menu_user_command   == '1':
            return 'check_license'
        elif self.menu_user_command == '2':
            return 'server_id'
        elif self.menu_user_command == '3':
            return 'apply_license'
        elif self.menu_user_command == '4':
            return 'delete_active_license'
        elif self.menu_user_command == '112':
            return 'check_serverId_validation'

        # Databases
        elif self.menu_user_command == '5':
            return 'truncate_user_objects'
        elif self.menu_user_command == '5i':
            return 'truncate_user_objects_info'
        
        # Transfer data
        elif self.menu_user_command == '6':
            return 'export_object_model'
        elif self.menu_user_command == '7':
            return 'export_workflows'
        elif self.menu_user_command == '8':
            return 'import_object_model'
        elif self.menu_user_command == '9':
            return 'import_workflows'
        elif self.menu_user_command == 'dsp_w':
            return 'display_workflows'
        elif self.menu_user_command == 'del_w':
            return 'delete_workflows'
        elif self.menu_user_command == '09':
            return 'clean_transfer_files_directory'

        # User
        elif self.menu_user_command == 't':
            return 'user_access_token'

        # Main
        if self.menu_user_command == 'm':
            return 'main_menu'
        elif self.menu_user_command == 'q':
            return 'q'



        ### To do list ###      
        elif self.menu_user_command == 'c':
            return 'connect_to_another_server'
