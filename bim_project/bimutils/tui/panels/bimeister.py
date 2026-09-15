from dataclasses import dataclass, field
from datetime import date, datetime
import logging
import os

from textual import on, work
from textual.app import ComposeResult
from textual.widgets import Input, Button, Static, Select
from textual.containers import VerticalScroll
from rich.table import Table

from bimutils.bimeister.auth import Auth
from bimutils.bimeister.license import License

_logger = logging.getLogger(__name__)

@dataclass
class BimeisterSession:
    url: str | None = None
    provider_id: str | None = None
    access_token: str | None = None
    username: str | None = None
    auth: Auth = field(default_factory=Auth)
    license: License = field(default_factory=License)


class LoginPanel(VerticalScroll):
    def __init__(
            self,
            session: BimeisterSession,
            **kwargs
        ) -> None:
        super().__init__(**kwargs)
        self.session = session
        self.default_user: str = os.getenv("BIMEISTER_DEFAULT_USER")
        self.default_pass: str = os.getenv("BIMEISTER_DEFAULT_PASS")

    def compose(self) -> ComposeResult:
        yield Input(placeholder="URL", id="login-url")
        yield Button("Go", variant="primary", compact=True, id="login-go")
        yield Select([], prompt="Select provider", id="login-provider", disabled=True)
        yield Input(value=self.default_user, placeholder="Username", id="login-user", disabled=True)
        yield Input(value=self.default_pass, placeholder="Password", id="login-pass", password=True, disabled=True)
        yield Button("Login", variant="success", compact=True, id="login-submit", disabled=True)
        yield Static(id="login-status")

    @on(Button.Pressed, "#login-go")
    def on_go(self) -> None:
        url = self.query_one("#login-url", Input).value.strip().lower().removesuffix('/').removesuffix('/auth').removesuffix('/products')
        if not url:
            self.query_one("#login-status", Static).update("Enter a URL first.")
            return
        self.query_one("#login-status", Static).update("Connecting...")
        self.fetch_providers(url)

    @work(thread=True)
    def fetch_providers(self, url: str) -> None:
        try:
            providers = self.session.auth.get_providerId(url, interactive=False)
        except Exception:
            providers = None
        self.app.call_from_thread(self._apply_providers, url, providers)

    def _apply_providers(self, url, providers) -> None:
        status = self.query_one("#login-status", Static)
        if providers is None:
            status.update("Error: press Show log button from the footer menu.")
            return
        if isinstance(providers, str):
            options = [('Local', providers)]
        else:
            options = [next(iter(d.items())) for d in providers]
        provider = self.query_one("#login-provider", Select)
        provider.set_options(options)

        default = next((value for label, value in options if label == "Local"), options[0][1],)
        provider.value = default
        self.session.url = url

        for wid in ("#login-provider", "#login-user", "#login-pass", "#login-submit"):
            self.query_one(wid).disabled = False
        status.update("Enter username, password and log in.")

    @on(Button.Pressed, "#login-submit")
    def on_login(self) -> None:
        provider_id = self.query_one("#login-provider", Select).value
        username = self.query_one("#login-user", Input).value
        password = self.query_one("#login-pass", Input).value
        status = self.query_one("#login-status", Static)

        if not username or not password:
            status.update("Enter username and password.")
            return
        status.update("Logging in...")
        self.do_login(provider_id, username, password)

    @work(thread=True)
    def do_login(self, provider_id: str, username: str, password: str) -> None:
        try:
            token = self.session.auth.get_user_access_token(self.session.url, username, password, provider_id)
        except Exception:
            token = None
        self.app.call_from_thread(self._apply_login, provider_id, token)

    def _apply_login(self, provider_id, token):
        status = self.query_one("#login-status", Static)
        if not token:
            status.update("Login failed: press Show log from the footer.")
            return
        self.session.provider_id = provider_id
        self.session.access_token = token
        status.update("Connected. You can now use Bimeister commands.")


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
        if self.session.access_token:
            result.update(self.session.access_token)
        else:
            result.update("Not connected. Use Bimeister → Login first.")

    @work(thread=True)
    def fetch_token(self, result: Static, url: str, username: str, password: str, provider_id: str) -> None:
        try:
            token = self.session.auth.get_user_access_token(url, username, password, provider_id)
        except Exception as err:
            token = f"Error: {err}"
        if not token:
            token = "Error: press Show log button from the footer menu."
        self.app.call_from_thread(result.update, token)


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
        if not self.session.access_token:
            result.update("Not connected. Use Bimeister → Login first.")
            return
        result.update("Loading...")
        self.fetch_licenses(result)

    @work(thread=True)
    def fetch_licenses(self, result: Static) -> None:
        try:
            licenses = self.session.license.get_licenses(self.session.url, self.session.access_token)
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