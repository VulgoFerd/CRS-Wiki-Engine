from __future__ import annotations

from typing import Dict, Any, List, Set, Tuple
from collections import defaultdict
import hashlib
import re


class EntityIndexer:
    """
    Takes raw parsed entities and transforms them into a clean,
    deduplicated and relational dataset ready for the engine.

    Responsibilities:
    - Deduplicate bosses/items/loot
    - Normalize IDs
    - Cross-link entities
    - Build relationship maps
    """

    def __init__(self):
        self.index: Dict[str, Any] = {
            "bosses": {},
            "items": {},
            "loot": [],
        }

        self.relationships: Dict[str, Set[str]] = defaultdict(set)

    # -----------------------------
    # Entry Point
    # -----------------------------

    def build(self, parsed_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Main pipeline:
        raw parsed data -> clean indexed dataset
        """

        self._index_bosses(parsed_data.get("bosses", []))
        self._index_items(parsed_data.get("items", []))
        self._index_loot(parsed_data.get("loot", []))

        self._build_relationships()

        return {
            "index": self.index,
            "relationships": self.relationships
        }

    # -----------------------------
    # Boss Indexing
    # -----------------------------

    def _index_bosses(self, bosses: List[Dict[str, Any]]) -> None:
        for boss in bosses:
            boss_id = self._normalize_id(boss.get("id") or boss.get("name"))

            if boss_id in self.index["bosses"]:
                self._merge(self.index["bosses"][boss_id], boss)
            else:
                self.index["bosses"][boss_id] = boss

    # -----------------------------
    # Item Indexing
    # -----------------------------

    def _index_items(self, items: List[Dict[str, Any]]) -> None:
        for item in items:
            item_id = self._normalize_id(item.get("id") or item.get("name"))

            if item_id in self.index["items"]:
                self._merge(self.index["items"][item_id], item)
            else:
                self.index["items"][item_id] = item

    # -----------------------------
    # Loot Indexing
    # -----------------------------

    def _index_loot(self, loot: List[Dict[str, Any]]) -> None:
        for drop in loot:
            self.index["loot"].append({
                "boss": self._normalize_id(drop.get("boss") or ""),
                "item": self._normalize_id(drop.get("item") or drop.get("name")),
                "rate": self._normalize_rate(drop.get("rate")),
                "source": drop.get("source"),
            })

    # -----------------------------
    # Relationship Builder
    # -----------------------------

    def _build_relationships(self) -> None:
        """
        Builds graph edges:
        boss -> item
        item -> boss
        """

        for drop in self.index["loot"]:
            boss = drop["boss"]
            item = drop["item"]

            if boss and item:
                self.relationships[boss].add(item)
                self.relationships[item].add(boss)

    # -----------------------------
    # Merge Logic (important for duplicates)
    # -----------------------------

    def _merge(self, base: Dict[str, Any], new: Dict[str, Any]) -> None:
        """
        Merge entity fields intelligently instead of overwriting.
        """

        for k, v in new.items():
            if k not in base or not base[k]:
                base[k] = v
                continue

            # merge lists
            if isinstance(base[k], list) and isinstance(v, list):
                base[k] = list({*base[k], *v})

            # merge dicts shallow
            elif isinstance(base[k], dict) and isinstance(v, dict):
                base[k].update(v)

    # -----------------------------
    # Normalization
    # -----------------------------

    def _normalize_id(self, text: str) -> str:
        if not text:
            return ""

        text = text.lower().strip()
        text = re.sub(r"[^a-z0-9\s]", "", text)
        text = re.sub(r"\s+", "_", text)

        return text

    def _normalize_rate(self, rate: Any) -> float:
        if not rate:
            return 0.0

        if isinstance(rate, str):
            rate = rate.replace("%", "")
            try:
                rate = float(rate)
            except ValueError:
                return 0.0

        rate = float(rate)

        return rate / 100 if rate > 1 else rate

    # -----------------------------
    # Debug Helpers
    # -----------------------------

    def get_stats(self) -> Dict[str, int]:
        return {
            "bosses": len(self.index["bosses"]),
            "items": len(self.index["items"]),
            "loot": len(self.index["loot"]),
            "relationships": len(self.relationships),
        }