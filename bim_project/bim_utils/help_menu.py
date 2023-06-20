#

class Help:


    def options_menu(self):
        ''' Display help menu if --help argument was provided. '''

        help_menu:str = "\nOptions:                                                                                                                                         \
                         \n                                                                                                                                                 \
                         \n  <run without arguments>      list of available commands will be provided in the menu                                                           \
                         \n  --docker                     list of docker options                                                                                            \
                         \n  --sql-query                  exec PostgreSQL query from the file                                                                               \
                         \n    usage: \
                         \n      bim_utils --sql-query --file query.sql --host sandbox-4 --db bimeisterdb --port 5432 --user postgres --password mypassword[optional]  "
        

        print(help_menu)