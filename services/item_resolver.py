from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from models.item import Item


class ItemResolver:
    """Resolve dropped item references against source XML item definitions."""

    def __init__(
        self,
        source_path: Path,
        loot_path: Path = Path("workspace/database/loot/loot.json"),
        output_dir: Path = Path("workspace/database/items"),
    ) -> None:
        self.source_path = source_path
        self.loot_path = loot_path
        self.output_dir = output_dir
        self.resolved: list[Item] = []
        self.unresolved: list[dict[str, object]] = []

    def resolve(self) -> list[Item]:
        """Resolve concrete item drops from XML definitions."""

        self._validate_inputs()
        item_drops = self._load_item_drops()
        item_index = self._load_item_index()

        resolved: list[Item] = []
        unresolved: list[dict[str, object]] = []

        for item_name, drops in sorted(item_drops.items()):
            item_data = item_index.get(self._normalize(item_name))
            if item_data is None:
                unresolved.append({
                    "item_name": item_name,
                    "reason": "XML item definition not found",
                    "drops": drops,
                })
                continue

            resolved.append(self._item_from_data(item_name, item_data, drops))

        self.resolved = resolved
        self.unresolved = unresolved
        return self.resolved

    def save(self) -> None:
        """Persist resolved and unresolved items under workspace database."""

        self.output_dir.mkdir(parents=True, exist_ok=True)

        summary = {
            "total": len(self.resolved),
            "unresolved_total": len(self.unresolved),
            "items": [item.to_dict() for item in self.resolved],
            "unresolved": self.unresolved,
        }

        with (self.output_dir / "items.json").open("w", encoding="utf8") as file:
            json.dump(summary, file, indent=4, ensure_ascii=False)

        for item in self.resolved:
            with (
                self.output_dir / f"{self._slugify(item.name)}.json"
            ).open("w", encoding="utf8") as file:
                json.dump(item.to_dict(), file, indent=4, ensure_ascii=False)

        with (self.output_dir / "unresolved.json").open("w", encoding="utf8") as file:
            json.dump(
                {
                    "total": len(self.unresolved),
                    "items": self.unresolved,
                },
                file,
                indent=4,
                ensure_ascii=False,
            )

    def _validate_inputs(self) -> None:
        if not self.source_path.exists():
            raise FileNotFoundError(f"Source path not found: {self.source_path}")

        if not self.loot_path.exists():
            raise FileNotFoundError(f"Loot database not found: {self.loot_path}")

    def _load_item_drops(self) -> dict[str, list[dict[str, object]]]:
        with self.loot_path.open("r", encoding="utf8") as file:
            data = json.load(file)

        item_drops: dict[str, list[dict[str, object]]] = {}
        for portal_name, bosses in data.get("portals", {}).items():
            for boss_name, drops in bosses.items():
                for drop in drops:
                    if drop.get("drop_type") != "item":
                        continue

                    item_name = str(drop["item_name"])
                    item_drops.setdefault(item_name, []).append({
                        "portal_name": portal_name,
                        "boss_name": boss_name,
                        "probability": drop.get("probability"),
                        "raw_probability": drop.get("raw_probability", ""),
                        "source_context": drop.get("source_context", ""),
                        "source_file": drop.get("source_file", ""),
                    })

        return item_drops

    def _load_item_index(self) -> dict[str, dict[str, object]]:
        item_index: dict[str, dict[str, object]] = {}

        for path in self.source_path.rglob("*.xml"):
            try:
                root = ET.parse(path).getroot()
            except ET.ParseError:
                continue

            for node in root.iter():
                if self._local_name(node.tag) != "Object":
                    continue

                object_id = node.attrib.get("id", "")
                if not object_id or not self._is_item_node(node):
                    continue

                key = self._normalize(object_id)
                current = item_index.setdefault(key, self._extract_item_data(node))
                source_file = path.relative_to(self.source_path).as_posix()
                if source_file not in current["source_files"]:
                    current["source_files"].append(source_file)

        return item_index

    def _is_item_node(self, node: ET.Element) -> bool:
        return node.find("Item") is not None or self._text(node, "Class") == "Equipment"

    def _extract_item_data(self, node: ET.Element) -> dict[str, object]:
        texture = node.find("Texture")
        texture_file = self._text(texture, "File") if texture is not None else ""
        texture_index = self._text(texture, "Index") if texture is not None else ""

        return {
            "object_id": node.attrib.get("id", ""),
            "object_type": node.attrib.get("type", ""),
            "display_id": self._text(node, "DisplayId"),
            "class_name": self._text(node, "Class"),
            "slot_type": self._int_text(node, "SlotType"),
            "tier": self._int_text(node, "Tier"),
            "description": self._text(node, "Description"),
            "texture_file": texture_file,
            "texture_index": texture_index,
            "bag_type": self._int_text(node, "BagType"),
            "feed_power": self._int_text(node, "feedPower"),
            "soulbound": node.find("Soulbound") is not None,
            "usable": node.find("Usable") is not None,
            "no_loot_boost": node.find("NoLootBoost") is not None,
            "source_files": [],
        }

    def _item_from_data(
        self,
        name: str,
        item_data: dict[str, object],
        drops: list[dict[str, object]],
    ) -> Item:
        return Item(
            name=name,
            object_id=str(item_data["object_id"]),
            object_type=str(item_data["object_type"]),
            display_id=str(item_data["display_id"]),
            class_name=str(item_data["class_name"]),
            slot_type=item_data["slot_type"],
            tier=item_data["tier"],
            description=str(item_data["description"]),
            texture_file=str(item_data["texture_file"]),
            texture_index=str(item_data["texture_index"]),
            bag_type=item_data["bag_type"],
            feed_power=item_data["feed_power"],
            soulbound=bool(item_data["soulbound"]),
            usable=bool(item_data["usable"]),
            no_loot_boost=bool(item_data["no_loot_boost"]),
            source_files=sorted(item_data["source_files"]),
            dropped_by=drops,
        )

    def _text(self, node: ET.Element | None, tag: str) -> str:
        if node is None:
            return ""

        child = node.find(tag)
        if child is None or child.text is None:
            return ""

        return child.text.strip()

    def _int_text(self, node: ET.Element, tag: str) -> int | None:
        text = self._text(node, tag)
        if not text:
            return None

        try:
            return int(text)
        except ValueError:
            return None

    def _local_name(self, tag: str) -> str:
        return tag.rsplit("}", 1)[-1]

    def _normalize(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", value.casefold())

    def _slugify(self, value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
        return slug or "item"
