from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from models.boss import Boss


class BossResolver:
    """Resolve boss candidates reachable from whitelisted portal maps."""

    def __init__(
        self,
        source_path: Path,
        portals_path: Path = Path("workspace/database/portals/portals.json"),
        output_dir: Path = Path("workspace/database/bosses"),
    ) -> None:
        self.source_path = source_path
        self.portals_path = portals_path
        self.output_dir = output_dir
        self.resolved: list[Boss] = []

    def resolve(self) -> list[Boss]:
        """Resolve bosses from portal worlds and behavior spawner logic."""

        self._validate_inputs()
        portals = self._load_portals()
        worlds = self._load_worlds()
        behavior_index = self._load_behavior_index()
        object_index = self._load_object_index()

        bosses: list[Boss] = []
        seen: set[tuple[str, str]] = set()

        for portal in portals:
            world = worlds.get(self._normalize(portal["dungeon_name"]))
            if world is None:
                continue

            map_objects = self._load_map_objects(world)
            for map_object in map_objects:
                boss_names = self._resolve_map_object_boss_names(
                    map_object,
                    behavior_index,
                    object_index,
                )

                for boss_name in boss_names:
                    key = (portal["name"], self._normalize(boss_name))
                    if key in seen:
                        continue

                    seen.add(key)
                    bosses.append(
                        self._build_boss(
                            boss_name=boss_name,
                            portal=portal,
                            map_object=map_object,
                            world=world,
                            object_index=object_index,
                            behavior_index=behavior_index,
                        )
                    )

        self.resolved = bosses
        return self.resolved

    def save(self) -> None:
        """Persist resolved bosses under the workspace database directory."""

        self.output_dir.mkdir(parents=True, exist_ok=True)

        by_portal: dict[str, list[dict[str, object]]] = {}
        for boss in self.resolved:
            by_portal.setdefault(boss.portal_name, []).append(boss.to_dict())

        summary = {
            "total": len(self.resolved),
            "portals": by_portal,
        }

        with (self.output_dir / "bosses.json").open("w", encoding="utf8") as file:
            json.dump(summary, file, indent=4, ensure_ascii=False)

        for portal_name, bosses in by_portal.items():
            portal_dir = self.output_dir / self._slugify(portal_name)
            portal_dir.mkdir(parents=True, exist_ok=True)

            with (portal_dir / "bosses.json").open("w", encoding="utf8") as file:
                json.dump(
                    {"total": len(bosses), "bosses": bosses},
                    file,
                    indent=4,
                    ensure_ascii=False,
                )

            for boss in bosses:
                with (
                    portal_dir / f"{self._slugify(str(boss['name']))}.json"
                ).open("w", encoding="utf8") as file:
                    json.dump(boss, file, indent=4, ensure_ascii=False)

    def _validate_inputs(self) -> None:
        if not self.source_path.exists():
            raise FileNotFoundError(f"Source path not found: {self.source_path}")

        if not self.portals_path.exists():
            raise FileNotFoundError(f"Portals database not found: {self.portals_path}")

    def _load_portals(self) -> list[dict[str, str]]:
        with self.portals_path.open("r", encoding="utf8") as file:
            data = json.load(file)

        return [
            portal for portal in data.get("portals", [])
            if portal.get("enabled", True)
        ]

    def _load_worlds(self) -> dict[str, dict[str, object]]:
        worlds: dict[str, dict[str, object]] = {}

        for path in self.source_path.rglob("*.jw"):
            raw = path.read_text(encoding="utf8", errors="ignore")
            name_match = re.search(r'"name"\s*:\s*"([^"]+)"', raw)
            if name_match is None:
                continue

            maps_match = re.search(r'"maps"\s*:\s*\[(.*?)\]', raw, re.DOTALL)
            maps = re.findall(r'"([^"]+\.(?:jm|wmap))"', maps_match.group(1)) if maps_match else []

            world = {
                "name": name_match.group(1),
                "maps": maps,
                "source_file": path.relative_to(self.source_path).as_posix(),
                "directory": path.parent,
            }
            worlds[self._normalize(str(world["name"]))] = world

        return worlds

    def _load_map_objects(self, world: dict[str, object]) -> list[dict[str, str]]:
        objects: list[dict[str, str]] = []
        directory = world["directory"]
        if not isinstance(directory, Path):
            return objects

        for map_name in world["maps"]:
            map_path = directory / str(map_name)
            if map_path.suffix.lower() != ".jm" or not map_path.exists():
                continue

            with map_path.open("r", encoding="utf8") as file:
                map_data = json.load(file)

            for entry in map_data.get("dict", []):
                for obj in entry.get("objs", []):
                    object_id = obj.get("id", "")
                    if object_id:
                        objects.append({
                            "id": object_id,
                            "map": map_path.relative_to(self.source_path).as_posix(),
                        })

        return objects

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
                    "spawns": sorted(set(re.findall(r'new\s+Spawn\("([^"]+)"', block))),
                }

        return behavior_index

    def _load_object_index(self) -> dict[str, dict[str, object]]:
        object_index: dict[str, dict[str, object]] = {}

        for path in self.source_path.rglob("*.xml"):
            try:
                root = ET.parse(path).getroot()
            except ET.ParseError:
                continue

            for node in root.iter():
                if self._local_name(node.tag) != "Object":
                    continue

                object_id = node.attrib.get("id", "")
                if not object_id:
                    continue

                current = object_index.setdefault(object_id, {
                    "object_id": object_id,
                    "object_type": node.attrib.get("type", ""),
                    "display_id": self._text(node, "DisplayId"),
                    "group": self._text(node, "Group"),
                    "class_name": self._text(node, "Class"),
                    "enemy": node.find("Enemy") is not None,
                    "quest": node.find("Quest") is not None,
                    "texture_file": "",
                    "texture_index": "",
                    "source_files": [],
                })

                texture = node.find("Texture")
                if texture is not None and not current["texture_file"]:
                    current["texture_file"] = self._text(texture, "File")
                    current["texture_index"] = self._text(texture, "Index")

                source_file = path.relative_to(self.source_path).as_posix()
                if source_file not in current["source_files"]:
                    current["source_files"].append(source_file)

        return object_index

    def _resolve_map_object_boss_names(
        self,
        map_object: dict[str, str],
        behavior_index: dict[str, dict[str, object]],
        object_index: dict[str, dict[str, object]],
    ) -> list[str]:
        object_id = map_object["id"]
        behavior = behavior_index.get(object_id)
        if behavior is not None:
            return list(behavior["spawns"])

        obj = object_index.get(object_id)
        if obj is not None and (obj["enemy"] or obj["quest"]):
            return [object_id]

        return []

    def _build_boss(
        self,
        boss_name: str,
        portal: dict[str, str],
        map_object: dict[str, str],
        world: dict[str, object],
        object_index: dict[str, dict[str, object]],
        behavior_index: dict[str, dict[str, object]],
    ) -> Boss:
        source = object_index.get(boss_name, {})
        source_files = set(source.get("source_files", []))
        behavior = behavior_index.get(boss_name)
        if behavior is not None:
            source_files.add(str(behavior["source_file"]))

        spawner_behavior = behavior_index.get(map_object["id"])
        evidence = [
            f"portal:{portal['name']}",
            f"world:{world['name']}",
            f"map:{map_object['map']}",
            f"map_object:{map_object['id']}",
        ]
        if spawner_behavior is not None:
            evidence.append(f"spawner_behavior:{spawner_behavior['source_file']}")
        if behavior is not None:
            evidence.append(f"boss_behavior:{behavior['source_file']}")

        return Boss(
            name=boss_name,
            portal_name=portal["name"],
            difficulty=portal["difficulty"],
            object_id=str(source.get("object_id", boss_name)),
            object_type=str(source.get("object_type", "")),
            display_id=str(source.get("display_id", "")),
            group=str(source.get("group", "")),
            class_name=str(source.get("class_name", "")),
            enemy=bool(source.get("enemy", False)),
            quest=bool(source.get("quest", False)),
            texture_file=str(source.get("texture_file", "")),
            texture_index=str(source.get("texture_index", "")),
            source_files=sorted(source_files),
            evidence=evidence,
        )

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
        return slug or "boss"
