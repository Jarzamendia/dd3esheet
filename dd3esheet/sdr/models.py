from django.db import models

class SDR_Class(models.Model):
    name = models.CharField(max_length=999,)
    type = models.CharField(max_length=999,blank=True, null=True)
    alignment = models.CharField(max_length=999,blank=True, null=True)
    hit_die = models.CharField(max_length=999,blank=True, null=True)
    class_skills = models.TextField(blank=True, null=True)  # This field type is a guess.
    skill_points = models.CharField(max_length=999,blank=True, null=True)
    skill_points_ability = models.CharField(max_length=999,blank=True, null=True)
    spell_stat = models.CharField(max_length=999,blank=True, null=True)
    proficiencies = models.TextField(blank=True, null=True)  # This field type is a guess.
    spell_type = models.CharField(max_length=999,blank=True, null=True)
    epic_feat_base_level = models.CharField(max_length=999,blank=True, null=True)
    epic_feat_interval = models.CharField(max_length=999,blank=True, null=True)
    epic_feat_list = models.TextField(blank=True, null=True)  # This field type is a guess.
    epic_full_text = models.TextField(blank=True, null=True)  # This field type is a guess.
    req_race = models.CharField(max_length=999,blank=True, null=True)
    req_weapon_proficiency = models.CharField(max_length=999,blank=True, null=True)
    req_base_attack_bonus = models.CharField(max_length=999,blank=True, null=True)
    req_skill = models.CharField(max_length=999,blank=True, null=True)
    req_feat = models.CharField(max_length=999,blank=True, null=True)
    req_spells = models.CharField(max_length=999,blank=True, null=True)
    req_languages = models.CharField(max_length=999,blank=True, null=True)
    req_psionics = models.CharField(max_length=999,blank=True, null=True)
    req_epic_feat = models.CharField(max_length=999,blank=True, null=True)
    req_special = models.CharField(max_length=999,blank=True, null=True)
    spell_list_1 = models.TextField(blank=True, null=True)  # This field type is a guess.
    spell_list_2 = models.CharField(max_length=999,blank=True, null=True)
    spell_list_3 = models.CharField(max_length=999,blank=True, null=True)
    spell_list_4 = models.CharField(max_length=999,blank=True, null=True)
    spell_list_5 = models.CharField(max_length=999,blank=True, null=True)
    full_text = models.TextField(blank=True, null=True)  # This field type is a guess.
    reference = models.CharField(max_length=999,blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'class'


class SDR_ClassTable(models.Model):
    name = models.CharField(max_length=999,)
    level = models.CharField(max_length=999,blank=True, null=True)
    base_attack_bonus = models.CharField(max_length=999,blank=True, null=True)
    fort_save = models.CharField(max_length=999,blank=True, null=True)
    ref_save = models.CharField(max_length=999,blank=True, null=True)
    will_save = models.CharField(max_length=999,blank=True, null=True)
    caster_level = models.CharField(max_length=999,blank=True, null=True)
    points_per_day = models.CharField(max_length=999,blank=True, null=True)
    ac_bonus = models.CharField(max_length=999,blank=True, null=True)
    flurry_of_blows = models.CharField(max_length=999,blank=True, null=True)
    bonus_spells = models.CharField(max_length=999,blank=True, null=True)
    powers_known = models.CharField(max_length=999,blank=True, null=True)
    unarmored_speed_bonus = models.CharField(max_length=999,blank=True, null=True)
    unarmed_damage = models.CharField(max_length=999,blank=True, null=True)
    power_level = models.CharField(max_length=999,blank=True, null=True)
    special = models.CharField(max_length=999,blank=True, null=True)
    slots_0 = models.CharField(max_length=999,blank=True, null=True)
    slots_1 = models.CharField(max_length=999,blank=True, null=True)
    slots_2 = models.CharField(max_length=999,blank=True, null=True)
    slots_3 = models.CharField(max_length=999,blank=True, null=True)
    slots_4 = models.CharField(max_length=999,blank=True, null=True)
    slots_5 = models.CharField(max_length=999,blank=True, null=True)
    slots_6 = models.CharField(max_length=999,blank=True, null=True)
    slots_7 = models.CharField(max_length=999,blank=True, null=True)
    slots_8 = models.CharField(max_length=999,blank=True, null=True)
    slots_9 = models.CharField(max_length=999,blank=True, null=True)
    spells_known_0 = models.CharField(max_length=999,blank=True, null=True)
    spells_known_1 = models.CharField(max_length=999,blank=True, null=True)
    spells_known_2 = models.CharField(max_length=999,blank=True, null=True)
    spells_known_3 = models.CharField(max_length=999,blank=True, null=True)
    spells_known_4 = models.CharField(max_length=999,blank=True, null=True)
    spells_known_5 = models.CharField(max_length=999,blank=True, null=True)
    spells_known_6 = models.CharField(max_length=999,blank=True, null=True)
    spells_known_7 = models.CharField(max_length=999,blank=True, null=True)
    spells_known_8 = models.CharField(max_length=999,blank=True, null=True)
    spells_known_9 = models.CharField(max_length=999,blank=True, null=True)
    reference = models.CharField(max_length=999,blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'class_table'


class SDR_Domain(models.Model):
    name = models.CharField(max_length=999,)
    granted_powers = models.TextField(blank=True, null=True)  # This field type is a guess.
    spell_1 = models.CharField(max_length=999,blank=True, null=True)
    spell_2 = models.CharField(max_length=999,blank=True, null=True)
    spell_3 = models.CharField(max_length=999,blank=True, null=True)
    spell_4 = models.CharField(max_length=999,blank=True, null=True)
    spell_5 = models.CharField(max_length=999,blank=True, null=True)
    spell_6 = models.CharField(max_length=999,blank=True, null=True)
    spell_7 = models.CharField(max_length=999,blank=True, null=True)
    spell_8 = models.CharField(max_length=999,blank=True, null=True)
    spell_9 = models.CharField(max_length=999,blank=True, null=True)
    full_text = models.TextField(blank=True, null=True)  # This field type is a guess.
    reference = models.CharField(max_length=999,blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'domain'


class SDR_Equipment(models.Model):
    name = models.CharField(max_length=999,)
    family = models.CharField(max_length=999,blank=True, null=True)
    category = models.CharField(max_length=999,blank=True, null=True)
    subcategory = models.CharField(max_length=999,blank=True, null=True)
    cost = models.CharField(max_length=999,blank=True, null=True)
    dmg_s = models.CharField(max_length=999,blank=True, null=True)
    armor_shield_bonus = models.CharField(max_length=999,blank=True, null=True)
    maximum_dex_bonus = models.CharField(max_length=999,blank=True, null=True)
    dmg_m = models.CharField(max_length=999,blank=True, null=True)
    weight = models.CharField(max_length=999,blank=True, null=True)
    critical = models.CharField(max_length=999,blank=True, null=True)
    armor_check_penalty = models.CharField(max_length=999,blank=True, null=True)
    arcane_spell_failure_chance = models.CharField(max_length=999,blank=True, null=True)
    range_increment = models.CharField(max_length=999,blank=True, null=True)
    speed_30 = models.CharField(max_length=999,blank=True, null=True)
    type = models.CharField(max_length=999,blank=True, null=True)
    speed_20 = models.CharField(max_length=999,blank=True, null=True)
    full_text = models.TextField(blank=True, null=True)  # This field type is a guess.
    reference = models.CharField(max_length=999,blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'equipment'


class SDR_Feat(models.Model):
    name = models.CharField(max_length=999,)
    type = models.CharField(max_length=999,blank=True, null=True)
    multiple = models.CharField(max_length=999,blank=True, null=True)
    stack = models.CharField(max_length=999,blank=True, null=True)
    choice = models.CharField(max_length=999,blank=True, null=True)
    prerequisite = models.TextField(blank=True, null=True)  # This field type is a guess.
    benefit = models.TextField(blank=True, null=True)  # This field type is a guess.
    normal = models.TextField(blank=True, null=True)  # This field type is a guess.
    special = models.TextField(blank=True, null=True)  # This field type is a guess.
    full_text = models.TextField(blank=True, null=True)  # This field type is a guess.
    reference = models.CharField(max_length=999,blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'feat'


class SDR_Item(models.Model):
    name = models.CharField(max_length=999,)
    category = models.CharField(max_length=999,blank=True, null=True)
    subcategory = models.CharField(max_length=999,blank=True, null=True)
    special_ability = models.CharField(max_length=999,blank=True, null=True)
    aura = models.CharField(max_length=999,blank=True, null=True)
    caster_level = models.CharField(max_length=999,blank=True, null=True)
    price = models.CharField(max_length=999,blank=True, null=True)
    manifester_level = models.CharField(max_length=999,blank=True, null=True)
    prereq = models.TextField(blank=True, null=True)  # This field type is a guess.
    cost = models.CharField(max_length=999,blank=True, null=True)
    weight = models.CharField(max_length=999,blank=True, null=True)
    full_text = models.TextField(blank=True, null=True)  # This field type is a guess.
    reference = models.CharField(max_length=999,blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'item'


class SDR_Monster(models.Model):
    family = models.CharField(max_length=999,blank=True, null=True)
    name = models.CharField(max_length=999,)
    altname = models.CharField(max_length=999,blank=True, null=True)
    size = models.CharField(max_length=999,blank=True, null=True)
    type = models.CharField(max_length=999,blank=True, null=True)
    descriptor = models.CharField(max_length=999,blank=True, null=True)
    hit_dice = models.CharField(max_length=999,blank=True, null=True)
    initiative = models.CharField(max_length=999,blank=True, null=True)
    speed = models.CharField(max_length=999,blank=True, null=True)
    armor_class = models.CharField(max_length=999,blank=True, null=True)
    base_attack = models.CharField(max_length=999,blank=True, null=True)
    grapple = models.CharField(max_length=999,blank=True, null=True)
    attack = models.CharField(max_length=999,blank=True, null=True)
    full_attack = models.TextField(blank=True, null=True)  # This field type is a guess.
    space = models.CharField(max_length=999,blank=True, null=True)
    reach = models.CharField(max_length=999,blank=True, null=True)
    special_attacks = models.CharField(max_length=999,blank=True, null=True)
    special_qualities = models.TextField(blank=True, null=True)  # This field type is a guess.
    saves = models.CharField(max_length=999,blank=True, null=True)
    abilities = models.CharField(max_length=999,blank=True, null=True)
    skills = models.TextField(blank=True, null=True)  # This field type is a guess.
    bonus_feats = models.CharField(max_length=999,blank=True, null=True)
    feats = models.TextField(blank=True, null=True)  # This field type is a guess.
    epic_feats = models.TextField(blank=True, null=True)  # This field type is a guess.
    environment = models.CharField(max_length=999,blank=True, null=True)
    organization = models.TextField(blank=True, null=True)  # This field type is a guess.
    challenge_rating = models.CharField(max_length=999,blank=True, null=True)
    treasure = models.CharField(max_length=999,blank=True, null=True)
    alignment = models.CharField(max_length=999,blank=True, null=True)
    advancement = models.CharField(max_length=999,blank=True, null=True)
    level_adjustment = models.CharField(max_length=999,blank=True, null=True)
    special_abilities = models.TextField(blank=True, null=True)  # This field type is a guess.
    stat_block = models.TextField(blank=True, null=True)  # This field type is a guess.
    full_text = models.TextField(blank=True, null=True)  # This field type is a guess.
    reference = models.CharField(max_length=999,blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'monster'


class SDR_Power(models.Model):
    name = models.CharField(max_length=999,)
    discipline = models.CharField(max_length=999,blank=True, null=True)
    subdiscipline = models.CharField(max_length=999,blank=True, null=True)
    descriptor = models.CharField(max_length=999,blank=True, null=True)
    level = models.CharField(max_length=999,blank=True, null=True)
    display = models.CharField(max_length=999,blank=True, null=True)
    manifesting_time = models.CharField(max_length=999,blank=True, null=True)
    range = models.CharField(max_length=999,blank=True, null=True)
    target = models.CharField(max_length=999,blank=True, null=True)
    area = models.CharField(max_length=999,blank=True, null=True)
    effect = models.CharField(max_length=999,blank=True, null=True)
    duration = models.CharField(max_length=999,blank=True, null=True)
    saving_throw = models.CharField(max_length=999,blank=True, null=True)
    power_points = models.CharField(max_length=999,blank=True, null=True)
    power_resistance = models.CharField(max_length=999,blank=True, null=True)
    short_description = models.TextField(blank=True, null=True)  # This field type is a guess.
    xp_cost = models.TextField(blank=True, null=True)  # This field type is a guess.
    description = models.TextField(blank=True, null=True)  # This field type is a guess.
    augment = models.TextField(blank=True, null=True)  # This field type is a guess.
    full_text = models.TextField(blank=True, null=True)  # This field type is a guess.
    reference = models.CharField(max_length=999,blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'power'


class SDR_Skill(models.Model):
    name = models.CharField(max_length=999,)
    subtype = models.TextField(blank=True, null=True)  # This field type is a guess.
    key_ability = models.CharField(max_length=999,blank=True, null=True)
    psionic = models.CharField(max_length=999,blank=True, null=True)
    trained = models.CharField(max_length=999,blank=True, null=True)
    armor_check = models.CharField(max_length=999,blank=True, null=True)
    description = models.TextField(blank=True, null=True)  # This field type is a guess.
    skill_check = models.TextField(blank=True, null=True)  # This field type is a guess.
    action = models.TextField(blank=True, null=True)  # This field type is a guess.
    try_again = models.TextField(blank=True, null=True)  # This field type is a guess.
    special = models.TextField(blank=True, null=True)  # This field type is a guess.
    restriction = models.TextField(blank=True, null=True)  # This field type is a guess.
    synergy = models.TextField(blank=True, null=True)  # This field type is a guess.
    epic_use = models.TextField(blank=True, null=True)  # This field type is a guess.
    untrained = models.TextField(blank=True, null=True)  # This field type is a guess.
    full_text = models.TextField(blank=True, null=True)  # This field type is a guess.
    reference = models.CharField(max_length=999,blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'skill'


class SDR_Spell(models.Model):
    name = models.CharField(max_length=999,)
    altname = models.CharField(max_length=999,blank=True, null=True)
    school = models.CharField(max_length=999,blank=True, null=True)
    subschool = models.CharField(max_length=999,blank=True, null=True)
    descriptor = models.CharField(max_length=999,blank=True, null=True)
    spellcraft_dc = models.CharField(max_length=999,blank=True, null=True)
    level = models.CharField(max_length=999,blank=True, null=True)
    components = models.TextField(blank=True, null=True)  # This field type is a guess.
    casting_time = models.CharField(max_length=999,blank=True, null=True)
    range = models.CharField(max_length=999,blank=True, null=True)
    target = models.CharField(max_length=999,blank=True, null=True)
    area = models.CharField(max_length=999,blank=True, null=True)
    effect = models.CharField(max_length=999,blank=True, null=True)
    duration = models.CharField(max_length=999,blank=True, null=True)
    saving_throw = models.CharField(max_length=999,blank=True, null=True)
    spell_resistance = models.CharField(max_length=999,blank=True, null=True)
    short_description = models.CharField(max_length=999,blank=True, null=True)
    to_develop = models.TextField(blank=True, null=True)  # This field type is a guess.
    material_components = models.TextField(blank=True, null=True)  # This field type is a guess.
    arcane_material_components = models.CharField(max_length=999,blank=True, null=True)
    focus = models.TextField(blank=True, null=True)  # This field type is a guess.
    description = models.TextField(blank=True, null=True)  # This field type is a guess.
    xp_cost = models.TextField(blank=True, null=True)  # This field type is a guess.
    arcane_focus = models.CharField(max_length=999,blank=True, null=True)
    wizard_focus = models.CharField(max_length=999,blank=True, null=True)
    verbal_components = models.CharField(max_length=999,blank=True, null=True)
    sorcerer_focus = models.CharField(max_length=999,blank=True, null=True)
    bard_focus = models.CharField(max_length=999,blank=True, null=True)
    cleric_focus = models.CharField(max_length=999,blank=True, null=True)
    druid_focus = models.CharField(max_length=999,blank=True, null=True)
    full_text = models.TextField(blank=True, null=True)  # This field type is a guess.
    reference = models.CharField(max_length=999,blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'spell'
