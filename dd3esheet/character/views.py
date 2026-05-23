from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import Character
from .forms import CharacterForm, CharacterStatsForm, CharacterCreateForm, CharacterIdentityForm
from .services import _bootstrap_character_siblings
from .constants import DEITY_SUGGESTIONS


@login_required
def home(request):
    characters = (
        Character.objects
        .filter(User=request.user)
        .select_related('characterstatus', 'charactersavingthrows', 'characterattackmodifiers')
    )
    return render(request, 'character/home.html', {'characters': characters})


@login_required
def character(request, pk):
    char = get_object_or_404(Character, pk=pk, User=request.user)

    if request.method == 'POST' and request.htmx:

        if request.htmx.target == 'characterIdentityForm':
            form = CharacterIdentityForm(request.POST, instance=char)
            if form.is_valid():
                form.save()
                char.refresh_from_db()
            context = {
                'character': char,
                'characterIdentityForm': form,
                'deity_suggestions': DEITY_SUGGESTIONS,
            }
            return render(request, 'character/partials/character_identity.html', context)

        if request.htmx.target == 'characterForm':
            characterForm = CharacterForm(request.POST, instance=char)
            if characterForm.is_valid():
                char = characterForm.save()
            context = {'character': char, 'characterForm': characterForm}
            return render(request, 'character/partials/character_description.html', context)

        if request.htmx.target == 'characterStatsForm':
            stats = getattr(char, 'characterstats', None)
            characterStatsForm = CharacterStatsForm(request.POST, instance=stats)
            if characterStatsForm.is_valid():
                characterStatsForm.save()
                char.refresh_from_db()
            context = {'character': char, 'characterStatsForm': characterStatsForm}
            return render(request, 'character/partials/character_stats.html', context)

    characterForm = CharacterForm(instance=char)
    stats = getattr(char, 'characterstats', None)
    characterStatsForm = CharacterStatsForm(instance=stats)
    characterIdentityForm = CharacterIdentityForm(instance=char)

    context = {
        'character': char,
        'characterForm': characterForm,
        'characterStatsForm': characterStatsForm,
        'characterIdentityForm': characterIdentityForm,
        'deity_suggestions': DEITY_SUGGESTIONS,
    }
    return render(request, 'character/character.html', context)


@login_required
def createCharacter(request):
    if request.method == 'POST':
        form = CharacterCreateForm(request.POST)
        if form.is_valid():
            char = form.save(commit=False)
            char.User = request.user
            char.save()
            _bootstrap_character_siblings(char)
            return redirect('character:character', pk=char.pk)
    else:
        form = CharacterCreateForm()
    return render(request, 'character/character_form.html', {'form': form})


@login_required
def deleteCharacter(request, pk):
    char = get_object_or_404(Character, pk=pk, User=request.user)
    if request.method == 'POST':
        char.delete()
        return redirect('character:home')
    return render(request, 'character/character_delete.html', {'obj': char})
