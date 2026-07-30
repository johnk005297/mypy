from textual.containers import Vertical
from textual.app import ComposeResult
from textual.widgets import Label
from textual.widgets import Input
from textual.widgets import Button

class VsphereOperationPanel(Vertical):
    def __init__(self) -> None:
        super().__init__(id="operation-panel")

    # def show_message(self, text: str) -> None:
    #     self.update(text)

    def compose(self) -> ComposeResult:
        yield Label("VM name contains:")
        yield Input(
            placeholder="Leave empty to list all VMs",
            id="vm-filter",
        )
        yield Button("Run", id="run")
