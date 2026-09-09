from textual.app import App, ComposeResult, on
from textual.widgets import Select, Static, ContentSwitcher, Footer
from textual.binding import Binding

import logging

from bimutils.tui.menus import MAIN_MENU

_logger = logging.getLogger(__name__)


class BimutilsTUI(App):
    TITLE = "bimutils"
    CSS_PATH = "bimutils.tcss"
    BINDINGS = [
        Binding(key="q", action="quit", description="Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Select(
            MAIN_MENU,
            value=MAIN_MENU[0][1],
            allow_blank=False,
            compact=False
        )
        yield Footer()

        with ContentSwitcher(initial="vsphere"):
            yield Static("vSphere data", id="vsphere")
            yield Static("Git data", id="git")
            yield Static("Bimeister data", id="bimeister")
            yield Static("Token", id="bim-user-token")

    @on(Select.Changed)
    def select_changed_handler(self, event: Select.Changed) -> None:
        self.query_one(ContentSwitcher).current = str(event.value)