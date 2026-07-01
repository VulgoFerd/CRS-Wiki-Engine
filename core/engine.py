from __future__ import annotations

from typing import Dict, Any, Optional

from ingestion.parser import SourceParser
from ingestion.indexer import EntityIndexer

from services.boss_resolver import BossResolver
from services.loot_resolver import LootResolver
from services.entity_linker import EntityLinker


class CRSWikiEngine:
    """
    SINGLE SOURCE OF TRUTH for wiki generation.

    This version guarantees:
    - consistent WikiPage schema
    - ingestion integration
    - deterministic output for Discord + export
    """

    def __init__(
        self,
        boss_resolver: BossResolver,
        loot_resolver: LootResolver,
        entity_linker: EntityLinker,
        source_path: Optional[str] = None,
    ):
        self.boss_resolver = boss_resolver
        self.loot_resolver = loot_resolver
        self.entity_linker = entity_linker

        self.source_path = source_path

        # cache (important for bot performance)
        self._cache: Dict[str, Dict[str, Any]] = {}

    # -----------------------------
    # PUBLIC API (USED BY BOT)
    # -----------------------------

    def generate_boss_wiki(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Main entry point for Discord bot.
        Always returns a FULL WikiPage (never partial data).
        """

        cache_key = query.lower().strip()

        if cache_key in self._cache:
            return self._cache[cache_key]

        # 1. INGESTION (ONLY IF SOURCE EXISTS)
        parsed_data = None
        indexed_data = None

        if self.source_path:
            parser = SourceParser(self.source_path)
            parsed_data = parser.parse()

            indexer = EntityIndexer()
            indexed_data = indexer.build(parsed_data)

        # 2. RESOLVE BOSS
        boss = self.boss_resolver.resolve(query)

        if not boss:
            return None

        # 3. RESOLVE LOOT
        loot = self.loot_resolver.resolve(boss.get("id") or boss.get("name"))

        # 4. ENTITY LINKING
        linked = self.entity_linker.link(boss, loot)

        # 5. BUILD FINAL WIKI PAGE (STRICT CONTRACT)
        page = self._build_wiki_page(
            boss=boss,
            loot=loot,
            linked=linked,
            indexed=indexed_data,
        )

        self._cache[cache_key] = page

        return page

    # -----------------------------
    # GRAPH API (Discord !graph)
    # -----------------------------

    def get_entity_graph(self, entity_id: str) -> Dict[str, Any]:
        return self.entity_linker.get_graph(entity_id)

    # -----------------------------
    # STRICT WIKI CONTRACT (CRITICAL PART)
    # -----------------------------

    def _build_wiki_page(
        self,
        boss: Dict[str, Any],
        loot: Dict[str, Any],
        linked: Dict[str, Any],
        indexed: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:

        return {
            "meta": {
                "id": boss.get("id"),
                "title": boss.get("name"),
                "source": boss.get("source"),
                "aliases": boss.get("aliases", []),
            },

            "boss": {
                "summary": boss.get("summary") or boss.get("description") or "No description available.",
                "stats": boss.get("stats", {}),
            },

            "phases": boss.get("phases", []),

            "loot": {
                "items": loot if isinstance(loot, list) else [],
            },

            "linked": linked,

            "indexed": indexed or {},
        }