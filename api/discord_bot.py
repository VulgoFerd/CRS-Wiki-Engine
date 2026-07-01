from __future__ import annotations

import discord
from discord.ext import commands

from core.engine import CRSWikiEngine
from services.boss_resolver import BossResolver
from services.loot_resolver import LootResolver
from services.entity_linker import EntityLinker


# -----------------------------
# Engine Setup
# -----------------------------

boss_resolver = BossResolver()
loot_resolver = LootResolver()
entity_linker = EntityLinker()

engine = CRSWikiEngine(
    boss_resolver=boss_resolver,
    loot_resolver=loot_resolver,
    entity_linker=entity_linker
)


# -----------------------------
# Bot Setup
# -----------------------------

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# -----------------------------
# Commands
# -----------------------------

@bot.command(name="boss")
async def boss(ctx, *, query: str):
    """
    !boss <name>
    Generates full wiki page for a boss.
    """

    page = engine.generate_boss_wiki(query)

    if not page:
        await ctx.send("Boss não encontrado.")
        return

    boss = page["boss"]

    embed = discord.Embed(
        title=page["meta"]["title"],
        description=boss["summary"],
        color=0x2ecc71
    )

    stats = boss["stats"]
    embed.add_field(name="HP", value=stats.get("hp"), inline=True)
    embed.add_field(name="DEF", value=stats.get("defense"), inline=True)

    loot = page["loot"]["items"][:5]
    loot_text = "\n".join(
        f"- {i.get('name')} ({i.get('rarity')})"
        for i in loot
    )

    embed.add_field(name="Loot (top 5)", value=loot_text or "None", inline=False)

    await ctx.send(embed=embed)


@bot.command(name="graph")
async def graph(ctx, entity_id: str):
    """
    !graph <entity_id>
    Shows relationship graph.
    """

    data = engine.get_entity_graph(entity_id)

    text = (
        f"**Entity:** {data['entity']}\n\n"
        f"**Related:** {', '.join(data['related']) or 'None'}\n\n"
        f"**Backlinks:** {', '.join(data['backlinks']) or 'None'}"
    )

    await ctx.send(text)


# -----------------------------
# Run
# -----------------------------

def run_bot(token: str):
    bot.run(token)