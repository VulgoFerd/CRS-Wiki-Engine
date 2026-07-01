from __future__ import annotations

from typing import Dict, Any, Optional, List
from datetime import datetime

from services.boss_resolver import BossResolver
from services.loot_resolver import LootResolver


# -----------------------------
# Wiki Builder Core
# -----------------------------

class WikiBuilder:
    """
    Orchestrates all resolvers into final Wiki-ready structures.

    Responsibilities:
    - Combine boss + loot intelligence
    - Generate structured wiki pages
    - Normalize output for Discord/API consumption
    """

    def __init__(
        self,
        boss_resolver: BossResolver,
        loot_resolver: LootResolver
    ):
        self.boss_resolver = boss_resolver
        self.loot_resolver = loot_resolver

    # -----------------------------
    # Main Entry Point
    # -----------------------------

    def build_boss_page(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Full pipeline:
        query -> boss resolution -> enrichment -> loot enrichment -> wiki page
        """

        boss = self.boss_resolver.resolve(query)
        if not boss:
            return None

        boss_data = self.boss_resolver.enrich_boss(boss)

        loot_data = self._build_loot_section(boss_data.get("loot", []))

        return self._compose_page(boss_data, loot_data)

    # -----------------------------
    # Loot Pipeline
    # -----------------------------

    def _build_loot_section(self, loot_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        enriched = []

        for entry in loot_entries:
            resolved = self.loot_resolver.resolve(entry.get("item") or entry.get("name"))

            if resolved:
                enriched.append(self.loot_resolver.enrich_loot(resolved))
            else:
                enriched.append({
                    "name": entry.get("item"),
                    "dropRate": entry.get("rate"),
                    "quantity": entry.get("quantity"),
                    "rarity": "unknown"
                })

        return enriched

    # -----------------------------
    # Page Composition
    # -----------------------------

    def _compose_page(
        self,
        boss_data: Dict[str, Any],
        loot_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:

        return {
            "meta": self._build_meta(boss_data),
            "boss": self._build_boss_section(boss_data),
            "loot": self._build_loot_section_output(loot_data),
            "phases": boss_data.get("phases", []),
            "generatedAt": datetime.utcnow().isoformat() + "Z"
        }

    # -----------------------------
    # Sections
    # -----------------------------

    def _build_meta(self, boss_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "title": boss_data.get("name"),
            "id": boss_data.get("id"),
            "aliases": boss_data.get("aliases", []),
            "type": "boss_page"
        }

    def _build_boss_section(self, boss_data: Dict[str, Any]) -> Dict[str, Any]:
        stats = boss_data.get("stats", {})

        return {
            "summary": boss_data.get("summary"),
            "stats": {
                "hp": stats.get("hp"),
                "defense": stats.get("defense"),
                "attack": stats.get("attack"),
                "speed": stats.get("speed"),
            }
        }

    def _build_loot_section_output(self, loot_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "items": loot_data,
            "totalItems": len(loot_data),
            "rarityBreakdown": self._calculate_rarity_breakdown(loot_data)
        }

    # -----------------------------
    # Analytics Layer (Wiki Intelligence)
    # -----------------------------

    def _calculate_rarity_breakdown(self, loot_data: List[Dict[str, Any]]) -> Dict[str, int]:
        breakdown = {
            "legendary": 0,
            "rare": 0,
            "uncommon": 0,
            "common": 0,
            "unknown": 0
        }

        for item in loot_data:
            rarity = item.get("rarity", "unknown")
            if rarity not in breakdown:
                rarity = "unknown"
            breakdown[rarity] += 1

        return breakdown

    # -----------------------------
    # Export Formats (future-proofing)
    # -----------------------------

    def to_markdown(self, page: Dict[str, Any]) -> str:
        """
        Optional renderer for Wiki export.
        """

        boss = page["boss"]
        loot = page["loot"]

        lines = []

        lines.append(f"# {page['meta']['title']}\n")
        lines.append(f"{boss['summary']}\n")

        lines.append("## Stats")
        stats = boss["stats"]
        for k, v in stats.items():
            lines.append(f"- **{k.upper()}**: {v}")

        lines.append("\n## Loot Table")
        for item in loot["items"]:
            lines.append(
                f"- {item.get('name')} "
                f"({item.get('dropRate')}, {item.get('rarity')})"
            )

        lines.append("\n## Phases")
        for p in page["phases"]:
            lines.append(f"- {p.get('name')}")

        return "\n".join(lines)

    def to_json(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean export format (API-ready)
        """
        return page