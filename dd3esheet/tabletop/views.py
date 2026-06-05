import json

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from sprites.models import SpriteAsset

from .calculations import axial_to_pixel, snap_to_grid, token_visible_to
from .models import FogRegion, GameTable, Map, TerrainCell, Token
from .serializers import apply_scene_payload, serialize_scene
from .services import attach_sprites_to_tokens, create_sprite_from_upload
from .terrains import TERRAINS


TOKEN_LIBRARY_CATEGORIES = (SpriteAsset.MAP_TOKEN, SpriteAsset.ITEM, SpriteAsset.GENERIC)


# --- helpers ---------------------------------------------------------------

def _int_or(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _bool_post(request, field):
    """Checkbox: presente e marcado → True; ausente (desmarcado) → False."""
    return request.POST.get(field) in ('1', 'on', 'true', 'True')


def _clean_kind(value):
    valid = {Token.PLAYER, Token.ENEMY, Token.NPC, Token.OBJECT}
    return value if value in valid else Token.ENEMY


def _clean_grid(value):
    return value if value in {Map.HEX, Map.FREE} else Map.HEX


def _parse_cells(raw):
    """Parse 'q,r;q,r;...' into ordered, deduplicated integer tuples."""
    seen, cells = set(), []
    for part in (raw or '').split(';'):
        bits = part.split(',')
        if len(bits) != 2:
            continue
        q, r = _int_or(bits[0]), _int_or(bits[1])
        if q is None or r is None or (q, r) in seen:
            continue
        seen.add((q, r))
        cells.append((q, r))
    return cells


def _is_owner(request, table):
    return request.user.is_authenticated and table.Owner_id == request.user.id


def _get_owned(request, slug):
    """Acha a mesa pelo slug; 404 se não existe, 403 se quem pede não é o dono."""
    table = get_object_or_404(GameTable, Slug=slug)
    if not _is_owner(request, table):
        raise PermissionDenied
    return table


def _resolve_sprite(request, field, category):
    """Sprite vindo de upload (`<field>File`) ou da biblioteca (`<field>Id`)."""
    upload = request.FILES.get(f'{field}File')
    if upload:
        name = request.POST.get(f'{field}Name') or request.POST.get('Label') or request.POST.get('Name')
        return create_sprite_from_upload(request.user, upload, name, category)
    sprite_id = _int_or(request.POST.get(f'{field}Id'))
    if sprite_id:
        return SpriteAsset.objects.active().visible_to(request.user).filter(pk=sprite_id).first()
    return None


def _terrain_palette_payload(user):
    """Paleta de terreno + URLs resolvidas das texturas (por Slug conhecido)."""
    slug_to_url = {}
    texture_slugs = [t['slug'] for t in TERRAINS if t.get('kind') == 'texture']
    if texture_slugs:
        assets = SpriteAsset.objects.active().visible_to(user).filter(Slug__in=texture_slugs)
        for asset in assets:
            slug_to_url[asset.Slug] = asset.original_url
    out = []
    for t in TERRAINS:
        entry = dict(t)
        if t.get('kind') == 'texture':
            entry['url'] = slug_to_url.get(t['slug'], '')
        out.append(entry)
    return out


def _sprite_library(user, category):
    assets = SpriteAsset.objects.active().visible_to(user)
    if isinstance(category, (list, tuple, set)):
        assets = assets.filter(Category__in=category)
    else:
        assets = assets.filter(Category=category)
    return list(assets.order_by('Name'))


def _canvas_context(table, m, is_owner):
    """Tokens filtered by visibility plus terrain cells with pixel centers."""
    fogs = list(m.fogregion_set.all()) if m else []
    tokens = []
    terrain = []
    if m:
        candidates = list(m.token_set.select_related('SpriteAsset').all())
        tokens = [t for t in candidates if token_visible_to(t, fogs, is_owner)]
        attach_sprites_to_tokens(tokens)
        for t in tokens:  # tamanho em px p/ o template (pegada × célula)
            t.PxWidth = t.GridWidth * m.GridSize
            t.PxHeight = t.GridHeight * m.GridSize
        if m.GridMode == Map.HEX:
            terrain = list(m.terraincell_set.select_related('SpriteAsset').all())
            for cell in terrain:
                cell.Cx, cell.Cy = axial_to_pixel(cell.Q, cell.R, m.GridSize)
    return {
        'table': table,
        'map': m,
        'tokens': tokens,
        'fogs': fogs,
        'terrain': terrain,
        'is_owner': is_owner,
        'slug': table.Slug,
    }


def _render_canvas(request, table, m, is_owner):
    return render(request, 'tabletop/partials/_canvas.html', _canvas_context(table, m, is_owner))


def _render_editor_body(request, table, m):
    ctx = _canvas_context(table, m, is_owner=True)
    ctx['token_sprites'] = _sprite_library(request.user, TOKEN_LIBRARY_CATEGORIES)
    ctx['tile_sprites'] = _sprite_library(request.user, SpriteAsset.MAP_TILE)
    return render(request, 'tabletop/partials/_editor_body.html', ctx)


def _render_manage_body(request, table):
    return render(request, 'tabletop/partials/_manage_body.html', {
        'table': table,
        'maps': list(table.map_set.all()),
        'is_owner': True,
        'bg_sprites': _sprite_library(request.user, SpriteAsset.MAP_TILE),
    })


# --- páginas do mestre -----------------------------------------------------

@login_required
def home(request):
    tables = GameTable.objects.filter(Owner=request.user)
    return render(request, 'tabletop/home.html', {'tables': tables})


@login_required
@require_POST
def create_table(request):
    name = request.POST.get('Name', '').strip() or 'Nova Mesa'
    table = GameTable.objects.create(Owner=request.user, Name=name)
    return redirect('tabletop:manage', slug=table.Slug)


def manage(request, slug):
    table = _get_owned(request, slug)
    return render(request, 'tabletop/manage.html', {
        'table': table,
        'maps': list(table.map_set.all()),
        'is_owner': True,
        'bg_sprites': _sprite_library(request.user, SpriteAsset.MAP_TILE),
    })


def _token_library_payload(user):
    """Lista enxuta de assets de token p/ a paleta do editor (id/nome/url)."""
    return [
        {'id': s.id, 'name': s.Name, 'url': s.original_url}
        for s in _sprite_library(user, TOKEN_LIBRARY_CATEGORIES)
    ]


def editor(request, slug, mid):
    table = _get_owned(request, slug)
    m = get_object_or_404(Map, id=mid, Table=table)
    return render(request, 'tabletop/editor.html', {
        'table': table, 'map': m, 'slug': table.Slug,
        'scene': serialize_scene(m, is_owner=True),
        'terrain_palette': _terrain_palette_payload(request.user),
        'token_lib': _token_library_payload(request.user),
        'scene_save_url': reverse('tabletop:scene-save', args=[table.Slug, m.id]),
    })


@require_POST
def scene_save(request, slug, mid):
    """Autosave transacional da cena inteira (só o dono)."""
    table = _get_owned(request, slug)
    m = get_object_or_404(Map, id=mid, Table=table)
    try:
        payload = json.loads(request.POST.get('scene') or request.body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'json'}, status=400)
    id_map = apply_scene_payload(m, payload)
    table.save()  # bumpa UpdatedAt (versão p/ polling)
    return JsonResponse({'ok': True, 'savedAt': table.UpdatedAt.isoformat(), 'idMap': id_map})


# --- visão ao vivo (pública via slug) -------------------------------------

def table_view(request, slug):
    table = get_object_or_404(GameTable, Slug=slug)
    is_owner = _is_owner(request, table)
    scene = serialize_scene(table.ActiveMap, is_owner)
    return render(request, 'tabletop/table_view.html', {
        'table': table, 'map': table.ActiveMap, 'slug': table.Slug, 'is_owner': is_owner,
        'scene': scene if scene is not None else {'empty': True},
    })


def live_fragment(request, slug):
    table = get_object_or_404(GameTable, Slug=slug)
    is_owner = _is_owner(request, table)
    scene = serialize_scene(table.ActiveMap, is_owner)
    return JsonResponse(scene if scene is not None else {'empty': True})


# --- mapas / cenas (somente o dono) ---------------------------------------

@require_POST
def add_map(request, slug):
    table = _get_owned(request, slug)
    m = Map(
        Table=table,
        Name=request.POST.get('Name', '').strip() or 'Novo Mapa',
        GridMode=_clean_grid(request.POST.get('GridMode')),
        Order=table.map_set.count(),
    )
    background = _resolve_sprite(request, 'Background', SpriteAsset.MAP_TILE)
    if background:
        m.Background = background
        if background.Width and background.Height:
            m.WidthPx, m.HeightPx = background.Width, background.Height
    m.save()
    if table.ActiveMap_id is None:  # primeira cena já entra no ar
        table.ActiveMap = m
    table.save()
    return _render_manage_body(request, table)


@require_POST
def edit_map(request, slug, mid):
    table = _get_owned(request, slug)
    m = get_object_or_404(Map, id=mid, Table=table)
    if 'Name' in request.POST:
        m.Name = request.POST['Name'].strip() or m.Name
    if 'GridMode' in request.POST:
        m.GridMode = _clean_grid(request.POST['GridMode'])
    if 'GridSize' in request.POST:
        m.GridSize = _int_or(request.POST['GridSize'], m.GridSize) or m.GridSize
    m.ShowGrid = _bool_post(request, 'ShowGrid')
    background = _resolve_sprite(request, 'Background', SpriteAsset.MAP_TILE)
    if background:
        m.Background = background
        if background.Width and background.Height:
            m.WidthPx, m.HeightPx = background.Width, background.Height
    m.save()
    table.save()
    return _render_manage_body(request, table)


@require_POST
def delete_map(request, slug, mid):
    table = _get_owned(request, slug)
    m = get_object_or_404(Map, id=mid, Table=table)
    m.delete()  # SET_NULL limpa ActiveMap se apontava p/ ele
    table.refresh_from_db()
    table.save()
    return _render_manage_body(request, table)


@require_POST
def set_active(request, slug, mid):
    table = _get_owned(request, slug)
    m = get_object_or_404(Map, id=mid, Table=table)
    table.ActiveMap = m
    table.save()
    return _render_manage_body(request, table)


# --- tokens / props (somente o dono) --------------------------------------

@require_POST
def add_token(request, slug):
    table = _get_owned(request, slug)
    m = get_object_or_404(Map, id=_int_or(request.POST.get('MapId')), Table=table)
    kind = _clean_kind(request.POST.get('Kind'))
    movable = _bool_post(request, 'MovableByPlayers') if 'MovableByPlayers' in request.POST \
        else Token.default_movable_for_kind(kind)
    x = _int_or(request.POST.get('X'))
    y = _int_or(request.POST.get('Y'))
    if x is None or y is None:
        x, y = m.WidthPx // 2, m.HeightPx // 2
    else:
        x, y = snap_to_grid(x, y, m.GridSize, m.GridMode)
    Token.objects.create(
        Map=m,
        Kind=kind,
        Label=request.POST.get('Label', '').strip(),
        SpriteAsset=_resolve_sprite(request, 'Sprite', SpriteAsset.MAP_TOKEN),
        X=x,
        Y=y,
        GridWidth=_int_or(request.POST.get('GridWidth'), 1) or 1,
        GridHeight=_int_or(request.POST.get('GridHeight'), 1) or 1,
        MovableByPlayers=movable,
        Order=m.token_set.count(),
    )
    table.save()
    return _render_editor_body(request, table, m)


@require_POST
def edit_token(request, slug, tid):
    table = _get_owned(request, slug)
    token = get_object_or_404(Token, id=tid, Map__Table=table)
    if 'Label' in request.POST:
        token.Label = request.POST['Label'].strip()
    if 'Kind' in request.POST:
        token.Kind = _clean_kind(request.POST['Kind'])
    if 'GridWidth' in request.POST:
        token.GridWidth = _int_or(request.POST['GridWidth'], token.GridWidth) or token.GridWidth
    if 'GridHeight' in request.POST:
        token.GridHeight = _int_or(request.POST['GridHeight'], token.GridHeight) or token.GridHeight
    if '_token_edit_form' in request.POST:
        token.MovableByPlayers = _bool_post(request, 'MovableByPlayers')
        token.Hidden = _bool_post(request, 'Hidden')
    elif 'MovableByPlayers' in request.POST:
        token.MovableByPlayers = _bool_post(request, 'MovableByPlayers')
    elif 'Hidden' in request.POST:
        token.Hidden = _bool_post(request, 'Hidden')
    if 'Rotation' in request.POST:
        token.Rotation = (_int_or(request.POST['Rotation'], token.Rotation) or 0) % 360
    sprite = _resolve_sprite(request, 'Sprite', SpriteAsset.MAP_TOKEN)
    if sprite:
        token.SpriteAsset = sprite
    token.save()
    table.save()
    return _render_editor_body(request, table, token.Map)


@require_POST
def delete_token(request, slug, tid):
    table = _get_owned(request, slug)
    token = get_object_or_404(Token, id=tid, Map__Table=table)
    m = token.Map
    token.delete()
    table.save()
    return _render_editor_body(request, table, m)


@require_POST
def move_token(request, slug, tid):
    """Mover é trust-based: o dono move qualquer token; o jogador anônimo só move
    tokens `MovableByPlayers` que estejam na cena ativa."""
    table = get_object_or_404(GameTable, Slug=slug)
    token = get_object_or_404(Token, id=tid, Map__Table=table)
    is_owner = _is_owner(request, table)
    if not is_owner and (not token.MovableByPlayers or table.ActiveMap_id != token.Map_id):
        raise PermissionDenied
    x = _int_or(request.POST.get('X'), token.X)
    y = _int_or(request.POST.get('Y'), token.Y)
    token.X, token.Y = snap_to_grid(x, y, token.Map.GridSize, token.Map.GridMode)
    if 'Rotation' in request.POST:
        token.Rotation = (_int_or(request.POST['Rotation'], token.Rotation) or 0) % 360
    token.save()
    table.save()
    if is_owner and getattr(request, 'htmx', False) and request.htmx.target == 'tt-editor':
        return _render_editor_body(request, table, token.Map)
    return _render_canvas(request, table, token.Map, is_owner)


# --- névoa (somente o dono) -----------------------------------------------

@require_POST
def add_fog(request, slug, mid):
    table = _get_owned(request, slug)
    m = get_object_or_404(Map, id=mid, Table=table)
    FogRegion.objects.create(
        Map=m,
        X=_int_or(request.POST.get('X'), 0) or 0,
        Y=_int_or(request.POST.get('Y'), 0) or 0,
        Width=max(0, _int_or(request.POST.get('Width'), 0) or 0),
        Height=max(0, _int_or(request.POST.get('Height'), 0) or 0),
    )
    table.save()
    return _render_canvas(request, table, m, is_owner=True)


@require_POST
def delete_fog(request, slug, fid):
    table = _get_owned(request, slug)
    fog = get_object_or_404(FogRegion, id=fid, Map__Table=table)
    m = fog.Map
    fog.delete()
    table.save()
    return _render_canvas(request, table, m, is_owner=True)


# --- terreno (somente o dono) ---------------------------------------------

@require_POST
def paint_terrain(request, slug, mid):
    table = _get_owned(request, slug)
    m = get_object_or_404(Map, id=mid, Table=table)
    sprite = _resolve_sprite(request, 'Sprite', SpriteAsset.MAP_TILE)
    for q, r in _parse_cells(request.POST.get('cells')):
        TerrainCell.objects.update_or_create(Map=m, Q=q, R=r, defaults={'SpriteAsset': sprite})
    table.save()
    return _render_editor_body(request, table, m)


@require_POST
def clear_terrain(request, slug, mid):
    table = _get_owned(request, slug)
    m = get_object_or_404(Map, id=mid, Table=table)
    cells = _parse_cells(request.POST.get('cells'))
    if cells:
        for q, r in cells:
            TerrainCell.objects.filter(Map=m, Q=q, R=r).delete()
    else:
        TerrainCell.objects.filter(Map=m).delete()
    table.save()
    return _render_editor_body(request, table, m)
