from textual.app import App, ComposeResult, on
from textual.containers import Horizontal, VerticalScroll, Container
from textual.widgets import Button, Footer
from textual.binding import Binding

import logging

from bimutils.tui import menus
from bimutils.tui.widgets.vsphere.vm_operations import VsphereScreen

_logger = logging.getLogger(__name__)


class MainApp(App):
    TITLE = "bimutils"
    CSS_PATH = "bimutils.tcss"
    BINDINGS = [
        Binding(key="q", action="quit", description="Quit"),
    ]

    def compose(self) -> ComposeResult:
        with Horizontal():
            with VerticalScroll(id="menu"):
                for label, button_id in menus.MAIN_MENU:
                    yield Button(label, id=button_id)
            yield Container(id="content")
        yield Footer()

    def on_mount(self):
        self.theme = "gruvbox"

    @on(Button.Pressed, "#git")
    async def handle_git_button_pressed(self, event: Button.Pressed) -> None:
        """Called when the Git button is pressed."""
        await self.show_menu(menus.GIT_MENU, show_back=True)

    @on(Button.Pressed, "#vsphere")
    async def handle_vsphere_button_pressed(self, event: Button.Pressed) -> None:
        """Called when the vSphere button is pressed."""
        await self.show_content(VsphereScreen())

    @on(Button.Pressed, "#bimeister")
    async def handle_bimeister_button_pressed(self, event: Button.Pressed) -> None:
        """Called when the Bimeister button is pressed."""
        await self.show_menu(menus.BIMEISTER_MENU, show_back=True)

    @on(Button.Pressed, "#back")
    async def handle_back_button_pressed(self, event: Button.Pressed) -> None:
        """Called when the Back button is pressed."""
        await self.show_menu(menus.MAIN_MENU)

    async def show_menu(self, menu_items, show_back=False) -> None:
        menu = self.query_one("#menu", VerticalScroll)
        await menu.remove_children()
        for label, button_id in menu_items:
            await menu.mount(Button(label, id=button_id))
        if show_back:
            await menu.mount(Button("Back", id="back"))

    async def show_content(self, widget) -> None:
        content = self.query_one("#content", Container)
        await content.remove_children()
        await content.mount(widget)