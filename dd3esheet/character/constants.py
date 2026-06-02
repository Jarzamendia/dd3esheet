CLASS_LABEL_PT = {
    'Barbarian': 'Bárbaro',
    'Bard':      'Bardo',
    'Cleric':    'Clérigo',
    'Druid':     'Druida',
    'Fighter':   'Guerreiro',
    'Monk':      'Monge',
    'Paladin':   'Paladino',
    'Ranger':    'Ranger',
    'Rogue':     'Ladino',
    'Sorcerer':  'Feiticeiro',
    'Wizard':    'Mago',
}

PHB_BASE_CLASSES = [
    'Barbarian', 'Bard', 'Cleric', 'Druid', 'Fighter',
    'Monk', 'Paladin', 'Ranger', 'Rogue', 'Sorcerer', 'Wizard',
]

SKILL_LIST_PT = [
    'Avaliar', 'Equilibrio', 'Blefar', 'Escalar', 'Concentracao',
    'Oficios', 'Oficios', 'Oficios',
    'Decifrar Escrita', 'Diplomacia', 'Operar Mecanismo', 'Disfarces', 'Arte da Fuga',
    'Falsificacao', 'Obter Informacao', 'Adestrar Animais', 'Cura', 'Esconder-se',
    'Intimidar', 'Saltar',
    'Conhecimento', 'Conhecimento', 'Conhecimento',
    'Ouvir', 'Furtividade', 'Abrir Fechaduras',
    'Atuacao', 'Profissao', 'Profissao', 'Profissao',
    'Cavalgar', 'Procurar', 'Sentir Motivacao', 'Prestidigitacao',
    'Identificar Magia', 'Observar', 'Sobrevivencia', 'Natacao', 'Acrobacia', 'Usar Instrumento Magico',
    'Usar Cordas',
]

EXPANDABLE_SKILL_NAMES = ('Conhecimento', 'Oficios', 'Profissao')

RACE_CHOICES = [
    ('',         '—'),
    ('Human',    'Humano'),
    ('Dwarf',    'Anão'),
    ('Elf',      'Elfo'),
    ('Gnome',    'Gnomo'),
    ('Half-Elf', 'Meio-elfo'),
    ('Half-Orc', 'Meio-orc'),
    ('Halfling', 'Halfling'),
]

ALIGNMENT_CHOICES = [
    ('',   '—'),
    ('LG', 'Leal e Bom'),
    ('NG', 'Neutro e Bom'),
    ('CG', 'Caótico e Bom'),
    ('LN', 'Leal e Neutro'),
    ('N',  'Neutro'),
    ('CN', 'Caótico e Neutro'),
    ('LE', 'Leal e Mau'),
    ('NE', 'Neutro e Mau'),
    ('CE', 'Caótico e Mau'),
]

SIZE_CHOICES = [
    ('', '—'),
    ('F', 'Mínimo'),
    ('D', 'Diminuto'),
    ('T', 'Minúsculo'),
    ('S', 'Pequeno'),
    ('M', 'Médio'),
    ('L', 'Grande'),
    ('H', 'Enorme'),
    ('G', 'Imenso'),
    ('C', 'Colossal'),
]

# Usado em Fase E (cálculo de CA/ataque por tamanho).
SIZE_MODS = {
    'F': {'ac_attack': +8,  'hide': +16, 'space_ft': 0.5,  'reach_ft_tall': 0,  'reach_ft_long': 0},
    'D': {'ac_attack': +4,  'hide': +12, 'space_ft': 1,    'reach_ft_tall': 0,  'reach_ft_long': 0},
    'T': {'ac_attack': +2,  'hide': +8,  'space_ft': 2.5,  'reach_ft_tall': 0,  'reach_ft_long': 0},
    'S': {'ac_attack': +1,  'hide': +4,  'space_ft': 5,    'reach_ft_tall': 5,  'reach_ft_long': 5},
    'M': {'ac_attack':  0,  'hide':  0,  'space_ft': 5,    'reach_ft_tall': 5,  'reach_ft_long': 5},
    'L': {'ac_attack': -1,  'hide': -4,  'space_ft': 10,   'reach_ft_tall': 10, 'reach_ft_long': 5},
    'H': {'ac_attack': -2,  'hide': -8,  'space_ft': 15,   'reach_ft_tall': 15, 'reach_ft_long': 10},
    'G': {'ac_attack': -4,  'hide': -12, 'space_ft': 20,   'reach_ft_tall': 20, 'reach_ft_long': 15},
    'C': {'ac_attack': -8,  'hide': -16, 'space_ft': 30,   'reach_ft_tall': 30, 'reach_ft_long': 20},
}

DEITY_SUGGESTIONS = [
    ('Boccob',             'N'),
    ('Corellon Larethian', 'CG'),
    ('Ehlonna',            'NG'),
    ('Erythnul',           'CE'),
    ('Fharlanghn',         'N'),
    ('Garl Glittergold',   'NG'),
    ('Gruumsh',            'CE'),
    ('Heironeous',         'LG'),
    ('Hextor',             'LE'),
    ('Kord',               'CG'),
    ('Moradin',            'LG'),
    ('Nerull',             'NE'),
    ('Obad-Hai',           'N'),
    ('Olidammara',         'CN'),
    ('Pelor',              'NG'),
    ('St. Cuthbert',       'LN'),
    ('Vecna',              'NE'),
    ('Wee Jas',            'LN'),
    ('Yondalla',           'LG'),
]


# Buffs prontos (efeitos comuns de D&D 3.5e). Cada preset vira um CharacterBuff
# que o jogador ativa/desativa. Bonus de atributo cascateiam pelo motor de
# modificador efetivo; AttackBonus/ACBonus/SaveBonus sao bonus planos.
BUFF_PRESETS = [
    {'Name': 'Forca do Touro',      'StrengthBonus': 4,     'Notes': '+4 Forca (aprimoramento)'},
    {'Name': 'Agilidade do Gato',   'DexterityBonus': 4,    'Notes': '+4 Destreza (aprimoramento)'},
    {'Name': 'Vigor do Urso',       'ConstitutionBonus': 4, 'Notes': '+4 Constituicao (aprimoramento)'},
    {'Name': 'Raposa Astuta',       'IntelligenceBonus': 4, 'Notes': '+4 Inteligencia (aprimoramento)'},
    {'Name': 'Sabedoria da Coruja', 'WisdomBonus': 4,       'Notes': '+4 Sabedoria (aprimoramento)'},
    {'Name': 'Esplendor da Aguia',  'CharismaBonus': 4,     'Notes': '+4 Carisma (aprimoramento)'},
    {'Name': 'Bencao',              'AttackBonus': 1, 'SaveBonus': 1, 'Notes': '+1 ataque, +1 salvas vs medo'},
    {'Name': 'Cancao do Bardo',     'AttackBonus': 1, 'SaveBonus': 1, 'Notes': '+1 ataque e dano, +1 vs encanto/medo'},
    {'Name': 'Pressa',              'AttackBonus': 1, 'ACBonus': 1,   'Notes': '+1 ataque, +1 CA/Reflexos, +9m, acao extra'},
    {'Name': 'Favor Divino',        'AttackBonus': 1, 'Notes': '+1 ataque e dano por 3 niveis (max +3)'},
    {'Name': 'Escudo da Fe',        'ACBonus': 2, 'Notes': '+2 CA (deflexao)'},
    {'Name': 'Heroismo',            'AttackBonus': 2, 'SaveBonus': 2, 'Notes': '+2 ataque, salvas e testes de pericia'},
]

BUFF_EFFECT_FIELDS = (
    'StrengthBonus', 'DexterityBonus', 'ConstitutionBonus', 'IntelligenceBonus',
    'WisdomBonus', 'CharismaBonus', 'AttackBonus', 'ACBonus', 'SaveBonus',
)
