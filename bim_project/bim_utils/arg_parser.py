import argparse
from datetime import datetime


class Parser():

    def __init__(self):
        pass

    @classmethod
    def parse_args(cls):
        """ Function for parsing arguments of the command line. """

        # create the top-level parser
        parser = argparse.ArgumentParser(description='Frankenstein CLI for work with licenses, workflows, featureToggles, K8S/Docker logs, etc.')
        parser.add_argument('-V', '--version', required=False, action="store_true", help='Get version of the bim_utils')
        parser.add_argument('--local', required=False, action="store_true", help='Execute script with locally available options on the current host')

        # create main subparser
        subparser = parser.add_subparsers(dest='command', required=False)

        # create parent parser for "vsphere" subcommand
        vcenter_parent_parser = argparse.ArgumentParser(add_help=False)
        vcenter_parent_parser.add_argument('-u', '--user', required=False, help='Login account for vCenter')
        vcenter_parent_parser.add_argument('-p', '--password', required=False, help='Password for vCenter')
        # create parser for the "vsphere" subcommand
        vcenter_command = subparser.add_parser('vsphere', help='Performing operations with vSphere API')
        # create subparsers for the "vsphere" subcommand
        vcenter_subcommand = vcenter_command.add_subparsers(help='Subcommands for "vsphere" command')
        vcenter_list_vm_parser = vcenter_subcommand.add_parser('list-vm', help='Print VMs in implementation cluster', parents=[vcenter_parent_parser])
        vcenter_list_vm_parser.add_argument('--filter', required=False, help='Filter VMs by occurrences in the name')
        vcenter_list_vm_parser.add_argument('--powered-on', required=False, action="store_true", help='Print only VM with POWERED_ON status')
        vcenter_list_snap_parser = vcenter_subcommand.add_parser('show-snap', help='Print list of snapshots for a given VMs', parents=[vcenter_parent_parser])
        vcenter_list_snap_parser.add_argument('--filter', required=True, help='Filter VMs by occurrences in the name')
        vcenter_revert_snap_parser = vcenter_subcommand.add_parser('revert-snap', help='Revert to snapshot for a given VMs', parents=[vcenter_parent_parser])
        vcenter_revert_snap_parser.add_argument('--filter', required=False, help='Filter VMs by occurrences in the name')
        vcenter_take_snap_parser = vcenter_subcommand.add_parser('take-snap', help='Take snaphost for a given VMs', parents=[vcenter_parent_parser])
        vcenter_take_snap_parser.add_argument('--name', required=False, default='{}'.format(datetime.today().strftime("%d.%m.%Y_%H:%M:%S")), help='vSphere snapshot name')
        vcenter_take_snap_parser.add_argument('--desc', required=False, default=' ', help='Description for a snapshot')
        vcenter_take_snap_parser.add_argument('--filter', required=True, help='Filter VMs by occurrences in the name')
        vcenter_start_vm_parser = vcenter_subcommand.add_parser('start-vm', help='Start select VMs in vSphere', parents=[vcenter_parent_parser])
        vcenter_start_vm_parser.add_argument('--filter', required=True, help='Filter VMs by occurrences in the name')
        vcenter_stop_vm_parser = vcenter_subcommand.add_parser('stop-vm', help='Start select VMs in vSphere', parents=[vcenter_parent_parser])
        vcenter_stop_vm_parser.add_argument('--filter', required=True, help='Filter VMs by occurrences in the name')
        vcenter_restart_vm_parser = vcenter_subcommand.add_parser('restart-vm', help='Perform guest OS reboot for VMs in implementation cluster', parents=[vcenter_parent_parser])
        vcenter_restart_vm_options = vcenter_restart_vm_parser.add_mutually_exclusive_group(required=False)
        vcenter_restart_vm_options.add_argument('--filter', required=False, help='Filter VMs by occurrences in the name')
        vcenter_restart_vm_options.add_argument('--all', required=False, action="store_true", help='Restart all working VMs in implementation cluster')
        vcenter_restart_vm_parser.add_argument('--exclude-vm', type=str, nargs='+', required=False, help='A list of VMs to be excluded from the reboot OS')

        # create parser for the "drop-UO" subcommand
        user_obj_parser = subparser.add_parser('drop-UO', help='Truncate bimeisterdb.UserObjects table')
        user_obj_parser.add_argument('--url', help='Provide URL to the web.', required=True)
        user_obj_parser.add_argument('-u', '--user', required=False)
        user_obj_parser.add_argument('-p', '--password', required=False)

        # create parser for the "sql" subcommand
        sql_parser = subparser.add_parser('sql', help='Execute sql query provided in a *.sql file')
        sql_parser.add_argument('-s', '--host', required=True, help='DB hostname or IP address')
        sql_parser.add_argument('-d', '--db', required=True, help='DB name')
        sql_parser.add_argument('-u', '--user', required=True, help='Username with access to db')
        sql_parser.add_argument('-pw', '--password', required=False, help='DB user password')
        sql_parser.add_argument('-p', '--port', required=True, help='DB port')
        sql_parser.add_argument('-o', '--out', required=False, action="store_true", help='Print SQL query response on a screen')
        sql_parser.add_argument('--list-db', required=False, action="store_true", help='Print list of all databases')
        sql_mdm_connection = sql_parser.add_mutually_exclusive_group(required=False)
        sql_mdm_connection.add_argument('--mdm-prod', required=False, action="store_true", help='Switch ExternalKey value to production. Requires for MDM connector integration')
        sql_mdm_connection.add_argument('--mdm-test', required=False, action="store_true", help='Switch ExternalKey value to test. Requires for MDM connector integration')
        sql_exclusive = sql_parser.add_mutually_exclusive_group(required=False)
        sql_exclusive.add_argument('-lmv', '--list-matviews', required=False, nargs='?', const='*', help='Get list of materialized views created by implementation department')
        sql_exclusive.add_argument('-dmv', '--drop-matviews', required=False, nargs='?', const='*', help='Delete materialized views by it\'s name pattern')
        sql_exclusive.add_argument('-rmv', '--refresh-matviews', required=False, nargs='?', const='*', help='Refresh materialized views created by implementation department')
        sql_exclusive.add_argument('-f', '--file', required=False, help='Sql filename containing a query')

        # create parser for the "git" subcommand
        product_list_parser = subparser.add_parser('git', help='Get info from product-collection.yaml. Search branches, tags, commits in git')
        product_list_parser.add_argument('-lbf', '--list-branch-folder', required=False, help='Prints a list of files and folders for a given branch')
        product_list_parser.add_argument('-p', '--project-name', required=False, help='Option allows to provide project name from the product-collection.yaml without prompt')
        product_list_group = product_list_parser.add_mutually_exclusive_group(required=False)
        product_list_group.add_argument('-sb', '--search-branch', required=False, nargs='+', help='Search for a branch by it\'s name')
        product_list_group.add_argument('--commit', required=False, help='Get info from the product-collection.yaml file for a specific commit')
        product_list_group.add_argument('--compare', required=False, nargs=2, help='Compare two commits for difference in product-collection.yaml in DBs list and services list')
        product_list_group.add_argument('-st', '--search-tag', required=False, nargs='+', help='Search for a tag by it\'s name')

        # create parser for the "bim-version" subcommand
        bim_version = subparser.add_parser('bim-version', help='Get bimeister version information')
        bim_version.add_argument('-u', '--url', required=True)
        args = parser.parse_args()
        return args
    
    @classmethod
    def parse_args_main(cls, user_command):
        """ Parse user command in main block """

        # create the top-level parser
        parser = argparse.ArgumentParser(description='Frankenstein CLI for work with licenses, workflows, featureToggles, K8S/Docker logs, etc.')
        parser.add_argument('--quit', required=False, metavar=('q', 'exit', 'quit'), action="store_true")


        # create main subparser
        subparser = parser.add_subparsers(dest='command', required=False)

        m_parser = subparser.add_parser('m', help='List available commands')
        exit_parser = subparser.add_parser('exit', help='Exit CLI')
        ft_parser = subparser.add_parser('ft', help='Command to work with feature toggles')
        ft_parser.add_argument('--list', required=False)
        ft_parser.add_argument('--on', required=False)

        args = parser.parse_args(user_command)
        return args