from __future__ import annotations

import argparse
import multiprocessing
import os

from rich.console import Console

from services.boss_resolver import BossResolver
from services.item_resolver import ItemResolver
from services.loot_resolver import LootResolver
from services.manifest_service import ManifestService
from services.portal_scanner import PortalScanner
from services.sprite_resolver import SpriteResolver
from services.source_analyzer import SourceAnalyzer
from services.xml_indexer import XMLIndexer

from core.engine import CRSWikiEngine
from services.entity_linker import EntityLinker

from api.discord_bot import run_bot



class Application:
    """CRS Wiki Engine unified entrypoint (CLI + API + Bot)."""

    def __init__(self) -> None:
        self.console = Console()

    # -----------------------------
    # Entry
    # -----------------------------

    def run(self) -> None:
        args = self._parse_args()

        if args.command == "sync":
            self.sync()
            return

        if args.command == "api":
            self.run_api()
            return

        if args.command == "bot":
            self.run_bot()
            return

        if args.command == "both":
            self.run_both()
            return

        raise ValueError(f"Unsupported command: {args.command}")

    # -----------------------------
    # Sync Pipeline (SEU ORIGINAL)
    # -----------------------------

def sync(self) -> None:
    manifest = ManifestService()
    manifest.load()

    source_path = manifest.get_source_path()
    portals = manifest.get_portals()

    # -----------------------------
    # Analysis / preprocessing
    # -----------------------------
    analyzer = SourceAnalyzer(str(source_path))
    analyzer.scan()
    analyzer.save()

    indexer_raw = XMLIndexer(str(source_path))
    indexer_raw.build()
    indexer_raw.save()

    scanner = PortalScanner(
        source_path=source_path,
        manifest_portals=portals,
    )
    discovered = scanner.scan()
    scanner.save()

    # -----------------------------
    # INGESTION LAYER (NOVO)
    # -----------------------------
    from ingestion.parser import SourceParser
    from ingestion.indexer import EntityIndexer
    from storage.database import Database

    db = Database()
    db.save_index(indexed_data)

    parser = SourceParser(str(source_path))
    parsed_data = parser.parse()

    indexer = EntityIndexer()
    indexed_data = indexer.build(parsed_data)

    # opcional: persistir dataset consolidado
    try:
        import json
        with open("data/indexed_dataset.json", "w", encoding="utf-8") as f:
            json.dump(indexed_data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    # -----------------------------
    # ORIGINAL RESOLVERS (mantido)
    # -----------------------------
    boss_resolver = BossResolver(source_path=source_path)
    bosses = boss_resolver.resolve()
    boss_resolver.save()

    loot_resolver = LootResolver(source_path=source_path)
    drops = loot_resolver.resolve()
    loot_resolver.save()

    item_resolver = ItemResolver(source_path=source_path)
    items = item_resolver.resolve()
    item_resolver.save()

    sprite_resolver = SpriteResolver(source_path=source_path)
    sprites = sprite_resolver.resolve()
    sprite_resolver.save()

    # -----------------------------
    # LOG OUTPUT
    # -----------------------------
    self.console.print(
        f"[green]PortalScanner completed:[/green] {len(discovered)} portal(s)"
    )
    self.console.print(
        f"[green]BossResolver completed:[/green] {len(bosses)} boss(es)"
    )
    self.console.print(
        f"[green]LootResolver completed:[/green] {len(drops)} drop(s)"
    )
    self.console.print(
        f"[green]ItemResolver completed:[/green] {len(items)} item(s)"
    )
    self.console.print(
        f"[green]SpriteResolver completed:[/green] {len(sprites)} sprite(s)"
    )

    self.console.print(
        f"[cyan]Ingestion completed:[/cyan] "
        f"{len(indexed_data['index']['bosses'])} bosses, "
        f"{len(indexed_data['index']['items'])} items"
    )

    # -----------------------------
    # Engine Setup (shared runtime)
    # -----------------------------

    def _build_engine(self) -> CRSWikiEngine:
        boss_resolver = BossResolver()
        loot_resolver = LootResolver()
        entity_linker = EntityLinker()

        return CRSWikiEngine(
            boss_resolver=boss_resolver,
            loot_resolver=loot_resolver,
            entity_linker=entity_linker,
        )

    # -----------------------------
    # API Runner
    # -----------------------------

    def run_api(self) -> None:
        import uvicorn

        self.console.print("[cyan]Starting API server...[/cyan]")

        uvicorn.run(
            "api.http_server:app",
            host="0.0.0.0",
            port=int(os.getenv("PORT", 8000)),
            reload=True,
        )

    # -----------------------------
    # Bot Runner
    # -----------------------------

    def run_bot(self) -> None:
        self.console.print("[cyan]Starting Discord bot...[/cyan]")

        token = os.getenv("DISCORD_TOKEN")

        if not token:
            raise ValueError("DISCORD_TOKEN not set")

        run_bot(token)

    # -----------------------------
    # Both (parallel execution)
    # -----------------------------

    def run_both(self) -> None:
        self.console.print("[cyan]Starting API + Bot...[/cyan]")

        p1 = multiprocessing.Process(target=self.run_api)
        p2 = multiprocessing.Process(target=self.run_bot)

        p1.start()
        p2.start()

        p1.join()
        p2.join()

    # -----------------------------
    # CLI
    # -----------------------------

    def _parse_args(self) -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            prog="crs-wiki-engine",
            description="CRS Wiki Engine command-line interface.",
        )

        subparsers = parser.add_subparsers(dest="command", required=True)

        subparsers.add_parser("sync", help="Analyze source and sync workspace data.")
        subparsers.add_parser("api", help="Run HTTP API server.")
        subparsers.add_parser("bot", help="Run Discord bot.")
        subparsers.add_parser("both", help="Run API + Discord bot together.")

        return parser.parse_args()


if __name__ == "__main__":
    Application().run()