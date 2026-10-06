from dataclasses import dataclass, field
from datetime import date, datetime
import logging
import os

from textual import on, work
from textual.app import ComposeResult
from textual.widgets import (
    Input,
    Button,
    Static,
    Select,
    Tree
)
from textual.containers import (
    VerticalScroll,
    Vertical,
    Horizontal
)
from rich.table import Table

from bimutils.bimeister.auth import Auth
from bimutils.bimeister.license import License
from bimutils.tui.panels.constants import CHECK_LOG_MSG

_logger = logging.getLogger(__name__)

@dataclass
class BimeisterSession:
    url: str | None = None
    auth: Auth = field(default_factory=Auth)
    license: License = field(default_factory=License)


class BimeisterMenu:
    """Builds the Bimeister subtree and owns its state."""

    def __init__(self, parent: Tree) -> None:
        bimeister = parent.add("Bimeister", expand=False)

        self.login_leaf = bimeister.add_leaf("[red]●[/red] Login", data="bim-user-login")

        license_menu = bimeister.add("License")
        license_menu.add_leaf("License", data="bim-check-license")
        license_menu.add_leaf("Server ID", data="bim-get-server-id")

        user_menu = bimeister.add("User")
        user_menu.add_leaf("Access token", data="bim-token")
        user_menu.add_leaf("Private token", data="bim-private-token")

    def set_connected(self, connected: bool) -> None:
        dot = "[green]●[/green]" if connected else "[red]●[/red]"
        self.login_leaf.label = f"{dot} Login"

class LoginPanel(VerticalScroll):

    def __init__(
            self,
            session: BimeisterSession,
            menu: BimeisterMenu,
            **kwargs
        ) -> None:
        super().__init__(**kwargs)
        self.session = session
        self.default_user: str = os.getenv("BIMEISTER_DEFAULT_USER")
        self.default_pass: str = os.getenv("BIMEISTER_DEFAULT_PASS")
        self.menu = menu

    def compose(self) -> ComposeResult:
        yield Input(placeholder="URL", id="login-url")
        yield Button("Go", variant="primary", compact=True, id="url-go-button")

        with Vertical(id="login-form"):
            yield Select([], prompt="Select provider", id="login-provider")
            yield Input(value=self.default_user, placeholder="Username", id="login-user")
            yield Input(value=self.default_pass, placeholder="Password", id="login-pass", password=True)
            with Horizontal(id="login-form-buttons"):
                yield Button("Login", variant="primary", compact=True, id="login-submit")
                yield Button("Logout", variant="primary", compact=True, id="logout-submit")

    @on(Button.Pressed, "#url-go-button")
    def on_go(self) -> None:
        self.session.url = self.query_one("#login-url", Input).value.strip().lower().removesuffix('/').removesuffix('/auth').removesuffix('/products')
        if not self.session.url:
            self.notify("Enter a URL first.", severity="warning")
            return
        self.fetch_providers(self.session.url)

    @work(thread=True)
    def fetch_providers(self, url: str) -> None:
        try:
            providers = self.session.auth.get_providerId(url, interactive=False)
        except Exception:
            providers = None
        self.app.call_from_thread(self._apply_providers, providers)

    def _apply_providers(self, providers) -> None:
        if providers is None:
            self.notify(CHECK_LOG_MSG, title="ERROR", severity="error")
            return
        if isinstance(providers, str):
            options = [('Local', providers)]
        else:
            options = [next(iter(d.items())) for d in providers]
        provider = self.query_one("#login-provider", Select)
        provider.set_options(options)
        default = next((value for label, value in options if label == "Local"), options[0][1],)
        provider.value = default
        self.query_one("#login-form").display = True

    @on(Button.Pressed, "#login-submit")
    def on_login(self) -> None:
        provider_id = self.query_one("#login-provider", Select).value
        username = self.query_one("#login-user", Input).value
        password = self.query_one("#login-pass", Input).value

        if not username or not password:
            self.notify("Enter username and password.", title="INFO")
            return
        self.do_login(provider_id, username, password)

    @work(thread=True)
    def do_login(self, provider_id: str, username: str, password: str) -> None:
        try:
            self.session.auth.get_user_access_token(self.session.url, username, password, provider_id)
        except Exception as err:
            self.notify(err, severity="error")
        self.app.call_from_thread(self._apply_login, self.session.auth.token)

    def _apply_login(self, token):
        if not token:
            self.notify(CHECK_LOG_MSG, title="LOGIN FAILED", severity="error")
            return
        self.notify("You can now use Bimeister commands.", title="Connected")
        self.menu.set_connected(True)

    @on(Button.Pressed, "#logout-submit")
    def on_logout(self) -> None:
        self.do_logout()

    @work(thread=True)
    def do_logout(self) -> None:
        try:
            self.session.auth.user_logout(self.session.auth.url, self.session.auth.token)
        except Exception as err:
            _logger.error(err)
            self.notify(CHECK_LOG_MSG, severity="error")
        self.app.call_from_thread(self._after_logout)

    def _after_logout(self) -> None:
        self.query_one("#login-form").display = False
        self.query_one("#login-url", Input).value = ""
        self.notify("Logged out.", title="Disconnected")
        self.menu.set_connected(True)


class TokenPanel(VerticalScroll):
    def __init__(
            self,
            session: BimeisterSession,
            **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.session = session

    def compose(self) -> ComposeResult:
        yield Button("Show token", variant="primary", compact=True, id="token-run-button")
        yield Static(id="token-result")

    @on(Button.Pressed, "#token-run-button")
    def load_token(self) -> None:
        result: Static = self.query_one("#token-result", Static)
        if self.session.auth.token:
            result.update(self.session.auth.token)
        else:
            self.notify("Bimeister → Login first.", title="Not connected", severity="warning")


class PrivateTokenPanel(VerticalScroll):
    def __init__(
            self,
            session: BimeisterSession,
            **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.session = session

    def compose(self) -> ComposeResult:
        yield Button("Get private token", variant="primary", compact=True, id="get-priv-token-button")
        yield Static(id="get-priv-token-result")

    @on(Button.Pressed, "#get-priv-token-button")
    def on_get_priv_token(self) -> None:
        result: Static = self.query_one("#get-priv-token-result", Static)
        if not self.session.auth.token:
            self.notify("Bimeister → Login first.", title="Not connected", severity="warning")
            return
        result.update("Loading...")
        self.get_priv_token(result)

    @work(thread=True)
    def get_priv_token(self, result: Static) -> None:
        if not self.session.auth.url.startswith("http"):
            url = "https://" + self.session.auth.url
        else:
            url = self.session.auth.url
        try:
            response = self.session.auth.get_private_token(url, self.session.auth.token)
        except Exception as err:
            _logger.error(err)
            self.notify(CHECK_LOG_MSG, title="ERROR", severity="error")
            return
        if response:
            self.app.call_from_thread(result.update, response)
        else:
            self.notify(CHECK_LOG_MSG, title="ERROR", severity="error")


class CheckLicensePanel(VerticalScroll):
    def __init__(
            self,
            session: BimeisterSession,
            **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.session = session

    def compose(self) -> ComposeResult:
        yield Button("Check license", variant="primary", compact=True, id="check-lic-button")
        yield Static(id="check-lic-result")

    @on(Button.Pressed, "#check-lic-button")
    def on_check(self) -> None:
        result: Static = self.query_one("#check-lic-result", Static)
        if not self.session.auth.token:
            self.notify("Bimeister → Login first.", title="Not connected", severity="warning")
            return
        result.update("Loading...")
        self.fetch_licenses(result)

    @work(thread=True)
    def fetch_licenses(self, result: Static) -> None:
        try:
            licenses = self.session.license.get_licenses(self.session.url, self.session.auth.token)
        except Exception as err:
            _logger.error(err)
            self.app.call_from_thread(result.update, f"Error: {err}")
            return
        if not licenses:
            self.app.call_from_thread(result.update, "No licenses found.")
            return
        table = self._build_table(licenses)
        self.app.call_from_thread(result.update, table)

    def _build_table(self, licenses: list) -> Table:
        licenses = licenses[:5]
        table = Table(show_lines=True)
        table.add_column("Name", justify="left", no_wrap=True)
        table.add_column("Server Id", justify="left")
        table.add_column("Users", justify="left")
        table.add_column("Expiration date", justify="left")
        table.add_column("Status", justify="center")

        current_date: str = str(date.today()) + 'T' + datetime.now().strftime("%H:%M:%S")
        for license in licenses:
            # convert str format of expiration date to datetime format
            dt_obj = datetime.fromisoformat(license["until"])
            expiration_date = dt_obj.strftime("%d %B %Y")
            table.add_row(
                        license["name"],
                        license["serverId"],
                        f"{license['activeUsers']}/{license['activeUsersLimit']}",
                        f"[red]{expiration_date}[/red]" if license["until"] < current_date and license["isActive"] else expiration_date,
                        "[green]Active[/green]" if license["isActive"] else "[red]Inactive[/red]", style="cyan" if license["isActive"] else "dim cyan"
                        )
        return table


class GetServerIdPanel(VerticalScroll):
    def __init__(
            self,
            session: BimeisterSession,
            **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.session = session

    def compose(self) -> ComposeResult:
        yield Button("Get server ID", variant="primary", compact=True, id="get-sid-button")
        yield Static(id="get-sid-result")

    @on(Button.Pressed, "#get-sid-button")
    def on_get_sid(self) -> None:
        result: Static = self.query_one("#get-sid-result", Static)
        if not self.session.auth.token:
            self.notify("Bimeister → Login first.", title="Not connected", severity="warning")
            return
        result.update("Loading...")
        self.get_server_id(result)

    @work(thread=True)
    def get_server_id(self, result: Static) -> None:
        try:
            response = self.session.license.get_serverID(self.session.auth.url, self.session.auth.token)
        except Exception as err:
            _logger.error(err)
            self.notify(CHECK_LOG_MSG, title="ERROR", severity="error")
            return
        if response[0]:
            self.app.call_from_thread(result.update, response[1])
        else:
            self.notify(CHECK_LOG_MSG, title="ERROR", severity="error")