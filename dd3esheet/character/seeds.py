"""Seeds reutilizáveis para popular o banco com dados de exemplo/teste.

Cria uma conta admin e fichas completas (Guerreiro, Mago, Druida e Ranger).
São a fonte única de dados de exemplo: a linha de comando e os testes usam as
mesmas funções, evitando divergência entre o que se vê no app e o que os testes
exercitam.

Uso:
  - Linha de comando: ``python manage.py seed``
  - Em testes::

        from character.seeds import seed_all, seed_fighter, seed_wizard, seed_druid, seed_ranger, seed_admin

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
    Ability, Character, CharacterActiveEffect, CharacterArmor, CharacterBuff,
    CharacterCompanion, CharacterContact, CharacterContract, CharacterDailyResource,
    CharacterFaction, CharacterFeat, CharacterLanguages, CharacterMoney,
    CharacterOtherItem, CharacterProtectionItem, CharacterShield, CharacterSkill,
    CharacterSpell, CharacterSpellSlot, CharacterSummon, CharacterWeapon,
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
DRUID_NAME = 'Thalara Verdefolha'
RANGER_NAME = 'Kael Rastrolongo'


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


def _set_progress(character, campaign, xp):
    return _apply(character.characterprogress, CampaignName=campaign, ExperiencePoints=xp)


def _add_resource(character, name, source, maximum, used=0, refresh='Diário', checks=''):
    remaining = max(int(maximum or 0) - int(used or 0), 0)
    return CharacterDailyResource.objects.create(
        Character=character, Name=name, Source=source, Maximum=maximum, Used=used,
        Remaining=remaining, Refresh=refresh, Checks=checks,
    )


def _add_active_effect(character, name, source, modifier, rounds, notes=''):
    return CharacterActiveEffect.objects.create(
        Character=character, Name=name, Source=source, Modifier=modifier,
        RoundsRemaining=rounds, Notes=notes,
    )


def _set_daily_notes(character, Preparation='', Spent=''):
    return _apply(character.characterdailynotes, Preparation=Preparation, Spent=Spent)


def _add_reputation(character, contact, faction, contract):
    CharacterContact.objects.create(Character=character, **contact)
    CharacterFaction.objects.create(Character=character, **faction)
    CharacterContract.objects.create(Character=character, **contract)


def _add_buff(character, **fields):
    defaults = {'IsActive': False}
    defaults.update(fields)
    return CharacterBuff.objects.create(Character=character, **defaults)


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

    _set_progress(char, 'Fronteira de Elsir', 10500)
    _add_resource(char, 'Surto de Acao', 'Regra da mesa', 1, used=0, refresh='Encontro')
    _add_active_effect(char, 'Postura defensiva', 'Tatica', '+2 CA contra o alvo marcado', 3)
    _add_reputation(
        char,
        {
            'Name': 'Capita Alandra', 'Location': 'Vau de Drellin',
            'Relationship': 'Aliada', 'Favor': 'Pode pedir escolta',
            'Notes': 'Serviu com Borin na milicia local.',
        },
        {
            'Name': 'Guarda da Ponte', 'Reputation': 'Respeitado',
            'Influence': 'Media', 'Risk': 'Baixo',
            'Notes': 'Veteranos confiam em sua palavra.',
        },
        {
            'Title': 'Escoltar o comboio de mantimentos', 'Party': 'Guarda da Ponte',
            'Reward': '300 po', 'Deadline': 'Proxima lua cheia',
            'Status': 'Aberto', 'Notes': 'Passar pela estrada velha.',
        },
    )

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

    _set_progress(char, 'Fronteira de Elsir', 28000)
    _add_resource(char, 'Perola de Poder I', 'Item magico', 1, used=1, refresh='Diario')
    _add_active_effect(char, 'Armadura Arcana', 'Magia', '+4 armadura', 480, 'Ja contabilizar manualmente se ativa.')
    _add_buff(char, Name='Raposa Astuta', IntelligenceBonus=4, Notes='+4 INT por 8 minutos')
    _add_reputation(
        char,
        {
            'Name': 'Sibila de Brindol', 'Location': 'Biblioteca da Torre',
            'Relationship': 'Mentora', 'Favor': 'Acesso a grimorios',
            'Notes': 'Cobra relatorios sobre artefatos encontrados.',
        },
        {
            'Name': 'Circulo dos Oito Sinais', 'Reputation': 'Membro',
            'Influence': 'Alta', 'Risk': 'Medio',
            'Notes': 'Rivais querem copiar o grimorio de Maelis.',
        },
        {
            'Title': 'Catalogar o obelisco rachado', 'Party': 'Circulo dos Oito Sinais',
            'Reward': 'Pergaminhos raros', 'Deadline': 'Antes do equinocio',
            'Status': 'Em andamento', 'Notes': 'Levar amostras de runas.',
        },
    )

    return char


# ---------------------------------------------------------------------------
# Druida nivel 9
# ---------------------------------------------------------------------------

_DRUID_PREPARED_SLOTS = [
    (0, 'Criar Agua', 'normal', False),
    (0, 'Detectar Magia', 'normal', False),
    (0, 'Orientacao', 'normal', False),
    (1, 'Enredar', 'normal', False),
    (1, 'Presa Magica', 'normal', True),
    (1, 'Curar Ferimentos Leves', 'normal', False),
    (2, 'Esfera Flamejante', 'normal', False),
    (2, 'Forca do Touro', 'normal', False),
    (3, 'Invocar Aliado da Natureza III', 'normal', True),
    (3, 'Dissipar Magia', 'normal', False),
    (4, 'Pele Rochosa', 'normal', False),
    (4, 'Tempestade de Gelo', 'normal', False),
    (5, 'Invocar Aliado da Natureza V', 'normal', False),
]


def seed_druid(user):
    """Druida humana nivel 9 com companheiro animal, invocacoes e recursos."""
    char = _fresh_character(user, DRUID_NAME)
    _apply(
        char,
        Class='Druid', Level='9', Race='Human', Alignment='N',
        Deity='Obad-Hai', Size='M', Age='34', Sex='Feminino',
        Heigth='1,70 m', Weight='66 kg', Eye='Verdes', Hair='Castanhos',
        Skin='Queimada de sol',
        Description='Guardia dos bosques que negocia com aldeias e espiritos.',
    )
    _apply(
        char.characterstats,
        Strength=12, Dexterity=14, Constitution=14,
        Intelligence=12, Wisdom=18, Charisma=10,
    )
    _apply(
        char.characterstatus,
        TotalHitPoints=61, Speed=30, ACArmorBonus=3, ACShieldBonus=2,
        ACNaturalArmor=0, ACDeflectionModifier=1, ACMiscModifier=0,
        ACSizeModifier=0, DamageReduction=0,
    )
    _apply(
        char.charactersavingthrows,
        FortitudeBaseSave=6, ReflexBaseSave=3, WillBaseSave=6,
    )
    _apply(
        char.characterattackmodifiers,
        BBA=6, SpellResistence=0, GrapplerBBA=6,
        GrapplerSizeModifier=0, GrapplerMiscModifier=0,
    )

    _recalculate_stats(char)

    _set_skill(char, 'Concentracao', ranks=12, ability_mod=2)
    _set_skill(char, 'Conhecimento', ranks=9, ability_mod=1, misc=2)
    _set_skill(char, 'Adestrar Animais', ranks=12, ability_mod=0)
    _set_skill(char, 'Sobrevivencia', ranks=12, ability_mod=4, misc=2)
    _set_skill(char, 'Cura', ranks=8, ability_mod=4)
    _set_skill(char, 'Ouvir', ranks=6, ability_mod=4)
    _set_skill(char, 'Observar', ranks=6, ability_mod=4)

    CharacterWeapon.objects.create(
        Character=char, Name='Cimitarra', Attack='Cimitarra',
        AttackBonus='+7', Damage='1d6+1', Critical='18-20/x2',
        Range='-', Type='Corte', Notes='Arma druidica',
    )
    CharacterWeapon.objects.create(
        Character=char, Name='Funda', Attack='Funda',
        AttackBonus='+8', Damage='1d4+1', Critical='x2',
        Range='15 m', Type='Concussao', Notes='Pedras comuns',
        AmmunitionName='Balas de funda', AmmunitionCount='20',
    )
    CharacterArmor.objects.create(
        Character=char, Name='Armadura de couro batido', Type='Leve',
        ACBonus='+3', MaxDex='+5', CheckPenalty='-1', SpellFailure='15%',
        Speed='9 m', Weigth='20 lb', SpecialProperties='Nao metalica',
    )
    CharacterShield.objects.create(
        Character=char, Name='Escudo pesado de madeira', ACBonus='+2',
        Weigth='10 lb', CheckPenalty='-2', SpellFailure='15%',
    )
    CharacterProtectionItem.objects.create(
        Character=char, Name='Anel de Protecao +1', ACBonus='+1',
        Weigth='-', SpecialProperties='Deflexao',
    )

    CharacterCompanion.objects.create(
        Character=char, Type='animal', Name='Bruma', Species='Lobo atroz',
        HitPoints=45, ArmorClass=16, Speed='15 m',
        Skills='Ouvir +8, Observar +8, Furtividade +6, Sobrevivencia +5',
        Feats='Rastrear, Derrubar Aprimorado',
        SpecialAbilities='Vinculo, truques: atacar, defender, rastrear, guardar',
        Notes='Companheiro animal; compartilha magias quando adjacente.',
    )
    CharacterSummon.objects.create(
        Character=char, Name='Urso pardo convocado', SpellOrigin='Aliado da Natureza IV',
        Level=4, HitPointsMax=51, HitPointsCurrent=38, ArmorClass=15,
        Initiative='+1', Speed='12 m', BaseAttackBonus='+6', Grapple='+16',
        Size='Grande', Attack='Garra +11 (1d8+8)',
        FullAttack='2 garras +11 (1d8+8) e mordida +6 (2d6+4)',
        AttackBonus='+11', Damage='1d8+8', SpecialAbility='Agarrar aprimorado',
        Skills='Ouvir +6, Observar +6, Natacao +12',
        RoundsTotal=9, RoundsRemaining=6, Highlighted=True,
        SdrMonsterName='Brown Bear',
    )
    CharacterSummon.objects.create(
        Character=char, Name='Unicornio aliado', SpellOrigin='Aliado da Natureza IV',
        Level=4, HitPointsMax=42, HitPointsCurrent=42, ArmorClass=18,
        Initiative='+3', Speed='18 m', BaseAttackBonus='+4', Grapple='+8',
        Size='Grande', Attack='Chifre +11 (1d8+8)',
        FullAttack='Chifre +11 (1d8+8) e 2 cascos +3 (1d4+2)',
        AttackBonus='+11', Damage='1d8+8',
        SpecialAbility='Circulo magico contra o mal, cura 3/dia',
        Skills='Ouvir +11, Observar +11, Sobrevivencia +6',
        RoundsTotal=9, RoundsRemaining=9, SdrMonsterName='Unicorn',
    )

    for name in ['Companheiro Animal', 'Empatia Selvagem', 'Passo sem Pegadas',
                 'Resistir a Atracao da Natureza', 'Forma Selvagem 3/dia',
                 'Imunidade a venenos']:
        Ability.objects.create(Character=char, Name=name, Page='PHB')
    for name in ['Magias Naturais', 'Foco em Magia (Conjuracao)', 'Invocacao Aprimorada',
                 'Magia Estendida']:
        CharacterFeat.objects.create(Character=char, Name=name, Page='PHB')

    _apply(
        char.characterspellcasting,
        CasterClass='Druid', CastingAbility='Sabedoria (SAB)',
        CastingMode='prepared_spontaneous',
        SpontaneousConversion='Invocar Aliado da Natureza',
    )
    for level, name, slot_type, is_used in _DRUID_PREPARED_SLOTS:
        CharacterSpellSlot.objects.create(
            Character=char, Level=level, SlotType=slot_type,
            PreparedSpellName=name, IsUsed=is_used,
        )
    for name, level in [
        ('Enredar', 1), ('Presa Magica', 1), ('Forca do Touro', 2),
        ('Invocar Aliado da Natureza III', 3), ('Pele Rochosa', 4),
        ('Invocar Aliado da Natureza V', 5),
    ]:
        CharacterSpell.objects.create(Character=char, Name=name, Level=level, Page='PHB')

    for name, page, weight in [
        ('Azevinho e visco', 'PHB', '-'),
        ('Bornal de ervas', 'PHB', '2 lb'),
        ('Pergaminho de Comunhao com a Natureza', 'DMG', '-'),
        ('Racoes para Bruma', 'PHB', '8 lb'),
    ]:
        CharacterOtherItem.objects.create(Character=char, Name=name, Page=page, Weigth=weight)
    _apply(char.charactermoney, GP=350, SP=12, CP=0, PP=2)
    for value in ['Comum', 'Druidico', 'Silvestre']:
        CharacterLanguages.objects.create(Character=char, Value=value)

    _set_progress(char, 'Fronteira de Elsir', 36000)
    _set_daily_notes(
        char,
        Preparation='Preparar curas, controle de terreno e invocacoes antes da marcha.',
        Spent='1 uso de Forma Selvagem gasto; Aliado da Natureza III convertido.',
    )
    _add_resource(char, 'Forma Selvagem', 'Druida 9', 3, used=1, refresh='Diario', checks='1')
    _add_resource(char, 'Empatia Selvagem', 'Druida', 99, used=0, refresh='Livre')
    _add_active_effect(char, 'Pele Rochosa', 'Magia', 'RD 10/adamante', 70, 'Limite 90 pontos.')
    _add_buff(char, Name='Forca do Touro', StrengthBonus=4, IsActive=True, Notes='Ativa em forma selvagem')
    _recalculate_stats(char)
    _add_reputation(
        char,
        {
            'Name': 'Ancia Meriel', 'Location': 'Bosque do Carvalho Partido',
            'Relationship': 'Mentora', 'Favor': 'Ritual de purificacao',
            'Notes': 'Desconfia de cidades muradas.',
        },
        {
            'Name': 'Circulo Esmeralda', 'Reputation': 'Guardia',
            'Influence': 'Alta', 'Risk': 'Medio',
            'Notes': 'Protege rotas de animais e druidas locais.',
        },
        {
            'Title': 'Selar a fenda do brejo', 'Party': 'Circulo Esmeralda',
            'Reward': 'Favor do circulo', 'Deadline': 'Antes da cheia',
            'Status': 'Urgente', 'Notes': 'Levar Bruma e evitar fogo.',
        },
    )
    return char


# ---------------------------------------------------------------------------
# Ranger nivel 6
# ---------------------------------------------------------------------------

def seed_ranger(user):
    """Ranger humano nivel 6 com companheiro animal e trilha de exploracao."""
    char = _fresh_character(user, RANGER_NAME)
    _apply(
        char,
        Class='Ranger', Level='6', Race='Human', Alignment='NG',
        Deity='Ehlonna', Size='M', Age='29', Sex='Masculino',
        Heigth='1,78 m', Weight='74 kg', Eye='Cinzentos', Hair='Escuros',
        Skin='Morena',
        Description='Batedor de fronteira que patrulha estradas e ruinas.',
    )
    _apply(
        char.characterstats,
        Strength=14, Dexterity=16, Constitution=12,
        Intelligence=12, Wisdom=14, Charisma=10,
    )
    _apply(
        char.characterstatus,
        TotalHitPoints=45, Speed=30, ACArmorBonus=4, ACShieldBonus=0,
        ACNaturalArmor=0, ACDeflectionModifier=0, ACMiscModifier=0,
        ACSizeModifier=0, DamageReduction=0,
    )
    _apply(
        char.charactersavingthrows,
        FortitudeBaseSave=5, ReflexBaseSave=5, WillBaseSave=2,
    )
    _apply(
        char.characterattackmodifiers,
        BBA=6, SpellResistence=0, GrapplerBBA=6,
        GrapplerSizeModifier=0, GrapplerMiscModifier=0,
    )
    _recalculate_stats(char)

    _set_skill(char, 'Sobrevivencia', ranks=9, ability_mod=2, misc=2)
    _set_skill(char, 'Esconder-se', ranks=9, ability_mod=3)
    _set_skill(char, 'Furtividade', ranks=9, ability_mod=3)
    _set_skill(char, 'Ouvir', ranks=9, ability_mod=2)
    _set_skill(char, 'Observar', ranks=9, ability_mod=2)
    _set_skill(char, 'Procurar', ranks=6, ability_mod=1)
    _set_skill(char, 'Adestrar Animais', ranks=5, ability_mod=0)

    CharacterWeapon.objects.create(
        Character=char, Name='Arco Longo Composto +1', Attack='Arco Longo',
        AttackBonus='+10/+5', Damage='1d8+3', Critical='x3',
        Range='33 m', Type='Perfuracao', Notes='Inimigo predileto: goblinoides +4',
        AmmunitionName='Flechas', AmmunitionCount='60',
    )
    CharacterWeapon.objects.create(
        Character=char, Name='Espada Curta', Attack='Espada Curta',
        AttackBonus='+8/+3', Damage='1d6+2', Critical='19-20/x2',
        Range='-', Type='Perfuracao', Notes='Combate com duas armas',
    )
    CharacterArmor.objects.create(
        Character=char, Name='Camisao de cota de malha +1', Type='Leve',
        ACBonus='+5', MaxDex='+4', CheckPenalty='-1', SpellFailure='20%',
        Speed='9 m', Weigth='25 lb', SpecialProperties='Mantem estilo de combate',
    )
    CharacterCompanion.objects.create(
        Character=char, Type='animal', Name='Flecha', Species='Aguia',
        HitPoints=18, ArmorClass=15, Speed='3 m, voo 24 m',
        Skills='Ouvir +6, Observar +14, Sobrevivencia +2',
        Feats='Prontidao, Acuidade com Arma',
        SpecialAbilities='Vinculo, evasao, truques: atacar, vigiar, buscar',
        Notes='Companheiro animal usado para reconhecimento aereo.',
    )

    for name in ['Rastrear', 'Empatia Selvagem', 'Estilo de Combate: Arquearia',
                 'Inimigo Predileto: Goblinoides +4', 'Inimigo Predileto: Orcs +2',
                 'Tolerancia', 'Companheiro Animal']:
        Ability.objects.create(Character=char, Name=name, Page='PHB')
    for name in ['Tiro Certeiro', 'Tiro Preciso', 'Rastrear (bonus)',
                 'Tiro Rapido (estilo)', 'Vontade de Ferro']:
        CharacterFeat.objects.create(Character=char, Name=name, Page='PHB')

    _apply(
        char.characterspellcasting,
        CasterClass='Ranger', CastingAbility='Sabedoria (SAB)',
        CastingMode='prepared', SpontaneousConversion='',
    )
    for level, name, slot_type, is_used in [
        (1, 'Resistir a Energia', 'normal', False),
        (1, 'Passos Longos', 'normal', True),
    ]:
        CharacterSpellSlot.objects.create(
            Character=char, Level=level, SlotType=slot_type,
            PreparedSpellName=name, IsUsed=is_used,
        )
    for name, level in [('Resistir a Energia', 1), ('Passos Longos', 1)]:
        CharacterSpell.objects.create(Character=char, Name=name, Level=level, Page='PHB')

    for name, page, weight in [
        ('Kit de escalada', 'PHB', '5 lb'),
        ('Armadilhas pequenas desmontaveis', 'PHB', '4 lb'),
        ('Corda de seda (15 m)', 'PHB', '5 lb'),
        ('Mapa das trilhas antigas', 'Campanha', '-'),
    ]:
        CharacterOtherItem.objects.create(Character=char, Name=name, Page=page, Weigth=weight)
    _apply(char.charactermoney, GP=420, SP=18, CP=4, PP=0)
    for value in ['Comum', 'Goblin', 'Orc']:
        CharacterLanguages.objects.create(Character=char, Value=value)

    _set_progress(char, 'Fronteira de Elsir', 17000)
    _set_daily_notes(
        char,
        Preparation='Patrulha ao amanhecer; preparar Passos Longos se houver marcha forcada.',
        Spent='Passos Longos gasto na exploracao do vale.',
    )
    _add_resource(char, 'Inimigo Predileto: goblinoides', 'Ranger 6', 4, used=0, refresh='Sempre ativo')
    _add_resource(char, 'Racoes de Flecha', 'Companheiro animal', 3, used=1, refresh='Diario')
    _add_active_effect(char, 'Passos Longos', 'Magia', '+3 m deslocamento', 60)
    _add_reputation(
        char,
        {
            'Name': 'Tessa da Trilha', 'Location': 'Estalagem da Encruzilhada',
            'Relationship': 'Informante', 'Favor': 'Boatos de estrada',
            'Notes': 'Conhece caravanas que sumiram ao norte.',
        },
        {
            'Name': 'Patrulha do Vale', 'Reputation': 'Batedor confiavel',
            'Influence': 'Media', 'Risk': 'Baixo',
            'Notes': 'Pode requisitar abrigo em postos avancados.',
        },
        {
            'Title': 'Encontrar o acampamento goblin', 'Party': 'Patrulha do Vale',
            'Reward': '600 po', 'Deadline': 'Tres dias',
            'Status': 'Investigando', 'Notes': 'Flecha viu fumaca alem do penhasco.',
        },
    )
    return char


# ---------------------------------------------------------------------------
# Orquestrador
# ---------------------------------------------------------------------------

def seed_all():
    """Cria a conta admin e as fichas de exemplo (de posse do admin).

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
    druid = seed_druid(admin)
    ranger = seed_ranger(admin)
    return {
        'admin': admin,
        'fighter': fighter,
        'wizard': wizard,
        'druid': druid,
        'ranger': ranger,
    }
