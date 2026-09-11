from textual.widgets import (
    Static,
    ContentSwitcher,
    Footer,
    Tree,
    Button,
    Input,
    Log
    )
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll

import logging

from bimutils.tui.menus import MAIN_MENU
from bimutils.bimeister.auth import Auth
from bimutils.common.mlogger import Logs

_logger = logging.getLogger(__name__)


class LogPanel(VerticalScroll):
    def compose(self) -> ComposeResult:
        yield Log(id="log-view")


class TokenPanel(VerticalScroll):
    def compose(self) -> ComposeResult:
        yield Input(placeholder="URL", id="token-url")
        yield Input(placeholder="Provider ID", id="token-provider-id")
        yield Input(placeholder="Username", id="token-user")
        yield Input(placeholder="Password", password=True, id="token-pass")
        yield Button("Get token", variant="primary", compact=True, id="token-run-button")
        yield Static(id="token-result")


class CheckLicensePanel(VerticalScroll):
    def compose(self) -> ComposeResult:
        yield Static("Check license", classes="panel-title")
        yield Input(placeholder="Bimeister URL")
        yield Button("Check license", variant="primary", compact=True)


class BimutilsTUI(App):
    CSS_PATH = "bimutils.tcss"
    BINDINGS = [
        Binding(key="q", action="quit", description="Quit"),
        Binding(key="l", action="show_log", description="Show log")
    ]

    def compose(self) -> ComposeResult:
        tree: Tree[str] = Tree("hidden", id="command-tree")
        tree.show_root = False
        tree.root.expand()

        tree.root.add("Git", expand=False)
        tree.root.add("vSphere", expand=False)
        tree.root.add("SQL", expand=False)
        tree.root.add("Images", expand=False)

        bimeister = tree.root.add("Bimeister", expand=False)

        license_menu = bimeister.add("License")
        license_menu.add_leaf("Check license", data="bim-check-license")
        license_menu.add_leaf("Get server ID", data="bim-get-server-id")

        user_menu = bimeister.add("User")
        user_menu.add_leaf("Get user access token", data="bim-token")
        user_menu.add_leaf("Get private token", data="bim-private-token")

        with Horizontal(id="main"):
            yield tree
            with ContentSwitcher(initial=None, id="content"):
                yield CheckLicensePanel(id="bim-check-license")
                yield TokenPanel(id="bim-token")
                yield Static("Get server ID", id="bim-get-server-id")
                yield Static("Get private token", id="bim-private-token")
                yield LogPanel(id="log-panel")
        yield Footer()

    @on(Tree.NodeSelected, "#command-tree")
    def command_selected(self, event: Tree.NodeSelected[str]) -> None:
        panel_id = event.node.data
        if panel_id is None:
            return
        self.query_one("#content", ContentSwitcher).current = panel_id

    @on(Button.Pressed, "#token-run-button")
    def load_token(self) -> None:
        panel = self.query_one("#bim-token", TokenPanel)
        result = panel.query_one("#token-result", Static)
        result.update("Loading...")
        self.fetch_token(
            result,
            panel.query_one("#token-url", Input).value,
            panel.query_one("#token-user", Input).value,
            panel.query_one("#token-pass", Input).value,
            panel.query_one("#token-provider-id", Input).value,
        )

    @work(thread=True)
    def fetch_token(self, result, url: str, username: str, password: str, provider_id: str) -> None:
        auth = Auth()
        try:
            token = auth.get_user_access_token(url, username, password, provider_id)
        except Exception as err:
            token = f"Error: {err}"
        if not token:
            token = "Error: press Show log button from the footer menu."
        self.call_from_thread(result.update, token)

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