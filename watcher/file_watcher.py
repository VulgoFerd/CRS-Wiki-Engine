from __future__ import annotations

import time
from pathlib import Path
from typing import Optional, Callable, Dict

from rich.console import Console


class FileWatcher:
    """
    Watches the RotMG source directory for changes
    and triggers automatic sync cycles.

    This replaces polling loops with event-like behavior.
    """

    def __init__(
        self,
        source_path: str,
        on_change: Callable[[], None],
        debounce_seconds: float = 5.0
    ):
        self.source_path = Path(source_path)
        self.on_change = on_change
        self.debounce = debounce_seconds

        self.console = Console()
        self._last_snapshot: Dict[str, float] = {}
        self._running = False

    # -----------------------------
    # Public API
    # -----------------------------

    def start(self) -> None:
        self._running = True
        self.console.print("[cyan]FileWatcher started...[/cyan]")

        self._snapshot_initial()

        while self._running:
            try:
                if self._detect_changes():
                    self.console.print("[yellow]Change detected, triggering sync...[/yellow]")
                    self.on_change()
                    time.sleep(self.debounce)

                time.sleep(1)

            except Exception as e:
                self.console.print(f"[red]Watcher error:[/red] {e}")

    def stop(self) -> None:
        self._running = False
        self.console.print("[yellow]FileWatcher stopped.[/yellow]")

    # -----------------------------
    # Snapshot System
    # -----------------------------

    def _snapshot_initial(self) -> None:
        self._last_snapshot = self._scan_directory()

    def _scan_directory(self) -> Dict[str, float]:
        snapshot = {}

        for file in self.source_path.rglob("*"):
            if file.is_file():
                try:
                    snapshot[str(file)] = file.stat().st_mtime
                except Exception:
                    continue

        return snapshot

    def _detect_changes(self) -> bool:
        current = self._scan_directory()

        if current != self._last_snapshot:
            self._last_snapshot = current
            return True

        return False