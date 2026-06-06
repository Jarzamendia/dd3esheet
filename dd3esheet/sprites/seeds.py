import functools
import json
from pathlib import Path

from .manifest_data import all_assets, category_for_type, footprint_to_grid
from .models import SpriteAsset, SpriteBinding


_CASAMENTO_PATH = Path(__file__).resolve().parent / 'fixtures' / 'monster_token_casamento.json'

# Pegada no mapa derivada do `size` do SDR (ver PLAN-SDR.md secao 0).
_SIZE_FOOTPRINT = {
    'fine': (1, 1), 'diminutive': (1, 1), 'tiny': (1, 1),
    'small': (1, 1), 'medium': (1, 1),
    'large': (2, 2), 'huge': (3, 3), 'gargantuan': (4, 4), 'colossal': (6, 6),
}


def footprint_for_size(size):
    """Mapeia o `size` do SDR_Monster para (grid_width, grid_height)."""
    key = (size or '').strip().lower().rstrip('+').strip()
    return _SIZE_FOOTPRINT.get(key, (1, 1))


@functools.lru_cache(maxsize=1)
def _monster_casamento():
    """{nome_no_SDR: slug_do_token_de_arte} — casamento auditado em PLAN-SDR.md."""
    if _CASAMENTO_PATH.exists():
        return json.loads(_CASAMENTO_PATH.read_text(encoding='utf-8'))
    return {}


CLASS_SPRITES = {
    'Fighter': ('Guerreiro', '#23395d', '#ffffff', 'FIG'),
    'Wizard': ('Mago', '#51306f', '#ffffff', 'MAG'),
    'Druid': ('Druida', '#2f5f3a', '#ffffff', 'DRU'),
    'Ranger': ('Ranger', '#5a4a24', '#ffffff', 'RAN'),
}

COMBATANT_SPRITES = {
    'player': ('Jogador', '#1f5fb0', '#ffffff', 'PJ'),
    'npc': ('NPC', '#5a5a5a', '#ffffff', 'NPC'),
    'enemy': ('Inimigo', '#a32020', '#ffffff', 'INI'),
}

MONSTER_SPRITES = {
    'Brown Bear': ('Urso Pardo', '#5a351d', '#ffffff', 'UR'),
    'Unicorn': ('Unicornio', '#f5f5f5', '#1a1a1a', 'UN'),
    'Wolf': ('Lobo', '#404852', '#ffffff', 'LO'),
}


def _asset(slug, name, category):
    asset = SpriteAsset.objects.filter(Slug=slug).first()
    if asset is None:
        asset = SpriteAsset(
            Slug=slug,
            Name=name,
            Category=category,
            AltText=name,
            Width=0,
            Height=0,
        )
    else:
        asset.Name = name
        asset.Category = category
        asset.AltText = name
    asset.Visibility = SpriteAsset.PUBLIC
    asset.IsActive = True
    asset.save()
    return asset


def _bind(target_type, target_key, purpose, asset):
    return SpriteBinding.objects.update_or_create(
        TargetType=target_type,
        TargetKey=target_key,
        Purpose=purpose,
        defaults={'SpriteAsset': asset},
    )[0]


def seed_sprites():
    assets = {}

    for class_name, (label, _background, _foreground, _short) in CLASS_SPRITES.items():
        asset = _asset(
            f'class-{class_name.lower()}',
            label,
            SpriteAsset.CLASS,
        )
        _bind(SpriteBinding.SDR_CLASS, class_name, SpriteBinding.CLASS_ICON, asset)
        _bind(SpriteBinding.SDR_CLASS, class_name, SpriteBinding.CLASS_PORTRAIT, asset)
        assets[class_name] = asset

    for kind, (name, _background, _foreground, _short) in COMBATANT_SPRITES.items():
        asset = _asset(f'combatant-{kind}', name, SpriteAsset.MAP_TOKEN)
        _bind(SpriteBinding.COMBATANT_KIND, kind, SpriteBinding.INITIATIVE_TOKEN, asset)
        assets[kind] = asset

    for monster_name, (label, _background, _foreground, _short) in MONSTER_SPRITES.items():
        slug = monster_name.lower().replace(' ', '-')
        asset = _asset(f'monster-{slug}', label, SpriteAsset.MONSTER)
        _bind(SpriteBinding.SDR_MONSTER, monster_name, SpriteBinding.MONSTER_TOKEN, asset)
        _bind(SpriteBinding.SDR_MONSTER, monster_name, SpriteBinding.MAP_TOKEN, asset)
        assets[monster_name] = asset

    return assets


def _existing_monster_asset(monster_id, name):
    """Asset ja vinculado a este monstro (idempotencia + preserva seed_sprites)."""
    keys = [str(monster_id)]
    if name:
        keys.append(name)
    binding = (
        SpriteBinding.objects
        .select_related('SpriteAsset')
        .filter(
            TargetType=SpriteBinding.SDR_MONSTER,
            Purpose=SpriteBinding.MONSTER_TOKEN,
            TargetKey__in=keys,
            SpriteAsset__IsActive=True,
        )
        .first()
    )
    return binding.SpriteAsset if binding else None


def _resolve_monster_asset(monster, casamento, summary):
    name = (monster.name or '').strip()

    # 1. Arte do casamento (PLAN-SDR.md 0.1) tem prioridade sobre placeholders.
    slug = casamento.get(name)
    if slug:
        art = SpriteAsset.objects.filter(Slug=slug).first()
        if art is not None:
            summary['reused'] += 1
            return art

    # 2. Vinculo ja existente (idempotencia dos placeholders + binds manuais).
    existing = _existing_monster_asset(monster.pk, name)
    if existing is not None:
        summary['reused'] += 1
        return existing

    # 3. Placeholder sem imagem, com pegada derivada do size.
    grid_width, grid_height = footprint_for_size(monster.size)
    asset = SpriteAsset(
        Slug=f'monster-{monster.pk}',
        Name=name or f'Monster {monster.pk}',
        Category=SpriteAsset.MONSTER,
        AltText=name,
        Visibility=SpriteAsset.PUBLIC,
        IsActive=True,
        DefaultGridWidth=grid_width,
        DefaultGridHeight=grid_height,
    )
    asset.save()
    summary['created'] += 1
    return asset


def seed_monster_tokens():
    """Cria/reutiliza um SpriteAsset por monstro do SDR e o vincula por id e nome.

    Reutiliza a arte ja existente quando ha casamento (PLAN-SDR.md secao 0.1);
    senao cria um placeholder sem imagem com a pegada derivada do `size`.
    Idempotente: a 2a rodada reaproveita os vinculos existentes.
    """
    from sdr.models import SDR_Monster

    casamento = _monster_casamento()
    summary = {'created': 0, 'reused': 0, 'bound': 0, 'total': 0}

    for monster in SDR_Monster.objects.using('sdr').all().iterator():
        name = (monster.name or '').strip()
        asset = _resolve_monster_asset(monster, casamento, summary)
        for key in (str(monster.pk), name):
            if not key:
                continue
            for purpose in (SpriteBinding.MONSTER_TOKEN, SpriteBinding.MAP_TOKEN):
                _bind(SpriteBinding.SDR_MONSTER, key, purpose, asset)
                summary['bound'] += 1
        summary['total'] += 1

    return summary


def seed_sprite_library():
    summary = {'created': 0, 'updated': 0, 'total': 0}
    for asset in all_assets():
        grid_width, grid_height = footprint_to_grid(asset.get('footprint'))
        _, was_created = SpriteAsset.objects.update_or_create(
            Slug=asset['id'],
            defaults={
                'Name': asset.get('name') or asset['id'].replace('_', ' ').title(),
                'Category': category_for_type(asset['type']),
                'AltText': asset.get('description', ''),
                'Visibility': SpriteAsset.PUBLIC,
                'Owner': None,
                'DefaultGridWidth': grid_width,
                'DefaultGridHeight': grid_height,
                'IsActive': True,
            },
        )
        if was_created:
            summary['created'] += 1
        else:
            summary['updated'] += 1
    summary['total'] = summary['created'] + summary['updated']
    return summary
