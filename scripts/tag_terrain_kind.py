"""Tagueia `terrain_kind` em todos os MAP_PIECE dos manifestos de sprites.

Idempotente: rode quantas vezes quiser. Slugs em BASE_SLUGS viram 'base';
qualquer outro MAP_PIECE vira 'detail'.

Preserva a formatacao de cada arquivo (indent, escapes \\u, trailing newline)
para manter o diff minimo.
"""
import json
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent.parent / 'dd3esheet' / 'sprites' / 'fixtures'

# (path, indent) -- indent espelha o estilo existente de cada arquivo.
MANIFESTS = [
    (FIXTURES / 'sprite_manifest.json', 1),
    (FIXTURES / 'sprite_manifest_tokens_expansion.json', 2),
]

BASE_SLUGS = {
    # manifesto base
    'dungeon_floor_tile', 'cave_floor_tile', 'deep_water_tile',
    'shallow_water_tile', 'grass_field_tile', 'rocky_ground_patch',
    'swamp_muck_tile', 'cobblestone_street',
    # expansao -- terrenos
    'terrain_village_grass_low_tile', 'terrain_village_irregular_stone_floor',
    'terrain_city_courtyard_stone_tile', 'terrain_city_flagstone_floor_tile',
    'terrain_city_castle_floor_tile', 'terrain_city_inner_courtyard_tile',
    'terrain_swamp_dark_water_tile', 'terrain_swamp_mud_tile',
    'terrain_swamp_dry_ground_tile', 'terrain_rocky_mountain_ground_tile',
    # expansao -- pisos de construcao (chao solido tileavel)
    'building_floor_wood_tile', 'building_floor_packed_earth_tile',
}


def tag(path, indent):
    raw = path.read_text(encoding='utf-8')
    trailing_nl = raw.endswith('\n')
    data = json.loads(raw)
    changed = 0
    for section in data.get('sections', []):
        for asset in section.get('assets', []):
            if asset.get('type') != 'MAP_PIECE':
                continue
            kind = 'base' if asset['id'] in BASE_SLUGS else 'detail'
            if asset.get('terrain_kind') != kind:
                asset['terrain_kind'] = kind
                changed += 1
    out = json.dumps(data, indent=indent, ensure_ascii=True)
    if trailing_nl:
        out += '\n'
    path.write_text(out, encoding='utf-8')
    return changed


if __name__ == '__main__':
    for manifest, indent in MANIFESTS:
        n = tag(manifest, indent)
        print(f'{manifest.name}: {n} map pieces atualizados')
