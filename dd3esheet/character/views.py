from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import models, transaction
from django.db.models import Prefetch

from .models import (
    Ability, Character, CharacterArmor, CharacterAttackModifiers,
    CharacterActiveEffect, CharacterDailyNotes, CharacterDailyResource,
    CharacterCompanion, CharacterContact, CharacterContract, CharacterFaction,
    CharacterFeat, CharacterLanguages, CharacterMoney, CharacterOtherItem,
    CharacterOtherItemObs, CharacterProgress, CharacterProtectionItem, CharacterSavingThrows,
    CharacterShield, CharacterSkill, CharacterSkillGraduation,
    CharacterSpell, CharacterSpellSlot, CharacterSpellcasting,
    CharacterStatus, CharacterWeapon,
)
from .forms import CharacterForm, CharacterStatsForm, CharacterCreateForm, CharacterIdentityForm
from .services import _bootstrap_character_siblings, ensure_expandable_skill_slots
from .constants import DEITY_SUGGESTIONS
from .calculations import (
    ABILITY_FIELDS, ability_modifier, compute_armor_class, compute_grapple_total,
    compute_save_total, compute_skill_row, equipment_armor_class_bonuses,
    load_limits_for_strength, daily_resource_remaining,
    is_trained_only_skill, skill_ability_key, skill_ability_modifier, skill_graduation_limits,
    skill_total, total_carried_weight,
)
from .spellcasting import spellcasting_context


def _annotate_skill_rules(skills):
    for skill in skills:
        skill.IsTrainedOnly = is_trained_only_skill(skill.SkillName)
    return skills


def _to_int(value, default=0):
    if value in (None, ''):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _ability_mod(value):
    return ability_modifier(value)


def _xp_to_next_level(level, current_xp):
    level = _to_int(level, 0)
    if level < 1:
        return None
    next_level_xp = level * (level + 1) * 500
    return max(next_level_xp - _to_int(current_xp, 0), 0)


def _post_int(request, name, default=0):
    return _to_int(request.POST.get(name), default)


def _clamp_int(value, minimum=-999, maximum=999):
    return max(min(value, maximum), minimum)


def _integer_bounds(model_field):
    if model_field.model is CharacterProgress and model_field.name == 'ExperiencePoints':
        return 0, 999999999
    return -999, 999


def _clean_text_value(value, model_field):
    max_length = getattr(model_field, 'max_length', None) or 200
    return (value or '').strip()[:max_length]


def _clean_post_value(raw_value, model_field):
    if isinstance(model_field, models.IntegerField):
        return _clamp_int(_to_int(raw_value, 0), *_integer_bounds(model_field))
    if isinstance(model_field, models.BooleanField):
        return raw_value in ('on', 'true', '1', 'yes')
    return _clean_text_value(raw_value, model_field)


def _update_fields_from_post(instance, request, fields, prefix=''):
    changed = False
    for field in fields:
        name = f'{prefix}{field}'
        if name not in request.POST:
            continue
        model_field = instance._meta.get_field(field)
        value = _clean_post_value(request.POST.get(name), model_field)
        setattr(instance, field, value)
        changed = True
    if changed:
        instance.save()
    return changed


def _ordered_slots(character, related_name, model, count):
    slots = _related_items(character, related_name, model)[:count]
    while len(slots) < count:
        slots.append(None)
    return slots


def _related_items(character, related_name, model):
    prefetched = getattr(character, '_prefetched_objects_cache', {}).get(related_name)
    if prefetched is not None:
        return list(prefetched)
    return list(getattr(character, related_name).all().order_by('id'))


def _sheet_character_queryset():
    return (
        Character.objects
        .select_related(
            'characterstats',
            'characterstatus',
            'charactersavingthrows',
            'characterattackmodifiers',
            'characterskillgraduation',
            'characterotheritemobs',
            'charactermoney',
            'characterprogress',
            'characterspellcasting',
        )
        .prefetch_related(
            Prefetch('characterarmor_set', queryset=CharacterArmor.objects.order_by('id')),
            Prefetch('charactershield_set', queryset=CharacterShield.objects.order_by('id')),
            Prefetch('characterweapon_set', queryset=CharacterWeapon.objects.order_by('id')),
            Prefetch('characterprotectionitem_set', queryset=CharacterProtectionItem.objects.order_by('id')),
            Prefetch('characterotheritem_set', queryset=CharacterOtherItem.objects.order_by('id')),
            Prefetch('characterfeat_set', queryset=CharacterFeat.objects.order_by('id')),
            Prefetch('ability_set', queryset=Ability.objects.order_by('id')),
            Prefetch('characterlanguages_set', queryset=CharacterLanguages.objects.order_by('id')),
            Prefetch('characterspellslot_set', queryset=CharacterSpellSlot.objects.order_by('Level', 'SlotType', 'id')),
            Prefetch('characterspell_set', queryset=CharacterSpell.objects.order_by('Level', 'Name')),
            Prefetch('characterskill_set', queryset=CharacterSkill.objects.order_by('id')),
        )
    )


def _has_full_sheet_prefetch(character):
    prefetched = getattr(character, '_prefetched_objects_cache', {})
    return 'characterskill_set' in prefetched


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


def _checked_indexes_from_post(request, prefix, count):
    return ','.join(str(index) for index in range(1, count + 1) if request.POST.get(f'{prefix}Checks_{index}'))


def _daily_resources_context(char, **extra):
    notes, _ = CharacterDailyNotes.objects.get_or_create(Character=char)
    resource_items = _ordered_slots(char, 'characterdailyresource_set', CharacterDailyResource, 18)
    resource_slots = [
        {
            'item': item,
            'checks': set((item.Checks or '').split(',')) if item else set(),
        }
        for item in resource_items
    ]
    context = {
        'character': char,
        'daily_notes': notes,
        'resource_suggestions': [
            'Furia',
            'Musica de Bardo',
            'Expulsar/Fascinar Mortos-vivos',
            'Forma Selvagem',
            'Imposicao das Maos',
            'Destruir o Mal',
            'Inimigo Predileto',
            'Poder de Dominio',
            'Ataque Furtivo',
            'Inspirar Coragem',
            'Magias por Dia',
            'Cargas de Item',
        ],
        'resource_slots': resource_slots,
        'condition_slots': _ordered_slots(char, 'characteractiveeffect_set', CharacterActiveEffect, 12),
    }
    context.update(extra)
    return context


def _companions_context(char, **extra):
    context = {
        'character': char,
        'companion_slots': _ordered_slots(char, 'charactercompanion_set', CharacterCompanion, 4),
        'companion_types': ['Animal', 'Familiar', 'Montaria', 'Invocacao'],
        'companion_skills': [
            ('Esconder-se', 'DES'),
            ('Ouvir', 'SAB'),
            ('Furtividade', 'DES'),
            ('Procurar', 'INT'),
            ('Observar', 'SAB'),
            ('Equilibrio', 'DES'),
            ('Escalar', 'FOR'),
            ('Arte da Fuga', 'DES'),
            ('Saltar', 'FOR'),
            ('Sobrevivencia', 'SAB'),
            ('Natacao', 'FOR'),
        ],
        'summon_nature_rows': _summon_nature_rows(),
    }
    context.update(extra)
    return context


def _summon_nature_rows():
    return [
        {
            'level': 1,
            'spell': 'Aliado da Natureza I',
            'quantity': '1 criatura de 1o nivel',
            'examples': 'Rato atroz, aguia, macaco, coruja, lobo, vibora pequena',
        },
        {
            'level': 2,
            'spell': 'Aliado da Natureza II',
            'quantity': '1 de 2o, 1d3 de 1o',
            'examples': 'Urso negro, crocodilo, texugo atroz, morcego atroz, elemental pequeno',
        },
        {
            'level': 3,
            'spell': 'Aliado da Natureza III',
            'quantity': '1 de 3o, 1d3 de 2o, 1d4+1 de 1o',
            'examples': 'Gorila, doninha atroz, lobo atroz, leao, thoqqua',
        },
        {
            'level': 4,
            'spell': 'Aliado da Natureza IV',
            'quantity': '1 de 4o, 1d3 de 3o, 1d4+1 menores',
            'examples': 'Urso pardo, aguia gigante, elemental medio, tigre, unicornio',
        },
        {
            'level': 5,
            'spell': 'Aliado da Natureza V',
            'quantity': '1 de 5o, 1d3 de 4o, 1d4+1 menores',
            'examples': 'Urso polar, leao atroz, elemental grande, grifo, rinoceronte',
        },
        {
            'level': 6,
            'spell': 'Aliado da Natureza VI',
            'quantity': '1 de 6o, 1d3 de 5o, 1d4+1 menores',
            'examples': 'Urso atroz, elemental enorme, elefante, girallon, megaraptor',
        },
        {
            'level': 7,
            'spell': 'Aliado da Natureza VII',
            'quantity': '1 de 7o, 1d3 de 6o, 1d4+1 menores',
            'examples': 'Tigre atroz, elemental maior, djinni, triceratopo, tiranossauro',
        },
        {
            'level': 8,
            'spell': 'Aliado da Natureza VIII',
            'quantity': '1 de 8o, 1d3 de 7o, 1d4+1 menores',
            'examples': 'Elemental anciao, roc, salamandra nobre, baleia cachalote',
        },
        {
            'level': 9,
            'spell': 'Aliado da Natureza IX',
            'quantity': '1 de 9o, 1d3 de 8o, 1d4+1 menores',
            'examples': 'Elemental anciao, grifo celestial, unicornios e aliados maiores',
        },
    ]


def _reputation_context(char, **extra):
    context = {
        'character': char,
        'contact_slots': _ordered_slots(char, 'charactercontact_set', CharacterContact, 16),
        'faction_slots': _ordered_slots(char, 'characterfaction_set', CharacterFaction, 10),
        'contract_slots': _ordered_slots(char, 'charactercontract_set', CharacterContract, 12),
    }
    context.update(extra)
    return context


def _save_daily_resources(char, request):
    existing = list(CharacterDailyResource.objects.filter(Character=char).order_by('id')[:18])
    fields = ['Name', 'Source', 'Maximum', 'Used', 'Refresh']
    for index in range(1, 19):
        item = existing[index - 1] if index <= len(existing) else None
        slot_prefix = f'resource_{index}_'
        checks = _checked_indexes_from_post(request, slot_prefix, 10)
        has_any_value = checks or any(request.POST.get(f'{slot_prefix}{field}', '') for field in fields)
        if item is None and not has_any_value:
            continue
        if item is None:
            item = CharacterDailyResource(Character=char)
        _update_fields_from_post(item, request, fields, slot_prefix)
        item.Checks = checks
        item.Remaining = daily_resource_remaining(item.Maximum, item.Used)
        item.save()


def _recalculate_stats(character):
    with transaction.atomic():
        stats = character.characterstats
        for ability in ABILITY_FIELDS:
            setattr(stats, f'{ability}StatMod', _ability_mod(getattr(stats, ability)))
        stats.save(update_fields=[f'{a}StatMod' for a in ABILITY_FIELDS])

        graduation = character.characterskillgraduation
        graduation.MaxGraduation, graduation.OtherClassMaxGraduation = skill_graduation_limits(character.Level)
        graduation.save(update_fields=['MaxGraduation', 'OtherClassMaxGraduation'])

        status = character.characterstatus
        # Fetch each equipment type once; reuse ACBonus and Weigth from same queryset
        armor_rows = list(CharacterArmor.objects.filter(Character=character).order_by('id').values('ACBonus', 'Weigth'))
        shield_rows = list(CharacterShield.objects.filter(Character=character).order_by('id').values('ACBonus', 'Weigth'))
        protection_rows = list(CharacterProtectionItem.objects.filter(Character=character).values('ACBonus', 'Weigth'))
        other_weights = list(CharacterOtherItem.objects.filter(Character=character).values_list('Weigth', flat=True))

        armor_ac = armor_rows[0]['ACBonus'] if armor_rows else None
        shield_ac = shield_rows[0]['ACBonus'] if shield_rows else None
        protection_bonuses = [r['ACBonus'] for r in protection_rows]
        weight_values = (
            [r['Weigth'] for r in armor_rows]
            + [r['Weigth'] for r in shield_rows]
            + [r['Weigth'] for r in protection_rows]
            + list(other_weights)
        )

        if armor_rows or shield_rows or protection_rows:
            status.ACArmorBonus, status.ACShieldBonus, status.ACMiscModifier = equipment_armor_class_bonuses(
                armor_ac, shield_ac, protection_bonuses,
            )
        status.ACDexModifier = stats.DexterityStatMod
        status.ACTotal, status.ACTouch, status.ACFlatFooterd = compute_armor_class(
            armor_bonus=status.ACArmorBonus,
            shield_bonus=status.ACShieldBonus,
            dex_mod=status.ACDexModifier,
            size_mod=status.ACSizeModifier,
            natural_armor=status.ACNaturalArmor,
            deflection=status.ACDeflectionModifier,
            misc=status.ACMiscModifier,
        )
        status.Initiative = stats.DexterityStatMod
        status.save(update_fields=[
            'ACArmorBonus', 'ACShieldBonus', 'ACMiscModifier', 'ACDexModifier',
            'ACTotal', 'ACTouch', 'ACFlatFooterd', 'Initiative',
        ])

        saves = character.charactersavingthrows
        saves.FortitudeAbilityModifier = stats.ConstitutionStatMod
        saves.ReflexAbilityModifier = stats.DexterityStatMod
        saves.WillAbilityModifier = stats.WisdomStatMod
        saves.TotalFortitude = compute_save_total(
            base=saves.FortitudeBaseSave, ability_mod=saves.FortitudeAbilityModifier,
            magic=saves.FortitudeMagicModifier, misc=saves.FortitudeMiscModifier,
            temporary=saves.FortitudeTemporaryModifier,
        )
        saves.TotalReflex = compute_save_total(
            base=saves.ReflexBaseSave, ability_mod=saves.ReflexAbilityModifier,
            magic=saves.ReflexMagicModifier, misc=saves.ReflexMiscModifier,
            temporary=saves.ReflexTemporaryModifier,
        )
        saves.TotalWill = compute_save_total(
            base=saves.WillBaseSave, ability_mod=saves.WillAbilityModifier,
            magic=saves.WillMagicModifier, misc=saves.WillMiscModifier,
            temporary=saves.WillTemporaryModifier,
        )
        saves.save(update_fields=[
            'FortitudeAbilityModifier', 'ReflexAbilityModifier', 'WillAbilityModifier',
            'TotalFortitude', 'TotalReflex', 'TotalWill',
        ])

        attack = character.characterattackmodifiers
        attack.GrapplerStrModifier = stats.StrengthStatMod
        attack.TotalGrappler = compute_grapple_total(
            bba=attack.GrapplerBBA,
            str_mod=attack.GrapplerStrModifier,
            size_mod=attack.GrapplerSizeModifier,
            misc=attack.GrapplerMiscModifier,
        )
        attack.save(update_fields=['GrapplerStrModifier', 'TotalGrappler'])

        skills = list(CharacterSkill.objects.filter(Character=character))
        for skill in skills:
            skill.SkillAbility, skill.AbilityModifier = compute_skill_row(
                skill_name=skill.SkillName, stats=stats,
            )
            skill.SkillModifier = skill_total(
                skill.AbilityModifier,
                skill.Ranks,
                skill.MiscModifier,
                trained_only=is_trained_only_skill(skill.SkillName),
            )
        CharacterSkill.objects.bulk_update(skills, ['SkillAbility', 'AbilityModifier', 'SkillModifier'])

        encumbrance = character.characterotheritemobs
        (
            encumbrance.LightLoad,
            encumbrance.MediumLoad,
            encumbrance.HeavyLoad,
            encumbrance.LiftOverHEad,
            encumbrance.LiftOffGround,
            encumbrance.PushOrDrag,
        ) = load_limits_for_strength(stats.Strength)
        encumbrance.TotalWCarried = total_carried_weight(weight_values)
        encumbrance.save(update_fields=[
            'LightLoad', 'MediumLoad', 'HeavyLoad', 'LiftOverHEad',
            'LiftOffGround', 'PushOrDrag', 'TotalWCarried',
        ])


def _sheet_context(char, **extra):
    ensure_expandable_skill_slots(char)
    try:
        if not _has_full_sheet_prefetch(char):
            char = _sheet_character_queryset().get(pk=char.pk)
        progress = char.characterprogress
    except CharacterProgress.DoesNotExist:
        progress, _ = CharacterProgress.objects.get_or_create(Character=char)
        char = _sheet_character_queryset().get(pk=char.pk)
    context = {
        'character': char,
        'progress': progress,
        'xp_to_next_level': _xp_to_next_level(char.Level, progress.ExperiencePoints),
        'characterForm': CharacterForm(instance=char),
        'characterStatsForm': CharacterStatsForm(instance=getattr(char, 'characterstats', None)),
        'characterIdentityForm': CharacterIdentityForm(instance=char),
        'deity_suggestions': DEITY_SUGGESTIONS,
        'spellcasting': spellcasting_context(char),
        'weapon_slots': _ordered_slots(char, 'characterweapon_set', CharacterWeapon, 4),
        'protection_slots': _ordered_slots(char, 'characterprotectionitem_set', CharacterProtectionItem, 5),
        'other_item_slots': _ordered_slots(char, 'characterotheritem_set', CharacterOtherItem, 32),
        'feat_slots': _ordered_slots(char, 'characterfeat_set', CharacterFeat, 24),
        'ability_slots': _ordered_slots(char, 'ability_set', Ability, 12),
        'language_slots': _ordered_slots(char, 'characterlanguages_set', CharacterLanguages, 12),
        'spell_slots_edit': _ordered_slots(char, 'characterspellslot_set', CharacterSpellSlot, 20),
        'known_spell_slots': _ordered_slots(char, 'characterspell_set', CharacterSpell, 36),
    }
    context['character'].skill_rows = _annotate_skill_rules(
        _related_items(context['character'], 'characterskill_set', CharacterSkill)
    )
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
    if request.method == 'GET':
        char = get_object_or_404(_sheet_character_queryset(), pk=pk, User=request.user)
    else:
        char = get_object_or_404(Character, pk=pk, User=request.user)

    if request.method == 'POST' and request.htmx:

        if request.htmx.target == 'characterIdentityForm':
            form = CharacterIdentityForm(request.POST, instance=char)
            if form.is_valid():
                form.save()
                char.refresh_from_db()
                _recalculate_stats(char)
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
                'StrengthModTemp', 'DexterityModTemp', 'ConstitutionModTemp', 'IntelligenceModTemp',
                'WisdomModTemp', 'CharismaModTemp',
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
                    'SkillName', 'SkillSpecialization', 'Ranks', 'MiscModifier',
                ], prefix)
                skill.save()
            _recalculate_stats(char)
            return render(request, 'character/partials/character_skills.html', _sheet_context(char))

        if request.htmx.target == 'characterWeaponsForm':
            _save_repeating_slots(char, request, CharacterWeapon, 'weapon', [
                'Attack', 'AttackBonus', 'Damage', 'Critical', 'Range', 'Type', 'Notes', 'AmmunitionName',
            ], 4)
            return render(request, 'character/partials/character_weapon_card.html', _sheet_context(char))

        if request.htmx.target == 'characterProgressForm':
            progress, _ = CharacterProgress.objects.get_or_create(Character=char)
            _update_fields_from_post(progress, request, ['ExperiencePoints', 'CampaignName'])
            return render(request, 'character/partials/character_progress.html', _sheet_context(char))

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
            ], 5)
            _recalculate_stats(char)
            return render(request, 'character/partials/character_armor.html', _sheet_context(char))

        if request.htmx.target == 'characterItemsForm':
            _save_repeating_slots(char, request, CharacterOtherItem, 'item', ['Name', 'Page', 'Weigth'], 32)
            _recalculate_stats(char)
            return render(request, 'character/partials/character_items.html', _sheet_context(char))

        if request.htmx.target == 'characterMoneyForm':
            _update_fields_from_post(char.charactermoney, request, ['CP', 'SP', 'GP', 'PP'])
            _update_fields_from_post(char.characterotheritemobs, request, [
                'LightLoad', 'MediumLoad', 'HeavyLoad', 'LiftOverHEad', 'LiftOffGround',
                'PushOrDrag', 'TotalWCarried',
            ])
            _recalculate_stats(char)
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
            _save_repeating_slots(char, request, CharacterSpell, 'known_spell', ['Name', 'Page', 'Level'], 36)
            return render(request, 'character/partials/character_spells.html', _sheet_context(char))

    return render(request, 'character/character.html', _sheet_context(char))


@login_required
def companions(request, pk):
    char = get_object_or_404(Character, pk=pk, User=request.user)
    if request.method == 'POST' and request.htmx:
        _save_repeating_slots(char, request, CharacterCompanion, 'companion', [
            'Type', 'Name', 'Species', 'HitPoints', 'ArmorClass', 'Speed',
            'Skills', 'Feats', 'SpecialAbilities', 'Notes',
        ], 4)
        return render(request, 'character/partials/companions_form.html', _companions_context(char))

    return render(request, 'character/companions.html', _companions_context(char))


@login_required
def dailyResources(request, pk):
    char = get_object_or_404(Character, pk=pk, User=request.user)
    if request.method == 'POST' and request.htmx:
        _save_daily_resources(char, request)
        _save_repeating_slots(char, request, CharacterActiveEffect, 'effect', [
            'Name', 'Source', 'Modifier', 'RoundsRemaining', 'Notes',
        ], 12)
        notes, _ = CharacterDailyNotes.objects.get_or_create(Character=char)
        _update_fields_from_post(notes, request, ['Preparation', 'Spent'])
        return render(request, 'character/daily_resources.html', _daily_resources_context(char))

    return render(request, 'character/daily_resources.html', _daily_resources_context(char))


@login_required
def reputation(request, pk):
    char = get_object_or_404(Character, pk=pk, User=request.user)
    if request.method == 'POST' and request.htmx:
        if request.htmx.target == 'reputationContactsForm':
            _save_repeating_slots(char, request, CharacterContact, 'contact', [
                'Name', 'Location', 'Relationship', 'Favor', 'Notes',
            ], 16)
            return render(request, 'character/partials/reputation_contacts_form.html', _reputation_context(char))

        if request.htmx.target == 'reputationFactionsForm':
            _save_repeating_slots(char, request, CharacterFaction, 'faction', [
                'Name', 'Reputation', 'Influence', 'Risk', 'Notes',
            ], 10)
            return render(request, 'character/partials/reputation_factions_form.html', _reputation_context(char))

        if request.htmx.target == 'reputationContractsForm':
            _save_repeating_slots(char, request, CharacterContract, 'contract', [
                'Title', 'Party', 'Reward', 'Deadline', 'Status', 'Notes',
            ], 12)
            return render(request, 'character/partials/reputation_contracts_form.html', _reputation_context(char))

    return render(request, 'character/reputation.html', _reputation_context(char))


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
