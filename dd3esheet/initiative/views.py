from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Combatant, Encounter


# --- helpers ---------------------------------------------------------------

def _int_or(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _clean_kind(value):
    valid = {Combatant.PLAYER, Combatant.NPC, Combatant.ENEMY}
    return value if value in valid else Combatant.ENEMY


def _is_owner(request, enc):
    return request.user.is_authenticated and enc.Owner_id == request.user.id


def _get_owned(request, slug):
    """Encontra o encontro pelo slug; 404 se não existe, 403 se quem pede não é o dono."""
    enc = get_object_or_404(Encounter, Slug=slug)
    if not _is_owner(request, enc):
        raise PermissionDenied
    return enc


def _board_context(request, enc, is_owner=None):
    if is_owner is None:
        is_owner = _is_owner(request, enc)
    return {
        'encounter': enc,
        'combatants': list(enc.combatant_set.all()),
        'is_owner': is_owner,
    }


def _render_board(request, enc):
    """Devolve o partial da board já atualizado (resposta das ações do mestre)."""
    return render(request, 'initiative/partials/_board_fragment.html',
                  _board_context(request, enc, is_owner=True))


# --- páginas do mestre -----------------------------------------------------

@login_required
def home(request):
    encounters = Encounter.objects.filter(Owner=request.user)
    return render(request, 'initiative/home.html', {'encounters': encounters})


@login_required
@require_POST
def create_encounter(request):
    name = request.POST.get('Name', '').strip() or 'Novo Encontro'
    enc = Encounter.objects.create(Owner=request.user, Name=name)
    return redirect('initiative:board', slug=enc.Slug)


# --- board (pública via slug) ---------------------------------------------

def board(request, slug):
    enc = get_object_or_404(Encounter, Slug=slug)
    return render(request, 'initiative/board.html', _board_context(request, enc))


def board_fragment(request, slug):
    enc = get_object_or_404(Encounter, Slug=slug)
    return render(request, 'initiative/partials/_board_fragment.html',
                  _board_context(request, enc))


# --- ações de edição (somente o dono) -------------------------------------

@require_POST
def add_combatant(request, slug):
    enc = _get_owned(request, slug)
    Combatant.objects.create(
        Encounter=enc,
        Name=request.POST.get('Name', '').strip() or 'Sem nome',
        Kind=_clean_kind(request.POST.get('Kind')),
        Initiative=_int_or(request.POST.get('Initiative'), 0),
        ArmorClass=_int_or(request.POST.get('ArmorClass'), None),
    )
    enc.save()  # atualiza UpdatedAt (versão do polling)
    return _render_board(request, enc)


@require_POST
def edit_combatant(request, slug, cid):
    enc = _get_owned(request, slug)
    c = get_object_or_404(Combatant, id=cid, Encounter=enc)
    if 'Name' in request.POST:
        c.Name = request.POST['Name'].strip() or c.Name
    if 'Kind' in request.POST:
        c.Kind = _clean_kind(request.POST['Kind'])
    if 'Initiative' in request.POST:
        c.Initiative = _int_or(request.POST['Initiative'], c.Initiative)
    if 'ArmorClass' in request.POST:
        c.ArmorClass = _int_or(request.POST['ArmorClass'], None)
    if 'Effects' in request.POST:
        c.Effects = request.POST['Effects']
    if 'Notes' in request.POST:
        c.Notes = request.POST['Notes']
    c.save()
    enc.save()
    return _render_board(request, enc)


@require_POST
def apply_damage(request, slug, cid):
    enc = _get_owned(request, slug)
    c = get_object_or_404(Combatant, id=cid, Encounter=enc)
    delta = _int_or(request.POST.get('delta'), 0)
    c.DamageTaken = max(0, c.DamageTaken + delta)  # clamp: nunca negativo
    c.save()
    enc.save()
    return _render_board(request, enc)


@require_POST
def delete_combatant(request, slug, cid):
    enc = _get_owned(request, slug)
    c = get_object_or_404(Combatant, id=cid, Encounter=enc)
    c.delete()  # on_delete=SET_NULL limpa ActiveCombatant se apontava p/ ele
    enc.refresh_from_db()  # recarrega o ponteiro já anulado antes de salvar
    enc.save()
    return _render_board(request, enc)


@require_POST
def next_turn(request, slug):
    enc = _get_owned(request, slug)
    combatants = list(enc.combatant_set.all())
    if combatants:
        if enc.ActiveCombatant_id is None:
            enc.ActiveCombatant = combatants[0]
        else:
            ids = [c.id for c in combatants]
            try:
                idx = ids.index(enc.ActiveCombatant_id)
            except ValueError:
                idx = -1
            if idx >= len(combatants) - 1:
                enc.ActiveCombatant = combatants[0]
                enc.Round += 1  # deu a volta → novo round
            else:
                enc.ActiveCombatant = combatants[idx + 1]
        enc.save()
    return _render_board(request, enc)


@require_POST
def reset_turn(request, slug):
    enc = _get_owned(request, slug)
    enc.ActiveCombatant = None
    enc.Round = 1
    enc.save()
    return _render_board(request, enc)
