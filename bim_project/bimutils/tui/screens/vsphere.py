from textual.widgets import Static


class VsphereScreen(Static):
    def __init__(self) -> None:
        super().__init__("vSphere module")