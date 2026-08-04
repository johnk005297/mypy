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
from .messages import ModuleSelected, OperationSelected


class Navigation(ListView):
    def __init__(self, items: list[str]) -> None:
        self.items = items
        self.mode = "modules"
        super().__init__()

    def on_mount(self) -> None:
        self.set_items(self.items)

    def set_items(self, items: list[str]) -> None:
        self.clear()
        for item in items:
            self.append(ListItem(Label(item)))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        label = event.item.query_one(Label)
        text = str(label.render())
        if self.mode == "modules":
            self.post_message(ModuleSelected(text))
        else:
            self.post_message(OperationSelected(text))