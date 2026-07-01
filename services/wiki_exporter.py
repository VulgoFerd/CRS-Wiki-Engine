from __future__ import annotations

from typing import Dict, Any, List
from pathlib import Path
import json


class WikiExporter:
    """
    Final stage of CRS Wiki Engine.

    Responsibilities:
    - Convert engine output into wiki pages
    - Export Markdown files
    - Optionally prepare HTML structure
    - Organize file-based wiki system
    """

    def __init__(self, output_dir: str = "wiki_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # -----------------------------
    # Entry Point
    # -----------------------------

    def export_boss_page(self, page: Dict[str, Any]) -> Path:
        boss_id = page["meta"]["id"]
        path = self.output_dir / f"{boss_id}.md"

        content = self._render_markdown(page)

        path.write_text(content, encoding="utf-8")

        return path

    def export_bulk(self, pages: List[Dict[str, Any]]) -> List[Path]:
        paths = []

        for page in pages:
            paths.append(self.export_boss_page(page))

        return paths

    # -----------------------------
    # Markdown Renderer
    # -----------------------------

    def _render_markdown(self, page: Dict[str, Any]) -> str:
        boss = page["boss"]
        loot = page["loot"]
        meta = page["meta"]

        lines = []

        # Title
        lines.append(f"# {meta['title']}\n")

        # Summary
        lines.append("## Overview")
        lines.append(boss.get("summary", "No description available."))

        # Stats
        lines.append("\n## Stats")
        for k, v in boss.get("stats", {}).items():
            lines.append(f"- **{k.upper()}**: {v}")

        # Phases
        lines.append("\n## Phases")
        if page.get("phases"):
            for p in page["phases"]:
                lines.append(f"- Phase {p.get('index')} - {p.get('name')}")
        else:
            lines.append("- None")

        # Loot
        lines.append("\n## Loot Table")
        for item in loot.get("items", []):
            lines.append(
                f"- {item.get('name')} "
                f"({item.get('dropRate')}, {item.get('rarity')})"
            )

        # Metadata
        lines.append("\n## Metadata")
        lines.append(f"- Boss ID: {meta['id']}")
        lines.append(f"- Aliases: {', '.join(meta.get('aliases', [])) or 'None'}")

        return "\n".join(lines)

    # -----------------------------
    # Optional JSON Export
    # -----------------------------

    def export_json(self, page: Dict[str, Any]) -> Path:
        boss_id = page["meta"]["id"]
        path = self.output_dir / f"{boss_id}.json"

        with open(path, "w", encoding="utf-8") as f:
            json.dump(page, f, indent=2, ensure_ascii=False)

        return path