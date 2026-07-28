from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Header, Footer, Tree, Static


class Navigation(Tree[str]):
    def __init__(self):
        super().__init__("Services")

    def on_mount(self):
        self.root.expand()
        self.show_root = False

        self.root.add("GitLab")
        self.root.add("Database")
        self.root.add("Feature Toggles")
        self.root.add("Docker Images")
        self.root.add("Licenses")
        self.root.add("vSphere")
        # self.root.add("Authentication")
        self.root.add("Bimeister")


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