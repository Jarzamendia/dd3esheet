from django.db import models
from django.contrib.auth.models import User

class Character(models.Model):
    Description = models.TextField(null=True, blank=True)
    Name        = models.CharField(max_length=200, null=True, blank=True)
    Class       = models.CharField(max_length=200, null=True, blank=True)
    Level       = models.CharField(max_length=200, null=True, blank=True)
    Race        = models.CharField(max_length=200, null=True, blank=True)
    Alignment   = models.CharField(max_length=200, null=True, blank=True)
    Deity       = models.CharField(max_length=200, null=True, blank=True)
    Size        = models.CharField(max_length=200, null=True, blank=True)
    Age         = models.CharField(max_length=200, null=True, blank=True)
    Sex         = models.CharField(max_length=200, null=True, blank=True)
    Heigth      = models.CharField(max_length=200, null=True, blank=True)
    Weight      = models.CharField(max_length=200, null=True, blank=True)
    Eye         = models.CharField(max_length=200, null=True, blank=True)
    Hair        = models.CharField(max_length=200, null=True, blank=True)
    Skin        = models.CharField(max_length=200, null=True, blank=True)

    User        = models.ForeignKey(User, on_delete=models.CASCADE)
    UpdatedAt   = models.DateTimeField(auto_now=True)
    CreatedAt   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-UpdatedAt', 'CreatedAt']

    def __str__(self):
        return self.Name

class CharacterStats(models.Model):
    Character           = models.OneToOneField(Character, on_delete=models.CASCADE, primary_key=True)

    Strength            = models.IntegerField(default=0, null=True, blank=True)
    Dexterity           = models.IntegerField(default=0, null=True, blank=True)
    Constitution        = models.IntegerField(default=0, null=True, blank=True)
    Intelligence        = models.IntegerField(default=0, null=True, blank=True)
    Wisdom              = models.IntegerField(default=0, null=True, blank=True)
    Charisma            = models.IntegerField(default=0, null=True, blank=True)

    StrengthStatMod     = models.IntegerField(default=0, null=True, blank=True)
    DexterityStatMod    = models.IntegerField(default=0, null=True, blank=True)
    ConstitutionStatMod = models.IntegerField(default=0, null=True, blank=True)
    IntelligenceStatMod = models.IntegerField(default=0, null=True, blank=True)
    WisdomStatMod       = models.IntegerField(default=0, null=True, blank=True)
    CharismaStatMod     = models.IntegerField(default=0, null=True, blank=True)

    StrengthTemp        = models.IntegerField(default=0, null=True, blank=True)
    DexterityTemp       = models.IntegerField(default=0, null=True, blank=True)
    ConstitutionTemp    = models.IntegerField(default=0, null=True, blank=True)
    IntelligenceTemp    = models.IntegerField(default=0, null=True, blank=True)
    WisdomTemp          = models.IntegerField(default=0, null=True, blank=True)
    CharismaTemp        = models.IntegerField(default=0, null=True, blank=True)

    StrengthModTemp     = models.IntegerField(default=0, null=True, blank=True)
    DexterityModTemp    = models.IntegerField(default=0, null=True, blank=True)
    ConstitutionModTemp = models.IntegerField(default=0, null=True, blank=True)
    IntelligenceModTemp = models.IntegerField(default=0, null=True, blank=True)
    WisdomModTemp       = models.IntegerField(default=0, null=True, blank=True)
    CharismaModTemp     = models.IntegerField(default=0, null=True, blank=True)

class CharacterStatus(models.Model):
    Character            = models.OneToOneField(Character, on_delete=models.CASCADE, primary_key=True)

    TotalHitPoints       = models.IntegerField(default=0, null=True, blank=True)
    NonLethalDamager     = models.IntegerField(default=0, null=True, blank=True)
    Speed                = models.IntegerField(default=0, null=True, blank=True)
    ACTotal              = models.IntegerField(default=0, null=True, blank=True)
    ACArmorBonus         = models.IntegerField(default=0, null=True, blank=True)
    ACShieldBonus        = models.IntegerField(default=0, null=True, blank=True)
    ACDexModifier        = models.IntegerField(default=0, null=True, blank=True)
    ACSizeModifier       = models.IntegerField(default=0, null=True, blank=True)
    ACNaturalArmor       = models.IntegerField(default=0, null=True, blank=True)
    ACDeflectionModifier = models.IntegerField(default=0, null=True, blank=True)
    ACMiscModifier       = models.IntegerField(default=0, null=True, blank=True)
    DamageReduction      = models.IntegerField(default=0, null=True, blank=True)
    ACTouch              = models.IntegerField(default=0, null=True, blank=True)
    ACFlatFooterd        = models.IntegerField(default=0, null=True, blank=True)
    Initiative           = models.IntegerField(default=0, null=True, blank=True)

class CharacterSavingThrows(models.Model):
    Character = models.OneToOneField(Character, on_delete=models.CASCADE, primary_key=True)

    TotalFortitude                = models.IntegerField(default=0, null=True, blank=True)
    FortitudeBaseSave             = models.IntegerField(default=0, null=True, blank=True)
    FortitudeAbilityModifier      = models.IntegerField(default=0, null=True, blank=True)
    FortitudeMagicModifier        = models.IntegerField(default=0, null=True, blank=True)
    FortitudeMiscModifier         = models.IntegerField(default=0, null=True, blank=True)
    FortitudeTemporaryModifier    = models.IntegerField(default=0, null=True, blank=True)
    FortitudeConditionalModifier  = models.IntegerField(default=0, null=True, blank=True)
    TotalReflex                   = models.IntegerField(default=0, null=True, blank=True)
    ReflexBaseSave                = models.IntegerField(default=0, null=True, blank=True)
    ReflexAbilityModifier         = models.IntegerField(default=0, null=True, blank=True)
    ReflexMagicModifier           = models.IntegerField(default=0, null=True, blank=True)
    ReflexMiscModifier            = models.IntegerField(default=0, null=True, blank=True)
    ReflexTemporaryModifier       = models.IntegerField(default=0, null=True, blank=True)
    ReflexConditionalModifier     = models.IntegerField(default=0, null=True, blank=True)
    TotalWill                     = models.IntegerField(default=0, null=True, blank=True)
    WillBaseSave                  = models.IntegerField(default=0, null=True, blank=True)
    WillAbilityModifier           = models.IntegerField(default=0, null=True, blank=True)
    WillMagicModifier             = models.IntegerField(default=0, null=True, blank=True)
    WillMiscModifier              = models.IntegerField(default=0, null=True, blank=True)
    WillTemporaryModifier         = models.IntegerField(default=0, null=True, blank=True)
    WillConditionalModifier       = models.IntegerField(default=0, null=True, blank=True)

class CharacterAttackModifiers(models.Model):
    Character = models.OneToOneField(Character, on_delete=models.CASCADE, primary_key=True)

    BBA                  = models.IntegerField(default=0, null=True, blank=True)
    SpellResistence      = models.IntegerField(default=0, null=True, blank=True)
    TotalGrappler        = models.IntegerField(default=0, null=True, blank=True)
    GrapplerBBA          = models.IntegerField(default=0, null=True, blank=True)
    GrapplerStrModifier  = models.IntegerField(default=0, null=True, blank=True)
    GrapplerSizeModifier = models.IntegerField(default=0, null=True, blank=True)
    GrapplerMiscModifier = models.IntegerField(default=0, null=True, blank=True)

class CharacterSkillGraduation(models.Model):
    Character = models.OneToOneField(Character, on_delete=models.CASCADE, primary_key=True)

    MaxGraduation           = models.IntegerField(default=0, null=True, blank=True)
    OtherClassMaxGraduation = models.IntegerField(default=0, null=True, blank=True)

class CharacterSkill(models.Model):
    SkillIsActive = models.BinaryField(default=0, null=True, blank=True)
    SkillName       = models.CharField(max_length=200, null=True, blank=True)
    SkillAbility    = models.IntegerField(default=0, null=True, blank=True)
    SkillModifier   = models.IntegerField(default=0, null=True, blank=True)
    AbilityModifier = models.IntegerField(default=0, null=True, blank=True)
    Ranks           = models.IntegerField(default=0, null=True, blank=True)
    MiscModifier    = models.IntegerField(default=0, null=True, blank=True)

    def __str__(self):
        return self.SkillName

class CharacterWeapon(models.Model):
    Character       = models.ForeignKey(Character, on_delete=models.CASCADE)

    Name            = models.CharField(max_length=200, null=True, blank=True)
    Attack          = models.CharField(max_length=200, null=True, blank=True)
    AttackBonus     = models.CharField(max_length=200, null=True, blank=True)
    Damage          = models.CharField(max_length=200, null=True, blank=True)
    Critical        = models.CharField(max_length=200, null=True, blank=True)
    Range           = models.CharField(max_length=200, null=True, blank=True)
    Type            = models.CharField(max_length=200, null=True, blank=True)
    Notes           = models.CharField(max_length=200, null=True, blank=True)
    AmmunitionName  = models.CharField(max_length=200, null=True, blank=True)
    AmmunitionCount = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.Name

class CharacterArmor(models.Model):
    Character         = models.ForeignKey(Character, on_delete=models.CASCADE)

    Name              = models.CharField(max_length=200, null=True, blank=True)
    Type              = models.CharField(max_length=200, null=True, blank=True)
    ACBonus           = models.CharField(max_length=200, null=True, blank=True)
    MaxDex            = models.CharField(max_length=200, null=True, blank=True)
    CheckPenalty      = models.CharField(max_length=200, null=True, blank=True)
    SpellFailure      = models.CharField(max_length=200, null=True, blank=True)
    Speed             = models.CharField(max_length=200, null=True, blank=True)
    Weigth            = models.CharField(max_length=200, null=True, blank=True)
    SpecialProperties = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.Name
    
class CharacterShield(models.Model):
    Character = models.ForeignKey(Character, on_delete=models.CASCADE)

    Name              = models.CharField(max_length=200, null=True, blank=True)
    ACBonus           = models.CharField(max_length=200, null=True, blank=True)
    Weigth            = models.CharField(max_length=200, null=True, blank=True)
    CheckPenalty      = models.CharField(max_length=200, null=True, blank=True)
    SpellFailure      = models.CharField(max_length=200, null=True, blank=True)
    SpecialProperties = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.Name

class CharacterProtectionItem(models.Model):
    Character         = models.ForeignKey(Character, on_delete=models.CASCADE)

    Name              = models.CharField(max_length=200, null=True, blank=True)
    ACBonus           = models.CharField(max_length=200, null=True, blank=True)
    Weigth            = models.CharField(max_length=200, null=True, blank=True)
    SpecialProperties = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.Name

class CharacterOtherItem(models.Model):
    Character = models.ForeignKey(Character, on_delete=models.CASCADE)

    Name      = models.CharField(max_length=200, null=True, blank=True)
    Page      = models.CharField(max_length=200, null=True, blank=True)
    Weigth    = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.Name

class CharacterOtherItemObs(models.Model):
    Character      = models.OneToOneField(Character, on_delete=models.CASCADE, primary_key=True)

    LightLoad      = models.IntegerField(default=0, null=True, blank=True)
    MediumLoad     = models.IntegerField(default=0, null=True, blank=True)
    HeavyLoad      = models.IntegerField(default=0, null=True, blank=True)
    LiftOverHEad   = models.IntegerField(default=0, null=True, blank=True)
    LiftOffGround  = models.IntegerField(default=0, null=True, blank=True)
    PushOrDrag     = models.IntegerField(default=0, null=True, blank=True)
    TotalWCarried  = models.IntegerField(default=0, null=True, blank=True)

class CharacterMoney(models.Model):
    Character = models.OneToOneField(Character, on_delete=models.CASCADE, primary_key=True)
    
    CP        = models.IntegerField(default=0, null=True, blank=True)
    SP        = models.IntegerField(default=0, null=True, blank=True)
    GP        = models.IntegerField(default=0, null=True, blank=True)
    PP        = models.IntegerField(default=0, null=True, blank=True)

class CharacterFeat(models.Model):
    Character = models.ForeignKey(Character, on_delete=models.CASCADE)

    Name      = models.CharField(max_length=200, null=True, blank=True)
    Page      = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.Name

class Ability(models.Model):
    Character = models.ForeignKey(Character, on_delete=models.CASCADE)

    Name      = models.CharField(max_length=200, null=True, blank=True)
    Page      = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.Name

class CharacterSpell(models.Model):
    Character = models.ForeignKey(Character, on_delete=models.CASCADE)

    Name      = models.CharField(max_length=200, null=True, blank=True)
    Page      = models.CharField(max_length=200, null=True, blank=True)
    Level     = models.IntegerField(default=0, null=True, blank=True)

    def __str__(self):
        return self.Name

class CharacterSpellSave(models.Model):
    Character = models.OneToOneField(Character, on_delete=models.CASCADE, primary_key=True)
    Value     = models.IntegerField(default=0, null=True, blank=True)

class CharacterArcaneSpellFailCheck(models.Model):
    Character = models.OneToOneField(Character, on_delete=models.CASCADE, primary_key=True)
    Value     = models.IntegerField(default=0, null=True, blank=True)

class CharacterMagicConditionalModifiers(models.Model):
    Character = models.OneToOneField(Character, on_delete=models.CASCADE, primary_key=True)
    Value     = models.TextField(null=True, blank=True)

class CharacterMagicDayUse(models.Model):
    Character    = models.ForeignKey(Character, on_delete=models.CASCADE)

    Level        = models.IntegerField(default=0, null=True, blank=True)
    SpellsKnown  = models.IntegerField(default=0, null=True, blank=True)
    SpellSaveDC  = models.IntegerField(default=0, null=True, blank=True)
    SpellsPerDay = models.IntegerField(default=0, null=True, blank=True)
    BonusSpells  = models.IntegerField(default=0, null=True, blank=True)

class CharacterLanguages(models.Model):
    Character = models.ForeignKey(Character, on_delete=models.CASCADE)
    Value     = models.CharField(max_length=200, null=True, blank=True)
