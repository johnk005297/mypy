from .models import Operation

VSPHERE_OPERATIONS = [
    Operation("list_vm", "List VMs"),
    Operation("start_vm", "Start VM"),
    Operation("stop_vm", "Stop VM"),
    Operation("restart_vm", "Restart VM"),
    Operation("show_snap", "Show Snapshots"),
    Operation("take_snap", "Take Snapshot"),
    Operation("remove_snap", "Remove Snapshot"),
    Operation("revert_snap", "Revert Snapshot"),
    Operation("replace_snap", "Replace Snapshot"),
]