from textual.app import App, ComposeResult, on
from textual.containers import Horizontal, VerticalScroll, Container
from textual.widgets import Button

import logging

from bimutils.common.mlogger import file_logger, Logs
from bimutils.tui import menus
from bimutils.tui.widgets.vsphere.list_vm import VmListWidget
from bimutils.common.startup import initialize
initialize() # load credentials from .env file


_logger = logging.getLogger(__name__)
logs = Logs()

class MainApp(App):
    TITLE = "bimutils"
    CSS_PATH = "bimutils.tcss"

    def compose(self) -> ComposeResult:
        with Horizontal():
            with VerticalScroll(id="menu"):
                for label, button_id in menus.MAIN_MENU:
                    yield Button(label, id=button_id)
            yield Container(id="content")

    @on(Button.Pressed, "#exit")
    def exit_pressed(self, event: Button.Pressed) -> None:
        self.exit()

    @on(Button.Pressed)
    async def button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        if event.button.id == "vsphere":
            await self.show_menu(menus.VSPHERE_MENU, show_back=True)
        elif event.button.id == "git":
            pass
        elif event.button.id == "bimeister":
            pass
        elif event.button.id == "back":
            await self.show_menu(menus.MAIN_MENU)
        elif event.button.id == "list_vm":
            await self.show_content(VmListWidget())

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

if __name__ == "__main__":
    file_logger(logs.filepath, logLevel=logging.INFO)
    app = MainApp()
    app.run()