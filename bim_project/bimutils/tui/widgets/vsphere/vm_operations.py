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
                yield Input(id="filter")

            with Horizontal(id="exclude-row"):
                yield Label("Exclude:")
                yield Input(id="exclude")

            with Horizontal(id="filter-options"):
                yield Checkbox("Powered on only", id="powered-on")
                yield Button("Refresh", id="refresh")

            with Container(id="actions"):
                with Horizontal(id="power-row"):
                    yield Label("Power")
                    yield Button("Start", id="start")
                    yield Button("Stop", id="stop")
                    yield Button("Restart", id="restart")
                with Horizontal(id="snapshot-row"):
                    yield Label("Snapshot")
                    yield Button("Show", id="show-snap")
                    yield Button("Take", id="take-snap")
                    yield Button("Revert", id="revert-snap")
                    yield Button("Remove", id="remove-snap")
                    yield Button("Replace", id="replace-snap")

            with Container(id="vsphere-content"):
                table = DataTable(id="vm-table")
                table.add_columns("VM Name", "Power State")
                table.add_rows([
                    ("box1-db1.imp.bimeister.io", "POWERED_ON"),
                    ("box1-k8s-m1.imp.bimeister.io", "POWERED_OFF"),
                    ("box1-k8s-w1.imp.bimeister.io", "POWERED_ON"),
                ])
                yield table

    @on(Button.Pressed, "#refresh")
    def handle_refresh_pressed(self) -> None:
        _logger.info("Rerfresh pressed")