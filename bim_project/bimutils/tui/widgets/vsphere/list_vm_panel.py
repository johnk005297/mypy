from textual.containers import Vertical
from textual.app import ComposeResult
from textual.widgets import Label
from textual.widgets import Input
from textual.widgets import Button
from textual.widgets import Checkbox
from textual.widgets import DataTable



class ListVmPanel(Vertical):
    def compose(self) -> ComposeResult:
        yield Label("VM name contains:")
        yield Input(
            placeholder="Leave empty to list all VMs",
            id="vm-filter",
        )
        yield Label("Exclude:")
        yield Input(
            placeholder="Names to exclude via whitespace",
            id="vm-exclude",
        )
        yield Checkbox(
            "Powered on only",
            id="vm-powered-on",
        )
        yield Button("Run", id="run")
        yield DataTable(id="vm-table")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        filter_value = self.query_one("#vm-filter", Input).value
        exclude_value = self.query_one("#vm-exclude", Input).value
        powered_on = self.query_one("#vm-powered-on", Checkbox).value

        # vm_headers = vs_ctx.vs.get_headers()
        # vm_array = vs_ctx.vs.get_array_of_vm(
        #     vm_headers,
        #     exclude_value or None,
        #     filter_value or None,
        #     powered_on
        # )

        self.notify(filter_value)