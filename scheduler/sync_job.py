from __future__ import annotations

import time
from typing import Optional

from rich.console import Console

from ingestion.parser import SourceParser
from ingestion.indexer import EntityIndexer

from storage.database import Database


class SyncJob:
    """
    Automated pipeline runner for CRS Wiki Engine.

    Responsibilities:
    - Periodically re-run ingestion pipeline
    - Update indexed dataset
    - Persist results
    - Enable "self-updating wiki"
    """

    def __init__(
        self,
        source_path: str,
        interval_seconds: int = 3600
    ):
        self.source_path = source_path
        self.interval = interval_seconds

        self.console = Console()
        self.db = Database()

        self._running = False

    # -----------------------------
    # Main Loop
    # -----------------------------

    def start(self) -> None:
        self._running = True

        self.console.print("[cyan]SyncJob started...[/cyan]")

        while self._running:
            try:
                self._run_cycle()
            except Exception as e:
                self.console.print(f"[red]Sync error:[/red] {e}")

            time.sleep(self.interval)

    def stop(self) -> None:
        self._running = False
        self.console.print("[yellow]SyncJob stopped.[/yellow]")

    # -----------------------------
    # Single Cycle
    # -----------------------------

    def _run_cycle(self) -> None:
        self.console.print("[blue]Running ingestion cycle...[/blue]")

        # 1. Parse raw source
        parser = SourceParser(self.source_path)
        parsed = parser.parse()

        # 2. Index dataset
        indexer = EntityIndexer()
        indexed = indexer.build(parsed)

        # 3. Persist dataset
        self.db.save_index(indexed)

        stats = indexer.get_stats()

        self.console.print(
            f"[green]Cycle complete:[/green] "
            f"{stats['bosses']} bosses | "
            f"{stats['items']} items | "
            f"{stats['loot']} loot entries"
        )