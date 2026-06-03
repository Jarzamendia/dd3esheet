# AGENTS.md

Guia para agentes de codificação (Claude Code, Codex, Copilot, etc.) trabalhando neste repositório.

## Produto

Ficha virtual de **D&D 3.5**. O objetivo é uma ficha que **pareça com a ficha em papel** do D&D 3.5, mas com automação de um app.

Diretrizes de produto que orientam toda decisão técnica:

- **Visual de ficha em papel.** Layout, agrupamento de campos e ordem devem lembrar a ficha oficial. Não reinvente UX que já existe no papel — replique.
- **Cálculos são automáticos.** O jogador digita o que é fonte de verdade (Strength = 16, ranks de Climb = 4); modificadores e totais derivados (mod +3, AC total, saves, BAB, total de skill) são calculados pelo backend, não digitados.
- **Sem reload de página.** Toda edição salva via HTMX e devolve apenas o partial relevante já com os valores recalculados (ver "Padrão HTMX + partials"). `crispy-forms` formata os forms dentro dos partials.
- **Múltiplas fichas por usuário.** `Character` já é `ForeignKey(User)`. A "home" lista todas as fichas do usuário logado.
- **Compartilhamento entre jogadores logados.** Outros usuários (com conta) podem ser convidados a **ver** uma ficha. Ainda não implementado — quando for, modele como permissão explícita (ex: `CharacterShare(character, user, can_edit=False)`), não como link público.

Stack: Django 4.2 + django-htmx + django-crispy-forms (bootstrap5) + django-filter. Python 3.12. Código Django em `dd3esheet/` (subdiretório do repo).

## Running

Everything runs in Docker. From the `dd3esheet/` directory:

```
docker-compose up                    # starts web on localhost:8000
docker-compose exec web bash         # shell into the container
```

O `command` do serviço `web` roda `migrate` → `seed` → `runserver` a cada `up`, então o banco já sobe migrado e com a conta admin + fichas de exemplo prontas (ver "Seeds"). O `seed` é idempotente; rodar várias vezes é seguro.

Inside the container (the commands the README assumes):

```
python manage.py makemigrations
python manage.py migrate             # ONLY migrates the 'default' DB (see Databases)
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
python manage.py test <app>          # e.g. python manage.py test character
```

Admin is at `localhost:8000/admin`.

## Seeds (dados de exemplo / teste)

`character/seeds.py` é a fonte única de dados de exemplo. Cria uma conta admin e duas fichas **completas e consistentes** (Guerreiro humano nível 5 e Mago elfo nível 8 especialista em Evocação). Os mesmos builders são usados pela linha de comando e pelos testes, então o que se vê no app é o que os testes exercitam.

Roda **automaticamente** no `docker compose up` (o `command` do serviço `web` faz `migrate` → `seed` → `runserver`). Para rodar manualmente:

```
python manage.py seed                       # dentro do container
docker compose exec web python manage.py seed
```

API importável (usada em `character/tests.py::SeedTests`):

```python
from character.seeds import seed_all, seed_admin, seed_fighter, seed_wizard
from character.seeds import ADMIN_USERNAME, ADMIN_PASSWORD, FIGHTER_NAME, WIZARD_NAME
```

Pontos importantes:

- **Idempotente.** Rodar de novo recria as fichas de exemplo do zero (apaga a anterior do mesmo dono/nome e cria uma nova) e redefine a senha do admin.
- **Derivados consistentes.** Os builders setam só as fontes de verdade e chamam `views._recalculate_stats` — o mesmo recálculo da edição inline — para mods/CA/saves/grapple. Skills e slots de magia são preenchidos explicitamente.
- **Conta admin = `jarza` / `P@ssw0rd`** (superusuário). Credenciais fixas e conhecidas: **só para uso local/teste**, nunca produção.
- `db.sqlite3` é `gitignore`d, então rodar o seed afeta só o banco local.

## Architecture

Apps mounted in `dd3esheet/urls.py`:

- `home/` — landing page (`/`).
- `character/` — user-owned character sheets (`/character/`). All character data lives here: `Character` plus a constellation of `OneToOneField`/`ForeignKey` siblings (`CharacterStats`, `CharacterStatus`, `CharacterSavingThrows`, `CharacterAttackModifiers`, `CharacterSkill`, `CharacterWeapon`, `CharacterArmor`, `CharacterShield`, `CharacterFeat`, `CharacterSpell`, `CharacterMoney`, `CharacterProgress`, `CharacterDailyNotes`, `CharacterDailyResource`, `CharacterActiveEffect`, etc.). Além da ficha principal, expõe páginas dedicadas de Companheiros, Recursos Diários e Reputação. New character-related fields generally mean a new sibling model keyed back to `Character`, not adding columns to `Character` itself. Supporting modules: `services.py` (`_bootstrap_character_siblings` cria todos os singletons + perícias base de `constants.SKILL_LIST_PT` ao criar a ficha; `ensure_expandable_skill_slots` mantém slots adicionais para Conhecimento/Ofícios/Profissão; `sdr_class_choices` lê classes do banco `sdr`), `calculations.py` (funções puras: `ability_modifier`, `skill_total`, `load_limits_for_strength`, `parse_bonus`, `daily_resource_remaining`, etc. — testáveis com `SimpleTestCase`), `spellcasting.py` (cálculo de slots/DC/bônus dirigido pela tabela `class_table` do SDR), `constants.py` (choices de alignment/size/race, sugestões de divindade, rótulos PT de classe, `SKILL_LIST_PT`, `EXPANDABLE_SKILL_NAMES`).
- `sdr/` — read-only D&D 3.5 SRD reference data (`/sdr/`): spells, monsters, classes, feats, equipment, items, powers, skills, domains. Browsing and filtering only.
- `initiative/` — rastreador de iniciativa compartilhado (`/iniciativa/`): dono + `Slug` público + polling HTMX (viewer anônimo lê, dono edita).
- `sprites/` — Sprite Library navegável (`/sprites/`) + biblioteca central de imagens: `SpriteAsset` + variantes + bindings, usada por classes, monstros, iniciativa e mapas. O manifesto Parchment & Ink entra como 496 placeholders via `python manage.py seed_sprite_library` (também chamado pelo seed geral).
- `tabletop/` — mesa virtual / criador de mapas (`/mesa/`): cenas compartilhadas, miniaturas arrastáveis (drag JS vanilla) e névoa retangular aplicada no servidor. Reaproveita o padrão do `initiative` e guarda imagens no `sprites`. Detalhes em `TABLETOP.md`.

### Two databases

`settings.py` defines two SQLite DBs:

- `default` (`db.sqlite3`) — Django auth + everything in the `character` and `home` apps. This is what `migrate` writes to.
- `sdr` (`dnd35.sqlite3`) — the SRD reference data, **pre-existing and externally maintained**. All `sdr/models.py` models use `managed = False` with explicit `db_table = '...'`. Never run migrations against this database, and never edit `sdr/` models without matching the existing schema.

Because there is no default router, **every SDR query must use `.using('sdr')`** (see `sdr/views.py` for the pattern: `SDR_Spell.objects.using('sdr')...`). Forgetting this hits `default` and silently returns nothing.

The README documents regenerating `sdr/models.py` from the SRD DB via `python manage.py inspectdb --database sdr` — use this rather than hand-writing model fields if the SRD schema changes.

### Templates

`TEMPLATES.DIRS` includes the top-level `templates/` directory in addition to per-app `templates/`. Shared base templates live at the top level; app-specific templates under `<app>/templates/<app>/`.

### Filtering pattern

List views use `django-filter` `FilterSet` classes (see `sdr/filters.py`) with `icontains` lookups. The view passes the bound filter into the template; templates render `{{ filtered_X.form }}` plus iterate `filtered_X.qs`.

## Padrão HTMX + partials (regra dura)

Editar qualquer campo da ficha **não pode** causar reload de página. O fluxo é sempre:

1. Form renderizado por `crispy-forms` dentro de um **partial** (`character/partials/*.html`), com `hx-post`, `hx-target` apontando pro próprio container do partial e `hx-swap="outerHTML"`.
2. A view detecta `request.htmx` e usa `request.htmx.target` para rotear qual form processar (ver `character/views.py::character`). Cada partial tem um `target` único (ex: `characterForm`, `characterStatsForm`).
3. Após `form.save()`, a view **recalcula os campos derivados** (mods, AC, saves, totais de skill) e devolve `render(request, "character/partials/<o_mesmo_partial>.html", context)` com os valores atualizados.
4. Resposta a request não-HTMX renderiza a página inteira (fallback). Resposta HTMX devolve só o partial.

**A ficha inteira já é editável inline.** A view `character/views.py::character(request, pk)` é um *dispatcher* único: um encadeamento de `if request.htmx.target == '...'` cobre todas as seções (`characterIdentityForm`, `characterForm`, `characterStatsForm`, `characterStatusForm`, `characterArmorForm`, `characterSavesForm`, `characterAttackForm`, `characterSkillsForm`, `characterWeaponsForm`, `characterProgressForm`, `characterEquipmentForm`, `characterItemsForm`, `characterMoneyForm`, `characterFeatsForm`, `characterSpecialsForm`, `characterSpellsForm`). Páginas extras (companions, daily-resources, reputation) têm views próprias em `character/views.py`. Só identidade/descrição/stats usam `ModelForm` crispy (`CharacterIdentityForm`, `CharacterForm`, `CharacterStatsForm`); o resto lê o POST direto via helpers:

- `_update_fields_from_post(instance, request, fields, prefix='')` — atribui campos do POST a um model, convertendo por tipo de field (int/bool/str) e salvando se algo mudou.
- `_save_repeating_slots` / `_ordered_slots` — seções de linhas repetidas com contagem fixa (armas=4, itens de proteção=5, outros itens=32, talentos=24, habilidades=12, idiomas=12, slots de magia=20, magias conhecidas=36). Os inputs vêm com prefixo `prefix_<n>_campo`.
- `_recalculate_stats(character)` — recalcula e persiste todos os derivados (mods de atributo, AC total/toque/surpresa, iniciativa, saves totais, grapple) num único save, apoiando-se nas funções puras de `character/calculations.py`. É chamada nas branches de stats/status/armor/saves/attack.
- `_sheet_context(char, **extra)` — monta o contexto completo da ficha (forms + todos os slots ordenados + `spellcasting_context` + progresso/XP). Toda branch retorna `render(..., _sheet_context(char))`.

Não adicione `<form action="">` com submit tradicional pra editar ficha. Se precisar de algo que não cabe em partial (ex: criar ficha nova), aí sim página inteira + redirect.

## Cálculos derivados (regra dura)

São **calculados no backend**, nunca digitados pelo jogador, nunca calculados em JS no template:

- **Modificador de atributo:** `(stat - 10) // 2` (regra D&D 3.5; vale para todos os 6 atributos).
- **AC Total:** `10 + armor + shield + dex_mod + size_mod + natural_armor + deflection + misc`.
- **Saves totais:** `base + ability_mod + magic + misc + temporary` para Fort/Ref/Will.
- **Skill total:** `ranks + ability_mod + misc` (e zero se `trained_only` e ranks == 0).
- **BAB derivado / grapple total / iniciativa:** somar componentes que já existem nos models.

Sempre que um campo fonte muda, os derivados que dependem dele devem ser recalculados **no mesmo save** e persistidos. Não calcule "on the fly" no template — o valor persistido é a fonte da verdade pra quem está vendo a ficha compartilhada.

Onde os cálculos vivem hoje: as **funções puras** ficam em `character/calculations.py` — `ability_modifier`, `skill_total`, `skill_ability_modifier`, `skill_graduation_limits`, `is_trained_only_skill`, `load_limits_for_strength`, `parse_weight`/`total_carried_weight`, `parse_bonus`/`equipment_armor_class_bonuses`, `daily_resource_remaining`. O orquestrador `character/views.py::_recalculate_stats(character)` aplica regras de CA, saves, iniciativa e grapple e persiste nos siblings num só fluxo. A matemática de conjuração (DC de magia, bônus de magias por atributo, contagem de slots) está em `character/spellcasting.py` como funções puras (`spell_save_dc`, `bonus_spells_for_level`, `ability_modifier`, `numeric_slot_count`) — testáveis sem DB com `SimpleTestCase` (ver TDD abaixo). Ao adicionar derivados novos, prefira funções puras em `calculations.py` ou `spellcasting.py` e chame-as no fluxo de save; não calcule no template.

## TDD (regra dura)

**Teste primeiro, código depois.** Para cada feature ou correção:

1. Escreva um teste que falha (`python manage.py test character`).
2. Implemente o mínimo pra passar.
3. Refatore se precisar, mantendo verde.

O que **tem que** ter teste:

- Toda função de cálculo derivado (mods, AC, saves, skills, etc.) — testes unitários puros, sem DB.
- Toda permissão de acesso (dono vê e edita, convidado vê, estranho recebe 404).
- Toda view HTMX: que retorna o partial correto, que recalcula derivados ao salvar, e que não-HTMX cai no fallback.

CRUD trivial e admin não precisam de teste dedicado. Testes ficam em `<app>/tests.py` (ou pacote `tests/` se crescer). Use `Django TestCase` padrão; pra cálculos puros, `SimpleTestCase` (não toca DB, é mais rápido).

## Qualidade de implementação

Ao fazer qualquer alteração de código, o agente deve:

- **Criar ou atualizar testes junto com a mudança.** Se a alteração não justificar teste novo, explique brevemente por quê na resposta final.
- **Simplificar o código tocado.** Prefira funções pequenas, nomes claros e fluxo direto. Remova duplicação quando isso reduzir complexidade real, mas evite refatorações grandes sem relação com a tarefa.
- **Manter a solução local ao problema.** Não introduza abstrações, dependências ou padrões novos sem necessidade concreta e alinhada ao restante do projeto.
- **Deixar o código mais fácil de testar.** Regras de negócio e cálculos devem ficar em funções puras sempre que possível; views devem orquestrar forms, permissões, saves e renderização.

## Compartilhamento (quando for implementar)

Modelo de permissão explícito, não link público:

- Crie um model tipo `CharacterShare(character=FK, user=FK, can_edit=Bool)`.
- Toda view de ficha checa: usuário é dono **OU** tem `CharacterShare` ativo. Caso contrário → 404 (não 403 — não revele que a ficha existe).
- Convite por username ou email do usuário já cadastrado. Sem fluxo de "convidar quem não tem conta" por enquanto.

## Convenções de código

- **Models de `character/` usam PascalCase** (`Name`, `Strength`, `ACTotal`) — não é convenção Django, mas é consistente em todo o app. Mantenha ao estender.
- **Idioma:** código Python em inglês, templates e textos de UI podem ser em português, comentários no idioma que fizer mais sentido pro contexto.
- **Models do `sdr/` são read-only** (`managed = False`). Toda query precisa de `.using('sdr')` — esquecer isso bate no DB `default` e retorna vazio em silêncio.
- **`requirements.txt` é UTF-16** (BOM + null bytes). Não reescreva como UTF-8 sem confirmar — `pip install` lida com isso dentro do container, e ferramentas que re-encodaram já quebraram o build do Docker antes.
- **Novos campos da ficha = novo sibling model** com FK/OneToOne para `Character`, não colunas novas em `Character`. Segue o padrão que já está lá (`CharacterStats`, `CharacterStatus`, etc.).
- **Código simples primeiro.** Antes de finalizar, revise se a mudança pode ser expressa com menos ramificações, menos estado mutável ou menos acoplamento, sem perder clareza.
