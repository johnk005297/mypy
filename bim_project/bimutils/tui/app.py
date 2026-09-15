from textual.widgets import (
    Static,
    ContentSwitcher,
    Footer,
    Tree,
    Log
    )
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.binding import Binding

import logging

from bimutils.tui.menus import MAIN_MENU
from bimutils.tui.panels.bimeister import CheckLicensePanel, TokenPanel, BimeisterSession, LoginPanel

_logger = logging.getLogger(__name__)


class LogPanel(VerticalScroll):
    def compose(self) -> ComposeResult:
        yield Log(id="log-view")


class BimutilsTUI(App):
    CSS_PATH = "styles/bimutils.tcss"
    BINDINGS = [
        Binding(key="q", action="quit", description="Quit"),
        Binding(key="l", action="show_log", description="Show log")
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bimeister_session = BimeisterSession()

    def compose(self) -> ComposeResult:
        tree: Tree[str] = Tree("hidden", id="command-tree")
        tree.show_root = False
        tree.root.expand()

        tree.root.add("Git", expand=False)
        tree.root.add("vSphere", expand=False)
        tree.root.add("SQL", expand=False)
        tree.root.add("Images", expand=False)

        bimeister = tree.root.add("Bimeister", expand=False)

        login_menu = bimeister.add_leaf("Login", data="bim-user-login")

        license_menu = bimeister.add("License")
        license_menu.add_leaf("Check license", data="bim-check-license")
        license_menu.add_leaf("Get server ID", data="bim-get-server-id")

        user_menu = bimeister.add("User")
        user_menu.add_leaf("Get user access token", data="bim-token")
        user_menu.add_leaf("Get private token", data="bim-private-token")

        with Horizontal(id="main"):
            yield tree
            with ContentSwitcher(initial=None, id="content"):
                yield CheckLicensePanel(self.bimeister_session, id="bim-check-license")
                yield TokenPanel(self.bimeister_session, id="bim-token")
                yield Static("Get server ID", id="bim-get-server-id")
                yield Static("Get private token", id="bim-private-token")
                yield LoginPanel(self.bimeister_session, id="bim-user-login")
                yield LogPanel(id="log-panel")
        yield Footer()

    @on(Tree.NodeSelected, "#command-tree")
    def command_selected(self, event: Tree.NodeSelected[str]) -> None:
        panel_id = event.node.data
        if panel_id is None:
            return
        self.query_one("#content", ContentSwitcher).current = panel_id

    def action_show_log(self) -> None:
        self.query_one("#content", ContentSwitcher).current = "log-panel"
        log_view = self.query_one("#log-view", Log)
        log_view.clear()
        self.read_log(log_view)

    @work(thread=True)
    def read_log(self, log_view: Log, lines: int = 300) -> None:
        from pathlib import Path
        from collections import deque
        path = Path.home() / ".bimutils.log"
        try:
            text = "".join(deque(open(path), maxlen=lines))
        except Exception as err:
            text = f"Error reading log: {err}"
        self.call_from_thread(log_view.write, text)