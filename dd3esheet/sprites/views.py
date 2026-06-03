from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from .manifest_data import (
    NEGATIVE, OUTPUT_RULES, PALETTE, PRINCIPLES, SIZE_BY_FOOTPRINT, STYLE,
    TYPE_SPECS, all_assets, category_for_type, footprint_to_grid,
    group_for_section, sections, section_groups, type_spec_for_type,
)
from .models import SpriteAsset, SpriteVariant
from .services import manifest_for_assets


CREATURE_GROUP_KEYS = {
    'pcs', 'companions', 'npcs', 'humanoids', 'undead', 'beasts', 'giants',
    'aberrations', 'dragons', 'outsiders', 'constructs', 'plants', 'swarms',
    'magical',
}
TYPE_ORDER = (
    'TABLETOP_TOKEN', 'PROP_TOKEN', 'STATUS_MARKER', 'CLASS_ICON',
    'PORTRAIT', 'BATTLE_MAP', 'CITY_OR_WORLD_MAP', 'MAP_PIECE',
)
FOOTPRINT_ORDER = ('1x1', '2x1', '1x2', '2x2', '3x3', '4x4', '6x6')


def _parse_ids(raw):
    ids = []
    for value in (raw or '').split(','):
        try:
            ids.append(int(value.strip()))
        except (TypeError, ValueError):
            continue
    return ids


def _manifest_by_slug():
    return {asset['id']: asset for asset in all_assets()}


def _slot_class(asset_type):
    if asset_type == 'PORTRAIT':
        return 'sl-slot--portrait'
    if asset_type == 'STATUS_MARKER':
        return 'sl-slot--marker'
    if asset_type in ('BATTLE_MAP', 'CITY_OR_WORLD_MAP'):
        return 'sl-slot--map'
    if asset_type == 'MAP_PIECE':
        return 'sl-slot--hex'
    return 'sl-slot--circle'


def _grid_class(group_key):
    if group_key in ('battle_maps', 'world_maps'):
        return 'sl-grid--wide'
    if group_key == 'markers':
        return 'sl-grid--tight'
    return 'sl-grid--std'


def _library_row(asset, manifest_asset=None, group=None):
    manifest_asset = manifest_asset or {}
    group = group or group_for_section(manifest_asset.get('section', ''))
    asset_type = manifest_asset.get('type') or asset.Category
    type_spec = type_spec_for_type(asset_type)
    footprint = manifest_asset.get('footprint')
    grid_width, grid_height = footprint_to_grid(footprint)
    return {
        'asset': asset,
        'id': asset.Slug,
        'name': asset.Name,
        'description': manifest_asset.get('description') or asset.AltText,
        'section': manifest_asset.get('section', ''),
        'type': asset_type,
        'type_label': type_spec['label'],
        'canvas': manifest_asset.get('canvas') or type_spec.get('canvas', ''),
        'alpha': type_spec.get('alpha', ''),
        'format': manifest_asset.get('format', ''),
        'footprint': footprint or '',
        'grid_label': f'{grid_width}x{grid_height}',
        'size_label': SIZE_BY_FOOTPRINT.get(footprint, '') if group.get('key') in CREATURE_GROUP_KEYS else '',
        'category': asset.Category,
        'glyph': group.get('glyph', 'shield'),
        'accent': group.get('accent', '--iron'),
        'group_key': group.get('key', 'other'),
        'group_label': group.get('label', ''),
        'slot_class': _slot_class(asset_type),
        'has_grid': asset_type == 'BATTLE_MAP',
        'image_url': asset.original_url,
        'alt': asset.display_alt,
    }


def _library_groups_for_user(user):
    manifest_rows = all_assets()
    visible_assets = {
        asset.Slug: asset
        for asset in (
            SpriteAsset.objects
            .active()
            .visible_to(user)
            .filter(Slug__in=[row['id'] for row in manifest_rows])
            .order_by('Name')
        )
    }
    groups = []
    for group in section_groups():
        rows = []
        for manifest_asset in group['assets']:
            asset = visible_assets.get(manifest_asset['id'])
            if asset:
                rows.append(_library_row(asset, manifest_asset, group))
        groups.append({
            **group,
            'assets': rows,
            'visible_count': len(rows),
            'grid_class': _grid_class(group['key']),
        })
    return groups


def _type_filters():
    counts = {}
    for asset in all_assets():
        counts[asset['type']] = counts.get(asset['type'], 0) + 1
    return [
        {'type': item, 'label': type_spec_for_type(item)['label'], 'count': counts[item]}
        for item in TYPE_ORDER
        if item in counts
    ]


def _footprint_filters():
    counts = {}
    for asset in all_assets():
        footprint = asset.get('footprint')
        if footprint:
            counts[footprint] = counts.get(footprint, 0) + 1
    return [
        {'footprint': item, 'label': item, 'count': counts[item]}
        for item in FOOTPRINT_ORDER
        if item in counts
    ]


@login_required
def library(request):
    groups = _library_groups_for_user(request.user)
    asset_count = sum(group['visible_count'] for group in groups)
    return render(request, 'sprites/library.html', {
        'groups': groups,
        'assets_count': asset_count,
        'manifest_total': len(all_assets()),
        'type_filters': _type_filters(),
        'footprint_filters': _footprint_filters(),
    })


@login_required
def art_spec(request):
    return render(request, 'sprites/art_spec.html', {
        'style': STYLE,
        'negative': NEGATIVE,
        'palette': PALETTE,
        'principles': PRINCIPLES,
        'output_rules': OUTPUT_RULES,
        'type_specs': TYPE_SPECS,
        'size_by_footprint': SIZE_BY_FOOTPRINT,
        'sections': sections(),
        'total': len(all_assets()),
    })


@login_required
def asset_detail(request, slug):
    asset = get_object_or_404(
        SpriteAsset.objects.active().visible_to(request.user),
        Slug=slug,
    )
    manifest_asset = _manifest_by_slug().get(asset.Slug)
    row = _library_row(asset, manifest_asset, group_for_section((manifest_asset or {}).get('section', '')))
    return render(request, 'sprites/partials/_detail.html', {'row': row})


@login_required
def search(request):
    query = (request.GET.get('q') or '').strip()
    category = (request.GET.get('category') or '').strip()
    assets = SpriteAsset.objects.active().visible_to(request.user)
    if category:
        assets = assets.filter(Category=category)
    if query:
        assets = assets.filter(
            Q(Name__icontains=query) |
            Q(Slug__icontains=query) |
            Q(AltText__icontains=query)
        )
    rows = [
        {
            'id': asset.id,
            'name': asset.Name,
            'category': asset.Category,
            'url': asset.original_url,
            'alt': asset.display_alt,
        }
        for asset in assets.order_by('Name')[:30]
    ]
    return JsonResponse({'sprites': rows})


@login_required
def manifest(request):
    ids = _parse_ids(request.GET.get('ids'))
    variant = request.GET.get('variant') or SpriteVariant.TOKEN_128
    assets = (
        SpriteAsset.objects
        .active()
        .visible_to(request.user)
        .filter(id__in=ids)
        .order_by('Name')
    )
    return JsonResponse({'sprites': manifest_for_assets(assets, variant=variant)})
