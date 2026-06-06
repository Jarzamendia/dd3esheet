import os
import sqlite3
import sys
import tempfile
import time
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cut_sprite_asset as cut


class CutSpriteAssetTests(unittest.TestCase):
    def test_parse_asset_specs_accepts_slug_equals_path(self):
        parsed = cut.parse_asset_specs(["wolf=C:/tmp/wolf.png", "bear=relative.png"])

        self.assertEqual(parsed[0][0], "wolf")
        self.assertEqual(parsed[0][1], Path("C:/tmp/wolf.png"))
        self.assertEqual(parsed[1], ("bear", Path("relative.png")))

    def test_select_latest_sources_returns_latest_in_oldest_to_newest_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = []
            for index in range(4):
                path = root / f"image-{index}.png"
                path.write_bytes(b"x")
                stamp = time.time() + index
                os.utime(path, (stamp, stamp))
                paths.append(path)

            selected = cut.select_latest_sources(root, 3)

            self.assertEqual(selected, paths[1:])

    def test_cut_chroma_to_alpha_makes_background_transparent(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.png"
            output = Path(tmp) / "out.png"
            image = Image.new("RGBA", (8, 8), (0, 255, 0, 255))
            for x in range(3, 5):
                for y in range(3, 5):
                    image.putpixel((x, y), (150, 20, 20, 255))
            image.save(source)

            result = cut.cut_chroma_to_alpha(source, output)
            out = Image.open(output).convert("RGBA")

            self.assertEqual(result.key_color, (0, 255, 0))
            self.assertEqual(out.getpixel((0, 0))[3], 0)
            self.assertEqual(out.getpixel((4, 4))[3], 255)

    def test_update_sprite_asset_updates_existing_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "db.sqlite3"
            conn = sqlite3.connect(db)
            try:
                conn.execute(
                    "create table sprites_spriteasset "
                    "(Slug text primary key, OriginalImage text, Width integer, Height integer)"
                )
                conn.execute(
                    "insert into sprites_spriteasset values "
                    "('wolf', '', 0, 0)"
                )
                conn.commit()
            finally:
                conn.close()

            updated = cut.update_sprite_asset(
                db,
                "wolf",
                "sprites/original/map_token/wolf.png",
                512,
                512,
            )

            conn = sqlite3.connect(db)
            try:
                row = conn.execute(
                    "select OriginalImage, Width, Height from sprites_spriteasset where Slug='wolf'"
                ).fetchone()
            finally:
                conn.close()

            self.assertEqual(updated, 1)
            self.assertEqual(row, ("sprites/original/map_token/wolf.png", 512, 512))


if __name__ == "__main__":
    unittest.main()
