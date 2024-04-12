from django.shortcuts import render, redirect
from .models import Character, CharacterStats, CharacterStatus,CharacterSavingThrows, CharacterAttackModifiers, CharacterSkillGraduation, CharacterSkill, CharacterWeapon
from .models import CharacterArmor, CharacterShield, CharacterProtectionItem, CharacterOtherItem
from .models import CharacterOtherItemObs, CharacterMoney, CharacterFeat, Ability
from .models import CharacterSpell, CharacterSpellSave, CharacterArcaneSpellFailCheck
from .models import CharacterMagicConditionalModifiers,CharacterMagicDayUse, CharacterLanguages
from .forms import CharacterForm, CharacterStatsForm

def home(request):
    characters = Character.objects.all()
    return render(request, 'base/home.html', {'characters': characters})

def character(request, pk):
    character = Character.objects.get(id=pk)
    characterStats = CharacterStats.objects.get(Character=character.id)
    characterWeapons = CharacterWeapon.objects.filter(Character=character.id)

    context = {
            'character': character,
            'characterStats': characterStats,
            'characterWeapons': characterWeapons,
            }
    return render(request, "base/character.html", context)

def createCharacterWithDefaults(request):

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
    
    return render(request, 'base/character_form2.html', context)

def createCharacter(request):
    if request.method == 'POST':
        characterForm = CharacterForm(request.POST)
        characterStatsForm = CharacterStatsForm(request.POST)

        if characterForm.is_valid() and characterStatsForm.is_valid():
            character = characterForm.save()
            characterStats = characterStatsForm.save(commit=False)
            characterStats.Character = character
            characterStatsForm.save()
            return redirect('home')
    
    characterForm = CharacterForm()
    characterStatsForm = CharacterStatsForm()

    context = { 'characterForm': characterForm,
                'characterStatsForm': characterStatsForm
            }
    
    return render(request, 'base/character_form.html', context)

def updateCharacter(request, pk):
    character = Character.objects.get(id=pk)

    characterStats = CharacterStats.objects.filter(Character=character.id)
    form = CharacterForm(instance=character)

    context = {'form': form}

    if request.method == 'POST':
        form = CharacterForm(request.POST, instance=character)

        if form.is_valid():
            form.save()
            return redirect('home')

    return render(request, 'base/character_form.html', context)

def deleteCharacter(request, pk):
    character = Character.objects.get(id=pk)
    if request.method == 'POST':
        character.delete()
        return redirect('home')
    
    return render(request, 'base/character_delete.html', {'obj': character})