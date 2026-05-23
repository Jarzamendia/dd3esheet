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

Inside the container (the commands the README assumes):

```
python manage.py makemigrations
python manage.py migrate             # ONLY migrates the 'default' DB (see Databases)
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
python manage.py test <app>          # e.g. python manage.py test character
```

Admin is at `localhost:8000/admin`.

## Architecture

Three Django apps, mounted in `dd3esheet/urls.py`:

- `home/` — landing page (`/`).
- `character/` — user-owned character sheets (`/character/`). All character data lives here: `Character` plus a constellation of `OneToOneField`/`ForeignKey` siblings (`CharacterStats`, `CharacterStatus`, `CharacterSavingThrows`, `CharacterAttackModifiers`, `CharacterSkill`, `CharacterWeapon`, `CharacterArmor`, `CharacterShield`, `CharacterFeat`, `CharacterSpell`, `CharacterMoney`, etc.). New character-related fields generally mean a new sibling model keyed back to `Character`, not adding columns to `Character` itself.
- `sdr/` — read-only D&D 3.5 SRD reference data (`/sdr/`): spells, monsters, classes, feats, equipment, items, powers, skills, domains. Browsing and filtering only.

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

Não adicione `<form action="">` com submit tradicional pra editar ficha. Se precisar de algo que não cabe em partial (ex: criar ficha nova), aí sim página inteira + redirect.

## Cálculos derivados (regra dura)

São **calculados no backend**, nunca digitados pelo jogador, nunca calculados em JS no template:

- **Modificador de atributo:** `(stat - 10) // 2` (regra D&D 3.5; vale para todos os 6 atributos).
- **AC Total:** `10 + armor + shield + dex_mod + size_mod + natural_armor + deflection + misc`.
- **Saves totais:** `base + ability_mod + magic + misc + temporary` para Fort/Ref/Will.
- **Skill total:** `ranks + ability_mod + misc` (e zero se `trained_only` e ranks == 0).
- **BAB derivado / grapple total / iniciativa:** somar componentes que já existem nos models.

Sempre que um campo fonte muda, os derivados que dependem dele devem ser recalculados **no mesmo save** e persistidos. Não calcule "on the fly" no template — o valor persistido é a fonte da verdade pra quem está vendo a ficha compartilhada.

Coloque a lógica de cálculo em funções puras (ex: `character/calculations.py`) que recebem os valores e retornam os derivados. View chama a função, atribui aos campos, salva. Isso é o que será testado (ver TDD abaixo).

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
