"""Generate first-pass PNGs for the TOKENS.md sprite expansion.

The output follows the existing local-media convention:

  dd3esheet/media/sprites/original/<category>/<slug>.png

The script is intentionally deterministic and lightweight. It creates a coherent
Parchment & Ink first pass for every asset in
``sprite_manifest_tokens_expansion.json`` and updates ``db.sqlite3`` rows when
they already exist.

Example:

  python scripts/generate_token_expansion_pngs.py --overwrite
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sqlite3
import sys
from collections.abc import Callable
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageOps
except ImportError as exc:  # pragma: no cover - exercised manually.
    raise SystemExit("Pillow is required. Install it with: python -m pip install pillow") from exc


DARK_INK = (43, 38, 34, 255)
PARCHMENT = (239, 230, 210, 255)
OCHRE = (200, 146, 58, 255)
LEATHER = (122, 79, 42, 255)
FOREST = (79, 107, 58, 255)
IRON = (107, 111, 115, 255)
DEEP_RED = (138, 47, 40, 255)
STEEL_BLUE = (63, 96, 121, 255)
BONE = (214, 198, 170, 255)
SHADOW = (73, 54, 40, 255)
MUTED_GOLD = (181, 138, 54, 255)
ARCANE_TEAL = (47, 111, 106, 255)
ROYAL_BLUE = (49, 79, 124, 255)
DULL_VIOLET = (93, 73, 120, 255)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resampling_filter() -> int:
    return getattr(Image, "Resampling", Image).LANCZOS


def seeded_random(slug: str) -> random.Random:
    return random.Random(f"dd3e-token-expansion:{slug}:v1")


def manifest_path(root: Path) -> Path:
    return root / "dd3esheet" / "sprites" / "fixtures" / "sprite_manifest_tokens_expansion.json"


def load_assets(root: Path) -> list[dict]:
    data = json.loads(manifest_path(root).read_text(encoding="utf-8"))
    return [asset for section in data["sections"] for asset in section["assets"]]


def image_data(image: Image.Image):
    return image.get_flattened_data() if hasattr(image, "get_flattened_data") else image.getdata()


def noise_layer(size: int, rng: random.Random, cells: int) -> Image.Image:
    count = max(2, math.ceil(size / cells) + 2)
    image = Image.new("L", (count, count))
    image.putdata([rng.randrange(256) for _index in range(count * count)])
    return image.resize((size, size), getattr(Image, "Resampling", Image).BICUBIC)


def fractal_noise(size: int, rng: random.Random) -> Image.Image:
    result = Image.new("L", (size, size), 128)
    for cells, blend in ((96, 0.42), (48, 0.33), (20, 0.24), (8, 0.12)):
        result = Image.blend(result, noise_layer(size, rng, cells), blend)
    return result.filter(ImageFilter.GaussianBlur(0.65))


def colorized_texture(size: int, rng: random.Random, dark: tuple[int, int, int], light: tuple[int, int, int]) -> Image.Image:
    return ImageOps.colorize(fractal_noise(size, rng), black=dark, white=light).convert("RGBA")


def rgba(rgb: tuple[int, int, int] | tuple[int, int, int, int], alpha: int = 255) -> tuple[int, int, int, int]:
    if len(rgb) == 4:
        return (rgb[0], rgb[1], rgb[2], alpha)
    return (rgb[0], rgb[1], rgb[2], alpha)


def force_opaque(image: Image.Image) -> Image.Image:
    rgb = image.convert("RGB")
    return Image.merge("RGBA", (*rgb.split(), Image.new("L", rgb.size, 255)))


def transparent(size: int) -> Image.Image:
    return Image.new("RGBA", (size, size), (0, 0, 0, 0))


def draw_ink_grain(image: Image.Image, rng: random.Random, count: int, color: tuple[int, int, int, int]) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    for _index in range(count):
        x = rng.randrange(image.width)
        y = rng.randrange(image.height)
        radius = rng.choice((1, 1, 2, 2, 3))
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)


def draw_texture_strokes(image: Image.Image, rng: random.Random, count: int, color: tuple[int, int, int, int]) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    size = image.width
    for _index in range(count):
        x = rng.randrange(-20, size + 20)
        y = rng.randrange(-20, size + 20)
        length = rng.randrange(18, 82)
        angle = rng.uniform(0, math.tau)
        draw.line((x, y, x + math.cos(angle) * length, y + math.sin(angle) * length), fill=color, width=rng.choice((1, 1, 2)))


def draw_blob(draw: ImageDraw.ImageDraw, center: tuple[float, float], radius: float, rng: random.Random, fill, outline=DARK_INK, width: int = 3, sides: int = 10) -> None:
    cx, cy = center
    points = []
    for index in range(sides):
        angle = math.tau * index / sides + rng.uniform(-0.13, 0.13)
        distance = radius * rng.uniform(0.78, 1.16)
        points.append((cx + math.cos(angle) * distance, cy + math.sin(angle) * distance))
    draw.polygon(points, fill=fill, outline=outline)
    if width > 1:
        draw.line(points + [points[0]], fill=outline, width=width, joint="curve")


def draw_path(image: Image.Image, points: list[tuple[int, int]], color: tuple[int, int, int, int], width: int) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    for offset in range(width + 22, 0, -12):
        draw.line(points, fill=(color[0], color[1], color[2], max(20, color[3] // 5)), width=offset, joint="curve")
    draw.line(points, fill=color, width=width, joint="curve")


def draw_road_by_role(image: Image.Image, rng: random.Random, role: str, color: tuple[int, int, int, int], width: int) -> None:
    size = image.width
    if role in {"curve", "corner"}:
        points = [(-30, size // 2), (size // 3, size // 2), (size // 2, size // 3), (size // 2, -30)]
    elif role in {"t_junction", "fork"}:
        draw_path(image, [(-30, size // 2), (size + 30, size // 2)], color, width)
        points = [(size // 2, size // 2), (size // 2, -30)]
    elif role == "crossroads":
        draw_path(image, [(-30, size // 2), (size + 30, size // 2)], color, width)
        points = [(size // 2, -30), (size // 2, size + 30)]
    elif role == "end_cap":
        points = [(-30, size // 2), (size // 2, size // 2)]
    else:
        points = [(-30, size // 2 + rng.randrange(-14, 15)), (size // 2, size // 2 + rng.randrange(-18, 19)), (size + 30, size // 2 + rng.randrange(-14, 15))]
    draw_path(image, points, color, width)


def clamp_byte(value: int) -> int:
    return max(0, min(255, value))


def shifted(color: tuple[int, int, int], amount: int, alpha: int) -> tuple[int, int, int, int]:
    return (
        clamp_byte(color[0] + amount),
        clamp_byte(color[1] + amount),
        clamp_byte(color[2] + amount),
        alpha,
    )


def draw_material_grain(image: Image.Image, rng: random.Random, dark_count: int = 260, light_count: int = 80) -> None:
    draw_ink_grain(image, rng, dark_count, rgba(DARK_INK, 30))
    draw_ink_grain(image, rng, light_count, (230, 218, 178, 22))
    draw_texture_strokes(image, rng, 26, rgba(DARK_INK, 24))


def cobblestone_material(size: int, rng: random.Random, *, darker: bool = False) -> Image.Image:
    base_dark = (38, 37, 34) if darker else (45, 43, 38)
    base_light = (76, 72, 63) if darker else (92, 87, 74)
    stone_base = (98, 94, 82) if darker else (114, 109, 94)
    image = colorized_texture(size, rng, base_dark, base_light)
    draw = ImageDraw.Draw(image, "RGBA")
    y = -30
    row = 0
    while y < size + 34:
        height = rng.randrange(34, 54)
        x = -70 - (row % 2) * rng.randrange(18, 46)
        while x < size + 72:
            width = rng.randrange(42, 82)
            shade = rng.randrange(-25, 24)
            radius = rng.randrange(7, 15)
            rect = (x, y, x + width, y + height)
            draw.rounded_rectangle(
                rect,
                radius=radius,
                fill=shifted(stone_base, shade, 228),
                outline=(28, 27, 24, 145),
                width=2,
            )
            draw.arc((x + 5, y + 4, x + width - 5, y + height - 3), 198, 292, fill=(230, 222, 194, 40), width=1)
            draw.line((x + 8, y + height - 5, x + width - 8, y + height - 6), fill=(20, 19, 17, 42), width=1)
            if rng.random() < 0.48:
                cx = x + rng.randrange(8, max(9, width - 7))
                cy = y + rng.randrange(8, max(9, height - 7))
                draw.line((cx - 9, cy, cx + 9, cy + rng.randrange(-4, 5)), fill=(34, 33, 30, 52), width=1)
            x += width + rng.randrange(5, 12)
        y += height + rng.randrange(5, 10)
        row += 1
    draw_material_grain(image, rng, 300, 90)
    return force_opaque(image.filter(ImageFilter.UnsharpMask(radius=1.1, percent=80, threshold=3)))


def flagstone_material(size: int, rng: random.Random, *, darker: bool = False) -> Image.Image:
    image = colorized_texture(size, rng, (44, 43, 39) if darker else (61, 58, 51), (92, 87, 76) if darker else (135, 127, 109))
    draw = ImageDraw.Draw(image, "RGBA")
    y = -18
    while y < size + 24:
        height = rng.randrange(62, 98)
        x = -28
        row_shift = rng.randrange(-18, 19)
        while x < size + 32:
            width = rng.randrange(72, 132)
            jitter = rng.randrange(4, 14)
            points = [
                (x + rng.randrange(-jitter, jitter + 1) + row_shift, y + rng.randrange(-jitter, jitter + 1)),
                (x + width + rng.randrange(-jitter, jitter + 1) + row_shift, y + rng.randrange(-jitter, jitter + 1)),
                (x + width + rng.randrange(-jitter, jitter + 1) + row_shift, y + height + rng.randrange(-jitter, jitter + 1)),
                (x + rng.randrange(-jitter, jitter + 1) + row_shift, y + height + rng.randrange(-jitter, jitter + 1)),
            ]
            shade = rng.randrange(-20, 22)
            draw.polygon(points, fill=shifted((112, 107, 94), shade, 205), outline=(29, 28, 25, 116))
            if rng.random() < 0.55:
                mid_y = y + height // 2 + rng.randrange(-9, 10)
                draw.line((x + 12, mid_y, x + width - 14, mid_y + rng.randrange(-7, 8)), fill=(36, 34, 30, 48), width=1)
            x += width + rng.randrange(5, 13)
        y += height + rng.randrange(5, 12)
    draw_material_grain(image, rng, 240, 85)
    return force_opaque(image.filter(ImageFilter.UnsharpMask(radius=1.0, percent=70, threshold=3)))


def grass_material(size: int, rng: random.Random, *, village: bool = False, dense: bool = False) -> Image.Image:
    dark = (44, 74, 33) if not village else (61, 78, 39)
    light = (128, 136, 67) if not village else (158, 141, 74)
    image = colorized_texture(size, rng, dark, light)
    draw_grass_blades(image, rng, 250 if dense else 150, alpha=85 if dense else 68)
    for _index in range(28 if dense else 6):
        cx = rng.randrange(-20, size + 20)
        cy = rng.randrange(-20, size + 20)
        radius = rng.randrange(18, 48) if dense else rng.randrange(10, 26)
        alpha = rng.randrange(64, 96) if dense else rng.randrange(30, 54)
        draw_blob(ImageDraw.Draw(image, "RGBA"), (cx, cy), radius, rng, rgba(rng.choice(((49, 88, 39), (70, 101, 45), (91, 100, 45))), alpha), rgba(DARK_INK, 22), width=1, sides=11)
    draw_material_grain(image, rng, 220, 90)
    return force_opaque(image.filter(ImageFilter.UnsharpMask(radius=1.0, percent=55, threshold=4)))


def dirt_material(size: int, rng: random.Random, *, mud: bool = False) -> Image.Image:
    if mud:
        image = colorized_texture(size, rng, (59, 56, 36), (130, 103, 59))
    else:
        image = colorized_texture(size, rng, (91, 61, 39), (181, 139, 82))
    draw = ImageDraw.Draw(image, "RGBA")
    for _index in range(120):
        x = rng.randrange(size)
        y = rng.randrange(size)
        radius = rng.choice((1, 1, 2, 2, 3, 4))
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(52, 38, 25, rng.randrange(30, 70)))
    for _index in range(24):
        x = rng.randrange(size)
        y = rng.randrange(size)
        length = rng.randrange(22, 90)
        angle = rng.uniform(-0.4, 0.4) + rng.choice((0, math.pi))
        draw.line((x, y, x + math.cos(angle) * length, y + math.sin(angle) * length), fill=(43, 31, 22, 48), width=rng.choice((1, 1, 2)))
    draw_material_grain(image, rng, 210, 70)
    return force_opaque(image.filter(ImageFilter.UnsharpMask(radius=1.0, percent=60, threshold=4)))


def swamp_water_material(size: int, rng: random.Random, *, black: bool = False) -> Image.Image:
    image = colorized_texture(size, rng, (11, 28, 29) if black else (22, 55, 56), (44, 75, 65) if black else (88, 124, 107))
    draw = ImageDraw.Draw(image, "RGBA")
    for _index in range(42):
        y = rng.randrange(35, size - 35)
        phase = rng.random() * math.tau
        points = [(x, y + math.sin(x / rng.uniform(42, 80) + phase) * rng.uniform(2, 8)) for x in range(-18, size + 19, 22)]
        draw.line(points, fill=(172, 209, 190, rng.randrange(30, 74)), width=rng.choice((1, 1, 2)), joint="curve")
    for _index in range(28):
        x = rng.randrange(size)
        y = rng.randrange(size)
        r = rng.randrange(8, 26)
        draw.ellipse((x - r, y - r // 2, x + r, y + r // 2), outline=(13, 25, 22, 42), width=1)
    return force_opaque(image.filter(ImageFilter.UnsharpMask(radius=1.0, percent=55, threshold=4)))


def rocky_material(size: int, rng: random.Random, *, dark: bool = False) -> Image.Image:
    image = colorized_texture(size, rng, (50, 49, 44) if dark else (67, 64, 54), (122, 117, 101) if dark else (163, 151, 126))
    draw = ImageDraw.Draw(image, "RGBA")
    draw_boulder_field(draw, rng, size, 62 if dark else 72, alpha=(65, 135))
    for _index in range(38):
        x = rng.randrange(size)
        y = rng.randrange(size)
        angle = rng.uniform(0, math.tau)
        length = rng.randrange(24, 100)
        draw.line((x, y, x + math.cos(angle) * length, y + math.sin(angle) * length), fill=(30, 29, 26, 60), width=rng.choice((1, 1, 2)))
    draw_material_grain(image, rng, 270, 70)
    return force_opaque(image.filter(ImageFilter.UnsharpMask(radius=1.0, percent=75, threshold=3)))


def draw_boulder_field(draw: ImageDraw.ImageDraw, rng: random.Random, size: int, count: int, *, alpha: tuple[int, int] = (85, 180)) -> None:
    for _index in range(count):
        cx = rng.randrange(-20, size + 20)
        cy = rng.randrange(-20, size + 20)
        radius = rng.randrange(9, 36)
        shade = rng.randrange(-22, 28)
        fill = shifted((118, 112, 95), shade, rng.randrange(alpha[0], alpha[1]))
        draw_blob(draw, (cx, cy), radius, rng, fill, (34, 33, 29, 88), width=2, sides=rng.randrange(6, 10))
        draw.line((cx - radius // 2, cy - radius // 3, cx + radius // 4, cy - radius // 2), fill=(226, 216, 188, 34), width=1)


def draw_grass_blades(image: Image.Image, rng: random.Random, count: int, *, alpha: int = 70, y_range: tuple[int, int] | None = None) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    top, bottom = y_range or (0, image.height)
    for _index in range(count):
        x = rng.randrange(image.width)
        y = rng.randrange(top, bottom)
        h = rng.randrange(9, 34)
        lean = rng.randrange(-7, 8)
        color = rng.choice(((49, 88, 37), (63, 100, 44), (88, 108, 50), (38, 72, 35)))
        draw.line((x, y, x + lean, y - h), fill=(*color, rng.randrange(max(30, alpha - 25), min(160, alpha + 35))), width=rng.choice((1, 1, 2)))


def route_paths(size: int, rng: random.Random, role: str) -> list[list[tuple[int, int]]]:
    if role == "curve":
        return [[(-38, size // 2 + rng.randrange(-8, 9)), (size // 3, size // 2), (size // 2, size // 3), (size // 2 + rng.randrange(-8, 9), -38)]]
    if role == "t_junction":
        return [
            [(-38, size // 2), (size + 38, size // 2 + rng.randrange(-8, 9))],
            [(size // 2, size // 2), (size // 2 + rng.randrange(-10, 11), -38)],
        ]
    if role == "fork":
        return [
            [(-38, size // 2), (size // 2, size // 2), (size + 38, size // 3)],
            [(size // 2, size // 2), (size + 38, size - size // 3)],
        ]
    if role == "crossroads":
        return [
            [(-38, size // 2), (size + 38, size // 2 + rng.randrange(-8, 9))],
            [(size // 2 + rng.randrange(-8, 9), -38), (size // 2, size + 38)],
        ]
    if role == "end_cap":
        return [[(-38, size // 2), (size // 2 + 24, size // 2 + rng.randrange(-12, 13))]]
    return [[(-38, size // 2 + rng.randrange(-14, 15)), (size // 2, size // 2 + rng.randrange(-18, 19)), (size + 38, size // 2 + rng.randrange(-14, 15))]]


def mask_for_paths(size: int, paths: list[list[tuple[int, int]]], width: int, *, blur: float = 1.4) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    for points in paths:
        draw.line(points, fill=255, width=width, joint="curve")
        radius = width // 2
        draw.ellipse((points[-1][0] - radius, points[-1][1] - radius, points[-1][0] + radius, points[-1][1] + radius), fill=255)
    return mask.filter(ImageFilter.GaussianBlur(blur))


def paint_textured_route(image: Image.Image, rng: random.Random, role: str, *, material: str, width: int) -> None:
    size = image.width
    paths = route_paths(size, rng, role)
    if material == "stone":
        texture = cobblestone_material(size, rng)
        edge_color = (28, 27, 24, 82)
    elif material == "rock":
        texture = rocky_material(size, rng, dark=True)
        edge_color = (31, 29, 24, 80)
    else:
        texture = dirt_material(size, rng, mud=material == "mud")
        edge_color = (54, 39, 25, 76)
    wide_mask = mask_for_paths(size, paths, width + 34, blur=2.4)
    core_mask = mask_for_paths(size, paths, width, blur=1.2)
    image.paste(Image.new("RGBA", (size, size), edge_color), (0, 0), wide_mask)
    image.paste(texture, (0, 0), core_mask)
    draw = ImageDraw.Draw(image, "RGBA")
    for points in paths:
        if material == "stone":
            draw.line(points, fill=(238, 230, 198, 22), width=max(2, width // 28), joint="curve")
        else:
            for offset in (-width // 4, width // 4):
                shifted_points = [(x, y + offset) for x, y in points]
                draw.line(shifted_points, fill=(44, 31, 21, 58), width=max(2, width // 22), joint="curve")
    mask_pixels = core_mask.load()
    for _index in range(95 if width > 70 else 50):
        x = rng.randrange(size)
        y = rng.randrange(size)
        if mask_pixels[x, y] < 70:
            continue
        r = rng.choice((1, 1, 2, 3))
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(38, 31, 24, rng.randrange(38, 90)))


def terrain_base(asset: dict, size: int, rng: random.Random) -> Image.Image:
    slug = asset["id"]
    subcategory = asset.get("subcategory", "")
    role = asset.get("modular_role", "")

    if "cobblestone_transition" in slug:
        grass = grass_material(size, rng, village=True)
        cobble = cobblestone_material(size, rng)
        mask = Image.new("L", (size, size), 0)
        md = ImageDraw.Draw(mask)
        boundary = size // 2 + rng.randrange(-18, 19)
        md.rectangle((0, 0, boundary, size), fill=255)
        for y in range(-20, size + 21, 36):
            md.ellipse((boundary - 42 + rng.randrange(-12, 13), y - 26, boundary + 42 + rng.randrange(-12, 13), y + 34), fill=255)
        grass.paste(cobble, (0, 0), mask.filter(ImageFilter.GaussianBlur(2.2)))
        draw_grass_blades(grass, rng, 80, alpha=78)
        draw_material_grain(grass, rng, 130, 42)
        return force_opaque(grass)

    if "black_pool" in slug:
        base = dirt_material(size, rng, mud=True)
        draw = ImageDraw.Draw(base, "RGBA")
        draw.ellipse((106, 104, 406, 408), fill=(13, 18, 15, 218), outline=(61, 50, 34, 190), width=8)
        draw.ellipse((158, 152, 354, 354), fill=(4, 7, 7, 225), outline=(27, 38, 34, 120), width=4)
        for _index in range(15):
            x = rng.randrange(160, 352)
            y = rng.randrange(158, 350)
            if (x - 256) ** 2 + (y - 256) ** 2 < 92 ** 2:
                draw.ellipse((x - 2, y - 1, x + 2, y + 1), fill=(132, 158, 131, 42))
        draw_material_grain(base, rng, 130, 36)
        return force_opaque(base)

    if "water" in slug or "pool" in slug or "earth_island" in slug:
        water = swamp_water_material(size, rng, black="black_pool" in slug)
        if "edge" in slug:
            base = dirt_material(size, rng, mud=True)
            draw_grass_blades(base, rng, 95, alpha=72, y_range=(0, size // 2 + 80))
            mask = Image.new("L", (size, size), 0)
            md = ImageDraw.Draw(mask)
            md.rectangle((0, size // 2, size, size), fill=255)
            for x in range(-20, size + 21, 34):
                md.ellipse((x - 34, size // 2 - 50 + rng.randrange(-24, 25), x + 48, size // 2 + 46 + rng.randrange(-24, 25)), fill=255)
            base.paste(water, (0, 0), mask.filter(ImageFilter.GaussianBlur(5)))
        elif "island" in slug:
            base = water
            draw = ImageDraw.Draw(base, "RGBA")
            island = dirt_material(size, rng, mud=True)
            mask = Image.new("L", (size, size), 0)
            md = ImageDraw.Draw(mask)
            radius = size * (0.30 if "small" in slug else 0.41)
            points = []
            for index in range(22):
                angle = math.tau * index / 22
                distance = radius * rng.uniform(0.76, 1.16)
                points.append((size // 2 + math.cos(angle) * distance, size // 2 + math.sin(angle) * distance))
            md.polygon(points, fill=255)
            base.paste(island, (0, 0), mask.filter(ImageFilter.GaussianBlur(2.2)))
            draw.line(points + [points[0]], fill=rgba(DARK_INK, 95), width=3, joint="curve")
            draw_grass_blades(base, rng, 90, alpha=70, y_range=(120, 392))
        else:
            base = water
        draw = ImageDraw.Draw(base, "RGBA")
        if "reeds" not in slug:
            for _index in range(42):
                x = rng.randrange(size)
                y = rng.randrange(size)
                draw.line((x, y, x + rng.randrange(-5, 6), y - rng.randrange(12, 34)), fill=(72, 94, 45, 78), width=1)
        draw_material_grain(base, rng, 140, 45)
        return force_opaque(base)

    if "city" in subcategory or "castle_floor" in slug or "stone_floor" in slug or "flagstone" in slug or "courtyard" in slug:
        if "flagstone" in slug or "castle_floor" in slug or "courtyard" in slug or "irregular_stone" in slug:
            base = flagstone_material(size, rng, darker="castle" in slug)
        else:
            base = cobblestone_material(size, rng)
    elif "rocky" in subcategory or "rocky" in slug:
        base = rocky_material(size, rng)
    elif "mud_patch" in slug:
        base = dirt_material(size, rng, mud=True)
    elif "swamp" in subcategory or "swamp" in slug:
        base = dirt_material(size, rng, mud=True)
        draw_grass_blades(base, rng, 105, alpha=72)
    elif "forest" in subcategory or "forest" in slug:
        base = grass_material(size, rng, dense="dense" in slug or "underbrush" in slug)
    elif "village" in subcategory or "village" in slug:
        base = grass_material(size, rng, village=True, dense="grass" in slug or "garden" in slug)
    else:
        base = dirt_material(size, rng)

    draw = ImageDraw.Draw(base, "RGBA")

    if any(part in slug for part in ("dirt_road", "trail", "path", "stone_road", "sidewalk", "rocky_path")):
        material = "dirt"
        if "stone_road" in slug or "sidewalk" in slug:
            material = "stone"
        elif "rocky_path" in slug:
            material = "rock"
        elif "swamp" in slug:
            material = "mud"
        paint_textured_route(base, rng, role, material=material, width=92 if "road" in slug else 58)

    if "fence" in slug:
        draw_transparent_fence(base, rng, role, as_overlay=True)
    if "garden" in slug:
        for y in range(82, size - 64, 46):
            draw.line((54, y, size - 54, y + rng.randrange(-8, 9)), fill=(66, 92, 38, 170), width=15)
            draw.line((54, y + 16, size - 54, y + 16 + rng.randrange(-8, 9)), fill=(114, 79, 42, 150), width=6)
            for x in range(76, size - 70, 42):
                draw.ellipse((x - 5, y - 7, x + 5, y + 5), fill=(49, 110, 42, 130))
    if "grass" in slug or "clearing" in slug or "underbrush" in slug or "reeds" in slug:
        draw_grass_blades(base, rng, 230 if "high" in slug or "reeds" in slug else 110, alpha=112 if "high" in slug or "reeds" in slug else 78)
    if "reeds" in slug:
        draw_reeds(draw, rng, size, count=46)
    if "bush" in slug:
        draw_bush_cluster(draw, rng, size, count=18)
    if "clearing_edge" in slug or "edge_dense" in slug:
        for _index in range(36 if "dense" in slug else 22):
            x = rng.randrange(-28, size + 28)
            y = rng.choice((rng.randrange(-20, 140), rng.randrange(size - 140, size + 20)))
            draw_tree(draw, x, y, rng, large=True)
    if "tree" in slug:
        if "group" not in slug:
            if "pine" in slug:
                draw_pine_tree(draw, size // 2, size // 2, rng)
            else:
                draw_tree(draw, size // 2, size // 2, rng, large="large" in slug, dead="dead" in slug)
        else:
            count = 12 if "sparse" in slug else 34
            for _index in range(count):
                x = rng.randrange(40, size - 40)
                y = rng.randrange(40, size - 40)
                draw_tree(draw, x, y, rng, large=True, dead=False)
    if "rock" in slug or "stone" in slug or "cliff" in slug or "loose" in slug:
        draw_boulder_field(draw, rng, size, 46 if "tile" in slug or "loose" in slug else 18, alpha=(95, 190))
        if "cliff" in slug or "elevated" in slug:
            shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            shadow_pixels = []
            for y in range(size):
                alpha = 0
                if y > size // 2 + 28:
                    alpha = min(74, round((y - (size // 2 + 28)) / (size // 2) * 74))
                shadow_pixels.extend([(22, 22, 20, alpha)] * size)
            shadow.putdata(shadow_pixels)
            base.alpha_composite(shadow)
            for x in range(-10, size + 20, 34):
                draw.line((x, size // 2 + rng.randrange(28, 60), x + rng.randrange(-26, 27), size - rng.randrange(12, 70)), fill=(24, 23, 21, 90), width=rng.choice((2, 3, 4)))
    if "log" in slug:
        draw_log(draw, (72, size // 2 - 28, size - 70, size // 2 + 28), rng, submerged="submerged" in slug)
    if "roots" in slug:
        for _index in range(16):
            y = rng.randrange(120, size - 90)
            draw.line((30, y, size - 30, y + rng.randrange(-50, 51)), fill=(75, 48, 31, 172), width=rng.randrange(4, 10))
            draw.line((30, y - 2, size - 30, y + rng.randrange(-50, 51) - 2), fill=(152, 103, 56, 45), width=1)
    if "sinkhole" in slug:
        draw.ellipse((126, 128, 386, 390), fill=(31, 35, 28, 210), outline=(72, 54, 34, 185), width=8)
        draw.ellipse((172, 170, 340, 338), fill=(13, 16, 14, 190))
    if "natural_platform" in slug:
        points = []
        for index in range(18):
            angle = math.tau * index / 18
            distance = rng.uniform(142, 190)
            points.append((size // 2 + math.cos(angle) * distance, size // 2 + math.sin(angle) * distance))
        draw.polygon(points, fill=(121, 116, 99, 210), outline=(34, 33, 29, 135))
        draw.line(points + [points[0]], fill=(226, 216, 188, 36), width=2, joint="curve")
        draw_boulder_field(draw, rng, size, 18, alpha=(55, 105))

    draw_material_grain(base, rng, 150, 42)
    return force_opaque(base.filter(ImageFilter.UnsharpMask(radius=1.0, percent=58, threshold=4)))


def draw_tree(draw: ImageDraw.ImageDraw, x: int, y: int, rng: random.Random, *, large: bool = False, dead: bool = False) -> None:
    if dead:
        draw.line((x + 5, y + 42, x, y - 52), fill=rgba(LEATHER, 225), width=11)
        for angle in (-0.9, -0.45, 0.45, 0.9):
            draw.line((x, y - 16, x + math.cos(angle) * 66, y - 16 + math.sin(angle) * 66), fill=rgba(LEATHER, 190), width=5)
            draw.line((x + 1, y - 19, x + math.cos(angle) * 42, y - 19 + math.sin(angle) * 42), fill=rgba(BONE, 42), width=1)
        return
    radius = 48 if large else 32
    for _index in range(8 if large else 5):
        ox = rng.randrange(-radius // 2, radius // 2 + 1)
        oy = rng.randrange(-radius // 2, radius // 2 + 1)
        rx = rng.randrange(radius - 12, radius + 10)
        ry = rng.randrange(radius - 16, radius + 7)
        green = rng.choice((FOREST, (60, 96, 47), (42, 76, 39), (73, 111, 51)))
        draw.ellipse((x + ox - rx, y + oy - ry, x + ox + rx, y + oy + ry), fill=rgba(green, 188), outline=rgba(DARK_INK, 58), width=2)
        draw.arc((x + ox - rx + 8, y + oy - ry + 8, x + ox + rx - 8, y + oy + ry - 8), 205, 300, fill=(218, 232, 164, 35), width=2)
    draw.ellipse((x - 8, y - 8, x + 8, y + 8), fill=rgba(LEATHER, 170))


def draw_pine_tree(draw: ImageDraw.ImageDraw, x: int, y: int, rng: random.Random) -> None:
    for radius, alpha, offset in ((58, 210, 0), (45, 205, -4), (32, 200, -8)):
        points = []
        for index in range(14):
            angle = math.tau * index / 14
            distance = radius * (1.05 if index % 2 == 0 else 0.68) * rng.uniform(0.9, 1.08)
            points.append((x + math.cos(angle) * distance, y + offset + math.sin(angle) * distance))
        draw.polygon(points, fill=rgba(rng.choice(((36, 74, 42), (43, 86, 47), (31, 65, 39))), alpha), outline=rgba(DARK_INK, 75))
    draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill=rgba(LEATHER, 150))


def draw_bush_cluster(draw: ImageDraw.ImageDraw, rng: random.Random, size: int, *, count: int) -> None:
    for _index in range(count):
        x = rng.randrange(size // 2 - 130, size // 2 + 131)
        y = rng.randrange(size // 2 - 120, size // 2 + 121)
        rx = rng.randrange(22, 54)
        ry = rng.randrange(18, 46)
        color = rng.choice(((42, 84, 38), (55, 98, 45), (72, 105, 50)))
        draw.ellipse((x - rx, y - ry, x + rx, y + ry), fill=rgba(color, rng.randrange(155, 215)), outline=rgba(DARK_INK, 55), width=2)
        draw.arc((x - rx + 6, y - ry + 5, x + rx - 6, y + ry - 5), 205, 305, fill=(218, 232, 164, 34), width=2)


def draw_reeds(draw: ImageDraw.ImageDraw, rng: random.Random, size: int, *, count: int) -> None:
    for _index in range(count):
        x = rng.randrange(42, size - 42)
        y = rng.randrange(90, size - 42)
        height = rng.randrange(34, 92)
        lean = rng.randrange(-10, 11)
        draw.line((x, y, x + lean, y - height), fill=(67, 95, 45, rng.randrange(135, 205)), width=rng.choice((2, 2, 3)))
        if rng.random() < 0.65:
            draw.ellipse((x + lean - 4, y - height - 9, x + lean + 4, y - height + 9), fill=(139, 111, 62, 150))


def draw_log(draw: ImageDraw.ImageDraw, rect: tuple[int, int, int, int], rng: random.Random, *, submerged: bool = False) -> None:
    fill = rgba(LEATHER, 145 if submerged else 225)
    outline = rgba(DARK_INK, 75 if submerged else 150)
    draw.rounded_rectangle(rect, radius=20, fill=fill, outline=outline, width=4)
    for x in range(rect[0] + 28, rect[2] - 20, 54):
        draw.line((x, rect[1] + 5, x + rng.randrange(-6, 7), rect[3] - 5), fill=rgba(SHADOW, 90), width=2)
    draw.line((rect[0] + 24, rect[1] + 12, rect[2] - 28, rect[1] + 16), fill=rgba(BONE, 42 if submerged else 70), width=2)
    for x in (rect[0] + 24, rect[2] - 44):
        draw.ellipse((x - 18, rect[1] + 4, x + 18, rect[3] - 4), outline=rgba(DARK_INK, 95 if submerged else 140), width=3)


def draw_transparent_fence(image: Image.Image, rng: random.Random, role: str, *, as_overlay: bool = False) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    size = image.width
    segments = []
    if role == "corner":
        segments = [((40, size // 2), (size // 2, size // 2)), ((size // 2, size // 2), (size // 2, 40))]
    elif role == "gate":
        segments = [((30, size // 2), (210, size // 2)), ((302, size // 2), (size - 30, size // 2))]
    else:
        segments = [((30, size // 2), (size - 30, size // 2))]
    for start, end in segments:
        draw.line((*start, *end), fill=rgba(SHADOW, 118), width=28)
        draw.line((*start, *end), fill=rgba(LEATHER, 238), width=14)
        draw.line((start[0], start[1] - 28, end[0], end[1] - 28), fill=rgba(LEATHER, 220), width=10)
        draw.line((start[0], start[1] + 28, end[0], end[1] + 28), fill=rgba(LEATHER, 220), width=10)
        for t in range(0, 101, 20):
            x = round(start[0] + (end[0] - start[0]) * t / 100)
            y = round(start[1] + (end[1] - start[1]) * t / 100)
            draw.rectangle((x - 9, y - 42, x + 9, y + 42), fill=rgba(SHADOW, 220), outline=rgba(DARK_INK, 130), width=2)
            draw.line((x - 5, y - 38, x - 5, y + 38), fill=rgba(BONE, 45), width=1)
    if as_overlay:
        return


def building_piece(asset: dict, size: int, rng: random.Random) -> Image.Image:
    slug = asset["id"]
    role = asset.get("modular_role", "")
    image = transparent(size)
    draw = ImageDraw.Draw(image, "RGBA")

    if "floor" in slug or "roof" in slug or "courtyard" in slug:
        if "roof_thatch" in slug:
            image = colorized_texture(size, rng, (126, 96, 48), (207, 166, 83))
            for y in range(34, size, 34):
                draw = ImageDraw.Draw(image, "RGBA")
                draw.line((0, y, size, y + rng.randrange(-8, 9)), fill=rgba(SHADOW, 62), width=3)
        elif "roof_wood" in slug or "wood" in slug:
            image = colorized_texture(size, rng, (80, 50, 28), (161, 107, 58))
            draw = ImageDraw.Draw(image, "RGBA")
            for x in range(22, size, 44):
                draw.line((x, 0, x + rng.randrange(-8, 9), size), fill=rgba(DARK_INK, 58), width=3)
        else:
            image = terrain_base({"id": "terrain_city_castle_floor_tile", "subcategory": "city_terrain", "modular_role": "tile"}, size, rng)
        return image

    if "wall" in slug or "battlement" in slug or "partition" in slug:
        color = rgba(LEATHER if "wood" in slug or "stable" in slug else IRON, 235)
        if role == "corner":
            draw.rounded_rectangle((60, 218, size - 50, 294), radius=10, fill=color, outline=rgba(DARK_INK, 170), width=5)
            draw.rounded_rectangle((218, 60, 294, size - 50), radius=10, fill=color, outline=rgba(DARK_INK, 170), width=5)
        else:
            y1, y2 = 208, 304
            if "damaged" in slug or "broken" in slug:
                draw.rounded_rectangle((20, y1, 210, y2), radius=10, fill=color, outline=rgba(DARK_INK, 170), width=5)
                draw.rounded_rectangle((302, y1, size - 20, y2), radius=10, fill=color, outline=rgba(DARK_INK, 170), width=5)
                for _index in range(12):
                    draw_blob(draw, (rng.randrange(210, 302), rng.randrange(y1 - 18, y2 + 18)), rng.randrange(5, 15), rng, rgba(IRON, 180), rgba(DARK_INK, 85), width=1, sides=6)
            else:
                draw.rounded_rectangle((20, y1, size - 20, y2), radius=10, fill=color, outline=rgba(DARK_INK, 170), width=5)
        for x in range(52, size - 30, 70):
            draw.line((x, 214, x + rng.randrange(-4, 5), 298), fill=rgba(SHADOW, 82), width=3)
        return image

    if "door" in slug or "gate" in slug or "portcullis" in slug:
        fill = rgba(LEATHER, 235)
        draw.rounded_rectangle((150, 150, 362, 362), radius=18, fill=fill, outline=rgba(DARK_INK, 170), width=6)
        if "open" in slug:
            draw.polygon(((156, 156), (300, 112), (300, 318), (156, 362)), fill=rgba(LEATHER, 205), outline=rgba(DARK_INK, 150))
        if "portcullis" in slug:
            for x in range(176, 342, 34):
                draw.line((x, 128, x, 384), fill=rgba(IRON, 230), width=8)
            for y in range(172, 352, 58):
                draw.line((142, y, 370, y), fill=rgba(IRON, 210), width=6)
        return image

    if "window" in slug:
        draw.rounded_rectangle((164, 176, 348, 336), radius=50 if "arched" in slug else 10, fill=rgba(STEEL_BLUE, 145), outline=rgba(DARK_INK, 170), width=7)
        draw.line((256, 184, 256, 328), fill=rgba(DARK_INK, 125), width=5)
        draw.line((174, 256, 338, 256), fill=rgba(DARK_INK, 125), width=5)
        return image

    if "tower" in slug:
        if "round" in slug:
            draw.ellipse((96, 96, 416, 416), fill=rgba(IRON, 235), outline=rgba(DARK_INK, 185), width=7)
        else:
            draw.rounded_rectangle((106, 106, 406, 406), radius=12, fill=rgba(IRON, 235), outline=rgba(DARK_INK, 185), width=7)
        for angle in range(0, 360, 45):
            x = 256 + math.cos(math.radians(angle)) * 142
            y = 256 + math.sin(math.radians(angle)) * 142
            draw.rectangle((x - 16, y - 16, x + 16, y + 16), fill=rgba(BONE, 180), outline=rgba(DARK_INK, 95))
        return image

    if "stair" in slug:
        for index in range(8):
            y = 112 + index * 34
            draw.rectangle((124 + index * 8, y, 388 - index * 8, y + 20), fill=rgba(IRON, 205), outline=rgba(DARK_INK, 90), width=2)
        return image

    if "drawbridge" in slug:
        draw.rounded_rectangle((80, 150, 432, 362), radius=18, fill=rgba(LEATHER, 230), outline=rgba(DARK_INK, 170), width=6)
        for x in range(112, 426, 46):
            draw.line((x, 156, x + rng.randrange(-5, 6), 356), fill=rgba(SHADOW, 120), width=3)
        return image

    return item_or_prop(asset, size, rng)


def building_starter(asset: dict, size: int, rng: random.Random) -> Image.Image:
    image = transparent(size)
    draw = ImageDraw.Draw(image, "RGBA")
    slug = asset["id"]
    if "fortress" in slug:
        draw.rounded_rectangle((86, 86, 426, 426), radius=18, fill=rgba(IRON, 235), outline=rgba(DARK_INK, 190), width=8)
        draw.rounded_rectangle((146, 146, 366, 366), radius=10, fill=rgba((84, 78, 68), 220), outline=rgba(DARK_INK, 130), width=4)
        if "gatehouse" in slug:
            draw.rectangle((218, 70, 294, 212), fill=rgba(LEATHER, 230), outline=rgba(DARK_INK, 160), width=5)
            draw.ellipse((72, 72, 180, 180), fill=rgba(IRON, 230), outline=rgba(DARK_INK, 150), width=5)
            draw.ellipse((332, 72, 440, 180), fill=rgba(IRON, 230), outline=rgba(DARK_INK, 150), width=5)
    else:
        roof = rgba((143, 89, 44), 238)
        if "church" in slug:
            draw.polygon(((256, 56), (418, 190), (366, 432), (146, 432), (94, 190)), fill=rgba(IRON, 232), outline=rgba(DARK_INK, 180))
            draw.rectangle((224, 76, 288, 170), fill=rgba(IRON, 235), outline=rgba(DARK_INK, 160), width=5)
        elif "stable" in slug:
            draw.rounded_rectangle((78, 126, 434, 386), radius=14, fill=rgba(LEATHER, 225), outline=rgba(DARK_INK, 170), width=6)
            for x in (170, 256, 342):
                draw.line((x, 142, x, 378), fill=rgba(DARK_INK, 120), width=4)
        else:
            if "tavern" in slug or "town_hall" in slug:
                draw.rounded_rectangle((68, 112, 444, 400), radius=18, fill=roof, outline=rgba(DARK_INK, 180), width=7)
            else:
                draw.rounded_rectangle((96, 142, 416, 370), radius=18, fill=roof, outline=rgba(DARK_INK, 180), width=7)
            draw.rectangle((226, 326, 286, 412), fill=rgba(LEATHER, 230), outline=rgba(DARK_INK, 150), width=4)
        for _index in range(16):
            y = rng.randrange(130, 392)
            draw.line((92, y, 420, y + rng.randrange(-9, 10)), fill=rgba(SHADOW, 55), width=2)
    return image


def item_or_prop(asset: dict, size: int, rng: random.Random) -> Image.Image:
    slug = asset["id"]
    image = transparent(size)
    draw = ImageDraw.Draw(image, "RGBA")

    def shadow_ellipse(box):
        draw.ellipse(box, fill=(0, 0, 0, 38))

    shadow_ellipse((132, 354, 380, 410))

    if "chest" in slug:
        draw.rounded_rectangle((142, 192, 370, 332), radius=18, fill=rgba(LEATHER, 238), outline=rgba(DARK_INK, 180), width=7)
        draw.rectangle((142, 242, 370, 276), fill=rgba(MUTED_GOLD, 225), outline=rgba(DARK_INK, 120), width=3)
        draw.rectangle((238, 214, 274, 292), fill=rgba(IRON, 230), outline=rgba(DARK_INK, 130), width=3)
        if "open" in slug:
            draw.polygon(((150, 192), (362, 192), (338, 136), (174, 136)), fill=rgba(LEATHER, 230), outline=rgba(DARK_INK, 150))
            for _index in range(20):
                x = rng.randrange(178, 338)
                y = rng.randrange(220, 286)
                draw.ellipse((x - 6, y - 4, x + 6, y + 4), fill=rgba(MUTED_GOLD, 230), outline=rgba(DARK_INK, 45))
    elif "coin" in slug or "treasure" in slug:
        if "sack" in slug:
            draw.ellipse((170, 164, 342, 360), fill=rgba((148, 104, 58), 235), outline=rgba(DARK_INK, 160), width=6)
            draw.line((196, 180, 316, 180), fill=rgba(DARK_INK, 130), width=7)
        for _index in range(34):
            x = rng.randrange(174, 340)
            y = rng.randrange(240, 342)
            draw.ellipse((x - 9, y - 6, x + 9, y + 6), fill=rgba(MUTED_GOLD, 235), outline=rgba(DARK_INK, 65))
    elif "sword" in slug:
        draw.line((152, 340, 350, 142), fill=rgba(IRON, 245), width=18)
        draw.line((152, 340, 350, 142), fill=rgba(BONE, 160), width=5)
        draw.line((136, 324, 186, 374), fill=rgba(MUTED_GOLD, 240), width=13)
    elif "shield" in slug or "protected" in slug:
        draw.polygon(((256, 120), (356, 168), (330, 330), (256, 390), (182, 330), (156, 168)), fill=rgba(IRON, 232), outline=rgba(DARK_INK, 180))
        draw.polygon(((256, 148), (322, 184), (304, 312), (256, 356), (208, 312), (190, 184)), fill=rgba(ROYAL_BLUE, 150))
    elif "scroll" in slug:
        draw.rounded_rectangle((130, 170, 382, 326), radius=22, fill=rgba(PARCHMENT, 242), outline=rgba(DARK_INK, 150), width=5)
        draw.ellipse((116, 164, 174, 332), fill=rgba(BONE, 235), outline=rgba(DARK_INK, 130), width=4)
        draw.ellipse((338, 164, 396, 332), fill=rgba(BONE, 235), outline=rgba(DARK_INK, 130), width=4)
    elif "book" in slug:
        draw.rounded_rectangle((154, 130, 358, 374), radius=18, fill=rgba(DULL_VIOLET, 235), outline=rgba(DARK_INK, 170), width=6)
        draw.line((256, 134, 256, 370), fill=rgba(DARK_INK, 90), width=5)
        draw.rectangle((190, 188, 322, 230), fill=rgba(MUTED_GOLD, 150), outline=rgba(DARK_INK, 60))
    elif "key" in slug:
        draw.ellipse((144, 180, 238, 274), outline=rgba(MUTED_GOLD, 240), width=18)
        draw.line((226, 256, 368, 358), fill=rgba(MUTED_GOLD, 240), width=17)
        draw.line((326, 326, 356, 296), fill=rgba(MUTED_GOLD, 230), width=11)
    elif "torch" in slug or "campfire" in slug:
        draw.line((232, 350, 292, 186), fill=rgba(LEATHER, 235), width=24)
        draw.polygon(((256, 110), (304, 198), (256, 244), (208, 198)), fill=rgba(OCHRE, 232), outline=rgba(DEEP_RED, 150))
        draw.polygon(((256, 138), (282, 198), (254, 222), (228, 196)), fill=rgba(MUTED_GOLD, 235))
    elif "lantern" in slug:
        draw.rounded_rectangle((190, 176, 322, 342), radius=22, fill=rgba(IRON, 225), outline=rgba(DARK_INK, 170), width=6)
        draw.rectangle((214, 212, 298, 314), fill=rgba(OCHRE, 145), outline=rgba(DARK_INK, 85), width=3)
        draw.arc((208, 122, 304, 218), 190, 350, fill=rgba(DARK_INK, 170), width=8)
    elif "barrel" in slug:
        for offset in ((0, 0), (46, -28), (-42, -16)) if "stack" in slug else ((0, 0),):
            ox, oy = offset
            draw.ellipse((176 + ox, 142 + oy, 336 + ox, 198 + oy), fill=rgba(LEATHER, 235), outline=rgba(DARK_INK, 150), width=4)
            draw.rounded_rectangle((176 + ox, 170 + oy, 336 + ox, 342 + oy), radius=24, fill=rgba(LEATHER, 230), outline=rgba(DARK_INK, 150), width=5)
            draw.ellipse((176 + ox, 312 + oy, 336 + ox, 368 + oy), fill=rgba(SHADOW, 205), outline=rgba(DARK_INK, 130), width=4)
    elif "crate" in slug:
        offsets = ((0, 0), (58, -46), (-48, -24)) if "stack" in slug else ((0, 0),)
        for ox, oy in offsets:
            draw.rectangle((166 + ox, 176 + oy, 346 + ox, 344 + oy), fill=rgba(LEATHER, 228), outline=rgba(DARK_INK, 155), width=6)
            draw.line((176 + ox, 186 + oy, 336 + ox, 334 + oy), fill=rgba(DARK_INK, 80), width=4)
            draw.line((336 + ox, 186 + oy, 176 + ox, 334 + oy), fill=rgba(DARK_INK, 80), width=4)
    elif "rope" in slug:
        for inset in range(0, 86, 16):
            draw.ellipse((164 + inset, 160 + inset, 348 - inset, 344 - inset), outline=rgba((156, 116, 66), 235), width=13)
    elif "trap" in slug:
        draw.polygon(((156, 340), (356, 340), (322, 198), (190, 198)), fill=rgba(IRON, 210), outline=rgba(DARK_INK, 170))
        for x in range(188, 326, 34):
            draw.polygon(((x, 198), (x + 18, 150), (x + 36, 198)), fill=rgba(BONE, 230), outline=rgba(DARK_INK, 110))
    elif "lever" in slug:
        draw.ellipse((172, 294, 340, 374), fill=rgba(IRON, 225), outline=rgba(DARK_INK, 150), width=5)
        draw.line((254, 310, 322, 154), fill=rgba(LEATHER, 235), width=18)
        draw.ellipse((296, 126, 350, 180), fill=rgba(DEEP_RED, 230), outline=rgba(DARK_INK, 150), width=4)
    elif "runic" in slug or "crystal" in slug or "potion" in slug:
        fill = rgba(ARCANE_TEAL, 225)
        if "potion" in slug:
            draw.rounded_rectangle((204, 176, 308, 362), radius=38, fill=rgba(ROYAL_BLUE, 170), outline=rgba(DARK_INK, 160), width=6)
            draw.rectangle((226, 124, 286, 190), fill=rgba(BONE, 225), outline=rgba(DARK_INK, 120), width=4)
        elif "crystal" in slug:
            draw.polygon(((256, 92), (336, 230), (294, 386), (214, 386), (176, 230)), fill=fill, outline=rgba(DARK_INK, 165))
            draw.line((256, 92, 256, 384), fill=rgba(BONE, 70), width=5)
        else:
            draw_blob(draw, (256, 260), 108, rng, rgba(IRON, 225), rgba(DARK_INK, 160), width=6, sides=8)
            draw.ellipse((224, 226, 288, 290), outline=rgba(ARCANE_TEAL, 185), width=8)
    elif "food_table" in slug or "table_chairs" in slug:
        draw.rounded_rectangle((128, 178, 384, 326), radius=24, fill=rgba(LEATHER, 232), outline=rgba(DARK_INK, 170), width=6)
        for x, y in ((190, 226), (256, 246), (318, 224)):
            draw.ellipse((x - 22, y - 16, x + 22, y + 16), fill=rgba(BONE, 230), outline=rgba(DARK_INK, 85))
    elif "supply" in slug or "sack" in slug or "hay" in slug:
        color = rgba((175, 135, 68), 232)
        draw.ellipse((164, 158, 348, 360), fill=color, outline=rgba(DARK_INK, 150), width=6)
        draw.line((190, 184, 320, 184), fill=rgba(DARK_INK, 100), width=6)
    elif "well" in slug or "fountain" in slug:
        draw.ellipse((126, 126, 386, 386), fill=rgba(IRON, 230), outline=rgba(DARK_INK, 170), width=7)
        draw.ellipse((176, 176, 336, 336), fill=rgba(STEEL_BLUE, 165), outline=rgba(DARK_INK, 120), width=5)
    elif "wagon" in slug:
        draw.rounded_rectangle((118, 172, 394, 328), radius=20, fill=rgba(LEATHER, 230), outline=rgba(DARK_INK, 165), width=6)
        if "broken" in slug:
            draw.line((126, 178, 386, 320), fill=rgba(DARK_INK, 120), width=8)
        for x in (146, 366):
            draw.ellipse((x - 34, 318, x + 34, 386), fill=rgba(SHADOW, 230), outline=rgba(DARK_INK, 165), width=5)
    elif "sign" in slug:
        draw.line((256, 138, 256, 384), fill=rgba(LEATHER, 235), width=18)
        draw.rounded_rectangle((134, 166, 378, 236), radius=12, fill=rgba(LEATHER, 230), outline=rgba(DARK_INK, 160), width=5)
    elif "altar" in slug or "pew" in slug or "counter" in slug or "trough" in slug or "stall" in slug or "tent" in slug:
        if "tent" in slug:
            draw.polygon(((104, 340), (256, 118), (408, 340)), fill=rgba(BONE, 230), outline=rgba(DARK_INK, 160))
            draw.line((256, 118, 256, 340), fill=rgba(DARK_INK, 90), width=4)
        else:
            draw.rounded_rectangle((104, 190, 408, 318), radius=16, fill=rgba(LEATHER if "pew" in slug or "counter" in slug or "trough" in slug else IRON, 232), outline=rgba(DARK_INK, 160), width=6)
    else:
        draw_blob(draw, (256, 256), 92, rng, rgba(LEATHER, 230), rgba(DARK_INK, 160), width=6, sides=9)
    return image


def marker_or_status(asset: dict, size: int, rng: random.Random) -> Image.Image:
    slug = asset["id"]
    image = transparent(size)
    draw = ImageDraw.Draw(image, "RGBA")
    cx = cy = size // 2
    scale = size / 256

    def s(value: int) -> int:
        return round(value * scale)

    def line(points, fill, width=6):
        draw.line([(s(x), s(y)) for x, y in points], fill=fill, width=s(width), joint="curve")

    if slug.startswith("marker_"):
        color = rgba(OCHRE, 235)
        if "danger" in slug or "trap" in slug or "blocked" in slug:
            color = rgba(DEEP_RED, 235)
        elif "treasure" in slug:
            color = rgba(MUTED_GOLD, 235)
        elif "secret" in slug:
            color = rgba(DULL_VIOLET, 235)
        elif "npc" in slug or "quest" in slug:
            color = rgba(ROYAL_BLUE, 235)
        draw.ellipse((s(58), s(42), s(198), s(182)), fill=color, outline=rgba(DARK_INK, 175), width=s(6))
        draw.polygon(((cx, s(226)), (s(98), s(158)), (s(158), s(158))), fill=color, outline=rgba(DARK_INK, 175))
        if "entrance" in slug:
            draw.arc((s(86), s(82), s(170), s(180)), 180, 360, fill=rgba(DARK_INK, 185), width=s(8))
            draw.rectangle((s(100), s(128), s(156), s(180)), outline=rgba(DARK_INK, 185), width=s(6))
        elif "exit" in slug:
            line([(88, 128), (164, 128)], rgba(DARK_INK, 190), 8)
            draw.polygon(((s(164), s(96)), (s(206), s(128)), (s(164), s(160))), fill=rgba(DARK_INK, 190))
        elif "objective" in slug:
            draw.ellipse((s(92), s(78), s(164), s(150)), outline=rgba(DARK_INK, 190), width=s(7))
            draw.ellipse((s(114), s(100), s(142), s(128)), fill=rgba(DARK_INK, 190))
        elif "danger" in slug:
            draw.polygon(((s(128), s(74)), (s(180), s(158)), (s(76), s(158))), fill=rgba(BONE, 225), outline=rgba(DARK_INK, 170))
            line([(128, 100), (128, 138)], rgba(DEEP_RED, 220), 7)
        elif "treasure" in slug:
            draw.rounded_rectangle((s(86), s(100), s(170), s(154)), radius=s(8), fill=rgba(LEATHER, 230), outline=rgba(DARK_INK, 150), width=s(4))
            draw.rectangle((s(86), s(122), s(170), s(136)), fill=rgba(MUTED_GOLD, 220))
        elif "npc" in slug:
            draw.ellipse((s(108), s(80), s(148), s(120)), fill=rgba(BONE, 230), outline=rgba(DARK_INK, 140), width=s(4))
            draw.ellipse((s(92), s(122), s(164), s(170)), fill=rgba(DARK_INK, 170))
        elif "blocked" in slug:
            for y in (92, 126, 160):
                line([(82, y), (174, y)], rgba(BONE, 230), 9)
        elif "secret" in slug:
            draw.ellipse((s(78), s(96), s(178), s(154)), outline=rgba(BONE, 230), width=s(7))
            draw.ellipse((s(116), s(112), s(140), s(136)), fill=rgba(BONE, 230))
        elif "camp" in slug:
            draw.polygon(((s(84), s(160)), (s(128), s(84)), (s(172), s(160))), fill=rgba(BONE, 230), outline=rgba(DARK_INK, 120))
        elif "trap" in slug:
            for x in range(88, 164, 28):
                draw.polygon(((s(x), s(156)), (s(x + 14), s(98)), (s(x + 28), s(156))), fill=rgba(BONE, 230), outline=rgba(DARK_INK, 120))
        else:
            draw.ellipse((s(106), s(92), s(150), s(136)), fill=rgba(BONE, 230), outline=rgba(DARK_INK, 120), width=s(4))
        return image

    color = rgba(ARCANE_TEAL, 230)
    if any(key in slug for key in ("burning", "bleeding", "cursed", "dead")):
        color = rgba(DEEP_RED, 232)
    elif any(key in slug for key in ("frozen", "protected", "blessed")):
        color = rgba(ROYAL_BLUE, 232)
    draw.ellipse((s(38), s(38), s(218), s(218)), fill=rgba(PARCHMENT, 205), outline=rgba(DARK_INK, 165), width=s(6))
    if "poisoned" in slug:
        draw.polygon(((s(128), s(62)), (s(174), s(142)), (s(128), s(196)), (s(82), s(142))), fill=color, outline=rgba(DARK_INK, 130))
    elif "stunned" in slug or "concentrating" in slug:
        for radius in (30, 54, 78):
            draw.arc((cx - s(radius), cy - s(radius), cx + s(radius), cy + s(radius)), 25, 310, fill=color, width=s(8))
    elif "paralyzed" in slug:
        for x in (92, 128, 164):
            line([(x, 72), (x, 184)], color, 10)
        line([(76, 118), (180, 118)], rgba(DARK_INK, 135), 8)
    elif "prone" in slug:
        line([(72, 160), (184, 160)], color, 18)
        draw.ellipse((s(58), s(146), s(94), s(182)), fill=color, outline=rgba(DARK_INK, 120), width=s(4))
    elif "bleeding" in slug:
        for x, y in ((110, 78), (148, 104), (128, 146)):
            draw.polygon(((s(x), s(y)), (s(x + 24), s(y + 46)), (s(x), s(y + 74)), (s(x - 24), s(y + 46))), fill=color, outline=rgba(DARK_INK, 110))
    elif "burning" in slug:
        draw.polygon(((s(128), s(54)), (s(178), s(146)), (s(128), s(202)), (s(78), s(146))), fill=color, outline=rgba(DARK_INK, 120))
        draw.polygon(((s(128), s(92)), (s(152), s(150)), (s(126), s(180)), (s(104), s(148))), fill=rgba(OCHRE, 235))
    elif "frozen" in slug:
        for angle in range(0, 180, 30):
            dx = math.cos(math.radians(angle)) * 78
            dy = math.sin(math.radians(angle)) * 78
            draw.line((cx - dx, cy - dy, cx + dx, cy + dy), fill=color, width=s(7))
    elif "frightened" in slug:
        draw.ellipse((s(86), s(76), s(170), s(182)), fill=color, outline=rgba(DARK_INK, 130), width=s(5))
        draw.ellipse((s(104), s(108), s(118), s(124)), fill=rgba(DARK_INK, 180))
        draw.ellipse((s(138), s(108), s(152), s(124)), fill=rgba(DARK_INK, 180))
        draw.arc((s(104), s(130), s(152), s(170)), 200, 340, fill=rgba(DARK_INK, 180), width=s(5))
    elif "invisible" in slug:
        draw.ellipse((s(78), s(80), s(178), s(178)), outline=color, width=s(7))
        for x in range(76, 180, 28):
            line([(x, 84), (x + 40, 172)], rgba(PARCHMENT, 180), 8)
    elif "protected" in slug:
        draw.polygon(((s(128), s(62)), (s(184), s(90)), (s(170), s(166)), (s(128), s(200)), (s(86), s(166)), (s(72), s(90))), fill=color, outline=rgba(DARK_INK, 130))
    elif "cursed" in slug:
        for radius in (28, 54, 78):
            draw.arc((cx - s(radius), cy - s(radius), cx + s(radius), cy + s(radius)), 120, 400, fill=color, width=s(7))
        draw.line((s(88), s(88), s(174), s(174)), fill=rgba(DARK_INK, 150), width=s(8))
    elif "blessed" in slug:
        for angle in range(0, 360, 45):
            draw.line((cx, cy, cx + math.cos(math.radians(angle)) * s(82), cy + math.sin(math.radians(angle)) * s(82)), fill=rgba(MUTED_GOLD, 220), width=s(7))
        draw.ellipse((s(98), s(98), s(158), s(158)), fill=rgba(MUTED_GOLD, 230), outline=rgba(DARK_INK, 100))
    else:
        draw.ellipse((s(92), s(92), s(164), s(164)), fill=color, outline=rgba(DARK_INK, 130), width=s(5))
        line([(96, 164), (160, 96)], rgba(DARK_INK, 150), 7)
    return image


def scene_map(asset: dict, size: tuple[int, int], rng: random.Random, imagegen_source: Path | None) -> Image.Image:
    slug = asset["id"]
    width, height = size
    if slug == "scene_forest_village_editable" and imagegen_source and imagegen_source.exists():
        image = Image.open(imagegen_source).convert("RGBA")
        source_ratio = image.width / image.height
        target_ratio = width / height
        if source_ratio > target_ratio:
            new_width = round(image.height * target_ratio)
            left = (image.width - new_width) // 2
            image = image.crop((left, 0, left + new_width, image.height))
        else:
            new_height = round(image.width / target_ratio)
            top = (image.height - new_height) // 2
            image = image.crop((0, top, image.width, top + new_height))
        return force_opaque(image.resize((width, height), resampling_filter()))

    if "swamp" in slug:
        image = colorized_texture(width, rng, (34, 49, 36), (96, 100, 61)).resize((width, height), resampling_filter())
        draw = ImageDraw.Draw(image, "RGBA")
        for _index in range(18):
            draw_blob(draw, (rng.randrange(120, width - 120), rng.randrange(80, height - 80)), rng.randrange(80, 210), rng, rgba(STEEL_BLUE, 115), rgba(DARK_INK, 45), width=2, sides=16)
        points = [(80, 1320), (340, 1120), (510, 1040), (540, 850), (800, 780), (720, 560), (1010, 470), (1280, 590), (1450, 430), (1820, 310)]
        draw_path(image, points, rgba((111, 84, 48), 180), 72)
        for _index in range(120):
            x = rng.randrange(width)
            y = rng.randrange(height)
            draw.line((x, y, x + rng.randrange(-8, 9), y - rng.randrange(20, 58)), fill=rgba(FOREST, 78), width=2)
    elif "fortress" in slug:
        image = colorized_texture(width, rng, (62, 68, 46), (138, 122, 75)).resize((width, height), resampling_filter())
        draw = ImageDraw.Draw(image, "RGBA")
        draw.rounded_rectangle((330, 210, 1720, 1260), radius=24, fill=rgba(IRON, 220), outline=rgba(DARK_INK, 190), width=18)
        draw.rounded_rectangle((470, 350, 1580, 1120), radius=20, fill=rgba((119, 108, 83), 220), outline=rgba(DARK_INK, 130), width=10)
        for x, y in ((300, 180), (1660, 180), (300, 1160), (1660, 1160)):
            draw.ellipse((x, y, x + 160, y + 160), fill=rgba(IRON, 232), outline=rgba(DARK_INK, 165), width=10)
        draw.rounded_rectangle((860, 520, 1188, 855), radius=18, fill=rgba((78, 73, 64), 232), outline=rgba(DARK_INK, 170), width=10)
        draw.rectangle((896, 1120, 1152, 1340), fill=rgba(LEATHER, 230), outline=rgba(DARK_INK, 150), width=8)
        draw_path(image, [(1024, height + 40), (1024, 1320), (1024, 1120)], rgba((126, 91, 52), 170), 86)
    else:
        image = colorized_texture(width, rng, (43, 71, 34), (130, 124, 64)).resize((width, height), resampling_filter())
        draw = ImageDraw.Draw(image, "RGBA")
        if "forest_road" in slug:
            draw_path(image, [(-40, 840), (360, 750), (760, 790), (1120, 640), (1500, 700), (width + 40, 520)], rgba((127, 91, 53), 170), 120)
            draw_path(image, [(760, 790), (790, 1040), (990, height + 30)], rgba((127, 91, 53), 135), 76)
        else:
            draw_path(image, [(0, 820), (520, 760), (1010, 790), (width, 720)], rgba((127, 91, 53), 170), 120)
        for _index in range(180):
            x = rng.randrange(width)
            y = rng.randrange(height)
            if rng.random() < 0.25:
                continue
            radius = rng.randrange(24, 66)
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=rgba(rng.choice((FOREST, (58, 92, 45), (42, 75, 38))), 170), outline=rgba(DARK_INK, 35))
        if "village" in slug:
            for x, y, w, h in ((650, 520, 180, 120), (910, 480, 240, 150), (1220, 620, 220, 140), (730, 890, 200, 120), (1060, 880, 250, 150)):
                draw.rounded_rectangle((x, y, x + w, y + h), radius=14, fill=rgba(LEATHER, 220), outline=rgba(DARK_INK, 150), width=6)
            draw.ellipse((980, 710, 1080, 810), fill=rgba(IRON, 225), outline=rgba(DARK_INK, 150), width=6)
    draw_ink_grain(image, rng, 1800, rgba(DARK_INK, 24))
    return force_opaque(image)


def generate_asset(asset: dict, imagegen_scene_source: Path | None) -> Image.Image:
    slug = asset["id"]
    rng = seeded_random(slug)
    asset_type = asset["type"]
    if asset_type == "CITY_OR_WORLD_MAP":
        return scene_map(asset, (2048, 1536), rng, imagegen_scene_source)
    if asset_type in {"MAP_MARKER", "STATUS_MARKER"}:
        return marker_or_status(asset, 256, rng)
    size = 512
    if asset_type in {"PROP_TOKEN", "ITEM_SPRITE"}:
        return item_or_prop(asset, size, rng)
    if asset.get("subcategory") == "building_starter":
        return building_starter(asset, size, rng)
    if asset.get("subcategory", "").endswith("building_piece") or asset["id"].startswith("building_"):
        return building_piece(asset, size, rng)
    return terrain_base(asset, size, rng)


def rel_media_path(asset: dict) -> str:
    return f"sprites/original/{asset['category']}/{asset['id']}.png"


def output_path(media_root: Path, asset: dict) -> Path:
    return media_root / rel_media_path(asset)


def update_db(db_path: Path, rows: list[tuple[str, str, int, int]]) -> int:
    if not db_path.exists():
        return 0
    conn = sqlite3.connect(db_path)
    try:
        total = 0
        for slug, image_path, width, height in rows:
            cur = conn.execute(
                "update sprites_spriteasset set OriginalImage = ?, Width = ?, Height = ? where Slug = ?",
                (image_path, width, height, slug),
            )
            total += cur.rowcount
        conn.commit()
        return total
    finally:
        conn.close()


def latest_imagegen_file() -> Path | None:
    generated_dir = Path.home() / ".codex" / "generated_images"
    if not generated_dir.exists():
        return None
    files = [path for path in generated_dir.rglob("*") if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}]
    if not files:
        return None
    return max(files, key=lambda path: path.stat().st_mtime)


def parse_args(argv: list[str]) -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("slugs", nargs="*", help="Optional subset of slugs to generate.")
    parser.add_argument("--media-root", type=Path, default=root / "dd3esheet" / "media")
    parser.add_argument("--db", type=Path, default=root / "dd3esheet" / "db.sqlite3")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--no-db", action="store_true")
    parser.add_argument("--imagegen-scene-source", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    assets = load_assets(repo_root())
    if args.slugs:
        wanted = set(args.slugs)
        assets = [asset for asset in assets if asset["id"] in wanted]
        missing = sorted(wanted.difference({asset["id"] for asset in assets}))
        if missing:
            print(f"error: unknown slug(s): {', '.join(missing)}", file=sys.stderr)
            return 1

    updates: list[tuple[str, str, int, int]] = []
    generated = 0
    skipped = 0
    for asset in assets:
        path = output_path(args.media_root, asset)
        if path.exists() and not args.overwrite:
            skipped += 1
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        image = generate_asset(asset, args.imagegen_scene_source)
        image.save(path)
        updates.append((asset["id"], rel_media_path(asset), image.width, image.height))
        generated += 1
        print(f"{asset['id']}: {image.width}x{image.height} -> {path}")

    updated = 0 if args.no_db else update_db(args.db, updates)
    print(f"generated={generated} skipped={skipped} db_updated={updated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
