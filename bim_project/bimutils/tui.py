from dataclasses import dataclass, field

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Header, Footer, Tree, Static


@dataclass
class MenuItem:
    id: str
    title: str
    children: list["MenuItem"] = field(default_factory=list)

class Navigation(Tree[MenuItem]):
    def __init__(self):
        super().__init__("Services")

    def on_mount(self):
        self.root.expand()
        self.show_root = False
        for item in MENU:
            if not item.children:
                self.root.add(item.title, data=item)
            else:
                parent_node = self.root.add(item.title, data=item)
                for i in item.children:
                    parent_node.add(i.title, data=i)


MENU = [
    MenuItem("git", "GitLab"),
    MenuItem("database", "Database"),
    MenuItem("docker", "Docker Images"),
    MenuItem("vsphere", "vSphere"),
    MenuItem(
        "bimeister",
        "Bimeister",
        children=[
            MenuItem("feature_toggle", "Feature Toggles"),
            MenuItem("license", "Licenses"),
            MenuItem("import", "Import"),
            MenuItem("export", "Export"),
        ],
    ),
]

class Content(Static):
    pass


class MyToolApp(App):

    CSS = """
    Screen {
        layout: vertical;
    }

    Horizontal {
        height: 1fr;
    }

    Navigation {
        width: 24;
        border: round green;
    }

    Content {
        width: 28;
        border: round blue;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Horizontal():
            yield Navigation()
            yield Content("Content")

        yield Footer()


if __name__ == "__main__":
    MyToolApp().run()