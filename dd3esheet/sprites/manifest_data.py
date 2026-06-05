"""Sprite manifest data and display metadata for the Parchment & Ink library."""
import functools
import json
import re
from copy import deepcopy
from pathlib import Path

from .models import SpriteAsset


_FIXTURES_PATH = Path(__file__).resolve().parent / 'fixtures'
_MANIFEST_PATH = _FIXTURES_PATH / 'sprite_manifest.json'
_EXPANSION_MANIFEST_PATHS = (
    _FIXTURES_PATH / 'sprite_manifest_tokens_expansion.json',
)

TYPE_TO_CATEGORY = {
    'TABLETOP_TOKEN': SpriteAsset.MAP_TOKEN,
    'PROP_TOKEN': SpriteAsset.MAP_TOKEN,
    'ITEM_SPRITE': SpriteAsset.ITEM,
    'MAP_MARKER': SpriteAsset.GENERIC,
    'BATTLE_MAP': SpriteAsset.MAP_TILE,
    'CITY_OR_WORLD_MAP': SpriteAsset.MAP_TILE,
    'MAP_PIECE': SpriteAsset.MAP_TILE,
    'CLASS_ICON': SpriteAsset.CLASS,
    'PORTRAIT': SpriteAsset.CHARACTER,
    'STATUS_MARKER': SpriteAsset.GENERIC,
}

# Style and negative prompt for the house "Parchment & Ink" art direction.
STYLE = (
    "Warm parchment storybook style: digital illustration that looks hand-inked "
    "for a classic fantasy tabletop RPG sourcebook. Confident dark ink outlines of "
    "even medium weight, semi-flat cel shading with 2-3 tonal steps per color, "
    "subtle aged-paper grain, soft overhead lighting. Mood: heroic, readable, "
    "friendly, timeless."
)

NEGATIVE = (
    "No text, letters, numbers, labels, UI, frames, borders, watermarks, signatures, "
    "grids, token rings, base discs, health bars, or selection marks anywhere."
)

# 14 cores da paleta da casa (nome, hex, uso) - de theme.css / specs.js do handoff.
PALETTE = [
    {'name': 'Dark Ink', 'hex': '#2b2622', 'usage': 'contornos, texto'},
    {'name': 'Parchment', 'hex': '#efe6d2', 'usage': 'papel base'},
    {'name': 'Ochre', 'hex': '#c8923a', 'usage': 'destaque quente'},
    {'name': 'Leather', 'hex': '#7a4f2a', 'usage': 'couro/madeira'},
    {'name': 'Forest', 'hex': '#4f6b3a', 'usage': 'vegetação'},
    {'name': 'Iron', 'hex': '#6b6f73', 'usage': 'metal/pedra'},
    {'name': 'Deep Red', 'hex': '#8a2f28', 'usage': 'perigo/sangue'},
    {'name': 'Steel Blue', 'hex': '#3f6079', 'usage': 'água/aço'},
    {'name': 'Bone', 'hex': '#d6c6aa', 'usage': 'osso/claro'},
    {'name': 'Shadow Brown', 'hex': '#493628', 'usage': 'sombra'},
    {'name': 'Muted Gold', 'hex': '#b58a36', 'usage': 'ouro suave'},
    {'name': 'Arcane Teal', 'hex': '#2f6f6a', 'usage': 'magia'},
    {'name': 'Royal Blue', 'hex': '#314f7c', 'usage': 'nobreza/arcano'},
    {'name': 'Dull Violet', 'hex': '#5d4978', 'usage': 'sombrio/feérico'},
]

PRINCIPLES = [
    {'title': 'Inked & timeless', 'body': 'Contornos escuros confiantes, cel shading semi-plano, grão de papel sutil.'},
    {'title': 'Readable at size', 'body': 'Legível em miniatura na mesa; nada de detalhe que some a 32-96 px.'},
    {'title': 'Moderate palette', 'body': 'Saturação moderada da família de 14 cores; sem neon, pastel ou 3D plástico.'},
    {'title': 'No UI in art', 'body': 'Sem texto, molduras, anéis de base, grids ou marcas de UI dentro da imagem.'},
]

OUTPUT_RULES = [
    {'title': 'Arquivos separados', 'body': 'Um arquivo por asset; nome = id snake_case.'},
    {'title': 'Alpha correto', 'body': 'Tokens/props/ícones: PNG transparente. Mapas: PNG/WebP opaco full-bleed.'},
    {'title': 'Composição segura', 'body': 'Tokens circle-safe (detalhe no círculo inscrito). Map pieces tile-edge-to-edge.'},
    {'title': 'Sem grid desenhado', 'body': 'Mapas alinham ao grid invisível (64px=5ft / hex), mas não desenham linhas.'},
]

TYPE_SPECS = {
    'TABLETOP_TOKEN': {
        'label': 'Tabletop Token',
        'canvas': '512x512',
        'alpha': 'Transparent PNG',
        'spec': 'Vista de cima ~60°, miniatura pintada. Um sujeito centralizado, circle-safe, '
                'sombra de contato pequena. Sem anel de base.',
    },
    'PROP_TOKEN': {
        'label': 'Prop Token',
        'canvas': '512x512',
        'alpha': 'Transparent PNG',
        'spec': 'Vista de cima. Um objeto/prop centralizado com sombra de contato. '
                'Circle-safe salvo se intencionalmente retangular.',
    },
    'ITEM_SPRITE': {
        'label': 'Item Sprite',
        'canvas': '512x512',
        'alpha': 'Transparent PNG',
        'spec': 'Item de mapa em vista top-down, centralizado, com sombra de contato suave.',
    },
    'MAP_MARKER': {
        'label': 'Map Marker',
        'canvas': '256x256',
        'alpha': 'Transparent PNG',
        'spec': 'Pictograma de local ou objetivo; legivel a 32x32. Sem texto/numeros.',
    },
    'STATUS_MARKER': {
        'label': 'Status Marker',
        'canvas': '256x256',
        'alpha': 'Transparent PNG',
        'spec': 'Pictograma simples; legível a 32×32. Sem texto/números.',
    },
    'CLASS_ICON': {
        'label': 'Class Icon',
        'canvas': '512x512',
        'alpha': 'Transparent PNG',
        'spec': 'Emblema/silhueta de classe; legível a 96×96. Sem moldura, sem texto.',
    },
    'PORTRAIT': {
        'label': 'Portrait',
        'canvas': '640x640',
        'alpha': 'Opaque parchment background',
        'spec': 'Busto/meio-corpo no estilo inked sobre fundo parchment. Sem texto/moldura.',
    },
    'BATTLE_MAP': {
        'label': 'Battle Map',
        'canvas': '2048x1536',
        'alpha': 'Opaque, full bleed',
        'spec': 'Top-down em grid de 64px (1 célula=5ft) sem desenhar linhas. Sem tokens/texto.',
    },
    'CITY_OR_WORLD_MAP': {
        'label': 'City / World Map',
        'canvas': '2048x1536',
        'alpha': 'Opaque, full bleed',
        'spec': 'Cartografia top-down em parchment envelhecido. Sem nomes/texto/bússola.',
    },
    'MAP_PIECE': {
        'label': 'Map Piece',
        'canvas': '512x512',
        'alpha': 'Transparent PNG',
        'spec': 'Bloco modular que tile em grid hex pointy-top (odd-r, 1 hex=5ft). '
                'NÃO circle-safe; preenche o hex borda a borda.',
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
    manifest = json.loads(_MANIFEST_PATH.read_text(encoding='utf-8'))
    for path in _EXPANSION_MANIFEST_PATHS:
        if path.exists():
            manifest = _merge_manifest(manifest, json.loads(path.read_text(encoding='utf-8')))
    return _with_manifest_totals(manifest)


def _merge_manifest(base, expansion):
    """Merge additive expansion sections while keeping sprite ids unique."""
    merged = deepcopy(base)
    sections_by_name = {section['name']: section for section in merged['sections']}
    seen_ids = {asset['id'] for section in merged['sections'] for asset in section['assets']}

    for section in expansion.get('sections', []):
        target = sections_by_name.get(section['name'])
        if target is None:
            target = {'name': section['name'], 'assets': []}
            merged['sections'].append(target)
            sections_by_name[section['name']] = target

        for asset in section.get('assets', []):
            if asset['id'] in seen_ids:
                raise ValueError(f"Duplicate sprite manifest id: {asset['id']}")
            target['assets'].append(asset)
            seen_ids.add(asset['id'])

    return merged


def _with_manifest_totals(manifest):
    manifest = deepcopy(manifest)
    by_type = {}
    total = 0
    for section in manifest['sections']:
        for asset in section['assets']:
            total += 1
            by_type[asset['type']] = by_type.get(asset['type'], 0) + 1
    manifest['total'] = total
    manifest['byType'] = by_type
    return manifest


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


@functools.lru_cache(maxsize=1)
def tile_kind_by_slug():
    """{slug: 'base'|'detail'} para todos os assets da categoria MAP_TILE.

    Map pieces usam seu ``terrain_kind``; mapas completos (BATTLE_MAP e
    CITY_OR_WORLD_MAP) sao sempre 'detail' — nao sao terreno basico tileavel.
    Outros tipos ficam de fora do mapa.
    """
    out = {}
    for asset in all_assets():
        atype = asset.get('type')
        if atype == 'MAP_PIECE':
            out[asset['id']] = asset.get('terrain_kind', 'detail')
        elif atype in ('BATTLE_MAP', 'CITY_OR_WORLD_MAP'):
            out[asset['id']] = 'detail'
    return out


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


def footprint_feet(footprint):
    """'NxM' -> 'AxB ft' (x5); None/sem match -> None."""
    if not footprint:
        return None
    match = re.match(r'(\d+)x(\d+)', footprint)
    if not match:
        return None
    return f'{int(match.group(1)) * 5}×{int(match.group(2)) * 5} ft'


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
