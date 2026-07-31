from textual.containers import Vertical

class OperationArea(Vertical):
    def __init__(self) -> None:
        super().__init__(id="operation-panel")

    async def show(self, widget) -> None:
        await self.remove_children()
        await self.mount(widget)