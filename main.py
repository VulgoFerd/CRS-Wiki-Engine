from __future__ import annotations

import argparse

from rich.console import Console

from services.manifest_service import ManifestService
from services.portal_scanner import PortalScanner
from services.source_analyzer import SourceAnalyzer
from services.xml_indexer import XMLIndexer


class Application:
    """Command-line entrypoint for CRS Wiki Engine."""

    def __init__(self) -> None:
        self.console = Console()

    def run(self) -> None:
        args = self._parse_args()

        if args.command == "sync":
            self.sync()
            return

        raise ValueError(f"Unsupported command: {args.command}")

    def sync(self) -> None:
        manifest = ManifestService()
        manifest.load()

        source_path = manifest.get_source_path()
        portals = manifest.get_portals()

        analyzer = SourceAnalyzer(str(source_path))
        analyzer.scan()
        analyzer.save()

        indexer = XMLIndexer(str(source_path))
        indexer.build()
        indexer.save()

        scanner = PortalScanner(
            source_path=source_path,
            manifest_portals=portals,
        )
        discovered = scanner.scan()
        scanner.save()

        self.console.print(
            f"[green]PortalScanner completed:[/green] "
            f"{len(discovered)} portal(s) discovered."
        )

    def _parse_args(self) -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            prog="crs-wiki-engine",
            description="CRS Wiki Engine command-line interface.",
        )
        subparsers = parser.add_subparsers(dest="command", required=True)
        subparsers.add_parser("sync", help="Analyze source and sync workspace data.")
        return parser.parse_args()


if __name__ == "__main__":
    Application().run()
