"""
Main content area container.

Responsible for:
- displaying the currently selected module screen;
- replacing the current content widget.

Does not:
- decide which module to open;
- contain business logic.
"""
from textual.containers import Vertical


class Content(Vertical):
    async def show(self, widget) -> None:
        await self.remove_children()
        await self.mount(widget)