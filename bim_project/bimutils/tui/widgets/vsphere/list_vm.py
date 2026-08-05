from textual.widgets import Static

from bimutils.vsphere_tools.context import vs_ctx

class VmListWidget(Static):
    def on_mount(self) -> None:
        headers = vs_ctx.vs.get_headers()
        if not headers:
            self.update("Authentication failed")
            return
        vm_array = vs_ctx.vs.get_array_of_vm(headers=headers, search_for="box1")
        text = "\n".join(vm["name"] for vm in vm_array.values())
        self.update(text)