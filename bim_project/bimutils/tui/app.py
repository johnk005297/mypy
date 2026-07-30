# Navigation role

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Header, Footer

from .navigation import Navigation
from .content import Content
from .messages import MenuSelected
from .screens.vsphere import VsphereScreen

from .screens import SCREENS


class MyToolApp(App):

    CSS_PATH = "app.tcss"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Horizontal():
            yield Navigation()
            yield Content()
        yield Footer()

    async def on_menu_selected(self, message: MenuSelected) -> None:
        content = self.query_one("#content", Content)

        screen_class = SCREENS.get(message.item.id)
        if screen_class is not None:
            await content.show(screen_class())

    async def on_mount(self) -> None:
        content = self.query_one("#content", Content)
        await content.show(VsphereScreen())


if __name__ == "__main__":
    MyToolApp().run()