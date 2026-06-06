r"""Fill tabletop terrain tiles edge-to-edge.

The map tabletop clips terrain sprites into pointy-top hexes. Existing floor
tiles were generated as loose pieces with transparent margins and shadows, which
leaves light/dark gaps at the hex vertices. This script crops the opaque center
of each tile source and resizes it back to a fully opaque square.

Examples from the repo root:

  python scripts/fill_terrain_tile.py --overwrite

  python scripts/fill_terrain_tile.py --overwrite dungeon_floor_tile cave_floor_tile
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    from PIL import Image, ImageFilter
except ImportError as exc:  # pragma: no cover - exercised manually.
    raise SystemExit("Pillow is required. Install it with: python -m pip install pillow") from exc

import cut_sprite_asset as cut


FLOOR_TERRAIN_SLUGS = (
    "dungeon_floor_tile",
    "cave_floor_tile",
    "dungeon_rubble_floor",
    "grass_field_tile",
    "deep_water_tile",
    "shallow_water_tile",
)
ADDITIONAL_FULL_BLEED_TERRAIN_SLUGS = (
    "river_segment",
    "water_shore_edge",
    "dense_woods_patch",
    "dirt_road_straight",
    "rocky_ground_patch",
    "swamp_muck_tile",
    "lava_flow_segment",
    "cobblestone_street",
)
SCENE_TERRAIN_SLUGS = (
    "blacksmith_workshop",
    "bridge_over_chasm",
    "building_wall_segment",
    "cave_entrance",
    "cave_network_map",
    "cavern_lake",
    "crypt_chamber",
    "desert_ruins",
    "dungeon_crossroads",
    "dungeon_level_map",
    "dungeon_prison_block",
    "dungeon_trap_hall",
    "forest_clearing",
    "forest_road_ambush",
    "frontier_valley_map",
    "graveyard_night",
    "inn_guest_rooms",
    "island_campaign_map",
    "kingdom_overland_map",
    "mushroom_cavern",
    "planar_crossroads_map",
    "port_city_map",
    "regional_overland_map",
    "river_ford",
    "sewer_crossing",
    "ship_deck",
    "snowy_pass",
    "stone_dungeon_room",
    "swamp_boardwalk",
    "tavern_ground_floor",
    "temple_sanctum",
    "throne_room",
    "village_map",
    "village_street_market",
    "walled_city_map",
    "wizard_laboratory",
)
DEFAULT_SLUGS = FLOOR_TERRAIN_SLUGS + ADDITIONAL_FULL_BLEED_TERRAIN_SLUGS + SCENE_TERRAIN_SLUGS
DEFAULT_TILE_SUBDIR = Path("sprites/original/map_tile")


@dataclass(frozen=True)
class FillResult:
    slug: str
    source: Path
    output: Path
    mask_bbox: tuple[int, int, int, int]
    crop_box: tuple[int, int, int, int]
    width: int
    height: int
    min_alpha: int
    max_alpha: int
    seamless: bool
    db_updated: bool


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def image_data(image: Image.Image):
    return image.get_flattened_data() if hasattr(image, "get_flattened_data") else image.getdata()


def is_green_chroma_key(color: tuple[int, int, int]) -> bool:
    red, green, blue = color
    return green >= 180 and green - max(red, blue) >= 80


def source_path_for_slug(media_root: Path, tile_subdir: Path, slug: str) -> Path:
    output_dir = media_root / tile_subdir
    full_bleed_source = output_dir / f"{slug}-fullbleed-source.png"
    if full_bleed_source.exists():
        return full_bleed_source
    source = output_dir / f"{slug}-source.png"
    if source.exists():
        return source
    return output_dir / f"{slug}.png"


def mask_from_chroma(
    image: Image.Image,
    *,
    mask_alpha_threshold: int,
    transparent_threshold: int,
    opaque_threshold: int,
) -> tuple[Image.Image, tuple[int, int, int]]:
    rgba = image.convert("RGBA")
    key = cut.infer_key_color(rgba)
    values: list[int] = []

    for red, green, blue, original_alpha in image_data(rgba):
        distance = cut.color_distance((red, green, blue), key)
        alpha = cut.alpha_for_distance(distance, transparent_threshold, opaque_threshold)
        alpha = min(alpha, original_alpha)
        values.append(255 if alpha >= mask_alpha_threshold else 0)

    mask = Image.new("L", rgba.size)
    mask.putdata(values)
    return mask, key


def mask_from_alpha(image: Image.Image, *, mask_alpha_threshold: int) -> Image.Image:
    alpha = image.convert("RGBA").getchannel("A")
    mask = Image.new("L", alpha.size)
    mask.putdata([255 if value >= mask_alpha_threshold else 0 for value in image_data(alpha)])
    return mask


def opaque_region_mask(
    image: Image.Image,
    *,
    mask_alpha_threshold: int,
    transparent_threshold: int,
    opaque_threshold: int,
) -> Image.Image:
    rgba = image.convert("RGBA")
    min_alpha, _max_alpha = rgba.getchannel("A").getextrema()

    if min_alpha < 255:
        return mask_from_alpha(rgba, mask_alpha_threshold=mask_alpha_threshold)

    key = cut.infer_key_color(rgba)
    if is_green_chroma_key(key):
        mask, _key = mask_from_chroma(
            rgba,
            mask_alpha_threshold=mask_alpha_threshold,
            transparent_threshold=transparent_threshold,
            opaque_threshold=opaque_threshold,
        )
        return mask

    return Image.new("L", rgba.size, 255)


def erode_mask(mask: Image.Image, pixels: int) -> Image.Image:
    if pixels <= 0:
        return mask
    return mask.filter(ImageFilter.MinFilter(pixels * 2 + 1))


def square_is_filled(mask: Image.Image, box: tuple[int, int, int, int]) -> bool:
    left, top, right, bottom = box
    if left < 0 or top < 0 or right > mask.width or bottom > mask.height:
        return False
    return mask.crop(box).getextrema() == (255, 255)


def largest_centered_square(mask: Image.Image) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int]]:
    bbox = mask.getbbox()
    if bbox is None:
        raise ValueError("could not find an opaque terrain region")

    center_x = (bbox[0] + bbox[2]) // 2
    center_y = (bbox[1] + bbox[3]) // 2
    low = 1
    high = min(mask.size)
    best: tuple[int, int, int, int] | None = None

    while low <= high:
        side = (low + high) // 2
        left = center_x - side // 2
        top = center_y - side // 2
        box = (left, top, left + side, top + side)
        if square_is_filled(mask, box):
            best = box
            low = side + 1
        else:
            high = side - 1

    if best is None:
        raise ValueError("could not find a centered square inside the opaque terrain region")
    return bbox, best


def force_opaque(image: Image.Image) -> Image.Image:
    rgb = image.convert("RGB")
    return Image.merge("RGBA", (*rgb.split(), Image.new("L", rgb.size, 255)))


def make_full_bleed_tile(
    source: Path,
    *,
    size: int,
    erosion: int,
    mask_alpha_threshold: int,
    transparent_threshold: int,
    opaque_threshold: int,
) -> tuple[Image.Image, tuple[int, int, int, int], tuple[int, int, int, int]]:
    if not source.exists():
        raise FileNotFoundError(source)

    image = Image.open(source).convert("RGBA")
    mask = opaque_region_mask(
        image,
        mask_alpha_threshold=mask_alpha_threshold,
        transparent_threshold=transparent_threshold,
        opaque_threshold=opaque_threshold,
    )
    mask = erode_mask(mask, erosion)
    mask_bbox, crop_box = largest_centered_square(mask)
    resampling = getattr(Image, "Resampling", Image).LANCZOS
    cropped = image.crop(crop_box).resize((size, size), resampling)
    return force_opaque(cropped), mask_bbox, crop_box


def process_slug(
    slug: str,
    *,
    media_root: Path,
    tile_subdir: Path,
    db_path: Path | None,
    overwrite: bool,
    size: int,
    erosion: int,
    mask_alpha_threshold: int,
    transparent_threshold: int,
    opaque_threshold: int,
) -> FillResult:
    output_dir = media_root / tile_subdir
    output = output_dir / f"{slug}.png"
    source = source_path_for_slug(media_root, tile_subdir, slug)
    if output.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing file: {output}")

    previous_size: tuple[int, int] | None = None
    if output.exists():
        with Image.open(output) as existing:
            previous_size = existing.size

    filled, mask_bbox, crop_box = make_full_bleed_tile(
        source,
        size=size,
        erosion=erosion,
        mask_alpha_threshold=mask_alpha_threshold,
        transparent_threshold=transparent_threshold,
        opaque_threshold=opaque_threshold,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    filled.save(output)
    min_alpha, max_alpha = filled.getchannel("A").getextrema()
    db_updated = False

    if db_path is not None and (previous_size is None or previous_size != filled.size):
        rel_path = cut.sprite_media_path(slug, tile_subdir)
        db_updated = cut.update_sprite_asset(db_path, slug, rel_path, filled.width, filled.height) > 0

    return FillResult(
        slug=slug,
        source=source,
        output=output,
        mask_bbox=mask_bbox,
        crop_box=crop_box,
        width=filled.width,
        height=filled.height,
        min_alpha=min_alpha,
        max_alpha=max_alpha,
        seamless=False,
        db_updated=db_updated,
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("slugs", nargs="*", default=list(DEFAULT_SLUGS), help="Terrain floor tile slugs.")
    parser.add_argument("--media-root", type=Path, default=root / "dd3esheet" / "media")
    parser.add_argument("--tile-subdir", type=Path, default=DEFAULT_TILE_SUBDIR)
    parser.add_argument("--db", type=Path, default=root / "dd3esheet" / "db.sqlite3")
    parser.add_argument("--no-db", action="store_true", help="Do not update db.sqlite3 if dimensions change.")
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing existing slug.png files.")
    parser.add_argument("--size", type=int, default=512, help="Output square size in pixels.")
    parser.add_argument("--erosion", type=int, default=8, help="Pixels to erode inward from the opaque mask.")
    parser.add_argument("--mask-alpha-threshold", type=int, default=180)
    parser.add_argument("--transparent-threshold", type=int, default=12)
    parser.add_argument("--opaque-threshold", type=int, default=220)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        db_path = None if args.no_db else args.db
        for slug in args.slugs:
            result = process_slug(
                slug,
                media_root=args.media_root,
                tile_subdir=args.tile_subdir,
                db_path=db_path,
                overwrite=args.overwrite,
                size=args.size,
                erosion=args.erosion,
                mask_alpha_threshold=args.mask_alpha_threshold,
                transparent_threshold=args.transparent_threshold,
                opaque_threshold=args.opaque_threshold,
            )
            print(
                f"{result.slug}: {result.width}x{result.height} "
                f"alpha={result.min_alpha}-{result.max_alpha} "
                f"crop={result.crop_box} mask={result.mask_bbox} "
                f"seamless={'yes' if result.seamless else 'no'} "
                f"db_updated={'yes' if result.db_updated else 'no'}"
            )
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
