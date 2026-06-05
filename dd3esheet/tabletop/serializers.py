"""Contrato JSON da cena: usado pelo shell do editor, pelo polling do live e
pelo endpoint scene/save (round-trip)."""
from django.db import transaction

from .calculations import axial_to_pixel, pixel_to_axial
from .models import FogCell, TerrainCell, Token
from .services import attach_sprites_to_tokens
from .terrains import DEFAULT_TERRAIN, is_valid_terrain

_VALID_FACTIONS = {Token.PARTY, Token.ALLY, Token.NEUTRAL, Token.ENEMY_FACTION}
_VALID_SIZES = {'sm', 'md', 'lg', 'xl'}
_VALID_KINDS = {Token.PLAYER, Token.ENEMY, Token.NPC, Token.OBJECT}
MAX_CELLS = 6000
MAX_TOKENS = 400


# --- serialização (DB -> JSON) ---------------------------------------------

def serialize_token(token, grid_size):
    q, r = pixel_to_axial(token.X, token.Y, grid_size) if grid_size else (0, 0)
    return {
        'id': token.id,
        'assetId': token.SpriteAsset_id,
        'spriteUrl': getattr(token, 'SpriteUrl', '') or '',
        'name': token.Label,
        'kind': token.Kind,
        'faction': token.Faction,
        'q': q, 'r': r,
        'hp': token.HP, 'maxHp': token.MaxHP,
        'conditions': token.Conditions or [],
        'size': token.Size,
        'rotation': token.Rotation,
        'hidden': token.Hidden,
        'movable': token.MovableByPlayers,
    }


def serialize_scene(m, is_owner):
    if m is None:
        return None
    grid_size = m.GridSize
    fog = list(m.fogcell_set.all())
    fog_keys = {(c.Q, c.R) for c in fog}

    tokens_qs = list(m.token_set.select_related('SpriteAsset').all())
    attach_sprites_to_tokens(tokens_qs)
    tokens = []
    for t in tokens_qs:
        q, r = pixel_to_axial(t.X, t.Y, grid_size) if grid_size else (0, 0)
        if not is_owner and (t.Hidden or (q, r) in fog_keys):
            continue
        tokens.append(serialize_token(t, grid_size))

    terrain = [{'q': c.Q, 'r': c.R, 'terrain': c.Terrain}
               for c in m.terraincell_set.all()]

    return {
        'mapId': m.id,
        'name': m.Name,
        'grid': {'size': grid_size, 'cols': _cols(m), 'rows': _rows(m), 'showGrid': m.ShowGrid},
        'background': m.Background.original_url if (m.Background and m.Background.original_url) else '',
        'terrain': terrain,
        'fog': [{'q': c.Q, 'r': c.R} for c in fog],
        'tokens': tokens,
        'isOwner': is_owner,
    }


def _cols(m):
    return max(8, round(m.WidthPx / m.GridSize)) if m.GridSize else 30


def _rows(m):
    return max(6, round(m.HeightPx / m.GridSize)) if m.GridSize else 22


# --- aplicação (JSON -> DB, autosave) --------------------------------------

def _clean_conditions(value):
    return [c for c in (value or []) if isinstance(c, str)][:6]


def _clamp(v, lo, hi):
    try:
        return max(lo, min(hi, int(v)))
    except (TypeError, ValueError):
        return None


@transaction.atomic
def apply_scene_payload(m, payload):
    """Aplica a cena inteira (last-write-wins do mestre).

    Retorna ``id_map`` ({tempId: id_real}) p/ o cliente reconciliar tokens novos.
    """
    if isinstance(payload.get('name'), str) and payload['name'].strip():
        m.Name = payload['name'].strip()[:120]
    grid = payload.get('grid') or {}
    cols = _clamp(grid.get('cols'), 8, 80)
    rows = _clamp(grid.get('rows'), 6, 60)
    if cols and rows and m.GridSize:
        m.WidthPx = cols * m.GridSize
        m.HeightPx = rows * m.GridSize
    if 'showGrid' in grid:
        m.ShowGrid = bool(grid['showGrid'])
    m.save()

    # terreno: replace
    TerrainCell.objects.filter(Map=m).delete()
    cells = []
    for c in (payload.get('terrain') or [])[:MAX_CELLS]:
        key = c.get('terrain')
        if not is_valid_terrain(key):
            key = DEFAULT_TERRAIN
        cells.append(TerrainCell(Map=m, Q=int(c['q']), R=int(c['r']), Terrain=key))
    TerrainCell.objects.bulk_create(cells, ignore_conflicts=True)

    # névoa: replace
    FogCell.objects.filter(Map=m).delete()
    fog = [FogCell(Map=m, Q=int(c['q']), R=int(c['r'])) for c in (payload.get('fog') or [])[:MAX_CELLS]]
    FogCell.objects.bulk_create(fog, ignore_conflicts=True)

    # tokens: upsert por id; deleta os ausentes
    incoming = (payload.get('tokens') or [])[:MAX_TOKENS]
    keep_ids = set()
    id_map = {}
    for i, td in enumerate(incoming):
        kept_id, temp_id = _upsert_token(m, td, order=i)
        keep_ids.add(kept_id)
        if temp_id is not None:
            id_map[temp_id] = kept_id
    Token.objects.filter(Map=m).exclude(id__in=keep_ids).delete()
    return id_map


def _upsert_token(m, td, order):
    """Atualiza (por id) ou cria um token. Retorna (id_resultante, tempId|None)."""
    q, r = int(td.get('q', 0)), int(td.get('r', 0))
    x, y = axial_to_pixel(q, r, m.GridSize) if m.GridSize else (0, 0)
    faction = td.get('faction') if td.get('faction') in _VALID_FACTIONS else Token.ENEMY_FACTION
    size = td.get('size') if td.get('size') in _VALID_SIZES else 'md'
    kind = td.get('kind') if td.get('kind') in _VALID_KINDS else Token.ENEMY
    fields = dict(
        Label=(td.get('name') or '')[:80],
        Kind=kind,
        Faction=faction,
        Size=size,
        HP=int(td.get('hp', 0)),
        MaxHP=int(td.get('maxHp', 0)),
        Conditions=_clean_conditions(td.get('conditions')),
        Rotation=(int(td.get('rotation', 0)) % 360),
        Hidden=bool(td.get('hidden', False)),
        MovableByPlayers=bool(td.get('movable', False)),
        X=x, Y=y, Order=order,
    )
    sprite_id = td.get('assetId')
    fields['SpriteAsset_id'] = sprite_id if sprite_id else None

    temp_id = td.get('tempId')
    tid = td.get('id')
    if tid:
        updated = Token.objects.filter(Map=m, id=tid).update(**fields)
        if updated:
            return tid, None
    created = Token.objects.create(Map=m, **fields)
    return created.id, temp_id
