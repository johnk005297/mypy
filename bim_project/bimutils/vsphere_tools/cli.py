import typer
from rich.console import Console

import sys
from datetime import datetime
import time

from .service import Vsphere
from common import utils


# vsphere_app CLI
vsphere_app = typer.Typer(help="Perform different operations in vSphere.")

VSPHERE_HELP = {
    'filter': "Filter VMs by occurrences in the name using regular expressions",
    'exclude': "Exclude VMs by occurrences in the name using regular expressions",
}
class VsphereContext:
    """Store shared vsphere parameters"""
    def __init__(self):
        self.vs = Vsphere()
        self.console = Console()
        self.headers = None

# Create a context instance
vs_ctx = VsphereContext()

def action_confirmation_and_stop_vm(vm_array):
    """ Function to confirm some actions in vsphere before execution. 
        After confirmation, VMs are shutted down.
    """
    if not vm_array:
        raise typer.Abort("No VM were matched.")
    for vm in vm_array:
        print(vm_array[vm]['name'])
    confirm = input("\nIs it correct VM list? (Y/N): ").lower()
    if confirm not in ('y', 'yes'):
        raise typer.Abort()
    vm_powered_on: dict = {k: v for k,v in vm_array.items() if v.get('power_state') == 'POWERED_ON'}
    if vm_powered_on:
        vs_ctx.console.rule(title="Shutdown guest OS")
        for value in vm_powered_on.values():
            vs_ctx.vs.stop_vm(vs_ctx.headers, value["moId"], value["name"])

def vm_power_restore(vm_array: dict):
    """ Function to restore power state after operations with VMs. """
    vm_powered_on: dict = {k: v for k,v in vm_array.items() if v.get('power_state') == 'POWERED_ON'}
    if vm_powered_on:
        vs_ctx.console.rule(title="Power state restore")
        for value in vm_powered_on.values():
            vs_ctx.vs.start_vm(vs_ctx.headers, value["moId"], value["name"])

@vsphere_app.callback()
def get_headers_callback():
    """Get headers once for all vSphere commands"""
    vs_ctx.headers = vs_ctx.vs.get_headers()
    if not vs_ctx.headers:
        typer.echo("Failed to authenticate with vSphere.")
        raise typer.Exit(1)


@vsphere_app.command(help="Print VMs in implementation cluster.")
def list_vm(
    filter: str = typer.Option(None, "-f", "--filter", help=VSPHERE_HELP['filter']),
    exclude: str = typer.Option(None, "-e", "--exclude", help=VSPHERE_HELP['exclude']),
    powered_on: bool = typer.Option(False, "--powered-on", help="Print only VM with POWERED_ON status.")
        ):
    vm_array: dict = vs_ctx.vs.get_array_of_vm(vs_ctx.headers, exclude, filter, powered_on)
    vs_ctx.vs.print_list_of_vm(vm_array)

@vsphere_app.command(help="Perform guest OS reboot for VMs in implementation cluster.")
def restart_vm(
    filter: str = typer.Option(None, "-f", "--filter", help=VSPHERE_HELP['filter']),
    exclude: str = typer.Option(None, "-e", "--exclude", help=VSPHERE_HELP['exclude']),
    all: bool = typer.Option("False", "--all", help="Restart all working VMs in implementation cluster.")
        ):
    vs_ctx.console.rule(title="Reboot guest OS")
    if all:
        confirm: bool = True if input("YOU ARE ABOUT TO RESTART ALL VM's IN THE CLUSTER!!! ARE YOU SURE?(YES|NO) ").lower() == 'yes' else False
        if not confirm:
            raise typer.Abort()
        vm_array: dict = vs_ctx.vs.get_array_of_vm(vs_ctx.headers, exclude, filter, powered_on=True)
        vs_ctx.vs.restart_os(vs_ctx.headers, vm_array)
    else:
        vm_array: dict = vs_ctx.vs.get_array_of_vm(vs_ctx.headers, exclude, filter, powered_on=True)
        vs_ctx.vs.restart_os(vs_ctx.headers, vm_array)

@vsphere_app.command(help="Start selected VMs in vSphere.")
def start_vm(
    filter: str = typer.Option(None, "-f", "--filter", help=VSPHERE_HELP['filter']),
    exclude: str = typer.Option(None, "-e", "--exclude", help=VSPHERE_HELP['exclude'])
        ):
    vs_ctx.console.rule(title="Power On virtual machine")
    vm_array: dict = vs_ctx.vs.get_array_of_vm(vs_ctx.headers, exclude, filter)
    for value in vm_array.values():
        vs_ctx.vs.start_vm(vs_ctx.headers, value["moId"], value["name"])

@vsphere_app.command(help="Start selected VMs in vSphere.")
def stop_vm(
    filter: str = typer.Option(None, "-f", "--filter", help=VSPHERE_HELP['filter']),
    exclude: str = typer.Option(None, "-e", "--exclude", help=VSPHERE_HELP['exclude'])
        ):
    vs_ctx.console.rule(title="Shutdown guest OS")
    vm_array: dict = vs_ctx.vs.get_array_of_vm(vs_ctx.headers, exclude, filter)
    for value in vm_array.values():
        vs_ctx.vs.stop_vm(vs_ctx.headers, value["moId"], value["name"])

@vsphere_app.command(help="Print list of snapshots for a given VMs.")
def show_snap(
    filter: str = typer.Option(None, "-f", "--filter", help=VSPHERE_HELP['filter']),
    exclude: str = typer.Option(None, "-e", "--exclude", help=VSPHERE_HELP['exclude'])
        ):
    vm_array: dict = vs_ctx.vs.get_array_of_vm(vs_ctx.headers, exclude, filter)
    for value in vm_array.values():
        snapshots: dict = vs_ctx.vs.get_vm_snapshots(vs_ctx.headers, value["moId"], value["name"])
        vs_ctx.vs.print_vm_snapshots(value["name"], snapshots)
        print()

# Logic of snaps procedures:
# get needed VMs -> power OFF -> take/revert/remove snaps -> restore power state

@vsphere_app.command(help="Take snapshot for a given VMs.")
def take_snap(
    filter: str = typer.Option("", "-f", "--filter", help=VSPHERE_HELP['filter']),
    exclude: str = typer.Option("", "-e", "--exclude", help=VSPHERE_HELP['exclude']),
    name: str = typer.Option(datetime.today().strftime("%d.%m.%Y_%H:%M:%S"), "--name", help="vSphere snapshot name."),
    description: str = typer.Option("", "--desc", help="Description for a snapshot."),
    skip_confirm: bool = typer.Option("False", "--skip/--confirm", hidden=True, help="Flag to skip action_confirmation_and_stop_vm function for replace snapshot logic."),
    hide_console_rule: bool = typer.Option("False", "--hide/--show", hidden=True, help="Hide console rule sign on a screen."),
    skip_power_restore: bool = typer.Option("False", "--restore/--no-restore", hidden=True, help="Skip VM power restore procedure.")
        ):

    vm_array: dict = vs_ctx.vs.get_array_of_vm(vs_ctx.headers, exclude, filter)
    # vm_powered_on: dict = {k: v for k,v in vm_array.items() if v.get('power_state') == 'POWERED_ON'}
    if not skip_confirm:
        action_confirmation_and_stop_vm(vm_array)
    snap_name: str = name.strip()
    if not hide_console_rule:
        vs_ctx.console.rule(title="Create virtual machine snapshot")
    for value in vm_array.values():
        with vs_ctx.console.status(f"[bold magenta]Create snapshot: {value['name']}[/bold magenta]", spinner="earth") as status:
            take_snap_status: bool = vs_ctx.vs.take_snapshot(vs_ctx.headers, value['moId'], value['name'], snap_name=snap_name, description=description)
            time.sleep(0.5)
            if take_snap_status:
                count = utils.counter()
                while True:
                    time.sleep(5)
                    if vs_ctx.vs.is_has_snap(vs_ctx.headers, value['name'], snap_name):
                        break
                    elif count() == 1200:
                        sys.exit("Error: Couldn't take snapshot in 20 minutes. Abort procedure!")
                        break
                    else:
                        continue
                status.console.print(f"[bold magenta]Create snapshot: {value['name']}[/bold magenta]  [green]✅[/green]")
            else:
                status.console.print(f"[bold magenta]Create snapshot: {value['name']}[/bold magenta]  [red]❌[/red]")
    if not skip_power_restore:
        vm_power_restore(vm_array)

@vsphere_app.command(help="Remove snapshot from vCenter.")
def remove_snap(
    filter: str = typer.Option("", "-f", "--filter", help=VSPHERE_HELP['filter']),
    exclude: str = typer.Option("", "-e", "--exclude", help=VSPHERE_HELP['exclude']),
    name: str = typer.Option(..., "--name", help="vSphere snapshot name."),
    skip_confirm: bool = typer.Option("False", "--skip/--confirm", hidden=True, help="Flag to skip action_confirmation_and_stop_vm function for replace snapshot logic."),
    hide_console_rule: bool = typer.Option("False", "--hide/--show", hidden=True, help="Hide console rule sign on a screen."),
    skip_power_restore: bool = typer.Option("False", "--restore/--no-restore", hidden=True, help="Skip VM power restore procedure.")
        ):
    vm_array: dict = vs_ctx.vs.get_array_of_vm(vs_ctx.headers, exclude, filter)
    # vm_powered_on: dict = {k: v for k,v in vm_array.items() if v.get('power_state') == 'POWERED_ON'}
    if not skip_confirm:
        action_confirmation_and_stop_vm(vm_array)
    snap_name: str = name.strip()
    if not hide_console_rule:
        vs_ctx.console.rule(title="Remove virtual machine snapshot")
    for value in vm_array.values():
        with vs_ctx.console.status(f"[bold magenta]Remove snapshot: {value['name']}[/bold magenta]", spinner="earth") as status:
            snapshots: dict = vs_ctx.vs.get_vm_snapshots(vs_ctx.headers, value['moId'], value['name'])
            is_snap_exists: bool = False
            for snap in snapshots.values():
                if snap['snapName'].strip() == snap_name:
                    is_snap_exists = True
                    remove_snap_status = vs_ctx.vs.remove_vm_snapshot(vs_ctx.headers, snap['snapId'])
                    time.sleep(0.5)
                    if remove_snap_status:
                        count = utils.counter()
                        while True:
                            time.sleep(5)
                            if not vs_ctx.vs.is_has_snap(vs_ctx.headers, value['name'], snap['snapName'].strip()):
                                break
                            elif count() == 1200:
                                sys.exit("Error: Couldn't remove snapshot in 20 minutes. Abort procedure!")
                                break
                            else:
                                continue
                        status.console.print(f"[bold magenta]Remove snapshot: {value['name']}[/bold magenta]  [green]✅[/green]")
                    else:
                        status.console.print(f"[bold magenta]Remove snapshot: {value['name']}[/bold magenta]  [red]❌[/red]")
                    break
            if not is_snap_exists:
                status.console.print(f"[red]No snapshot name '{snap_name}' for VM: {value['name']}[/red]")
    if not skip_power_restore:
        vm_power_restore(vm_array)

@vsphere_app.command(help="Revert to snapshot for a given VMs.")
def revert_snap(
    filter: str = typer.Option(..., "-f", "--filter", help=VSPHERE_HELP['filter']),
    exclude: str = typer.Option("", "-e", "--exclude", help=VSPHERE_HELP['exclude']),
    name: str = typer.Option(..., "--name", help="vSphere snapshot name.")
        ):
    vm_array: dict = vs_ctx.vs.get_array_of_vm(vs_ctx.headers, exclude, filter)
    vm_powered_on: dict = {k: v for k,v in vm_array.items() if v.get('power_state') == 'POWERED_ON'}
    action_confirmation_and_stop_vm(vm_array)
    vs_ctx.console.rule(title="Revert virtual machine snapshot")
    snap_name: str = name.strip()
    for value in vm_array.values():
        with vs_ctx.console.status(f"[bold magenta]Revert snapshot: {value['name']}[/bold magenta]", spinner="earth"):
            snapshots: dict = vs_ctx.vs.get_vm_snapshots(vs_ctx.headers, value['moId'], value['name'])
            is_snap_exists: bool = False
            for snap in snapshots.values():
                if snap['snapName'].strip() == snap_name:
                    is_snap_exists = True
                    revert_snap_status = vs_ctx.vs.revert_to_snapshot(vs_ctx.headers, snap['snapId'])
                    time.sleep(1)
                    if revert_snap_status:
                        vs_ctx.console.print(f"[bold magenta]Revert snapshot: {value['name']}[/bold magenta]  [green]✅[/green]")
                    else:
                        vs_ctx.console.print(f"[bold magenta]Revert snapshot: {value['name']}[/bold magenta]  [red]❌[/red]")
                    break
            if not is_snap_exists:
                vs_ctx.console.print(f"[red]No snapshot name '{snap_name}' for VM: {value['name']}[/red]")
    if vm_powered_on:
        vs_ctx.console.rule(title="Power state restore")
        for value in vm_powered_on.values():
            vs_ctx.vs.start_vm(vs_ctx.headers, value["moId"], value["name"])

@vsphere_app.command(help="Replace one snapshot in vSphere to another for a given VMs.")
def replace_snap(
    filter: str = typer.Option(..., "-f", "--filter", help=VSPHERE_HELP['filter']),
    exclude: str = typer.Option("", "-e", "--exclude", help=VSPHERE_HELP['exclude']),
    old_snap_name: str = typer.Option(..., "--old", help="Snapshot name to replace(old)."),
    new_snap_name: str = typer.Option(datetime.today().strftime("%d.%m.%Y_%H:%M:%S"), "--new", help="New snapshot to create."),
    description: str = typer.Option("", "--desc", help="Description for a snapshot.")
        ):
    vm_array: dict = vs_ctx.vs.get_array_of_vm(vs_ctx.headers, exclude, filter)
    action_confirmation_and_stop_vm(vm_array)
    vs_ctx.console.rule(title="Replace virtual machine snapshot")
    remove_snap(
        filter=filter,
        exclude=exclude,
        name=old_snap_name,
        skip_confirm=True,
        hide_console_rule=True,
        skip_power_restore=True
    )
    take_snap(
        filter=filter,
        exclude=exclude,
        name=new_snap_name,
        description=description,
        skip_confirm=True,
        hide_console_rule=True,
        skip_power_restore=True
    )
    vm_power_restore(vm_array)