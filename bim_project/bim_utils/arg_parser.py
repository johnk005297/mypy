import argparse
from datetime import datetime
import sys


class Parser():

    def __init__(self):
        pass

    @classmethod
    def parse_args(cls):
        """ Function for parsing arguments of the command line. """

        # create the top-level parser
        parser = argparse.ArgumentParser(prog='bim_utils', description='\'Frankenstein\' CLI for work with licenses, workflows, featureToggles, K8S/Docker logs, etc.')
        parser.add_argument('-V', '--version', required=False, action="store_true")
        parser.add_argument('--local', required=False, action="store_true", help='Execute script with locally available options on the current host')

        # create main subparser
        subparser = parser.add_subparsers(dest='command', required=False)

        # create parser for the "vsphere" subcommand
        vcenter_command = subparser.add_parser('vsphere', help='Performing operations with vSphere API')
        vcenter_command.add_argument('-u', '--user', required=False)
        vcenter_command.add_argument('-p', '--password', required=False)
        vcenter_command.add_argument('--exclude-vm', type=str, nargs='+', required=False, help='A list of VMs to be excluded from the reboot OS')

        # create subparsers for the "vsphere" subcommand
        vcenter_subcommand = vcenter_command.add_subparsers(help='Subcommands for "vsphere" command')
        vcenter_list_vm = vcenter_subcommand.add_parser('list-vm', help='Print VMs in implementation cluster')
        vcenter_list_vm.add_argument('--filter', required=False, help='Filter VMs by occurrences in the name')
        vcenter_list_vm.add_argument('--powered-on', required=False, action="store_true", help='Print only VM with POWERED_ON status')
        vcenter_take_snap = vcenter_subcommand.add_parser('take-snap', help='Take snaphost for a given VMs')
        vcenter_take_snap.add_argument('--name', required=False, default='{}'.format(datetime.today().strftime("%d.%m.%Y")), help='vSphere snapshot name')
        vcenter_take_snap.add_argument('--desc', required=False, default=' ', help='Description for a snapshot')
        vcenter_take_snap.add_argument('--filter', required=True, help='Filter VMs by occurrences in the name')
        vcenter_start_vm = vcenter_subcommand.add_parser('start-vm', help='Start select VMs in vSphere')
        vcenter_start_vm.add_argument('--filter', required=True, help='Filter VMs by occurrences in the name')
        vcenter_stop_vm = vcenter_subcommand.add_parser('stop-vm', help='Start select VMs in vSphere')
        vcenter_stop_vm.add_argument('--filter', required=True, help='Filter VMs by occurrences in the name')
        vcenter_restart_vm = vcenter_subcommand.add_parser('restart-vm', help='Perform guest OS reboot for VMs in implementation cluster')
        vcenter_restart_vm_options = vcenter_restart_vm.add_mutually_exclusive_group(required=False)
        vcenter_restart_vm_options.add_argument('--filter', required=False, help='Filter VMs by occurrences in the name')
        vcenter_restart_vm_options.add_argument('--all', required=False, action="store_true", help='Restart all working VMs in implementation cluster')
        vcenter_restart_vm.add_argument('--exclude-vm', type=str, nargs='+', required=False, help='A list of VMs to be excluded from the reboot OS')

        # create parser for the "drop-UO" subcommand
        user_obj = subparser.add_parser('drop-UO', help='Truncate bimeisterdb.UserObjects table')
        user_obj.add_argument('--url', help='Provide URL to the web.', required=True)
        user_obj.add_argument('-u', '--user', required=False)
        user_obj.add_argument('-p', '--password', required=False)

        # create parser for the "sql" subcommand
        sql = subparser.add_parser('sql', help='Execute sql query provided in a *.sql file')
        sql.add_argument('-s', '--host', required=True, help='DB hostname or IP address')
        sql.add_argument('-d', '--db', required=True, help='DB name')
        sql.add_argument('-u', '--user', required=True, help='Username with access to db')
        sql.add_argument('-pw', '--password', required=False, help='DB user password')
        sql.add_argument('-p', '--port', required=True, help='DB port')
        sql.add_argument('-o', '--out', required=False, action="store_true", help='Output context of the saved .csv file')
        sql_mdm_connection = sql.add_mutually_exclusive_group(required=False)
        sql_mdm_connection.add_argument('--mdm-prod', action="store_true", help='Switch ExternalKey value to production. Requires for MDM connector integration', required=False)
        sql_mdm_connection.add_argument('--mdm-test', action="store_true", help='Switch ExternalKey value to test. Requires for MDM connector integration', required=False)
        sql_exclusive = sql.add_mutually_exclusive_group(required=False)
        sql_exclusive.add_argument('-lmv', '--list-matviews', action='store_true', help='Get list of materialized views created by implementation department', required=False)
        sql_exclusive.add_argument('-dmv', '--drop-matviews', action='store_true', help='Delete materialized views created by implementation department', required=False)
        sql_exclusive.add_argument('-rmv', '--refresh-matviews', action='store_true', help='Refresh materialized views created by implementation department', required=False)
        sql_exclusive.add_argument('-f', '--file', required=False, help='Sql filename containing a query')

        # create parser for the "product-list" subcommand
        product_list = subparser.add_parser('product-list', help='Get list of services and DB for a specific project from product-collection.yaml')
        product_list.add_argument('-lbf', '--list-branch-folder', required=False, help='Prints the list of files and folders for a given branch')
        product_list.add_argument('-p', '--project-name', required=False, help='Provide project name from the product-collection.yaml without prompt')
        product_list_group = product_list.add_mutually_exclusive_group(required=False)
        product_list_group.add_argument('-sb', '--search-branch', required=False, nargs='+', help='Get a list of branch names from GitLab')
        product_list_group.add_argument('--commit', required=False, help='Get info from the product-collection.yaml file for a specific commit')
        product_list_group.add_argument('--compare', required=False, nargs=2, help='Compare two commits for difference in product-collection.yaml in DBs list and services list')

        # create parser for the "bim-version" subcommand
        bim_version = subparser.add_parser('bim-version', help='Get bimeister version information')
        bim_version.add_argument('-u', '--url', required=True)        
        args = parser.parse_args()
        return args