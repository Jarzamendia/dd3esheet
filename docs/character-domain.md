# Dominio da ficha de personagem

## Produto

A ficha deve replicar a experiencia da ficha de papel de D&D 3.5, com automacao onde o app agrega valor.

O jogador deve preencher fontes de verdade:

- atributos;
- ranks;
- bonus base;
- itens;
- magias conhecidas/preparadas;
- dinheiro;
- equipamentos.

O sistema deve calcular derivados:

- modificadores de atributos;
- CA;
- saves;
- iniciativa;
- agarrar;
- totais de pericia;
- resumo de magias.

## Modelo principal

`Character` representa a ficha e pertence a um usuario:

```python
User = models.ForeignKey(User, on_delete=models.CASCADE)
```

Regra de acesso atual:

- o dono ve e edita;
- outro usuario recebe 404;
- compartilhamento ainda nao existe.

## Models irmaos

O app evita colocar tudo dentro de `Character`. Cada area da ficha vive em um model relacionado.

One-to-one principais:

- `CharacterStats`
- `CharacterStatus`
- `CharacterSavingThrows`
- `CharacterAttackModifiers`
- `CharacterSkillGraduation`
- `CharacterOtherItemObs`
- `CharacterMoney`
- `CharacterProgress` (XP, nome da campanha)
- `CharacterSpellSave`
- `CharacterArcaneSpellFailCheck`
- `CharacterMagicConditionalModifiers`
- `CharacterSpellcasting`
- `CharacterDailyNotes` (anotacoes de preparacao/gastos do dia)

Foreign keys principais:

- `CharacterSkill` (com campo `SkillSpecialization` para pericias expansiveis como Conhecimento, Oficios, Profissao)
- `CharacterWeapon`
- `CharacterArmor`
- `CharacterShield`
- `CharacterProtectionItem`
- `CharacterOtherItem`
- `CharacterFeat`
- `Ability`
- `CharacterSpell`
- `CharacterSpellSlot`
- `CharacterMagicDayUse`
- `CharacterLanguages`
- `CharacterDailyResource` (recursos com maximo/usado/recarga)
- `CharacterActiveEffect` (efeitos ativos com duracao em rounds)

Ao criar uma ficha, `character.services._bootstrap_character_siblings(character)` cria os one-to-one e as pericias base (lista em `constants.SKILL_LIST_PT`, com slots multiplos para pericias expansiveis). `character.services.ensure_expandable_skill_slots(character)` garante slots adicionais para Conhecimento, Oficios e Profissao conforme o jogador preenche especializacoes.

## Convencoes de model

O app `character` usa nomes PascalCase nos campos:

- `Name`
- `Strength`
- `ACTotal`
- `UpdatedAt`

Mantenha esse padrao ao alterar models existentes.

Novas areas da ficha devem preferir um novo model irmao ligado a `Character`, em vez de adicionar colunas ao proprio `Character`.

## Criacao de ficha

Fluxo:

1. `createCharacter` recebe `CharacterCreateForm`.
2. Salva `Character` com `User=request.user`.
3. Chama `_bootstrap_character_siblings`.
4. Redireciona para a ficha.

O usuario nao pode escolher outro dono via POST.

## Slots fixos de UI

A ficha renderiza algumas areas com quantidade fixa de linhas mesmo que o banco ainda nao tenha registros.

`character.views._sheet_context` monta:

- 4 armas;
- 5 itens de protecao;
- 32 outros itens;
- 24 talentos;
- 12 habilidades especiais;
- 12 idiomas;
- 20 slots de magia;
- 36 magias conhecidas.

Se o usuario digita em um slot vazio, `_save_repeating_slots` cria o registro.

## Calculos derivados atuais

`character.views._recalculate_stats(character)` orquestra o recalculo e persiste:

- modificadores dos seis atributos;
- modificadores temporarios;
- CA total;
- CA de toque;
- CA surpreso;
- iniciativa;
- modificadores de habilidade dos saves;
- totais de Fortitude, Reflexos e Vontade;
- modificador de forca do agarrar;
- total de agarrar.

As regras puras vivem em `character/calculations.py` (testaveis sem DB com `SimpleTestCase`):

- `ability_modifier(score)`
- `skill_total(ability_mod, ranks, misc, trained_only=False)`
- `skill_ability_modifier(skill_name, stats)` / `skill_ability_key(skill_name)`
- `skill_graduation_limits(level)` (classe e cruzada)
- `is_trained_only_skill(skill_name)`
- `load_limits_for_strength(strength)` (leve/medio/pesado/levantar/empurrar)
- `parse_weight(value)` / `total_carried_weight(values)`
- `parse_bonus(value)` / `equipment_armor_class_bonuses(...)`
- `daily_resource_remaining(maximum, used)`

Tabelas auxiliares: `ABILITY_FIELDS`, `ABILITY_KEY_LABELS`, `SKILL_ABILITY_BY_NAME`, `TRAINED_ONLY_SKILLS`.

Magias usam funcoes em `character/spellcasting.py`:

- `ability_modifier`
- `spell_save_dc`
- `bonus_spells_for_level`
- `numeric_slot_count`
- `spellcasting_context`

## Regra de ouro

Nao calcule valores derivados no template ou em JavaScript. Salve a fonte de verdade, recalcule no backend e persista o derivado no mesmo fluxo.

