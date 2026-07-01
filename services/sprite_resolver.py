from __future__ import annotations

import json
import re
import struct
from pathlib import Path

from models.sprite import Sprite


class SpriteResolver:
    """Resolve sprite atlas references for items."""

    def __init__(
        self,
        source_path: Path,
        items_path: Path = Path("workspace/database/items/items.json"),
        output_dir: Path = Path("workspace/database/sprites"),
    ) -> None:
        self.source_path = source_path
        self.items_path = items_path
        self.output_dir = output_dir
        self.resolved: list[Sprite] = []
        self.unresolved: list[dict[str, object]] = []

    def resolve(self) -> list[Sprite]:
        """Resolve sprite atlas metadata from item texture references."""

        self._validate_inputs()
        items = self._load_items()
        assets_dir = self.source_path / "client" / "src" / "kabam" / "rotmg" / "assets"
        embedded_sources = self._load_embedded_sources(assets_dir)
        aliases = self._load_asset_aliases(assets_dir, embedded_sources)

        resolved: list[Sprite] = []
        unresolved: list[dict[str, object]] = []

        for item in items:
            texture_file = str(item.get("texture_file", ""))
            texture_index = str(item.get("texture_index", ""))
            if not texture_file or not texture_index:
                unresolved.append({
                    "owner_type": "item",
                    "owner_name": item.get("name", ""),
                    "reason": "Item has no texture reference",
                })
                continue

            atlas_path = self._resolve_atlas_path(texture_file, assets_dir, aliases)
            if atlas_path is None:
                unresolved.append({
                    "owner_type": "item",
                    "owner_name": item.get("name", ""),
                    "texture_file": texture_file,
                    "texture_index": texture_index,
                    "reason": "Texture atlas PNG not found",
                })
                continue

            resolved.append(
                self._sprite_from_item(
                    item=item,
                    texture_file=texture_file,
                    texture_index=texture_index,
                    atlas_path=atlas_path,
                )
            )

        self.resolved = resolved
        self.unresolved = unresolved
        return self.resolved

    def save(self) -> None:
        """Persist resolved sprite references under workspace database."""

        self.output_dir.mkdir(parents=True, exist_ok=True)

        summary = {
            "total": len(self.resolved),
            "unresolved_total": len(self.unresolved),
            "sprites": [sprite.to_dict() for sprite in self.resolved],
            "unresolved": self.unresolved,
        }

        with (self.output_dir / "sprites.json").open("w", encoding="utf8") as file:
            json.dump(summary, file, indent=4, ensure_ascii=False)

        for sprite in self.resolved:
            with (
                self.output_dir / f"{self._slugify(sprite.owner_name)}.json"
            ).open("w", encoding="utf8") as file:
                json.dump(sprite.to_dict(), file, indent=4, ensure_ascii=False)

        with (self.output_dir / "unresolved.json").open("w", encoding="utf8") as file:
            json.dump(
                {
                    "total": len(self.unresolved),
                    "sprites": self.unresolved,
                },
                file,
                indent=4,
                ensure_ascii=False,
            )

    def _validate_inputs(self) -> None:
        if not self.source_path.exists():
            raise FileNotFoundError(f"Source path not found: {self.source_path}")

        if not self.items_path.exists():
            raise FileNotFoundError(f"Items database not found: {self.items_path}")

    def _load_items(self) -> list[dict[str, object]]:
        with self.items_path.open("r", encoding="utf8") as file:
            data = json.load(file)

        return data.get("items", [])

    def _load_embedded_sources(self, assets_dir: Path) -> dict[str, str]:
        embedded_sources: dict[str, str] = {}
        pattern = re.compile(
            r'\[Embed\(source="([^"]+)"\)\]\s*public\s+class\s+(\w+)',
            re.DOTALL,
        )

        for path in assets_dir.glob("*.as"):
            text = path.read_text(encoding="utf8", errors="ignore")
            match = pattern.search(text)
            if match is None:
                continue

            source_name = match.group(1)
            class_name = match.group(2)
            embedded_sources[class_name] = source_name

        return embedded_sources

    def _load_asset_aliases(
        self,
        assets_dir: Path,
        embedded_sources: dict[str, str],
    ) -> dict[str, Path]:
        aliases: dict[str, Path] = {}
        embedded_assets = assets_dir / "EmbeddedAssets.as"
        if embedded_assets.exists():
            text = embedded_assets.read_text(encoding="utf8", errors="ignore")
            for alias, class_name in re.findall(
                r'public\s+static\s+(?:var|const)\s+(\w+)\s*:\s*Class\s*=\s*(\w+)',
                text,
            ):
                source_name = embedded_sources.get(class_name)
                if source_name is None:
                    continue

                self._register_alias_keys(aliases, alias, assets_dir / source_name)

        for class_name, source_name in embedded_sources.items():
            stem = class_name.removeprefix("EmbeddedAssets_").rstrip("_")
            self._register_alias_keys(aliases, stem, assets_dir / source_name)

        return aliases

    def _register_alias_keys(
        self,
        aliases: dict[str, Path],
        key: str,
        path: Path,
    ) -> None:
        clean_key = key.rstrip("_")
        aliases.setdefault(clean_key, path)
        if clean_key.endswith("Embed"):
            aliases.setdefault(clean_key.removesuffix("Embed"), path)

    def _resolve_atlas_path(
        self,
        texture_file: str,
        assets_dir: Path,
        aliases: dict[str, Path],
    ) -> Path | None:
        alias = aliases.get(texture_file)
        if alias is not None and alias.exists():
            return alias

        candidates = [
            assets_dir / f"EmbeddedAssets_{texture_file}_.png",
            assets_dir / f"EmbeddedAssets_{texture_file}Embed_.png",
            assets_dir / f"{texture_file}.png",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate

        return None

    def _sprite_from_item(
        self,
        item: dict[str, object],
        texture_file: str,
        texture_index: str,
        atlas_path: Path,
    ) -> Sprite:
        index = self._parse_index(texture_index)
        atlas_width, atlas_height = self._read_png_dimensions(atlas_path)
        tile_width, tile_height = self._infer_tile_size(texture_file, atlas_width, atlas_height)
        x = None
        y = None
        if index is not None and tile_width and tile_height and atlas_width:
            columns = max(atlas_width // tile_width, 1)
            x = (index % columns) * tile_width
            y = (index // columns) * tile_height

        return Sprite(
            owner_type="item",
            owner_name=str(item["name"]),
            texture_file=texture_file,
            texture_index=texture_index,
            index=index,
            atlas_path=atlas_path.relative_to(self.source_path).as_posix(),
            atlas_width=atlas_width,
            atlas_height=atlas_height,
            tile_width=tile_width,
            tile_height=tile_height,
            x=x,
            y=y,
            source_files=list(item.get("source_files", [])),
            evidence=[
                f"item:{item['name']}",
                f"texture:{texture_file}",
                f"atlas:{atlas_path.relative_to(self.source_path).as_posix()}",
            ],
        )

    def _parse_index(self, value: str) -> int | None:
        try:
            return int(value, 0)
        except ValueError:
            return None

    def _read_png_dimensions(self, path: Path) -> tuple[int | None, int | None]:
        try:
            data = path.read_bytes()
        except OSError:
            return None, None

        if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
            return None, None

        width, height = struct.unpack(">II", data[16:24])
        return width, height

    def _infer_tile_size(
        self,
        texture_file: str,
        atlas_width: int | None,
        atlas_height: int | None,
    ) -> tuple[int | None, int | None]:
        explicit = re.search(r"(\d+)x(\d+)", texture_file)
        if explicit is not None:
            return int(explicit.group(1)), int(explicit.group(2))

        if "40x40" in texture_file:
            return 40, 40

        if "32x32" in texture_file or "Big" in texture_file:
            return 16, 16

        if atlas_width is not None and atlas_height is not None and atlas_height <= 16:
            return 8, 8

        return 8, 8

    def _slugify(self, value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
        return slug or "sprite"
