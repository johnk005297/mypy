from textual.widgets import Static

from bimutils.vsphere_tools.context import vs_ctx
from bimutils.common.startup import initialize

initialize() # load credentials from .env file

class VmListWidget(Static):
    def on_mount(self) -> None:
        self.update("Authenticating...")
        headers = vs_ctx.vs.get_headers()
        if not headers:
            self.update("Authentication failed")
            return
        self.update("Authentication successful")