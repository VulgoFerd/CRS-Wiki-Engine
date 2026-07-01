from __future__ import annotations

from typing import Dict, List, Set, Tuple, Optional
import re
import itertools


class EntityLinker:
    """
    Builds relationships between entities in the Wiki system.

    Responsibilities:
    - Link bosses to similar bosses
    - Link loot items to multiple sources
    - Build alias graphs
    - Prepare future knowledge graph expansion
    """

    def __init__(self):
        self.links: Dict[str, Set[str]] = {}
        self.reverse_links: Dict[str, Set[str]] = {}

    # -----------------------------
    # Link Management
    # -----------------------------

    def add_link(self, a: str, b: str) -> None:
        if a == b:
            return

        self.links.setdefault(a, set()).add(b)
        self.reverse_links.setdefault(b, set()).add(a)

    def add_bidirectional_link(self, a: str, b: str) -> None:
        self.add_link(a, b)
        self.add_link(b, a)

    # -----------------------------
    # Boss Linking Logic
    # -----------------------------

    def link_bosses_by_similarity(self, bosses: List[Dict]) -> None:
        """
        Links bosses with similar names or shared keywords.
        """

        for b1, b2 in itertools.combinations(bosses, 2):
            id1 = b1.get("id")
            id2 = b2.get("id")

            if not id1 or not id2:
                continue

            score = self._name_similarity(
                b1.get("name", ""),
                b2.get("name", "")
            )

            if score >= 0.6:
                self.add_bidirectional_link(id1, id2)

    def link_boss_to_loot(self, boss_id: str, loot_items: List[Dict]) -> None:
        for item in loot_items:
            item_id = item.get("id") or self._normalize(item.get("name", ""))
            if item_id:
                self.add_link(boss_id, item_id)

    # -----------------------------
    # Alias Linking
    # -----------------------------

    def link_aliases(self, entity_id: str, aliases: List[str]) -> None:
        for alias in aliases:
            alias_id = self._normalize(alias)
            self.add_bidirectional_link(entity_id, alias_id)

    # -----------------------------
    # Querying
    # -----------------------------

    def get_related(self, entity_id: str) -> Set[str]:
        return self.links.get(entity_id, set())

    def get_backlinks(self, entity_id: str) -> Set[str]:
        return self.reverse_links.get(entity_id, set())

    def get_all_links(self, entity_id: str) -> Set[str]:
        return self.get_related(entity_id) | self.get_backlinks(entity_id)

    # -----------------------------
    # Helpers
    # -----------------------------

    def _normalize(self, text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"[^a-z0-9\s]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text

    def _name_similarity(self, a: str, b: str) -> float:
        """
        Lightweight similarity (token overlap).
        """

        set_a = set(self._normalize(a).split())
        set_b = set(self._normalize(b).split())

        if not set_a or not set_b:
            return 0.0

        return len(set_a & set_b) / len(set_a | set_b)