from django.shortcuts import render, redirect
from .models import Character, CharacterDescription, CharacterStats, CharacterStatus, CharacterSavingThrows
from .models import  CharacterAttackModifiers, CharacterWeapon, CharacterSkillGraduation, CharacterSkill
from .models import  CharacterArmor, CharacterShield, CharacterProtectionItem, CharacterOtherItem, CharacterOtherItemObs
from .models import  CharacterMoney, CharacterFeat, CharacterAbility, CharacterSpell, CharacterSpellSave
from .models import  CharacterArcaneSpellFailCheck, CharacterMagicConditionalModifiers, CharacterMagicDayUse, CharacterLanguages
from .forms import CharacterForm

skillList = ['Appraise', 'Balance', 'Bluff', 'Climb', 'Concentration', 'Craft', 'DecipherScript', 'Diplomacy', 'DisableDevice', 'Disguise', 'EscapeArtist', 'Forgery', 'GatherInformation', 'HandleAnimal', 'Heal', 'Hide', 'Intimidate', 'Jump' , 'Knowledge', 'Listen', 'MoveSilently', 'OpenLock', 'Perform', 'Profession', 'Ride', 'Search', 'SenseMotive', 'SleightofHand', 'Spellcraft', 'Spot', 'Survival', 'Swim', 'Tumble', 'UseMagicDevice', 'UseRope']

def home(request):
    characters = Character.objects.all()
    return render(request, 'base/home.html', {'characters': characters})

def character(request, pk):
    character = Character.objects.get(id=pk)
    characterDesc = CharacterDescription.objects.get(Character=character.id)
    characterStats = CharacterStats.objects.get(Character=character.id)
    characterStatus = CharacterStatus.objects.get(Character=character.id)
    context = {
            'character': character,
            'characterDescription': characterDesc,
            'characterStats': characterStats,
            'characterStatus': characterStatus,
            }
    return render(request, "base/character.html", context)

def createCharacter(request):
    if request.method == 'POST':
        form = CharacterForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('home')

    form = CharacterForm()

    context = { 'form': form}
    
    return render(request, 'base/character_form.html', context)

def updateCharacter(request, pk):
    character = Character.objects.get(id=pk)
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