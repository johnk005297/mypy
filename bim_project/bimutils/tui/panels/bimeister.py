from textual import on, work
from textual.app import ComposeResult
from textual.widgets import Input, Button, Static
from textual.containers import VerticalScroll

from bimutils.bimeister.auth import Auth


class TokenPanel(VerticalScroll):
    def compose(self) -> ComposeResult:
        yield Input(placeholder="URL", id="token-url")
        yield Input(placeholder="Provider ID", id="token-provider-id")
        yield Input(placeholder="Username", id="token-user")
        yield Input(placeholder="Password", password=True, id="token-pass")
        yield Button("Get token", variant="primary", compact=True, id="token-run-button")
        yield Static(id="token-result")

    @on(Button.Pressed, "#token-run-button")
    def load_token(self) -> None:
        result = self.query_one("#token-result", Static)
        result.update("Loading...")
        self.fetch_token(
            result,
            self.query_one("#token-url", Input).value,
            self.query_one("#token-user", Input).value,
            self.query_one("#token-pass", Input).value,
            self.query_one("#token-provider-id", Input).value,
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
        self.app.call_from_thread(result.update, token)


class CheckLicensePanel(VerticalScroll):
    def compose(self) -> ComposeResult:
        yield Input(placeholder="Bimeister URL")
        yield Button("Check license", variant="primary", compact=True)