from .manifest_data import all_assets, category_for_type, footprint_to_grid
from .models import SpriteAsset, SpriteBinding


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


def seed_sprite_library():
    summary = {'created': 0, 'updated': 0, 'total': 0}
    for asset in all_assets():
        grid_width, grid_height = footprint_to_grid(asset.get('footprint'))
        _, was_created = SpriteAsset.objects.update_or_create(
            Slug=asset['id'],
            defaults={
                'Name': asset['id'].replace('_', ' ').title(),
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
