from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import models

from .models import (
    Ability, Character, CharacterArmor, CharacterAttackModifiers,
    CharacterFeat, CharacterLanguages, CharacterMoney, CharacterOtherItem,
    CharacterOtherItemObs, CharacterProtectionItem, CharacterSavingThrows,
    CharacterShield, CharacterSkill, CharacterSkillGraduation,
    CharacterSpell, CharacterSpellSlot, CharacterSpellcasting,
    CharacterStatus, CharacterWeapon,
)
from .forms import CharacterForm, CharacterStatsForm, CharacterCreateForm, CharacterIdentityForm
from .services import _bootstrap_character_siblings
from .constants import DEITY_SUGGESTIONS
from .spellcasting import spellcasting_context


def _to_int(value, default=0):
    if value in (None, ''):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _ability_mod(value):
    return (_to_int(value, 0) - 10) // 2


def _post_int(request, name, default=0):
    return _to_int(request.POST.get(name), default)


def _update_fields_from_post(instance, request, fields, prefix=''):
    changed = False
    for field in fields:
        name = f'{prefix}{field}'
        if name not in request.POST:
            continue
        model_field = instance._meta.get_field(field)
        raw_value = request.POST.get(name)
        if isinstance(model_field, models.IntegerField):
            value = _to_int(raw_value, 0)
        elif isinstance(model_field, models.BooleanField):
            value = raw_value in ('on', 'true', '1', 'yes')
        else:
            value = raw_value
        setattr(instance, field, value)
        changed = True
    if changed:
        instance.save()
    return changed


def _ordered_slots(character, related_name, model, count):
    slots = list(getattr(character, related_name).all().order_by('id')[:count])
    while len(slots) < count:
        slots.append(None)
    return slots


def _save_repeating_slots(character, request, model, prefix, fields, count):
    existing = list(model.objects.filter(Character=character).order_by('id')[:count])
    for index in range(1, count + 1):
        item = existing[index - 1] if index <= len(existing) else None
        slot_prefix = f'{prefix}_{index}_'
        has_any_value = any(request.POST.get(f'{slot_prefix}{field}', '') for field in fields)
        if item is None and not has_any_value:
            continue
        if item is None:
            item = model(Character=character)
        _update_fields_from_post(item, request, fields, slot_prefix)


def _recalculate_stats(character):
    stats = character.characterstats
    for ability in ['Strength', 'Dexterity', 'Constitution', 'Intelligence', 'Wisdom', 'Charisma']:
        setattr(stats, f'{ability}StatMod', _ability_mod(getattr(stats, ability)))
        temp = getattr(stats, f'{ability}Temp')
        setattr(stats, f'{ability}ModTemp', _ability_mod(temp) if temp else 0)
    stats.save()

    status = character.characterstatus
    status.ACDexModifier = stats.DexterityStatMod
    status.ACTotal = (
        10 + _to_int(status.ACArmorBonus) + _to_int(status.ACShieldBonus)
        + _to_int(status.ACDexModifier) + _to_int(status.ACSizeModifier)
        + _to_int(status.ACNaturalArmor) + _to_int(status.ACDeflectionModifier)
        + _to_int(status.ACMiscModifier)
    )
    status.ACTouch = 10 + _to_int(status.ACDexModifier) + _to_int(status.ACSizeModifier) + _to_int(status.ACDeflectionModifier) + _to_int(status.ACMiscModifier)
    status.ACFlatFooterd = 10 + _to_int(status.ACArmorBonus) + _to_int(status.ACShieldBonus) + _to_int(status.ACSizeModifier) + _to_int(status.ACNaturalArmor) + _to_int(status.ACDeflectionModifier) + _to_int(status.ACMiscModifier)
    status.Initiative = stats.DexterityStatMod
    status.save()

    saves = character.charactersavingthrows
    saves.FortitudeAbilityModifier = stats.ConstitutionStatMod
    saves.ReflexAbilityModifier = stats.DexterityStatMod
    saves.WillAbilityModifier = stats.WisdomStatMod
    saves.TotalFortitude = _to_int(saves.FortitudeBaseSave) + _to_int(saves.FortitudeAbilityModifier) + _to_int(saves.FortitudeMagicModifier) + _to_int(saves.FortitudeMiscModifier) + _to_int(saves.FortitudeTemporaryModifier)
    saves.TotalReflex = _to_int(saves.ReflexBaseSave) + _to_int(saves.ReflexAbilityModifier) + _to_int(saves.ReflexMagicModifier) + _to_int(saves.ReflexMiscModifier) + _to_int(saves.ReflexTemporaryModifier)
    saves.TotalWill = _to_int(saves.WillBaseSave) + _to_int(saves.WillAbilityModifier) + _to_int(saves.WillMagicModifier) + _to_int(saves.WillMiscModifier) + _to_int(saves.WillTemporaryModifier)
    saves.save()

    attack = character.characterattackmodifiers
    attack.GrapplerStrModifier = stats.StrengthStatMod
    attack.TotalGrappler = _to_int(attack.GrapplerBBA) + _to_int(attack.GrapplerStrModifier) + _to_int(attack.GrapplerSizeModifier) + _to_int(attack.GrapplerMiscModifier)
    attack.save()


def _sheet_context(char, **extra):
    context = {
        'character': char,
        'characterForm': CharacterForm(instance=char),
        'characterStatsForm': CharacterStatsForm(instance=getattr(char, 'characterstats', None)),
        'characterIdentityForm': CharacterIdentityForm(instance=char),
        'deity_suggestions': DEITY_SUGGESTIONS,
        'spellcasting': spellcasting_context(char),
        'weapon_slots': _ordered_slots(char, 'characterweapon_set', CharacterWeapon, 4),
        'protection_slots': _ordered_slots(char, 'characterprotectionitem_set', CharacterProtectionItem, 3),
        'other_item_slots': _ordered_slots(char, 'characterotheritem_set', CharacterOtherItem, 32),
        'feat_slots': _ordered_slots(char, 'characterfeat_set', CharacterFeat, 24),
        'ability_slots': _ordered_slots(char, 'ability_set', Ability, 12),
        'language_slots': _ordered_slots(char, 'characterlanguages_set', CharacterLanguages, 12),
        'spell_slots_edit': _ordered_slots(char, 'characterspellslot_set', CharacterSpellSlot, 20),
        'known_spell_slots': _ordered_slots(char, 'characterspell_set', CharacterSpell, 24),
    }
    context.update(extra)
    return context


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
            context = _sheet_context(char, characterIdentityForm=form)
            return render(request, 'character/partials/character_identity.html', context)

        if request.htmx.target == 'characterForm':
            characterForm = CharacterForm(request.POST, instance=char)
            if characterForm.is_valid():
                char = characterForm.save()
            context = _sheet_context(char, characterForm=characterForm)
            return render(request, 'character/partials/character_description.html', context)

        if request.htmx.target == 'characterStatsForm':
            stats = getattr(char, 'characterstats', None)
            _update_fields_from_post(stats, request, [
                'Strength', 'Dexterity', 'Constitution', 'Intelligence', 'Wisdom', 'Charisma',
                'StrengthTemp', 'DexterityTemp', 'ConstitutionTemp', 'IntelligenceTemp',
                'WisdomTemp', 'CharismaTemp',
            ])
            _save_repeating_slots(char, request, CharacterWeapon, 'weapon', [
                'Attack', 'AttackBonus', 'Damage', 'Critical', 'Range', 'Type', 'Notes', 'AmmunitionName',
            ], 4)
            _recalculate_stats(char)
            char.refresh_from_db()
            context = _sheet_context(char)
            return render(request, 'character/partials/character_stats.html', context)

        if request.htmx.target == 'characterStatusForm':
            _update_fields_from_post(char.characterstatus, request, ['TotalHitPoints', 'NonLethalDamager', 'Speed'])
            _recalculate_stats(char)
            return render(request, 'character/partials/character_combat.html', _sheet_context(char))

        if request.htmx.target == 'characterArmorForm':
            _update_fields_from_post(char.characterstatus, request, [
                'ACArmorBonus', 'ACShieldBonus', 'ACSizeModifier', 'ACNaturalArmor',
                'ACDeflectionModifier', 'ACMiscModifier', 'DamageReduction',
            ])
            _recalculate_stats(char)
            return render(request, 'character/partials/character_combat.html', _sheet_context(char))

        if request.htmx.target == 'characterSavesForm':
            _update_fields_from_post(char.charactersavingthrows, request, [
                'FortitudeBaseSave', 'FortitudeMagicModifier', 'FortitudeMiscModifier',
                'ReflexBaseSave', 'ReflexMagicModifier', 'ReflexMiscModifier',
                'WillBaseSave', 'WillMagicModifier', 'WillMiscModifier',
            ])
            _recalculate_stats(char)
            return render(request, 'character/partials/character_stats.html', _sheet_context(char))

        if request.htmx.target == 'characterAttackForm':
            _update_fields_from_post(char.characterattackmodifiers, request, [
                'BBA', 'SpellResistence', 'GrapplerBBA', 'GrapplerSizeModifier', 'GrapplerMiscModifier',
            ])
            _recalculate_stats(char)
            return render(request, 'character/partials/character_stats.html', _sheet_context(char))

        if request.htmx.target == 'characterSkillsForm':
            skills = list(CharacterSkill.objects.filter(Character=char).order_by('id'))
            for index, skill in enumerate(skills, start=1):
                prefix = f'skill_{index}_'
                skill.SkillIsActive = f'{prefix}SkillIsActive' in request.POST
                _update_fields_from_post(skill, request, [
                    'SkillName', 'SkillAbility', 'Ranks', 'MiscModifier',
                ], prefix)
                skill.SkillModifier = _to_int(skill.AbilityModifier) + _to_int(skill.Ranks) + _to_int(skill.MiscModifier)
                skill.save()
            return render(request, 'character/partials/character_skills.html', _sheet_context(char))

        if request.htmx.target == 'characterWeaponsForm':
            _save_repeating_slots(char, request, CharacterWeapon, 'weapon', [
                'Attack', 'AttackBonus', 'Damage', 'Critical', 'Range', 'Type', 'Notes', 'AmmunitionName',
            ], 4)
            return render(request, 'character/partials/character_weapon_card.html', _sheet_context(char))

        if request.htmx.target == 'characterEquipmentForm':
            armor, _ = CharacterArmor.objects.get_or_create(Character=char)
            shield, _ = CharacterShield.objects.get_or_create(Character=char)
            _update_fields_from_post(armor, request, [
                'Name', 'Type', 'ACBonus', 'MaxDex', 'CheckPenalty', 'SpellFailure',
                'Speed', 'Weigth', 'SpecialProperties',
            ], 'armor_')
            _update_fields_from_post(shield, request, [
                'Name', 'ACBonus', 'Weigth', 'CheckPenalty', 'SpellFailure', 'SpecialProperties',
            ], 'shield_')
            _save_repeating_slots(char, request, CharacterProtectionItem, 'protection', [
                'Name', 'ACBonus', 'Weigth', 'SpecialProperties',
            ], 3)
            return render(request, 'character/partials/character_armor.html', _sheet_context(char))

        if request.htmx.target == 'characterItemsForm':
            _save_repeating_slots(char, request, CharacterOtherItem, 'item', ['Name', 'Page', 'Weigth'], 32)
            return render(request, 'character/partials/character_items.html', _sheet_context(char))

        if request.htmx.target == 'characterMoneyForm':
            _update_fields_from_post(char.charactermoney, request, ['CP', 'SP', 'GP', 'PP'])
            _update_fields_from_post(char.characterotheritemobs, request, [
                'LightLoad', 'MediumLoad', 'HeavyLoad', 'LiftOverHEad', 'LiftOffGround',
                'PushOrDrag', 'TotalWCarried',
            ])
            return render(request, 'character/partials/character_money.html', _sheet_context(char))

        if request.htmx.target == 'characterFeatsForm':
            _save_repeating_slots(char, request, CharacterFeat, 'feat', ['Name', 'Page'], 24)
            return render(request, 'character/partials/character_feats.html', _sheet_context(char))

        if request.htmx.target == 'characterSpecialsForm':
            _save_repeating_slots(char, request, Ability, 'ability', ['Name', 'Page'], 12)
            _save_repeating_slots(char, request, CharacterLanguages, 'language', ['Value'], 12)
            return render(request, 'character/partials/character_specials.html', _sheet_context(char))

        if request.htmx.target == 'characterSpellsForm':
            _update_fields_from_post(char.characterspellcasting, request, [
                'CasterClass', 'CastingAbility', 'CastingMode', 'Domain1', 'Domain2',
                'SpecializedSchool', 'SpontaneousConversion',
            ], 'spellcasting_')
            _save_repeating_slots(char, request, CharacterSpellSlot, 'slot', [
                'Level', 'SlotType', 'PreparedSpellName', 'ConvertedTo',
            ], 20)
            _save_repeating_slots(char, request, CharacterSpell, 'known_spell', ['Name', 'Page', 'Level'], 24)
            return render(request, 'character/partials/character_spells.html', _sheet_context(char))

    return render(request, 'character/character.html', _sheet_context(char))


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


@login_required
def toggleSpellSlot(request, pk, slot_id):
    char = get_object_or_404(Character, pk=pk, User=request.user)
    slot = get_object_or_404(CharacterSpellSlot, pk=slot_id, Character=char)
    if request.method == 'POST':
        slot.IsUsed = not slot.IsUsed
        slot.save(update_fields=['IsUsed'])
    return render(request, 'character/partials/character_spells.html', _sheet_context(char))
