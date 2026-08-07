from textual.app import App, ComposeResult, on
from textual.containers import Horizontal, VerticalScroll, Container
from textual.widgets import Button, Footer
from textual.binding import Binding

import logging

from bimutils.tui import menus
from bimutils.tui.widgets.vsphere.vm_operations import VmOperationsWidget


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

    @on(Button.Pressed)
    async def button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        if event.button.id == "vsphere":
            await self.show_menu(menus.VSPHERE_MENU, show_back=True)
        elif event.button.id == "git":
            await self.show_menu(menus.GIT_MENU, show_back=True)
        elif event.button.id == "bimeister":
            await self.show_menu(menus.BIMEISTER_MENU, show_back=True)
        elif event.button.id == "back":
            await self.show_menu(menus.MAIN_MENU)
        elif event.button.id == "list_vm":
            await self.show_content(VmOperationsWidget())

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