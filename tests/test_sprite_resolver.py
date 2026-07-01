import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from services.sprite_resolver import SpriteResolver


class SpriteResolverTest(unittest.TestCase):
    def test_resolve_item_sprite_from_embedded_asset_alias(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            assets_dir = source / "client" / "src" / "kabam" / "rotmg" / "assets"
            database = root / "workspace" / "database"

            assets_dir.mkdir(parents=True)
            (database / "items").mkdir(parents=True)

            (database / "items" / "items.json").write_text(
                json.dumps({
                    "total": 1,
                    "items": [{
                        "name": "Pillager Head",
                        "texture_file": "MinecraftItems",
                        "texture_index": "0x03",
                        "source_files": ["items.xml"],
                    }],
                }),
                encoding="utf8",
            )

            (assets_dir / "EmbeddedAssets.as").write_text(
                """
                public class EmbeddedAssets {
                    public static var MinecraftItemsEmbed_:Class = EmbeddedAssets_MinecraftItemsEmbed_;
                }
                """,
                encoding="utf8",
            )
            (assets_dir / "EmbeddedAssets_MinecraftItemsEmbed_.as").write_text(
                """
                package kabam.rotmg.assets {
                [Embed(source="EmbeddedAssets_MinecraftItemsEmbed_.png")]
                public class EmbeddedAssets_MinecraftItemsEmbed_ extends BitmapAsset {}
                }
                """,
                encoding="utf8",
            )
            self._write_png(assets_dir / "EmbeddedAssets_MinecraftItemsEmbed_.png", 32, 16)

            resolver = SpriteResolver(
                source_path=source,
                items_path=database / "items" / "items.json",
                output_dir=database / "sprites",
            )

            sprites = resolver.resolve()
            resolver.save()

            self.assertEqual(1, len(sprites))
            self.assertEqual("Pillager Head", sprites[0].owner_name)
            self.assertEqual(3, sprites[0].index)
            self.assertEqual(32, sprites[0].atlas_width)
            self.assertEqual(16, sprites[0].atlas_height)
            self.assertEqual(8, sprites[0].tile_width)
            self.assertEqual(24, sprites[0].x)
            self.assertEqual(0, sprites[0].y)

            summary = json.loads(
                (database / "sprites" / "sprites.json").read_text(encoding="utf8")
            )
            self.assertEqual(1, summary["total"])
            self.assertTrue(
                (database / "sprites" / "pillager-head.json").exists()
            )

    def _write_png(self, path: Path, width: int, height: int) -> None:
        raw_scanlines = b"".join(
            b"\x00" + b"\x00\x00\x00\x00" * width
            for _ in range(height)
        )

        def chunk(name: bytes, payload: bytes) -> bytes:
            checksum = zlib.crc32(name + payload) & 0xFFFFFFFF
            return (
                struct.pack(">I", len(payload))
                + name
                + payload
                + struct.pack(">I", checksum)
            )

        png = (
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw_scanlines))
            + chunk(b"IEND", b"")
        )
        path.write_bytes(png)


if __name__ == "__main__":
    unittest.main()
