#!/usr/bin/env python
import logging
import mlogger
import sys
import app_menu
import auth
import license
import import_data
import postgre
import vsphere
import time
import confluence
import platform
# import rlcompleter
import interactive_menu
import readline
from parser import Parser
from passwork import *
from git import Git
from rich.live import Live
from rich.table import Table
from rich.console import Console
from getpass import getpass
from tools import Bimeister

# block for correct build with pyinstaller, to add .env file
from dotenv import load_dotenv
extDataDir = os.getcwd()
if getattr(sys, 'frozen', False):
    extDataDir = sys._MEIPASS
load_dotenv(dotenv_path=os.path.join(extDataDir, '.env'))

# opportunity to have access of input history
if platform.system() == 'Windows':
    import pyreadline3
else:
    import readline
    # readline.set_completer(rlcompleter.Completer().complete)
    # readline.parse_and_bind('tab: complete')


if __name__ == '__main__':
    logs = mlogger.Logs()
    logger = mlogger.file_logger(logs.filepath, logLevel=logging.INFO)
    parser = Parser().get_parser()
    args = parser.parse_args()
    try:
        if args.command == 'git':
            g = Git()
            project = g.project()
            branch = g.branch()
            product_collection = g.product_collection()
            job = g.job()
            tree = g.tree()
            project_id = project.get_project_id(project='bimeister')
            if not project_id:
                sys.exit()
            if args.search:
                data = branch.search_branches_commits_tags_jobs(project_id, args.search)
                g.display_table_with_branches_commits_tags_jobs(data)
            elif args.build_charts:
                branches: list = branch.get_branch_name_using_commit(project_id, args.build_charts)
                if len(branches) == 1:
                    branch_name = branches[0]
                else:
                    branch_name = input(f"{args.build_charts} commit appears in several branches: {branches}\nSelect branch: ")
                charts_jobs = job.get_specific_jobs(project_id, args.build_charts, branch_name)
                pipeline_id = charts_jobs['pipeline_id']
                if not pipeline_id:
                    print("No pipelines with 'success' status. Can't run the job.")
                    sys.exit()
                job.run_job(project_id, str(charts_jobs['build_chart']['id']).split())
            elif args.commit:
                file_content: dict = product_collection.get_product_collection_file_content(project_id, args.commit)
                if not file_content:
                    sys.exit()
                data = product_collection.parse_product_collection_yaml(file_content, project_name=args.project_name)
                if not data:
                    sys.exit()
                else:
                    project_name, services, db = data
                if not services or not db:
                    sys.exit()
                product_collection.print_services_and_db(services, db)
            elif args.compare:
                first_commit, second_commit = args.compare[0], args.compare[1]
                first_commit_data: dict = product_collection.get_product_collection_file_content(project_id, first_commit)
                second_commit_data: dict = product_collection.get_product_collection_file_content(project_id, second_commit)
                if not first_commit_data or not second_commit_data:
                    sys.exit()
                data = product_collection.parse_product_collection_yaml(first_commit_data)
                if not data:
                    sys.exit()
                first_commit_project_name, first_commit_services, first_commit_db = data
                data = product_collection.parse_product_collection_yaml(second_commit_data, project_name=first_commit_project_name)
                if not data:
                    sys.exit()
                second_commit_project_name, second_commit_services, second_commit_db = data
                product_collection.compare_two_commits(first_commit_services, first_commit_db, second_commit_services, second_commit_db)
            elif args.ls_branch_folder:
                tree.print_list_of_branch_files(project_id, args.ls_branch_folder)

        elif args.command == 'drop-UO':
            postgre.DB.drop_userObjects(args.url, username=args.user, password=args.password)

        elif args.command == 'sql':
            pg = postgre.DB()
            q = postgre.Queries()
            conn = pg.connect_to_db(db=args.db, host=args.host, user=args.user, password=args.password, port=args.port)
            if not conn:
                sys.exit()
            if args.file:
                pg.execute_query_from_file(conn, filepath=args.file, chunk_size=args.chunk_size)
            elif args.list_matviews:
                pg.execute_query(conn, query=q.get_matviews_list(args.list_matviews), query_name='matviews-list')
            elif args.drop_matviews:                
                pg.execute_query(conn, query=q.drop_materialized_view(args.drop_matviews), query_name='drop-matviews')
            elif args.refresh_matviews:
                pg.execute_query(conn, query=q.refresh_materialized_view(), query_name='refresh-matviews')
            elif args.mdm:
                if args.mdm == 'prod':
                    pg.execute_query(conn, query=q.swith_externalKey_for_mdm_connector(value='Prod'), query_name='swith-extkey-mdm-connector')
                elif args.mdm == 'test':
                    pg.execute_query(conn, query=q.swith_externalKey_for_mdm_connector(value='Test'), query_name='swith-extkey-mdm-connector')
                else: print("mdm option has two values: prod or test.")
            elif args.list_db:
                db_list = pg.execute_query(conn, query=q.get_list_of_all_db(), query_name='db-list')
            elif args.list_tables:
                pg.execute_query(conn, query=q.get_list_of_db_tables(), query_name='tables-list')
            elif args.create_user_ro:
                pg.execute_query(conn, query=q.create_postgresql_user_ro(args.name, args.user_ro_pass), query_name='create-user-ready-only')
            elif args.list_users:
                pg.execute_query(conn, query=q.get_list_of_users(), query_name='users-list')
                pg.print_list_of_users(pg.output_file)

        elif args.command == 'vsphere':
            v = vsphere.Vsphere()
            headers = v.get_headers(args.user, args.password)
            if not headers:
                sys.exit()
            elif args.vsphere_command == 'list-vm':
                exclude_vm: list = args.exclude.split() if args.exclude else []
                vm_array = v.get_array_of_vm(headers, exclude_vm, args.filter, args.powered_on)
                v.print_list_of_vm(vm_array)
            elif args.vsphere_command == 'restart-vm':
                if args.all:
                    confirm: bool = True if input("YOU ARE ABOUT TO RESTART ALL VM's IN THE CLUSTER!!! ARE YOU SURE?(YES|NO) ").lower() == 'yes' else False
                    if not confirm:
                        print("Restart procedure aborted!")
                        sys.exit()
                    exclude_vm: list = args.exclude.split() if args.exclude else []
                    vm_array = v.get_array_of_vm(headers, exclude_vm, powered_on=True)
                    v.restart_os(headers, vm_array)
                else:
                    exclude_vm: list = args.exclude.split() if args.exclude else []
                    vm_array = v.get_array_of_vm(headers, exclude_vm, args.filter, powered_on=True)
                    v.restart_os(headers, vm_array)
            elif args.vsphere_command == 'start-vm':
                exclude_vm: list = args.exclude.split() if args.exclude else []
                vm_array: dict = v.get_array_of_vm(headers, exclude_vm, args.filter)
                for value in vm_array.values():
                    v.start_vm(headers, value["moId"], value["name"])
            elif args.vsphere_command == 'stop-vm':
                exclude_vm: list = args.exclude.split() if args.exclude else []
                vm_array: dict = v.get_array_of_vm(headers, exclude_vm, args.filter)
                for value in vm_array.values():
                    v.stop_vm(headers, value["moId"], value["name"])
            elif args.vsphere_command == 'show-snap':
                exclude_vm: list = args.exclude.split() if args.exclude else []
                vm_array: dict = v.get_array_of_vm(headers, exclude_vm, args.filter)
                for value in vm_array.values():
                    snapshots: dict = v.get_vm_snapshots(headers, value["moId"], value["name"])
                    v.print_vm_snapshots(value["name"], snapshots)
                    print()
            elif args.vsphere_command in ('take-snap', 'revert-snap', 'remove-snap'):
                # Logic of snaps procedures:
                # get needed VMs -> power OFF -> take/revert/remove snaps -> restore power state
                exclude_vm: list = args.exclude.split() if args.exclude else []
                vm_array: dict = v.get_array_of_vm(headers, exclude_vm, args.filter)
                if not vm_array:
                    sys.exit("No VM were matched. Exit!")
                for vm in vm_array:
                    print(vm_array[vm]['name'])
                confirm = input("\nIs it correct VM list? (Y/N): ").lower()
                if confirm not in ('y', 'yes'):
                    sys.exit("Abort procedure!")
                for value in vm_array.values():
                    v.stop_vm(headers, value["moId"], value["name"], print_msg=False)

                console = Console()
                snap_name = args.name.strip()
                with console.status("[bold blue]Shutting down guest OS", spinner="earth") as status:
                    for value in vm_array.values():
                        count = 0
                        while count < 350:
                            count += 1
                            power_status = v.get_vm_power_state(headers, value["moId"])
                            status.update(f"[bold blue]Shutting down guest OS: {value['name']}")
                            time.sleep(1)
                            if power_status != "POWERED_OFF":
                                continue
                            elif power_status == "POWERED_OFF":
                                console.print(f"[bold magenta]Shutdown guest OS: {value['name']}[/bold magenta]  [green]✅[/green]", overflow="ellipsis")
                                break
                        else:
                            print(f"Couldn't stop {value['name']} within 5 minutes. Check VM status in vCenter. Exit!")
                            break
                if args.vsphere_command == 'take-snap':
                    with console.status("[bold magenta]Create snapshot", spinner="dots") as status:
                        for value in vm_array.values():
                            take_snap_status: bool = v.take_snapshot(headers, value['moId'], value['name'], snap_name=snap_name, description=args.desc)
                            time.sleep(1)
                            if take_snap_status:
                                console.print(f"[bold magenta]Create snapshot: {value['name']}[/bold magenta]  [green]✅[/green]")
                            else:
                                console.print(f"[bold magenta]Create snapshot: {value['name']}[/bold magenta]  [red]❌[/red]")

                elif args.vsphere_command == 'revert-snap':
                    with console.status("[bold magenta]Revert snapshot", spinner="dots") as status:
                        for value in vm_array.values():
                            snapshots: dict = v.get_vm_snapshots(headers, value['moId'], value['name'])
                            is_snap_exists: bool = False
                            for snap in snapshots.values():
                                if snap['snapName'].strip() == snap_name:
                                    is_snap_exists = True
                                    revert_snap_status = v.revert_to_snapshot(headers, snap['snapId'], value['name'], print_msg=False)
                                    time.sleep(1)
                                    if revert_snap_status:
                                        console.print(f"[bold magenta]Revert snapshot: {value['name']}[/bold magenta]  [green]✅[/green]")
                                    else:
                                        console.print(f"[bold magenta]Revert snapshot: {value['name']}[/bold magenta]  [red]❌[/red]")
                                    break
                            if not is_snap_exists:
                                console.print(f"[red]Incorrect snapshot name for VM: {value['name']}[/red]")

                elif args.vsphere_command == 'remove-snap':
                    with console.status("[bold magenta]Remove snapshot", spinner="dots") as status:
                        for value in vm_array.values():
                            snapshots: dict = v.get_vm_snapshots(headers, value['moId'], value['name'])
                            is_snap_exists: bool = False
                            for snap in snapshots.values():
                                if snap['snapName'].strip() == snap_name:
                                    is_snap_exists = True
                                    remove_snap_status = v.remove_vm_snapshot(headers, snap['snapId'], print_msg=False)
                                    time.sleep(1)
                                    if remove_snap_status:
                                        console.print(f"[bold magenta]Remove snapshot: {value['name']}[/bold magenta]  [green]✅[/green]")
                                    else:
                                        console.print(f"[bold magenta]Remove snapshot: {value['name']}[/bold magenta]  [red]❌[/red]")
                                    break
                            if not is_snap_exists:
                                console.print(f"[red]Incorrect snapshot name for VM: {value['name']}[/red]")

                # Restoring power state
                for value in vm_array.values():
                    with console.status(f"[bold blue]Starting VM: {value['name']}", spinner="dots") as status:
                        if value["power_state"] == "POWERED_ON":
                            v.start_vm(headers, value["moId"], value["name"], print_msg=False)
                        else: 
                            continue
                        count = 0
                        while count < 350:
                            count += 1
                            power_status = v.get_vm_power_state(headers, value["moId"])
                            status.update(f"[bold blue]Starting VM: {value['name']}")
                            time.sleep(1)
                            if power_status == "POWERED_OFF":
                                continue
                            elif power_status == "POWERED_ON":
                                console.print(f"[bold magenta]Power On VM: {value['name']}[/bold magenta]  [green]✅[/green]", overflow="ellipsis")
                                break
                        else:
                            print(f"Couldn't start {value['name']} within 5 minutes. Check VM status in vCenter!")
                            break

        elif args.command == 'mdm':
            mdm = import_data.Mdmconnector()
            url = mdm.check_url(args.url)
            if args.export_file:
                mdm.export_mdm_config(url)
            else:
                mdm.import_mdm_config(url, args.import_file)

        elif args.command == 'issue-lic':
            lic_issue = license.Issue()
            lic = license.License()
            if not tools.is_socket_available(lic_issue._license_server, lic_issue._license_server_port):
                print(f"Socket is NOT available on {lic_issue._license_server}:{lic_issue._license_server_port}\nCheck the log!")
                sys.exit()
            lic_username, lic_password = Tools.get_creds_from_env('LICENSE_USER', 'LICENSE_PASSWORD')
            if not lic_username or not lic_password:
                # logger.error("No 'LICENSE_USER' and 'LICENSE_PASSWORD' in .env file.")
                print("Enter credentials for license server:")
                lic_username = input("login: ")
                lic_password = getpass("password: ")
            token = lic_issue.get_token_to_issue_license(username=lic_username, password=lic_password)
            if args.serverId:
                server_license = lic_issue.issue_license(
                            token
                            ,version=args.version
                            ,product=args.product
                            ,licenceType=args.licenceType
                            ,activationType=args.activationType
                            ,client=args.client
                            ,clientEmail=args.clientEmail
                            ,organization=args.organization
                            ,isOrganization=args.isOrganization
                            ,numberOfUsers=args.numberOfUsers
                            ,numberOfIpConnectionsPerUser=args.numberOfIpConnectionsPerUser
                            ,serverId=args.serverId
                            ,period=args.period
                            ,until=args.until
                            ,orderId=args.orderId
                            ,crmOrderId=args.crmOrderId
                            ,save=args.save
                            ,url=args.url
                            ,print=args.print
                )
                sys.exit()
            if args.url:
                url = tools.is_url_available(args.url)
                if not url:
                    print(f"URL {args.url} is not available.")
                    sys.exit()
                else:
                    args.url = url
                auth = auth.Auth()
                check = auth.establish_connection(url=args.url, username=args.user, password=args.password)
                if not check:
                    sys.exit()
                success, message = lic.get_serverID(args.url, auth.token)
                if success:
                    server_id: str = message
                else:
                    print(f"Error: {message}")
                    sys.exit()
                server_license = lic_issue.issue_license(
                            token
                            ,version=args.version
                            ,product=args.product
                            ,licenceType=args.licenceType
                            ,activationType=args.activationType
                            ,client=args.client
                            ,clientEmail=args.clientEmail
                            ,organization=args.organization
                            ,isOrganization=args.isOrganization
                            ,numberOfUsers=args.numberOfUsers
                            ,numberOfIpConnectionsPerUser=args.numberOfIpConnectionsPerUser
                            ,serverId=server_id
                            ,period=args.period
                            ,until=args.until
                            ,orderId=args.orderId
                            ,crmOrderId=args.crmOrderId
                            ,save=args.save
                            ,url=args.url
                            ,print=args.print
                )
                if args.apply:
                    lic.apply_license(args.url, auth.token, args.user, args.password, license=server_license)
        elif args.command == 'pk':
            pass
        elif args.command == 'ft':
            conf = confluence.Conf()
            page = conf.get_confluence_page()
            data = conf.get_ft_data_of_all_projects(page)
            if len(sys.argv) == 2 or (len(sys.argv) == 3 and sys.argv[2].strip() == '--save') or (len(sys.argv) == 3 and sys.argv[2].strip() == '--save-pretty'):
                project = conf.choose_project()
                conf.display_ft_for_project(data, project, args.save, args.save_pretty)
            elif args.gazprom_suid:
                conf.display_ft_for_project(data, conf.project_name_suid, args.save, args.save_pretty)
            elif args.gazprom_dtoir:
                conf.display_ft_for_project(data, conf.project_name_dtoir, args.save, args.save_pretty)
            elif args.gazprom_salavat:
                conf.display_ft_for_project(data, conf.project_name_salavat, args.save, args.save_pretty)
            elif args.novatek_murmansk:
                conf.display_ft_for_project(data, conf.project_name_murmansk, args.save, args.save_pretty)
            elif args.novatek_yamal:
                conf.display_ft_for_project(data, conf.project_name_yamal, args.save, args.save_pretty)
            elif args.crea_cod:
                conf.display_ft_for_project(data, conf.project_name_crea_cod, args.save, args.save_pretty)
        elif args.version:
            if args.url:
                Bimeister.print_bim_version(args.url)
            else:
                print(app_menu.AppMenu.__version__)
        elif args.command == 'token':
            autht = auth.Auth()
            providers = autht.get_providerId(args.url, interactive=False)
            if providers and isinstance(providers, list) and len(providers) > 1 and not args.providerId:
                print("Provide needed id with flag --providerId")
                for provider in providers:
                    for k,v in provider.items():
                        print(k,v)
            elif providers and args.providerId:
                token = autht.get_user_access_token(args.url, args.user, args.password, args.providerId)
                print(token if token else '')
            elif providers and isinstance(providers, str):
                token = autht.get_user_access_token(args.url, args.user, args.password, providers)
                print(token if token else '')
        else:
            interactive_menu.launch_menu()
    except KeyboardInterrupt:
        print('\nKeyboardInterrupt')


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