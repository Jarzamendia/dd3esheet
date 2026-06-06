r"""Cut generated sprite images from a chroma-key background and bind them.

Examples from the repo root:

  python scripts/cut_sprite_asset.py ^
    --asset wolf_companion=C:\path\to\generated.png

  python scripts/cut_sprite_asset.py ^
    --latest 3 ^
    --slugs wolf_companion black_bear_companion brown_bear_companion

The second form maps the oldest file among the latest N generated images to the
first slug, matching the order in which prompts were generated.
"""

from __future__ import annotations

import argparse
import math
import shutil
import sqlite3
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover - exercised manually.
    raise SystemExit("Pillow is required. Install it with: python -m pip install pillow") from exc


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
DEFAULT_OUTPUT_SUBDIR = Path("sprites/original/map_token")


@dataclass(frozen=True)
class CutResult:
    key_color: tuple[int, int, int]
    transparent_pixels: int
    partial_transparent_pixels: int
    total_pixels: int
    width: int
    height: int


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_generated_dir() -> Path:
    return Path.home() / ".codex" / "generated_images"


def parse_asset_specs(values: list[str]) -> list[tuple[str, Path]]:
    pairs: list[tuple[str, Path]] = []
    for value in values:
        if "=" not in value:
            raise ValueError(f"Invalid --asset value {value!r}; use slug=path")
        slug, raw_path = value.split("=", 1)
        slug = slug.strip()
        raw_path = raw_path.strip().strip('"')
        if not slug or not raw_path:
            raise ValueError(f"Invalid --asset value {value!r}; use slug=path")
        pairs.append((slug, Path(raw_path)))
    return pairs


def select_latest_sources(generated_dir: Path, count: int) -> list[Path]:
    if count < 1:
        raise ValueError("--latest must be greater than zero")
    files = [
        path
        for path in generated_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    ]
    if len(files) < count:
        raise ValueError(
            f"Only found {len(files)} image(s) in {generated_dir}, cannot select {count}"
        )
    latest_desc = sorted(files, key=lambda path: path.stat().st_mtime, reverse=True)[:count]
    return sorted(latest_desc, key=lambda path: path.stat().st_mtime)


def border_pixels(image: Image.Image) -> list[tuple[int, int, int]]:
    rgba = image.convert("RGBA")
    width, height = rgba.size
    pixels = rgba.load()
    values: list[tuple[int, int, int]] = []

    for x in range(width):
        values.append(pixels[x, 0][:3])
        values.append(pixels[x, height - 1][:3])
    for y in range(1, height - 1):
        values.append(pixels[0, y][:3])
        values.append(pixels[width - 1, y][:3])
    return values


def infer_key_color(image: Image.Image) -> tuple[int, int, int]:
    return Counter(border_pixels(image)).most_common(1)[0][0]


def color_distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    return math.sqrt(sum((a[index] - b[index]) ** 2 for index in range(3)))


def alpha_for_distance(distance: float, transparent_threshold: int, opaque_threshold: int) -> int:
    if distance <= transparent_threshold:
        return 0
    if distance >= opaque_threshold:
        return 255
    span = max(1, opaque_threshold - transparent_threshold)
    return round(255 * ((distance - transparent_threshold) / span))


def despill_rgb(
    rgb: tuple[int, int, int],
    key_color: tuple[int, int, int],
    alpha: int,
) -> tuple[int, int, int]:
    if alpha >= 255:
        return rgb
    dominant = max(range(3), key=lambda index: key_color[index])
    if key_color[dominant] < 180:
        return rgb

    values = list(rgb)
    other_max = max(values[index] for index in range(3) if index != dominant)
    limit = other_max + 8
    if values[dominant] > limit:
        keep = alpha / 255
        values[dominant] = round(limit + (values[dominant] - limit) * keep)
    return tuple(values)


def cut_chroma_to_alpha(
    source: Path,
    output: Path,
    *,
    key_color: tuple[int, int, int] | None = None,
    transparent_threshold: int = 12,
    opaque_threshold: int = 220,
    despill: bool = True,
) -> CutResult:
    image = Image.open(source).convert("RGBA")
    key = key_color or infer_key_color(image)
    data = []
    transparent = 0
    partial = 0

    pixels = image.get_flattened_data() if hasattr(image, "get_flattened_data") else image.getdata()
    for red, green, blue, original_alpha in pixels:
        distance = color_distance((red, green, blue), key)
        alpha = alpha_for_distance(distance, transparent_threshold, opaque_threshold)
        alpha = min(alpha, original_alpha)
        if alpha == 0:
            transparent += 1
        elif alpha < 255:
            partial += 1
        if despill:
            red, green, blue = despill_rgb((red, green, blue), key, alpha)
        data.append((red, green, blue, alpha))

    out = Image.new("RGBA", image.size)
    out.putdata(data)
    output.parent.mkdir(parents=True, exist_ok=True)
    out.save(output)
    width, height = out.size
    return CutResult(key, transparent, partial, width * height, width, height)


def sprite_media_path(slug: str, output_subdir: Path = DEFAULT_OUTPUT_SUBDIR) -> str:
    return str((output_subdir / f"{slug}.png").as_posix())


def update_sprite_asset(
    db_path: Path,
    slug: str,
    image_path: str,
    width: int,
    height: int,
) -> int:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            "update sprites_spriteasset "
            "set OriginalImage = ?, Width = ?, Height = ? "
            "where Slug = ?",
            (image_path, width, height, slug),
        )
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def process_asset(
    slug: str,
    source: Path,
    *,
    media_root: Path,
    output_subdir: Path,
    db_path: Path | None,
    copy_source: bool,
    overwrite: bool,
    transparent_threshold: int,
    opaque_threshold: int,
    despill: bool,
) -> CutResult:
    if not source.exists():
        raise FileNotFoundError(source)

    output_dir = media_root / output_subdir
    final_path = output_dir / f"{slug}.png"
    source_copy = output_dir / f"{slug}-source{source.suffix.lower() or '.png'}"
    if not overwrite:
        existing = [path for path in (final_path, source_copy if copy_source else final_path) if path.exists()]
        if existing:
            names = ", ".join(str(path) for path in existing)
            raise FileExistsError(f"Refusing to overwrite existing file(s): {names}")

    output_dir.mkdir(parents=True, exist_ok=True)
    cut_source = source
    if copy_source:
        shutil.copy2(source, source_copy)
        cut_source = source_copy

    result = cut_chroma_to_alpha(
        cut_source,
        final_path,
        transparent_threshold=transparent_threshold,
        opaque_threshold=opaque_threshold,
        despill=despill,
    )

    if db_path is not None:
        rel_path = sprite_media_path(slug, output_subdir)
        updated = update_sprite_asset(db_path, slug, rel_path, result.width, result.height)
        if updated == 0:
            print(f"warning: no SpriteAsset row found for slug {slug!r}", file=sys.stderr)
    return result


def build_pairs(args: argparse.Namespace) -> list[tuple[str, Path]]:
    explicit = parse_asset_specs(args.asset or [])
    if explicit:
        if args.latest or args.slugs:
            raise ValueError("Use either --asset or --latest/--slugs, not both")
        return explicit

    if args.latest is None or not args.slugs:
        raise ValueError("Provide --asset slug=path, or --latest N with --slugs ...")
    if len(args.slugs) != args.latest:
        raise ValueError("--latest count must match the number of --slugs")

    sources = select_latest_sources(args.generated_dir, args.latest)
    return list(zip(args.slugs, sources))


def parse_args(argv: list[str]) -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--asset", action="append", help="Pair in the form slug=path. Repeat for batches.")
    parser.add_argument("--latest", type=int, help="Use the latest N generated image files.")
    parser.add_argument("--slugs", nargs="+", help="Slugs matching --latest, in prompt order.")
    parser.add_argument("--generated-dir", type=Path, default=default_generated_dir())
    parser.add_argument("--media-root", type=Path, default=root / "dd3esheet" / "media")
    parser.add_argument("--output-subdir", type=Path, default=DEFAULT_OUTPUT_SUBDIR)
    parser.add_argument("--db", type=Path, default=root / "dd3esheet" / "db.sqlite3")
    parser.add_argument("--no-db", action="store_true", help="Do not update db.sqlite3.")
    parser.add_argument("--no-source-copy", action="store_true", help="Do not keep slug-source.png.")
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing existing files.")
    parser.add_argument("--transparent-threshold", type=int, default=12)
    parser.add_argument("--opaque-threshold", type=int, default=220)
    parser.add_argument("--no-despill", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        pairs = build_pairs(args)
        db_path = None if args.no_db else args.db
        for slug, source in pairs:
            result = process_asset(
                slug,
                source,
                media_root=args.media_root,
                output_subdir=args.output_subdir,
                db_path=db_path,
                copy_source=not args.no_source_copy,
                overwrite=args.overwrite,
                transparent_threshold=args.transparent_threshold,
                opaque_threshold=args.opaque_threshold,
                despill=not args.no_despill,
            )
            print(
                f"{slug}: wrote {sprite_media_path(slug, args.output_subdir)} "
                f"key=#{result.key_color[0]:02x}{result.key_color[1]:02x}{result.key_color[2]:02x} "
                f"transparent={result.transparent_pixels}/{result.total_pixels} "
                f"partial={result.partial_transparent_pixels}"
            )
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
