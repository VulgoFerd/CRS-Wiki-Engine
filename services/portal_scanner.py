from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from models.portal import Portal


class PortalScanner:
    """Discover whitelisted portals from indexed XML files."""

    def __init__(
        self,
        source_path: Path,
        manifest_portals: list[Portal],
        xml_index_path: Path = Path("workspace/reports/xml_index.json"),
        output_dir: Path = Path("workspace/database/portals"),
    ) -> None:
        self.source_path = source_path
        self.manifest_portals = manifest_portals
        self.xml_index_path = xml_index_path
        self.output_dir = output_dir
        self.discovered: list[Portal] = []

    def scan(self) -> list[Portal]:
        """Scan source XML files with portal tags and return whitelist matches."""

        self._validate_inputs()
        candidates = self._load_candidate_xml_paths()
        all_portals = self._extract_portals(candidates)
        self.discovered = self._match_whitelist(all_portals)
        return self.discovered

    def save(self) -> None:
        """Persist portal scan results under the workspace database directory."""

        self.output_dir.mkdir(parents=True, exist_ok=True)

        summary = {
            "total": len(self.discovered),
            "portals": [portal.to_dict() for portal in self.discovered],
        }

        summary_path = self.output_dir / "portals.json"
        with summary_path.open("w", encoding="utf8") as file:
            json.dump(summary, file, indent=4, ensure_ascii=False)

        for portal in self.discovered:
            portal_path = self.output_dir / f"{self._slugify(portal.name)}.json"
            with portal_path.open("w", encoding="utf8") as file:
                json.dump(portal.to_dict(), file, indent=4, ensure_ascii=False)

    def _validate_inputs(self) -> None:
        if not self.source_path.exists():
            raise FileNotFoundError(f"Source path not found: {self.source_path}")

        if not self.xml_index_path.exists():
            raise FileNotFoundError(f"XML index not found: {self.xml_index_path}")

    def _load_candidate_xml_paths(self) -> list[Path]:
        with self.xml_index_path.open("r", encoding="utf8") as file:
            xml_index: dict[str, dict[str, int]] = json.load(file)

        candidates = []
        for relative_path, tags in xml_index.items():
            if tags.get("IntergamePortal", 0) > 0 or tags.get("DungeonName", 0) > 0:
                candidates.append(self.source_path / relative_path)

        return sorted(candidates)

    def _extract_portals(self, paths: list[Path]) -> list[Portal]:
        portals = []

        for path in paths:
            if not path.exists():
                continue

            root = ET.parse(path).getroot()
            for node in root.iter():
                if self._local_name(node.tag) != "Object":
                    continue

                if self._text(node, "Class") != "Portal":
                    continue

                if node.find("IntergamePortal") is None:
                    continue

                portals.append(self._portal_from_node(node, path))

        return portals

    def _portal_from_node(self, node: ET.Element, source_file: Path) -> Portal:
        texture = node.find("Texture")
        texture_file = self._text(texture, "File") if texture is not None else ""
        texture_index = self._text(texture, "Index") if texture is not None else ""

        return Portal(
            name=node.attrib.get("id", ""),
            difficulty="",
            object_id=node.attrib.get("id", ""),
            object_type=node.attrib.get("type", ""),
            dungeon_name=self._text(node, "DungeonName"),
            display_id=self._text(node, "DisplayId"),
            texture_file=texture_file,
            texture_index=texture_index,
            source_files=[source_file.relative_to(self.source_path).as_posix()],
        )

    def _match_whitelist(self, all_portals: list[Portal]) -> list[Portal]:
        discovered = []

        for manifest_portal in self.manifest_portals:
            matches = [
                portal for portal in all_portals
                if self._matches(manifest_portal.name, portal)
            ]

            if not matches:
                continue

            discovered.append(
                self._merge_matches(manifest_portal, matches)
            )

        return discovered

    def _merge_matches(self, manifest_portal: Portal, matches: list[Portal]) -> Portal:
        primary = matches[0]
        source_files = sorted({
            source_file
            for match in matches
            for source_file in match.source_files
        })

        return Portal(
            name=manifest_portal.name,
            difficulty=manifest_portal.difficulty,
            enabled=manifest_portal.enabled,
            object_id=primary.object_id,
            object_type=primary.object_type,
            dungeon_name=primary.dungeon_name,
            display_id=primary.display_id,
            texture_file=primary.texture_file,
            texture_index=primary.texture_index,
            source_files=source_files,
        )

    def _matches(self, requested_name: str, portal: Portal) -> bool:
        requested = self._normalize(requested_name)
        candidates = [
            portal.object_id,
            portal.display_id,
            portal.dungeon_name,
            portal.name,
        ]

        return requested in {self._normalize(candidate) for candidate in candidates}

    def _text(self, node: ET.Element | None, tag: str) -> str:
        if node is None:
            return ""

        child = node.find(tag)
        if child is None or child.text is None:
            return ""

        return child.text.strip()

    def _local_name(self, tag: str) -> str:
        return tag.rsplit("}", 1)[-1]

    def _normalize(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", value.casefold())

    def _slugify(self, value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
        return slug or "portal"
