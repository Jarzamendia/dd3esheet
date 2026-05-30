import re


ABILITY_FIELDS = ('Strength', 'Dexterity', 'Constitution', 'Intelligence', 'Wisdom', 'Charisma')

ABILITY_KEY_LABELS = {
    'Strength': 'FOR',
    'Dexterity': 'DES',
    'Constitution': 'CON',
    'Intelligence': 'INT',
    'Wisdom': 'SAB',
    'Charisma': 'CAR',
}


SKILL_ABILITY_BY_NAME = {
    'Avaliar': 'Intelligence',
    'Equilibrio': 'Dexterity',
    'Blefar': 'Charisma',
    'Escalar': 'Strength',
    'Concentracao': 'Constitution',
    'Oficios': 'Intelligence',
    'Decifrar Escrita': 'Intelligence',
    'Operar Mecanismo': 'Intelligence',
    'Disfarces': 'Charisma',
    'Arte da Fuga': 'Dexterity',
    'Falsificacao': 'Intelligence',
    'Obter Informacao': 'Charisma',
    'Adestrar Animais': 'Charisma',
    'Cura': 'Wisdom',
    'Esconder-se': 'Dexterity',
    'Intimidar': 'Charisma',
    'Saltar': 'Strength',
    'Conhecimento': 'Intelligence',
    'Ouvir': 'Wisdom',
    'Furtividade': 'Dexterity',
    'Abrir Fechaduras': 'Dexterity',
    'Atuacao': 'Charisma',
    'Profissao': 'Wisdom',
    'Cavalgar': 'Dexterity',
    'Procurar': 'Intelligence',
    'Sentir Motivacao': 'Wisdom',
    'Prestidigitacao': 'Dexterity',
    'Identificar Magia': 'Intelligence',
    'Observar': 'Wisdom',
    'Sobrevivencia': 'Wisdom',
    'Natacao': 'Strength',
    'Acrobacia': 'Dexterity',
    'Usar Instrumento Magico': 'Charisma',
    'Usar Cordas': 'Dexterity',
    'Appraise': 'Intelligence',
    'Balance': 'Dexterity',
    'Bluff': 'Charisma',
    'Climb': 'Strength',
    'Concentration': 'Constitution',
    'Craft': 'Intelligence',
    'DecipherScript': 'Intelligence',
    'Diplomacy': 'Charisma',
    'DisableDevice': 'Intelligence',
    'Disguise': 'Charisma',
    'EscapeArtist': 'Dexterity',
    'Forgery': 'Intelligence',
    'GatherInformation': 'Charisma',
    'HandleAnimal': 'Charisma',
    'Heal': 'Wisdom',
    'Hide': 'Dexterity',
    'Intimidate': 'Charisma',
    'Jump': 'Strength',
    'Knowledge': 'Intelligence',
    'Listen': 'Wisdom',
    'MoveSilently': 'Dexterity',
    'OpenLock': 'Dexterity',
    'Perform': 'Charisma',
    'Profession': 'Wisdom',
    'Ride': 'Dexterity',
    'Search': 'Intelligence',
    'SenseMotive': 'Wisdom',
    'SleightofHand': 'Dexterity',
    'Spellcraft': 'Intelligence',
    'Spot': 'Wisdom',
    'Survival': 'Wisdom',
    'Swim': 'Strength',
    'Tumble': 'Dexterity',
    'UseMagicDevice': 'Charisma',
    'UseRope': 'Dexterity',
}


TRAINED_ONLY_SKILLS = {
    'Decifrar Escrita',
    'Operar Mecanismo',
    'Adestrar Animais',
    'Conhecimento',
    'Abrir Fechaduras',
    'Oficios',
    'Profissao',
    'Prestidigitacao',
    'Identificar Magia',
    'Acrobacia',
    'Usar Instrumento Magico',
    'DecipherScript',
    'DisableDevice',
    'HandleAnimal',
    'Knowledge',
    'OpenLock',
    'Craft',
    'Profession',
    'SleightofHand',
    'Spellcraft',
    'Tumble',
    'UseMagicDevice',
}


_LOAD_LIMITS = {
    1: (3, 6, 10),
    2: (6, 13, 20),
    3: (10, 20, 30),
    4: (13, 26, 40),
    5: (16, 33, 50),
    6: (20, 40, 60),
    7: (23, 46, 70),
    8: (26, 53, 80),
    9: (30, 60, 90),
    10: (33, 66, 100),
    11: (38, 76, 115),
    12: (43, 86, 130),
    13: (50, 100, 150),
    14: (58, 116, 175),
    15: (66, 133, 200),
    16: (76, 153, 230),
    17: (86, 173, 260),
    18: (100, 200, 300),
    19: (116, 233, 350),
    20: (133, 266, 400),
    21: (153, 306, 460),
    22: (173, 346, 520),
    23: (200, 400, 600),
    24: (233, 466, 700),
    25: (266, 533, 800),
    26: (306, 613, 920),
    27: (346, 693, 1040),
    28: (400, 800, 1200),
    29: (466, 933, 1400),
}


def to_int(value, default=0):
    if value in (None, ''):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def ability_modifier(score):
    return (to_int(score, 0) - 10) // 2


def skill_graduation_limits(level):
    level = to_int(level, 0)
    if level < 1:
        return 0, 0
    max_class = level + 3
    return max_class, max_class // 2


def skill_total(ability_mod, ranks, misc, trained_only=False):
    if trained_only and to_int(ranks) <= 0:
        return 0
    return to_int(ability_mod) + to_int(ranks) + to_int(misc)


def skill_ability_modifier(skill_name, stats):
    ability = SKILL_ABILITY_BY_NAME.get(skill_name or '')
    if not ability:
        return 0
    if hasattr(stats, ability):
        return ability_modifier(getattr(stats, ability))
    return ability_modifier(stats.get(ability))


def skill_ability_key(skill_name):
    ability = SKILL_ABILITY_BY_NAME.get(skill_name or '')
    return ABILITY_KEY_LABELS.get(ability, '')


def is_trained_only_skill(skill_name):
    return (skill_name or '') in TRAINED_ONLY_SKILLS


def load_limits_for_strength(strength):
    strength = to_int(strength, 0)
    if strength < 1:
        return 0, 0, 0, 0, 0, 0

    if strength <= 29:
        light, medium, heavy = _LOAD_LIMITS[strength]
    else:
        base_strength = 20 + ((strength - 20) % 10)
        multiplier = 4 ** ((strength - 20) // 10)
        light, medium, heavy = (value * multiplier for value in _LOAD_LIMITS[base_strength])

    lift_over_head = heavy
    lift_off_ground = heavy * 2
    push_or_drag = heavy * 5
    return light, medium, heavy, lift_over_head, lift_off_ground, push_or_drag


def parse_weight(value):
    if value in (None, ''):
        return 0
    match = re.search(r'-?\d+(?:[.,]\d+)?', str(value))
    if not match:
        return 0
    return float(match.group(0).replace(',', '.'))


def total_carried_weight(values):
    return round(sum(parse_weight(value) for value in values))


def parse_bonus(value):
    if value in (None, ''):
        return 0
    match = re.search(r'[+-]?\d+', str(value))
    if not match:
        return 0
    return int(match.group(0))


def equipment_armor_class_bonuses(armor_bonus, shield_bonus, protection_bonuses):
    protection_total = sum(parse_bonus(value) for value in protection_bonuses)
    return parse_bonus(armor_bonus), parse_bonus(shield_bonus), protection_total


def daily_resource_remaining(maximum, used):
    return max(to_int(maximum) - to_int(used), 0)


def compute_armor_class(*, armor_bonus, shield_bonus, dex_mod, size_mod,
                        natural_armor, deflection, misc):
    armor_bonus = to_int(armor_bonus)
    shield_bonus = to_int(shield_bonus)
    dex_mod = to_int(dex_mod)
    size_mod = to_int(size_mod)
    natural_armor = to_int(natural_armor)
    deflection = to_int(deflection)
    misc = to_int(misc)
    total = 10 + armor_bonus + shield_bonus + dex_mod + size_mod + natural_armor + deflection + misc
    touch = 10 + dex_mod + size_mod + deflection + misc
    flat_footed = 10 + armor_bonus + shield_bonus + size_mod + natural_armor + deflection + misc
    return total, touch, flat_footed


def compute_save_total(*, base, ability_mod, magic, misc, temporary):
    return to_int(base) + to_int(ability_mod) + to_int(magic) + to_int(misc) + to_int(temporary)


def compute_grapple_total(*, bba, str_mod, size_mod, misc):
    return to_int(bba) + to_int(str_mod) + to_int(size_mod) + to_int(misc)


def compute_skill_row(*, skill_name, stats):
    ability_key = skill_ability_key(skill_name)
    ability_mod = skill_ability_modifier(skill_name, stats)
    return ability_key, ability_mod
