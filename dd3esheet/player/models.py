from django.db import models

# Create your models here.
class PlayerDescription(models.Model):
    Name       = models.CharField(max_length=200)
    PlayerName = models.CharField(max_length=200)
    Class      = models.CharField(max_length=200)
    Level      = models.CharField(max_length=200)
    Race       = models.CharField(max_length=200)
    Alignment  = models.CharField(max_length=200)
    Deity      = models.CharField(max_length=200)
    Size       = models.CharField(max_length=200)
    Age        = models.CharField(max_length=200)
    Sex        = models.CharField(max_length=200)
    Heigth     = models.CharField(max_length=200)
    Weight     = models.CharField(max_length=200)
    Eye        = models.CharField(max_length=200)
    Hair       = models.CharField(max_length=200)
    Skin       = models.CharField(max_length=200)

class PlayerStats(models.Model):
    Strength     = models.IntegerField(default=0)
    Dexterity    = models.IntegerField(default=0)
    Constitution = models.IntegerField(default=0)
    Intelligence = models.IntegerField(default=0)
    Wisdom       = models.IntegerField(default=0)
    Charisma     = models.IntegerField(default=0)

class PlayerStatus(models.Model):
    TotalHitPoints       = models.IntegerField(default=0)
    NonLethalDamager     = models.IntegerField(default=0)
    Speed                = models.IntegerField(default=0)
    ACTotal              = models.IntegerField(default=0)
    ACArmorBonus         = models.IntegerField(default=0)
    ACShieldBonus        = models.IntegerField(default=0)
    ACDexModifier        = models.IntegerField(default=0)
    ACSizeModifier       = models.IntegerField(default=0)
    ACNaturalArmor       = models.IntegerField(default=0)
    ACDeflectionModifier = models.IntegerField(default=0)
    ACMiscModifier       = models.IntegerField(default=0)
    DamageReduction      = models.IntegerField(default=0)
    ACTouch              = models.IntegerField(default=0)
    ACFlatFooterd        = models.IntegerField(default=0)
    Initiative           = models.IntegerField(default=0)

class PlayerSavingThrows(models.Model):
    TotalFortitude                = models.IntegerField(default=0)
    FortitudeBaseSave             = models.IntegerField(default=0)
    FortitudeAbilityModifier      = models.IntegerField(default=0)
    FortitudeMagicModifier        = models.IntegerField(default=0)
    FortitudeMiscModifier         = models.IntegerField(default=0)
    FortitudeTemporaryModifier    = models.IntegerField(default=0)
    FortitudeConditionalModifier  = models.IntegerField(default=0)
    TotalReflex                   = models.IntegerField(default=0)
    ReflexBaseSave                = models.IntegerField(default=0)
    ReflexAbilityModifier         = models.IntegerField(default=0)
    ReflexMagicModifier           = models.IntegerField(default=0)
    ReflexMiscModifier            = models.IntegerField(default=0)
    ReflexTemporaryModifier       = models.IntegerField(default=0)
    ReflexConditionalModifier     = models.IntegerField(default=0)
    TotalWill                     = models.IntegerField(default=0)
    WillBaseSave                  = models.IntegerField(default=0)
    WillAbilityModifier           = models.IntegerField(default=0)
    WillMagicModifier             = models.IntegerField(default=0)
    WillMiscModifier              = models.IntegerField(default=0)
    WillTemporaryModifier         = models.IntegerField(default=0)
    WillConditionalModifier       = models.IntegerField(default=0)

class PlayerAttackModifiers(models.Model):
    BBA                  = models.IntegerField(default=0)
    SpellResistence      = models.IntegerField(default=0)
    TotalGrappler        = models.IntegerField(default=0)
    GrapplerBBA          = models.IntegerField(default=0)
    GrapplerStrModifier  = models.IntegerField(default=0)
    GrapplerSizeModifier = models.IntegerField(default=0)
    GrapplerMiscModifier = models.IntegerField(default=0)

class PlayerWeapon(models.Model):
    Attack          = models.CharField(max_length=200)
    AttackBonus     = models.CharField(max_length=200)
    Damage          = models.CharField(max_length=200)
    Critical        = models.CharField(max_length=200)
    Range           = models.CharField(max_length=200)
    Type            = models.CharField(max_length=200)
    Notes           = models.CharField(max_length=200)
    AmmunitionName  = models.CharField(max_length=200)
    AmmunitionCount = models.CharField(max_length=200)

class PlayerSkillGraduation(models.Model):
    MaxGraduation           = models.IntegerField(default=0)
    OtherClassMaxGraduation = models.IntegerField(default=0)

class PlayerSkill(models.Model):
    SkillName       = models.CharField(max_length=200)
    SkillAbility    = models.IntegerField(default=0)
    SkillModifier   = models.IntegerField(default=0)
    AbilityModifier = models.IntegerField(default=0)
    Ranks           = models.IntegerField(default=0)
    MiscModifier    = models.IntegerField(default=0)

class PlayerSkillList(models.Model):
    Appraise = models.IntegerField(default=0)
    Balance = models.IntegerField(default=0)
    Bluff = models.IntegerField(default=0)
    Climb = models.IntegerField(default=0)
    Concentration = models.IntegerField(default=0)
    Craft = models.IntegerField(default=0)
    DecipherScript = models.IntegerField(default=0)
    Diplomacy = models.IntegerField(default=0)
    DisableDevice = models.IntegerField(default=0)
    Disguise = models.IntegerField(default=0)
    EscapeArtist = models.IntegerField(default=0)
    Forgery = models.IntegerField(default=0)
    GatherInformation = models.IntegerField(default=0)
    HandleAnimal = models.IntegerField(default=0)
    Heal = models.IntegerField(default=0)
    Hide = models.IntegerField(default=0)
    Intimidate = models.IntegerField(default=0)
    Jump  = models.IntegerField(default=0)
    Knowledge = models.IntegerField(default=0)
    Listen = models.IntegerField(default=0)
    MoveSilently = models.IntegerField(default=0)
    OpenLock = models.IntegerField(default=0)
    Perform = models.IntegerField(default=0)
    Profession = models.IntegerField(default=0)
    Ride = models.IntegerField(default=0)
    Search = models.IntegerField(default=0)
    SenseMotive = models.IntegerField(default=0)
    SleightofHand = models.IntegerField(default=0)
    Spellcraft = models.IntegerField(default=0)
    Spot = models.IntegerField(default=0)
    Survival = models.IntegerField(default=0)
    Swim = models.IntegerField(default=0)
    Tumble = models.IntegerField(default=0)
    UseMagicDevice = models.IntegerField(default=0)
    UseRope = models.IntegerField(default=0)

class PlayerShieldOrProtection(models.Model):
    Appraise = models.IntegerField(default=0)

class PlayerProtectionItem(models.Model):
    Appraise = models.IntegerField(default=0)

class PlayerOtherItem(models.Model):
    Appraise = models.IntegerField(default=0)

class PlayerFeat(models.Model):
    Appraise = models.IntegerField(default=0)

class PlayerTalent(models.Model):
    Appraise = models.IntegerField(default=0)

class PlayerMagic(models.Model):
    Appraise = models.IntegerField(default=0)

class PlayerMagicResistenceCheck(models.Model):
    Appraise = models.IntegerField(default=0)

class PlayerArcaneFailCheck(models.Model):
    Appraise = models.IntegerField(default=0)

class MagicConditionalModifiers(models.Model):
    Appraise = models.IntegerField(default=0)

class MagicDayUse(models.Model):
    Appraise = models.IntegerField(default=0)

class Languages(models.Model):
    Appraise = models.IntegerField(default=0)

class Player(models.Model):
    PlayerDescription = models.ForeignKey(PlayerDescription, on_delete=models.CASCADE)
    PlayerStats = models.ForeignKey(PlayerStats, on_delete=models.CASCADE)