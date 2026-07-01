from dataclasses import asdict, dataclass, field


@dataclass(slots=True)
class Sprite:
    """Sprite atlas reference resolved from an item texture."""

    owner_type: str
    owner_name: str
    texture_file: str
    texture_index: str
    index: int | None
    atlas_path: str
    atlas_width: int | None = None
    atlas_height: int | None = None
    tile_width: int | None = None
    tile_height: int | None = None
    x: int | None = None
    y: int | None = None
    source_files: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON representation for workspace persistence."""

        return asdict(self)
