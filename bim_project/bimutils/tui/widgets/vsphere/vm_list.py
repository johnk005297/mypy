from textual.widgets import Static

from bimutils.vsphere_tools.context import vs_ctx


class VmList(Static):
    def __init__(self) -> None:
        super().__init__("Loading VM list...")