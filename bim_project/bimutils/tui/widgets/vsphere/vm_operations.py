from textual.containers import Container, Vertical
from textual.widgets import Static, Input, Checkbox, Button
from textual.app import on

import logging

_logger = logging.getLogger(__name__)


class VsphereScreen(Container):
    def compose(self):
        with Vertical():
            yield Input(placeholder="Filter VMs...")
            yield Input(placeholder="Exclude VMs...")
            yield Checkbox("Powered on only")
            yield Button("Refresh", id="refresh")
            yield Static("ACTIONS", id="actions")
            yield Static("VM TABLE", id="vm-table")

    @on(Button.Pressed, "#refresh")
    def handle_refresh_pressed(self) -> None:
        _logger.info("Rerfresh pressed")