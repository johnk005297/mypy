from textual.containers import Vertical


class OperationArea(Vertical):
    async def show(self, widget) -> None:
        await self.remove_children()
        await self.mount(widget)