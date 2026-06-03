# Mesa Virtual — Tema "Parchment & Ink" (Fatia A) — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Vestir todas as telas do `/mesa/` (tabletop) com o design language "Parchment & Ink" do `design_handoff_dnd_vtt/`, de forma imersiva (inclui nav e rodapé enquanto na mesa), sem alterar comportamento nem tocar no resto do app.

**Architecture:** Um stylesheet compartilhado novo (`parchment-theme.css`) declara os design tokens **escopados sob a classe `.tt-themed`** (não em `:root`, para não colidir com as variáveis do `character_sheet.css`) mais as primitivas reutilizáveis. As páginas da mesa ativam o tema via uma classe no `<body>` (`sheet-body tt-themed paper-field`), o que também permite re-skinnar a nav/rodapé globais só na mesa. O `tabletop.css` é reescrito para consumir esses tokens. Mudança é 100% visual: nenhum model, rota ou lógica de view muda.

**Tech Stack:** Django 4.2 + templates (DTL) + CSS puro + Google Fonts (CDN). Sem build step, sem framework JS. Testes com `python manage.py test tabletop` (rodar dentro do container Docker).

**Spec de origem:** `docs/superpowers/specs/2026-06-03-tabletop-parchment-theme-design.md`.

---

## Contexto que o agente precisa saber

- **Onde rodar comandos:** tudo roda no Docker, a partir do diretório `dd3esheet/` (subdiretório do repo). Para testes: `docker compose exec web python manage.py test tabletop`. Se já estiver num shell do container, é só `python manage.py test tabletop`.
- **Idioma:** código Python em inglês; textos de UI e comentários podem ser PT. Models do `tabletop` usam PascalCase (`Name`, `Slug`).
- **TDD (regra dura do projeto):** teste primeiro. Mas a fatia A é quase só CSS/template; o único comportamento testável é "a página da mesa carrega o tema". Há **uma** tarefa de teste (Task 1) que cobre isso; o resto é CSS sem teste automatizável (justificado em cada tarefa).
- **Não** adicionar trailer `Co-Authored-By` nos commits deste repo.
- **Não** commitar outros arquivos já modificados na árvore — cada `git add` abaixo lista exatamente os arquivos da tarefa.
- **Caminhos são relativos à raiz do repo** (`C:/Users/Jarzamendia/git/github/dd3esheet/`). O código Django vive em `dd3esheet/` dentro do repo.

## Por que `.tt-themed` e não `:root`

`dd3esheet/static/css/character_sheet.css` é carregado globalmente e define em `:root`:
`--ink: #1a1a1a`, `--ink-soft: #585858`, `--paper-bg: #ffffff`, `--font-display`, `--gap`, etc.
Se o tema parchment redefinisse esses nomes em `:root`, vazaria para as fichas. Declarando os tokens em `.tt-themed` (aplicado ao `<body>` só nas páginas da mesa), eles sobrescrevem os valores de `:root` **apenas para os descendentes do body da mesa** (cascata de custom properties), sem afetar nenhuma outra tela.

## Estrutura de arquivos

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `dd3esheet/static/css/parchment-theme.css` | **Criar** | Tokens (sob `.tt-themed`) + primitivas (`.paper-field`, `.btn`, `.eyebrow`, `.rule`, `.mono`, `.swatch`, scrollbars) + re-skin imersivo de `.app-nav`/`.app-footer`. Compartilhado com fatias D/E. |
| `dd3esheet/templates/main.html` | **Modificar** | Trocar `<body class="sheet-body">` por um `{% block body_class %}`. |
| `dd3esheet/tabletop/templates/tabletop/base_tabletop.html` | **Modificar** | Setar a classe do body, linkar fontes (Spectral + JetBrains Mono) e `parchment-theme.css` antes de `tabletop.css`. |
| `dd3esheet/static/css/tabletop.css` | **Reescrever** | Consumir os tokens parchment; mapear Kind→acento; revestir topbar/botões/cards/forms/canvas/tokens/névoa/editor. |
| `dd3esheet/tabletop/tests.py` | **Modificar** | Teste-guarda: página da mesa renderiza `tt-themed` e linka `parchment-theme.css`. |
| `TABLETOP.md` | **Modificar** | Nota curta de que a mesa usa o tema Parchment & Ink. |

---

## Task 1: Teste-guarda + ativação do tema (body class + theme file)

Cria o teste que falha, depois faz passar criando o stylesheet e ligando-o às páginas da mesa.

**Files:**
- Test: `dd3esheet/tabletop/tests.py` (adicionar uma classe ao final)
- Create: `dd3esheet/static/css/parchment-theme.css`
- Modify: `dd3esheet/templates/main.html:22`
- Modify: `dd3esheet/tabletop/templates/tabletop/base_tabletop.html` (arquivo inteiro)

- [ ] **Step 1: Escrever o teste que falha**

Adicionar ao **final** de `dd3esheet/tabletop/tests.py` (o arquivo já importa `User`, `TestCase`, `reverse`, `GameTable`):

```python
class ThemeTests(TestCase):
    """Fatia A: paginas da mesa carregam o tema Parchment & Ink."""

    def test_table_view_uses_parchment_theme(self):
        owner = User.objects.create_user('gm', password='x' * 12)
        table = GameTable.objects.create(Owner=owner, Name='Mesa Teste')
        resp = self.client.get(reverse('tabletop:table', args=[table.Slug]))
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        # classe imersiva no body ativa os tokens parchment
        self.assertIn('tt-themed', html)
        # stylesheet compartilhado dos tokens esta linkado
        self.assertIn('parchment-theme.css', html)
```

- [ ] **Step 2: Rodar o teste para confirmar que falha**

Run: `docker compose exec web python manage.py test tabletop.tests.ThemeTests -v 2`
Expected: FAIL — `'tt-themed' not found in` (o body ainda é só `sheet-body` e não há link pro novo CSS).

- [ ] **Step 3: Criar o stylesheet compartilhado `parchment-theme.css`**

Criar `dd3esheet/static/css/parchment-theme.css` com exatamente este conteúdo:

```css
/* ============================================================
   Parchment & Ink — tema compartilhado das telas da mesa.
   Tokens portados de design_handoff_dnd_vtt/theme.css, porem
   escopados sob .tt-themed (NAO :root) para nao colidir com as
   variaveis globais de character_sheet.css. Reusado por D/E.
   ============================================================ */

.tt-themed {
  /* --- core ink + paper --- */
  --ink:        #2b2622;
  --ink-soft:   #493628;
  --parchment:  #efe6d2;
  --bone:       #d6c6aa;

  /* --- palette family --- */
  --ochre:        #c8923a;
  --leather:      #7a4f2a;
  --forest:       #4f6b3a;
  --iron:         #6b6f73;
  --deep-red:     #8a2f28;
  --steel-blue:   #3f6079;
  --muted-gold:   #b58a36;
  --arcane-teal:  #2f6f6a;
  --royal-blue:   #314f7c;
  --dull-violet:  #5d4978;

  /* --- derived surfaces --- */
  --paper-0:    #f4ecd9;
  --paper-1:    #efe6d2;
  --paper-2:    #e6d9bd;
  --paper-3:    #ddcca9;
  --edge-line:  #cdbb96;
  --edge-strong:#b29b6f;

  /* --- text --- */
  --text:        #2b2622;
  --text-soft:   #5a4a37;
  --text-faint:  #8a7857;
  --line:        #2b2622;

  /* --- typography --- */
  --font-display: 'Cinzel', Georgia, serif;
  --font-body:    'EB Garamond', Georgia, serif;
  --font-alt:     'Spectral', Georgia, serif;
  --font-mono:    'JetBrains Mono', ui-monospace, monospace;

  /* --- spacing scale --- */
  --sp-1: 4px;  --sp-2: 8px;  --sp-3: 12px; --sp-4: 16px;
  --sp-5: 24px; --sp-6: 32px; --sp-7: 48px; --sp-8: 64px;

  --radius: 3px;
  --radius-lg: 5px;

  --shadow-1: 0 1px 2px rgba(43,38,34,.10), 0 2px 6px rgba(43,38,34,.06);
  --shadow-2: 0 4px 14px rgba(43,38,34,.16);
  --shadow-inset: inset 0 1px 0 rgba(255,255,255,.35), inset 0 -1px 0 rgba(43,38,34,.08);

  --grain: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.045'/%3E%3C/svg%3E");

  color: var(--text);
  font-family: var(--font-body);
}

/* campo de papel quente usado como fundo da pagina da mesa */
.tt-themed.paper-field {
  background-color: var(--paper-1);
  background-image:
    var(--grain),
    radial-gradient(120% 90% at 18% 8%, rgba(255,250,236,.7), rgba(255,250,236,0) 55%),
    radial-gradient(120% 120% at 88% 96%, rgba(120,92,52,.16), rgba(120,92,52,0) 50%),
    radial-gradient(100% 80% at 50% 50%, rgba(239,230,210,1), rgba(224,210,180,1));
}

.tt-themed h1, .tt-themed h2, .tt-themed h3, .tt-themed h4 {
  font-family: var(--font-display);
  font-weight: 600;
  color: var(--ink);
  letter-spacing: .01em;
  line-height: 1.12;
}
.tt-themed a { color: var(--leather); text-decoration: none; }
.tt-themed a:hover { color: var(--deep-red); }
.tt-themed ::selection { background: rgba(181,138,54,.35); }

/* --- primitivas reutilizaveis --- */
.tt-themed .eyebrow {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: .26em;
  text-transform: uppercase;
  color: var(--text-faint);
}
.tt-themed .rule {
  border: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--edge-strong) 18%, var(--edge-strong) 82%, transparent);
  position: relative;
}
.tt-themed .mono { font-family: var(--font-mono); }
.tt-themed .swatch {
  border: 1.5px solid var(--ink);
  border-radius: var(--radius);
  box-shadow: var(--shadow-1);
}
.tt-themed .btn {
  font-family: var(--font-display);
  font-size: 13px;
  letter-spacing: .04em;
  color: var(--ink);
  background: var(--paper-0);
  border: 1.5px solid var(--ink);
  border-radius: var(--radius);
  padding: 8px 14px;
  cursor: pointer;
  box-shadow: var(--shadow-1);
  transition: transform .08s ease, background .15s ease, color .15s ease;
}
.tt-themed .btn:hover { background: var(--ink); color: var(--parchment); }
.tt-themed .btn:active { transform: translateY(1px); }

/* scrollbars no tom parchment */
.tt-themed * { scrollbar-width: thin; scrollbar-color: var(--edge-strong) transparent; }
.tt-themed *::-webkit-scrollbar { width: 10px; height: 10px; }
.tt-themed *::-webkit-scrollbar-thumb {
  background: var(--edge-strong);
  border-radius: 10px;
  border: 2px solid transparent;
  background-clip: padding-box;
}
.tt-themed *::-webkit-scrollbar-thumb:hover { background: var(--leather); }
.tt-themed *::-webkit-scrollbar-track { background: transparent; }

/* --- quadro imersivo: re-skin da nav/rodape globais SO na mesa --- */
.tt-themed .app-nav {
  background: var(--leather);
  color: var(--parchment);
  border-bottom: 3px double var(--ink);
}
.tt-themed .app-nav .brand-mark { color: var(--parchment); }
.tt-themed .app-nav .nav-link { color: rgba(239,230,210,.85); }
.tt-themed .app-nav .nav-link:hover,
.tt-themed .app-nav .nav-link.active {
  color: var(--parchment);
  border-color: var(--ochre);
}
.tt-themed .app-nav .nav-user { color: var(--parchment); }
.tt-themed .app-footer { color: var(--text-faint); }
```

- [ ] **Step 4: Adicionar o bloco `body_class` no `main.html`**

Em `dd3esheet/templates/main.html`, linha 22, trocar:

```html
<body class="sheet-body">
```

por:

```html
<body class="{% block body_class %}sheet-body{% endblock %}">
```

- [ ] **Step 5: Reescrever `base_tabletop.html` para ativar o tema**

Substituir **todo** o conteúdo de `dd3esheet/tabletop/templates/tabletop/base_tabletop.html` por:

```html
{% extends "main.html" %}
{% load static %}

{% block body_class %}sheet-body tt-themed paper-field{% endblock %}

{% block extra_head %}
    <link rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Spectral:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap">
    <link rel="stylesheet" href="{% static 'css/parchment-theme.css' %}?v={% now 'U' %}">
    <link rel="stylesheet" href="{% static 'css/tabletop.css' %}?v={% now 'U' %}">
{% endblock %}

{% block extra_js %}
    <script src="{% static 'js/tabletop.js' %}?v={% now 'U' %}"></script>
{% endblock %}
```

- [ ] **Step 6: Rodar o teste para confirmar que passa**

Run: `docker compose exec web python manage.py test tabletop.tests.ThemeTests -v 2`
Expected: PASS (1 teste OK).

- [ ] **Step 7: Commit**

```bash
git add dd3esheet/tabletop/tests.py dd3esheet/static/css/parchment-theme.css dd3esheet/templates/main.html dd3esheet/tabletop/templates/tabletop/base_tabletop.html
git commit -m "feat(mesa): tema Parchment & Ink compartilhado + ativacao imersiva"
```

---

## Task 2: Reescrever `tabletop.css` para consumir os tokens parchment

Substitui a paleta `--tt-*` viva pelos acentos da paleta e reveste todos os componentes. Sem teste novo: é puramente visual e a estrutura de markup/classes é preservada, então os 22 testes existentes + o teste-guarda da Task 1 cobrem a regressão funcional. A verificação de aparência é manual (Task 3).

**Files:**
- Modify: `dd3esheet/static/css/tabletop.css` (arquivo inteiro)

- [ ] **Step 1: Substituir todo o conteúdo de `tabletop.css`**

Substituir **todo** o conteúdo de `dd3esheet/static/css/tabletop.css` por:

```css
/* Mesa virtual (tabletop) — tema Parchment & Ink.
   Consome os tokens de parchment-theme.css (escopados em .tt-themed,
   sempre presente nas paginas da mesa). Convencao .tt-. */

.tt-themed {
    --tt-player: var(--steel-blue);
    --tt-enemy:  var(--deep-red);
    --tt-npc:    var(--iron);
    --tt-object: var(--leather);
    --tt-active: var(--ochre);
}

.tt-page {
    max-width: 1280px;
    margin: 0 auto;
    padding: var(--sp-3) clamp(8px, 3vw, 24px) 48px;
}

/* --- topo / botoes ------------------------------------------------------ */
.tt-topbar {
    display: flex;
    align-items: center;
    gap: var(--sp-3);
    flex-wrap: wrap;
    margin: var(--sp-2) 0 var(--sp-3);
}
.tt-title { margin: 0; font-family: var(--font-display); font-size: 1.6rem; flex: 1 1 auto; }
.tt-topbar__tools { display: flex; gap: 6px; flex-wrap: wrap; }
.tt-hint { color: var(--text-faint); font-style: italic; }

.tt-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 7px 13px;
    border: 1.5px solid var(--ink);
    border-radius: var(--radius);
    background: var(--paper-0);
    color: var(--ink);
    font-family: var(--font-display);
    font-size: 13px;
    letter-spacing: .04em;
    text-decoration: none;
    cursor: pointer;
    box-shadow: var(--shadow-1);
    transition: transform .08s ease, background .15s ease, color .15s ease;
}
.tt-btn:hover { background: var(--ink); color: var(--parchment); }
.tt-btn:active { transform: translateY(1px); }
.tt-btn--primary { background: var(--steel-blue); border-color: var(--ink); color: var(--parchment); }
.tt-btn--primary:hover { background: var(--royal-blue); color: var(--parchment); }
.tt-btn--danger { background: #f0dcd6; border-color: var(--deep-red); color: var(--deep-red); }
.tt-btn--danger:hover { background: var(--deep-red); color: var(--parchment); }
.tt-btn.is-active { background: var(--ochre); border-color: var(--ink); color: var(--ink); }

/* --- formularios simples ------------------------------------------------ */
.tt-create {
    display: flex;
    gap: var(--sp-2);
    flex-wrap: wrap;
    align-items: center;
    margin-bottom: var(--sp-4);
}
.tt-create input[type="text"], .tt-create select,
.tt-token-edit input, .tt-token-edit select,
.tt-token-add input, .tt-token-add select,
.tt-map-card__edit input, .tt-map-card__edit select {
    padding: 6px 9px;
    border: 1.5px solid var(--edge-strong);
    border-radius: var(--radius);
    background: var(--paper-0);
    color: var(--text);
    font: inherit;
}
.tt-file { display: inline-flex; flex-direction: column; font-size: .8rem; gap: 2px; }
.tt-inline { display: inline-flex; align-items: center; gap: 4px; font-size: .85rem; }
.tt-share { color: var(--text-soft); }
.tt-share__url { background: var(--paper-2); padding: 2px 6px; border-radius: var(--radius); word-break: break-all; }
.tt-empty { color: var(--text-faint); padding: 12px; }
.tt-help { font-size: .8rem; color: var(--text-faint); margin: 6px 0; }

/* --- listas (mesas / mapas) -------------------------------------------- */
.tt-table-list, .tt-map-list {
    list-style: none; padding: 0; margin: 0;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 10px;
}
.tt-table-card, .tt-map-card {
    border: 1.5px solid var(--edge-line);
    border-left-width: 4px;
    border-radius: var(--radius);
    padding: 10px 12px;
    background: var(--paper-0);
    box-shadow: var(--shadow-1);
}
.tt-map-card.is-active { border-left-color: var(--ochre); background: var(--paper-2); }
.tt-table-card__name, .tt-map-card__name { font-family: var(--font-display); font-weight: 600; color: var(--ink); }
.tt-table-card { display: flex; flex-direction: column; gap: 4px; }
.tt-table-card__link, .tt-map-card__meta { font-size: .82rem; color: var(--text-soft); }
.tt-map-card__head { display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap; }
.tt-map-card__actions { display: flex; gap: 6px; margin-top: 8px; flex-wrap: wrap; }
.tt-map-card__edit { margin-top: 8px; }
.tt-map-card__edit form { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; margin-top: 6px; }
.tt-badge { background: var(--ochre); color: var(--ink); font-size: .72rem; padding: 1px 6px; border-radius: 10px; }

/* --- palco e canvas ----------------------------------------------------- */
.tt-stage {
    overflow: auto;
    max-height: 78vh;
    border: 2px solid var(--ink);
    border-radius: var(--radius);
    background: var(--ink-soft);
    background-image:
        linear-gradient(45deg, rgba(0,0,0,.18) 25%, transparent 25%),
        linear-gradient(-45deg, rgba(0,0,0,.18) 25%, transparent 25%),
        linear-gradient(45deg, transparent 75%, rgba(0,0,0,.18) 75%),
        linear-gradient(-45deg, transparent 75%, rgba(0,0,0,.18) 75%);
    background-size: 24px 24px;
    background-position: 0 0, 0 12px, 12px -12px, -12px 0;
    box-shadow: var(--shadow-inset);
}
.tt-canvas {
    position: relative;
    margin: 0;
    user-select: none;
    touch-action: none;          /* drag por pointer sem scroll/zoom acidental */
    background: var(--paper-3);
}
.tt-canvas--empty {
    width: 100% !important;
    height: auto !important;
    min-height: 200px;
    display: grid;
    place-items: center;
    background: transparent;
    color: var(--bone);
}
.tt-canvas--empty .tt-empty { color: var(--bone); }
.tt-canvas--fogging { cursor: crosshair; }
.tt-canvas__bg {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: fill;
    display: block;
}
.tt-canvas__grid {
    position: absolute;
    inset: 0;
    pointer-events: none;
    background-image:
        repeating-linear-gradient(to right, rgba(43,38,34,.28) 0 1px, transparent 1px var(--tt-cell, 64px)),
        repeating-linear-gradient(to bottom, rgba(43,38,34,.28) 0 1px, transparent 1px var(--tt-cell, 64px));
}

/* --- tokens ------------------------------------------------------------- */
.tt-token {
    position: absolute;
    transform: translate(-50%, -50%);
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    color: var(--parchment);
    box-shadow: 0 0 0 2px var(--parchment), 0 1px 4px rgba(0,0,0,.5);
    box-sizing: border-box;
}
.tt-token--player { background: var(--tt-player); }
.tt-token--enemy  { background: var(--tt-enemy); }
.tt-token--npc    { background: var(--tt-npc); }
.tt-token--object { background: var(--tt-object); border-radius: 12%; }
.tt-token[data-movable="1"] { cursor: grab; }
.tt-token.is-dragging { cursor: grabbing; z-index: 50; box-shadow: 0 0 0 3px var(--ochre), 0 4px 12px rgba(0,0,0,.6); }
.tt-token.is-hidden { opacity: .45; outline: 2px dashed var(--parchment); }
.tt-token__img {
    width: 100%; height: 100%;
    object-fit: cover;
    border-radius: inherit;
    display: block;
    pointer-events: none;
}
.tt-token__svg { width: 60%; height: 60%; pointer-events: none; }
.tt-token__label {
    position: absolute;
    bottom: -16px;
    left: 50%;
    transform: translateX(-50%);
    white-space: nowrap;
    font-size: 11px;
    line-height: 1;
    color: var(--parchment);
    background: rgba(43,38,34,.78);
    padding: 1px 4px;
    border-radius: var(--radius);
    pointer-events: none;
}

/* --- nevoa -------------------------------------------------------------- */
.tt-fog {
    position: absolute;
    background: #14110e;           /* opaco p/ jogadores */
}
.tt-fog--owner {
    background: rgba(43,38,34,.42);
    outline: 1px dashed var(--ochre);
}
.tt-fog--drawing {
    position: absolute;
    background: rgba(43,38,34,.30);
    outline: 2px dashed var(--ochre);
    pointer-events: none;
}
.tt-fog__del {
    position: absolute;
    top: 2px; right: 2px;
    width: 18px; height: 18px;
    line-height: 14px;
    border: none;
    border-radius: var(--radius);
    background: rgba(43,38,34,.6);
    color: var(--parchment);
    cursor: pointer;
}

/* --- editor ------------------------------------------------------------- */
.tt-editor-grid {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 320px;
    gap: 12px;
    align-items: start;
}
.tt-editor-side { display: flex; flex-direction: column; gap: 12px; }
.tt-panel { border: 1.5px solid var(--edge-line); border-radius: var(--radius); padding: 10px 12px; background: var(--paper-0); box-shadow: var(--shadow-1); }
.tt-panel__title { margin: 0 0 8px; font-family: var(--font-display); font-size: 1rem; }
.tt-token-add { display: flex; flex-direction: column; gap: 6px; }
.tt-token-rows { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 6px; }
.tt-token-row { border: 1px solid var(--edge-line); border-left-width: 4px; border-radius: var(--radius); padding: 4px 8px; background: var(--paper-0); }
.tt-token-row--player { border-left-color: var(--tt-player); }
.tt-token-row--enemy  { border-left-color: var(--tt-enemy); }
.tt-token-row--npc    { border-left-color: var(--tt-npc); }
.tt-token-row--object { border-left-color: var(--tt-object); }
.tt-token-row summary { cursor: pointer; display: flex; gap: 6px; align-items: center; }
.tt-token-row__name { font-weight: 600; }
.tt-tag { font-size: .68rem; background: var(--paper-2); border-radius: 8px; padding: 0 6px; color: var(--text-soft); }
.tt-token-edit { display: flex; flex-direction: column; gap: 5px; margin-top: 6px; }
.tt-token-edit__actions { display: flex; gap: 6px; }

@media (max-width: 860px) {
    .tt-editor-grid { grid-template-columns: 1fr; }
}
```

- [ ] **Step 2: Rodar a suíte do app para confirmar que nada quebrou**

Run: `docker compose exec web python manage.py test tabletop -v 2`
Expected: PASS — todos os testes do app (23: os 22 originais + o `ThemeTests` da Task 1).

- [ ] **Step 3: Commit**

```bash
git add dd3esheet/static/css/tabletop.css
git commit -m "feat(mesa): reveste tabletop.css com os tokens Parchment & Ink"
```

---

## Task 3: Verificação final + nota nos docs

- [ ] **Step 1: Rodar a suíte inteira (garantir que o resto do app segue verde)**

Run: `docker compose exec web python manage.py test -v 1`
Expected: PASS — a suíte completa do projeto (a fatia A não toca em nenhum outro app; `character`, `sdr`, `initiative`, `sprites` seguem verdes).

- [ ] **Step 2: Verificação manual no navegador**

Subir o app (`docker compose up`) e abrir, logado como `jarza` / `P@ssw0rd`:
- `/mesa/` — lista de mesas em cards de papel; nav superior em couro (leather) com links parchment.
- Criar/abrir uma mesa → `/mesa/<slug>/manage` — cards de mapa, botões inked.
- Abrir o editor de uma cena → painéis de papel, inputs parchment, palco com mat escuro.
- Abrir `/mesa/<slug>/` (cena ao vivo) numa janela anônima — tokens com acentos da paleta (player azul-aço, inimigo vermelho, npc ferro, objeto couro), névoa em tom de tinta.
- Conferir que `/character/` (uma ficha qualquer) **continua** com o visual antigo (nav preta, sem parchment) — prova de que o tema é escopado.

Confirmar visualmente; se algo destoar, ajustar o CSS da tarefa correspondente e re-commitar.

- [ ] **Step 3: Nota curta no `TABLETOP.md`**

Em `TABLETOP.md`, na seção **## Frontend**, adicionar como primeiro item da lista (antes da linha `- static/css/tabletop.css`):

```markdown
- `static/css/parchment-theme.css` — tokens do design language "Parchment & Ink"
  (do `design_handoff_dnd_vtt/`), escopados sob `.tt-themed`. Carregado por
  `base_tabletop.html`, que põe `sheet-body tt-themed paper-field` no `<body>`
  (via `{% block body_class %}` do `main.html`) para um quadro imersivo que
  reveste também nav/rodapé só na mesa. Compartilhável com futuras telas.
```

- [ ] **Step 4: Commit**

```bash
git add TABLETOP.md
git commit -m "docs: registra o tema Parchment & Ink no TABLETOP.md"
```

---

## Self-Review (feito pelo autor do plano)

**1. Cobertura do spec:**
- "Tokens compartilhados escopados sob `.tt-themed`" → Task 1 Step 3. ✅
- "Quadro imersivo via classe no body, revestindo nav/rodapé" → Task 1 Steps 4-5 + regras `.tt-themed .app-nav/.app-footer` no Step 3. ✅
- "Fontes Spectral + JetBrains Mono via link escopado" → Task 1 Step 5. ✅
- "Mapeamento Kind→acento" → Task 2 Step 1 (bloco `.tt-themed { --tt-*: var(--...) }`). ✅
- "Restyle das 5 superfícies preservando markup" → Task 2 (todas as classes `.tt-*` usadas pelos templates `home/table_view/manage/editor` e partials estão cobertas). ✅
- "Teste-guarda + 22 testes verdes" → Task 1 (teste) + Task 2 Step 2 + Task 3 Step 1. ✅

**2. Placeholders:** nenhum TBD/TODO; todo CSS/HTML/teste está completo e literal.

**3. Consistência de tipos/nomes:** as classes `.tt-themed`, `.paper-field`, `parchment-theme.css` e os nomes de tokens (`--steel-blue`, `--deep-red`, `--iron`, `--leather`, `--ochre`, `--paper-0..3`, `--edge-line/strong`, `--ink`, `--parchment`, etc.) são idênticos entre a Task 1 (definição) e a Task 2 (consumo). O `--tt-cell` referenciado em `.tt-canvas__grid` é setado inline pelo `tabletop.js`/template existente (comportamento preservado, não muda nesta fatia).

**Observação de escopo:** grade continua quadrada (hexágono = fatia B); nenhuma mudança em models, views, urls ou JS.
