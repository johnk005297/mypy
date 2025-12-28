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
import mdocker
# import rlcompleter
import interactive_menu
from parser import Parser
from passwork import *
from git import Git
from rich.console import Console
from getpass import getpass
from tools import Bimeister, Tools, File
from dotenv import load_dotenv
load_dotenv(dotenv_path=Tools.get_resourse_path(".env"))


# opportunity to have access of input history
if platform.system() == 'Linux':
    import readline
    # readline.set_completer(rlcompleter.Completer().complete)
    # readline.parse_and_bind('tab: complete')


if __name__ == '__main__':
    logs = mlogger.Logs()
    logs.set_full_access_to_log_file(logs.filepath, 0o666)
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

        # elif args.command == 'drop-UO':
        #     postgre.DB.drop_userObjects(args.url, username=args.user, password=args.password)

        elif args.command == 'sql':
            sql_queries_folder: str = Tools.get_resourse_path('sql_queries')
            pg = postgre.DB()
            queries = postgre.Queries()
            conn = pg.connect_to_db(db=args.db, host=args.host, user=args.user, password=args.password, port=args.port)
            if not conn:
                sys.exit()
            pg.execute_query_from_file(conn, filepath=args.file, chunk_size=args.chunk_size, read_by_line=args.read_by_line, print_=args.print, print_max=args.print_max)
            if args.get_matviews:
                query = pg.get_list_matviews_query(filepath=os.path.join(sql_queries_folder, 'get_list_of_matviews.sql'))
                params: dict = {"name": args.get_matviews.replace('*', '%')}
                pg.exec_query(conn, query, output_file="matviews-list.csv", remove_output_file=True, params=params, print_=args.print)
            elif args.drop_matviews:
                pattern = args.drop_matviews.replace('*', '%')
                matviews_before: int = queries.count_matviews(pattern, conn)
                drop_matviews_query = pg.get_query(filepath=os.path.join(sql_queries_folder, 'drop_matviews.sql'), search_pattern=pattern)
                pg.exec_query(conn, drop_matviews_query, keep_conn=True)
                if not pg.get_query_status():
                    conn.close()
                    sys.exit()
                matviews_after: int = queries.count_matviews(pattern, conn)
                print(f"Deleted: {matviews_before - matviews_after}")
                conn.close()
            elif args.refresh_matviews:
                pattern = args.refresh_matviews.replace('*', '%')
                refresh_matviews_query = pg.get_query(filepath=os.path.join(sql_queries_folder, 'refresh_matviews.sql'), search_pattern=pattern)
                pg.exec_query(conn, refresh_matviews_query, keep_conn=True, print_elapsed_time=True)
                conn.close()
            # elif args.get_db:
            #     pg.execute_query_from_file(conn, filepath=os.path.join(sql_queries_folder, 'get_list_of_db.sql'), print_output=args.print, name=args.get_db.replace('*', '%'))
            # elif args.get_tables:
            #     pg.execute_query_from_file(conn, filepath=os.path.join(sql_queries_folder, 'get_list_of_db_tables.sql'), print_output=args.print, name=args.get_tables.replace('*', '%'))
            # elif args.get_users:
            #     pg.execute_query_from_file(conn, filepath=os.path.join(sql_queries_folder, 'get_list_of_all_db_users.sql'), print_output=args.print, name=args.get_users.replace('*', '%'))
            # elif args.create_user_ro:
            #     password: str = getpass("Create user password: ")
            #     pg.execute_query_from_file(conn, filepath=os.path.join(sql_queries_folder, 'create_user_ro.sql'), split_by_delimiter=True, print_output=args.print, name=args.create_user_ro, password=password)
            # elif args.mdm:
            #     if args.mdm == 'prod':
            #         pg.execute_query(conn_string, query=q.swith_externalKey_for_mdm_connector(value='Prod'), query_name='swith-extkey-mdm-connector')
            #     elif args.mdm == 'test':
            #         pg.execute_query(conn_string, query=q.swith_externalKey_for_mdm_connector(value='Test'), query_name='swith-extkey-mdm-connector')
            #     else: print("mdm option has two values: prod or test.")

        elif args.command == 'vsphere':
            v = vsphere.Vsphere()
            console = Console()
            headers = v.get_headers(args.user, args.password)
            exclude_vm: list = args.exclude.split() if args.exclude else []
            def take_snap(snap_name):
                for value in vm_array.values():
                    with console.status(f"[bold magenta]Create snapshot: {value['name']}[/bold magenta]", spinner="earth"):
                        take_snap_status: bool = v.take_snapshot(headers, value['moId'], value['name'], snap_name=snap_name, description=args.desc)
                        time.sleep(2)
                        if take_snap_status:
                            count = Tools.counter()
                            while True:
                                time.sleep(5)
                                if v.is_has_snap(headers, value['name'], snap_name):
                                    break
                                elif count() == 1200:
                                    sys.exit("Error: Couldn't take snapshot in 20 minutes. Abort procedure!")
                                    break
                                else:
                                    continue
                            console.print(f"[bold magenta]Create snapshot: {value['name']}[/bold magenta]  [green]✅[/green]")
                        else:
                            console.print(f"[bold magenta]Create snapshot: {value['name']}[/bold magenta]  [red]❌[/red]")
            def remove_snap(snap_name):
                for value in vm_array.values():
                    with console.status(f"[bold magenta]Remove snapshot: {value['name']}[/bold magenta]", spinner="earth"):
                        snapshots: dict = v.get_vm_snapshots(headers, value['moId'], value['name'])
                        is_snap_exists: bool = False
                        for snap in snapshots.values():
                            if snap['snapName'].strip() == snap_name:
                                is_snap_exists = True
                                remove_snap_status = v.remove_vm_snapshot(headers, snap['snapId'], print_msg=False)
                                time.sleep(2)
                                if remove_snap_status:
                                    count = Tools.counter()
                                    while True:
                                        time.sleep(5)
                                        if not v.is_has_snap(headers, value['name'], snap['snapName'].strip()):
                                            break
                                        elif count() == 1200:
                                            sys.exit("Error: Couldn't remove snapshot in 20 minutes. Abort procedure!")
                                            break
                                        else:
                                            continue
                                    console.print(f"[bold magenta]Remove snapshot: {value['name']}[/bold magenta]  [green]✅[/green]")
                                else:
                                    console.print(f"[bold magenta]Remove snapshot: {value['name']}[/bold magenta]  [red]❌[/red]")
                                break
                        if not is_snap_exists:
                            console.print(f"[red]No snapshot name '{snap_name}' for VM: {value['name']}[/red]")
            if not headers:
                sys.exit()
            elif args.vsphere_command == 'list-vm':
                vm_array: dict = v.get_array_of_vm(headers, exclude_vm, args.filter, args.powered_on)
                v.print_list_of_vm(vm_array)
            elif args.vsphere_command == 'restart-vm':
                console.rule(title="Reboot guest OS")
                if args.all:
                    confirm: bool = True if input("YOU ARE ABOUT TO RESTART ALL VM's IN THE CLUSTER!!! ARE YOU SURE?(YES|NO) ").lower() == 'yes' else False
                    if not confirm:
                        print("Restart procedure aborted!")
                        sys.exit()
                    vm_array: dict = v.get_array_of_vm(headers, exclude_vm, powered_on=True)
                    v.restart_os(headers, vm_array)
                else:
                    vm_array: dict = v.get_array_of_vm(headers, exclude_vm, args.filter, powered_on=True)
                    v.restart_os(headers, vm_array)
            elif args.vsphere_command == 'start-vm':
                console.rule(title="Power On virtual machine")
                vm_array: dict = v.get_array_of_vm(headers, exclude_vm, args.filter)
                for value in vm_array.values():
                    v.start_vm(headers, value["moId"], value["name"])
            elif args.vsphere_command == 'stop-vm':
                console.rule(title="Shutdown guest OS")
                vm_array: dict = v.get_array_of_vm(headers, exclude_vm, args.filter)
                for value in vm_array.values():
                    v.stop_vm(headers, value["moId"], value["name"])
            elif args.vsphere_command == 'show-snap':
                vm_array: dict = v.get_array_of_vm(headers, exclude_vm, args.filter)
                for value in vm_array.values():
                    snapshots: dict = v.get_vm_snapshots(headers, value["moId"], value["name"])
                    v.print_vm_snapshots(value["name"], snapshots)
                    print()
            elif args.vsphere_command in ('take-snap', 'revert-snap', 'remove-snap', 'replace-snap'):
                # Logic of snaps procedures:
                # get needed VMs -> power OFF -> take/revert/remove snaps -> restore power state
                vm_array: dict = v.get_array_of_vm(headers, exclude_vm, args.filter)
                if not vm_array:
                    sys.exit("No VM were matched. Exit!")
                for vm in vm_array:
                    print(vm_array[vm]['name'])
                confirm = input("\nIs it correct VM list? (Y/N): ").lower()
                if confirm not in ('y', 'yes'):
                    sys.exit("Abort procedure!")

                console.rule(title="Shutdown guest OS")
                for value in vm_array.values():
                    v.stop_vm(headers, value["moId"], value["name"])
                if args.vsphere_command == 'take-snap':
                    snap_name: str = args.name.strip()
                    console.rule(title="Create snaphost")
                    take_snap(snap_name)
                elif args.vsphere_command == 'revert-snap':
                    snap_name: str = args.name.strip()
                    console.rule(title="Revert virtual machine snapshot")
                    for value in vm_array.values():
                        with console.status(f"[bold magenta]Revert snapshot: {value['name']}[/bold magenta]", spinner="earth"):
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
                                console.print(f"[red]No snapshot name '{snap_name}' for VM: {value['name']}[/red]")
                elif args.vsphere_command == 'remove-snap':
                    snap_name: str = args.name.strip()
                    console.rule(title="Remove virtual machine snaphost")
                    remove_snap(snap_name)
                elif args.vsphere_command == 'replace-snap':
                    old_snap_name: str = args.old
                    new_snap_name: str = args.new
                    remove_snap(old_snap_name)
                    take_snap(new_snap_name)

                # Restoring power state
                console.rule(title="Power state restore")
                for value in vm_array.values():
                    if value["power_state"] == "POWERED_ON":
                        v.start_vm(headers, value["moId"], value["name"])

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
        elif args.command == 'docker':
            docker = mdocker.Docker()
            if not docker.is_connected:
                sys.exit()
            if args.list:
                images = docker.get_list_of_images()
                docker.print_images(images)
            elif args.save:
                if args.file:
                    data = File.read_file(args.file)
                    images = [image for image in data.split()]
                elif args.images:
                    images = [image for image in args.images.split()]
                else:
                    print("docker: error: one of the arguments -f/--file -i/--images is required")
                    sys.exit()
                pulled_images = docker.pull_images(images)
                docker.save_images(pulled_images, purge=args.no_purge, output=args.output)
        else:
            interactive_menu.launch_menu()
    except KeyboardInterrupt:
        print('\nKeyboardInterrupt')


# # check username and password in Passwork vaults
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