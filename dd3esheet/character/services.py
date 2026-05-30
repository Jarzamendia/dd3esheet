from .models import (
    CharacterStats, CharacterStatus, CharacterSavingThrows,
    CharacterAttackModifiers, CharacterSkillGraduation, CharacterOtherItemObs,
    CharacterMoney, CharacterProgress, CharacterSpellSave, CharacterArcaneSpellFailCheck,
    CharacterMagicConditionalModifiers, CharacterSpellcasting, CharacterSkill,
    CharacterDailyNotes,
)
from sdr.models import SDR_Class

from .constants import CLASS_LABEL_PT, EXPANDABLE_SKILL_NAMES, PHB_BASE_CLASSES, SKILL_LIST_PT


_SKILL_LIST = SKILL_LIST_PT


def _bootstrap_character_siblings(character):
    CharacterStats(Character=character).save()
    CharacterStatus(Character=character).save()
    CharacterSavingThrows(Character=character).save()
    CharacterAttackModifiers(Character=character).save()
    CharacterSkillGraduation(Character=character).save()
    CharacterOtherItemObs(Character=character).save()
    CharacterMoney(Character=character).save()
    CharacterProgress(Character=character).save()
    CharacterSpellSave(Character=character).save()
    CharacterArcaneSpellFailCheck(Character=character).save()
    CharacterMagicConditionalModifiers(Character=character).save()
    CharacterSpellcasting(Character=character).save()
    CharacterDailyNotes(Character=character).save()
    for skill in _SKILL_LIST:
        CharacterSkill(Character=character, SkillName=skill).save()


def ensure_expandable_skill_slots(character):
    prefetched_skills = getattr(character, '_prefetched_objects_cache', {}).get('characterskill_set')
    if prefetched_skills is not None:
        existing_slots = [
            skill for skill in prefetched_skills
            if skill.SkillName in EXPANDABLE_SKILL_NAMES
        ]
    else:
        existing_slots = list(
            CharacterSkill.objects
            .filter(Character=character, SkillName__in=EXPANDABLE_SKILL_NAMES)
            .order_by('SkillName', 'id')
        )
    slots_by_name = {
        skill_name: [slot for slot in existing_slots if slot.SkillName == skill_name]
        for skill_name in EXPANDABLE_SKILL_NAMES
    }
    for skill_name in EXPANDABLE_SKILL_NAMES:
        slots = slots_by_name[skill_name]
        while len(slots) < 3:
            slots.append(CharacterSkill.objects.create(Character=character, SkillName=skill_name))
        if slots and all((slot.SkillSpecialization or '').strip() for slot in slots):
            CharacterSkill.objects.create(Character=character, SkillName=skill_name)


def sdr_class_choices():
    existing = set(
        SDR_Class.objects
        .using('sdr')
        .values_list('name', flat=True)
        .distinct()
    )
    names = [name for name in PHB_BASE_CLASSES if name in existing]
    return [('', '—')] + [(name, CLASS_LABEL_PT.get(name, name)) for name in names]
