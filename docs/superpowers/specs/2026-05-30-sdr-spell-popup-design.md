# Magias do SDR no input com tooltip + modal

**Status:** design aprovado, aguardando plano de implementação.
**Data:** 2026-05-30.
**Autor:** Joao E Arzamendia (brainstorm com Claude Code).

## Objetivo

Substituir os campos de nome de magia (hoje texto livre) por um autocomplete que sugere magias do SDR, mantendo texto livre como fallback para homebrew. Quando o nome digitado bate com uma magia do SDR, o jogador ganha duas affordances:

- **Hover** sobre o nome → tooltip com a ficha técnica completa (escola, nível, tempo de conjuração, alcance, componentes, duração, save, RM, short description).
- **Click** num ícone ao lado do nome → modal com o `full_text` completo da magia.

Magia sem match no SDR (homebrew / typo / vazio) comporta-se como hoje: input puro, sem tooltip, sem ícone, sem indicação visual extra.

## Escopo

Três lugares onde nomes de magia aparecem hoje:

1. **Livro de Magias** (`/character/<pk>/spellbook/`, `partials/spellbook_level_form.html`) — inputs editáveis por nível. Recebe **autocomplete + tooltip + modal**.
2. **Domínios de clérigo** (ficha principal, `partials/character_spells.html`) — spans read-only com nome da magia de domínio. Recebe **tooltip + modal** (sem autocomplete, não é editável).
3. **Magias de Invocação dos Aliados** (`companions.html`, seção `summon-spells`, `summon-spell-name`) — spans read-only com nome de magia de Aliado da Natureza. Recebe **tooltip + modal**.

Fora de escopo nesta entrega: familiares (não têm lista de magias), reputação, recursos diários.

## Decisões de UX (já validadas com o usuário)

| Decisão | Escolha |
|---|---|
| Input mode | Autocomplete SDR + fallback texto livre |
| Hover vs click | Tooltip leve no hover, modal grande no click (UIs distintas) |
| Conteúdo do tooltip | Ficha técnica completa (escola/nível, casting time, range, components, duration, save, SR, short_description) |
| Magia não encontrada no SDR | Sem popup, sem indicação visual |

## Arquitetura

### Modelo de dados

Adicionar uma coluna em `character.models.CharacterSpell`:

```python
SDRSpellId = models.IntegerField(null=True, blank=True, db_index=True)
```

- `IntegerField` (não `ForeignKey`) porque cruza DBs: `sdr` é um SQLite separado com `managed = False` e sem router. FK cross-DB é problemática no Django; um `IntegerField` + lookup explícito `.using('sdr')` é o padrão já estabelecido no projeto.
- `null=True` é fundamental: magia homebrew/livre fica com `SDRSpellId = NULL` e a UI degrada graciosamente (sem regressão para quem não usa SDR).
- `db_index=True` porque o template lê esse campo em loop e o modal usa para `get_object_or_404`.

Migration no DB `default` (nunca toca `sdr`).

Não criar coluna análoga em `CharacterDomainSpell` ou no `summon` agora — esses casos resolvem o nome → SDR em runtime quando o contexto é montado (são read-only e vêm de fontes determinísticas: tabela de domínio e linhas fixas de Summon Nature's Ally).

### Resolução nome → SDR_Spell

Lógica de matching já existe em `sdr/management/commands/import_spells.py` (busca por `name__iexact`, depois `altname__iexact`). Extrair para função pura reutilizável:

```python
# sdr/lookups.py
def resolve_spell(name: str | None) -> SDR_Spell | None:
    """Retorna o SDR_Spell que casa com `name` (por name ou altname, case-insensitive),
    ou None se vazio/não encontrado. Lê do DB 'sdr'."""
```

Refatorar `import_spells.py` para usar essa função (não duplicar a lógica). Cobrir com testes (precisa do DB `sdr`, então `TestCase` com `databases={'sdr', 'default'}`).

### Save hook no fluxo HTMX

Nos pontos que salvam `CharacterSpell` via HTMX — o handler do livro de magias em `character/views.py::spellbook` e qualquer outro `_save_repeating_slots`/equivalente que persista `CharacterSpell` (a checagem exata é responsabilidade do plano de implementação) — após gravar `Name` chamar `resolve_spell(name)` e setar `SDRSpellId = spell.id if spell else None`. Persistir no mesmo save.

Não inventar mecanismo novo: segue o padrão de "fonte de verdade salva → derivados calculados no mesmo fluxo" descrito no AGENTS.md.

### Endpoint de detalhe (modal)

Nova view em `character/views.py`:

```python
def spell_detail(request, pk, sdr_id):
    character = get_object_or_404(Character, pk=pk, ...)  # permissão de dono
    spell = get_object_or_404(SDR_Spell.objects.using('sdr'), id=sdr_id)
    return render(request, 'character/partials/spell_detail_dialog.html', {'spell': spell})
```

Rota: `character/<pk>/spell/<sdr_id>/` → name `character:spell-detail`.

A view checa permissão de dono da ficha (mesmo padrão das outras views do app — 404 para quem não é dono, não 403). `pk` no path mantém a checagem consistente; `sdr_id` identifica a magia.

Não reusar `sdr/spell.html` porque aquele estende `main.html` e injeta `full_text|safe` cru. Aqui queremos um partial que cabe dentro de `<dialog>` com o look-and-feel da ficha.

### Pré-carga do tooltip (evita N+1)

Ao montar contexto para o livro de magias / domínios / summon nature, fazer **uma única query bulk** no DB `sdr` pelos IDs colhidos e empacotar num dict `{sdr_id: spell_summary}` que vai pro template:

```python
sdr_ids = [s.SDRSpellId for s in spells if s.SDRSpellId]
sdr_lookup = {
    s.id: s
    for s in SDR_Spell.objects.using('sdr').filter(id__in=sdr_ids)
}
```

O template lê `sdr_lookup[spell.SDRSpellId]` para renderizar o tooltip inline. Para domínios e summon, o `sdr_id` é resolvido por nome ao montar a lista (mesma função `resolve_spell`).

### Templates

**`partials/spellbook_level_form.html`** (input editável):

- Cada linha do nome vira `<span class="spell-input-wrap" data-sdr-id="{{ spell.SDRSpellId|default:'' }}">` contendo:
  - O `<input>` existente, agora com `list="spell-suggestions"`.
  - Um `<button type="button" class="spell-detail-trigger">` que dispara `hx-get` ao modal. Renderizado só quando `SDRSpellId` existe.
  - Um `<aside class="spell-tooltip">` pré-renderizado com a ficha técnica do `sdr_lookup[SDRSpellId]`. Renderizado só quando `SDRSpellId` existe. Visível via CSS `:hover` no wrap.

**Datalist único** no fim do template do livro (uma vez, não por nível):

```html
<datalist id="spell-suggestions">
  {% for s in sdr_spell_suggestions %}
    <option value="{{ s.name }}">{{ s.school }} Nv {{ s.level }}</option>
  {% endfor %}
</datalist>
```

`sdr_spell_suggestions` = todas magias SDR ordenadas por nome (~1500 itens; datalist nativo HTML5 aguenta). O texto auxiliar (label do `<option>`) ajuda a desambiguar.

**`partials/character_spells.html` — domínios de clérigo:**

`spellcasting.py` (na função que monta `domain_1_spells` / `domain_2_spells`) passa a devolver dicts com `{name, level, sdr_id}` em vez de só `{name, level}`. Template:

```html
<span class="spell-name-link" data-sdr-id="{{ spell.sdr_id|default:'' }}">
  {{ spell.name|default:"-" }}
</span>
```

Mesmo CSS de hover; click no próprio span dispara `hx-get` ao modal (sem input para focar, span é alvo seguro).

**`companions.html` — Magias de Invocação:**

A view de companions passa a montar `row.spell` como dict `{name, sdr_id}`. Mesma tag `<span class="spell-name-link" data-sdr-id="...">`.

**Novo: `partials/spell_detail_dialog.html`** (conteúdo do modal):

```html
<article class="spell-detail">
  <header>
    <h2>{{ spell.name }}</h2>
    {% if spell.altname %}<p class="spell-altname">{{ spell.altname }}</p>{% endif %}
    <form method="dialog"><button type="submit" aria-label="Fechar">×</button></form>
  </header>
  <div class="spell-detail-body">{{ spell.full_text|safe }}</div>
</article>
```

O `<dialog id="spell-detail-dialog">` vazio fica em `templates/main.html` (base), recebendo conteúdo via `hx-target="#spell-detail-dialog"`.

### Frontend: CSS + uma linha de JS

**Tooltip hover** (CSS puro):

```css
.spell-input-wrap,
.spell-name-link[data-sdr-id]:not([data-sdr-id=""]) {
  position: relative;
}
.spell-tooltip { display: none; position: absolute; z-index: 100; /* ... */ }
.spell-input-wrap[data-sdr-id]:not([data-sdr-id=""]):hover .spell-tooltip,
.spell-name-link[data-sdr-id]:not([data-sdr-id=""]):hover .spell-tooltip {
  display: block;
}
```

Wraps sem `sdr-id` (homebrew) nunca casam o seletor → nunca mostram tooltip. Garante a decisão "sem indicação visual para não-SDR".

**Modal click** (HTMX + 1 linha de JS para abrir o `<dialog>` nativo):

```html
<button type="button"
        class="spell-detail-trigger"
        hx-get="{% url 'character:spell-detail' character.pk spell.SDRSpellId %}"
        hx-target="#spell-detail-dialog"
        hx-swap="innerHTML"
        onclick="document.getElementById('spell-detail-dialog').showModal()">📖</button>
```

Para spans read-only (domínios, summon), o próprio `<span>` recebe os atributos `hx-get`/`hx-target`/`hx-swap`/`onclick` — sem botão extra.

Fechar usa `<form method="dialog">` dentro do `<dialog>` (nativo, sem JS).

O `onclick` é a única linha de JS introduzida. Aceitável dentro do padrão do projeto (já existe `onclick` similar em `companions.html:73-74` para toggle de seção).

## Fluxo de dados

```
Usuário digita "Magic Missile" no livro de magias
   ↓ HTMX change (delay 300ms) → POST /character/<pk>/spellbook/
view spellbook(): _save_repeating_slots grava Name="Magic Missile"
   ↓
sdr.lookups.resolve_spell("Magic Missile") → SDR_Spell(id=42)
   ↓
CharacterSpell.SDRSpellId = 42; .save()
   ↓ render → contexto novo com sdr_lookup={42: <SDR_Spell>}
template spellbook_level_form.html devolvido com:
  - <input value="Magic Missile">
  - data-sdr-id="42"
  - <button hx-get="...spell-detail/42/"> renderizado
  - <aside class="spell-tooltip"> com ficha técnica pré-renderizada
   ↓ HTMX swap outerHTML
Hover no nome → CSS mostra tooltip imediatamente (sem round-trip).
Click no botão 📖 → HTMX GET spell-detail/42/ → injeta no <dialog> → onclick abre.
```

## Tratamento de erro

- `resolve_spell(None)` ou `resolve_spell("")` → retorna `None` sem erro. Save segue normal com `SDRSpellId = None`.
- POST com nome que não bate → mesmo comportamento (sem erro, `SDRSpellId = None`).
- GET `spell-detail/<sdr_id>` com ID inexistente → `404` via `get_object_or_404`.
- GET `spell-detail` para personagem que não é do usuário logado → `404` (padrão do app, não 403).
- Falha do datalist nativo em navegadores muito antigos → input se comporta como texto livre puro (degradação aceita).

## Testes (regra dura: TDD)

**Função pura `sdr.lookups.resolve_spell`** (`TestCase` com `databases={'sdr','default'}`):

- Casa por `name` exato (case-insensitive).
- Casa por `altname` (versão traduzida) quando `name` não bate.
- Retorna `None` para string vazia / `None`.
- Retorna `None` para nome inexistente.
- Quando há ambiguidade (duas magias com mesmo nome), retorna a primeira por `id` (decisão explícita, documentada no docstring).

**View HTMX do livro de magias:**

- POST com `Name="Magic Missile"` → `CharacterSpell.SDRSpellId` setado para o ID correto após save.
- POST com `Name="Bola de Fogo Tropical"` (custom) → `SDRSpellId = None`, sem erro.
- POST que muda de SDR conhecida para custom → `SDRSpellId` é limpo (passa a `None`).
- POST que esvazia o `Name` → `SDRSpellId = None`.
- POST não-HTMX → fallback de página inteira continua funcionando.

**View `spell_detail`:**

- GET `/character/<pk>/spell/<sdr_id>/` válido para o dono → 200 + HTML do dialog partial.
- GET com `sdr_id` inexistente → 404.
- GET para personagem de outro usuário → 404.
- Anônimo → redireciona/401 conforme padrão `login_required` do app.

**Render do template:**

- Linha com `SDRSpellId` setado renderiza `data-sdr-id="<id>"` no wrap e inclui o `<button>` e `<aside class="spell-tooltip">`.
- Linha sem `SDRSpellId` renderiza wrap sem `data-sdr-id` (ou vazio), sem botão, sem tooltip.
- Domínio de clérigo cujo nome bate com SDR_Spell renderiza `data-sdr-id` no span.

**O que NÃO testar via Django tests:**

- CSS hover (verificação visual com `/run`).
- `onclick` que abre `<dialog>` (verificação visual).

## Performance

- Datalist nativo com ~1500 opções: payload ~50KB. Aceitável; carregado uma vez por página.
- Lookup `resolve_spell`: 1 query por save no DB `sdr`. Não alterar índices do `sdr` (schema é `managed=False`, externamente mantido). Se ficar lento, mitigar no app (cache em memória) — não no DB SDR.
- Bulk fetch SDR no render: 1 query por página com `id__in=[...]`.
- Tooltip pré-renderizado: zero round-trip no hover.
- Modal: 1 round-trip por click (só quando jogador realmente quer ver detalhe).

## Não fazer (YAGNI)

- Filtrar datalist por nível ou por classe do personagem. Decisão: começar com lista completa. Refinar só se ficar lento ou ruim de usar.
- Caching server-side da query bulk. Django + SQLite local é rápido o bastante.
- Suporte a digitação em português (`altname`) para autocompletar mostrando ambos os nomes. Decisão: começar mostrando só `name` (versão original) no datalist; `altname` ainda casa no `resolve_spell` para quem digitar.
- Indicador visual de "magia ligada ao SDR" (decisão explícita do usuário: sem indicação).
- Editar SDR_Spell ou criar magias custom permanentes no SDR. Esse banco é read-only.

## Arquivos afetados (resumo)

Novos:

- `dd3esheet/sdr/lookups.py` — função `resolve_spell`.
- `dd3esheet/character/templates/character/partials/spell_detail_dialog.html` — partial do modal.
- Migration em `dd3esheet/character/migrations/` para a coluna `SDRSpellId`.

Modificados:

- `dd3esheet/character/models.py` — coluna `SDRSpellId` em `CharacterSpell`.
- `dd3esheet/character/views.py` — view `spell_detail`, save hook nos fluxos de magia.
- `dd3esheet/character/urls.py` — rota `character:spell-detail`.
- `dd3esheet/character/spellcasting.py` — `domain_1_spells` / `domain_2_spells` passam a incluir `sdr_id`.
- `dd3esheet/character/templates/character/partials/spellbook_level_form.html` — wrap, datalist, tooltip, botão modal.
- `dd3esheet/character/templates/character/partials/character_spells.html` — spans de domínio com `data-sdr-id`.
- `dd3esheet/character/templates/character/companions.html` — span de summon spell com `data-sdr-id`.
- `dd3esheet/templates/main.html` — `<dialog id="spell-detail-dialog">` vazio.
- `dd3esheet/static/css/character_sheet.css` — `.spell-input-wrap`, `.spell-tooltip`, `.spell-name-link`, `.spell-detail` e regras do dialog.
- `dd3esheet/sdr/management/commands/import_spells.py` — usar `resolve_spell` (deduplica lógica).
- `dd3esheet/character/tests.py` e `dd3esheet/sdr/tests.py` — cobertura de novos comportamentos.

## Aprovações e marcos

1. Design aprovado (este documento).
2. Plano de implementação detalhado (próximo passo: `writing-plans`).
3. Execução task-by-task com testes verdes a cada checkpoint.
4. Verificação visual via `/run` (hover + click) antes de fechar a feature.
