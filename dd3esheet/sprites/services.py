from django.core.files.base import ContentFile
from django.db.models import Case, IntegerField, Q, Value, When

from .models import SpriteAsset, SpriteBinding, SpriteVariant


_VARIANT_DIMENSIONS = {
    SpriteVariant.THUMB_64: (64, 64),
    SpriteVariant.ICON_96: (96, 96),
    SpriteVariant.TOKEN_128: (128, 128),
    SpriteVariant.TOKEN_256: (256, 256),
    SpriteVariant.PORTRAIT_320: (320, 320),
    SpriteVariant.PORTRAIT_640: (640, 640),
}


def _first_bound_asset(target_type, target_key, purpose):
    key = (target_key or '').strip()
    if not key:
        return None
    binding = (
        SpriteBinding.objects
        .select_related('SpriteAsset')
        .filter(
            TargetType=target_type,
            TargetKey=key,
            Purpose=purpose,
            SpriteAsset__IsActive=True,
        )
        .first()
    )
    return binding.SpriteAsset if binding else None


def sprite_for_class(class_name, purpose=SpriteBinding.CLASS_ICON):
    key = (class_name or '').strip()
    if not key:
        return None
    binding = (
        SpriteBinding.objects
        .select_related('SpriteAsset')
        .filter(
            Q(TargetType=SpriteBinding.SDR_CLASS) |
            Q(TargetType=SpriteBinding.CHARACTER_CLASS),
            TargetKey=key,
            Purpose=purpose,
            SpriteAsset__IsActive=True,
        )
        .annotate(_priority=Case(
            When(TargetType=SpriteBinding.SDR_CLASS, then=Value(0)),
            default=Value(1),
            output_field=IntegerField(),
        ))
        .order_by('_priority')
        .first()
    )
    return binding.SpriteAsset if binding else None


def sprite_for_monster(monster_id=None, monster_name=None, purpose=SpriteBinding.MONSTER_TOKEN):
    if monster_id:
        found = _first_bound_asset(SpriteBinding.SDR_MONSTER, str(monster_id), purpose)
        if found:
            return found
    return _first_bound_asset(SpriteBinding.SDR_MONSTER, monster_name, purpose)


def monster_id_for_asset(asset):
    """Id do monstro do SDR vinculado a este asset, ou None.

    Permite montar `reverse('sdr:monster', [id])` para o link token -> SRD.
    Usa o vinculo MONSTER_TOKEN cuja TargetKey e numerica (o id do monstro).
    """
    if not asset:
        return None
    bindings = SpriteBinding.objects.filter(
        TargetType=SpriteBinding.SDR_MONSTER,
        Purpose=SpriteBinding.MONSTER_TOKEN,
        SpriteAsset=asset,
    )
    for binding in bindings:
        if binding.TargetKey.isdigit():
            return int(binding.TargetKey)
    return None


def monster_ids_for_assets(asset_ids):
    """{asset_id: monster_id} para os assets vinculados a um monstro do SDR.

    Resolve em lote (uma query) para evitar N+1 ao montar muitos tokens. Mesma
    regra de `monster_id_for_asset`: usa o vínculo MONSTER_TOKEN cuja TargetKey é
    numérica (o id do monstro).
    """
    asset_ids = [aid for aid in (asset_ids or []) if aid]
    if not asset_ids:
        return {}
    result = {}
    bindings = (
        SpriteBinding.objects
        .filter(
            TargetType=SpriteBinding.SDR_MONSTER,
            Purpose=SpriteBinding.MONSTER_TOKEN,
            SpriteAsset_id__in=asset_ids,
        )
        .values_list('SpriteAsset_id', 'TargetKey')
    )
    for asset_id, target_key in bindings:
        if asset_id in result:
            continue
        if target_key and target_key.isdigit():
            result[asset_id] = int(target_key)
    return result


def preferred_variant(asset, variant=SpriteVariant.TOKEN_128):
    if not asset:
        return None
    prefetched = getattr(asset, '_prefetched_objects_cache', {}).get('variants')
    if prefetched is not None:
        for item in prefetched:
            if item.Variant == variant:
                return item
        return None
    return asset.variants.filter(Variant=variant).first()


def sprite_image_data(asset, variant=SpriteVariant.TOKEN_128):
    if not asset:
        return {'url': '', 'alt': '', 'width': 0, 'height': 0}
    selected = preferred_variant(asset, variant)
    if selected and selected.File:
        return {
            'url': selected.url,
            'alt': asset.display_alt,
            'width': selected.Width or asset.Width,
            'height': selected.Height or asset.Height,
        }
    return {
        'url': asset.original_url,
        'alt': asset.display_alt,
        'width': asset.Width,
        'height': asset.Height,
    }


def attach_sprites_to_combatants(combatants, variant=SpriteVariant.TOKEN_128):
    combatants = list(combatants)
    kind_keys = {(c.Kind or '').strip() for c in combatants if not getattr(c, 'SpriteAsset_id', None)}
    fallback_assets = {}
    if kind_keys:
        fallback_assets = {
            binding.TargetKey: binding.SpriteAsset
            for binding in (
                SpriteBinding.objects
                .select_related('SpriteAsset')
                .filter(
                    TargetType=SpriteBinding.COMBATANT_KIND,
                    TargetKey__in=kind_keys,
                    Purpose=SpriteBinding.INITIATIVE_TOKEN,
                    SpriteAsset__IsActive=True,
                )
            )
        }

    explicit_assets = [
        c.SpriteAsset for c in combatants
        if getattr(c, 'SpriteAsset_id', None) and getattr(c, 'SpriteAsset', None)
    ]
    assets = list({asset.id: asset for asset in [*explicit_assets, *fallback_assets.values()] if asset}.values())
    variants = {
        item.SpriteAsset_id: item
        for item in SpriteVariant.objects.filter(SpriteAsset_id__in=[asset.id for asset in assets], Variant=variant)
    }

    for combatant in combatants:
        asset = getattr(combatant, 'SpriteAsset', None) if getattr(combatant, 'SpriteAsset_id', None) else None
        if not asset:
            asset = fallback_assets.get((combatant.Kind or '').strip())
        selected = variants.get(asset.id) if asset else None
        data = {
            'url': selected.url if selected and selected.File else (asset.original_url if asset else ''),
            'alt': asset.display_alt if asset else '',
            'width': selected.Width if selected else (asset.Width if asset else 0),
            'height': selected.Height if selected else (asset.Height if asset else 0),
        }
        combatant.SpriteAssetResolved = asset
        combatant.SpriteUrl = data['url']
        combatant.SpriteAlt = data['alt']
        combatant.SpriteWidth = data['width']
        combatant.SpriteHeight = data['height']
    return combatants


def manifest_for_assets(assets, variant=SpriteVariant.TOKEN_128):
    assets = list(assets)
    variants = {
        item.SpriteAsset_id: item
        for item in SpriteVariant.objects.filter(SpriteAsset_id__in=[asset.id for asset in assets], Variant=variant)
    }
    rows = []
    for asset in assets:
        selected = variants.get(asset.id)
        url = selected.url if selected and selected.File else asset.original_url
        rows.append({
            'id': asset.id,
            'name': asset.Name,
            'category': asset.Category,
            'url': url,
            'alt': asset.display_alt,
            'width': selected.Width if selected else asset.Width,
            'height': selected.Height if selected else asset.Height,
            'grid': {
                'w': asset.DefaultGridWidth,
                'h': asset.DefaultGridHeight,
                'anchor_x': float(asset.AnchorX),
                'anchor_y': float(asset.AnchorY),
            },
        })
    return rows


def generate_variant(asset, variant):
    """Gera uma variante quando Pillow esta instalado.

    Sem Pillow, mantem o app funcional retornando None; os consumidores usam o
    original como fallback. Isso evita acoplar ficha/iniciativa ao processamento
    de imagem durante testes ou ambientes mínimos.
    """
    try:
        from PIL import Image
    except ImportError:
        return None

    import io

    size = _VARIANT_DIMENSIONS.get(variant)
    if not size or not asset.OriginalImage:
        return None

    asset.OriginalImage.open('rb')
    with Image.open(asset.OriginalImage) as image:
        image.thumbnail(size)
        output = io.BytesIO()
        image.save(output, format='WEBP', quality=86)
        width, height = image.size

    filename = f'{asset.Slug}-{variant}.webp'
    item, _created = SpriteVariant.objects.get_or_create(SpriteAsset=asset, Variant=variant)
    item.Width = width
    item.Height = height
    item.Format = 'WEBP'
    item.File.save(filename, ContentFile(output.getvalue()), save=False)
    item.save()
    return item


def generate_missing_variants(asset, variants=None):
    variants = variants or (SpriteVariant.THUMB_64, SpriteVariant.TOKEN_128, SpriteVariant.PORTRAIT_320)
    generated = []
    for variant in variants:
        if not asset.variants.filter(Variant=variant).exists():
            item = generate_variant(asset, variant)
            if item:
                generated.append(item)
    return generated
