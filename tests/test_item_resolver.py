import json
import tempfile
import unittest
from pathlib import Path

from services.item_resolver import ItemResolver


class ItemResolverTest(unittest.TestCase):
    def test_resolve_named_item_drops_from_xml_definitions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            xml_dir = source / "server" / "common" / "resources" / "xmls"
            database = root / "workspace" / "database"

            xml_dir.mkdir(parents=True)
            (database / "loot").mkdir(parents=True)

            (database / "loot" / "loot.json").write_text(
                json.dumps({
                    "total": 3,
                    "portals": {
                        "OVERWORLD": {
                            "Pillager": [
                                {
                                    "item_name": "Pillager Head",
                                    "boss_name": "Pillager",
                                    "portal_name": "OVERWORLD",
                                    "difficulty": "earlygame",
                                    "drop_type": "item",
                                    "probability": 1 / 30,
                                    "raw_probability": "1 / 30f",
                                    "source_context": "Threshold(0.0001)",
                                    "source_file": "BehaviorDb.Events.cs",
                                },
                                {
                                    "item_name": "Missing Item",
                                    "boss_name": "Pillager",
                                    "portal_name": "OVERWORLD",
                                    "difficulty": "earlygame",
                                    "drop_type": "item",
                                    "probability": 0.5,
                                    "raw_probability": "0.5",
                                    "source_context": "Threshold(0.0001)",
                                    "source_file": "BehaviorDb.Events.cs",
                                },
                                {
                                    "item_name": "T12 Weapon",
                                    "boss_name": "Pillager",
                                    "portal_name": "OVERWORLD",
                                    "difficulty": "earlygame",
                                    "drop_type": "tier",
                                    "tier": 12,
                                    "item_type": "Weapon",
                                },
                            ],
                        },
                    },
                }),
                encoding="utf8",
            )

            (xml_dir / "items.xml").write_text(
                """<?xml version="1.0" encoding="utf-8"?>
<Objects>
    <Object type="0x8ca5" id="Pillager Head">
        <Class>Equipment</Class>
        <Item />
        <Texture>
            <File>MinecraftItems</File>
            <Index>0x00</Index>
        </Texture>
        <SlotType>10</SlotType>
        <Description>A trophy head dropped by Pillager.</Description>
        <NoLootBoost />
        <BagType>11</BagType>
        <feedPower>750</feedPower>
        <DisplayId>Pillager Head</DisplayId>
    </Object>
</Objects>
""",
                encoding="utf8",
            )

            resolver = ItemResolver(
                source_path=source,
                loot_path=database / "loot" / "loot.json",
                output_dir=database / "items",
            )

            items = resolver.resolve()
            resolver.save()

            self.assertEqual(1, len(items))
            self.assertEqual("Pillager Head", items[0].name)
            self.assertEqual("0x8ca5", items[0].object_type)
            self.assertEqual(10, items[0].slot_type)
            self.assertEqual(11, items[0].bag_type)
            self.assertTrue(items[0].no_loot_boost)
            self.assertEqual(1, len(items[0].dropped_by))
            self.assertEqual(1, len(resolver.unresolved))
            self.assertEqual("Missing Item", resolver.unresolved[0]["item_name"])

            summary = json.loads(
                (database / "items" / "items.json").read_text(encoding="utf8")
            )
            self.assertEqual(1, summary["total"])
            self.assertEqual(1, summary["unresolved_total"])
            self.assertTrue((database / "items" / "pillager-head.json").exists())


if __name__ == "__main__":
    unittest.main()
