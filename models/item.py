from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class Item:

    object_type: str

    name: str

    item_class: str

    tier: Optional[str]

    slot: Optional[str]

    description: str

    sprite: Optional[str]

    feed_power: int

    soulbound: bool