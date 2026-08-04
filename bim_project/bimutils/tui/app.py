"""
Main TUI application.

Responsible for:
- creating the Textual application;
- assembling the main layout;
- connecting major UI components.

Does not contain:
- module logic;
- backend calls;
- screen-specific behavior.
"""
from textual.app import App, ComposeResult
from textual.containers import Horizontal

from .navigation import Navigation
from .content import Content
from .messages import ModuleSelected, OperationSelected, BackRequested
from .menus import MAIN_MENU
from .screens import SCREENS

class MainApp(App):
    """Main Textual application."""
    TITLE = "bimutils"
    BINDINGS = [
        ("escape", "back", "Back"),
    ]
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_menu = MAIN_MENU
        self.menu_stack = []
        self.current_screen = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Navigation(MAIN_MENU)
            yield Content()

    async def on_module_selected(self, message: ModuleSelected) -> None:
        navigation = self.query_one(Navigation)
        submenu = self.current_menu.get(message.module)
        if submenu is not None:
            self.menu_stack.append(self.current_menu)
            self.current_menu = submenu
            navigation.set_items(submenu)
            navigation.mode = "operations"

        content = self.query_one(Content)
        screen_class = SCREENS.get(message.module)
        if screen_class is not None:
            self.current_screen = screen_class()
            await content.show(self.current_screen)

    async def on_operation_selected(self, message: OperationSelected) -> None:
        if self.current_screen is None:
            return
        await self.current_screen.handle_operation(message.operation)

    async def action_back(self) -> None:
        if not self.menu_stack:
            return
        navigation = self.query_one(Navigation)
        self.current_menu = self.menu_stack.pop()
        navigation.set_items(list(self.current_menu.keys()))
        self.current_screen = None
        navigation.mode = "modules"

if __name__ == "__main__":
    MainApp().run()