from textual.widgets import Tree

from .messages import MenuSelected
from .models import MenuItem
from .menu import MENU


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
                parent = self.root.add(item.title, data=item)
                for child in item.children:
                    parent.add(child.title, data=child)

    def on_tree_node_selected(self, event: Tree.NodeSelected[MenuItem]) -> None:
        if event.node.data is not None:
            self.post_message(MenuSelected(event.node.data))