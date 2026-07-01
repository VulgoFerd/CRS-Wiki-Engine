from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Iterable
import re
import difflib


# -----------------------------
# Data Model
# -----------------------------

@dataclass
class Boss:
    id: str
    name: str
    raw: Dict[str, Any] = field(default_factory=dict)

    # optional enriched fields
    aliases: List[str] = field(default_factory=list)
    phases: List[Dict[str, Any]] = field(default_factory=list)
    loot_table: List[Dict[str, Any]] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)


# -----------------------------
# Resolver Core
# -----------------------------

class BossResolver:
    """
    Core intelligence layer for boss resolution.

    Responsibilities:
    - Normalize boss identifiers
    - Resolve by id, name or alias
    - Fuzzy matching for unknown references
    - Enrich boss metadata for Wiki generation
    """

    def __init__(self, bosses: Optional[Iterable[Dict[str, Any]]] = None):
        self._bosses_by_id: Dict[str, Boss] = {}
        self._bosses_by_name: Dict[str, Boss] = {}
        self._name_index: List[str] = []

        if bosses:
            self.load_bosses(bosses)

    # -----------------------------
    # Loading / Indexing
    # -----------------------------

    def load_bosses(self, bosses: Iterable[Dict[str, Any]]) -> None:
        for b in bosses:
            boss = self._build_boss(b)
            self._register(boss)

    def _build_boss(self, data: Dict[str, Any]) -> Boss:
        boss = Boss(
            id=str(data.get("id", "")),
            name=str(data.get("name", "")),
            raw=data
        )

        boss.aliases = self._extract_aliases(data)
        boss.phases = data.get("phases", []) or []
        boss.loot_table = data.get("loot", []) or []
        boss.stats = data.get("stats", {}) or {}

        return boss

    def _register(self, boss: Boss) -> None:
        self._bosses_by_id[boss.id] = boss

        normalized_name = self.normalize(boss.name)
        self._bosses_by_name[normalized_name] = boss
        self._name_index.append(normalized_name)

        for alias in boss.aliases:
            self._bosses_by_name[self.normalize(alias)] = boss
            self._name_index.append(self.normalize(alias))

    # -----------------------------
    # Normalization
    # -----------------------------

    def normalize(self, text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"[^a-z0-9\s]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text

    def _extract_aliases(self, data: Dict[str, Any]) -> List[str]:
        aliases = data.get("aliases", [])
        if isinstance(aliases, str):
            aliases = [aliases]
        return [a for a in aliases if a]

    # -----------------------------
    # Resolution API
    # -----------------------------

    def resolve(self, query: str) -> Optional[Boss]:
        """
        Resolve a boss by:
        - ID
        - Exact name / alias
        - Fuzzy match fallback
        """

        if not query:
            return None

        # 1. Direct ID
        if query in self._bosses_by_id:
            return self._bosses_by_id[query]

        norm = self.normalize(query)

        # 2. Exact name/alias match
        if norm in self._bosses_by_name:
            return self._bosses_by_name[norm]

        # 3. Fuzzy match fallback
        return self._fuzzy_resolve(norm)

    def _fuzzy_resolve(self, norm_query: str) -> Optional[Boss]:
        matches = difflib.get_close_matches(norm_query, self._name_index, n=1, cutoff=0.75)

        if not matches:
            return None

        best = matches[0]
        return self._bosses_by_name.get(best)

    # -----------------------------
    # Enrichment Layer (Wiki Core)
    # -----------------------------

    def enrich_boss(self, boss: Boss) -> Dict[str, Any]:
        """
        Transforms raw boss data into Wiki-ready structure.
        This is where intelligence expansion happens.
        """

        return {
            "id": boss.id,
            "name": boss.name,
            "aliases": boss.aliases,
            "stats": self._normalize_stats(boss.stats),
            "phases": self._normalize_phases(boss.phases),
            "loot": self._normalize_loot(boss.loot_table),
            "summary": self._generate_summary(boss),
        }

    def _normalize_stats(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        return {
            k: v for k, v in stats.items()
            if v is not None
        }

    def _normalize_phases(self, phases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        cleaned = []
        for i, p in enumerate(phases):
            cleaned.append({
                "index": i,
                "name": p.get("name", f"Phase {i+1}"),
                "hp_threshold": p.get("hpThreshold"),
                "abilities": p.get("abilities", [])
            })
        return cleaned

    def _normalize_loot(self, loot: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            {
                "item": drop.get("item"),
                "rate": drop.get("rate"),
                "quantity": drop.get("quantity", 1)
            }
            for drop in loot
        ]

    def _generate_summary(self, boss: Boss) -> str:
        hp = boss.stats.get("hp", "unknown")
        defense = boss.stats.get("defense", "unknown")
        phases = len(boss.phases)

        return (
            f"{boss.name} is a boss entity with {hp} HP and {defense} DEF. "
            f"It has {phases} phase(s) and a structured loot table."
        )

    # -----------------------------
    # Debug / Inspection
    # -----------------------------

    def list_bosses(self) -> List[str]:
        return list(self._bosses_by_id.keys())

    def get_raw(self, boss_id: str) -> Optional[Dict[str, Any]]:
        boss = self._bosses_by_id.get(boss_id)
        return boss.raw if boss else None