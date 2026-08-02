"""
Main module navigation.

Responsible for:
- displaying available application modules;
- notifying the app when the user selects a module.

Does not:
- load screens directly;
- call backend services.
"""
from textual.widgets import ListView, ListItem, Label
from .messages import ModuleSelected


class Navigation(ListView):
    def __init__(self, items: list[str]) -> None:
        self.items = items
        super().__init__()

    def on_mount(self) -> None:
        self.set_items(self.items)

    def set_items(self, items: list[str]) -> None:
        self.clear()
        for item in items:
            self.append(ListItem(Label(item)))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        label = event.item.query_one(Label)
        self.post_message(ModuleSelected(str(label.render())))