from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Label, ListView, ListItem

from ..widgets.vsphere_operation_panel import VsphereOperationPanel

class TaskPanel(Vertical):
    pass

class VsphereScreen(Vertical):

    def compose(self) -> ComposeResult:
        with Horizontal():
            with TaskPanel():
                yield Label("Operations")
                yield ListView(
                    ListItem(Label("List VMs")),
                    ListItem(Label("Start VM")),
                    ListItem(Label("Stop VM")),
                    ListItem(Label("Restart VM")),
                    ListItem(Label("Show Snapshots")),
                    ListItem(Label("Take Snapshot")),
                    ListItem(Label("Remove Snapshot")),
                    ListItem(Label("Revert Snapshot")),
                    ListItem(Label("Replace Snapshot")),
                    id="operations"
                )
            yield VsphereOperationPanel()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        label = event.item.children[0]
        operation = str(label.render())
        self.notify(operation)