from __future__ import annotations

import hashlib
import json
import random
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parents[1]
MEDIA_ROOT = ROOT / "dd3esheet" / "media" / "sprites" / "original"
MAP_TILE_DIR = MEDIA_ROOT / "map_tile"
MAP_TOKEN_DIR = MEDIA_ROOT / "map_token"
ITEM_DIR = MEDIA_ROOT / "item"
TMP_DIR = ROOT / "tmp"
DB_PATH = ROOT / "dd3esheet" / "db.sqlite3"

SOURCE_DIRS = {
    "map_tile": MAP_TILE_DIR,
    "map_token": MAP_TOKEN_DIR,
    "item": ITEM_DIR,
}

WIDTH = 2048
HEIGHT = 1536
CELL = 64
GRID_W = WIDTH // CELL
GRID_H = HEIGHT // CELL
TILE = 512

BATTLE_MAPS = [
    "stone_dungeon_room",
    "dungeon_crossroads",
    "dungeon_prison_block",
    "dungeon_trap_hall",
    "crypt_chamber",
    "temple_sanctum",
    "tavern_ground_floor",
    "inn_guest_rooms",
    "village_street_market",
    "blacksmith_workshop",
    "forest_clearing",
    "forest_road_ambush",
    "cave_entrance",
    "cavern_lake",
    "mushroom_cavern",
    "sewer_crossing",
    "bridge_over_chasm",
    "river_ford",
    "swamp_boardwalk",
    "desert_ruins",
    "snowy_pass",
    "ship_deck",
    "wizard_laboratory",
    "throne_room",
    "graveyard_night",
]


def hex_to_rgba(value: str, alpha: int = 255) -> tuple[int, int, int, int]:
    value = value.strip("#")
    return (
        int(value[0:2], 16),
        int(value[2:4], 16),
        int(value[4:6], 16),
        alpha,
    )


def cxy(cx: float, cy: float) -> tuple[int, int]:
    return int(round(cx * CELL)), int(round(cy * CELL))


def cbox(cx: float, cy: float, cw: float, ch: float) -> tuple[int, int, int, int]:
    x, y = cxy(cx, cy)
    return x, y, int(round(cw * CELL)), int(round(ch * CELL))


def lerp(a: int, b: int, amount: float) -> int:
    return int(round(a * (1.0 - amount) + b * amount))


def tint_image(img: Image.Image, color: str, amount: float) -> Image.Image:
    rgba = hex_to_rgba(color)
    base = img.convert("RGBA")
    px = base.load()
    for y in range(base.height):
        for x in range(base.width):
            r, g, b, a = px[x, y]
            if a:
                px[x, y] = (
                    lerp(r, rgba[0], amount),
                    lerp(g, rgba[1], amount),
                    lerp(b, rgba[2], amount),
                    a,
                )
    return base


def set_opacity(img: Image.Image, opacity: float) -> Image.Image:
    if opacity >= 0.999:
        return img
    out = img.copy()
    alpha = out.getchannel("A").point(lambda p: int(p * opacity))
    out.putalpha(alpha)
    return out


def fit_image(img: Image.Image, size: tuple[int, int], mode: str) -> Image.Image:
    if mode == "cover":
        return ImageOps.fit(img, size, method=Image.Resampling.LANCZOS)
    return img.resize(size, Image.Resampling.LANCZOS)


def rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=radius, fill=255)
    return mask


def asset_path(source: str, slug: str) -> Path:
    path = SOURCE_DIRS[source] / f"{slug}.png"
    if not path.exists():
        raise FileNotFoundError(f"Missing {source} asset: {slug} ({path})")
    return path


_ASSET_CACHE: dict[tuple[str, str], Image.Image] = {}


def load_asset(source: str, slug: str) -> Image.Image:
    key = (source, slug)
    if key not in _ASSET_CACHE:
        _ASSET_CACHE[key] = Image.open(asset_path(source, slug)).convert("RGBA")
    return _ASSET_CACHE[key].copy()


@dataclass
class Composer:
    slug: str
    seed: int

    def __post_init__(self) -> None:
        self.image = Image.new("RGBA", (WIDTH, HEIGHT), hex_to_rgba("2b2622"))
        self.ops: list[dict] = []
        self.rng = random.Random(self.seed)

    def record(self, op: dict) -> None:
        self.ops.append(op)

    def tile(self, slug: str, tint: str | None = None, tint_amount: float = 0.0, opacity: float = 1.0) -> None:
        img = load_asset("map_tile", slug)
        img = ImageOps.fit(img, (TILE, TILE), method=Image.Resampling.LANCZOS)
        if tint:
            img = tint_image(img, tint, tint_amount)
        img = set_opacity(img, opacity)
        for y in range(0, HEIGHT, TILE):
            for x in range(0, WIDTH, TILE):
                self.image.alpha_composite(img, (x, y))
        self.record(
            {
                "kind": "tile",
                "source": "map_tile",
                "asset": slug,
                "tile_px": TILE,
                "tint": tint,
                "tint_amount": tint_amount,
                "opacity": opacity,
            }
        )

    def place(
        self,
        source: str,
        slug: str,
        cx: float,
        cy: float,
        cw: float,
        ch: float,
        *,
        rotation: float = 0.0,
        opacity: float = 1.0,
        tint: str | None = None,
        tint_amount: float = 0.0,
        mode: str = "stretch",
        layer: str = "detail",
    ) -> None:
        x, y, w, h = cbox(cx, cy, cw, ch)
        img = load_asset(source, slug)
        img = fit_image(img, (max(1, w), max(1, h)), mode)
        if tint:
            img = tint_image(img, tint, tint_amount)
        if rotation:
            img = img.rotate(rotation, resample=Image.Resampling.BICUBIC, expand=True)
            x += (w - img.width) // 2
            y += (h - img.height) // 2
        img = set_opacity(img, opacity)
        self.image.alpha_composite(img, (x, y))
        self.record(
            {
                "kind": "place",
                "source": source,
                "asset": slug,
                "layer": layer,
                "cell": [cx, cy, cw, ch],
                "px": [x, y, img.width, img.height],
                "rotation": rotation,
                "opacity": opacity,
                "tint": tint,
                "tint_amount": tint_amount,
                "fit": mode,
            }
        )

    def rect(
        self,
        cx: float,
        cy: float,
        cw: float,
        ch: float,
        fill: str,
        *,
        alpha: int = 255,
        outline: str | None = None,
        outline_alpha: int = 255,
        width: int = 3,
        radius: float = 0.0,
        shadow: bool = True,
        layer: str = "primitive",
    ) -> None:
        x, y, w, h = cbox(cx, cy, cw, ch)
        overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        xy = (x, y, x + w, y + h)
        r = int(radius * CELL)
        if shadow:
            sxy = (x + 8, y + 8, x + w + 8, y + h + 8)
            if r:
                draw.rounded_rectangle(sxy, radius=r, fill=(24, 18, 13, 70))
            else:
                draw.rectangle(sxy, fill=(24, 18, 13, 70))
        if r:
            draw.rounded_rectangle(
                xy,
                radius=r,
                fill=hex_to_rgba(fill, alpha),
                outline=hex_to_rgba(outline, outline_alpha) if outline else None,
                width=width,
            )
        else:
            draw.rectangle(
                xy,
                fill=hex_to_rgba(fill, alpha),
                outline=hex_to_rgba(outline, outline_alpha) if outline else None,
                width=width,
            )
        self.image.alpha_composite(overlay)
        self.record(
            {
                "kind": "draw",
                "shape": "rect",
                "layer": layer,
                "cell": [cx, cy, cw, ch],
                "fill": fill,
                "alpha": alpha,
                "outline": outline,
                "outline_alpha": outline_alpha,
                "width": width,
                "radius_cells": radius,
            }
        )

    def ellipse(
        self,
        cx: float,
        cy: float,
        cw: float,
        ch: float,
        fill: str,
        *,
        alpha: int = 255,
        outline: str | None = None,
        outline_alpha: int = 255,
        width: int = 3,
        blur: float = 0.0,
        layer: str = "primitive",
    ) -> None:
        x, y, w, h = cbox(cx, cy, cw, ch)
        overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        draw.ellipse(
            (x, y, x + w, y + h),
            fill=hex_to_rgba(fill, alpha),
            outline=hex_to_rgba(outline, outline_alpha) if outline else None,
            width=width,
        )
        if blur:
            overlay = overlay.filter(ImageFilter.GaussianBlur(blur))
        self.image.alpha_composite(overlay)
        self.record(
            {
                "kind": "draw",
                "shape": "ellipse",
                "layer": layer,
                "cell": [cx, cy, cw, ch],
                "fill": fill,
                "alpha": alpha,
                "outline": outline,
                "outline_alpha": outline_alpha,
                "width": width,
                "blur": blur,
            }
        )

    def line(
        self,
        points: list[tuple[float, float]],
        fill: str,
        *,
        width_cells: float,
        alpha: int = 255,
        outline: str | None = None,
        outline_alpha: int = 255,
        layer: str = "primitive",
    ) -> None:
        px_points = [cxy(x, y) for x, y in points]
        overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        if outline:
            draw.line(
                px_points,
                fill=hex_to_rgba(outline, outline_alpha),
                width=int((width_cells + 0.35) * CELL),
                joint="curve",
            )
        draw.line(px_points, fill=hex_to_rgba(fill, alpha), width=int(width_cells * CELL), joint="curve")
        self.image.alpha_composite(overlay)
        self.record(
            {
                "kind": "draw",
                "shape": "line",
                "layer": layer,
                "points": points,
                "fill": fill,
                "alpha": alpha,
                "outline": outline,
                "outline_alpha": outline_alpha,
                "width_cells": width_cells,
            }
        )

    def polygon(
        self,
        points: list[tuple[float, float]],
        fill: str,
        *,
        alpha: int = 255,
        outline: str | None = None,
        outline_alpha: int = 255,
        layer: str = "primitive",
    ) -> None:
        px_points = [cxy(x, y) for x, y in points]
        overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        draw.polygon(px_points, fill=hex_to_rgba(fill, alpha))
        if outline:
            draw.line(px_points + [px_points[0]], fill=hex_to_rgba(outline, outline_alpha), width=6)
        self.image.alpha_composite(overlay)
        self.record(
            {
                "kind": "draw",
                "shape": "polygon",
                "layer": layer,
                "points": points,
                "fill": fill,
                "alpha": alpha,
                "outline": outline,
                "outline_alpha": outline_alpha,
            }
        )

    def texture_patch(
        self,
        slug: str,
        cx: float,
        cy: float,
        cw: float,
        ch: float,
        *,
        tint: str | None = None,
        tint_amount: float = 0.0,
        opacity: float = 0.45,
        layer: str = "terrain_patch",
    ) -> None:
        self.place(
            "map_tile",
            slug,
            cx,
            cy,
            cw,
            ch,
            tint=tint,
            tint_amount=tint_amount,
            opacity=opacity,
            mode="cover",
            layer=layer,
        )

    def scatter(
        self,
        source: str,
        slug: str,
        positions: list[tuple[float, float]],
        size: tuple[float, float],
        *,
        jitter: float = 0.0,
        opacity: float = 1.0,
        layer: str = "scatter",
    ) -> None:
        for i, (cx, cy) in enumerate(positions):
            jx = self.rng.uniform(-jitter, jitter) if jitter else 0.0
            jy = self.rng.uniform(-jitter, jitter) if jitter else 0.0
            rotation = self.rng.choice([0, 90, 180, 270])
            self.place(source, slug, cx + jx, cy + jy, size[0], size[1], rotation=rotation, opacity=opacity, layer=layer)

    def vignette(self, color: str = "2b2622", alpha: int = 70, border_cells: float = 2.0) -> None:
        overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        mask = Image.new("L", (WIDTH, HEIGHT), 0)
        draw = ImageDraw.Draw(mask)
        inset = int(border_cells * CELL)
        draw.rectangle((0, 0, WIDTH, HEIGHT), fill=255)
        draw.rectangle((inset, inset, WIDTH - inset, HEIGHT - inset), fill=0)
        mask = mask.filter(ImageFilter.GaussianBlur(inset // 2))
        overlay.paste(hex_to_rgba(color, alpha), (0, 0, WIDTH, HEIGHT), mask)
        self.image.alpha_composite(overlay)
        self.record(
            {
                "kind": "effect",
                "effect": "vignette",
                "color": color,
                "alpha": alpha,
                "border_cells": border_cells,
            }
        )

    def save(self) -> tuple[Path, Path]:
        out = MAP_TILE_DIR / f"{self.slug}.png"
        layout = MAP_TILE_DIR / f"{self.slug}-layout.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        rgb = self.image.convert("RGB")
        rgb.save(out, "PNG", optimize=True)
        layout.write_text(
            json.dumps(
                {
                    "slug": self.slug,
                    "canvas": {"width": WIDTH, "height": HEIGHT},
                    "grid": {"cell_px": CELL, "width": GRID_W, "height": GRID_H, "visible": False},
                    "source_policy": "Composed from existing project sprite pieces plus primitive masks/shapes recorded here.",
                    "rebuild_script": "scripts/generate_battle_maps_from_pieces.py",
                    "operations": self.ops,
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return out, layout


def wall_frame(m: Composer, color: str = "3a332d") -> None:
    m.rect(0, 0, 32, 1, color, alpha=245, outline="241f1b", width=4, shadow=False, layer="walls")
    m.rect(0, 23, 32, 1, color, alpha=245, outline="241f1b", width=4, shadow=False, layer="walls")
    m.rect(0, 0, 1, 24, color, alpha=245, outline="241f1b", width=4, shadow=False, layer="walls")
    m.rect(31, 0, 1, 24, color, alpha=245, outline="241f1b", width=4, shadow=False, layer="walls")


def columns(m: Composer, positions: list[tuple[float, float]], size: float = 1.15, round_col: bool = False) -> None:
    slug = "building_stone_tower_round" if round_col else "building_stone_tower_square"
    for cx, cy in positions:
        m.place("map_tile", slug, cx, cy, size, size, opacity=0.88, mode="cover", layer="columns")


def stone_debris(m: Composer, positions: list[tuple[float, float]], opacity: float = 0.72) -> None:
    for i, (cx, cy) in enumerate(positions):
        slug = "terrain_rocky_loose_stones" if i % 2 else "dungeon_rubble_floor"
        m.place("map_tile", slug, cx, cy, 2.0, 2.0, rotation=m.rng.choice([0, 90, 180, 270]), opacity=opacity, layer="debris")


def trees_around(m: Composer) -> None:
    positions = [
        (0.5, 0.0), (4.0, 0.3), (8.2, -0.1), (13.0, 0.1), (18.5, 0.0), (24.0, 0.2), (28.5, -0.1),
        (0.1, 4.0), (0.4, 8.0), (0.0, 13.0), (0.2, 18.0), (1.0, 21.0),
        (28.8, 3.4), (29.5, 8.5), (29.0, 13.5), (29.6, 18.4), (28.4, 21.0),
        (4.5, 21.5), (9.5, 22.0), (15.0, 21.4), (20.0, 21.8), (25.0, 21.2),
    ]
    for i, pos in enumerate(positions):
        slug = "terrain_forest_tree_group_dense" if i % 3 else "terrain_forest_tree_oak_large"
        m.place("map_tile", slug, pos[0], pos[1], 3.7, 3.7, rotation=m.rng.choice([0, 90, 180, 270]), opacity=0.95, layer="trees")


def furniture_rect(m: Composer, cx: float, cy: float, cw: float, ch: float, fill: str = "7a4f2a") -> None:
    m.rect(cx, cy, cw, ch, fill, alpha=230, outline="493628", width=5, radius=0.15, layer="furniture")


def make_stone_dungeon_room() -> Composer:
    m = Composer("stone_dungeon_room", 1101)
    m.tile("dungeon_floor_tile")
    wall_frame(m)
    m.rect(11, 7, 10, 10, "6b6f73", alpha=120, outline="3a332d", width=8, radius=0.15, layer="dais")
    m.rect(13, 9, 6, 6, "8a7d69", alpha=115, outline="493628", width=5, radius=0.15, layer="dais")
    columns(m, [(5.5, 5.0), (25.2, 5.2), (5.2, 18.1), (25.2, 18.3), (10.0, 11.5), (21.0, 11.5)], 1.25)
    stone_debris(m, [(3, 2), (15, 3), (26, 3), (4, 14), (23, 17), (14, 20), (27, 20)])
    m.place("map_tile", "dungeon_doorway", 14, 22.2, 4, 1.4, opacity=0.9, layer="door")
    m.place("item", "item_runic_stone", 15.0, 10.4, 2.0, 2.0, opacity=0.92, layer="centerpiece")
    m.vignette(alpha=60)
    return m


def make_dungeon_crossroads() -> Composer:
    m = Composer("dungeon_crossroads", 1102)
    m.tile("terrain_rocky_mountain_ground_tile", tint="2b2622", tint_amount=0.25)
    m.rect(13, 0, 6, 24, "6b6f73", alpha=230, outline="241f1b", width=6, layer="corridor")
    m.rect(0, 9, 32, 6, "6b6f73", alpha=230, outline="241f1b", width=6, layer="corridor")
    m.rect(10, 6, 12, 12, "777269", alpha=230, outline="241f1b", width=8, radius=0.2, layer="junction")
    for p in [(13, 1), (13, 5), (13, 17), (13, 21)]:
        m.place("map_tile", "dungeon_corridor_straight", p[0], p[1], 6, 4, opacity=0.34, layer="corridor_texture")
    for p in [(1, 9), (5, 9), (21, 9), (27, 9)]:
        m.place("map_tile", "dungeon_corridor_straight", p[0], p[1], 4, 6, rotation=90, opacity=0.34, layer="corridor_texture")
    columns(m, [(10.5, 6.5), (20.4, 6.5), (10.5, 16.5), (20.4, 16.5)], 1.05)
    stone_debris(m, [(7, 7), (23, 8), (8, 16), (23, 16)], 0.62)
    m.vignette(alpha=75)
    return m


def make_dungeon_prison_block() -> Composer:
    m = Composer("dungeon_prison_block", 1103)
    m.tile("dungeon_floor_tile", tint="3a332d", tint_amount=0.08)
    wall_frame(m)
    m.rect(13.5, 1, 5, 22, "6b6f73", alpha=145, outline="241f1b", width=6, layer="hall")
    for row in [2, 6.5, 11, 15.5, 20]:
        m.rect(1, row, 9, 3.1, "51483f", alpha=190, outline="241f1b", width=5, layer="cell")
        m.rect(22, row, 9, 3.1, "51483f", alpha=190, outline="241f1b", width=5, layer="cell")
        for x in [9.8, 21.1]:
            m.line([(x, row + 0.25), (x, row + 2.85)], "1c1917", width_cells=0.08, alpha=230, layer="bars")
            m.line([(x + 0.55, row + 0.25), (x + 0.55, row + 2.85)], "1c1917", width_cells=0.08, alpha=230, layer="bars")
    m.rect(12, 1.2, 8, 4, "493628", alpha=125, outline="241f1b", width=5, layer="guard_room")
    m.place("item", "item_key", 15.0, 2.1, 1.2, 1.2, opacity=0.95, layer="prop")
    m.place("item", "item_chest_closed", 17.0, 2.1, 1.6, 1.6, opacity=0.9, layer="prop")
    m.scatter("map_token", "prop_barrel_single", [(2.2, 2.4), (28.2, 6.6), (3.0, 15.8), (27.5, 20.2)], (1.1, 1.1), layer="prop")
    m.vignette(alpha=80)
    return m


def make_dungeon_trap_hall() -> Composer:
    m = Composer("dungeon_trap_hall", 1104)
    m.tile("terrain_rocky_mountain_ground_tile", tint="2b2622", tint_amount=0.28)
    m.rect(7, 2, 18, 20, "69645c", alpha=235, outline="241f1b", width=8, layer="hall")
    m.rect(10, 4, 12, 16, "777269", alpha=125, outline="3a332d", width=4, layer="walkway")
    for y in [5.5, 8.5, 11.5, 14.5, 17.5]:
        m.rect(13, y, 6, 1.0, "8a7d69", alpha=150, outline="493628", width=3, layer="trap_plate")
    m.place("map_tile", "dungeon_pit", 14, 10, 4, 4, opacity=0.88, layer="trap")
    m.place("item", "item_simple_trap", 15.2, 5.1, 1.6, 1.6, opacity=0.9, layer="trap")
    stone_debris(m, [(7.3, 3), (23, 4), (7.5, 19), (22.5, 18)], 0.6)
    m.place("map_tile", "dungeon_doorway", 13.5, 1.1, 5, 1.3, opacity=0.85, layer="door")
    m.place("map_tile", "dungeon_doorway", 13.5, 21.6, 5, 1.3, opacity=0.85, layer="door")
    m.vignette(alpha=80)
    return m


def make_crypt_chamber() -> Composer:
    m = Composer("crypt_chamber", 1105)
    m.tile("terrain_city_flagstone_floor_tile", tint="5d4978", tint_amount=0.08)
    wall_frame(m, "3a332d")
    m.rect(5, 3, 22, 18, "6b6f73", alpha=85, outline="2b2622", width=7, radius=0.25, layer="chamber")
    for x in [7, 12, 17, 22]:
        for y in [5, 15]:
            m.rect(x, y, 3.2, 5.0, "8a7d69", alpha=225, outline="493628", width=5, radius=0.12, layer="sarcophagus")
            m.rect(x + 0.45, y + 0.45, 2.3, 4.1, "6b6f73", alpha=95, outline="3a332d", width=2, radius=0.08, layer="sarcophagus_lid")
    m.place("map_token", "prop_church_altar", 14.2, 10.2, 3.6, 2.4, opacity=0.94, layer="altar")
    m.scatter("item", "item_lantern", [(5.3, 4.2), (26.0, 4.4), (5.2, 19.0), (26.0, 19.0)], (1.0, 1.0), layer="light")
    stone_debris(m, [(4, 2), (26, 2), (4, 19), (26, 19), (15, 2.2), (14.5, 20)], 0.55)
    m.vignette(color="1c1917", alpha=90)
    return m


def make_temple_sanctum() -> Composer:
    m = Composer("temple_sanctum", 1106)
    m.tile("terrain_city_inner_courtyard_tile", tint="d6c6aa", tint_amount=0.08)
    wall_frame(m, "6b6f73")
    columns(m, [(5.0, 5.0), (25.6, 5.0), (5.0, 17.8), (25.6, 17.8), (10.0, 6.8), (20.8, 6.8)], 1.35, True)
    m.ellipse(10.5, 7.1, 11, 9.8, "2f6f6a", alpha=55, outline="b58a36", outline_alpha=160, width=7, layer="ritual_floor")
    m.ellipse(12.8, 9.2, 6.4, 5.4, "314f7c", alpha=42, outline="d6c6aa", outline_alpha=130, width=5, layer="ritual_floor")
    m.place("map_token", "prop_church_altar", 14.0, 5.0, 4.0, 2.6, opacity=0.95, layer="altar")
    for x in [9, 13, 17, 21]:
        m.place("map_token", "prop_church_pew_straight", x, 16.5, 3.2, 1.2, opacity=0.9, layer="pews")
        m.place("map_token", "prop_church_pew_straight", x, 18.5, 3.2, 1.2, opacity=0.9, layer="pews")
    stone_debris(m, [(3, 2), (27, 2), (4, 21), (25, 20)], 0.5)
    m.vignette(alpha=55)
    return m


def make_tavern_ground_floor() -> Composer:
    m = Composer("tavern_ground_floor", 1107)
    m.tile("building_floor_wood_tile")
    wall_frame(m, "493628")
    m.place("map_token", "prop_tavern_bar_counter", 23.5, 2.2, 6.2, 3.0, opacity=0.95, layer="bar")
    m.rect(25.2, 5.1, 4.6, 2.0, "7a4f2a", alpha=210, outline="493628", width=4, radius=0.2, layer="bar")
    for pos in [(5, 4), (11, 4.2), (6, 10), (14, 10.5), (8, 17), (18, 17.5)]:
        m.place("map_token", "prop_tavern_table_chairs_round", pos[0], pos[1], 3.2, 3.2, rotation=m.rng.choice([0, 45, 90]), opacity=0.95, layer="tables")
    m.place("map_token", "prop_tavern_table_chairs_long", 18.2, 8.0, 5.4, 2.4, opacity=0.95, layer="tables")
    m.place("map_token", "prop_campfire", 2.4, 19.1, 2.5, 2.5, opacity=0.92, layer="hearth")
    m.rect(1.4, 18.1, 4.4, 4.4, "3a332d", alpha=160, outline="241f1b", width=4, radius=0.2, layer="hearth")
    m.scatter("map_token", "prop_barrel_stack", [(24, 7.8), (28, 7.6), (27.8, 20.0)], (1.7, 1.7), layer="storage")
    m.scatter("map_token", "prop_crate_stack", [(22, 19.6), (25, 19.5)], (1.6, 1.6), layer="storage")
    m.vignette(alpha=45)
    return m


def make_inn_guest_rooms() -> Composer:
    m = Composer("inn_guest_rooms", 1108)
    m.tile("building_floor_wood_tile", tint="d6c6aa", tint_amount=0.04)
    wall_frame(m, "493628")
    m.rect(13, 1, 6, 22, "7a4f2a", alpha=78, outline="493628", width=5, layer="hall")
    for x in [1.0, 19.0]:
        for y in [1.0, 6.6, 12.2, 17.8]:
            m.rect(x, y, 12, 5.0, "7a4f2a", alpha=42, outline="493628", width=6, layer="room")
            furniture_rect(m, x + 0.8, y + 0.8, 3.3, 2.0, "8a2f28")
            furniture_rect(m, x + 7.8, y + 0.9, 2.8, 1.4)
            m.place("map_tile", "building_wood_door_closed", 13.0 if x < 10 else 18.0, y + 1.9, 1.1, 1.1, opacity=0.8, layer="doors")
    m.scatter("item", "item_lantern", [(15.3, 3.2), (15.3, 9.0), (15.3, 14.8), (15.3, 20.5)], (0.9, 0.9), layer="lights")
    m.vignette(alpha=42)
    return m


def make_village_street_market() -> Composer:
    m = Composer("village_street_market", 1109)
    m.tile("terrain_village_grass_low_tile")
    m.line([(0, 12), (8, 11), (16, 12.3), (24, 11.4), (32, 12.2)], "7a4f2a", width_cells=4.2, alpha=205, outline="493628", outline_alpha=110, layer="road")
    m.texture_patch("terrain_village_dirt_road_straight", 0, 8.5, 8, 7, opacity=0.55)
    m.texture_patch("cobblestone_street", 12, 8.5, 8, 7, opacity=0.45)
    for x in [3, 7, 20, 25]:
        m.place("map_token", "prop_market_stall", x, 5.2 + (x % 2), 3.4, 2.7, rotation=m.rng.choice([0, 90, 180]), opacity=0.96, layer="market")
    m.place("map_token", "prop_wagon", 16.0, 14.0, 3.8, 2.5, rotation=-8, opacity=0.95, layer="wagon")
    m.place("map_token", "prop_village_well", 27.0, 15.8, 2.2, 2.2, opacity=0.95, layer="well")
    m.scatter("map_token", "prop_crate_stack", [(5, 8), (11, 7.5), (22, 8), (28, 7.3)], (1.4, 1.4), layer="goods")
    m.scatter("map_tile", "terrain_village_fence_straight", [(1, 2), (6, 2), (26, 21), (30, 20.5)], (4, 1), layer="fence")
    m.scatter("map_tile", "terrain_village_garden_rows", [(4, 17), (8, 17), (24, 3)], (3.2, 2.4), opacity=0.82, layer="garden")
    m.vignette(color="493628", alpha=30)
    return m


def make_blacksmith_workshop() -> Composer:
    m = Composer("blacksmith_workshop", 1110)
    m.tile("building_floor_packed_earth_tile")
    wall_frame(m, "493628")
    m.rect(1, 1, 30, 22, "7a4f2a", alpha=45, outline="493628", width=7, layer="workshop")
    m.rect(3, 3, 7, 7, "3a332d", alpha=160, outline="241f1b", width=6, radius=0.18, layer="forge")
    m.place("map_token", "prop_campfire", 4.4, 4.4, 3.6, 3.6, opacity=0.95, layer="forge")
    m.rect(12.2, 6.2, 2.2, 1.4, "6b6f73", alpha=235, outline="2b2622", width=4, radius=0.2, layer="anvil")
    for pos in [(16, 4), (22, 5), (17, 14), (24, 16)]:
        furniture_rect(m, pos[0], pos[1], 4.4, 1.7)
    for item, pos in [
        ("battleaxe_item", (17.0, 3.9)),
        ("warhammer_item", (23.1, 4.8)),
        ("longsword_item", (18.2, 14.0)),
        ("shield_steel_item", (24.7, 15.4)),
    ]:
        m.place("item", item, pos[0], pos[1], 1.4, 1.4, opacity=0.95, layer="tools")
    m.scatter("map_token", "prop_crate_stack", [(6.5, 17.0), (10.0, 18.0), (27.0, 20.0)], (1.5, 1.5), layer="storage")
    m.scatter("map_token", "prop_barrel_single", [(3.2, 15.5), (4.5, 16.5)], (1.0, 1.0), layer="storage")
    m.vignette(alpha=50)
    return m


def make_forest_clearing() -> Composer:
    m = Composer("forest_clearing", 1111)
    m.tile("terrain_village_grass_low_tile", tint="4f6b3a", tint_amount=0.1)
    m.ellipse(8, 5, 16, 12, "d6c6aa", alpha=36, outline="4f6b3a", outline_alpha=70, width=6, blur=2, layer="clearing")
    trees_around(m)
    m.scatter("map_tile", "terrain_forest_rock_cluster", [(7, 6), (22, 6.5), (10, 17.5), (24, 16)], (2.0, 2.0), opacity=0.85, layer="rocks")
    m.scatter("map_tile", "terrain_forest_fallen_log", [(5, 12), (18, 5), (23, 18)], (3.0, 1.2), opacity=0.9, layer="logs")
    m.scatter("map_tile", "terrain_forest_bush_patch", [(3, 7), (27, 9), (7, 20), (21, 21)], (2.5, 2.0), opacity=0.92, layer="underbrush")
    m.vignette(color="2b2622", alpha=45)
    return m


def make_forest_road_ambush() -> Composer:
    m = Composer("forest_road_ambush", 1112)
    m.tile("terrain_village_grass_low_tile", tint="4f6b3a", tint_amount=0.12)
    m.line([(0, 18), (6, 15), (13, 12), (18, 11), (25, 8), (32, 6)], "7a4f2a", width_cells=3.4, alpha=210, outline="493628", outline_alpha=105, layer="road")
    m.texture_patch("terrain_forest_dirt_path_curve", 4, 12, 5, 5, opacity=0.58)
    m.texture_patch("terrain_forest_dirt_path_straight", 13, 9, 6, 5, opacity=0.5)
    m.texture_patch("terrain_forest_dirt_path_curve", 23, 5, 5, 5, opacity=0.55)
    for pos in [(1, 1), (5, 1), (10, 2), (16, 1), (22, 0), (27, 1), (28, 11), (24, 14), (18, 16), (12, 18), (3, 20)]:
        m.place("map_tile", "terrain_forest_tree_group_dense", pos[0], pos[1], 4.0, 4.0, rotation=m.rng.choice([0, 90, 180, 270]), opacity=0.96, layer="trees")
    m.scatter("map_tile", "terrain_forest_fallen_log", [(8, 12), (21, 7), (24, 12)], (3.4, 1.3), opacity=0.9, layer="cover")
    m.scatter("map_tile", "terrain_forest_rock_cluster", [(11, 8), (17, 13), (27, 5.5)], (1.8, 1.8), opacity=0.85, layer="cover")
    m.vignette(alpha=50)
    return m


def make_cave_entrance() -> Composer:
    m = Composer("cave_entrance", 1113)
    m.tile("terrain_rocky_mountain_ground_tile")
    m.texture_patch("terrain_village_grass_low_tile", 0, 12, 14, 12, opacity=0.72)
    m.polygon([(11, 2), (28, 1), (31, 7), (28, 16), (17, 21), (10, 16)], "3a332d", alpha=220, outline="241f1b", outline_alpha=220, layer="cave_mass")
    m.ellipse(15.5, 5.5, 9, 10, "1c1917", alpha=245, outline="6b6f73", outline_alpha=170, width=10, layer="cave_mouth")
    m.place("map_tile", "cave_wall_edge", 12, 4, 12, 12, opacity=0.82, layer="cave_edge")
    m.line([(0, 18), (5, 16), (10, 15), (15, 13)], "7a4f2a", width_cells=3.0, alpha=145, outline="493628", outline_alpha=80, layer="approach")
    m.scatter("map_tile", "terrain_rocky_loose_stones", [(5, 9), (9, 5), (25, 18), (27, 9)], (2.0, 2.0), opacity=0.8, layer="rocks")
    m.scatter("map_tile", "terrain_forest_tree_pine_small", [(1, 13), (4, 20), (8, 18)], (2.5, 2.5), opacity=0.9, layer="trees")
    m.vignette(alpha=65)
    return m


def make_cavern_lake() -> Composer:
    m = Composer("cavern_lake", 1114)
    m.tile("cave_floor_tile", tint="3f6079", tint_amount=0.04)
    m.ellipse(8, 5, 16, 12, "3f6079", alpha=215, outline="2f6f6a", outline_alpha=100, width=8, layer="lake")
    m.ellipse(10, 7, 12, 8, "314f7c", alpha=120, blur=2, layer="deep_water")
    for pos in [(7, 4), (22, 5), (7, 16), (23, 15), (14, 3), (14, 18)]:
        m.place("map_tile", "water_shore_edge", pos[0], pos[1], 3, 2, rotation=m.rng.choice([0, 90, 180, 270]), opacity=0.62, layer="shore")
    m.scatter("map_tile", "stalagmite_cluster_piece", [(4, 3), (26, 3), (3, 17), (26, 18), (14, 20), (2, 10)], (2.3, 2.3), opacity=0.88, layer="stalagmites")
    m.scatter("map_tile", "terrain_rocky_natural_platform", [(2, 6), (24, 10), (15, 1)], (4, 3), opacity=0.55, layer="ledge")
    m.vignette(color="1c1917", alpha=85)
    return m


def make_mushroom_cavern() -> Composer:
    m = Composer("mushroom_cavern", 1115)
    m.tile("cave_floor_tile", tint="5d4978", tint_amount=0.08)
    m.texture_patch("terrain_swamp_mud_tile", 4, 4, 8, 8, tint="5d4978", tint_amount=0.08, opacity=0.55)
    m.texture_patch("terrain_swamp_mud_tile", 18, 12, 9, 8, tint="5d4978", tint_amount=0.08, opacity=0.55)
    fungus_positions = [(5, 5), (9, 7), (20, 5), (24, 8), (7, 16), (14, 14), (22, 17), (27, 14)]
    for i, pos in enumerate(fungus_positions):
        slug = "shrieker_fungus" if i % 2 else "violet_fungus"
        m.place("map_token", slug, pos[0], pos[1], 2.5, 2.5, rotation=m.rng.choice([0, 90, 180, 270]), opacity=0.88, layer="fungi")
        m.ellipse(pos[0] - 0.3, pos[1] - 0.2, 3.1, 2.8, "5d4978", alpha=32, blur=5, layer="spore_glow")
    m.scatter("map_tile", "stalagmite_cluster_piece", [(3, 11), (15, 3), (28, 20), (11, 19)], (2.1, 2.1), opacity=0.75, layer="stone")
    m.ellipse(15, 8.5, 5.5, 4.5, "2f6f6a", alpha=65, outline="3f6079", outline_alpha=70, width=4, layer="damp_pool")
    m.vignette(color="1c1917", alpha=95)
    return m


def make_sewer_crossing() -> Composer:
    m = Composer("sewer_crossing", 1116)
    m.tile("terrain_city_flagstone_floor_tile", tint="2f6f6a", tint_amount=0.07)
    wall_frame(m, "3a332d")
    m.line([(0, 8), (32, 8)], "2f6f6a", width_cells=4.2, alpha=215, outline="1c1917", outline_alpha=125, layer="channel")
    m.line([(16, 0), (16, 24)], "2f6f6a", width_cells=4.2, alpha=215, outline="1c1917", outline_alpha=125, layer="channel")
    m.rect(6, 10, 20, 4, "6b6f73", alpha=225, outline="493628", width=5, layer="walkway")
    m.rect(14, 2, 4, 20, "6b6f73", alpha=225, outline="493628", width=5, layer="walkway")
    m.place("map_tile", "wooden_bridge_segment", 7, 7.2, 6, 3, opacity=0.85, layer="bridge")
    m.place("map_tile", "wooden_bridge_segment", 19, 7.2, 6, 3, opacity=0.85, layer="bridge")
    m.place("map_tile", "wooden_bridge_segment", 13.2, 3.5, 3, 6, rotation=90, opacity=0.85, layer="bridge")
    m.place("map_tile", "wooden_bridge_segment", 13.2, 14.5, 3, 6, rotation=90, opacity=0.85, layer="bridge")
    m.scatter("map_token", "prop_crate_single", [(3, 18), (27, 3), (25, 19)], (1.2, 1.2), layer="debris")
    m.vignette(color="1c1917", alpha=75)
    return m


def make_bridge_over_chasm() -> Composer:
    m = Composer("bridge_over_chasm", 1117)
    m.tile("terrain_rocky_mountain_ground_tile")
    m.polygon([(0, 7), (9, 8), (15, 6), (24, 7), (32, 6), (32, 18), (23, 16), (16, 18), (7, 16), (0, 17)], "1c1917", alpha=245, outline="493628", outline_alpha=170, layer="chasm")
    m.line([(0, 12), (32, 12)], "2b2622", width_cells=6.8, alpha=160, layer="depth")
    for x in [3, 8, 13, 18, 23]:
        m.place("map_tile", "wooden_bridge_segment", x, 10, 6, 4, opacity=0.92, layer="bridge")
    m.scatter("map_tile", "terrain_rocky_cliff_edge", [(0, 5), (25, 4), (0, 15), (25, 16)], (7, 4), opacity=0.68, layer="cliff")
    m.scatter("map_tile", "terrain_rocky_loose_stones", [(5, 4), (24, 4), (7, 19), (26, 18)], (2, 2), opacity=0.86, layer="rocks")
    m.vignette(color="1c1917", alpha=85)
    return m


def make_river_ford() -> Composer:
    m = Composer("river_ford", 1118)
    m.tile("terrain_village_grass_low_tile", tint="d6c6aa", tint_amount=0.05)
    m.line([(0, 5), (7, 7), (13, 11), (20, 14), (32, 17)], "3f6079", width_cells=5.6, alpha=215, outline="2f6f6a", outline_alpha=85, layer="river")
    m.line([(0, 5), (7, 7), (13, 11), (20, 14), (32, 17)], "d6c6aa", width_cells=2.0, alpha=82, layer="ford")
    for pos in [(3, 5.5), (9, 8), (15, 12), (22, 14), (27, 16)]:
        m.place("map_tile", "river_segment", pos[0], pos[1], 4.0, 3.0, rotation=m.rng.choice([-18, 12, 25]), opacity=0.48, layer="water_texture")
    m.scatter("map_tile", "terrain_rocky_loose_stones", [(10, 10), (12, 11), (15, 12), (18, 13), (21, 14)], (1.2, 1.2), opacity=0.82, layer="ford_stones")
    m.scatter("map_tile", "terrain_forest_bush_patch", [(3, 12), (25, 7), (28, 20), (6, 18)], (2.5, 2), opacity=0.9, layer="bush")
    m.vignette(alpha=35)
    return m


def make_swamp_boardwalk() -> Composer:
    m = Composer("swamp_boardwalk", 1119)
    m.tile("terrain_swamp_dark_water_tile", tint="2f6f6a", tint_amount=0.04)
    for pos in [(1, 2), (12, 1), (22, 3), (4, 16), (18, 17), (26, 13)]:
        m.texture_patch("terrain_swamp_mud_tile", pos[0], pos[1], 8, 6, opacity=0.62)
    m.line([(2, 12), (10, 12), (18, 11), (30, 11)], "7a4f2a", width_cells=1.8, alpha=210, outline="493628", outline_alpha=180, layer="boardwalk")
    m.line([(14, 3), (14, 11), (17, 19)], "7a4f2a", width_cells=1.8, alpha=210, outline="493628", outline_alpha=180, layer="boardwalk")
    for pos in [(2, 10.5), (8, 10.5), (14, 9.5), (20, 9.7), (26, 9.8), (12.5, 3), (12.5, 7), (14.5, 14), (15.4, 18)]:
        m.place("map_tile", "wooden_bridge_segment", pos[0], pos[1], 4.2, 2.4, opacity=0.83, layer="planks")
    m.scatter("map_tile", "terrain_swamp_reeds_patch", [(4, 4), (25, 5), (6, 18), (28, 18), (20, 14)], (2.2, 2.2), opacity=0.88, layer="reeds")
    m.scatter("map_tile", "terrain_swamp_submerged_log", [(9, 5), (23, 19), (2, 16)], (3.2, 1.5), opacity=0.9, layer="logs")
    m.vignette(color="1c1917", alpha=80)
    return m


def make_desert_ruins() -> Composer:
    m = Composer("desert_ruins", 1120)
    m.tile("terrain_rocky_mountain_ground_tile", tint="c8923a", tint_amount=0.32)
    m.ellipse(3, 2, 26, 18, "d6c6aa", alpha=58, blur=8, layer="sand_drift")
    for pos in [(3, 4), (8, 4), (13, 4), (18, 4), (23, 4)]:
        m.place("map_tile", "building_stone_wall_straight", pos[0], pos[1], 4, 1.5, opacity=0.78, layer="ruins")
    for pos in [(3, 18), (8, 17.5), (22, 17), (27, 16.5)]:
        m.place("map_tile", "building_stone_wall_damaged", pos[0], pos[1], 4, 1.8, rotation=m.rng.choice([0, 90, 180]), opacity=0.8, layer="ruins")
    columns(m, [(6, 8), (12, 8.5), (20, 8), (25, 11.5), (10, 15), (17, 16)], 1.25, True)
    stone_debris(m, [(5, 12), (15, 6), (24, 6), (20, 19), (28, 12)], 0.58)
    m.place("item", "item_treasure_pile", 15.2, 11.2, 2.0, 2.0, opacity=0.82, layer="point_of_interest")
    m.vignette(color="7a4f2a", alpha=38)
    return m


def make_snowy_pass() -> Composer:
    m = Composer("snowy_pass", 1121)
    m.tile("terrain_rocky_mountain_ground_tile", tint="d6c6aa", tint_amount=0.48)
    m.line([(0, 17), (8, 14), (14, 11), (22, 9), (32, 5)], "6b6f73", width_cells=4.0, alpha=135, outline="d6c6aa", outline_alpha=110, layer="pass")
    m.scatter("map_tile", "terrain_rocky_cliff_edge", [(0, 0), (7, 0), (24, 0), (1, 19), (20, 18), (27, 16)], (7, 4), opacity=0.66, layer="cliff")
    for pos in [(3, 4), (10, 18), (18, 4), (26, 11), (23, 20)]:
        m.ellipse(pos[0], pos[1], 5.0, 2.8, "efe6d2", alpha=105, blur=5, layer="snow_drift")
    m.scatter("map_tile", "terrain_rocky_loose_stones", [(6, 14), (14, 10.5), (21, 8.5), (29, 5)], (1.6, 1.6), opacity=0.72, layer="rocks")
    m.vignette(color="3f6079", alpha=45)
    return m


def make_ship_deck() -> Composer:
    m = Composer("ship_deck", 1122)
    m.tile("building_floor_wood_tile", tint="7a4f2a", tint_amount=0.12)
    m.polygon([(3, 3), (16, 1), (29, 3), (31, 12), (28, 21), (16, 23), (4, 21), (1, 12)], "7a4f2a", alpha=90, outline="493628", outline_alpha=230, layer="hull_outline")
    m.rect(3.2, 2.8, 25.6, 1.0, "493628", alpha=210, outline="2b2622", width=4, layer="rail")
    m.rect(3.2, 20.2, 25.6, 1.0, "493628", alpha=210, outline="2b2622", width=4, layer="rail")
    m.rect(1.6, 4.8, 1.0, 14.3, "493628", alpha=210, outline="2b2622", width=4, layer="rail")
    m.rect(29.4, 4.8, 1.0, 14.3, "493628", alpha=210, outline="2b2622", width=4, layer="rail")
    m.ellipse(14.4, 9.6, 3.1, 3.1, "493628", alpha=235, outline="241f1b", width=6, layer="mast")
    m.line([(16, 2.5), (16, 21.5)], "493628", width_cells=0.15, alpha=190, layer="rigging")
    m.line([(6, 12), (27, 12)], "493628", width_cells=0.12, alpha=175, layer="rigging")
    m.scatter("map_token", "prop_crate_stack", [(6, 5), (23, 5), (7, 18), (24, 17)], (1.6, 1.6), layer="cargo")
    m.scatter("map_token", "prop_barrel_stack", [(10, 5.2), (20, 17.4)], (1.7, 1.7), layer="cargo")
    m.place("item", "item_rope", 18.2, 9.8, 1.8, 1.8, opacity=0.9, layer="cargo")
    m.vignette(alpha=35)
    return m


def make_wizard_laboratory() -> Composer:
    m = Composer("wizard_laboratory", 1123)
    m.tile("terrain_city_castle_floor_tile", tint="5d4978", tint_amount=0.07)
    wall_frame(m, "3a332d")
    m.ellipse(11, 7, 10, 9, "2f6f6a", alpha=50, outline="314f7c", outline_alpha=150, width=7, layer="arcane_circle")
    for pos in [(4, 4), (22, 4), (4, 16), (22, 16)]:
        furniture_rect(m, pos[0], pos[1], 5.5, 2.0)
    for item, pos in [
        ("spellbook_item", (5, 4.0)),
        ("item_potion", (23, 4.1)),
        ("potion_blue_item", (25, 4.0)),
        ("item_magic_crystal", (6, 16.1)),
        ("wand_item", (23, 16.0)),
        ("item_runic_stone", (16, 10.5)),
    ]:
        m.place("item", item, pos[0], pos[1], 1.4, 1.4, opacity=0.94, layer="apparatus")
    m.scatter("map_token", "prop_crate_stack", [(27, 19), (2, 20)], (1.4, 1.4), layer="storage")
    columns(m, [(6, 8.8), (24, 8.8), (6, 13.5), (24, 13.5)], 1.0, True)
    m.vignette(color="1c1917", alpha=70)
    return m


def make_throne_room() -> Composer:
    m = Composer("throne_room", 1124)
    m.tile("terrain_city_castle_floor_tile")
    wall_frame(m, "3a332d")
    m.rect(13, 1.5, 6, 20.5, "8a2f28", alpha=155, outline="493628", width=4, layer="carpet")
    m.rect(11, 3, 10, 4.5, "6b6f73", alpha=120, outline="493628", width=5, radius=0.15, layer="dais")
    m.rect(14.2, 4.0, 3.6, 2.4, "b58a36", alpha=210, outline="493628", width=5, radius=0.18, layer="throne")
    m.rect(14.6, 2.6, 2.8, 2.0, "b58a36", alpha=210, outline="493628", width=5, radius=0.15, layer="throne_back")
    columns(m, [(6, 5), (25, 5), (6, 10.5), (25, 10.5), (6, 16), (25, 16)], 1.3, True)
    m.scatter("map_tile", "building_castle_battlement_segment", [(2, 2), (25, 2), (2, 20), (25, 20)], (5, 1.5), opacity=0.72, layer="wall_detail")
    m.vignette(alpha=55)
    return m


def make_graveyard_night() -> Composer:
    m = Composer("graveyard_night", 1125)
    m.tile("terrain_village_grass_low_tile", tint="314f7c", tint_amount=0.34)
    m.line([(2, 23), (8, 17), (14, 13), (20, 8), (28, 2)], "493628", width_cells=2.0, alpha=165, outline="2b2622", outline_alpha=85, layer="path")
    m.rect(22, 2, 7, 5, "3a332d", alpha=185, outline="1c1917", width=6, radius=0.2, layer="crypt")
    m.ellipse(23.6, 3.2, 3.8, 3.4, "1c1917", alpha=230, outline="6b6f73", outline_alpha=140, width=5, layer="crypt_door")
    for x in [4, 8, 12, 17, 22, 27]:
        for y in [6, 10, 14, 18]:
            if (x + y) % 3:
                m.rect(x + m.rng.uniform(-0.3, 0.3), y + m.rng.uniform(-0.25, 0.25), 0.8, 1.2, "6b6f73", alpha=190, outline="2b2622", width=3, radius=0.18, layer="blank_gravestone")
    m.scatter("map_tile", "terrain_forest_tree_dead", [(2, 2), (28, 10), (3, 19), (18, 20)], (3.0, 3.0), opacity=0.8, layer="dead_trees")
    m.scatter("map_tile", "terrain_forest_rock_cluster", [(7, 3), (15, 17), (24, 20)], (1.6, 1.6), opacity=0.65, layer="rocks")
    m.vignette(color="1c1917", alpha=115)
    return m


FACTORIES = {
    "stone_dungeon_room": make_stone_dungeon_room,
    "dungeon_crossroads": make_dungeon_crossroads,
    "dungeon_prison_block": make_dungeon_prison_block,
    "dungeon_trap_hall": make_dungeon_trap_hall,
    "crypt_chamber": make_crypt_chamber,
    "temple_sanctum": make_temple_sanctum,
    "tavern_ground_floor": make_tavern_ground_floor,
    "inn_guest_rooms": make_inn_guest_rooms,
    "village_street_market": make_village_street_market,
    "blacksmith_workshop": make_blacksmith_workshop,
    "forest_clearing": make_forest_clearing,
    "forest_road_ambush": make_forest_road_ambush,
    "cave_entrance": make_cave_entrance,
    "cavern_lake": make_cavern_lake,
    "mushroom_cavern": make_mushroom_cavern,
    "sewer_crossing": make_sewer_crossing,
    "bridge_over_chasm": make_bridge_over_chasm,
    "river_ford": make_river_ford,
    "swamp_boardwalk": make_swamp_boardwalk,
    "desert_ruins": make_desert_ruins,
    "snowy_pass": make_snowy_pass,
    "ship_deck": make_ship_deck,
    "wizard_laboratory": make_wizard_laboratory,
    "throne_room": make_throne_room,
    "graveyard_night": make_graveyard_night,
}


def checksum(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def display_name(slug: str) -> str:
    return slug.replace("_", " ").title()


def update_database(paths: list[Path]) -> None:
    if not DB_PATH.exists():
        print(f"db skipped: {DB_PATH} not found")
        return
    conn = sqlite3.connect(DB_PATH)
    try:
        for path in paths:
            slug = path.stem
            rel = path.relative_to(ROOT / "dd3esheet" / "media").as_posix()
            size = path.stat().st_size
            digest = checksum(path)
            row = conn.execute("select id from sprites_spriteasset where Slug = ?", (slug,)).fetchone()
            if row:
                conn.execute(
                    """
                    update sprites_spriteasset
                       set Category = ?,
                           OriginalImage = ?,
                           Width = ?,
                           Height = ?,
                           FileSize = ?,
                           Checksum = ?,
                           DefaultGridWidth = ?,
                           DefaultGridHeight = ?,
                           UpdatedAt = datetime('now')
                     where Slug = ?
                    """,
                    ("map_tile", rel, WIDTH, HEIGHT, size, digest, GRID_W, GRID_H, slug),
                )
            else:
                conn.execute(
                    """
                    insert into sprites_spriteasset
                    (Name, Slug, Category, OriginalImage, AltText, Visibility, Owner_id,
                     Width, Height, FileSize, Checksum, DefaultGridWidth, DefaultGridHeight,
                     AnchorX, AnchorY, IsActive, CreatedAt, UpdatedAt)
                    values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                    """,
                    (
                        display_name(slug),
                        slug,
                        "map_tile",
                        rel,
                        f"{display_name(slug)} battle map",
                        "public",
                        None,
                        WIDTH,
                        HEIGHT,
                        size,
                        digest,
                        GRID_W,
                        GRID_H,
                        0.5,
                        0.5,
                        1,
                    ),
                )
        conn.commit()
    finally:
        conn.close()


def make_contact_sheet(paths: list[Path]) -> Path:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    thumb_w, thumb_h = 320, 240
    cols = 5
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * thumb_w, rows * thumb_h), (43, 38, 34))
    for i, path in enumerate(paths):
        img = Image.open(path).convert("RGB")
        img = ImageOps.fit(img, (thumb_w, thumb_h), method=Image.Resampling.LANCZOS)
        x = (i % cols) * thumb_w
        y = (i // cols) * thumb_h
        sheet.paste(img, (x, y))
    out = TMP_DIR / "battle_maps_final_contact.png"
    sheet.save(out, "PNG", optimize=True)
    return out


def validate(paths: list[Path]) -> None:
    missing = [slug for slug in BATTLE_MAPS if not (MAP_TILE_DIR / f"{slug}.png").exists()]
    if missing:
        raise RuntimeError(f"Missing generated maps: {missing}")
    for path in paths:
        img = Image.open(path)
        if img.size != (WIDTH, HEIGHT):
            raise RuntimeError(f"{path.name}: expected {(WIDTH, HEIGHT)}, got {img.size}")
        if img.mode not in {"RGB", "RGBA"}:
            raise RuntimeError(f"{path.name}: unexpected mode {img.mode}")
        layout = path.with_name(f"{path.stem}-layout.json")
        if not layout.exists():
            raise RuntimeError(f"{path.stem}: layout json missing")
        data = json.loads(layout.read_text(encoding="utf-8"))
        for op in data["operations"]:
            if op["kind"] in {"tile", "place"}:
                asset_path(op["source"], op["asset"])
    if DB_PATH.exists():
        conn = sqlite3.connect(DB_PATH)
        try:
            rows = conn.execute(
                """
                select Slug, Width, Height, DefaultGridWidth, DefaultGridHeight
                  from sprites_spriteasset
                 where Slug in ({})
                """.format(",".join("?" for _ in BATTLE_MAPS)),
                BATTLE_MAPS,
            ).fetchall()
        finally:
            conn.close()
        by_slug = {row[0]: row[1:] for row in rows}
        bad = {slug: by_slug.get(slug) for slug in BATTLE_MAPS if by_slug.get(slug) != (WIDTH, HEIGHT, GRID_W, GRID_H)}
        if bad:
            raise RuntimeError(f"Bad DB rows: {bad}")


def main() -> None:
    if set(FACTORIES) != set(BATTLE_MAPS):
        raise RuntimeError("FACTORIES and BATTLE_MAPS are out of sync")
    paths = []
    layouts = []
    for slug in BATTLE_MAPS:
        composer = FACTORIES[slug]()
        path, layout = composer.save()
        paths.append(path)
        layouts.append(layout)
        print(f"generated {slug}: {len(composer.ops)} ops")
    update_database(paths)
    validate(paths)
    contact = make_contact_sheet(paths)
    print(f"battle maps: {len(paths)} pngs, {len(layouts)} layouts")
    print(f"contact sheet: {contact}")


if __name__ == "__main__":
    main()
