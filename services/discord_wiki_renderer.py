from __future__ import annotations

from typing import Dict, Any
import discord


class DiscordWikiRenderer:
    """
    Converts WikiEngine output into rich Discord embeds.

    This is the FINAL presentation layer:
    - Boss summary
    - Stats
    - Phases
    - Loot table
    - Metadata
    """

    def render_boss_page(self, page: Dict[str, Any]) -> discord.Embed:
        boss = page["boss"]
        meta = page["meta"]
        loot = page["loot"]

        embed = discord.Embed(
            title=meta["title"],
            description=boss.get("summary", "No description available."),
            color=0x2ecc71
        )

        # -----------------------------
        # Stats Section
        # -----------------------------
        stats = boss.get("stats", {})
        if stats:
            embed.add_field(
                name="Stats",
                value=self._format_stats(stats),
                inline=False
            )

        # -----------------------------
        # Phases Section
        # -----------------------------
        phases = page.get("phases", [])
        if phases:
            embed.add_field(
                name="Phases",
                value=self._format_phases(phases),
                inline=False
            )

        # -----------------------------
        # Loot Section
        # -----------------------------
        loot_items = loot.get("items", [])
        if loot_items:
            embed.add_field(
                name="Loot Table",
                value=self._format_loot(loot_items),
                inline=False
            )

        # -----------------------------
        # Metadata
        # -----------------------------
        embed.set_footer(
            text=f"Boss ID: {meta.get('id')} | CRS Wiki Engine"
        )

        return embed

    # -----------------------------
    # Formatting Helpers
    # -----------------------------

    def _format_stats(self, stats: Dict[str, Any]) -> str:
        return "\n".join(
            f"**{k.upper()}**: {v}"
            for k, v in stats.items()
        ) or "None"

    def _format_phases(self, phases: list) -> str:
        return "\n".join(
            f"- Phase {p.get('index')}: {p.get('name')}"
            for p in phases
        ) or "None"

    def _format_loot(self, loot_items: list) -> str:
        # limit for Discord readability
        lines = []

        for item in loot_items[:10]:
            name = item.get("name")
            rate = item.get("dropRate")
            rarity = item.get("rarity")

            lines.append(f"- **{name}** ({rate}, {rarity})")

        return "\n".join(lines) or "None"