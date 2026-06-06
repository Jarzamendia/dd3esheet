"""Helpers da mesa: resolução de sprites dos tokens e upload de imagens.

Reaproveita o app `sprites` como camada de armazenamento (categorias
`MAP_TILE` para fundos e `MAP_TOKEN` para miniaturas).
"""
from pathlib import Path

from django.urls import reverse

from sprites.models import SpriteAsset, SpriteVariant
from sprites.services import monster_ids_for_assets


# Só formatos raster. SVG/HTML podem carregar <script> e, servidos na mesma
# origem a partir de /media/, viram XSS armazenado. De propósito mais restrito
# que `sprites.IMAGE_EXTENSIONS` (que ainda permite svg para outros fluxos).
ALLOWED_UPLOAD_EXTENSIONS = ('png', 'jpg', 'jpeg', 'webp', 'gif')


def _is_allowed_upload(uploaded_file):
    ext = Path(getattr(uploaded_file, 'name', '') or '').suffix.lower().lstrip('.')
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        return False
    # content_type é spoofável pelo cliente, mas barra os casos triviais (text/html).
    content_type = (getattr(uploaded_file, 'content_type', '') or '').lower()
    return content_type == '' or content_type.startswith('image/')


def attach_sprites_to_tokens(tokens, variant=SpriteVariant.TOKEN_256):
    """Anexa `SpriteUrl/Alt/Width/Height` a cada token.

    Prefere a variante pedida (uma query só) e cai no original quando não há
    variante. Tokens sem sprite ficam com `SpriteUrl=''` (o template desenha um
    fallback SVG por Kind). Análogo a `sprites.services.attach_sprites_to_combatants`.
    """
    tokens = list(tokens)
    asset_ids = [t.SpriteAsset_id for t in tokens if getattr(t, 'SpriteAsset_id', None)]
    variants = {}
    monster_ids = {}
    if asset_ids:
        variants = {
            item.SpriteAsset_id: item
            for item in SpriteVariant.objects.filter(SpriteAsset_id__in=asset_ids, Variant=variant)
        }
        # Link token -> ficha do SRD, resolvido em lote (sem N+1).
        monster_ids = monster_ids_for_assets(asset_ids)
    for token in tokens:
        asset = token.SpriteAsset if getattr(token, 'SpriteAsset_id', None) else None
        selected = variants.get(token.SpriteAsset_id) if asset else None
        if selected and selected.File:
            token.SpriteUrl = selected.url
            token.SpriteWidth = selected.Width or asset.Width
            token.SpriteHeight = selected.Height or asset.Height
        elif asset:
            token.SpriteUrl = asset.original_url
            token.SpriteWidth = asset.Width
            token.SpriteHeight = asset.Height
        else:
            token.SpriteUrl = ''
            token.SpriteWidth = 0
            token.SpriteHeight = 0
        token.SpriteAlt = asset.display_alt if asset else (token.Label or '')
        monster_id = monster_ids.get(token.SpriteAsset_id) if asset else None
        token.SrdUrl = reverse('sdr:monster', args=[monster_id]) if monster_id else ''
    return tokens


def read_image_dimensions(file_obj):
    """(width, height) da imagem via Pillow; (0, 0) se Pillow ausente ou erro.

    Mantém o app funcional sem Pillow — as dimensões só viram defaults do canvas.
    """
    try:
        from PIL import Image
    except ImportError:
        return (0, 0)
    try:
        file_obj.seek(0)
        with Image.open(file_obj) as image:
            return image.size
    except Exception:
        return (0, 0)
    finally:
        try:
            file_obj.seek(0)
        except (AttributeError, OSError):
            pass


def create_sprite_from_upload(user, uploaded_file, name, category):
    """Cria um `SpriteAsset` a partir de um upload, lendo dimensões quando possível.

    Rejeita (retorna `None`) extensões não-raster: como o `save()` do model não
    roda os validadores do FileField, validamos a extensão aqui — caso contrário
    um SVG/HTML enviado pelo mestre e servido na mesma origem viraria XSS armazenado.

    Visibilidade `OWNER`: o sprite só aparece na biblioteca/picker do próprio
    mestre (a imagem em si é servida por URL de mídia, então jogadores anônimos
    conseguem renderizá-la no mapa normalmente).
    """
    if not _is_allowed_upload(uploaded_file):
        return None
    width, height = read_image_dimensions(uploaded_file)
    asset = SpriteAsset(
        Name=(name or '').strip() or uploaded_file.name,
        Category=category,
        Owner=user,
        Visibility=SpriteAsset.OWNER,
        Width=width,
        Height=height,
    )
    asset.OriginalImage = uploaded_file
    asset.save()
    return asset
