from __future__ import annotations

from typing import Dict, Any, List, Optional, Iterable
from pathlib import Path
import re
import json


class SourceParser:
    """
    Responsible for ingesting raw RotMG source files and extracting
    structured entities (bosses, loot tables, items, sprites).

    This is the FIRST stage of the automated wiki pipeline.
    """

    def __init__(self, source_path: str):
        self.source_path = Path(source_path)

        self.raw_data: Dict[str, Any] = {}
        self.entities: Dict[str, Any] = {
            "bosses": [],
            "items": [],
            "loot": [],
            "sprites": [],
        }

    # -----------------------------
    # Entry Point
    # -----------------------------

    def parse(self) -> Dict[str, Any]:
        self.raw_data = self._load_source_tree()
        self._extract_all_entities()
        return self.entities

    # -----------------------------
    # Loading
    # -----------------------------

    def _load_source_tree(self) -> Dict[str, Any]:
        """
        Loads entire directory tree as structured JSON-like map.
        """

        tree = {}

        for file in self.source_path.rglob("*"):
            if file.is_file():
                rel = str(file.relative_to(self.source_path))
                tree[rel] = self._read_file(file)

        return tree

    def _read_file(self, file: Path) -> Optional[str]:
        try:
            return file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return None

    # -----------------------------
    # Extraction Pipeline
    # -----------------------------

    def _extract_all_entities(self) -> None:
        self.entities["bosses"] = self._extract_bosses()
        self.entities["items"] = self._extract_items()
        self.entities["loot"] = self._extract_loot()
        self.entities["sprites"] = self._extract_sprites()

    # -----------------------------
    # Boss Extraction
    # -----------------------------

    def _extract_bosses(self) -> List[Dict[str, Any]]:
        bosses = []

        for path, content in self.raw_data.items():
            if not content:
                continue

            if self._looks_like_boss_file(path, content):
                boss = self._parse_boss(path, content)
                if boss:
                    bosses.append(boss)

        return bosses

    def _looks_like_boss_file(self, path: str, content: str) -> bool:
        keywords = ["Boss", "Enemy", "Dungeon", "Encounter", "HP", "Attack"]

        score = sum(1 for k in keywords if k.lower() in content.lower())

        return score >= 2

    def _parse_boss(self, path: str, content: str) -> Optional[Dict[str, Any]]:
        name = self._extract_name(content)
        if not name:
            return None

        return {
            "id": self._generate_id(name),
            "name": name,
            "source": path,
            "stats": self._extract_stats(content),
            "phases": self._extract_phases(content),
            "loot": self._extract_loot_from_text(content),
            "aliases": self._extract_aliases(content),
        }

    # -----------------------------
    # Item Extraction
    # -----------------------------

    def _extract_items(self) -> List[Dict[str, Any]]:
        items = []

        for path, content in self.raw_data.items():
            if not content:
                continue

            if "Item" in content or "Drop" in content:
                item = self._parse_item(path, content)
                if item:
                    items.append(item)

        return items

    def _parse_item(self, path: str, content: str) -> Optional[Dict[str, Any]]:
        name = self._extract_name(content)
        if not name:
            return None

        return {
            "id": self._generate_id(name),
            "name": name,
            "source": path,
            "type": self._detect_item_type(content),
        }

    # -----------------------------
    # Loot Extraction
    # -----------------------------

    def _extract_loot(self) -> List[Dict[str, Any]]:
        loot = []

        for path, content in self.raw_data.items():
            if not content:
                continue

            if "Drop" in content or "Loot" in content:
                loot.extend(self._parse_loot_block(path, content))

        return loot

    def _parse_loot_block(self, path: str, content: str) -> List[Dict[str, Any]]:
        results = []

        pattern = re.findall(r"([\w\s\(\)]+)\s*\(?([\d\.]+%?)\)?", content)

        for name, rate in pattern:
            results.append({
                "item": name.strip(),
                "rate": rate.strip(),
                "source": path,
            })

        return results

    # -----------------------------
    # Sprite Extraction
    # -----------------------------

    def _extract_sprites(self) -> List[Dict[str, Any]]:
        sprites = []

        for path, content in self.raw_data.items():
            if path.endswith((".png", ".jpg", ".webp")):
                sprites.append({
                    "path": path,
                    "type": "sprite"
                })

        return sprites

    # -----------------------------
    # Helpers
    # -----------------------------

    def _extract_name(self, content: str) -> Optional[str]:
        match = re.search(r"Name\s*[:=]\s*(.+)", content)
        return match.group(1).strip() if match else None

    def _extract_stats(self, content: str) -> Dict[str, Any]:
        stats = {}

        patterns = {
            "hp": r"HP\s*[:=]\s*(\d+)",
            "attack": r"Attack\s*[:=]\s*(\d+)",
            "defense": r"Defense\s*[:=]\s*(\d+)",
            "speed": r"Speed\s*[:=]\s*(\d+)",
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                stats[key] = int(match.group(1))

        return stats

    def _extract_phases(self, content: str) -> List[Dict[str, Any]]:
        phases = []

        matches = re.findall(r"Phase\s*(\d+)[^\n]*", content)

        for m in matches:
            phases.append({
                "name": f"Phase {m}",
                "index": int(m)
            })

        return phases

    def _extract_aliases(self, content: str) -> List[str]:
        matches = re.findall(r"Alias\s*[:=]\s*(.+)", content)
        return [m.strip() for m in matches]

    def _detect_item_type(self, content: str) -> str:
        if "Weapon" in content:
            return "weapon"
        if "Armor" in content:
            return "armor"
        if "Ability" in content:
            return "ability"
        return "misc"

    def _generate_id(self, name: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")