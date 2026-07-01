from __future__ import annotations

from typing import Dict, Any, Optional

from services.boss_resolver import BossResolver
from services.loot_resolver import LootResolver
from services.wiki_builder import WikiBuilder
from services.entity_linker import EntityLinker


class CRSWikiEngine:
    """
    Main orchestrator of the entire system.

    This is the single entry point used by:
    - Discord bot
    - API layer
    - CLI tools
    """

    def __init__(
        self,
        boss_resolver: BossResolver,
        loot_resolver: LootResolver,
        entity_linker: EntityLinker
    ):
        self.boss_resolver = boss_resolver
        self.loot_resolver = loot_resolver
        self.entity_linker = entity_linker

        self.wiki_builder = WikiBuilder(
            boss_resolver=boss_resolver,
            loot_resolver=loot_resolver
        )

    # -----------------------------
    # Public API
    # -----------------------------

    def generate_boss_wiki(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Full pipeline entry point.
        """

        page = self.wiki_builder.build_boss_page(query)

        if not page:
            return None

        self._post_process_links(page)

        return page

    def generate_markdown(self, query: str) -> Optional[str]:
        page = self.generate_boss_wiki(query)
        if not page:
            return None

        return self.wiki_builder.to_markdown(page)

    # -----------------------------
    # Link Post-Processing
    # -----------------------------

    def _post_process_links(self, page: Dict[str, Any]) -> None:
        """
        Builds entity relationships after wiki generation.
        """

        boss_id = page["meta"]["id"]

        # link phases (future expansion)
        for phase in page.get("phases", []):
            phase_id = f"{boss_id}_phase_{phase.get('index')}"
            self.entity_linker.add_link(boss_id, phase_id)

        # link loot
        for item in page["loot"]["items"]:
            item_name = item.get("name")
            if item_name:
                self.entity_linker.add_link(boss_id, item_name)

        # link internal stats relationships (future graph use)
        stats = page["boss"]["stats"]
        for k, v in stats.items():
            stat_id = f"{boss_id}_stat_{k}"
            self.entity_linker.add_link(boss_id, stat_id)

    # -----------------------------
    # Debug / Graph View
    # -----------------------------

    def get_entity_graph(self, entity_id: str) -> Dict[str, Any]:
        return {
            "entity": entity_id,
            "related": list(self.entity_linker.get_related(entity_id)),
            "backlinks": list(self.entity_linker.get_backlinks(entity_id)),
            "connected": list(self.entity_linker.get_all_links(entity_id)),
        }