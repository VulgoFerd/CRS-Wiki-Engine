import json
import tempfile
import unittest
from pathlib import Path

from services.loot_resolver import LootResolver


class LootResolverTest(unittest.TestCase):
    def test_resolve_item_tier_and_template_loot_from_behavior_block(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            behavior_dir = source / "server" / "wServer" / "logic" / "db"
            loot_dir = source / "server" / "wServer" / "logic" / "loot"
            database = root / "workspace" / "database"

            behavior_dir.mkdir(parents=True)
            loot_dir.mkdir(parents=True)
            (database / "bosses").mkdir(parents=True)

            (database / "bosses" / "bosses.json").write_text(
                json.dumps({
                    "total": 1,
                    "portals": {
                        "OVERWORLD": [{
                            "name": "Pillager",
                            "portal_name": "OVERWORLD",
                            "difficulty": "earlygame",
                        }],
                    },
                }),
                encoding="utf8",
            )

            (behavior_dir / "BehaviorDb.Events.cs").write_text(
                '''
                .Init("Pillager",
                    new State(),
                    new MostDamagers(1,
                        LootTemplates.StatPots()
                    ),
                    new Threshold(0.0001,
                        new ItemLoot("Pillager Head", 1 / 30f),
                        new TierLoot(12, ItemType.Weapon, 0.05)
                    )
                )
                .Init("Other Boss",
                    new State(),
                    new Threshold(0.1,
                        new ItemLoot("Ignored Item", 1)
                    )
                )
                ''',
                encoding="utf8",
            )

            (loot_dir / "LootDefs.cs").write_text(
                '''
                public static class LootTemplates
                {
                    public static ILootDef[] StatPots()
                    {
                        return new ILootDef[]
                        {
                            new ItemLoot("Potion of Defense", 1),
                            new ItemLoot("Potion of Attack", 1)
                        };
                    }
                }
                ''',
                encoding="utf8",
            )

            resolver = LootResolver(
                source_path=source,
                bosses_path=database / "bosses" / "bosses.json",
                output_dir=database / "loot",
            )

            drops = resolver.resolve()
            resolver.save()

            names = [drop.item_name for drop in drops]
            self.assertEqual([
                "Pillager Head",
                "T12 Weapon",
                "Potion of Defense",
                "Potion of Attack",
            ], names)
            self.assertAlmostEqual(1 / 30, drops[0].probability)
            self.assertEqual("1 / 30f", drops[0].raw_probability)
            self.assertEqual(12, drops[1].tier)
            self.assertEqual("Weapon", drops[1].item_type)
            self.assertEqual("LootTemplates.StatPots()", drops[2].source_context)

            summary = json.loads(
                (database / "loot" / "loot.json").read_text(encoding="utf8")
            )
            self.assertEqual(4, summary["total"])
            self.assertTrue(
                (database / "loot" / "overworld" / "pillager.json").exists()
            )


if __name__ == "__main__":
    unittest.main()
