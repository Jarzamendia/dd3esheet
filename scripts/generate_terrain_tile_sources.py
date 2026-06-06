r"""Generate procedural full-bleed sources for tabletop terrain tiles.

The outputs are deterministic 512x512 opaque PNG sources named
``<slug>-fullbleed-source.png``. Run ``fill_terrain_tile.py`` afterwards to write
the served ``<slug>.png`` files and update SpriteAsset dimensions when needed.
Slugs listed in ``CURATED_IMAGEGEN_SLUGS`` use hand-selected generated sources
and are intentionally not overwritten by this procedural script.

Example from the repo root:

  python scripts/generate_terrain_tile_sources.py --overwrite
  python scripts/fill_terrain_tile.py --overwrite
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageOps
except ImportError as exc:  # pragma: no cover - exercised manually.
    raise SystemExit("Pillow is required. Install it with: python -m pip install pillow") from exc


CURATED_IMAGEGEN_SLUGS = (
    "river_segment",
    "water_shore_edge",
    "dense_woods_patch",
    "dirt_road_straight",
    "rocky_ground_patch",
    "swamp_muck_tile",
    "lava_flow_segment",
    "cobblestone_street",
)

DEFAULT_SLUGS = (
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
DEFAULT_TILE_SUBDIR = Path("sprites/original/map_tile")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resampling_filter() -> int:
    return getattr(Image, "Resampling", Image).BICUBIC


def seeded_random(slug: str) -> random.Random:
    return random.Random(f"dd3e-terrain:{slug}:v1")


def noise_layer(size: int, rng: random.Random, cells: int) -> Image.Image:
    cell_count = max(2, math.ceil(size / cells) + 2)
    values = [rng.randrange(256) for _index in range(cell_count * cell_count)]
    image = Image.new("L", (cell_count, cell_count))
    image.putdata(values)
    return image.resize((size, size), resampling_filter())


def fractal_noise(size: int, rng: random.Random) -> Image.Image:
    result = Image.new("L", (size, size), 128)
    for cells, blend in ((96, 0.45), (48, 0.35), (20, 0.25), (8, 0.12)):
        result = Image.blend(result, noise_layer(size, rng, cells), blend)
    return result.filter(ImageFilter.GaussianBlur(0.6))


def colorized_texture(size: int, rng: random.Random, dark: tuple[int, int, int], light: tuple[int, int, int]) -> Image.Image:
    return ImageOps.colorize(fractal_noise(size, rng), black=dark, white=light).convert("RGBA")


def force_opaque(image: Image.Image) -> Image.Image:
    rgb = image.convert("RGB")
    return Image.merge("RGBA", (*rgb.split(), Image.new("L", rgb.size, 255)))


def composite(base: Image.Image, overlay: Image.Image, mask: Image.Image) -> Image.Image:
    out = base.copy()
    out.paste(overlay, (0, 0), mask)
    return out


def band_mask(
    size: int,
    rng: random.Random,
    *,
    center_y: float,
    width: float,
    softness: float,
    wobble: float,
) -> Image.Image:
    offsets = [rng.uniform(-wobble, wobble) for _index in range(size // 32 + 4)]
    values: list[int] = []
    half = width / 2
    for y in range(size):
        for x in range(size):
            index = min(len(offsets) - 2, max(0, x // 32))
            frac = (x % 32) / 32
            offset = offsets[index] * (1 - frac) + offsets[index + 1] * frac
            wave = math.sin(x / 54 + offsets[index] / 10) * wobble * 0.35
            distance = abs(y - (center_y + offset + wave))
            if distance <= half:
                value = 255
            elif distance >= half + softness:
                value = 0
            else:
                value = round(255 * (1 - (distance - half) / softness))
            values.append(value)
    mask = Image.new("L", (size, size))
    mask.putdata(values)
    return mask.filter(ImageFilter.GaussianBlur(2.2))


def shore_mask(size: int, rng: random.Random) -> Image.Image:
    values: list[int] = []
    offsets = [rng.uniform(-32, 32) for _index in range(size // 40 + 4)]
    for y in range(size):
        for x in range(size):
            index = min(len(offsets) - 2, max(0, x // 40))
            frac = (x % 40) / 40
            boundary = 238 + offsets[index] * (1 - frac) + offsets[index + 1] * frac
            boundary += math.sin(x / 45) * 16
            distance = y - boundary
            if distance >= 28:
                value = 255
            elif distance <= -28:
                value = 0
            else:
                value = round(255 * ((distance + 28) / 56))
            values.append(value)
    mask = Image.new("L", (size, size))
    mask.putdata(values)
    return mask.filter(ImageFilter.GaussianBlur(1.8))


def draw_ink_grain(image: Image.Image, rng: random.Random, count: int, color: tuple[int, int, int, int]) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    size = image.width
    for _index in range(count):
        x = rng.randrange(size)
        y = rng.randrange(size)
        radius = rng.choice((1, 1, 2, 2, 3))
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)


def draw_flow_lines(image: Image.Image, rng: random.Random, color: tuple[int, int, int, int], count: int) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    size = image.width
    for _index in range(count):
        y = rng.randrange(70, size - 70)
        points = []
        phase = rng.random() * math.tau
        for x in range(-24, size + 25, 24):
            points.append((x, y + math.sin(x / 58 + phase) * rng.uniform(3, 10)))
        draw.line(points, fill=color, width=rng.choice((1, 1, 2)), joint="curve")


def draw_jittered_horizontal(image: Image.Image, rng: random.Random, y: int, color: tuple[int, int, int, int], width: int) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    points = []
    phase = rng.random() * math.tau
    for x in range(-20, image.width + 21, 20):
        points.append((x, y + math.sin(x / 35 + phase) * rng.uniform(1.5, 5)))
    draw.line(points, fill=color, width=width, joint="curve")


def rect_inset(rect: tuple[int, int, int, int], amount: int) -> tuple[int, int, int, int]:
    left, top, right, bottom = rect
    return (left + amount, top + amount, right - amount, bottom - amount)


def draw_stone_room(
    image: Image.Image,
    rng: random.Random,
    rect: tuple[int, int, int, int],
    *,
    wall_width: int = 18,
    wall_color: tuple[int, int, int, int] = (45, 43, 39, 230),
    floor_color: tuple[int, int, int, int] = (116, 110, 95, 160),
) -> tuple[int, int, int, int]:
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rectangle(rect, fill=wall_color)
    inner = rect_inset(rect, wall_width)
    draw.rectangle(inner, fill=floor_color)
    for _index in range(80):
        x = rng.randrange(inner[0], inner[2])
        y = rng.randrange(inner[1], inner[3])
        draw.line((x, y, x + rng.randrange(-18, 19), y + rng.randrange(-18, 19)), fill=(38, 36, 32, 38), width=1)
    return inner


def draw_tree_cluster(image: Image.Image, rng: random.Random, count: int, *, avoid: tuple[int, int, int, int] | None = None) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    greens = ((37, 68, 33), (47, 82, 38), (61, 91, 42), (72, 94, 48))
    for _index in range(count):
        for _attempt in range(20):
            x = rng.randrange(-20, image.width + 20)
            y = rng.randrange(-20, image.height + 20)
            if avoid is None or not (avoid[0] <= x <= avoid[2] and avoid[1] <= y <= avoid[3]):
                break
        radius = rng.randrange(14, 34)
        color = rng.choice(greens)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*color, rng.randrange(135, 205)), outline=(19, 37, 21, 58))


def draw_boulders(image: Image.Image, rng: random.Random, count: int, color: tuple[int, int, int, int] = (96, 91, 78, 120)) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    for _index in range(count):
        x = rng.randrange(-20, image.width + 20)
        y = rng.randrange(-20, image.height + 20)
        radius = rng.randrange(8, 30)
        sides = rng.randrange(6, 9)
        points = []
        for side in range(sides):
            angle = math.tau * side / sides + rng.uniform(-0.2, 0.2)
            distance = radius * rng.uniform(0.65, 1.15)
            points.append((x + math.cos(angle) * distance, y + math.sin(angle) * distance))
        draw.polygon(points, fill=color, outline=(38, 36, 32, 70))


def draw_path(image: Image.Image, rng: random.Random, points: list[tuple[int, int]], color: tuple[int, int, int, int], width: int) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    for offset in range(width, 0, -8):
        draw.line(points, fill=(color[0], color[1], color[2], max(25, color[3] // 4)), width=offset + 8, joint="curve")
    draw.line(points, fill=color, width=width, joint="curve")


def draw_small_buildings(image: Image.Image, rng: random.Random, count: int, area: tuple[int, int, int, int]) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    for _index in range(count):
        x = rng.randrange(area[0], area[2])
        y = rng.randrange(area[1], area[3])
        w = rng.randrange(22, 58)
        h = rng.randrange(18, 46)
        fill = rng.choice(((91, 71, 52, 210), (112, 92, 61, 210), (78, 73, 64, 210)))
        draw.rectangle((x, y, x + w, y + h), fill=fill, outline=(35, 29, 23, 110), width=2)


def draw_planks(image: Image.Image, rng: random.Random, rect: tuple[int, int, int, int], *, horizontal: bool = True) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rectangle(rect, fill=(111, 80, 47, 230), outline=(46, 31, 20, 150), width=3)
    if horizontal:
        y = rect[1] + 12
        while y < rect[3]:
            draw_jittered_horizontal(image, rng, y, (42, 29, 20, 85), 2)
            y += rng.randrange(22, 35)
    else:
        x = rect[0] + 12
        while x < rect[2]:
            draw.line((x, rect[1], x + rng.randrange(-4, 5), rect[3]), fill=(42, 29, 20, 85), width=2)
            x += rng.randrange(22, 35)


def dirt_road_straight(size: int, rng: random.Random) -> Image.Image:
    grass = colorized_texture(size, rng, (62, 72, 35), (142, 128, 66))
    dirt = colorized_texture(size, rng, (88, 62, 41), (185, 148, 91))
    road = composite(grass, dirt, band_mask(size, rng, center_y=256, width=270, softness=58, wobble=22))
    for y in (210, 302):
        draw_jittered_horizontal(road, rng, y, (53, 39, 28, 110), rng.choice((3, 4)))
    draw_ink_grain(road, rng, 430, (43, 31, 22, 44))
    draw_ink_grain(road, rng, 180, (210, 178, 115, 34))
    return force_opaque(road)


def river_segment(size: int, rng: random.Random) -> Image.Image:
    bank = colorized_texture(size, rng, (54, 68, 42), (133, 119, 69))
    water = colorized_texture(size, rng, (31, 68, 78), (89, 132, 135))
    image = composite(bank, water, band_mask(size, rng, center_y=256, width=335, softness=38, wobble=18))
    draw_flow_lines(image, rng, (179, 214, 205, 92), 34)
    draw_flow_lines(image, rng, (26, 50, 61, 54), 14)
    draw_ink_grain(image, rng, 220, (32, 38, 25, 42))
    return force_opaque(image)


def water_shore_edge(size: int, rng: random.Random) -> Image.Image:
    land = colorized_texture(size, rng, (70, 75, 43), (156, 138, 82))
    water = colorized_texture(size, rng, (38, 81, 88), (104, 145, 137))
    image = composite(land, water, shore_mask(size, rng))
    draw = ImageDraw.Draw(image, "RGBA")
    for _index in range(170):
        x = rng.randrange(size)
        y = rng.randrange(160, 340) + round(math.sin(x / 42) * 22)
        radius = rng.choice((1, 2, 2, 3, 4))
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(86, 79, 55, 75))
    draw_flow_lines(image, rng, (184, 217, 205, 70), 16)
    return force_opaque(image)


def rocky_ground_patch(size: int, rng: random.Random) -> Image.Image:
    image = colorized_texture(size, rng, (65, 62, 52), (154, 145, 121))
    draw = ImageDraw.Draw(image, "RGBA")
    for _index in range(75):
        cx = rng.randrange(-20, size + 20)
        cy = rng.randrange(-20, size + 20)
        radius = rng.randrange(12, 48)
        points = []
        sides = rng.randrange(6, 10)
        for side in range(sides):
            angle = math.tau * side / sides + rng.uniform(-0.18, 0.18)
            distance = radius * rng.uniform(0.65, 1.2)
            points.append((cx + math.cos(angle) * distance, cy + math.sin(angle) * distance))
        shade = rng.randrange(-18, 24)
        fill = (116 + shade, 111 + shade, 93 + shade, rng.randrange(45, 88))
        draw.polygon(points, fill=fill, outline=(44, 42, 36, 75))
    for _index in range(34):
        x = rng.randrange(size)
        y = rng.randrange(size)
        length = rng.randrange(24, 95)
        angle = rng.uniform(0, math.tau)
        draw.line(
            (x, y, x + math.cos(angle) * length, y + math.sin(angle) * length),
            fill=(35, 34, 30, 55),
            width=rng.choice((1, 1, 2)),
        )
    return force_opaque(image)


def dense_woods_patch(size: int, rng: random.Random) -> Image.Image:
    image = colorized_texture(size, rng, (38, 58, 30), (103, 107, 47))
    draw = ImageDraw.Draw(image, "RGBA")
    greens = ((42, 74, 34), (54, 91, 42), (66, 100, 49), (78, 96, 43), (35, 65, 34))
    for _index in range(190):
        cx = rng.randrange(-35, size + 35)
        cy = rng.randrange(-35, size + 35)
        rx = rng.randrange(18, 48)
        ry = rng.randrange(16, 43)
        green = rng.choice(greens)
        alpha = rng.randrange(118, 190)
        draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=(*green, alpha), outline=(20, 39, 24, 46))
    for _index in range(85):
        cx = rng.randrange(size)
        cy = rng.randrange(size)
        draw.ellipse((cx - 2, cy - 2, cx + 2, cy + 2), fill=(54, 35, 22, 74))
    draw_ink_grain(image, rng, 520, (19, 32, 21, 38))
    return force_opaque(image.filter(ImageFilter.UnsharpMask(radius=1.2, percent=65, threshold=4)))


def swamp_muck_tile(size: int, rng: random.Random) -> Image.Image:
    muck = colorized_texture(size, rng, (48, 61, 37), (118, 104, 60))
    water = colorized_texture(size, rng, (40, 76, 70), (96, 120, 99))
    draw_mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(draw_mask)
    for _index in range(36):
        cx = rng.randrange(-30, size + 30)
        cy = rng.randrange(-30, size + 30)
        rx = rng.randrange(20, 82)
        ry = rng.randrange(12, 54)
        draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=rng.randrange(70, 150))
    image = composite(muck, water, draw_mask.filter(ImageFilter.GaussianBlur(9)))
    draw = ImageDraw.Draw(image, "RGBA")
    for _index in range(155):
        x = rng.randrange(size)
        y = rng.randrange(size)
        length = rng.randrange(9, 26)
        draw.line((x, y, x + rng.randrange(-4, 5), y - length), fill=(84, 96, 45, 92), width=1)
    draw_ink_grain(image, rng, 260, (29, 36, 25, 50))
    return force_opaque(image)


def lava_flow_segment(size: int, rng: random.Random) -> Image.Image:
    basalt = colorized_texture(size, rng, (24, 24, 23), (74, 68, 59))
    lava = colorized_texture(size, rng, (112, 27, 18), (250, 137, 39))
    image = composite(basalt, lava, band_mask(size, rng, center_y=256, width=275, softness=50, wobble=26))
    draw = ImageDraw.Draw(image, "RGBA")
    for _index in range(48):
        y = rng.randrange(145, 368)
        points = []
        phase = rng.random() * math.tau
        for x in range(-10, size + 11, 18):
            points.append((x, y + math.sin(x / rng.uniform(25, 58) + phase) * rng.uniform(4, 18)))
        draw.line(points, fill=(255, 203, 70, rng.randrange(80, 145)), width=rng.choice((1, 2, 3)))
    for _index in range(38):
        x = rng.randrange(size)
        y = rng.randrange(size)
        angle = rng.uniform(0, math.tau)
        length = rng.randrange(28, 110)
        draw.line(
            (x, y, x + math.cos(angle) * length, y + math.sin(angle) * length),
            fill=(12, 12, 12, 82),
            width=rng.choice((1, 1, 2)),
        )
    return force_opaque(image)


def cobblestone_street(size: int, rng: random.Random) -> Image.Image:
    image = colorized_texture(size, rng, (45, 43, 38), (83, 78, 66))
    draw = ImageDraw.Draw(image, "RGBA")
    y = -28
    row = 0
    while y < size + 30:
        height = rng.randrange(35, 54)
        x = -60 - (row % 2) * rng.randrange(18, 45)
        while x < size + 65:
            width = rng.randrange(44, 82)
            shade = rng.randrange(-22, 24)
            fill = (112 + shade, 108 + shade, 94 + shade, 226)
            radius = rng.randrange(7, 15)
            draw.rounded_rectangle(
                (x, y, x + width, y + height),
                radius=radius,
                fill=fill,
                outline=(31, 30, 27, 130),
                width=2,
            )
            if rng.random() < 0.42:
                cx = x + rng.randrange(max(8, width))
                cy = y + rng.randrange(max(8, height))
                draw.line((cx - 9, cy, cx + 9, cy + rng.randrange(-4, 5)), fill=(38, 37, 34, 45), width=1)
            x += width + rng.randrange(5, 12)
        y += height + rng.randrange(5, 10)
        row += 1
    draw_ink_grain(image, rng, 340, (28, 27, 24, 38))
    return force_opaque(image)


def blacksmith_workshop(size: int, rng: random.Random) -> Image.Image:
    image = cobblestone_street(size, rng)
    inner = draw_stone_room(image, rng, (34, 34, size - 34, size - 34), wall_width=22)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rectangle((inner[0] + 18, inner[1] + 18, inner[0] + 130, inner[1] + 92), fill=(64, 49, 34, 190), outline=(31, 24, 18, 130), width=3)
    draw.rectangle((inner[2] - 126, inner[1] + 26, inner[2] - 22, inner[1] + 128), fill=(70, 40, 25, 210), outline=(35, 22, 16, 130), width=4)
    draw.ellipse((inner[2] - 105, inner[1] + 48, inner[2] - 43, inner[1] + 106), fill=(185, 70, 28, 145), outline=(55, 31, 18, 150), width=3)
    draw.polygon(((230, 246), (282, 238), (304, 270), (260, 292), (218, 278)), fill=(64, 64, 60, 210), outline=(25, 24, 22, 120))
    for _index in range(8):
        x = rng.randrange(inner[0] + 50, inner[2] - 80)
        y = rng.randrange(inner[1] + 150, inner[3] - 40)
        draw.rectangle((x, y, x + rng.randrange(22, 46), y + rng.randrange(8, 18)), fill=(32, 29, 24, 120))
    return force_opaque(image)


def bridge_over_chasm(size: int, rng: random.Random) -> Image.Image:
    image = colorized_texture(size, rng, (10, 11, 12), (43, 42, 38))
    draw = ImageDraw.Draw(image, "RGBA")
    draw.polygon(((-20, 72), (160, 48), (280, 126), (532, 66), (532, 446), (320, 392), (188, 460), (-20, 420)), fill=(14, 15, 17, 230))
    draw_boulders(image, rng, 42, (83, 80, 70, 110))
    draw_planks(image, rng, (0, 218, size, 294), horizontal=False)
    for x in range(-10, size + 40, 46):
        draw.rectangle((x, 206, x + 24, 306), fill=(83, 58, 36, 210), outline=(35, 25, 18, 120), width=2)
    return force_opaque(image)


def building_wall_segment(size: int, rng: random.Random) -> Image.Image:
    image = colorized_texture(size, rng, (80, 81, 48), (136, 123, 72))
    draw_planks(image, rng, (0, 190, size, 322), horizontal=False)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rectangle((0, 214, size, 298), fill=(76, 69, 58, 185), outline=(34, 29, 24, 135), width=4)
    for x in range(-30, size + 30, 68):
        draw.rectangle((x, 182, x + 24, 330), fill=(83, 57, 36, 210), outline=(35, 25, 18, 120), width=2)
    draw_ink_grain(image, rng, 230, (28, 24, 20, 44))
    return force_opaque(image)


def cave_entrance(size: int, rng: random.Random) -> Image.Image:
    image = colorized_texture(size, rng, (65, 76, 42), (139, 123, 70))
    draw = ImageDraw.Draw(image, "RGBA")
    draw.ellipse((104, 78, 410, 430), fill=(82, 79, 66, 190), outline=(36, 34, 29, 120), width=5)
    draw.ellipse((150, 142, 362, 392), fill=(17, 18, 18, 235), outline=(44, 42, 35, 180), width=8)
    draw_boulders(image, rng, 58, (91, 88, 76, 135))
    draw_path(image, rng, [(250, size + 30), (248, 392), (255, 290), (258, 190)], (112, 91, 58, 150), 64)
    return force_opaque(image)


def cave_network_map(size: int, rng: random.Random) -> Image.Image:
    image = colorized_texture(size, rng, (43, 42, 36), (107, 101, 84))
    draw = ImageDraw.Draw(image, "RGBA")
    nodes = [(98, 120), (218, 94), (350, 126), (406, 238), (308, 326), (184, 292), (112, 410), (384, 414)]
    for a, b in zip(nodes, nodes[1:]):
        draw_path(image, rng, [a, ((a[0] + b[0]) // 2 + rng.randrange(-35, 36), (a[1] + b[1]) // 2 + rng.randrange(-35, 36)), b], (28, 28, 25, 210), 54)
    for x, y in nodes:
        draw.ellipse((x - 48, y - 38, x + 48, y + 38), fill=(31, 31, 28, 220), outline=(71, 67, 56, 130), width=4)
    draw_boulders(image, rng, 38, (85, 82, 70, 90))
    return force_opaque(image)


def cavern_lake(size: int, rng: random.Random) -> Image.Image:
    image = colorized_texture(size, rng, (46, 44, 37), (101, 96, 78))
    water = colorized_texture(size, rng, (28, 62, 70), (89, 126, 124))
    mask = Image.new("L", (size, size), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((92, 98, 426, 392), fill=255)
    image = composite(image, water, mask.filter(ImageFilter.GaussianBlur(4)))
    draw_flow_lines(image, rng, (176, 210, 200, 65), 18)
    draw_boulders(image, rng, 45, (88, 85, 72, 110))
    return force_opaque(image)


def crypt_chamber(size: int, rng: random.Random) -> Image.Image:
    image = cobblestone_street(size, rng)
    inner = draw_stone_room(image, rng, (38, 38, 474, 474), wall_width=22)
    draw = ImageDraw.Draw(image, "RGBA")
    for x in (116, 286):
        for y in (122, 288):
            draw.rounded_rectangle((x, y, x + 92, y + 132), radius=10, fill=(80, 76, 66, 210), outline=(35, 33, 30, 130), width=4)
    draw.rectangle((inner[0] + 146, inner[1] + 185, inner[0] + 250, inner[1] + 232), fill=(70, 65, 57, 210), outline=(31, 30, 27, 120), width=3)
    return force_opaque(image)


def desert_ruins(size: int, rng: random.Random) -> Image.Image:
    image = colorized_texture(size, rng, (122, 97, 55), (214, 176, 101))
    draw = ImageDraw.Draw(image, "RGBA")
    for _index in range(24):
        x = rng.randrange(-30, size)
        y = rng.randrange(-30, size)
        w = rng.randrange(38, 122)
        h = rng.randrange(16, 36)
        angle = rng.uniform(-0.7, 0.7)
        points = [(x, y), (x + w, y + math.sin(angle) * 18), (x + w, y + h), (x, y + h)]
        draw.polygon(points, fill=(151, 129, 91, 150), outline=(75, 61, 42, 90))
    for _index in range(18):
        x = rng.randrange(size)
        y = rng.randrange(size)
        draw.ellipse((x - 12, y - 12, x + 12, y + 12), fill=(154, 139, 109, 135), outline=(72, 63, 48, 90))
    draw_ink_grain(image, rng, 480, (78, 55, 34, 34))
    return force_opaque(image)


def dungeon_crossroads(size: int, rng: random.Random) -> Image.Image:
    image = colorized_texture(size, rng, (29, 28, 25), (61, 58, 50))
    floor = cobblestone_street(size, rng)
    mask = Image.new("L", (size, size), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rectangle((182, 0, 330, size), fill=255)
    draw_mask.rectangle((0, 182, size, 330), fill=255)
    image = composite(image, floor, mask)
    draw = ImageDraw.Draw(image, "RGBA")
    for rect in ((166, 0, 182, size), (330, 0, 346, size), (0, 166, size, 182), (0, 330, size, 346)):
        draw.rectangle(rect, fill=(36, 34, 30, 190))
    return force_opaque(image)


def dungeon_level_map(size: int, rng: random.Random) -> Image.Image:
    image = colorized_texture(size, rng, (30, 29, 26), (67, 64, 56))
    rooms = [(38, 46, 164, 162), (246, 42, 444, 166), (72, 252, 222, 430), (314, 280, 464, 452), (206, 188, 318, 292)]
    floor = cobblestone_street(size, rng)
    mask = Image.new("L", (size, size), 0)
    draw_mask = ImageDraw.Draw(mask)
    centers = []
    for rect in rooms:
        draw_mask.rectangle(rect, fill=255)
        centers.append(((rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2))
    for a, b in zip(centers, centers[1:]):
        draw_mask.line((a, b), fill=255, width=52)
    image = composite(image, floor, mask)
    draw = ImageDraw.Draw(image, "RGBA")
    for rect in rooms:
        draw.rectangle(rect, outline=(32, 30, 27, 210), width=10)
    return force_opaque(image)


def dungeon_prison_block(size: int, rng: random.Random) -> Image.Image:
    image = cobblestone_street(size, rng)
    inner = draw_stone_room(image, rng, (28, 44, 484, 468), wall_width=18)
    draw = ImageDraw.Draw(image, "RGBA")
    for y in (92, 186, 280, 374):
        draw.line((inner[0], y, inner[2], y), fill=(37, 35, 31, 180), width=7)
        for x in range(inner[0] + 38, inner[2], 52):
            draw.line((x, y - 32, x, y + 32), fill=(22, 22, 20, 150), width=3)
    draw.rectangle((inner[2] - 116, inner[1] + 28, inner[2] - 30, inner[1] + 104), fill=(88, 66, 42, 160), outline=(34, 25, 17, 100), width=3)
    return force_opaque(image)


def dungeon_trap_hall(size: int, rng: random.Random) -> Image.Image:
    image = colorized_texture(size, rng, (30, 29, 26), (60, 56, 49))
    hall = cobblestone_street(size, rng)
    mask = Image.new("L", (size, size), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rectangle((118, 0, 394, size), fill=255)
    image = composite(image, hall, mask)
    draw = ImageDraw.Draw(image, "RGBA")
    for y in range(86, size - 60, 82):
        draw.rectangle((178, y, 334, y + 42), outline=(38, 36, 32, 120), width=3, fill=(93, 88, 76, 72))
    for x in (108, 394):
        draw.rectangle((x - 10, 0, x + 10, size), fill=(34, 32, 28, 180))
    return force_opaque(image)


def forest_clearing(size: int, rng: random.Random) -> Image.Image:
    image = grass_field_like(size, rng)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.ellipse((128, 116, 388, 392), fill=(115, 104, 62, 95))
    draw_tree_cluster(image, rng, 165, avoid=(118, 108, 398, 402))
    draw_boulders(image, rng, 18, (86, 82, 68, 82))
    return force_opaque(image)


def grass_field_like(size: int, rng: random.Random) -> Image.Image:
    image = colorized_texture(size, rng, (55, 74, 34), (132, 128, 62))
    draw_ink_grain(image, rng, 360, (29, 38, 20, 35))
    return image


def forest_road_ambush(size: int, rng: random.Random) -> Image.Image:
    image = grass_field_like(size, rng)
    road = colorized_texture(size, rng, (86, 61, 38), (174, 135, 82))
    mask = band_mask(size, rng, center_y=256, width=170, softness=44, wobble=38)
    image = composite(image, road, mask)
    draw_tree_cluster(image, rng, 190, avoid=(0, 164, size, 348))
    draw_boulders(image, rng, 24, (79, 76, 63, 82))
    return force_opaque(image)


def frontier_valley_map(size: int, rng: random.Random) -> Image.Image:
    image = grass_field_like(size, rng)
    water = colorized_texture(size, rng, (36, 79, 92), (92, 135, 133))
    mask = band_mask(size, rng, center_y=248, width=72, softness=28, wobble=42)
    image = composite(image, water, mask)
    draw_path(image, rng, [(28, 444), (152, 324), (280, 266), (404, 122), (520, 70)], (126, 93, 55, 130), 26)
    draw_boulders(image, rng, 60, (96, 91, 76, 92))
    draw_tree_cluster(image, rng, 85, avoid=(170, 150, 360, 380))
    return force_opaque(image)


def graveyard_night(size: int, rng: random.Random) -> Image.Image:
    image = colorized_texture(size, rng, (22, 35, 30), (62, 74, 53))
    draw = ImageDraw.Draw(image, "RGBA")
    for _index in range(46):
        x = rng.randrange(36, size - 36)
        y = rng.randrange(48, size - 48)
        draw.rounded_rectangle((x - 10, y - 18, x + 10, y + 18), radius=5, fill=(87, 89, 80, 150), outline=(30, 31, 29, 90))
    draw.rectangle((330, 122, 452, 244), fill=(40, 39, 36, 190), outline=(18, 18, 17, 120), width=4)
    draw.polygon(((316, 122), (391, 62), (466, 122)), fill=(55, 52, 47, 195), outline=(20, 20, 18, 120))
    return force_opaque(image)


def inn_guest_rooms(size: int, rng: random.Random) -> Image.Image:
    image = colorized_texture(size, rng, (82, 55, 32), (149, 103, 58))
    draw = ImageDraw.Draw(image, "RGBA")
    for y in range(28, size, 42):
        draw.line((0, y, size, y + rng.randrange(-3, 4)), fill=(48, 31, 20, 95), width=2)
    for x in (156, 318):
        draw.rectangle((x - 7, 0, x + 7, size), fill=(54, 35, 23, 190))
    draw.rectangle((0, 236, size, 256), fill=(54, 35, 23, 190))
    for x in (36, 196, 358):
        for y in (52, 298):
            draw.rectangle((x, y, x + 76, y + 112), fill=(107, 72, 43, 160), outline=(41, 28, 19, 110), width=3)
            draw.rectangle((x + 10, y + 10, x + 66, y + 42), fill=(150, 139, 108, 150))
    return force_opaque(image)


def island_campaign_map(size: int, rng: random.Random) -> Image.Image:
    image = colorized_texture(size, rng, (35, 82, 96), (86, 137, 139))
    land = colorized_texture(size, rng, (77, 96, 43), (174, 150, 83))
    mask = Image.new("L", (size, size), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((120, 78, 418, 398), fill=255)
    draw_mask.ellipse((254, 312, 432, 470), fill=255)
    image = composite(image, land, mask.filter(ImageFilter.GaussianBlur(3)))
    draw_tree_cluster(image, rng, 90, avoid=(0, 0, 0, 0))
    draw_flow_lines(image, rng, (182, 218, 210, 60), 22)
    return force_opaque(image)


def kingdom_overland_map(size: int, rng: random.Random) -> Image.Image:
    image = colorized_texture(size, rng, (86, 93, 48), (172, 151, 88))
    water = colorized_texture(size, rng, (42, 85, 97), (94, 139, 137))
    image = composite(image, water, band_mask(size, rng, center_y=320, width=56, softness=22, wobble=44))
    draw_path(image, rng, [(28, 420), (142, 330), (254, 268), (370, 210), (502, 118)], (126, 91, 52, 125), 20)
    draw_tree_cluster(image, rng, 70, avoid=(170, 170, 370, 370))
    draw_boulders(image, rng, 55, (97, 91, 76, 92))
    draw_small_buildings(image, rng, 16, (80, 80, 440, 410))
    return force_opaque(image)


def mushroom_cavern(size: int, rng: random.Random) -> Image.Image:
    image = colorized_texture(size, rng, (42, 41, 36), (103, 97, 79))
    draw = ImageDraw.Draw(image, "RGBA")
    for _index in range(56):
        x = rng.randrange(24, size - 24)
        y = rng.randrange(24, size - 24)
        radius = rng.randrange(10, 34)
        cap = rng.choice(((113, 72, 87), (112, 93, 60), (82, 101, 79), (128, 101, 75)))
        draw.ellipse((x - radius, y - radius // 2, x + radius, y + radius // 2), fill=(*cap, 150), outline=(35, 31, 28, 80))
        draw.rectangle((x - 4, y, x + 4, y + radius), fill=(139, 125, 96, 100))
    draw_boulders(image, rng, 28, (82, 79, 68, 90))
    return force_opaque(image)


def planar_crossroads_map(size: int, rng: random.Random) -> Image.Image:
    image = colorized_texture(size, rng, (33, 31, 43), (79, 70, 88))
    draw = ImageDraw.Draw(image, "RGBA")
    center = (size // 2, size // 2)
    paths = [
        [(center[0], center[1]), (size + 20, center[1] - 72)],
        [(center[0], center[1]), (-20, center[1] + 64)],
        [(center[0], center[1]), (center[0] + 78, -20)],
        [(center[0], center[1]), (center[0] - 62, size + 20)],
    ]
    colors = ((132, 64, 49, 150), (61, 110, 126, 150), (111, 96, 151, 150), (119, 112, 64, 150))
    for points, color in zip(paths, colors):
        draw_path(image, rng, points, color, 74)
    draw.ellipse((198, 198, 314, 314), fill=(39, 37, 45, 210), outline=(138, 121, 84, 130), width=5)
    return force_opaque(image)


def port_city_map(size: int, rng: random.Random) -> Image.Image:
    land = cobblestone_street(size, rng)
    water = colorized_texture(size, rng, (36, 80, 96), (91, 139, 142))
    mask = Image.new("L", (size, size), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rectangle((0, 0, 160, size), fill=255)
    image = composite(land, water, mask)
    draw = ImageDraw.Draw(image, "RGBA")
    for y in range(74, 438, 84):
        draw_planks(image, rng, (128, y, 286, y + 34), horizontal=False)
    draw_small_buildings(image, rng, 34, (230, 36, 480, 452))
    draw_flow_lines(image, rng, (184, 216, 210, 55), 12)
    return force_opaque(image)


def regional_overland_map(size: int, rng: random.Random) -> Image.Image:
    image = grass_field_like(size, rng)
    water = colorized_texture(size, rng, (38, 83, 96), (94, 138, 135))
    image = composite(image, water, band_mask(size, rng, center_y=212, width=54, softness=24, wobble=38))
    draw_path(image, rng, [(24, 382), (142, 302), (250, 248), (356, 180), (504, 128)], (128, 95, 56, 125), 18)
    draw_tree_cluster(image, rng, 100, avoid=(168, 128, 360, 340))
    draw_boulders(image, rng, 70, (92, 89, 76, 90))
    return force_opaque(image)


def river_ford(size: int, rng: random.Random) -> Image.Image:
    image = river_segment(size, rng)
    draw = ImageDraw.Draw(image, "RGBA")
    for x in range(70, size - 40, 48):
        y = 250 + round(math.sin(x / 43) * 32)
        radius = rng.randrange(14, 28)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(128, 121, 96, 150), outline=(45, 42, 34, 85))
    draw_path(image, rng, [(26, 318), (170, 286), (312, 242), (494, 202)], (151, 123, 76, 90), 30)
    return force_opaque(image)


def sewer_crossing(size: int, rng: random.Random) -> Image.Image:
    stone = cobblestone_street(size, rng)
    water = colorized_texture(size, rng, (34, 70, 58), (82, 105, 72))
    mask = Image.new("L", (size, size), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rectangle((0, 198, size, 314), fill=255)
    draw_mask.rectangle((198, 0, 314, size), fill=180)
    image = composite(stone, water, mask)
    draw_planks(image, rng, (0, 226, size, 286), horizontal=False)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rectangle((188, 0, 202, size), fill=(34, 32, 28, 160))
    draw.rectangle((310, 0, 324, size), fill=(34, 32, 28, 160))
    return force_opaque(image)


def ship_deck(size: int, rng: random.Random) -> Image.Image:
    image = colorized_texture(size, rng, (81, 54, 31), (155, 104, 56))
    draw = ImageDraw.Draw(image, "RGBA")
    for x in range(20, size, 42):
        draw.line((x, 0, x + rng.randrange(-5, 6), size), fill=(44, 29, 19, 100), width=3)
    draw.ellipse((210, 190, 302, 282), fill=(76, 49, 29, 220), outline=(30, 20, 14, 130), width=5)
    for _index in range(15):
        x = rng.randrange(40, size - 90)
        y = rng.randrange(40, size - 80)
        draw.rectangle((x, y, x + rng.randrange(32, 76), y + rng.randrange(24, 58)), fill=(96, 65, 39, 145), outline=(38, 25, 16, 100), width=2)
    return force_opaque(image)


def snowy_pass(size: int, rng: random.Random) -> Image.Image:
    image = colorized_texture(size, rng, (139, 150, 148), (231, 229, 211))
    draw_path(image, rng, [(20, 430), (154, 330), (244, 264), (340, 174), (492, 96)], (174, 177, 163, 125), 66)
    draw_boulders(image, rng, 70, (104, 108, 103, 112))
    draw_ink_grain(image, rng, 220, (82, 91, 92, 26))
    return force_opaque(image)


def stone_dungeon_room(size: int, rng: random.Random) -> Image.Image:
    image = cobblestone_street(size, rng)
    inner = draw_stone_room(image, rng, (38, 38, 474, 474), wall_width=24)
    draw = ImageDraw.Draw(image, "RGBA")
    for x in (130, 382):
        for y in (132, 382):
            draw.ellipse((x - 22, y - 22, x + 22, y + 22), fill=(76, 72, 63, 205), outline=(31, 30, 27, 120), width=4)
    draw.rectangle((inner[0] + 154, inner[1] + 154, inner[0] + 244, inner[1] + 244), fill=(78, 74, 64, 160), outline=(31, 30, 27, 110), width=4)
    draw_boulders(image, rng, 25, (88, 84, 72, 88))
    return force_opaque(image)


def swamp_boardwalk(size: int, rng: random.Random) -> Image.Image:
    image = swamp_muck_tile(size, rng)
    draw_planks(image, rng, (0, 226, size, 292), horizontal=False)
    draw_planks(image, rng, (230, 0, 292, size), horizontal=True)
    return force_opaque(image)


def tavern_ground_floor(size: int, rng: random.Random) -> Image.Image:
    image = colorized_texture(size, rng, (80, 51, 29), (150, 99, 53))
    draw = ImageDraw.Draw(image, "RGBA")
    for y in range(28, size, 38):
        draw.line((0, y, size, y + rng.randrange(-3, 4)), fill=(43, 27, 17, 95), width=2)
    draw.rectangle((24, 46, 112, 438), fill=(92, 57, 33, 190), outline=(35, 22, 14, 110), width=4)
    for _index in range(7):
        x = rng.randrange(150, size - 90)
        y = rng.randrange(70, size - 90)
        draw.ellipse((x, y, x + 58, y + 58), fill=(94, 62, 36, 165), outline=(35, 22, 14, 100), width=3)
    draw.rectangle((398, 54, 474, 138), fill=(68, 39, 27, 180), outline=(32, 20, 14, 120), width=4)
    return force_opaque(image)


def temple_sanctum(size: int, rng: random.Random) -> Image.Image:
    image = cobblestone_street(size, rng)
    inner = draw_stone_room(image, rng, (34, 34, 478, 478), wall_width=22)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.ellipse((172, 172, 340, 340), outline=(93, 81, 60, 140), width=6)
    draw.ellipse((210, 210, 302, 302), outline=(62, 55, 43, 120), width=4)
    for x in (112, 400):
        for y in (112, 400):
            draw.ellipse((x - 24, y - 24, x + 24, y + 24), fill=(80, 76, 66, 200), outline=(31, 30, 27, 120), width=4)
    draw.rectangle((inner[0] + 154, inner[1] + 46, inner[0] + 246, inner[1] + 88), fill=(87, 76, 58, 180), outline=(36, 32, 25, 110), width=4)
    return force_opaque(image)


def throne_room(size: int, rng: random.Random) -> Image.Image:
    image = cobblestone_street(size, rng)
    inner = draw_stone_room(image, rng, (30, 30, 482, 482), wall_width=24)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rectangle((222, inner[1], 290, inner[3]), fill=(113, 32, 31, 135))
    for x in (126, 386):
        for y in (126, 318):
            draw.ellipse((x - 22, y - 22, x + 22, y + 22), fill=(77, 73, 63, 205), outline=(31, 30, 27, 115), width=4)
    draw.rectangle((202, 80, 310, 158), fill=(86, 61, 43, 210), outline=(35, 25, 18, 120), width=5)
    return force_opaque(image)


def village_map(size: int, rng: random.Random) -> Image.Image:
    image = grass_field_like(size, rng)
    draw_path(image, rng, [(18, 292), (144, 260), (256, 254), (388, 222), (524, 188)], (133, 99, 59, 125), 46)
    draw_path(image, rng, [(260, 524), (250, 380), (262, 250), (238, 118), (222, -18)], (126, 91, 52, 100), 28)
    draw_small_buildings(image, rng, 26, (48, 56, 440, 420))
    draw_tree_cluster(image, rng, 70, avoid=(82, 86, 430, 424))
    return force_opaque(image)


def village_street_market(size: int, rng: random.Random) -> Image.Image:
    image = dirt_road_straight(size, rng)
    draw = ImageDraw.Draw(image, "RGBA")
    for _index in range(14):
        x = rng.randrange(52, size - 86)
        y = rng.choice((rng.randrange(76, 178), rng.randrange(334, 442)))
        draw.rectangle((x, y, x + rng.randrange(42, 86), y + rng.randrange(24, 48)), fill=rng.choice(((120, 44, 39, 150), (45, 82, 102, 150), (146, 116, 55, 150))), outline=(35, 27, 20, 100), width=2)
    draw_small_buildings(image, rng, 10, (20, 36, 474, 456))
    return force_opaque(image)


def walled_city_map(size: int, rng: random.Random) -> Image.Image:
    image = grass_field_like(size, rng)
    city = cobblestone_street(size, rng)
    mask = Image.new("L", (size, size), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((82, 78, 430, 424), fill=255)
    image = composite(image, city, mask)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.ellipse((76, 72, 436, 430), outline=(70, 65, 55, 230), width=18)
    draw_small_buildings(image, rng, 38, (124, 114, 386, 388))
    draw_path(image, rng, [(256, 430), (256, 328), (256, 256), (256, 84)], (91, 81, 64, 105), 22)
    draw_path(image, rng, [(82, 256), (198, 256), (256, 256), (430, 256)], (91, 81, 64, 105), 22)
    return force_opaque(image)


def wizard_laboratory(size: int, rng: random.Random) -> Image.Image:
    image = cobblestone_street(size, rng)
    inner = draw_stone_room(image, rng, (36, 36, 476, 476), wall_width=20, floor_color=(86, 80, 78, 165))
    draw = ImageDraw.Draw(image, "RGBA")
    for _index in range(8):
        x = rng.randrange(inner[0] + 16, inner[2] - 92)
        y = rng.randrange(inner[1] + 20, inner[3] - 92)
        draw.rectangle((x, y, x + rng.randrange(52, 96), y + rng.randrange(28, 58)), fill=(78, 54, 38, 160), outline=(34, 24, 18, 105), width=3)
    for _index in range(10):
        x = rng.randrange(inner[0] + 36, inner[2] - 36)
        y = rng.randrange(inner[1] + 36, inner[3] - 36)
        draw.ellipse((x - 14, y - 14, x + 14, y + 14), outline=(86, 121, 126, 120), width=3)
    draw.ellipse((190, 190, 322, 322), outline=(92, 75, 128, 120), width=5)
    return force_opaque(image)


GENERATORS = {
    "river_segment": river_segment,
    "water_shore_edge": water_shore_edge,
    "dense_woods_patch": dense_woods_patch,
    "dirt_road_straight": dirt_road_straight,
    "rocky_ground_patch": rocky_ground_patch,
    "swamp_muck_tile": swamp_muck_tile,
    "lava_flow_segment": lava_flow_segment,
    "cobblestone_street": cobblestone_street,
    "blacksmith_workshop": blacksmith_workshop,
    "bridge_over_chasm": bridge_over_chasm,
    "building_wall_segment": building_wall_segment,
    "cave_entrance": cave_entrance,
    "cave_network_map": cave_network_map,
    "cavern_lake": cavern_lake,
    "crypt_chamber": crypt_chamber,
    "desert_ruins": desert_ruins,
    "dungeon_crossroads": dungeon_crossroads,
    "dungeon_level_map": dungeon_level_map,
    "dungeon_prison_block": dungeon_prison_block,
    "dungeon_trap_hall": dungeon_trap_hall,
    "forest_clearing": forest_clearing,
    "forest_road_ambush": forest_road_ambush,
    "frontier_valley_map": frontier_valley_map,
    "graveyard_night": graveyard_night,
    "inn_guest_rooms": inn_guest_rooms,
    "island_campaign_map": island_campaign_map,
    "kingdom_overland_map": kingdom_overland_map,
    "mushroom_cavern": mushroom_cavern,
    "planar_crossroads_map": planar_crossroads_map,
    "port_city_map": port_city_map,
    "regional_overland_map": regional_overland_map,
    "river_ford": river_ford,
    "sewer_crossing": sewer_crossing,
    "ship_deck": ship_deck,
    "snowy_pass": snowy_pass,
    "stone_dungeon_room": stone_dungeon_room,
    "swamp_boardwalk": swamp_boardwalk,
    "tavern_ground_floor": tavern_ground_floor,
    "temple_sanctum": temple_sanctum,
    "throne_room": throne_room,
    "village_map": village_map,
    "village_street_market": village_street_market,
    "walled_city_map": walled_city_map,
    "wizard_laboratory": wizard_laboratory,
}


def generate_source(slug: str, *, size: int) -> Image.Image:
    if slug not in GENERATORS:
        known = ", ".join(sorted(GENERATORS))
        raise ValueError(f"Unknown procedural terrain slug {slug!r}. Known slugs: {known}")
    return GENERATORS[slug](size, seeded_random(slug))


def process_slug(slug: str, *, output_dir: Path, size: int, overwrite: bool) -> Path:
    if slug in CURATED_IMAGEGEN_SLUGS:
        raise ValueError(f"{slug} uses a curated image source; refusing to replace it procedurally")
    output = output_dir / f"{slug}-fullbleed-source.png"
    if output.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing file: {output}")
    output_dir.mkdir(parents=True, exist_ok=True)
    generate_source(slug, size=size).save(output)
    return output


def parse_args(argv: list[str]) -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("slugs", nargs="*", default=list(DEFAULT_SLUGS))
    parser.add_argument("--media-root", type=Path, default=root / "dd3esheet" / "media")
    parser.add_argument("--tile-subdir", type=Path, default=DEFAULT_TILE_SUBDIR)
    parser.add_argument("--size", type=int, default=512)
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing existing full-bleed sources.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        output_dir = args.media_root / args.tile_subdir
        for slug in args.slugs:
            output = process_slug(slug, output_dir=output_dir, size=args.size, overwrite=args.overwrite)
            print(f"{slug}: wrote {output.as_posix()}")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
