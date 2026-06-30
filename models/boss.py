from dataclasses import asdict, dataclass, field


@dataclass(slots=True)
class Boss:
    """Boss candidate resolved from portal world maps and source logic."""

    name: str
    portal_name: str
    difficulty: str
    object_id: str = ""
    object_type: str = ""
    display_id: str = ""
    group: str = ""
    class_name: str = ""
    enemy: bool = False
    quest: bool = False
    texture_file: str = ""
    texture_index: str = ""
    source_files: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON representation for workspace persistence."""

        return asdict(self)
