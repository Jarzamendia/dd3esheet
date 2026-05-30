"""Seeds reutilizáveis para popular o banco com dados de exemplo/teste.

Cria uma conta admin e duas fichas completas (Guerreiro nível 5, Mago nível 8).
São a fonte única de dados de exemplo: a linha de comando e os testes usam as
mesmas funções, evitando divergência entre o que se vê no app e o que os testes
exercitam.

Uso:
  - Linha de comando: ``python manage.py seed``
  - Em testes::

        from character.seeds import seed_all, seed_fighter, seed_wizard, seed_admin

Os builders são idempotentes: chamá-los de novo recria as fichas de exemplo do
zero (apaga a anterior do mesmo dono/nome e cria uma nova completa), e a conta
admin tem a senha redefinida a cada chamada.

Atenção: a conta admin usa credenciais fixas e conhecidas — destina-se apenas a
ambientes locais/de teste, nunca a produção.
"""
import os

from django.conf import settings
from django.contrib.auth.models import User

from .models import (
    Ability, Character, CharacterArmor, CharacterFeat, CharacterLanguages,
    CharacterMoney, CharacterOtherItem, CharacterProtectionItem,
    CharacterShield, CharacterSkill, CharacterSpell, CharacterSpellSlot,
    CharacterWeapon,
)
from .services import _bootstrap_character_siblings
# Reusa o recálculo canônico do app para que os derivados da ficha (mods, CA,
# saves, grapple) fiquem consistentes com o que a edição via HTMX produziria.
from .views import _recalculate_stats


ADMIN_USERNAME = 'jarza'
ADMIN_PASSWORD = 'P@ssw0rd'
ADMIN_EMAIL = 'jarza@example.com'

FIGHTER_NAME = 'Borin Escudoférreo'
WIZARD_NAME = 'Maelis Vorn'


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _apply(instance, **fields):
    for name, value in fields.items():
        setattr(instance, name, value)
    instance.save()
    return instance


def _set_skill(character, name, ranks, ability_mod, misc=0):
    skill = CharacterSkill.objects.filter(Character=character, SkillName=name).first()
    if skill is None:
        skill = CharacterSkill(Character=character, SkillName=name)
    skill.Ranks = ranks
    skill.AbilityModifier = ability_mod
    skill.MiscModifier = misc
    skill.SkillModifier = ranks + ability_mod + misc
    skill.SkillIsActive = True
    skill.save()
    return skill


def _clear_children(character):
    """Apaga todas as linhas filhas (irmãos OneToOne + listas FK) de uma ficha,
    mantendo a própria linha `Character` (e portanto o seu id/URL estável)."""
    for rel in character._meta.related_objects:
        rel.related_model._base_manager.filter(**{rel.field.name: character}).delete()


def _fresh_character(user, name):
    """Reaproveita a ficha de exemplo do mesmo dono+nome (mantendo o id estável
    entre execuções do seed) e reconstrói os filhos do zero, garantindo uma
    ficha completa e determinística."""
    character, _ = Character.objects.get_or_create(User=user, Name=name)
    _clear_children(character)
    _bootstrap_character_siblings(character)
    return character


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

def seed_admin(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, email=ADMIN_EMAIL):
    """Cria (ou repara) o superusuário de exemplo. Idempotente: a senha e as
    flags de staff/superuser são redefinidas a cada chamada."""
    user, _ = User.objects.get_or_create(username=username, defaults={'email': email})
    user.email = email
    user.is_staff = True
    user.is_superuser = True
    user.set_password(password)
    user.save()
    return user


# ---------------------------------------------------------------------------
# Guerreiro nível 5
# ---------------------------------------------------------------------------

def seed_fighter(user):
    """Guerreiro humano nível 5, equipado e completo."""
    char = _fresh_character(user, FIGHTER_NAME)
    _apply(
        char,
        Class='Fighter', Level='5', Race='Human', Alignment='LG',
        Deity='Heironeous', Size='M', Age='27', Sex='Masculino',
        Heigth='1,82 m', Weight='95 kg', Eye='Castanhos', Hair='Negros',
        Skin='Bronzeada',
        Description='Veterano da guarda da cidade, troca a lança pela aventura.',
    )

    # Atributos (fonte de verdade). Mods/CA/saves/grapple vêm do recálculo.
    _apply(
        char.characterstats,
        Strength=16, Dexterity=14, Constitution=14,
        Intelligence=10, Wisdom=12, Charisma=8,
    )
    _apply(
        char.characterstatus,
        TotalHitPoints=44, Speed=20,
        ACArmorBonus=5, ACShieldBonus=2, ACNaturalArmor=0,
        ACDeflectionModifier=0, ACMiscModifier=0, ACSizeModifier=0,
        DamageReduction=0,
    )
    _apply(
        char.charactersavingthrows,
        FortitudeBaseSave=4, ReflexBaseSave=1, WillBaseSave=1,
    )
    _apply(
        char.characterattackmodifiers,
        BBA=5, SpellResistence=0,
        GrapplerBBA=5, GrapplerSizeModifier=0, GrapplerMiscModifier=0,
    )

    _recalculate_stats(char)

    _set_skill(char, 'Escalar', ranks=8, ability_mod=3)
    _set_skill(char, 'Saltar', ranks=8, ability_mod=3)
    _set_skill(char, 'Intimidar', ranks=8, ability_mod=-1)
    _set_skill(char, 'Cavalgar', ranks=4, ability_mod=2)

    CharacterWeapon.objects.create(
        Character=char, Name='Espada Longa', Attack='Espada Longa',
        AttackBonus='+9', Damage='1d8+5', Critical='19-20/x2', Range='-',
        Type='Corte', Notes='Foco e Especialização em Arma',
    )
    CharacterWeapon.objects.create(
        Character=char, Name='Arco Longo Composto', Attack='Arco Longo Composto',
        AttackBonus='+7', Damage='1d8+3', Critical='x3', Range='110 ft',
        Type='Perfuração', Notes='À distância', AmmunitionName='Flechas',
        AmmunitionCount='40',
    )

    CharacterArmor.objects.create(
        Character=char, Name='Cota de Malha', Type='Média', ACBonus='+5',
        MaxDex='+2', CheckPenalty='-5', SpellFailure='30%', Speed='6 m',
        Weigth='40 lb', SpecialProperties='',
    )
    CharacterShield.objects.create(
        Character=char, Name='Escudo Pesado de Aço', ACBonus='+2',
        Weigth='15 lb', CheckPenalty='-2', SpellFailure='15%',
    )
    CharacterProtectionItem.objects.create(
        Character=char, Name='Amuleto de Armadura Natural +1', ACBonus='+1',
        Weigth='-', SpecialProperties='Bônus de armadura natural',
    )

    for name in ['Ataque Poderoso', 'Trespassar', 'Foco em Arma (Espada Longa)',
                 'Especialização em Arma (Espada Longa)', 'Iniciativa Aprimorada',
                 'Esquiva']:
        CharacterFeat.objects.create(Character=char, Name=name, Page='PHB')

    Ability.objects.create(Character=char, Name='Talentos de Guerreiro (bônus)', Page='PHB')

    for name, page, weight in [
        ('Mochila', 'PHB', '2 lb'),
        ('Saco de Dormir', 'PHB', '5 lb'),
        ('Corda de Cânhamo (15 m)', 'PHB', '10 lb'),
        ('Rações de Viagem (5 dias)', 'PHB', '5 lb'),
        ('Tocha (x5)', 'PHB', '5 lb'),
    ]:
        CharacterOtherItem.objects.create(Character=char, Name=name, Page=page, Weigth=weight)

    _apply(char.charactermoney, GP=200, SP=50, CP=0, PP=0)
    CharacterLanguages.objects.create(Character=char, Value='Comum')

    return char


# ---------------------------------------------------------------------------
# Mago nível 8
# ---------------------------------------------------------------------------

_WIZARD_PREPARED_SLOTS = [
    (0, 'Detectar Magia', 'normal', False),
    (0, 'Ler Magia', 'normal', False),
    (0, 'Luz', 'normal', False),
    (0, 'Raio de Gelo', 'normal', True),
    (1, 'Mísseis Mágicos', 'normal', True),
    (1, 'Armadura Arcana', 'normal', True),
    (1, 'Escudo Arcano', 'normal', False),
    (1, 'Identificação', 'normal', False),
    (1, 'Mãos Flamejantes', 'specialist', False),
    (2, 'Flecha Ácida de Melf', 'normal', False),
    (2, 'Invisibilidade', 'normal', False),
    (2, 'Toque Chocante em Área', 'normal', False),
    (2, 'Explosão Sônica', 'specialist', False),
    (3, 'Bola de Fogo', 'normal', True),
    (3, 'Relâmpago', 'normal', False),
    (3, 'Voo', 'normal', False),
    (3, 'Tempestade Sonora', 'specialist', False),
    (4, 'Tempestade de Gelo', 'normal', False),
    (4, 'Porta Dimensional', 'normal', False),
    (4, 'Explosão Flamejante', 'specialist', False),
]

_WIZARD_SPELLBOOK = [
    ('Detectar Magia', 0), ('Ler Magia', 0), ('Luz', 0), ('Raio de Gelo', 0),
    ('Prestidigitação', 0),
    ('Mísseis Mágicos', 1), ('Armadura Arcana', 1), ('Escudo Arcano', 1),
    ('Identificação', 1), ('Mãos Flamejantes', 1),
    ('Flecha Ácida de Melf', 2), ('Invisibilidade', 2), ('Explosão Sônica', 2),
    ('Bola de Fogo', 3), ('Relâmpago', 3), ('Voo', 3),
    ('Tempestade de Gelo', 4), ('Porta Dimensional', 4),
]


def seed_wizard(user):
    """Mago elfo nível 8, especialista em Evocação, com livro de magias e slots."""
    char = _fresh_character(user, WIZARD_NAME)
    _apply(
        char,
        Class='Wizard', Level='8', Race='Elf', Alignment='N',
        Deity='Boccob', Size='M', Age='124', Sex='Feminino',
        Heigth='1,68 m', Weight='52 kg', Eye='Âmbar', Hair='Prateados',
        Skin='Clara',
        Description='Especialista em Evocação obcecada por relíquias arcanas.',
    )

    _apply(
        char.characterstats,
        Strength=8, Dexterity=14, Constitution=12,
        Intelligence=18, Wisdom=12, Charisma=10,
    )
    _apply(
        char.characterstatus,
        TotalHitPoints=30, Speed=30,
        ACArmorBonus=0, ACShieldBonus=0, ACNaturalArmor=0,
        ACDeflectionModifier=1, ACMiscModifier=0, ACSizeModifier=0,
        DamageReduction=0,
    )
    _apply(
        char.charactersavingthrows,
        FortitudeBaseSave=2, ReflexBaseSave=2, WillBaseSave=6,
    )
    _apply(
        char.characterattackmodifiers,
        BBA=4, SpellResistence=0,
        GrapplerBBA=4, GrapplerSizeModifier=0, GrapplerMiscModifier=0,
    )

    _recalculate_stats(char)

    _set_skill(char, 'Identificar Magia', ranks=11, ability_mod=4)
    _set_skill(char, 'Concentracao', ranks=11, ability_mod=1)
    _set_skill(char, 'Conhecimento', ranks=11, ability_mod=4)
    _set_skill(char, 'Decifrar Escrita', ranks=8, ability_mod=4)
    _set_skill(char, 'Observar', ranks=4, ability_mod=1, misc=2)

    CharacterWeapon.objects.create(
        Character=char, Name='Bordão', Attack='Bordão', AttackBonus='+3',
        Damage='1d6-1', Critical='x2', Range='-', Type='Concussão',
        Notes='Corpo a corpo',
    )
    CharacterWeapon.objects.create(
        Character=char, Name='Adaga', Attack='Adaga', AttackBonus='+6',
        Damage='1d4-1', Critical='19-20/x2', Range='3 m', Type='Perfuração',
        Notes='Pode ser arremessada',
    )

    CharacterProtectionItem.objects.create(
        Character=char, Name='Anel de Proteção +1', ACBonus='+1', Weigth='-',
        SpecialProperties='Bônus de deflexão',
    )
    CharacterProtectionItem.objects.create(
        Character=char, Name='Braceletes de Armadura +4', ACBonus='+4',
        Weigth='1 lb', SpecialProperties='Bônus de armadura (não cumulativo com armadura física)',
    )

    for name in ['Inscrever Pergaminho (bônus)', 'Foco em Magia (Evocação)',
                 'Foco em Magia Aprimorado (Evocação)', 'Iniciativa Aprimorada',
                 'Conjuração em Combate', 'Potencializar Magia (bônus de mago)']:
        CharacterFeat.objects.create(Character=char, Name=name, Page='PHB')

    for name in ['Visão na Penumbra (elfo)', 'Imunidade a sono mágico (elfo)',
                 'Familiar', 'Especialista em Evocação']:
        Ability.objects.create(Character=char, Name=name, Page='PHB')

    for name, page, weight in [
        ('Livro de Magias', 'PHB', '3 lb'),
        ('Bolsa de Componentes', 'PHB', '2 lb'),
        ('Tinta e Pena', 'PHB', '-'),
        ('Poção de Cura Moderada (x2)', 'DMG', '-'),
    ]:
        CharacterOtherItem.objects.create(Character=char, Name=name, Page=page, Weigth=weight)

    _apply(char.charactermoney, GP=600, SP=0, CP=0, PP=5)

    for value in ['Comum', 'Élfico', 'Dracônico', 'Silvestre']:
        CharacterLanguages.objects.create(Character=char, Value=value)

    _apply(
        char.characterspellcasting,
        CasterClass='Wizard', CastingAbility='Inteligência (INT)',
        CastingMode='prepared_book', SpecializedSchool='Evocation',
        SpontaneousConversion='',
    )

    for level, name, slot_type, is_used in _WIZARD_PREPARED_SLOTS:
        CharacterSpellSlot.objects.create(
            Character=char, Level=level, SlotType=slot_type,
            PreparedSpellName=name, IsUsed=is_used,
        )

    for name, level in _WIZARD_SPELLBOOK:
        CharacterSpell.objects.create(Character=char, Name=name, Level=level, Page='PHB')

    return char


# ---------------------------------------------------------------------------
# Orquestrador
# ---------------------------------------------------------------------------

def seed_all():
    """Cria a conta admin e as duas fichas de exemplo (de posse do admin).

    Em produção (DEBUG=False), a conta admin só é criada se SEED_ADMIN=true
    estiver no ambiente — evitar criação acidental de credenciais fracas em
    servidores públicos.
    """
    # Django's test runner sets settings.DEBUG=False regardless of env.
    # Check the raw env var so the guard still works correctly in dev/test.
    _debug_env = os.environ.get('DEBUG', '').lower() in ('1', 'true', 'yes')
    _seed_admin_allowed = _debug_env or os.environ.get('SEED_ADMIN', '').lower() in ('1', 'true', 'yes')
    if _seed_admin_allowed:
        admin = seed_admin()
    else:
        admin = User.objects.filter(username=ADMIN_USERNAME).first()
        if admin is None:
            raise RuntimeError(
                "seed_all() em produção requer SEED_ADMIN=true no ambiente "
                "ou um admin preexistente. Nunca rode seed com credenciais "
                "fixas em produção sem confirmação explícita."
            )
    fighter = seed_fighter(admin)
    wizard = seed_wizard(admin)
    return {'admin': admin, 'fighter': fighter, 'wizard': wizard}
