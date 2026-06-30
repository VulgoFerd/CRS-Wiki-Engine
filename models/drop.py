from dataclasses import asdict, dataclass, field


@dataclass(slots=True)
class Drop:
    """Drop resolved from source loot definitions."""

    item_name: str
    boss_name: str
    portal_name: str
    difficulty: str
    drop_type: str
    probability: float | None = None
    raw_probability: str = ""
    tier: int | None = None
    item_type: str = ""
    source_file: str = ""
    source_context: str = ""
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON representation for workspace persistence."""

        return asdict(self)
