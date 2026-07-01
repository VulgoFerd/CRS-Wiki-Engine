from dataclasses import asdict, dataclass, field


@dataclass(slots=True)
class Item:
    """Item resolved from XML object definitions."""

    name: str
    object_id: str
    object_type: str
    display_id: str = ""
    class_name: str = ""
    slot_type: int | None = None
    tier: int | None = None
    description: str = ""
    texture_file: str = ""
    texture_index: str = ""
    bag_type: int | None = None
    feed_power: int | None = None
    soulbound: bool = False
    usable: bool = False
    no_loot_boost: bool = False
    source_files: list[str] = field(default_factory=list)
    dropped_by: list[dict[str, object]] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON representation for workspace persistence."""

        return asdict(self)
