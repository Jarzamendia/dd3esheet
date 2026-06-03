"""Sprite manifest data and display metadata for the Parchment & Ink library."""
import functools
import json
import re
from pathlib import Path

from .models import SpriteAsset


_MANIFEST_PATH = Path(__file__).resolve().parent / 'fixtures' / 'sprite_manifest.json'

TYPE_TO_CATEGORY = {
    'TABLETOP_TOKEN': SpriteAsset.MAP_TOKEN,
    'PROP_TOKEN': SpriteAsset.MAP_TOKEN,
    'BATTLE_MAP': SpriteAsset.MAP_TILE,
    'CITY_OR_WORLD_MAP': SpriteAsset.MAP_TILE,
    'MAP_PIECE': SpriteAsset.MAP_TILE,
    'CLASS_ICON': SpriteAsset.CLASS,
    'PORTRAIT': SpriteAsset.CHARACTER,
    'STATUS_MARKER': SpriteAsset.GENERIC,
}

TYPE_SPECS = {
    'TABLETOP_TOKEN': {
        'label': 'Tabletop Token',
        'canvas': '512x512',
        'alpha': 'Transparent PNG',
    },
    'PROP_TOKEN': {
        'label': 'Prop Token',
        'canvas': '512x512',
        'alpha': 'Transparent PNG',
    },
    'STATUS_MARKER': {
        'label': 'Status Marker',
        'canvas': '256x256',
        'alpha': 'Transparent PNG',
    },
    'CLASS_ICON': {
        'label': 'Class Icon',
        'canvas': '512x512',
        'alpha': 'Transparent PNG',
    },
    'PORTRAIT': {
        'label': 'Portrait',
        'canvas': '640x640',
        'alpha': 'Opaque parchment background',
    },
    'BATTLE_MAP': {
        'label': 'Battle Map',
        'canvas': '2048x1536',
        'alpha': 'Opaque, full bleed',
    },
    'CITY_OR_WORLD_MAP': {
        'label': 'City / World Map',
        'canvas': '2048x1536',
        'alpha': 'Opaque, full bleed',
    },
    'MAP_PIECE': {
        'label': 'Map Piece',
        'canvas': '512x512',
        'alpha': 'Transparent PNG',
    },
}

GROUPS = [
    {'key': 'class_icons', 'label': 'Class Icons', 'accent': '--muted-gold', 'glyph': 'shield', 'sections': ['CLASS ICONS']},
    {'key': 'class_portraits', 'label': 'Class Portraits', 'accent': '--muted-gold', 'glyph': 'bust', 'sections': ['CLASS PORTRAITS']},
    {'key': 'pcs', 'label': 'Player Characters', 'accent': '--royal-blue', 'glyph': 'hero', 'sections': ['PLAYER CHARACTER TOKENS']},
    {'key': 'companions', 'label': 'Companions & Familiars', 'accent': '--forest', 'glyph': 'paw', 'sections': ['COMPANION AND FAMILIAR TOKENS']},
    {'key': 'npcs', 'label': 'NPCs', 'accent': '--leather', 'glyph': 'person', 'sections': ['NPC TOKENS', 'ADDITIONAL NPC TOKENS']},
    {'key': 'humanoids', 'label': 'Humanoid Enemies', 'accent': '--deep-red', 'glyph': 'swords', 'sections': ['HUMANOID ENEMY TOKENS']},
    {'key': 'undead', 'label': 'Undead', 'accent': '--dull-violet', 'glyph': 'skull', 'sections': ['UNDEAD TOKENS', 'ADDITIONAL UNDEAD TOKENS']},
    {'key': 'beasts', 'label': 'Beasts & Vermin', 'accent': '--forest', 'glyph': 'claw', 'sections': ['BEAST AND VERMIN TOKENS', 'ADDITIONAL ANIMAL AND VERMIN TOKENS']},
    {'key': 'giants', 'label': 'Giants & Monstrous', 'accent': '--leather', 'glyph': 'club', 'sections': ['GIANT AND MONSTROUS HUMANOID TOKENS', 'ADDITIONAL GIANT TOKENS']},
    {'key': 'aberrations', 'label': 'Aberrations', 'accent': '--arcane-teal', 'glyph': 'eye', 'sections': ['ABERRATION TOKENS', 'ADDITIONAL ABERRATION TOKENS']},
    {'key': 'dragons', 'label': 'Dragons', 'accent': '--deep-red', 'glyph': 'wing', 'sections': ['DRAGON TOKENS', 'ADDITIONAL DRAGON TOKENS']},
    {'key': 'outsiders', 'label': 'Elementals & Outsiders', 'accent': '--arcane-teal', 'glyph': 'flame', 'sections': ['ELEMENTAL AND OUTSIDER TOKENS', 'ADDITIONAL OUTSIDER TOKENS']},
    {'key': 'constructs', 'label': 'Constructs & Oozes', 'accent': '--iron', 'glyph': 'gear', 'sections': ['CONSTRUCT AND OOZE TOKENS', 'ADDITIONAL CONSTRUCT TOKENS']},
    {'key': 'plants', 'label': 'Plants & Fey', 'accent': '--forest', 'glyph': 'leaf', 'sections': ['PLANT AND FEY TOKENS']},
    {'key': 'swarms', 'label': 'Swarms & Summons', 'accent': '--arcane-teal', 'glyph': 'swarm', 'sections': ['SWARM AND SUMMONING TOKENS']},
    {'key': 'magical', 'label': 'Magical Beasts', 'accent': '--muted-gold', 'glyph': 'feather', 'sections': ['MAGICAL BEAST TOKENS']},
    {'key': 'props_dungeon', 'label': 'Props - Dungeon & Town', 'accent': '--leather', 'glyph': 'chest', 'sections': ['PROP TOKENS: DUNGEON, TAVERN, AND TOWN']},
    {'key': 'props_wild', 'label': 'Props - Wilderness', 'accent': '--forest', 'glyph': 'pine', 'sections': ['PROP TOKENS: WILDERNESS AND TERRAIN']},
    {'key': 'markers', 'label': 'Markers & Status', 'accent': '--ochre', 'glyph': 'flag', 'sections': ['MARKER AND STATUS SPRITES']},
    {'key': 'items', 'label': 'Items', 'accent': '--muted-gold', 'glyph': 'potion', 'sections': ['ITEM SPRITES']},
    {'key': 'battle_maps', 'label': 'Battle Maps', 'accent': '--steel-blue', 'glyph': 'mapgrid', 'sections': ['BATTLE MAPS']},
    {'key': 'world_maps', 'label': 'City & World Maps', 'accent': '--ochre', 'glyph': 'worldmap', 'sections': ['CITY AND WORLD MAPS']},
    {'key': 'map_pieces', 'label': 'Map Pieces', 'accent': '--iron', 'glyph': 'hex', 'sections': ['MAP PIECES']},
]

SIZE_BY_FOOTPRINT = {
    '1x1': 'Tiny - Medium',
    '2x1': 'Medium (long)',
    '1x2': 'Medium (long)',
    '2x2': 'Large',
    '3x3': 'Huge',
    '4x4': 'Gargantuan',
    '6x6': 'Colossal',
}


@functools.lru_cache(maxsize=1)
def _manifest():
    return json.loads(_MANIFEST_PATH.read_text(encoding='utf-8'))


def all_assets():
    """Return a flat list of all manifest assets with their source section."""
    rows = []
    for section in _manifest()['sections']:
        for asset in section['assets']:
            row = dict(asset)
            row.setdefault('section', section['name'])
            rows.append(row)
    return rows


def sections():
    """Return raw manifest sections in manifest order."""
    return _manifest()['sections']


def category_for_type(asset_type):
    return TYPE_TO_CATEGORY.get(asset_type, SpriteAsset.GENERIC)


def footprint_to_grid(footprint):
    """Convert a manifest footprint like '2x2' into grid dimensions."""
    if not footprint:
        return (1, 1)
    match = re.match(r'(\d+)x(\d+)', footprint)
    if not match:
        return (1, 1)
    return (int(match.group(1)), int(match.group(2)))


def type_spec_for_type(asset_type):
    return TYPE_SPECS.get(asset_type, {'label': asset_type or 'Unknown', 'canvas': '', 'alpha': ''})


def section_groups():
    """Return display groups with manifest assets attached."""
    assets_by_section = {section['name']: section['assets'] for section in sections()}
    grouped = []
    for group in GROUPS:
        assets = []
        for section_name in group['sections']:
            assets.extend(assets_by_section.get(section_name, []))
        grouped.append({**group, 'assets': assets, 'count': len(assets)})
    return grouped


def group_for_section(section_name):
    for group in GROUPS:
        if section_name in group['sections']:
            return group
    return {'key': 'other', 'label': section_name, 'accent': '--iron', 'glyph': 'shield'}
