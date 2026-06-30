from __future__ import annotations

import json
import re
from pathlib import Path

from models.drop import Drop


class LootResolver:
    """Resolve drops for bosses discovered by BossResolver."""

    def __init__(
        self,
        source_path: Path,
        bosses_path: Path = Path("workspace/database/bosses/bosses.json"),
        output_dir: Path = Path("workspace/database/loot"),
    ) -> None:
        self.source_path = source_path
        self.bosses_path = bosses_path
        self.output_dir = output_dir
        self.resolved: list[Drop] = []

    def resolve(self) -> list[Drop]:
        """Resolve drops from behavior blocks and loot template methods."""

        self._validate_inputs()
        bosses = self._load_bosses()
        behavior_index = self._load_behavior_index()
        loot_templates = self._load_loot_templates()

        drops: list[Drop] = []
        seen: set[tuple[str, str, str, str]] = set()

        for boss in bosses:
            behavior = behavior_index.get(boss["name"])
            if behavior is None:
                continue

            boss_drops = self._extract_drops_from_block(
                block=str(behavior["block"]),
                source_file=str(behavior["source_file"]),
                boss=boss,
                loot_templates=loot_templates,
            )

            for drop in boss_drops:
                key = (
                    drop.portal_name,
                    drop.boss_name,
                    drop.drop_type,
                    f"{drop.item_name}:{drop.raw_probability}:{drop.tier}:{drop.item_type}",
                )
                if key in seen:
                    continue

                seen.add(key)
                drops.append(drop)

        self.resolved = drops
        return self.resolved

    def save(self) -> None:
        """Persist resolved loot under the workspace database directory."""

        self.output_dir.mkdir(parents=True, exist_ok=True)

        by_portal: dict[str, dict[str, list[dict[str, object]]]] = {}
        for drop in self.resolved:
            portal = by_portal.setdefault(drop.portal_name, {})
            portal.setdefault(drop.boss_name, []).append(drop.to_dict())

        summary = {
            "total": len(self.resolved),
            "portals": by_portal,
        }

        with (self.output_dir / "loot.json").open("w", encoding="utf8") as file:
            json.dump(summary, file, indent=4, ensure_ascii=False)

        for portal_name, bosses in by_portal.items():
            portal_dir = self.output_dir / self._slugify(portal_name)
            portal_dir.mkdir(parents=True, exist_ok=True)

            with (portal_dir / "loot.json").open("w", encoding="utf8") as file:
                json.dump(
                    {
                        "total": sum(len(drops) for drops in bosses.values()),
                        "bosses": bosses,
                    },
                    file,
                    indent=4,
                    ensure_ascii=False,
                )

            for boss_name, drops in bosses.items():
                with (
                    portal_dir / f"{self._slugify(boss_name)}.json"
                ).open("w", encoding="utf8") as file:
                    json.dump(
                        {"total": len(drops), "drops": drops},
                        file,
                        indent=4,
                        ensure_ascii=False,
                    )

    def _validate_inputs(self) -> None:
        if not self.source_path.exists():
            raise FileNotFoundError(f"Source path not found: {self.source_path}")

        if not self.bosses_path.exists():
            raise FileNotFoundError(f"Boss database not found: {self.bosses_path}")

    def _load_bosses(self) -> list[dict[str, object]]:
        with self.bosses_path.open("r", encoding="utf8") as file:
            data = json.load(file)

        bosses = []
        for portal_bosses in data.get("portals", {}).values():
            bosses.extend(portal_bosses)

        return bosses

    def _load_behavior_index(self) -> dict[str, dict[str, object]]:
        behavior_index: dict[str, dict[str, object]] = {}
        init_pattern = re.compile(r'\.Init\("([^"]+)"\s*,')

        for path in (self.source_path / "server").rglob("*.cs"):
            text = path.read_text(encoding="utf8", errors="ignore")
            matches = list(init_pattern.finditer(text))

            for index, match in enumerate(matches):
                block_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
                block = text[match.start():block_end]
                behavior_index[match.group(1)] = {
                    "source_file": path.relative_to(self.source_path).as_posix(),
                    "block": block,
                }

        return behavior_index

    def _load_loot_templates(self) -> dict[str, list[dict[str, object]]]:
        templates: dict[str, list[dict[str, object]]] = {}
        loot_defs = self.source_path / "server" / "wServer" / "logic" / "loot" / "LootDefs.cs"
        if not loot_defs.exists():
            return templates

        text = loot_defs.read_text(encoding="utf8", errors="ignore")
        method_pattern = re.compile(
            r'public\s+static\s+ILootDef\[\]\s+(\w+)\s*\(\)\s*\{',
        )
        matches = list(method_pattern.finditer(text))
        for index, match in enumerate(matches):
            block_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            block = text[match.start():block_end]
            templates[match.group(1)] = self._extract_raw_loot_entries(block)

        return templates

    def _extract_drops_from_block(
        self,
        block: str,
        source_file: str,
        boss: dict[str, object],
        loot_templates: dict[str, list[dict[str, object]]],
    ) -> list[Drop]:
        drops = []
        raw_entries = self._extract_raw_loot_entries(block)
        raw_entries.extend(self._extract_template_entries(block, loot_templates))

        for entry in raw_entries:
            drops.append(
                Drop(
                    item_name=str(entry["item_name"]),
                    boss_name=str(boss["name"]),
                    portal_name=str(boss["portal_name"]),
                    difficulty=str(boss["difficulty"]),
                    drop_type=str(entry["drop_type"]),
                    probability=entry["probability"],
                    raw_probability=str(entry["raw_probability"]),
                    tier=entry["tier"],
                    item_type=str(entry["item_type"]),
                    source_file=source_file,
                    source_context=str(entry["source_context"]),
                    evidence=[
                        f"boss:{boss['name']}",
                        f"portal:{boss['portal_name']}",
                        f"source:{source_file}",
                    ],
                )
            )

        return drops

    def _extract_raw_loot_entries(self, block: str) -> list[dict[str, object]]:
        entries: list[dict[str, object]] = []
        clean_block = self._remove_commented_lines(block)

        for match in re.finditer(
            r'new\s+ItemLoot\("([^"]+)"\s*,\s*([^)]+?)\)',
            clean_block,
        ):
            raw_probability = match.group(2).strip()
            entries.append({
                "item_name": match.group(1),
                "drop_type": "item",
                "raw_probability": raw_probability,
                "probability": self._parse_probability(raw_probability),
                "tier": None,
                "item_type": "",
                "source_context": self._nearest_context(clean_block, match.start()),
            })

        for match in re.finditer(
            r'new\s+TierLoot\((\d+)\s*,\s*ItemType\.([A-Za-z]+)\s*,\s*([^)]+?)\)',
            clean_block,
        ):
            tier = int(match.group(1))
            item_type = match.group(2)
            raw_probability = match.group(3).strip()
            entries.append({
                "item_name": f"T{tier} {item_type}",
                "drop_type": "tier",
                "raw_probability": raw_probability,
                "probability": self._parse_probability(raw_probability),
                "tier": tier,
                "item_type": item_type,
                "source_context": self._nearest_context(clean_block, match.start()),
            })

        return entries

    def _extract_template_entries(
        self,
        block: str,
        loot_templates: dict[str, list[dict[str, object]]],
    ) -> list[dict[str, object]]:
        entries = []
        for template_name in re.findall(r'LootTemplates\.(\w+)\s*\(\)', block):
            for entry in loot_templates.get(template_name, []):
                copied = dict(entry)
                copied["source_context"] = f"LootTemplates.{template_name}()"
                entries.append(copied)

        return entries

    def _remove_commented_lines(self, block: str) -> str:
        lines = []
        for line in block.splitlines():
            if line.strip().startswith("//"):
                continue
            lines.append(line)

        return "\n".join(lines)

    def _nearest_context(self, block: str, position: int) -> str:
        prefix = block[:position]
        matches = list(re.finditer(r'new\s+(Threshold|MostDamagers|OnlyOne)\s*\(([^,\n)]*)', prefix))
        if not matches:
            return "direct"

        last = matches[-1]
        context_type = last.group(1)
        context_value = last.group(2).strip()
        if context_value:
            return f"{context_type}({context_value})"

        return context_type

    def _parse_probability(self, raw_value: str) -> float | None:
        value = raw_value.strip().rstrip(",").replace("f", "").replace("d", "")

        fraction = re.fullmatch(r'([0-9.]+)\s*/\s*([0-9.]+)', value)
        if fraction is not None:
            denominator = float(fraction.group(2))
            if denominator == 0:
                return None

            return float(fraction.group(1)) / denominator

        decimal = re.fullmatch(r'[0-9.]+', value)
        if decimal is not None:
            return float(value)

        return None

    def _slugify(self, value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
        return slug or "loot"
