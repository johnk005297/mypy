from textual.widgets import Static


class VsphereOperationPanel(Static):
    def __init__(self) -> None:
        super().__init__(
            "Select an operation from the list.",
            id="operation-panel",
        )