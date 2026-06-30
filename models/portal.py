from dataclasses import asdict, dataclass, field


@dataclass(slots=True)
class Portal:
    """Portal discovered from the source whitelist."""

    name: str
    difficulty: str
    enabled: bool = True
    object_id: str = ""
    object_type: str = ""
    dungeon_name: str = ""
    display_id: str = ""
    texture_file: str = ""
    texture_index: str = ""
    source_files: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON representation for workspace persistence."""

        return asdict(self)
