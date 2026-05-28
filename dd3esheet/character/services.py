from .models import (
    CharacterStats, CharacterStatus, CharacterSavingThrows,
    CharacterAttackModifiers, CharacterSkillGraduation, CharacterOtherItemObs,
    CharacterMoney, CharacterSpellSave, CharacterArcaneSpellFailCheck,
    CharacterMagicConditionalModifiers, CharacterSpellcasting, CharacterSkill,
)
from sdr.models import SDR_Class

from .constants import CLASS_LABEL_PT


_SKILL_LIST = [
    'Appraise', 'Balance', 'Bluff', 'Climb', 'Concentration', 'Craft',
    'DecipherScript', 'Diplomacy', 'DisableDevice', 'Disguise', 'EscapeArtist',
    'Forgery', 'GatherInformation', 'HandleAnimal', 'Heal', 'Hide',
    'Intimidate', 'Jump', 'Knowledge', 'Listen', 'MoveSilently', 'OpenLock',
    'Perform', 'Profession', 'Ride', 'Search', 'SenseMotive', 'SleightofHand',
    'Spellcraft', 'Spot', 'Survival', 'Swim', 'Tumble', 'UseMagicDevice',
    'UseRope',
]


def _bootstrap_character_siblings(character):
    CharacterStats(Character=character).save()
    CharacterStatus(Character=character).save()
    CharacterSavingThrows(Character=character).save()
    CharacterAttackModifiers(Character=character).save()
    CharacterSkillGraduation(Character=character).save()
    CharacterOtherItemObs(Character=character).save()
    CharacterMoney(Character=character).save()
    CharacterSpellSave(Character=character).save()
    CharacterArcaneSpellFailCheck(Character=character).save()
    CharacterMagicConditionalModifiers(Character=character).save()
    CharacterSpellcasting(Character=character).save()
    for skill in _SKILL_LIST:
        CharacterSkill(Character=character, SkillName=skill).save()


def sdr_class_choices():
    names = (
        SDR_Class.objects
        .using('sdr')
        .order_by('name')
        .values_list('name', flat=True)
        .distinct()
    )
    return [('', '—')] + [(n, CLASS_LABEL_PT.get(n, n)) for n in names]
