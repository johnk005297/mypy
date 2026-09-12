from dataclasses import dataclass

from textual import on, work
from textual.app import ComposeResult
from textual.widgets import Input, Button, Static, Select
from textual.containers import VerticalScroll

from bimutils.bimeister.auth import Auth


@dataclass
class BimeisterSession:
    url: str | None = None
    provider_id: str | None = None
    user_access_token: str | None = None


class LoginPanel(VerticalScroll):
    auth = Auth()
    def __init__(self, session, **kwargs):
        super().__init__(**kwargs)
        self.session = session

    def compose(self) -> ComposeResult:
        yield Input(placeholder="URL", id="login-url")
        yield Button("Go", variant="primary", compact=True, id="login-go")
        yield Select([], prompt="Select provider", id="login-provider", disabled=True)
        yield Input(placeholder="Username", id="login-user", disabled=True)
        yield Input(placeholder="Password", id="login-pass", password=True, disabled=True)
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
            providers = self.auth.get_providerId(url, interactive=False)
        except Exception as err:
            providers = None
            error = str(err)
        else:
            error = None
        self.app.call_from_thread(self._apply_providers, url, providers, error)

    def _apply_providers(self, url, providers, error) -> None:
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

        if len(options) == 1:
            provider.value = options[0][1]
        self.session.url = url

        for wid in ("#login-provider", "#login-user", "#login-pass", "#login-submit"):
            self.query_one(wid).disabled = False
            status.update("Select provider and log in.")

    @on(Button.Pressed, "#login-submit")
    def on_login(self) -> None:
        provider_id = self.query_one("#login-provider", Select).value
        username = self.query_one("#login-user", Input).value
        password = self.query_one("#login-pass", Input).value
        status = self.query_one("#login-status", Static)

        if provider_id == Select.BLANK or not username or not password:
            status.update("Select a provider and enter username and password.")
            return
        status.update("Logging in...")
        self.do_login(provider_id, username, password)

    @work(thread=True)
    def do_login(self, provider_id: str, username: str, password: str) -> None:
        try:
            token = self.auth.get_user_access_token(self.session.url, username, password, provider_id)
        except Exception as err:
            token = None
        else:
            error = None
        self.app.call_from_thread(self._apply_login, provider_id, token, error)

    def _apply_login(self, provider_id, token, error):
        status = self.query_one("#login-status", Static)
        if not token:
            status.update("Login failed: press Show log from the footer.")
            return
        self.session.provider_id = provider_id
        self.session.token = token
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
        yield Input(placeholder="URL", id="token-url")
        yield Input(placeholder="Provider ID", id="token-provider-id")
        yield Input(placeholder="Username", id="token-user")
        yield Input(placeholder="Password", password=True, id="token-pass")
        yield Button("Get token", variant="primary", compact=True, id="token-run-button")
        yield Static(id="token-result")

    @on(Button.Pressed, "#token-run-button")
    def load_token(self) -> None:
        result: Static = self.query_one("#token-result", Static)
        result.update("Loading...")
        self.fetch_token(
            result,
            self.query_one("#token-url", Input).value,
            self.query_one("#token-user", Input).value,
            self.query_one("#token-pass", Input).value,
            self.query_one("#token-provider-id", Input).value,
        )

    @work(thread=True)
    def fetch_token(self, result: Static, url: str, username: str, password: str, provider_id: str) -> None:
        auth = Auth()
        try:
            token = auth.get_user_access_token(url, username, password, provider_id)
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
        yield Input(placeholder="Bimeister URL")
        yield Button("Check license", variant="primary", compact=True)