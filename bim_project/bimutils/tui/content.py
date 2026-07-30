# Displays screens
from textual.widgets import Static
from textual.widget import Widget


class Content(Static):
    def __init__(self):
        super().__init__(id="content")

    async def show(self, widget: Widget) -> None:
        await self.remove_children()
        await self.mount(widget)