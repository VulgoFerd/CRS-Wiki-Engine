from __future__ import annotations

import os
import discord
from discord.ext import commands

from core.engine import CRSWikiEngine
from services.boss_resolver import BossResolver
from services.loot_resolver import LootResolver
from services.entity_linker import EntityLinker

from services.discord_wiki_renderer import DiscordWikiRenderer


# -----------------------------
# Engine setup (IMPORTANTE: único)
# -----------------------------

boss_resolver = BossResolver()
loot_resolver = LootResolver()
entity_linker = EntityLinker()

engine = CRSWikiEngine(
    boss_resolver=boss_resolver,
    loot_resolver=loot_resolver,
    entity_linker=entity_linker,
)

renderer = DiscordWikiRenderer()


# -----------------------------
# Bot setup
# -----------------------------

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# -----------------------------
# Events
# -----------------------------

@bot.event
async def on_ready():
    print(f"[CRS Wiki Bot] Online as {bot.user}")


# -----------------------------
# Commands
# -----------------------------

@bot.command(name="boss")
async def boss(ctx, *, query: str):
    try:
        page = engine.generate_boss_wiki(query)

        if not page:
            await ctx.send("❌ Boss não encontrado.")
            return

        # SAFE RENDERING (never crash embed)
        embed = renderer.render_boss_page(page)

        if not embed:
            await ctx.send("⚠️ Erro ao gerar embed da wiki.")
            return

        await ctx.send(embed=embed)

    except Exception as e:
        # NEVER CRASH BOT
        await ctx.send("❌ Erro interno ao gerar wiki.")
        print(f"[CRS BOT ERROR] {e}")


@bot.command(name="graph")
async def graph(ctx, entity_id: str):
    """
    Shows entity relationship graph.
    """

    try:
        data = engine.get_entity_graph(entity_id)

        text = (
            f"**Entity:** `{data['entity']}`\n\n"
            f"**Related:** {', '.join(data['related']) or 'None'}\n\n"
            f"**Backlinks:** {', '.join(data['backlinks']) or 'None'}"
        )

        await ctx.send(text)

    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")


# -----------------------------
# Runner
# -----------------------------

def run_bot(token: str):
    if not token:
        raise ValueError("DISCORD_TOKEN not provided")

    bot.run(token)


# -----------------------------
# CLI fallback (opcional)
# -----------------------------

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    run_bot(token)