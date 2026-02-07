from rich.console import Console

import logging
import sys
import time
import platform
from getpass import getpass

import mlogger
import app_menu
import auth
import license
import import_data
import postgre
import vsphere
import mdocker
import interactive_menu
from featureToggle import Conf, FeatureToggle
from parser import Parser
from passwork import *
from git import Git
from tools import Bimeister, Tools, File
from dotenv import load_dotenv
load_dotenv(dotenv_path=Tools.get_resourse_path(".env"))


# opportunity to have access of input history
if platform.system() == 'Linux':
    import readline
    # readline.set_completer(rlcompleter.Completer().complete)
    # readline.parse_and_bind('tab: complete')

import typer
from git import git_app
from postgre import sql_app

if __name__ == '__main__':
    logs = mlogger.Logs()
    logs.set_full_access_to_log_file(logs.filepath, 0o666)
    logger = mlogger.file_logger(logs.filepath, logLevel=logging.INFO)

    app = typer.Typer()
    app.add_typer(git_app, name="git")
    app.add_typer(sql_app, name="sql")
    app()
    # sys.exit()
    # parser = Parser().get_parser()
    # args = parser.parse_args()
    # try:
    #     elif args.command == 'sql':
    #         sql_queries_folder: str = Tools.get_resourse_path('sql_queries')
    #         pg = postgre.DB()
    #         queries = postgre.Queries()
    #         conn = pg.connect_to_db(db=args.db, host=args.host, user=args.user, password=args.password, port=args.port)
    #         if not conn:
    #             sys.exit()
    #         pg.execute_query_from_file(conn, filepath=args.file, chunk_size=args.chunk_size, read_by_line=args.read_by_line, print_=args.print, print_max=args.print_max)
    #         if args.get_matviews:
    #             query = pg.get_list_matviews_query(filepath=os.path.join(sql_queries_folder, 'get_list_of_matviews.sql'))
    #             params: dict = {"name": args.get_matviews.replace('*', '%')}
    #             pg.exec_query(conn, query, output_file="matviews-list.csv", remove_output_file=True, params=params, print_=args.print)
    #         elif args.drop_matviews:
    #             pattern = args.drop_matviews.replace('*', '%')
    #             matviews_before: int = queries.count_matviews(pattern, conn)
    #             drop_matviews_query = pg.get_query(filepath=os.path.join(sql_queries_folder, 'drop_matviews.sql'), search_pattern=pattern)
    #             pg.exec_query(conn, drop_matviews_query, keep_conn=True)
    #             if not pg.get_query_status():
    #                 conn.close()
    #                 sys.exit()
    #             matviews_after: int = queries.count_matviews(pattern, conn)
    #             print(f"Deleted: {matviews_before - matviews_after}")
    #             conn.close()
    #         elif args.refresh_matviews:
    #             pattern = args.refresh_matviews.replace('*', '%')
    #             refresh_matviews_query = pg.get_query(filepath=os.path.join(sql_queries_folder, 'refresh_matviews.sql'), search_pattern=pattern)
    #             pg.exec_query(conn, refresh_matviews_query, keep_conn=True, print_elapsed_time=True)
    #             conn.close()
    #         # elif args.get_db:
    #         #     pg.execute_query_from_file(conn, filepath=os.path.join(sql_queries_folder, 'get_list_of_db.sql'), print_output=args.print, name=args.get_db.replace('*', '%'))
    #         # elif args.get_tables:
    #         #     pg.execute_query_from_file(conn, filepath=os.path.join(sql_queries_folder, 'get_list_of_db_tables.sql'), print_output=args.print, name=args.get_tables.replace('*', '%'))
    #         # elif args.get_users:
    #         #     pg.execute_query_from_file(conn, filepath=os.path.join(sql_queries_folder, 'get_list_of_all_db_users.sql'), print_output=args.print, name=args.get_users.replace('*', '%'))
    #         # elif args.create_user_ro:
    #         #     password: str = getpass("Create user password: ")
    #         #     pg.execute_query_from_file(conn, filepath=os.path.join(sql_queries_folder, 'create_user_ro.sql'), split_by_delimiter=True, print_output=args.print, name=args.create_user_ro, password=password)
    #         # elif args.mdm:
    #         #     if args.mdm == 'prod':
    #         #         pg.execute_query(conn_string, query=q.swith_externalKey_for_mdm_connector(value='Prod'), query_name='swith-extkey-mdm-connector')
    #         #     elif args.mdm == 'test':
    #         #         pg.execute_query(conn_string, query=q.swith_externalKey_for_mdm_connector(value='Test'), query_name='swith-extkey-mdm-connector')
    #         #     else: print("mdm option has two values: prod or test.")

    #     elif args.command == 'vsphere':
    #         v = vsphere.Vsphere()
    #         console = Console()
    #         headers = v.get_headers(args.user, args.password)
    #         def take_snap(snap_name):
    #             for value in vm_array.values():
    #                 with console.status(f"[bold magenta]Create snapshot: {value['name']}[/bold magenta]", spinner="earth") as status:
    #                     take_snap_status: bool = v.take_snapshot(headers, value['moId'], value['name'], snap_name=snap_name, description=args.desc)
    #                     time.sleep(0.5)
    #                     if take_snap_status:
    #                         count = Tools.counter()
    #                         while True:
    #                             time.sleep(5)
    #                             if v.is_has_snap(headers, value['name'], snap_name):
    #                                 break
    #                             elif count() == 1200:
    #                                 sys.exit("Error: Couldn't take snapshot in 20 minutes. Abort procedure!")
    #                                 break
    #                             else:
    #                                 continue
    #                         status.console.print(f"[bold magenta]Create snapshot: {value['name']}[/bold magenta]  [green]✅[/green]")
    #                     else:
    #                         status.console.print(f"[bold magenta]Create snapshot: {value['name']}[/bold magenta]  [red]❌[/red]")
    #         def remove_snap(snap_name):
    #             for value in vm_array.values():
    #                 with console.status(f"[bold magenta]Remove snapshot: {value['name']}[/bold magenta]", spinner="earth") as status:
    #                     snapshots: dict = v.get_vm_snapshots(headers, value['moId'], value['name'])
    #                     is_snap_exists: bool = False
    #                     for snap in snapshots.values():
    #                         if snap['snapName'].strip() == snap_name:
    #                             is_snap_exists = True
    #                             remove_snap_status = v.remove_vm_snapshot(headers, snap['snapId'], print_msg=False)
    #                             time.sleep(0.5)
    #                             if remove_snap_status:
    #                                 count = Tools.counter()
    #                                 while True:
    #                                     time.sleep(5)
    #                                     if not v.is_has_snap(headers, value['name'], snap['snapName'].strip()):
    #                                         break
    #                                     elif count() == 1200:
    #                                         sys.exit("Error: Couldn't remove snapshot in 20 minutes. Abort procedure!")
    #                                         break
    #                                     else:
    #                                         continue
    #                                 status.console.print(f"[bold magenta]Remove snapshot: {value['name']}[/bold magenta]  [green]✅[/green]")
    #                             else:
    #                                 status.console.print(f"[bold magenta]Remove snapshot: {value['name']}[/bold magenta]  [red]❌[/red]")
    #                             break
    #                     if not is_snap_exists:
    #                         status.console.print(f"[red]No snapshot name '{snap_name}' for VM: {value['name']}[/red]")
    #         if not headers:
    #             sys.exit()
    #         elif args.vsphere_command == 'list-vm':
    #             vm_array: dict = v.get_array_of_vm(headers, args.exclude, args.filter, args.powered_on)
    #             v.print_list_of_vm(vm_array)
    #         elif args.vsphere_command == 'restart-vm':
    #             console.rule(title="Reboot guest OS")
    #             if args.all:
    #                 confirm: bool = True if input("YOU ARE ABOUT TO RESTART ALL VM's IN THE CLUSTER!!! ARE YOU SURE?(YES|NO) ").lower() == 'yes' else False
    #                 if not confirm:
    #                     print("Restart procedure aborted!")
    #                     sys.exit()
    #                 vm_array: dict = v.get_array_of_vm(headers, args.exclude, args.filter, powered_on=True)
    #                 v.restart_os(headers, vm_array)
    #             else:
    #                 vm_array: dict = v.get_array_of_vm(headers, args.exclude, args.filter, powered_on=True)
    #                 v.restart_os(headers, vm_array)
    #         elif args.vsphere_command == 'start-vm':
    #             console.rule(title="Power On virtual machine")
    #             vm_array: dict = v.get_array_of_vm(headers, args.exclude, args.filter)
    #             for value in vm_array.values():
    #                 v.start_vm(headers, value["moId"], value["name"])
    #         elif args.vsphere_command == 'stop-vm':
    #             console.rule(title="Shutdown guest OS")
    #             vm_array: dict = v.get_array_of_vm(headers, args.exclude, args.filter)
    #             for value in vm_array.values():
    #                 v.stop_vm(headers, value["moId"], value["name"])
    #         elif args.vsphere_command == 'show-snap':
    #             vm_array: dict = v.get_array_of_vm(headers, args.exclude, args.filter)
    #             for value in vm_array.values():
    #                 snapshots: dict = v.get_vm_snapshots(headers, value["moId"], value["name"])
    #                 v.print_vm_snapshots(value["name"], snapshots)
    #                 print()
    #         elif args.vsphere_command in ('take-snap', 'revert-snap', 'remove-snap', 'replace-snap'):
    #             # Logic of snaps procedures:
    #             # get needed VMs -> power OFF -> take/revert/remove snaps -> restore power state
    #             vm_array: dict = v.get_array_of_vm(headers, args.exclude, args.filter)
    #             vm_power_on = {k: v for k,v in vm_array.items() if v.get('power_state') == 'POWERED_ON'}
    #             if not vm_array:
    #                 sys.exit("No VM were matched. Exit!")
    #             for vm in vm_array:
    #                 print(vm_array[vm]['name'])
    #             confirm = input("\nIs it correct VM list? (Y/N): ").lower()
    #             if confirm not in ('y', 'yes'):
    #                 sys.exit("Abort procedure!")

    #             if vm_power_on: # type: ignore
    #                 console.rule(title="Shutdown guest OS")
    #                 for value in vm_power_on.values():
    #                     v.stop_vm(headers, value["moId"], value["name"])
    #             if args.vsphere_command == 'take-snap':
    #                 snap_name: str = args.name.strip()
    #                 console.rule(title="Create virtual machine snaphost")
    #                 take_snap(snap_name)
    #             elif args.vsphere_command == 'revert-snap':
    #                 console.rule(title="Revert virtual machine snapshot")
    #                 snap_name: str = args.name.strip()
    #                 for value in vm_array.values():
    #                     with console.status(f"[bold magenta]Revert snapshot: {value['name']}[/bold magenta]", spinner="earth"):
    #                         snapshots: dict = v.get_vm_snapshots(headers, value['moId'], value['name'])
    #                         is_snap_exists: bool = False
    #                         for snap in snapshots.values():
    #                             if snap['snapName'].strip() == snap_name:
    #                                 is_snap_exists = True
    #                                 revert_snap_status = v.revert_to_snapshot(headers, snap['snapId'], value['name'], print_msg=False)
    #                                 time.sleep(1)
    #                                 if revert_snap_status:
    #                                     console.print(f"[bold magenta]Revert snapshot: {value['name']}[/bold magenta]  [green]✅[/green]")
    #                                 else:
    #                                     console.print(f"[bold magenta]Revert snapshot: {value['name']}[/bold magenta]  [red]❌[/red]")
    #                                 break
    #                         if not is_snap_exists:
    #                             console.print(f"[red]No snapshot name '{snap_name}' for VM: {value['name']}[/red]")
    #             elif args.vsphere_command == 'remove-snap':
    #                 console.rule(title="Remove virtual machine snaphost")
    #                 snap_name: str = args.name.strip()
    #                 remove_snap(snap_name)
    #             elif args.vsphere_command == 'replace-snap':
    #                 console.rule(title="Replace virtual machine snapshot")
    #                 old_snap_name: str = args.old
    #                 new_snap_name: str = args.new
    #                 remove_snap(old_snap_name)
    #                 take_snap(new_snap_name)

    #             # Restoring power state
    #             if vm_power_on: # type: ignore
    #                 console.rule(title="Power state restore")
    #                 for value in vm_power_on.values():
    #                     v.start_vm(headers, value["moId"], value["name"])

    #     elif args.command == 'mdm':
    #         mdm = import_data.Mdmconnector()
    #         url = mdm.check_url(args.url)
    #         if args.export_file:
    #             mdm.export_mdm_config(url)
    #         else:
    #             mdm.import_mdm_config(url, args.import_file)

    #     elif args.command == 'issue-lic':
    #         lic_issue = license.Issue()
    #         lic = license.License()
    #         if not tools.is_socket_available(lic_issue._license_server, lic_issue._license_server_port):
    #             print(f"Socket is NOT available on {lic_issue._license_server}:{lic_issue._license_server_port}\nCheck the log!")
    #             sys.exit()
    #         lic_username, lic_password = Tools.get_creds_from_env('LICENSE_USER', 'LICENSE_PASSWORD')
    #         if not lic_username or not lic_password:
    #             # logger.error("No 'LICENSE_USER' and 'LICENSE_PASSWORD' in .env file.")
    #             print("Enter credentials for license server:")
    #             lic_username = input("login: ")
    #             lic_password = getpass("password: ")
    #         token = lic_issue.get_token_to_issue_license(username=lic_username, password=lic_password)
    #         if args.serverId:
    #             server_license = lic_issue.issue_license(
    #                         token
    #                         ,version=args.version
    #                         ,product=args.product
    #                         ,licenceType=args.licenceType
    #                         ,activationType=args.activationType
    #                         ,client=args.client
    #                         ,clientEmail=args.clientEmail
    #                         ,organization=args.organization
    #                         ,isOrganization=args.isOrganization
    #                         ,numberOfUsers=args.numberOfUsers
    #                         ,numberOfIpConnectionsPerUser=args.numberOfIpConnectionsPerUser
    #                         ,serverId=args.serverId
    #                         ,period=args.period
    #                         ,until=args.until
    #                         ,orderId=args.orderId
    #                         ,crmOrderId=args.crmOrderId
    #                         ,save=args.save
    #                         ,url=args.url
    #                         ,print=args.print
    #             )
    #             sys.exit()
    #         if args.url:
    #             url = tools.is_url_available(args.url)
    #             if not url:
    #                 print(f"URL {args.url} is not available.")
    #                 sys.exit()
    #             else:
    #                 args.url = url
    #             auth = auth.Auth()
    #             check = auth.establish_connection(url=args.url, username=args.user, password=args.password)
    #             if not check:
    #                 sys.exit()
    #             success, message = lic.get_serverID(args.url, auth.token)
    #             if success:
    #                 server_id: str = message
    #             else:
    #                 print(f"Error: {message}")
    #                 sys.exit()
    #             server_license = lic_issue.issue_license(
    #                         token
    #                         ,version=args.version
    #                         ,product=args.product
    #                         ,licenceType=args.licenceType
    #                         ,activationType=args.activationType
    #                         ,client=args.client
    #                         ,clientEmail=args.clientEmail
    #                         ,organization=args.organization
    #                         ,isOrganization=args.isOrganization
    #                         ,numberOfUsers=args.numberOfUsers
    #                         ,numberOfIpConnectionsPerUser=args.numberOfIpConnectionsPerUser
    #                         ,serverId=server_id
    #                         ,period=args.period
    #                         ,until=args.until
    #                         ,orderId=args.orderId
    #                         ,crmOrderId=args.crmOrderId
    #                         ,save=args.save
    #                         ,url=args.url
    #                         ,print=args.print
    #             )
    #             if args.apply:
    #                 lic.apply_license(args.url, auth.token, args.user, args.password, license=server_license)
    #     elif args.command == 'pk':
    #         pass
    #     elif args.command == 'ft':
    #         conf = Conf()
    #         FT = FeatureToggle()
    #         page = conf.get_confluence_page()
    #         data = conf.get_ft_data_of_all_projects(page)
    #         if args.check and not args.env:
    #             print("bimutils ft: error: --env argument is required")
    #             sys.exit()
    #         elif args.env and not args.check:
    #             print("bimutils ft: error: --check argument is required")
    #             sys.exit()
    #         if len(sys.argv) == 2 or (len(sys.argv) == 3 and sys.argv[2].strip() == '--save') or (len(sys.argv) == 3 and sys.argv[2].strip() == '--save-pretty'):
    #             project = conf.choose_project()
    #             conf.get_ft_for_project(data, project, args.save, args.save_pretty)
    #         elif args.gazprom_suid:
    #             if args.check:
    #                 conf_ft_list = conf.get_ft_for_project(data, conf.project_name_suid, args.save, args.save_pretty, no_print=True, env=args.env)
    #                 FT.compare_source_and_target(conf_ft_list, conf.project_name_suid, args.env)
    #             else:
    #                 conf.get_ft_for_project(data, conf.project_name_suid, args.save, args.save_pretty, args.no_print)
    #         elif args.gazprom_dtoir:
    #             if args.check:
    #                 conf_ft_list = conf.get_ft_for_project(data, conf.project_name_dtoir, args.save, args.save_pretty, no_print=True, env=args.env)
    #                 FT.compare_source_and_target(conf_ft_list, conf.project_name_dtoir, args.env)
    #             else:
    #                 conf.get_ft_for_project(data, conf.project_name_dtoir, args.save, args.save_pretty, args.no_print)
    #         elif args.gazprom_salavat:
    #             if args.check:
    #                 conf_ft_list = conf.get_ft_for_project(data, conf.project_name_salavat, args.save, args.save_pretty, no_print=True, env=args.env)
    #                 FT.compare_source_and_target(conf_ft_list, conf.project_name_salavat, args.env)
    #             else:
    #                 conf.get_ft_for_project(data, conf.project_name_salavat, args.save, args.save_pretty, args.no_print)
    #         elif args.novatek_murmansk:
    #             if args.check:
    #                 conf_ft_list = conf.get_ft_for_project(data, conf.project_name_murmansk, args.save, args.save_pretty, no_print=True, env=args.env)
    #                 FT.compare_source_and_target(conf_ft_list, conf.project_name_murmansk, args.env)
    #             else:
    #                 conf.get_ft_for_project(data, conf.project_name_murmansk, args.save, args.save_pretty, args.no_print)
    #         elif args.novatek_yamal:
    #             if args.check:
    #                 conf_ft_list = conf.get_ft_for_project(data, conf.project_name_yamal, args.save, args.save_pretty, no_print=True, env=args.env)
    #                 FT.compare_source_and_target(conf_ft_list, conf.project_name_yamal, args.env)
    #             else:
    #                 conf.get_ft_for_project(data, conf.project_name_yamal, args.save, args.save_pretty, args.no_print)
    #         elif args.crea_cod:
    #             if args.check:
    #                 conf_ft_list = conf.get_ft_for_project(data, conf.project_name_crea_cod, args.save, args.save_pretty, no_print=True, env=args.env)
    #                 FT.compare_source_and_target(conf_ft_list, conf.project_name_crea_cod, args.env)
    #             else:
    #                 conf.get_ft_for_project(data, conf.project_name_crea_cod, args.save, args.save_pretty, args.no_print)
    #     elif args.version:
    #         if args.url:
    #             Bimeister.print_bim_version(args.url)
    #         else:
    #             print(app_menu.AppMenu.__version__)
    #     elif args.command == 'token':
    #         autht = auth.Auth()
    #         providers = autht.get_providerId(args.url, interactive=False)
    #         if providers and isinstance(providers, list) and len(providers) > 1 and not args.providerId:
    #             print("Provide needed id with flag --providerId")
    #             for provider in providers:
    #                 for k,v in provider.items():
    #                     print(k,v)
    #         elif providers and args.providerId:
    #             token = autht.get_user_access_token(args.url, args.user, args.password, args.providerId)
    #             print(token if token else '')
    #         elif providers and isinstance(providers, str):
    #             token = autht.get_user_access_token(args.url, args.user, args.password, providers)
    #             print(token if token else '')
    #     elif args.command == 'docker':
    #         docker = mdocker.Docker()
    #         if not docker.is_connected:
    #             sys.exit()
    #         if args.list:
    #             images = docker.get_list_of_images()
    #             docker.print_images(images)
    #         elif args.save:
    #             if args.file:
    #                 data = File.read_file(args.file)
    #                 images = [image for image in data.split()]
    #             elif args.images:
    #                 images = [image for image in args.images.split()]
    #             else:
    #                 print("docker: error: one of the arguments -f/--file -i/--images is required")
    #                 sys.exit()
    #             pulled_images = docker.pull_images(images)
    #             docker.save_images(pulled_images, purge=args.no_purge, output=args.output)
    #     else:
    #         interactive_menu.launch_menu()
    # except KeyboardInterrupt:
    #     print('\nKeyboardInterrupt')


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