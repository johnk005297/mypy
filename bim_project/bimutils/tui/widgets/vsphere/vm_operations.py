from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Label, Input, Checkbox, Button, DataTable
from textual.app import on

import logging

_logger = logging.getLogger(__name__)


class VsphereScreen(Container):
    def compose(self):
        with Vertical(id="vsphere-screen"):
            with Horizontal(id="filter-row"):
                yield Label("Filter:")
                yield Input(id="filter-input")

            with Horizontal(id="exclude-row"):
                yield Label("Exclude:")
                yield Input(id="exclude-input")

            with Horizontal(id="filter-options"):
                yield Checkbox("Powered on only", id="powered-on-checkbox")
                yield Button("Refresh", id="refresh-button")

            with Container(id="actions"):
                with Horizontal(id="power-row"):
                    yield Label("Power:")
                    yield Button("Start", id="start-button", compact=True)
                    yield Button("Stop", id="stop-button", compact=True)
                    yield Button("Restart", id="restart-button", compact=True)
                with Horizontal(id="snapshot-row"):
                    yield Label("Snapshot:")
                    yield Button("Show", id="show-snap-button", compact=True)
                    yield Button("Take", id="take-snap-button", compact=True)
                    yield Button("Revert", id="revert-snap-button", compact=True)
                    yield Button("Remove", id="remove-snap-button", compact=True)
                    yield Button("Replace", id="replace-snap-button", compact=True)

            with Container(id="vsphere-content"):
                table = DataTable(id="vm-table")
                table.add_columns("VM Name", "Power State")
                table.add_rows([
                    ("box1-db1.imp.bimeister.io", "POWERED_ON"),
                    ("box1-k8s-m1.imp.bimeister.io", "POWERED_OFF"),
                    ("box1-k8s-w1.imp.bimeister.io", "POWERED_ON"),
                ])
                yield table

    @on(Button.Pressed, "#refresh-button")
    def handle_refresh_pressed(self) -> None:
        _logger.info("Rerfresh pressed")