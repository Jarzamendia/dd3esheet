"""Paleta fixa de terrenos da Mesa (espelhada em scene_canvas.js).

`color` para fundos sólidos; `texture` referencia um SpriteAsset MAP_TILE pelo
Slug conhecido (semeado pelo seed_sprite_library). As cores são semânticas
(grama=verde, água=azul) e NÃO seguem o chrome Parchment.
"""

TERRAINS = [
    {'id': 'stone',   'label': 'Pedra',     'kind': 'color',   'color': '#d8d4ca'},
    {'id': 'dungeon', 'label': 'Masmorra',  'kind': 'texture', 'slug': 'terrain-dungeon', 'color': '#3a3340'},
    {'id': 'cobble',  'label': 'Calçada',   'kind': 'texture', 'slug': 'terrain-cobblestone', 'color': '#6d6660'},
    {'id': 'woods',   'label': 'Floresta',  'kind': 'texture', 'slug': 'terrain-woods', 'color': '#3f5230'},
    {'id': 'grass',   'label': 'Grama',     'kind': 'color',   'color': '#54692f'},
    {'id': 'dirt',    'label': 'Terra',     'kind': 'color',   'color': '#6a4d31'},
    {'id': 'water',   'label': 'Água',      'kind': 'color',   'color': '#2b5266'},
    {'id': 'sand',    'label': 'Areia',     'kind': 'color',   'color': '#bda468'},
    {'id': 'rock',    'label': 'Rocha',     'kind': 'color',   'color': '#363139'},
]

TERRAIN_KEYS = [t['id'] for t in TERRAINS]
DEFAULT_TERRAIN = 'stone'
TEXTURE_SLUGS = {t['slug']: t['id'] for t in TERRAINS if t['kind'] == 'texture'}


def is_valid_terrain(key):
    return key in TERRAIN_KEYS
