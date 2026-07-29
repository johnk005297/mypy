from dataclasses import dataclass, field

@dataclass
class MenuItem:
    id: str
    title: str
    children: list["MenuItem"] = field(default_factory=list)

@dataclass
class Operation:
    id: str
    title: str