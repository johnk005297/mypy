import argparse
from datetime import datetime


class Parser():

    def __init__(self):
        pass

    @classmethod
    def get_parser(cls):
        """ Function for parsing arguments of the command line. """

        # create top-level parser with arguments and subparser
        parser = argparse.ArgumentParser(prog="bim-utils", description="Frankenstein's CLI for work with Bimeister(licenses/workflows/featureToggles/roleModes), gitlab, vCenter, etc.")
        parser.add_argument('-V', '--version', required=False, action='store_true', help='Get version of the bim_utils')
        parser.add_argument('--url', required=False, help='Url to get bimeister version')
        subparser = parser.add_subparsers(dest='command', required=False)

        # create parser and subparser for the "vsphere" command
        vsphere_parser = subparser.add_parser('vsphere', help='Perform operations in vSphere')
        vsphere_parser.add_argument('-u', '--user', required=False, help='Login account for vCenter')
        vsphere_parser.add_argument('-p', '--password', required=False, help='Password for vCenter')
        vsphere_subparser = vsphere_parser.add_subparsers(dest='vsphere_command')

        list_vm_parser = vsphere_subparser.add_parser('list-vm', help='Print VMs in implementation cluster')
        list_vm_parser.add_argument('-f', '--filter', required=False, help='Filter VMs by occurrences in the name using regular expressions')
        list_vm_parser.add_argument('--exclude', required=False, help='Full VM name to exclude from filter')
        list_vm_parser.add_argument('--powered-on', required=False, action='store_true', help='Print only VM with POWERED_ON status')

        show_snap_parser = vsphere_subparser.add_parser('show-snap', help='Print list of snapshots for a given VMs')
        show_snap_parser.add_argument('-f', '--filter', required=True, help='Filter VMs by occurrences in the name using regular expressions')
        show_snap_parser.add_argument('--exclude', required=False, help='Full VM name to exclude from filter')

        revert_snap_parser = vsphere_subparser.add_parser('revert-snap', help='Revert to snapshot for a given VMs')
        revert_snap_parser.add_argument('--name', required=True, help='Snapshot name')
        revert_snap_parser.add_argument('-f', '--filter', required=False, help='Filter VMs by occurrences in the name using regular expressions')
        revert_snap_parser.add_argument('--exclude', required=False, help='Full VM name to exclude from filter')

        remove_snap_parser = vsphere_subparser.add_parser('remove-snap', help='Remove snapshot from vCenter')
        remove_snap_parser.add_argument('--name', required=True, help='Snapshot name')
        remove_snap_parser.add_argument('-f', '--filter', required=False, help='Filter VMs by occurrences in the name using regular expressions')
        remove_snap_parser.add_argument('--exclude', required=False, help='Full VM name to exclude from filter')

        take_snap_parser = vsphere_subparser.add_parser('take-snap', help='Take snaphost for a given VMs')
        take_snap_parser.add_argument('--name', required=False, default='{}'.format(datetime.today().strftime("%d.%m.%Y_%H:%M:%S")), help='vSphere snapshot name')
        take_snap_parser.add_argument('--desc', required=False, default=' ', help='Description for a snapshot')
        take_snap_parser.add_argument('-f', '--filter', required=True, help='Filter VMs by occurrences in the name using regular expressions')
        take_snap_parser.add_argument('--exclude', required=False, help='Full VM name to exclude from filter')

        replace_snap_parser = vsphere_subparser.add_parser('replace-snap', help='Replace one snapshot in vSphere to another for a given VMs')
        replace_snap_parser.add_argument('-f', '--filter', required=True, help='Filter VMs by occurrences in the name using regular expressions')
        replace_snap_parser.add_argument('--exclude', required=False, help='Full VM name to exclude from filter')
        replace_snap_parser.add_argument('--old', required=True, help='Old snapshot to delete')
        replace_snap_parser.add_argument('--new', required=False, default='{}'.format(datetime.today().strftime("%d.%m.%Y_%H:%M:%S")), help='New snapshot to create')
        replace_snap_parser.add_argument('--desc', required=False, default=' ', help='Description for a snapshot')

        start_vm_parser = vsphere_subparser.add_parser('start-vm', help='Start select VMs in vSphere')
        start_vm_parser.add_argument('-f', '--filter', required=True, help='Filter VMs by occurrences in the name using regular expressions')
        start_vm_parser.add_argument('--exclude', required=False, help='Full VM name to exclude from filter')

        stop_vm_parser = vsphere_subparser.add_parser('stop-vm', help='Stop select VMs in vSphere')
        stop_vm_parser.add_argument('-f', '--filter', required=True, help='Filter VMs by occurrences in the name using regular expressions')
        stop_vm_parser.add_argument('--exclude', required=False, help='Full VM name to exclude from filter')

        restart_vm_parser = vsphere_subparser.add_parser('restart-vm', help='Perform guest OS reboot for VMs in implementation cluster')
        restart_vm_parser.add_argument('--exclude', required=False, help='Full VM name to exclude from filter')
        restart_vm_group = restart_vm_parser.add_mutually_exclusive_group(required=False)
        restart_vm_group.add_argument('-f', '--filter', required=False, help='Filter VMs by occurrences in the name using regular expressions')
        restart_vm_group.add_argument('--all', required=False, action='store_true', help='Restart all working VMs in implementation cluster')

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
        sql_parser.add_argument('--get-users', required=False, nargs='?', const='*', help='Get list of users')
        sql_parser.add_argument('--get-db', required=False, nargs='?', const='*', help="Get list of databases by it's name pattern. Default all")
        sql_parser.add_argument('--get-tables', required=False, nargs='?', const='*', help="Get list of the DB tables by it's name pattern. Default all")
        sql_parser.add_argument('--create-user-ro', required=False, nargs='?', const='bimeister_user_ro', help='Create db user with read-only access')
        sql_parser.add_argument('--read-by-line', required=False, action='store_true', help='Read .sql file line by line delimited by semicolons. \
                                This flag forces to read all the data from .sql file')
        # sql_parser.add_argument('--name', required=False, default=os.getenv('USERNAME_RO'), help='Set name for created user')
        # sql_parser.add_argument('-urp', '--user-ro-pass', required=False, default=os.getenv('USERNAME_RO_PASS'), help='Set password for created user')
        # sql_parser.add_argument('--mdm', required=False, help='Switch ExternalKey value to production or test. Requires for MDM connector integration')
        sql_parser.add_argument('--chunk-size', required=False, type=int, default=10_000, help='Adjust chunks of pulled data from database during select large amount of data')
        print_exclusive_group = sql_parser.add_mutually_exclusive_group(required=False)
        print_exclusive_group.add_argument('--print', required=False, action='store_true', help='Print content of dataframe on a screen')
        print_exclusive_group.add_argument('--print-max', required=False, action='store_true', help='Print full content of dataframe on a screen')
        matviews_exclusive_group = sql_parser.add_mutually_exclusive_group(required=False)
        matviews_exclusive_group.add_argument('-gmv', '--get-matviews', required=False, nargs='?', const='*', help="Get list of materialized views by it's name pattern. Default all")
        matviews_exclusive_group.add_argument('-dmv', '--drop-matviews', required=False, nargs='?', const='*', help="Delete materialized views by it's name pattern. Default all")
        matviews_exclusive_group.add_argument('-rmv', '--refresh-matviews', required=False, nargs='?', const='*', help='Refresh materialized views created by implementation department')
        matviews_exclusive_group.add_argument('-f', '--file', required=False, help='Sql filename containing a query')

        # create parser for the "git" subcommand
        git_parser = subparser.add_parser('git', help='Get info from product-collection.yaml. Search branches, tags, commits in git')
        git_parser.add_argument('-lbf', '--ls-branch-folder', required=False, help='Prints a list of files and folders for a given branch')
        git_parser.add_argument('--build-charts', required=False, help='Requires commit to activate "Build Charts" job.')
        git_parser.add_argument('-p', '--project-name', required=False, help='Option allows to provide project name from the product-collection.yaml without prompt')
        git_group = git_parser.add_mutually_exclusive_group(required=False)
        git_group.add_argument('-s', '--search', required=False, nargs='+', help='Search for branches and tags by it\'s name')
        git_group.add_argument('--commit', required=False, help='Get info from the product-collection.yaml file for a specific commit')
        git_group.add_argument('--compare', required=False, nargs=2, help='Compare two commits for difference in product-collection.yaml in DBs list and services list')
        git_group.add_argument('-st', '--search-tag', required=False, nargs='+', help='Search for a tag by it\'s name')

        # create parser for issuing new licenses
        issue_license = subparser.add_parser('issue-lic', help='Issue a new license from the license server')
        sid_url_group = issue_license.add_mutually_exclusive_group(required=True)
        sid_url_group.add_argument('-sid', '--serverId', required=False, help='Parameter of the license: serverID. Server which requires a license. Default value: None')
        issue_license.add_argument('-v', '--version', required=False, default=1, type=int, help='Parameter of the license: version. Default value: 1')
        issue_license.add_argument('-pr', '--product', required=False, default='Bimeister', help='Parameter of the license: product. Default value: Bimeister')
        issue_license.add_argument('-ltype', '--licenceType', required=False, default='Trial', help='Parameter of the license: licenceType. Default value: Trial')
        issue_license.add_argument('-atype', '--activationType', required=False, default='Offline', help='Parameter of the license: activationType. Default value: Offline')
        issue_license.add_argument('-c', '--client', required=False, default='', help='Parameter of the license: client. Default value: None')
        issue_license.add_argument('-email', '--clientEmail', required=False, default='', help='Parameter of the license: clientEmail. Default value: None')
        issue_license.add_argument('-org', '--organization', required=False, default='', help='Parameter of the license: organization. Default value: None')
        issue_license.add_argument('-isOrg', '--isOrganization', required=False, default=False, help='Parameter of the license: isOrganization. Default value: False')
        issue_license.add_argument('-nou', '--numberOfUsers', required=False, default=50, type=int, help='Parameter of the license: numberOfUsers. Default value: 50')
        issue_license.add_argument('-uip', '--numberOfIpConnectionsPerUser', required=False, default=0, type=int, help='Parameter of the license: numberOfIpConnectionsPerUser. Default value: 0')
        issue_license.add_argument('-p', '--period', default=3, required=False, type=int, help='Period of the license in months. Default value: 3')
        issue_license.add_argument('--until', required=False, help='Date until the license is valid in format YYYY-MM-DD e.g. 2025-12-26')
        issue_license.add_argument('-oId', '--orderId', required=False, default='', help='Parameter of the license: orderId. Default value: None')
        issue_license.add_argument('-crmId', '--crmOrderId', required=False, default='', help='Parameter of the license: crmOrderId. Default value: None')
        issue_license.add_argument('-s', '--save', required=False, action='store_true', help='Save license into a file')
        issue_license.add_argument('--print', required=False, action='store_true', help='Print license on a screen')
        sid_url_group.add_argument('--url', required=False, help='URL endpoint which needs a license to activate')
        issue_license.add_argument('-u', '--user', required=False, default='admin', help='Username with access to web interface and privileges to work with licenses')
        issue_license.add_argument('-pw', '--password', required=False, default='Qwerty12345!', help='Password for the --user')
        issue_license.add_argument('--apply', required=False, action='store_true', help='Activate license for specified URL')

        # create parser for confluence
        ft = subparser.add_parser('ft', help='Get information about feature toggles from confluence')
        ft.add_argument('-suid', '--gazprom-suid', required=False, action='store_true', help='FT for the project Gazprom Suid')
        ft.add_argument('-dtoir', '--gazprom-dtoir', required=False, action='store_true', help='FT for the project Gazprom Dtoir')
        ft.add_argument('-salavat', '--gazprom-salavat', required=False, action='store_true', help='FT for the project Gazprom Salavat')
        ft.add_argument('-murmansk', '--novatek-murmansk', required=False, action='store_true', help='FT for the project Novatek Murmansk')
        ft.add_argument('-yamal', '--novatek-yamal', required=False, action='store_true', help='FT for the project Novatek Yamal')
        ft.add_argument('-crea', '--crea-cod', required=False, action='store_true', help='FT for the project Rosatom Crea-Cod')
        ft_save_group = ft.add_mutually_exclusive_group(required=False)
        ft_save_group.add_argument('--save', required=False, action='store_true', help='Save output in file')
        ft_save_group.add_argument('--save-pretty', required=False, action='store_true', help='Save output in file more human readable')

        # create parser for user access token
        token = subparser.add_parser('token', help='Get user access token for a given URL')
        token.add_argument('--url', required=True, help='URL of the stand whom access token is required')
        token.add_argument('-u', '--user', required=True, help='Username with access to Bimeister')
        token.add_argument('-p', '--password', required=True, help='User\'s password with access to Bimeister')
        token.add_argument('-pid', '--providerId', required=False, help='Pass providerId in cases where more the one providers had been set up')

        docker = subparser.add_parser('docker', help='Perform operations with Docker Engine')
        docker.add_argument('--list-images', required=False, action='store_true', help='Get list of images on a localhost')
        docker.add_argument('--save-images', required=False, action='store_true', help='Save docker image(s) in tgz archive')
        docker.add_argument('--push-images', required=False, action='store_true', help='Push images to the registry ##NOT READY')
        docker.add_argument('-u', '--user', required=False, help='Username with access to the registry')
        docker.add_argument('-p', '--password', required=False, help='User password with access to the registry')
        docker.add_argument('-ru', '--repo-url', required=False, help='Registry URL')
        docker.add_argument('-rn', '--repo-name', required=False, help='Repository name')
        docker.add_argument('-ref', '--image-ref', required=False, help='Image reference REPOSITORY[:TAG]')
        docker.add_argument('--tag', required=False, help='Image tag')
        docker.add_argument('--onefile', required=False, action='store_true', help='Pack tgz docker image(s) into single tar archive')
        docker.add_argument('--no-purge', required=False, action='store_false', help='Purge images from the docker after. Default value: False')
        docker_images_group = docker.add_mutually_exclusive_group(required=False)
        docker_images_group.add_argument('-f', '--file', required=False, help='Text file with a list of images')
        docker_images_group.add_argument('-i', '--images', required=False, help='Images names separated with whitespace')

        # create parser for passwork
        # passwork = subparser.add_parser('pk', help='Work with passwork vault')
        # passwork.add_argument('--url', required=False, help='')

        # mdm connector import config
        mdm_connector_parser = subparser.add_parser('mdm', help='Import MDM autosetup config file. Requires for MDM connector integration')
        mdm_connector_parser.add_argument('--url', required=True)
        mdm_connector_group = mdm_connector_parser.add_mutually_exclusive_group(required=True)
        mdm_connector_group.add_argument('--import-file', help='Point .json config file for MDM autosetup for import')
        mdm_connector_group.add_argument('--export-file', action='store_true', help='Export .json config file for MDM autosetup')
        return parser
    
    ## NOT READY ##
    @classmethod
    def parse_args_main(cls, user_command):
        """ Parse user command in main block """

        # create the top-level parser
        parser = argparse.ArgumentParser(description='Frankenstein CLI for work with licenses, workflows, featureToggles, etc.')
        parser.add_argument('--quit', required=False, metavar=('q', 'exit', 'quit'), action='store_true')


        # create main subparser
        subparser = parser.add_subparsers(dest='command', required=False)

        m_parser = subparser.add_parser('m', help='List available commands')
        exit_parser = subparser.add_parser('exit', help='Exit CLI')
        ft_parser = subparser.add_parser('ft', help='Command to work with feature toggles')
        ft_parser.add_argument('--list', required=False)
        ft_parser.add_argument('--on', required=False)

        args = parser.parse_args(user_command)
        return args
