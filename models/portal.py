from dataclasses import dataclass


@dataclass(slots=True)
class Portal:
    name: str
    difficulty: str
    enabled: bool = True