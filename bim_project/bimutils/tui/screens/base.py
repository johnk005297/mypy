from textual.widgets import Static


class BaseScreen(Static):
    """Base class for all module screens."""

    async def handle_operation(self, operation: str) -> None:
        raise NotImplementedError