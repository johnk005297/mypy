from textual.message import Message

from .models import MenuItem


class MenuSelected(Message):
    """Sent when the user selects a menu item."""

    def __init__(self, item: MenuItem):
        super().__init__()
        self.item = item