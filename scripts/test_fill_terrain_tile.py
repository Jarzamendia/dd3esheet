import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fill_terrain_tile as fill
import generate_terrain_tile_sources as generate


class FillTerrainTileTests(unittest.TestCase):
    def test_source_path_prefers_full_bleed_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            media_root = Path(tmp)
            tile_dir = media_root / fill.DEFAULT_TILE_SUBDIR
            tile_dir.mkdir(parents=True)
            legacy = tile_dir / "river_segment-source.png"
            full_bleed = tile_dir / "river_segment-fullbleed-source.png"
            legacy.write_bytes(b"legacy")
            full_bleed.write_bytes(b"full")

            self.assertEqual(
                fill.source_path_for_slug(media_root, fill.DEFAULT_TILE_SUBDIR, "river_segment"),
                full_bleed,
            )

    def test_make_full_bleed_tile_forces_opaque_alpha(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.png"
            image = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
            for x in range(2, 6):
                for y in range(2, 6):
                    image.putpixel((x, y), (120, 100, 80, 200))
            image.save(source)

            out, _mask_bbox, crop_box = fill.make_full_bleed_tile(
                source,
                size=16,
                erosion=0,
                mask_alpha_threshold=180,
                transparent_threshold=12,
                opaque_threshold=220,
            )

            self.assertEqual(out.size, (16, 16))
            self.assertEqual(out.getchannel("A").getextrema(), (255, 255))
            self.assertEqual(crop_box, (2, 2, 6, 6))

    def test_process_slug_updates_db_for_new_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            media_root = root / "media"
            tile_dir = media_root / fill.DEFAULT_TILE_SUBDIR
            tile_dir.mkdir(parents=True)
            Image.new("RGBA", (16, 16), (100, 80, 60, 255)).save(
                tile_dir / "rocky_ground_patch-fullbleed-source.png"
            )

            db = root / "db.sqlite3"
            conn = sqlite3.connect(db)
            try:
                conn.execute(
                    "create table sprites_spriteasset "
                    "(Slug text primary key, OriginalImage text, Width integer, Height integer)"
                )
                conn.execute(
                    "insert into sprites_spriteasset values ('rocky_ground_patch', '', 0, 0)"
                )
                conn.commit()
            finally:
                conn.close()

            result = fill.process_slug(
                "rocky_ground_patch",
                media_root=media_root,
                tile_subdir=fill.DEFAULT_TILE_SUBDIR,
                db_path=db,
                overwrite=True,
                size=16,
                erosion=0,
                mask_alpha_threshold=180,
                transparent_threshold=12,
                opaque_threshold=220,
            )

            conn = sqlite3.connect(db)
            try:
                row = conn.execute(
                    "select OriginalImage, Width, Height from sprites_spriteasset "
                    "where Slug='rocky_ground_patch'"
                ).fetchone()
            finally:
                conn.close()

            self.assertTrue(result.db_updated)
            self.assertEqual(row, ("sprites/original/map_tile/rocky_ground_patch.png", 16, 16))


class GenerateTerrainTileSourceTests(unittest.TestCase):
    def test_generate_source_is_opaque_square(self):
        image = generate.generate_source("blacksmith_workshop", size=512)

        self.assertEqual(image.size, (512, 512))
        self.assertEqual(image.getchannel("A").getextrema(), (255, 255))

    def test_default_generated_slugs_have_generators_and_fill_entries(self):
        generated = set(generate.DEFAULT_SLUGS)

        self.assertTrue(generated.issubset(set(generate.GENERATORS)))
        self.assertTrue(set(generate.CURATED_IMAGEGEN_SLUGS).issubset(set(generate.GENERATORS)))
        self.assertTrue(set(generate.CURATED_IMAGEGEN_SLUGS).isdisjoint(generated))
        self.assertTrue(generated.issubset(set(fill.DEFAULT_SLUGS)))

    def test_process_slug_refuses_curated_imagegen_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                generate.process_slug(
                    "river_segment",
                    output_dir=Path(tmp),
                    size=128,
                    overwrite=True,
                )


if __name__ == "__main__":
    unittest.main()
