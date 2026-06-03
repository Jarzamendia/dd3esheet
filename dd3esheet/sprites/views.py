from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .models import SpriteAsset, SpriteVariant
from .services import manifest_for_assets


def _parse_ids(raw):
    ids = []
    for value in (raw or '').split(','):
        try:
            ids.append(int(value.strip()))
        except (TypeError, ValueError):
            continue
    return ids


@login_required
def search(request):
    query = (request.GET.get('q') or '').strip()
    category = (request.GET.get('category') or '').strip()
    assets = SpriteAsset.objects.active().visible_to(request.user)
    if category:
        assets = assets.filter(Category=category)
    if query:
        assets = assets.filter(Name__icontains=query)
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
