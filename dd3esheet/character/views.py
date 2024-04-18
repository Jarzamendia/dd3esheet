from django.shortcuts import render, redirect
from .models import *
from .forms import *

def home(request):
    characters = Character.objects.all()
    return render(request, 'character/home.html', {'characters': characters})

# Character CRUD
def character(request, pk):

    character = Character.objects.get(id=pk)

    if request.method == 'POST':

        if request.htmx:

            if request.htmx.target == 'characterForm':
                characterForm = CharacterForm(request.POST, instance=character)
                if characterForm.is_valid():
                    print("valid")
                    character = characterForm.save()

                    context = {
                        "character": character,
                        "characterForm": characterForm
                    }

                    return render(request, "character/partials/character_description.html", context)

            if request.htmx.target == 'characterStatsForm':
                characterStatsForm = CharacterStatsForm(request.POST, instance=character)
                if characterStatsForm.is_valid():
                    character = characterStatsForm.save()

                    context = {
                        "character": character,
                        "characterStatsForm": characterStatsForm,
                    }

                    return render(request, "character/partials/character_stats.html", context)

    characterForm = CharacterForm(instance=character)
    characterStatsForm = CharacterStatsForm(instance=character)

    context = {
        "character": character,
        "characterForm": characterForm,
        "characterStatsForm": characterStatsForm,
    }
    return render(request, "character/character.html", context)

def createCharacter(request):

    skillList = ['Appraise', 'Balance', 'Bluff', 'Climb', 'Concentration', 'Craft', 'DecipherScript', 'Diplomacy', 'DisableDevice', 'Disguise', 'EscapeArtist', 'Forgery', 'GatherInformation', 'HandleAnimal', 'Heal', 'Hide', 'Intimidate', 'Jump' , 'Knowledge', 'Listen', 'MoveSilently', 'OpenLock', 'Perform', 'Profession', 'Ride', 'Search', 'SenseMotive', 'SleightofHand', 'Spellcraft', 'Spot', 'Survival', 'Swim', 'Tumble', 'UseMagicDevice', 'UseRope']

    if request.method == 'POST':

        characterForm = CharacterForm(request.POST)

        if characterForm.is_valid():
            character = characterForm.save()
            CharacterStats(Character = character).save()
            CharacterStatus(Character = character).save()
            CharacterSavingThrows(Character = character).save()
            CharacterAttackModifiers(Character = character).save()
            CharacterSkillGraduation(Character = character).save()
            CharacterOtherItemObs(Character = character).save()
            CharacterMoney(Character = character).save()
            CharacterSpellSave(Character = character).save()
            CharacterArcaneSpellFailCheck(Character = character).save()
            CharacterMagicConditionalModifiers(Character = character).save()

            for skill in skillList:
                CharacterSkill(Character = character, SkillName = skill).save()

            return redirect('home')
    
    characterForm = CharacterForm()

    context = { 'characterForm': characterForm}
    
    return render(request, 'character/character_form.html', context)

def deleteCharacter(request, pk):
    character = Character.objects.get(id=pk)
    if request.method == 'POST':
        character.delete()
        return redirect('home')
    
    return render(request, 'character/character_delete.html', {'obj': character})