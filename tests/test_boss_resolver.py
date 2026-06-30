import json
import tempfile
import unittest
from pathlib import Path

from services.boss_resolver import BossResolver


class BossResolverTest(unittest.TestCase):
    def test_resolve_bosses_from_portal_world_map_and_spawner_logic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            worlds = source / "server" / "common" / "resources" / "worlds"
            behaviors = source / "server" / "wServer" / "logic" / "db"
            xmls = source / "server" / "common" / "resources" / "xmls"
            database = root / "workspace" / "database"

            worlds.mkdir(parents=True)
            behaviors.mkdir(parents=True)
            xmls.mkdir(parents=True)
            (database / "portals").mkdir(parents=True)

            (database / "portals" / "portals.json").write_text(
                json.dumps({
                    "total": 1,
                    "portals": [{
                        "name": "OVERWORLD",
                        "difficulty": "earlygame",
                        "enabled": True,
                        "dungeon_name": "Minecraft",
                    }],
                }),
                encoding="utf8",
            )

            (worlds / "minecraft.jw").write_text(
                '{"name":"Minecraft","maps":["minecraft.jm"],"portals":[0x5b98]}',
                encoding="utf8",
            )
            (worlds / "minecraft.jm").write_text(
                json.dumps({
                    "dict": [
                        {"objs": [{"id": "Spawner Overword"}]},
                        {"objs": [{"id": "Decorative Tree"}]},
                    ],
                }),
                encoding="utf8",
            )

            (behaviors / "BehaviorDb.Events.cs").write_text(
                '''
                .Init("Spawner Overword",
                    new State(
                        new Spawn("Pillager", 1, 1, 1000000),
                        new Spawn("Creeper", 1, 1, 1000000)
                    )
                )
                .Init("Decorative Tree",
                    new State()
                )
                ''',
                encoding="utf8",
            )

            (xmls / "objects.xml").write_text(
                """<?xml version="1.0" encoding="utf-8"?>
<Objects>
    <Object type="0x1001" id="Pillager">
        <Class>Character</Class>
        <Enemy />
        <Quest />
        <Group>Minecraft Bosses</Group>
        <DisplayId>Pillager Captain</DisplayId>
        <MaxHitPoints>999999</MaxHitPoints>
        <Texture>
            <File>minecraftEnemies</File>
            <Index>0x1</Index>
        </Texture>
    </Object>
    <Object type="0x1002" id="Creeper">
        <Class>Character</Class>
        <Enemy />
        <Texture>
            <File>minecraftEnemies</File>
            <Index>0x2</Index>
        </Texture>
    </Object>
</Objects>
""",
                encoding="utf8",
            )

            resolver = BossResolver(
                source_path=source,
                portals_path=database / "portals" / "portals.json",
                output_dir=database / "bosses",
            )

            bosses = resolver.resolve()
            resolver.save()

            self.assertEqual(["Creeper", "Pillager"], [
                boss.name for boss in bosses
            ])
            self.assertEqual("OVERWORLD", bosses[0].portal_name)
            self.assertTrue(bosses[1].enemy)
            self.assertTrue(bosses[1].quest)
            self.assertEqual("Pillager Captain", bosses[1].display_id)

            boss_data = bosses[1].to_dict()
            self.assertNotIn("max_hit_points", boss_data)
            self.assertNotIn("hp", boss_data)

            summary = json.loads(
                (database / "bosses" / "bosses.json").read_text(encoding="utf8")
            )
            self.assertEqual(2, summary["total"])
            self.assertTrue(
                (database / "bosses" / "overworld" / "pillager.json").exists()
            )


if __name__ == "__main__":
    unittest.main()
