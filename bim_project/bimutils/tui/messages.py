"""
Textual event messages.

Responsible for:
- defining communication events between widgets;
- allowing components to notify each other without direct imports.

Does not:
- perform actions;
- contain UI or backend logic.
"""
from textual.message import Message


class ModuleSelected(Message):
    def __init__(self, module: str) -> None:
        self.module = module
        super().__init__()

class BackRequested(Message):
    pass