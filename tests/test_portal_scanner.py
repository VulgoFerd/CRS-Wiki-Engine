import json
import tempfile
import unittest
from pathlib import Path

from models.portal import Portal
from services.portal_scanner import PortalScanner


class PortalScannerTest(unittest.TestCase):
    def test_scan_matches_whitelisted_portals_across_source_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            report_dir = root / "reports"
            output_dir = root / "database" / "portals"
            xml_dir = source / "xmls"
            xml_dir.mkdir(parents=True)
            report_dir.mkdir(parents=True)

            first_xml = xml_dir / "portals.xml"
            first_xml.write_text(
                """<?xml version="1.0" encoding="utf-8"?>
<Objects>
    <Object type="0x5b98" id="DA ALVIN ZONE">
        <Class>Portal</Class>
        <IntergamePortal />
        <DungeonName>Minecraft</DungeonName>
        <DisplayId>OVERWORLD</DisplayId>
        <Texture>
            <File>MinecraftOverworldPortal</File>
            <Index>0</Index>
        </Texture>
    </Object>
    <Object type="0x5b99" id="MINNESOTA">
        <Class>Portal</Class>
        <IntergamePortal />
        <DungeonName>Terraria</DungeonName>
        <DisplayId>Terraria</DisplayId>
        <Texture>
            <File>lofiObjSp</File>
            <Index>0x190</Index>
        </Texture>
    </Object>
</Objects>
""",
                encoding="utf8",
            )

            second_xml = xml_dir / "duplicate.xml"
            second_xml.write_text(
                """<?xml version="1.0" encoding="utf-8"?>
<Objects>
    <Object type="0x5b99" id="MINNESOTA">
        <Class>Portal</Class>
        <IntergamePortal />
        <DungeonName>Terraria</DungeonName>
        <DisplayId>Terraria</DisplayId>
        <Texture>
            <File>lofiObjSp</File>
            <Index>0x190</Index>
        </Texture>
    </Object>
</Objects>
""",
                encoding="utf8",
            )

            xml_index = {
                "xmls/portals.xml": {
                    "Object": 2,
                    "IntergamePortal": 2,
                    "DungeonName": 2,
                },
                "xmls/duplicate.xml": {
                    "Object": 1,
                    "IntergamePortal": 1,
                    "DungeonName": 1,
                },
                "xmls/ignored.xml": {
                    "Object": 1,
                },
            }
            index_path = report_dir / "xml_index.json"
            index_path.write_text(json.dumps(xml_index), encoding="utf8")

            scanner = PortalScanner(
                source_path=source,
                manifest_portals=[
                    Portal(name="OVERWORLD", difficulty="earlygame"),
                    Portal(name="Minnesota", difficulty="midgame"),
                    Portal(name="Missing", difficulty="endgame"),
                ],
                xml_index_path=index_path,
                output_dir=output_dir,
            )

            discovered = scanner.scan()
            scanner.save()

            self.assertEqual(["OVERWORLD", "Minnesota"], [
                portal.name for portal in discovered
            ])
            self.assertEqual("Minecraft", discovered[0].dungeon_name)
            self.assertEqual("MINNESOTA", discovered[1].object_id)
            self.assertEqual([
                "xmls/duplicate.xml",
                "xmls/portals.xml",
            ], discovered[1].source_files)

            summary = json.loads(
                (output_dir / "portals.json").read_text(encoding="utf8")
            )
            self.assertEqual(2, summary["total"])
            self.assertTrue((output_dir / "overworld.json").exists())
            self.assertTrue((output_dir / "minnesota.json").exists())


if __name__ == "__main__":
    unittest.main()
