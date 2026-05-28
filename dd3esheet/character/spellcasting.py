from dataclasses import dataclass

from sdr.models import SDR_ClassTable, SDR_Domain


CASTER_CONFIG = {
    'Wizard': {
        'ability': 'Intelligence',
        'ability_label': 'INT',
        'mode': 'prepared_book',
        'conversion': '',
    },
    'Sorcerer': {
        'ability': 'Charisma',
        'ability_label': 'CAR',
        'mode': 'spontaneous_known',
        'conversion': '',
    },
    'Cleric': {
        'ability': 'Wisdom',
        'ability_label': 'SAB',
        'mode': 'prepared_divine',
        'conversion': 'cure_or_inflict',
    },
    'Druid': {
        'ability': 'Wisdom',
        'ability_label': 'SAB',
        'mode': 'prepared_divine',
        'conversion': 'summon_nature_ally',
    },
}


@dataclass(frozen=True)
class SpellLevelSummary:
    level: int
    spells_known: str
    save_dc: str
    spells_per_day: str
    bonus_spells: str
    used_slots: int
    remaining_slots: str


def ability_modifier(score):
    if score is None:
        return 0
    return (score - 10) // 2


def spell_save_dc(spell_level, ability_score):
    return 10 + int(spell_level) + ability_modifier(ability_score)


def bonus_spells_for_level(ability_score, spell_level):
    spell_level = int(spell_level)
    if spell_level == 0:
        return 0
    mod = ability_modifier(ability_score)
    if mod < spell_level:
        return 0
    return 1 + ((mod - spell_level) // 4)


def numeric_slot_count(value):
    if value in (None, '', '-', 'None'):
        return 0
    total = 0
    for part in str(value).split('+'):
        try:
            total += int(part)
        except ValueError:
            continue
    return total


def caster_config_for_class(class_name):
    return CASTER_CONFIG.get(class_name or '', {
        'ability': 'Wisdom',
        'ability_label': 'SAB',
        'mode': 'custom',
        'conversion': '',
    })


def class_table_for_character(character):
    if not character.Class or not character.Level:
        return None
    return (
        SDR_ClassTable.objects
        .using('sdr')
        .filter(name=character.Class, level=str(character.Level))
        .first()
    )


def domain_spells(domain_name):
    if not domain_name:
        return []
    domain = SDR_Domain.objects.using('sdr').filter(name=domain_name).first()
    if not domain:
        return []
    return [
        {'level': level, 'name': getattr(domain, f'spell_{level}') or ''}
        for level in range(1, 10)
    ]


def spellcasting_context(character):
    config = caster_config_for_class(character.Class)
    try:
        profile = character.characterspellcasting
    except Exception:
        profile = None
    stats = getattr(character, 'characterstats', None)
    class_table = class_table_for_character(character)
    slots = list(character.characterspellslot_set.all().order_by('Level', 'SlotType', 'id'))
    slot_counts = {}
    for slot in slots:
        slot_counts.setdefault(slot.Level, 0)
        if slot.IsUsed:
            slot_counts[slot.Level] += 1

    ability_score = 10
    if config and stats:
        ability_score = getattr(stats, config['ability'], 10) or 10

    levels = []
    for level in range(10):
        per_day = getattr(class_table, f'slots_{level}', None) if class_table else None
        known = getattr(class_table, f'spells_known_{level}', None) if class_table else None
        if known in (None, '', 'None'):
            known = 'todas' if character.Class in ('Cleric', 'Druid') else '-'
        if per_day in (None, '', 'None'):
            per_day = '-'
        bonus = bonus_spells_for_level(ability_score, level)
        total_slots = numeric_slot_count(per_day) + bonus
        used = slot_counts.get(level, 0)
        remaining = '-' if total_slots == 0 else str(max(total_slots - used, 0))
        levels.append(SpellLevelSummary(
            level=level,
            spells_known=known,
            save_dc=spell_save_dc(level, ability_score) if config else '-',
            spells_per_day=per_day,
            bonus_spells='-' if level == 0 else str(bonus),
            used_slots=used,
            remaining_slots=remaining,
        ))

    return {
        'profile': profile,
        'config': config,
        'levels': levels,
        'slots': slots,
        'known_spells': character.characterspell_set.all().order_by('Level', 'Name'),
        'domain_1_spells': domain_spells(profile.Domain1 if profile else ''),
        'domain_2_spells': domain_spells(profile.Domain2 if profile else ''),
    }
