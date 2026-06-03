# Art Direction Spec — "art bible" gerada (Fatia E) — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) ou superpowers:executing-plans. Steps usam checkbox (`- [ ]`).

**Goal:** Trazer a tela **Art Direction Spec** do handoff: uma página "livro" tipografada, **gerada a partir dos dados do manifesto**, com capa, estilo da casa, paleta de 14 cores, regras de output, specs dos 8 tipos de asset, tabela de tamanho/footprint, o manifesto completo e um checklist de QA — no estilo Parchment & Ink.

**Architecture:** Página server-rendered, **dirigida por dados** (mesmas constantes/manifesto da fatia D, em `sprites/manifest_data.py`), de modo que a spec nunca diverge do manifesto. TOC fixo à esquerda com scroll-spy; conteúdo central. Reusa o tema da fatia A.

**Tech Stack:** Django 4.2 (view + template data-driven), JS vanilla leve (scroll-spy), `parchment-theme.css` (fatia A), testes `python manage.py test sprites`. Docker.

**Depende de:** Fatia A (tema) **e** Fatia D (`sprites/manifest_data.py` + manifesto). É a fatia mais barata se D já existe.

**Spec de origem:** `design_handoff_dnd_vtt/README.md` (seção "2. Art Direction Spec") + `app/spec-render.js`, `app/spec.css`, `app/specs.js` (STYLE/PALETTE/NEGATIVE/TYPE_SPECS/GROUPS/SIZE_BY_FOOTPRINT).

---

## ⚠️ Decisões assumidas — REVISAR antes de executar

1. **Conteúdo 100% data-driven** das constantes em `sprites/manifest_data.py` (paleta, princípios, regras, specs de tipo, tabela de tamanho) + `all_assets()`/`sections()` para o manifesto. Sem texto hardcoded no template que possa divergir do manifesto.
2. **Tela em `/sprites/estilo/`** com link **"Estilo"** no nav. `login_required` (ferramenta do mestre/ilustrador).
3. **Constantes de arte** (STYLE, PALETTE_STR, NEGATIVE, PRINCIPLES, TYPE_SPECS, SIZE_BY_FOOTPRINT, PALETTE) são portadas de `app/specs.js` para `manifest_data.py` (Python), fonte única compartilhada com a fatia D.

---

## Estrutura de arquivos

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `dd3esheet/sprites/manifest_data.py` | **Modificar** | Adicionar `PALETTE` (14), `PRINCIPLES`, `OUTPUT_RULES`, `TYPE_SPECS`, `SIZE_BY_FOOTPRINT`, `STYLE`/`NEGATIVE`, `footprint_feet()`. |
| `dd3esheet/sprites/views.py` | **Modificar** | View `art_spec` (monta o contexto data-driven). |
| `dd3esheet/sprites/urls.py` | **Modificar** | Rota `'estilo/'` → `art_spec`. |
| `dd3esheet/sprites/templates/sprites/art_spec.html` | **Criar** | A página "livro" (TOC + 8 seções). |
| `dd3esheet/static/css/sprite_spec.css` | **Criar** | Estilos (porta de `app/spec.css`, tokens parchment). |
| `dd3esheet/static/js/sprite_spec.js` | **Criar** | Scroll-spy do TOC. |
| `dd3esheet/templates/main.html` | **Modificar** | Link "Estilo" no nav. |
| `dd3esheet/sprites/tests.py` | **Modificar** | Testes das constantes + da view. |

---

## Task 1: Constantes de arte em `manifest_data.py` (TDD)

**Files:**
- Modify: `dd3esheet/sprites/manifest_data.py`
- Test: `dd3esheet/sprites/tests.py` (adicionar `ArtConstantsTests`)

- [ ] **Step 1: Teste que falha**

```python
class ArtConstantsTests(SimpleTestCase):
    def test_palette_has_14_colors(self):
        from sprites.manifest_data import PALETTE
        self.assertEqual(len(PALETTE), 14)
        self.assertTrue(all('hex' in c and 'name' in c for c in PALETTE))

    def test_type_specs_cover_eight_types(self):
        from sprites.manifest_data import TYPE_SPECS
        self.assertEqual(len(TYPE_SPECS), 8)
        self.assertIn('TABLETOP_TOKEN', TYPE_SPECS)

    def test_footprint_feet(self):
        from sprites.manifest_data import footprint_feet
        self.assertEqual(footprint_feet('2x2'), '10×10 ft')
        self.assertIsNone(footprint_feet(None))
```

- [ ] **Step 2: Rodar p/ confirmar que falha**

Run: `docker compose exec web python manage.py test sprites.tests.ArtConstantsTests -v 2`
Expected: FAIL (`ImportError: cannot import name 'PALETTE'`).

- [ ] **Step 3: Adicionar as constantes**

Em `dd3esheet/sprites/manifest_data.py`, adicionar (valores exatos de `design_handoff_dnd_vtt/app/specs.js` + `theme.css`):

```python
import re  # (se ainda não importado no topo)

STYLE = (
    "Warm parchment storybook style: digital illustration that looks hand-inked "
    "for a classic fantasy tabletop RPG sourcebook. Confident dark ink outlines of "
    "even medium weight, semi-flat cel shading with 2–3 tonal steps per color, "
    "subtle aged-paper grain, soft overhead lighting. Mood: heroic, readable, "
    "friendly, timeless."
)

NEGATIVE = (
    "No text, letters, numbers, labels, UI, frames, borders, watermarks, signatures, "
    "grids, token rings, base discs, health bars, or selection marks anywhere."
)

# 14 cores da paleta (nome, hex, uso) — de theme.css / specs.js
PALETTE = [
    {'name': 'Dark Ink', 'hex': '#2b2622', 'usage': 'contornos, texto'},
    {'name': 'Parchment', 'hex': '#efe6d2', 'usage': 'papel base'},
    {'name': 'Ochre', 'hex': '#c8923a', 'usage': 'destaque quente'},
    {'name': 'Leather', 'hex': '#7a4f2a', 'usage': 'couro/madeira'},
    {'name': 'Forest', 'hex': '#4f6b3a', 'usage': 'vegetação'},
    {'name': 'Iron', 'hex': '#6b6f73', 'usage': 'metal/pedra'},
    {'name': 'Deep Red', 'hex': '#8a2f28', 'usage': 'perigo/sangue'},
    {'name': 'Steel Blue', 'hex': '#3f6079', 'usage': 'água/aço'},
    {'name': 'Bone', 'hex': '#d6c6aa', 'usage': 'osso/claro'},
    {'name': 'Shadow Brown', 'hex': '#493628', 'usage': 'sombra'},
    {'name': 'Muted Gold', 'hex': '#b58a36', 'usage': 'ouro suave'},
    {'name': 'Arcane Teal', 'hex': '#2f6f6a', 'usage': 'magia'},
    {'name': 'Royal Blue', 'hex': '#314f7c', 'usage': 'nobreza/arcano'},
    {'name': 'Dull Violet', 'hex': '#5d4978', 'usage': 'sombrio/feérico'},
]

PRINCIPLES = [
    {'title': 'Inked & timeless', 'body': 'Contornos escuros confiantes, cel shading semi-plano, grão de papel sutil.'},
    {'title': 'Readable at size', 'body': 'Legível em miniatura na mesa; nada de detalhe que some a 32–96 px.'},
    {'title': 'Moderate palette', 'body': 'Saturação moderada da família de 14 cores; sem neon, pastel ou 3D plástico.'},
    {'title': 'No UI in art', 'body': 'Sem texto, molduras, anéis de base, grids ou marcas de UI dentro da imagem.'},
]

OUTPUT_RULES = [
    {'title': 'Arquivos separados', 'body': 'Um arquivo por asset; nome = id snake_case.'},
    {'title': 'Alpha correto', 'body': 'Tokens/props/ícones: PNG transparente. Mapas: PNG/WebP opaco full-bleed.'},
    {'title': 'Composição segura', 'body': 'Tokens circle-safe (detalhe no círculo inscrito). Map pieces tile-edge-to-edge.'},
    {'title': 'Sem grid desenhado', 'body': 'Mapas alinham ao grid invisível (64px=5ft / hex), mas não desenham linhas.'},
]

# 8 specs de tipo (canvas/alpha/regra) — de specs.js TYPE_SPECS
TYPE_SPECS = {
    'TABLETOP_TOKEN': {'label': 'Tabletop Token', 'canvas': '512×512', 'alpha': 'PNG transparente',
        'spec': 'Vista de cima ~60°, miniatura pintada. Um sujeito centralizado, circle-safe, sombra de contato pequena. Sem anel de base.'},
    'PROP_TOKEN': {'label': 'Prop Token', 'canvas': '512×512', 'alpha': 'PNG transparente',
        'spec': 'Vista de cima. Um objeto/prop centralizado com sombra de contato. Circle-safe salvo se intencionalmente retangular.'},
    'STATUS_MARKER': {'label': 'Status Marker', 'canvas': '256×256', 'alpha': 'PNG transparente',
        'spec': 'Pictograma simples; legível a 32×32. Sem texto/números.'},
    'CLASS_ICON': {'label': 'Class Icon', 'canvas': '512×512', 'alpha': 'PNG transparente',
        'spec': 'Emblema/silhueta de classe; legível a 96×96. Sem moldura, sem texto.'},
    'PORTRAIT': {'label': 'Portrait', 'canvas': '640×640', 'alpha': 'Fundo parchment opaco',
        'spec': 'Busto/meio-corpo no estilo inked sobre fundo parchment. Sem texto/moldura.'},
    'BATTLE_MAP': {'label': 'Battle Map', 'canvas': '2048×1536', 'alpha': 'Opaco, full bleed',
        'spec': 'Top-down em grid de 64px (1 célula=5ft) sem desenhar linhas. Sem tokens/texto.'},
    'CITY_OR_WORLD_MAP': {'label': 'City / World Map', 'canvas': '2048×1536', 'alpha': 'Opaco, full bleed',
        'spec': 'Cartografia top-down em parchment envelhecido. Sem nomes/texto/bússola.'},
    'MAP_PIECE': {'label': 'Map Piece (hex)', 'canvas': '512×512', 'alpha': 'PNG transparente',
        'spec': 'Bloco modular que tile em grid hex pointy-top (odd-r, 1 hex=5ft). NÃO circle-safe; preenche o hex borda a borda.'},
}

SIZE_BY_FOOTPRINT = {
    '1x1': 'Tiny – Medium', '2x1': 'Medium (longo)', '1x2': 'Medium (longo)',
    '2x2': 'Large', '3x3': 'Huge', '4x4': 'Gargantuan', '6x6': 'Colossal',
}


def footprint_feet(footprint):
    """'NxM' -> 'AxB ft' (×5); None/sem match -> None."""
    if not footprint:
        return None
    m = re.match(r'(\d+)x(\d+)', footprint)
    if not m:
        return None
    return f'{int(m.group(1)) * 5}×{int(m.group(2)) * 5} ft'
```

- [ ] **Step 4: Rodar o teste**

Run: `docker compose exec web python manage.py test sprites.tests.ArtConstantsTests -v 2`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add dd3esheet/sprites/manifest_data.py dd3esheet/sprites/tests.py
git commit -m "feat(sprites): constantes de art-direction (paleta/specs/regras) data-driven"
```

---

## Task 2: View + URL + template da spec (TDD)

**Files:**
- Modify: `dd3esheet/sprites/views.py`
- Modify: `dd3esheet/sprites/urls.py`
- Create: `dd3esheet/sprites/templates/sprites/art_spec.html`
- Test: `dd3esheet/sprites/tests.py` (adicionar `ArtSpecViewTests`)

- [ ] **Step 1: Teste que falha**

```python
class ArtSpecViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('a', password='x' * 12)
        self.client.force_login(self.user)

    def test_spec_page_is_data_driven(self):
        resp = self.client.get(reverse('sprites:art-spec'))
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn('tt-themed', html)       # tema (fatia A)
        self.assertIn('#c8923a', html)         # paleta (ochre) renderizada
        self.assertIn('Tabletop Token', html)  # spec de tipo renderizada

    def test_spec_requires_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse('sprites:art-spec')).status_code, 302)
```

- [ ] **Step 2: Rodar p/ confirmar que falha**

Run: `docker compose exec web python manage.py test sprites.tests.ArtSpecViewTests -v 2`
Expected: FAIL (`NoReverseMatch: 'art-spec'`).

- [ ] **Step 3: View + URL**

Em `dd3esheet/sprites/views.py`, adicionar:

```python
from .manifest_data import (
    PALETTE, PRINCIPLES, OUTPUT_RULES, TYPE_SPECS, SIZE_BY_FOOTPRINT,
    STYLE, NEGATIVE, sections, all_assets,
)


@login_required
def art_spec(request):
    return render(request, 'sprites/art_spec.html', {
        'style': STYLE,
        'negative': NEGATIVE,
        'palette': PALETTE,
        'principles': PRINCIPLES,
        'output_rules': OUTPUT_RULES,
        'type_specs': TYPE_SPECS,
        'size_by_footprint': SIZE_BY_FOOTPRINT,
        'sections': sections(),
        'total': len(all_assets()),
    })
```

Em `dd3esheet/sprites/urls.py`, adicionar:

```python
    path('estilo/', views.art_spec, name='art-spec'),
```

- [ ] **Step 4: Template (faz o teste passar; refine o estilo na Task 3)**

Criar `dd3esheet/sprites/templates/sprites/art_spec.html` com as 8 seções iterando o contexto. Mínimo para passar o teste (paleta + type specs renderizados):

```html
{% extends "main.html" %}
{% load static %}

{% block title %}Direção de Arte · Codex{% endblock %}
{% block body_class %}sheet-body tt-themed paper-field{% endblock %}

{% block extra_head %}
    <link rel="stylesheet" href="{% static 'css/parchment-theme.css' %}?v={% now 'U' %}">
    <link rel="stylesheet" href="{% static 'css/sprite_spec.css' %}?v={% now 'U' %}">
{% endblock %}

{% block content %}
<main class="ss-page" data-screen-label="art-spec">
    <section id="cover" class="ss-section">
        <p class="eyebrow">D&D 3.5 · Tabletop Set</p>
        <h1>Direção de Arte — Parchment &amp; Ink</h1>
        <p>{{ style }}</p>
        <p class="mono">{{ total }} assets</p>
    </section>

    <section id="palette" class="ss-section">
        <h2>Paleta</h2>
        <div class="ss-swatches">
            {% for c in palette %}
            <div class="ss-swatch">
                <span class="swatch" style="background:{{ c.hex }}; display:block; height:48px;"></span>
                <strong>{{ c.name }}</strong>
                <span class="mono">{{ c.hex }}</span>
                <span>{{ c.usage }}</span>
            </div>
            {% endfor %}
        </div>
    </section>

    <section id="principles" class="ss-section">
        <h2>Estilo da casa</h2>
        {% for p in principles %}<div class="ss-card"><h3>{{ p.title }}</h3><p>{{ p.body }}</p></div>{% endfor %}
    </section>

    <section id="rules" class="ss-section">
        <h2>Regras de output</h2>
        {% for r in output_rules %}<div class="ss-card"><h3>{{ r.title }}</h3><p>{{ r.body }}</p></div>{% endfor %}
    </section>

    <section id="types" class="ss-section">
        <h2>Specs por tipo de asset</h2>
        {% for key, t in type_specs.items %}
        <div class="ss-tspec">
            <h3>{{ t.label }}</h3>
            <p class="mono">{{ t.canvas }} · {{ t.alpha }}</p>
            <p>{{ t.spec }}</p>
        </div>
        {% endfor %}
    </section>

    <section id="sizes" class="ss-section">
        <h2>Tamanho &amp; footprint</h2>
        <table class="ss-table">
            <thead><tr><th>Footprint</th><th>Tamanho da criatura</th></tr></thead>
            <tbody>
            {% for fp, label in size_by_footprint.items %}<tr><td class="mono">{{ fp }}</td><td>{{ label }}</td></tr>{% endfor %}
            </tbody>
        </table>
    </section>

    <section id="manifest" class="ss-section">
        <h2>Manifesto completo</h2>
        {% for section in sections %}
        <h3>{{ section.name }}</h3>
        <ul class="ss-manifest">
            {% for a in section.assets %}
            <li><span class="mono">{{ a.id }}</span> · {{ a.footprint|default:'—' }} · {{ a.description }}</li>
            {% endfor %}
        </ul>
        {% endfor %}
    </section>

    <section id="qa" class="ss-section">
        <h2>Checklist de QA</h2>
        <ul>
            <li>Contornos inked, cel shading semi-plano, grão sutil.</li>
            <li>Tokens circle-safe; map pieces tile sem costura.</li>
            <li>Sem texto/UI/molduras/anéis de base na arte.</li>
            <li>Paleta da casa, saturação moderada.</li>
            <li>Nome do arquivo = id snake_case.</li>
        </ul>
        <p class="ss-neg">{{ negative }}</p>
    </section>
</main>
{% endblock %}

{% block extra_js %}
    <script src="{% static 'js/sprite_spec.js' %}?v={% now 'U' %}"></script>
{% endblock %}
```

- [ ] **Step 5: Rodar o teste**

Run: `docker compose exec web python manage.py test sprites.tests.ArtSpecViewTests -v 2`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add dd3esheet/sprites/views.py dd3esheet/sprites/urls.py dd3esheet/sprites/templates/sprites/art_spec.html dd3esheet/sprites/tests.py
git commit -m "feat(sprites): Art Direction Spec data-driven (paleta/specs/manifesto)"
```

---

## Task 3: Layout "livro" (TOC + scroll-spy) + estilo + nav

**Files:**
- Create: `dd3esheet/static/css/sprite_spec.css`
- Create: `dd3esheet/static/js/sprite_spec.js`
- Modify: `dd3esheet/sprites/templates/sprites/art_spec.html` (adicionar a coluna do TOC)
- Modify: `dd3esheet/templates/main.html` (link "Estilo")

- [ ] **Step 1: Estilo (`sprite_spec.css`)**

Portar `design_handoff_dnd_vtt/app/spec.css` consumindo os tokens parchment (fatia A): layout `grid-template-columns: 256px 1fr` (TOC fixo + coluna `max-width: 940px`), `.ss-swatches` grid de 14, `.ss-card`/`.ss-tspec`, `.ss-table` com regras hairline `--edge-line`, `.eyebrow`/`.mono`/`.rule` (já em `parchment-theme.css`).

- [ ] **Step 2: TOC + scroll-spy (`sprite_spec.js`)**

Adicionar uma `<nav class="ss-toc">` no template com links âncora para `#cover/#palette/#principles/#rules/#types/#sizes/#manifest/#qa`. `sprite_spec.js`: `IntersectionObserver` marca o item ativo do TOC conforme a seção entra na viewport (scroll-spy), espelhando `app/spec-render.js`.

- [ ] **Step 3: Link no nav**

Em `dd3esheet/templates/main.html`, após o link "Biblioteca" (fatia D), adicionar:

```html
        <a class="nav-link {% if request.resolver_match.url_name == 'art-spec' %}active{% endif %}"
           href="{% url 'sprites:art-spec' %}">Estilo</a>
```

- [ ] **Step 4: Verificação manual + commit**

Abrir `/sprites/estilo/`: página "livro" com TOC fixo que acompanha o scroll, paleta de 14 swatches, 8 cards de tipo, tabela de footprint e o manifesto completo. Confere visual parchment.

```bash
git add dd3esheet/static/css/sprite_spec.css dd3esheet/static/js/sprite_spec.js dd3esheet/sprites/templates/sprites/art_spec.html dd3esheet/templates/main.html
git commit -m "feat(sprites): layout livro + scroll-spy + nav da Art Direction Spec"
```

---

## Task 4: Suíte + docs

- [ ] **Step 1: Suíte**

Run: `docker compose exec web python manage.py test sprites -v 2` e `docker compose exec web python manage.py test -v 1`
Expected: PASS.

- [ ] **Step 2: Docs**

Atualizar `docs/architecture.md`/`AGENTS.md` citando a Art Direction Spec em `/sprites/estilo/` (gerada do manifesto). Commit.

```bash
git add docs/architecture.md AGENTS.md
git commit -m "docs: registra a Art Direction Spec (fatia E)"
```

---

## Self-Review (autor do plano)

**1. Cobertura vs. README "2. Art Direction Spec":** capa ✅ · estilo da casa (4 cards) ✅ · paleta 14 ✅ · regras de output ✅ · 8 specs de tipo ✅ · tabela tamanho/footprint ✅ · manifesto completo ✅ · checklist QA ✅ · TOC com scroll-spy ✅ · tudo data-driven (gerado de `manifest_data`) ✅.
**2. Placeholders:** view/constantes/template/teste literais; só a porta de CSS/scroll-spy (Task 3) referencia `app/spec.css`/`spec-render.js` como fonte concreta do handoff.
**3. Consistência:** `PALETTE`/`TYPE_SPECS`/`SIZE_BY_FOOTPRINT`/`footprint_feet`/`sections`/`all_assets` definidos em `manifest_data.py` (Task 1) e consumidos igual na view e nos testes; `sprites:art-spec` consistente em urls/nav/testes.

**Dependências:** A (tema) + D (`manifest_data.py` com `sections`/`all_assets` e o JSON do manifesto). Execute D antes de E. Se rodar E sem D, os imports de `sections`/`all_assets` falham.
