from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Label

from .base import BaseScreen
from bimutils.tui.widgets.vsphere.operation_area import OperationArea
from bimutils.tui.widgets.vsphere.vm_list import VmList


class VsphereScreen(BaseScreen):
    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label("vSphere")
            yield OperationArea()

    async def handle_operation(self, operation: str) -> None:
        area = self.query_one(OperationArea)
        if operation == "List VMs":
            await area.show(VmList())