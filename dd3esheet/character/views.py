import logging
import re

from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db import models, transaction
from django.db.models import Prefetch
from django.http import HttpResponse

from .models import (
    Ability, Character, CharacterArmor, CharacterAttackModifiers,
    CharacterActiveEffect, CharacterBuff, CharacterDailyNotes, CharacterDailyResource,
    CharacterCompanion, CharacterContact, CharacterContract, CharacterFaction,
    CharacterFeat, CharacterLanguages, CharacterMoney, CharacterOtherItem,
    CharacterOtherItemObs, CharacterProgress, CharacterProtectionItem, CharacterSavingThrows,
    CharacterShield, CharacterSkill, CharacterSkillGraduation, CharacterMagicDayUse,
    CharacterSummon,
    CharacterSpell, CharacterSpellSlot, CharacterSpellcasting,
    CharacterStatus, CharacterWeapon,
)
from .forms import CharacterForm, CharacterStatsForm, CharacterCreateForm, CharacterIdentityForm
from .services import _bootstrap_character_siblings, ensure_expandable_skill_slots
from .constants import DEITY_SUGGESTIONS, BUFF_PRESETS, BUFF_EFFECT_FIELDS
from .calculations import (
    ABILITY_FIELDS, SKILL_ABILITY_BY_NAME, ability_modifier, armor_check_penalty_for_skill, cap_dex_to_armor,
    compute_armor_class, compute_attack_bonus, compute_grapple_total,
    compute_save_total, compute_spell_save_dc, equipment_armor_class_bonuses,
    bonus_spells_for_ability,
    load_limits_for_strength, daily_resource_remaining,
    parse_bonus,
    is_trained_only_skill, skill_ability_key, skill_graduation_limits,
    signed_bonus, skill_total, total_carried_weight,
)
from .spellcasting import caster_config_for_class, numeric_slot_count, spellcasting_context
from sdr.models import SDR_Monster
from sdr.lookups import resolve_spell
from sdr.models import SDR_Spell
from sprites.models import SpriteVariant
from sprites.services import sprite_for_class, sprite_image_data

logger = logging.getLogger(__name__)

_SPELLBOOK_SLOT_TOTAL = 20

_SPELLBOOK_PROFILE_FIELDS = [
    'CastingMode',
    'Domain1',
    'Domain2',
    'SpecializedSchool',
    'SpontaneousConversion',
]


def _annotate_skill_rules(skills, stats=None, buff_ability=None):
    buff_ability = buff_ability or {}
    for skill in skills:
        skill.IsTrainedOnly = is_trained_only_skill(skill.SkillName)
        if stats is not None:
            ability = SKILL_ABILITY_BY_NAME.get(skill.SkillName or '')
            skill.AbilityModifier = (
                _effective_ability_mod(stats, ability, buff_ability.get(ability, 0))
                if ability else None
            )
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


def _effective_ability_mod(stats, ability, buff_score_bonus=0):
    """Mod efetivo (temp-aware): mod(VALOR + VALOR TEMPORARIO + buffs) + MOD TEMPORARIO.
    VALOR TEMPORARIO e MOD TEMPORARIO sao ajustes que somam (em branco = 0);
    buff_score_bonus = soma dos buffs ativos que afetam esse atributo.
    Retorna None quando nada foi preenchido (mostra '-', nao -5)."""
    base = _to_int(getattr(stats, ability, 0), 0)
    temp_score = _to_int(getattr(stats, f'{ability}Temp', 0), 0)
    temp_mod = _to_int(getattr(stats, f'{ability}ModTemp', 0), 0)
    effective_score = base + temp_score + _to_int(buff_score_bonus, 0)
    if effective_score <= 0 and temp_mod == 0:
        return None
    base_mod = ability_modifier(effective_score) if effective_score > 0 else 0
    return base_mod + temp_mod


def _active_buff_totals(character):
    """Soma os efeitos dos buffs ATIVOS. Retorna (ability_bonus_dict, flat_dict)."""
    ability_bonus = {a: 0 for a in ABILITY_FIELDS}
    flat = {'AttackBonus': 0, 'ACBonus': 0, 'SaveBonus': 0}
    for buff in _related_items(character, 'characterbuff_set', CharacterBuff):
        if not buff.IsActive:
            continue
        for ability in ABILITY_FIELDS:
            ability_bonus[ability] += _to_int(getattr(buff, f'{ability}Bonus'), 0)
        for key in flat:
            flat[key] += _to_int(getattr(buff, key), 0)
    return ability_bonus, flat


def _lowest_max_dex(armor_rows):
    values = [parse_bonus(row.get('MaxDex')) for row in armor_rows if row.get('MaxDex') not in (None, '')]
    if not values:
        return None
    return min(values)


def _armor_check_penalty_total(armor_rows, shield_rows):
    return sum(parse_bonus(row.get('CheckPenalty')) for row in [*armor_rows, *shield_rows])


def _weapon_uses_ranged_bonus(weapon):
    range_text = (weapon.Range or '').strip()
    if range_text and range_text not in ('-', '—'):
        return True

    notes = (weapon.Notes or '').lower()
    weapon_type = (weapon.Type or '').lower()
    if 'corpo a corpo' in notes:
        return False
    return 'dist' in notes or 'dist' in weapon_type


def _sync_spellcasting_rows(character, stats):
    if character.Class not in ('Wizard', 'Sorcerer', 'Cleric', 'Druid'):
        CharacterMagicDayUse.objects.filter(Character=character).delete()
        return

    config = caster_config_for_class(character.Class)
    ability_score = getattr(stats, config['ability'], 0) or 0
    ability_mod = ability_modifier(ability_score)
    existing = {
        row.Level: row
        for row in CharacterMagicDayUse.objects.filter(Character=character, Level__gte=0, Level__lte=9)
    }
    to_create = []
    to_update = []

    for level in range(10):
        row = existing.get(level)
        if row is None:
            row = CharacterMagicDayUse(Character=character, Level=level)
            to_create.append(row)
        else:
            to_update.append(row)
        row.SpellSaveDC = compute_spell_save_dc(level, ability_mod)
        row.BonusSpells = bonus_spells_for_ability(ability_score, level)

    if to_create:
        CharacterMagicDayUse.objects.bulk_create(to_create)
    if to_update:
        CharacterMagicDayUse.objects.bulk_update(to_update, ['SpellSaveDC', 'BonusSpells'])


def _summon_slot_count(character):
    active_count = CharacterSummon.objects.filter(Character=character).count()
    return max(active_count + 1, 3)


def _monster_hit_points(monster):
    match = re.search(r'\((\d+)\s*hp\)', monster.hit_dice or '', re.IGNORECASE)
    return _to_int(match.group(1), 0) if match else 0


def _monster_armor_class(monster):
    match = re.search(r'\d+', monster.armor_class or '')
    return _to_int(match.group(0), 0) if match else 0


def _monster_attack_bonus(monster):
    match = re.search(r'([+-]\d+)', monster.attack or '')
    return match.group(1) if match else ''


def _monster_damage(monster):
    match = re.search(r'\(([^)]+)\)', monster.attack or '')
    return match.group(1) if match else ''


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


def _is_autosave(request):
    return request.headers.get('HX-Autosave') == '1'


def _autosave_204():
    return HttpResponse(status=204)


def _update_fields_from_post(instance, request, fields, prefix=''):
    changed = False
    changes = []
    for field in fields:
        name = f'{prefix}{field}'
        if name not in request.POST:
            continue
        model_field = instance._meta.get_field(field)
        value = _clean_post_value(request.POST.get(name), model_field)
        old = getattr(instance, field, None)
        if old != value:
            changes.append(f'{field}: {old!r}->{value!r}')
        setattr(instance, field, value)
        changed = True
    if changed:
        instance.save()
    if changes:
        logger.debug('persist %s(%s) %s', type(instance).__name__, prefix or '-', '; '.join(changes))
    return changed


def _clamp_status_hit_points(status):
    # PV atual e temporario PODEM exceder o maximo (cura excedente, PV temporario,
    # buffs). So aplicamos piso 0 — sem teto pelo TotalHitPoints.
    current = max(_to_int(status.CurrentHitPoints, 0), 0)
    temporary = max(_to_int(status.TemporaryHitPoints, 0), 0)
    nonlethal = max(_to_int(status.NonLethalDamager, 0), 0)

    changed_fields = []
    if status.CurrentHitPoints != current:
        status.CurrentHitPoints = current
        changed_fields.append('CurrentHitPoints')
    if status.TemporaryHitPoints != temporary:
        status.TemporaryHitPoints = temporary
        changed_fields.append('TemporaryHitPoints')
    if status.NonLethalDamager != nonlethal:
        status.NonLethalDamager = nonlethal
        changed_fields.append('NonLethalDamager')
    if changed_fields:
        status.save(update_fields=changed_fields)


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
            'User',
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
            Prefetch('characterbuff_set', queryset=CharacterBuff.objects.order_by('id')),
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


def _save_typed_companion_slots(character, request, type_value, prefix, fields, count):
    existing = list(
        CharacterCompanion.objects
        .filter(Character=character, Type__iexact=type_value)
        .order_by('id')[:count]
    )
    for index in range(1, count + 1):
        item = existing[index - 1] if index <= len(existing) else None
        slot_prefix = f'{prefix}_{index}_'
        has_any_value = any(request.POST.get(f'{slot_prefix}{field}', '') for field in fields)
        if item is None and not has_any_value:
            continue
        if item is None:
            item = CharacterCompanion(Character=character, Type=type_value)
        _update_fields_from_post(item, request, fields, slot_prefix)
        if item.Type != type_value:
            item.Type = type_value
            item.save(update_fields=['Type'])


def _save_spellbook_level(character, request, level):
    prefix = f'spellbook_{level}'
    existing = list(
        CharacterSpell.objects.filter(Character=character, Level=level).order_by('id')
    )
    row_count = 0
    for key in request.POST.keys():
        if key.startswith(f'{prefix}_') and key.endswith('_Name'):
            try:
                row_count = max(row_count, int(key.split('_')[2]))
            except (IndexError, ValueError):
                continue
        elif key.startswith(f'{prefix}_') and key.endswith('_Page'):
            try:
                row_count = max(row_count, int(key.split('_')[2]))
            except (IndexError, ValueError):
                continue

    name_field = CharacterSpell._meta.get_field('Name')
    page_field = CharacterSpell._meta.get_field('Page')
    processed = 0
    for index in range(1, max(row_count, len(existing)) + 1):
        item = existing[index - 1] if index <= len(existing) else None
        name = _clean_text_value(request.POST.get(f'{prefix}_{index}_Name'), name_field)
        page = _clean_text_value(request.POST.get(f'{prefix}_{index}_Page'), page_field)
        if not name and not page:
            if item is not None:
                item.delete()
            continue
        if item is None:
            item = CharacterSpell(Character=character)
        item.Level = level
        item.Name = name
        item.Page = page
        matched = resolve_spell(name)
        item.SDRSpellId = matched.id if matched else None
        item.save()
        processed += 1
    return processed


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


def _spellbook_level_rows(character, level):
    spells = [
        spell for spell in _related_items(character, 'characterspell_set', CharacterSpell)
        if spell.Level == level
    ]
    return spells + [None]


def _build_sdr_lookup_for_spells(spells):
    ids = {s.SDRSpellId for s in spells if s and s.SDRSpellId}
    if not ids:
        return {}
    return {
        sdr.id: sdr
        for sdr in SDR_Spell.objects.using('sdr').filter(id__in=ids)
    }


def _sdr_spell_suggestions():
    return list(
        SDR_Spell.objects.using('sdr').only('id', 'name', 'school', 'level').order_by('name')
    )


def _spellbook_level_context(char, level, spellcasting=None):
    spellcasting = spellcasting or spellcasting_context(char)
    spells = _spellbook_level_rows(char, level)
    sdr_lookup = _build_sdr_lookup_for_spells(spells)
    return {
        'character': char,
        'spellcasting': spellcasting,
        'spellbook_profile_fields': _SPELLBOOK_PROFILE_FIELDS,
        'spellbook_level': {
            'level': level,
            'target': f'spellbookLevel{level}Form',
            'form_id': f'spellbookLevel{level}Form',
            'spells': spells,
            'count': len([spell for spell in spellcasting['known_spells'] if spell.Level == level]),
            'sdr_lookup': sdr_lookup,
        },
        'sdr_spell_suggestions': _sdr_spell_suggestions(),
    }


def _spellbook_slot_levels(char, spellcasting):
    db_slots = list(char.characterspellslot_set.all().order_by('id'))
    by_level = {}
    for slot in db_slots:
        by_level.setdefault(slot.Level or 0, []).append(slot)

    profile = spellcasting.get('profile')
    casting_mode = getattr(profile, 'CastingMode', None) or (
        spellcasting['config']['mode'] if spellcasting.get('config') else ''
    )
    is_spontaneous = casting_mode == 'spontaneous_known'
    has_conversion = bool(
        getattr(profile, 'SpontaneousConversion', '')
        or (spellcasting.get('config') or {}).get('conversion')
    )

    level_blocks = []
    next_index = 1
    for row in spellcasting['levels']:
        capacity = numeric_slot_count(row.spells_per_day)
        if row.level > 0:
            capacity += bonus_for_level(row.bonus_spells)
        existing = by_level.get(row.level, [])
        display_count = max(capacity, len(existing))
        if display_count == 0:
            continue
        if next_index > _SPELLBOOK_SLOT_TOTAL:
            break
        rows = []
        for offset in range(display_count):
            if next_index > _SPELLBOOK_SLOT_TOTAL:
                break
            slot = existing[offset] if offset < len(existing) else None
            rows.append({'slot': slot, 'index': next_index, 'level': row.level})
            next_index += 1
        used = sum(1 for slot in existing if slot and slot.IsUsed)
        remaining = max(capacity - used, 0) if capacity else max(len(existing) - used, 0)
        level_blocks.append({
            'level': row.level,
            'capacity': capacity,
            'used': used,
            'remaining': remaining,
            'rows': rows,
            'is_spontaneous': is_spontaneous,
            'has_conversion': has_conversion,
        })
    return level_blocks


def bonus_for_level(value):
    if value in (None, '', '-'):
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _spellbook_context(char, **extra):
    spellcasting = spellcasting_context(char)
    context = {
        'character': char,
        'spellcasting': spellcasting,
        'spell_slots_edit': _ordered_slots(char, 'characterspellslot_set', CharacterSpellSlot, 20),
        'spellbook_slot_levels': _spellbook_slot_levels(char, spellcasting),
        'spellbook_profile_fields': _SPELLBOOK_PROFILE_FIELDS,
        'spellbook_levels': [_spellbook_level_context(char, level, spellcasting)['spellbook_level'] for level in range(10)],
        'sdr_spell_suggestions': _sdr_spell_suggestions(),
    }
    context.update(extra)
    return context


def _companions_context(char, **extra):
    companions_qs = char.charactercompanion_set.all()
    animals = list(companions_qs.filter(Type__iexact='animal').order_by('id')[:4])
    while len(animals) < 4:
        animals.append(None)
    familiars = list(companions_qs.filter(Type__iexact='familiar').order_by('id')[:4])
    while len(familiars) < 4:
        familiars.append(None)
    summon_slots = _ordered_slots(char, 'charactersummon_set', CharacterSummon, _summon_slot_count(char))
    context = {
        'character': char,
        'animal_companions': animals,
        'familiars': familiars,
        'animal_companion': animals[0],
        'familiar': familiars[0],
        'summon_slots': summon_slots,
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
    raw = [
        {'level': 1, 'spell': 'Aliado da Natureza I',    'quantity': '1 criatura de 1o nivel',           'examples': 'Rato atroz, aguia, macaco, coruja, lobo, vibora pequena'},
        {'level': 2, 'spell': 'Aliado da Natureza II',   'quantity': '1 de 2o, 1d3 de 1o',               'examples': 'Urso negro, crocodilo, texugo atroz, morcego atroz, elemental pequeno'},
        {'level': 3, 'spell': 'Aliado da Natureza III',  'quantity': '1 de 3o, 1d3 de 2o, 1d4+1 de 1o', 'examples': 'Gorila, doninha atroz, lobo atroz, leao, thoqqua'},
        {'level': 4, 'spell': 'Aliado da Natureza IV',   'quantity': '1 de 4o, 1d3 de 3o, 1d4+1 menores','examples': 'Urso pardo, aguia gigante, elemental medio, tigre, unicornio'},
        {'level': 5, 'spell': 'Aliado da Natureza V',    'quantity': '1 de 5o, 1d3 de 4o, 1d4+1 menores','examples': 'Urso polar, leao atroz, elemental grande, grifo, rinoceronte'},
        {'level': 6, 'spell': 'Aliado da Natureza VI',   'quantity': '1 de 6o, 1d3 de 5o, 1d4+1 menores','examples': 'Urso atroz, elemental enorme, elefante, girallon, megaraptor'},
        {'level': 7, 'spell': 'Aliado da Natureza VII',  'quantity': '1 de 7o, 1d3 de 6o, 1d4+1 menores','examples': 'Tigre atroz, elemental maior, djinni, triceratopo, tiranossauro'},
        {'level': 8, 'spell': 'Aliado da Natureza VIII', 'quantity': '1 de 8o, 1d3 de 7o, 1d4+1 menores','examples': 'Elemental anciao, roc, salamandra nobre, baleia cachalote'},
        {'level': 9, 'spell': 'Aliado da Natureza IX',   'quantity': '1 de 9o, 1d3 de 8o, 1d4+1 menores','examples': 'Elemental anciao, grifo celestial, unicornios e aliados maiores'},
    ]
    for row in raw:
        sdr = resolve_spell(row['spell'])
        row['sdr_id'] = sdr.id if sdr else None
        row['sdr'] = sdr
    return raw


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
    logger.debug('recalc start char=%s level=%s', character.pk, character.Level)
    buff_ability, buff_flat = _active_buff_totals(character)
    with transaction.atomic():
        stats = character.characterstats
        # MOD. DE HABILIDADE = mod(VALOR + VALOR TEMPORARIO + buffs) + MOD TEMPORARIO.
        # VALOR TEMPORARIO e MOD TEMPORARIO sao ajustes que SOMAM (em branco = 0);
        # ambos sao inputs do usuario e nao sao sobrescritos. So StatMod e derivado.
        # Buffs ativos (Forca do Touro, etc.) somam ao score efetivo.
        for ability in ABILITY_FIELDS:
            base_score = _to_int(getattr(stats, ability), 0)
            temp_score = _to_int(getattr(stats, f'{ability}Temp'), 0)
            temp_mod = _to_int(getattr(stats, f'{ability}ModTemp'), 0)
            buff_bonus = buff_ability.get(ability, 0)
            mod = _effective_ability_mod(stats, ability, buff_bonus)
            setattr(stats, f'{ability}StatMod', mod)
            logger.debug(
                'recalc char=%s %s base=%s +valorTemp=%s +modTemp=%s +buff=%s -> mod=%s',
                character.pk, ability, base_score, temp_score, temp_mod, buff_bonus,
                '-' if mod is None else f'{mod:+d}',
            )
        stats.save(update_fields=[f'{a}StatMod' for a in ABILITY_FIELDS])

        graduation = character.characterskillgraduation
        graduation.MaxGraduation, graduation.OtherClassMaxGraduation = skill_graduation_limits(character.Level)
        graduation.save(update_fields=['MaxGraduation', 'OtherClassMaxGraduation'])

        status = character.characterstatus
        _clamp_status_hit_points(status)
        # Fetch each equipment type once; reuse ACBonus and Weigth from same queryset
        armor_rows = list(
            CharacterArmor.objects
            .filter(Character=character)
            .order_by('id')
            .values('ACBonus', 'Weigth', 'MaxDex', 'CheckPenalty', 'Speed')
        )
        shield_rows = list(
            CharacterShield.objects
            .filter(Character=character)
            .order_by('id')
            .values('ACBonus', 'Weigth', 'CheckPenalty')
        )
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
        status.ACDexModifier = cap_dex_to_armor(stats.DexterityStatMod, _lowest_max_dex(armor_rows))
        status.ACTotal, status.ACTouch, status.ACFlatFooterd = compute_armor_class(
            armor_bonus=status.ACArmorBonus,
            shield_bonus=status.ACShieldBonus,
            dex_mod=status.ACDexModifier,
            size_mod=status.ACSizeModifier,
            natural_armor=status.ACNaturalArmor,
            deflection=status.ACDeflectionModifier,
            misc=status.ACMiscModifier,
        )
        # buffs planos de CA (Escudo da Fe, Pressa, etc.) somam aos tres valores
        ac_buff = buff_flat['ACBonus']
        status.ACTotal += ac_buff
        status.ACTouch += ac_buff
        status.ACFlatFooterd += ac_buff
        status.Initiative = stats.DexterityStatMod

        saves = character.charactersavingthrows
        saves.FortitudeAbilityModifier = stats.ConstitutionStatMod
        saves.ReflexAbilityModifier = stats.DexterityStatMod
        saves.WillAbilityModifier = stats.WisdomStatMod
        save_buff = buff_flat['SaveBonus']  # buffs planos (Bencao, Heroismo, etc.)
        saves.TotalFortitude = compute_save_total(
            base=saves.FortitudeBaseSave, ability_mod=saves.FortitudeAbilityModifier,
            magic=saves.FortitudeMagicModifier, misc=saves.FortitudeMiscModifier,
            temporary=saves.FortitudeTemporaryModifier,
        ) + save_buff
        saves.TotalReflex = compute_save_total(
            base=saves.ReflexBaseSave, ability_mod=saves.ReflexAbilityModifier,
            magic=saves.ReflexMagicModifier, misc=saves.ReflexMiscModifier,
            temporary=saves.ReflexTemporaryModifier,
        ) + save_buff
        saves.TotalWill = compute_save_total(
            base=saves.WillBaseSave, ability_mod=saves.WillAbilityModifier,
            magic=saves.WillMagicModifier, misc=saves.WillMiscModifier,
            temporary=saves.WillTemporaryModifier,
        ) + save_buff
        saves.save(update_fields=[
            'FortitudeAbilityModifier', 'ReflexAbilityModifier', 'WillAbilityModifier',
            'TotalFortitude', 'TotalReflex', 'TotalWill',
        ])

        attack = character.characterattackmodifiers
        attack.GrapplerBBA = attack.BBA
        attack.GrapplerStrModifier = stats.StrengthStatMod
        attack.TotalGrappler = compute_grapple_total(
            bba=attack.GrapplerBBA,
            str_mod=attack.GrapplerStrModifier,
            size_mod=attack.GrapplerSizeModifier,
            misc=attack.GrapplerMiscModifier,
        )
        attack.save(update_fields=['GrapplerBBA', 'GrapplerStrModifier', 'TotalGrappler'])

        weapons = list(CharacterWeapon.objects.filter(Character=character).order_by('id'))
        for weapon in weapons:
            ability_mod = stats.DexterityStatMod if _weapon_uses_ranged_bonus(weapon) else stats.StrengthStatMod
            total_bonus = compute_attack_bonus(
                bba=attack.BBA,
                ability_mod=ability_mod,
                size_mod=status.ACSizeModifier,
                misc=buff_flat['AttackBonus'],  # buffs planos de ataque (Bencao, Cancao, etc.)
            )
            weapon.AttackBonus = signed_bonus(total_bonus)
        if weapons:
            CharacterWeapon.objects.bulk_update(weapons, ['AttackBonus'])

        skills = list(CharacterSkill.objects.filter(Character=character))
        armor_penalty = _armor_check_penalty_total(armor_rows, shield_rows)
        for skill in skills:
            ability = SKILL_ABILITY_BY_NAME.get(skill.SkillName or '')
            # usa o mod EFETIVO (ja temp-aware) que acabou de ser gravado em StatMod
            skill.SkillAbility = skill_ability_key(skill.SkillName)
            skill.AbilityModifier = getattr(stats, f'{ability}StatMod') if ability else 0
            skill.SkillModifier = skill_total(
                skill.AbilityModifier,
                skill.Ranks,
                (skill.MiscModifier or 0) + armor_check_penalty_for_skill(skill.SkillName, armor_penalty),
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
        # Deslocamento e 100% manual: o valor digitado e a fonte da verdade e
        # nao e sobrescrito pelo recalculo (a reducao por carga e aplicada a mao).
        encumbrance.save(update_fields=[
            'LightLoad', 'MediumLoad', 'HeavyLoad', 'LiftOverHEad',
            'LiftOffGround', 'PushOrDrag', 'TotalWCarried',
        ])
        status.save(update_fields=[
            'ACArmorBonus', 'ACShieldBonus', 'ACMiscModifier', 'ACDexModifier',
            'ACTotal', 'ACTouch', 'ACFlatFooterd', 'Initiative',
        ])
        _sync_spellcasting_rows(character, stats)
    logger.info(
        'recalc done char=%s CA=%s/toque=%s/surpresa=%s salvas=F%s/R%s/V%s agarrar=%s carga=%s/%s',
        character.pk, status.ACTotal, status.ACTouch, status.ACFlatFooterd,
        saves.TotalFortitude, saves.TotalReflex, saves.TotalWill,
        attack.TotalGrappler, encumbrance.TotalWCarried, encumbrance.HeavyLoad,
    )


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
        'class_sprite': sprite_image_data(sprite_for_class(char.Class), SpriteVariant.ICON_96),
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
        'character_buffs': _related_items(char, 'characterbuff_set', CharacterBuff),
        'buff_presets': BUFF_PRESETS,
    }
    buff_ability, _ = _active_buff_totals(context['character'])
    context['character'].skill_rows = _annotate_skill_rules(
        _related_items(context['character'], 'characterskill_set', CharacterSkill),
        getattr(context['character'], 'characterstats', None),
        buff_ability,
    )
    context.update(extra)
    return context


# Cada seção derivada e seu id de container. Um campo-fonte editado em qualquer
# seção pode mudar derivados que vivem em OUTRAS seções (ex.: Destreza muda CA,
# Reflexos, Iniciativa e perícias). Como cada form só troca a si mesmo via
# hx-target, as demais seções voltam como out-of-band swaps na mesma resposta.
_DERIVED_OOB_SECTIONS = (
    ('characterStatsForm', 'character/partials/character_attrs_form.html'),
    ('characterSavesForm', 'character/partials/character_saves_form.html'),
    ('characterAttackForm', 'character/partials/character_attack_form.html'),
    ('characterWeaponsForm', 'character/partials/character_weapon_card.html'),
    ('characterArmorForm', 'character/partials/character_armor_form.html'),
    ('characterStatusForm', 'character/partials/character_status_form.html'),
    ('characterDefenseSummary', 'character/partials/character_defense_summary.html'),
    ('characterSkillsForm', 'character/partials/character_skills.html'),
)


def _render_recalculated(request, char, primary_template, primary_target, **primary_extra):
    """Devolve o partial editado como swap principal e todas as demais seções
    derivadas como out-of-band, para que um único edit atualize na tela toda a
    cascata de valores calculados."""
    context = _sheet_context(char, **primary_extra)
    fragments = [render_to_string(primary_template, context, request=request)]
    oob_context = {**context, 'oob': True}
    for target, template in _DERIVED_OOB_SECTIONS:
        if target == primary_target:
            continue
        fragments.append(render_to_string(template, oob_context, request=request))
    return HttpResponse(''.join(fragments))


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
        posted = [k for k in request.POST if k != 'csrfmiddlewaretoken']
        logger.info(
            'sheet POST char=%s user=%s target=%s autosave=%s fields=%s',
            char.pk, request.user.username, request.htmx.target,
            _is_autosave(request), posted,
        )

        if request.htmx.target == 'characterIdentityForm':
            form = CharacterIdentityForm(request.POST, instance=char)
            if form.is_valid():
                form.save()
                if _is_autosave(request):
                    return _autosave_204()
                char.refresh_from_db()
                _recalculate_stats(char)
                return _render_recalculated(
                    request, char, 'character/partials/character_identity.html',
                    'characterIdentityForm', characterIdentityForm=form,
                )
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
                'Attack', 'Damage', 'Critical', 'Range', 'Type', 'Notes', 'AmmunitionName',
            ], 4)
            # Recalcula e re-renderiza mesmo ao digitar (sem 204) para que os
            # modificadores apareçam ao vivo; o htmx restaura foco/cursor pelo id.
            _recalculate_stats(char)
            return _render_recalculated(
                request, char, 'character/partials/character_attrs_form.html', 'characterStatsForm',
            )

        if request.htmx.target == 'characterStatusForm':
            _update_fields_from_post(char.characterstatus, request, [
                'TotalHitPoints', 'CurrentHitPoints', 'TemporaryHitPoints', 'NonLethalDamager', 'Speed',
            ])
            _clamp_status_hit_points(char.characterstatus)
            if _is_autosave(request):
                return _autosave_204()
            _recalculate_stats(char)
            return _render_recalculated(
                request, char, 'character/partials/character_status_form.html', 'characterStatusForm',
            )

        if request.htmx.target == 'characterArmorForm':
            _update_fields_from_post(char.characterstatus, request, [
                'ACSizeModifier', 'ACNaturalArmor', 'ACDeflectionModifier', 'DamageReduction',
            ])
            _recalculate_stats(char)
            return _render_recalculated(
                request, char, 'character/partials/character_armor_form.html', 'characterArmorForm',
            )

        if request.htmx.target == 'characterSavesForm':
            _update_fields_from_post(char.charactersavingthrows, request, [
                'FortitudeBaseSave', 'FortitudeMagicModifier', 'FortitudeMiscModifier',
                'ReflexBaseSave', 'ReflexMagicModifier', 'ReflexMiscModifier',
                'WillBaseSave', 'WillMagicModifier', 'WillMiscModifier',
            ])
            _recalculate_stats(char)
            return _render_recalculated(
                request, char, 'character/partials/character_saves_form.html', 'characterSavesForm',
            )

        if request.htmx.target == 'characterAttackForm':
            _update_fields_from_post(char.characterattackmodifiers, request, [
                'BBA', 'SpellResistence', 'GrapplerSizeModifier', 'GrapplerMiscModifier',
            ])
            _recalculate_stats(char)
            return _render_recalculated(
                request, char, 'character/partials/character_attack_form.html', 'characterAttackForm',
            )

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
            return _render_recalculated(
                request, char, 'character/partials/character_skills.html', 'characterSkillsForm',
            )

        if request.htmx.target == 'characterWeaponsForm':
            _save_repeating_slots(char, request, CharacterWeapon, 'weapon', [
                'Attack', 'Damage', 'Critical', 'Range', 'Type', 'Notes', 'AmmunitionName',
            ], 4)
            if _is_autosave(request):
                return _autosave_204()
            _recalculate_stats(char)
            return _render_recalculated(
                request, char, 'character/partials/character_weapon_card.html', 'characterWeaponsForm',
            )

        if request.htmx.target == 'characterProgressForm':
            progress, _ = CharacterProgress.objects.get_or_create(Character=char)
            _update_fields_from_post(progress, request, ['ExperiencePoints', 'CampaignName'])
            if _is_autosave(request):
                return _autosave_204()
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
            if _is_autosave(request):
                return _autosave_204()
            _recalculate_stats(char)
            return _render_recalculated(
                request, char, 'character/partials/character_armor.html', 'characterEquipmentForm',
            )

        if request.htmx.target == 'characterItemsForm':
            _save_repeating_slots(char, request, CharacterOtherItem, 'item', ['Name', 'Page', 'Weigth'], 32)
            if _is_autosave(request):
                return _autosave_204()
            _recalculate_stats(char)
            return _render_recalculated(
                request, char, 'character/partials/character_items.html', 'characterItemsForm',
            )

        if request.htmx.target == 'characterMoneyForm':
            _update_fields_from_post(char.charactermoney, request, ['CP', 'SP', 'GP', 'PP'])
            _update_fields_from_post(char.characterotheritemobs, request, [
                'LightLoad', 'MediumLoad', 'HeavyLoad', 'LiftOverHEad', 'LiftOffGround',
                'PushOrDrag', 'TotalWCarried',
            ])
            if _is_autosave(request):
                return _autosave_204()
            _recalculate_stats(char)
            return _render_recalculated(
                request, char, 'character/partials/character_money.html', 'characterMoneyForm',
            )

        if request.htmx.target == 'characterFeatsForm':
            _save_repeating_slots(char, request, CharacterFeat, 'feat', ['Name', 'Page'], 24)
            if _is_autosave(request):
                return _autosave_204()
            return render(request, 'character/partials/character_feats.html', _sheet_context(char))

        if request.htmx.target == 'characterSpecialsForm':
            _save_repeating_slots(char, request, Ability, 'ability', ['Name', 'Page'], 12)
            _save_repeating_slots(char, request, CharacterLanguages, 'language', ['Value'], 12)
            if _is_autosave(request):
                return _autosave_204()
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
        target = request.htmx.target or ''
        if target == 'animalCompanionsForm':
            _save_typed_companion_slots(char, request, 'animal', 'animalCompanion', [
                'Name', 'Species', 'HitPoints', 'ArmorClass', 'Speed', 'SpecialAbilities',
            ], 4)
            if _is_autosave(request):
                return _autosave_204()
            return render(request, 'character/partials/companions_animal_form.html', _companions_context(char))
        if target == 'familiarsForm':
            _save_typed_companion_slots(char, request, 'familiar', 'familiar', [
                'Name', 'Species', 'HitPoints', 'ArmorClass', 'Speed', 'SpecialAbilities', 'Notes',
            ], 4)
            if _is_autosave(request):
                return _autosave_204()
            return render(request, 'character/partials/companions_familiar_form.html', _companions_context(char))
        if target == 'summonsGrid':
            _save_repeating_slots(char, request, CharacterSummon, 'summon', [
                'Name', 'SpellOrigin', 'Level', 'HitPointsMax', 'HitPointsCurrent',
                'ArmorClass', 'Initiative', 'Speed', 'BaseAttackBonus', 'Grapple',
                'Size', 'Attack', 'FullAttack', 'AttackBonus', 'Damage',
                'SpecialAbility', 'Skills', 'RoundsTotal', 'RoundsRemaining',
                'SdrMonsterName',
            ], 9)
            return render(request, 'character/partials/companions_summons_grid.html', _companions_context(char))

    return render(request, 'character/companions.html', _companions_context(char))


@login_required
def toggle_summon_highlight(request, pk, summon_id):
    char = get_object_or_404(Character, pk=pk, User=request.user)
    summon = get_object_or_404(CharacterSummon, pk=summon_id, Character=char)
    summon.Highlighted = not summon.Highlighted
    summon.save(update_fields=['Highlighted'])
    return render(request, 'character/partials/companions_summons_grid.html', _companions_context(char))


@login_required
def summon_search(request, pk):
    char = get_object_or_404(Character, pk=pk, User=request.user)
    query = (request.GET.get('q') or '').strip()
    if len(query) < 2:
        return HttpResponse('')

    monsters = (
        SDR_Monster.objects
        .using('sdr')
        .filter(name__icontains=query)
        .order_by('name')[:10]
    )
    if not monsters:
        return HttpResponse('')
    return render(request, 'character/partials/companions_summon_search_results.html', {
        'character': char,
        'monsters': monsters,
    })


@login_required
def create_summon_from_monster(request, pk, monster_id):
    char = get_object_or_404(Character, pk=pk, User=request.user)
    monster = get_object_or_404(SDR_Monster.objects.using('sdr'), pk=monster_id)
    hit_points = _monster_hit_points(monster)
    CharacterSummon.objects.create(
        Character=char,
        Name=monster.name or '',
        HitPointsMax=hit_points,
        HitPointsCurrent=hit_points,
        ArmorClass=_monster_armor_class(monster),
        Initiative=monster.initiative or '',
        Speed=monster.speed or '',
        BaseAttackBonus=monster.base_attack or '',
        Grapple=monster.grapple or '',
        Size=monster.size or '',
        Attack=monster.attack or '',
        FullAttack=monster.full_attack or '',
        AttackBonus=_monster_attack_bonus(monster),
        Damage=_monster_damage(monster),
        SpecialAbility=(monster.special_abilities or '')[:500],
        Skills=monster.skills or '',
        SdrMonsterName=monster.name or '',
    )
    return render(request, 'character/partials/companions_summons_grid.html', _companions_context(char))


@login_required
def spellbook(request, pk):
    char = get_object_or_404(Character, pk=pk, User=request.user)
    if request.method == 'POST' and request.htmx:
        if request.htmx.target == 'spellbookHeaderForm':
            _update_fields_from_post(char.characterspellcasting, request, _SPELLBOOK_PROFILE_FIELDS, 'spellcasting_')
            return render(request, 'character/partials/spellbook_header_form.html', _spellbook_context(char))

        if request.htmx.target == 'spellbookSlotsForm':
            _save_repeating_slots(char, request, CharacterSpellSlot, 'slot', [
                'Level', 'SlotType', 'PreparedSpellName', 'ConvertedTo',
            ], 20)
            return render(request, 'character/partials/spellbook_slots_form.html', _spellbook_context(char))

        target = request.htmx.target or ''
        if target.startswith('spellbookLevel') and target.endswith('Form'):
            try:
                level = int(target.removeprefix('spellbookLevel').removesuffix('Form'))
            except ValueError:
                level = None
            if level is not None and 0 <= level <= 9:
                _save_spellbook_level(char, request, level)
                if _is_autosave(request):
                    return _autosave_204()
                return render(request, 'character/partials/spellbook_level_form.html', _spellbook_level_context(char, level))

    return render(request, 'character/spellbook.html', _spellbook_context(char))


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
        if _is_autosave(request):
            return _autosave_204()
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
            if _is_autosave(request):
                return _autosave_204()
            return render(request, 'character/partials/reputation_contacts_form.html', _reputation_context(char))

        if request.htmx.target == 'reputationFactionsForm':
            _save_repeating_slots(char, request, CharacterFaction, 'faction', [
                'Name', 'Reputation', 'Influence', 'Risk', 'Notes',
            ], 10)
            if _is_autosave(request):
                return _autosave_204()
            return render(request, 'character/partials/reputation_factions_form.html', _reputation_context(char))

        if request.htmx.target == 'reputationContractsForm':
            _save_repeating_slots(char, request, CharacterContract, 'contract', [
                'Title', 'Party', 'Reward', 'Deadline', 'Status', 'Notes',
            ], 12)
            if _is_autosave(request):
                return _autosave_204()
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
def toggle_buff(request, pk, buff_id):
    char = get_object_or_404(Character, pk=pk, User=request.user)
    buff = get_object_or_404(CharacterBuff, pk=buff_id, Character=char)
    buff.IsActive = not buff.IsActive
    buff.save(update_fields=['IsActive'])
    logger.info('buff toggle char=%s buff=%s ativo=%s', char.pk, buff.Name, buff.IsActive)
    _recalculate_stats(char)
    return _render_recalculated(
        request, char, 'character/partials/character_buffs.html', 'characterBuffsForm',
    )


@login_required
def add_buff(request, pk):
    char = get_object_or_404(Character, pk=pk, User=request.user)
    preset = next(
        (p for p in BUFF_PRESETS if p['Name'] == (request.POST.get('preset') or '').strip()),
        None,
    )
    if preset:
        CharacterBuff.objects.create(Character=char, **preset)
    else:
        name = _clean_text_value(request.POST.get('custom_name'), CharacterBuff._meta.get_field('Name'))
        if name:
            buff = CharacterBuff(Character=char, Name=name)
            for field in BUFF_EFFECT_FIELDS:
                setattr(buff, field, _clamp_int(_post_int(request, field)))
            buff.Notes = _clean_text_value(request.POST.get('Notes'), CharacterBuff._meta.get_field('Notes'))
            buff.save()
    # buff novo nasce inativo -> nao precisa recalcular, so re-renderiza o painel
    return render(request, 'character/partials/character_buffs.html', _sheet_context(char))


@login_required
def delete_buff(request, pk, buff_id):
    char = get_object_or_404(Character, pk=pk, User=request.user)
    buff = get_object_or_404(CharacterBuff, pk=buff_id, Character=char)
    was_active = buff.IsActive
    buff.delete()
    if was_active:
        _recalculate_stats(char)
        return _render_recalculated(
            request, char, 'character/partials/character_buffs.html', 'characterBuffsForm',
        )
    return render(request, 'character/partials/character_buffs.html', _sheet_context(char))


@login_required
def toggleSpellSlot(request, pk, slot_id):
    char = get_object_or_404(Character, pk=pk, User=request.user)
    slot = get_object_or_404(CharacterSpellSlot, pk=slot_id, Character=char)
    if request.method == 'POST':
        slot.IsUsed = not slot.IsUsed
        slot.save(update_fields=['IsUsed'])
    return render(request, 'character/partials/spellbook_slots_form.html', _spellbook_context(char))


@login_required
def spell_detail(request, pk, sdr_id):
    get_object_or_404(Character, pk=pk, User=request.user)
    spell = get_object_or_404(SDR_Spell.objects.using('sdr'), id=sdr_id)
    return render(request, 'character/partials/spell_detail_dialog.html', {'spell': spell})
