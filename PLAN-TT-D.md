# Sprite Library — navegador do manifesto (Fatia D) — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) ou superpowers:executing-plans. Steps usam checkbox (`- [ ]`).

**Goal:** Trazer a tela **Sprite Library** do handoff: um navegador pesquisável/filtrável dos **496 assets** do manifesto, cada um como um **placeholder** (glifo de categoria) com gaveta de detalhe, no estilo Parchment & Ink, sobre o app `sprites`.

**Architecture:** O manifesto vira dados no app `sprites`: um módulo de config (`manifest_data.py`) + um comando que cria/atualiza `SpriteAsset` **placeholders** (sem imagem) idempotentemente. A tela é server-rendered (lista por categoria, chips de filtro, busca) reusando o endpoint `sprites:search`; a gaveta de detalhe mostra a spec do asset. Arte real (PNGs) entra depois mapeando `id → arquivo` (Slug já = id snake_case).

**Tech Stack:** Django 4.2 (management command + view + template), JS vanilla leve (filtros/gaveta), `parchment-theme.css` (fatia A), testes `python manage.py test sprites`. Docker.

**Depende de:** Fatia A (tokens/tema Parchment & Ink — a tela usa `tt-themed`).

**Spec de origem:** `design_handoff_dnd_vtt/README.md` (seção "1. Sprite Library") + `app/library.js`, `app/library.css`, `app/specs.js` (GROUPS/glyphs), `data/assets.js` (`window.SPRITE_DATA`, 496 assets).

---

## ⚠️ Decisões assumidas — REVISAR antes de executar

Fatia sem brainstorming dedicado. Confirme:

1. **Os 496 assets entram como `SpriteAsset` placeholders** (`OriginalImage` vazio, `Visibility=PUBLIC`, `Owner=None`), com `Slug = id` do manifesto (snake_case, futuro nome do arquivo). Idempotente por `Slug`.
2. **Mapa de tipo→categoria** (para reuso pela mesa e filtros): `TABLETOP_TOKEN`/`PROP_TOKEN`→`map_token`; `BATTLE_MAP`/`CITY_OR_WORLD_MAP`/`MAP_PIECE`→`map_tile`; `CLASS_ICON`→`class`; `PORTRAIT`→`character`; `STATUS_MARKER`→`generic`. (Ajuste se quiser categorias novas no `sprites`.)
3. **Footprint→`DefaultGridWidth/Height`**: parse `"NxM"`; `null`→1×1.
4. **Tela em `/sprites/`** (nova `home` do app sprites), com link **"Biblioteca"** no nav. Os endpoints JSON existentes (`search/`, `manifest/`) seguem.
5. **Glifos**: portar o set SVG de `app/specs.js` (`glyphRaw`/`glyph`) para um partial de template (iconografia de UI, não arte). Placeholders = forma (círculo/hex/retângulo) + glifo da categoria.

---

## Estrutura de arquivos

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `dd3esheet/sprites/fixtures/sprite_manifest.json` | **Criar** | Cópia do JSON de `design_handoff_dnd_vtt/data/assets.js` (só o objeto, sem o `window.SPRITE_DATA =`). |
| `dd3esheet/sprites/manifest_data.py` | **Criar** | Loader do JSON + `GROUPS`/`TYPE_SPECS`/mapas (tipo→categoria, footprint), funções puras. |
| `dd3esheet/sprites/management/commands/seed_sprite_library.py` | **Criar** | Cria/atualiza os 496 placeholders idempotentemente. |
| `dd3esheet/sprites/views.py` | **Modificar** | `library` (lista agrupada + filtros) + `asset_detail` (gaveta). |
| `dd3esheet/sprites/urls.py` | **Modificar** | `''`→`library`; `'<slug>/'`→`asset_detail`. |
| `dd3esheet/sprites/templates/sprites/library.html` + `partials/_card.html`, `_glyphs.html`, `_detail.html` | **Criar** | Tela + tiles + glifos + gaveta. |
| `dd3esheet/static/css/sprite_library.css` | **Criar** | Estilos (porta de `app/library.css`, consumindo tokens parchment). |
| `dd3esheet/static/js/sprite_library.js` | **Criar** | Filtros client-side + abrir/fechar gaveta. |
| `dd3esheet/templates/main.html` | **Modificar** | Link "Biblioteca" no nav. |
| `dd3esheet/sprites/tests.py` | **Modificar** | Testes do loader, do comando (count/categoria/idempotência) e da view. |

---

## Task 1: Dados do manifesto (`manifest_data.py`) — TDD

**Files:**
- Create: `dd3esheet/sprites/fixtures/sprite_manifest.json`
- Create: `dd3esheet/sprites/manifest_data.py`
- Test: `dd3esheet/sprites/tests.py` (adicionar `ManifestDataTests`)

- [ ] **Step 1: Gerar o JSON do manifesto**

Extrair o objeto JSON de `design_handoff_dnd_vtt/data/assets.js` (que começa com `window.SPRITE_DATA = ` e termina com `;`) para `dd3esheet/sprites/fixtures/sprite_manifest.json`. Comando (dentro do container ou host):

```bash
python - <<'PY'
import re, json, pathlib
src = pathlib.Path('design_handoff_dnd_vtt/data/assets.js').read_text(encoding='utf-8')
obj = src[src.index('{'): src.rindex('}') + 1]
data = json.loads(obj)
out = pathlib.Path('dd3esheet/sprites/fixtures/sprite_manifest.json')
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
print('assets:', data['total'], 'sections:', len(data['sections']))
PY
```
Expected: imprime `assets: 496 sections: ...`.

- [ ] **Step 2: Teste que falha**

Adicionar em `dd3esheet/sprites/tests.py`:

```python
class ManifestDataTests(SimpleTestCase):
    def test_loads_all_assets_flat(self):
        from sprites.manifest_data import all_assets
        rows = all_assets()
        self.assertEqual(len(rows), 496)
        self.assertTrue(all('id' in r and 'type' in r for r in rows))

    def test_category_for_type(self):
        from sprites.manifest_data import category_for_type
        self.assertEqual(category_for_type('TABLETOP_TOKEN'), 'map_token')
        self.assertEqual(category_for_type('BATTLE_MAP'), 'map_tile')
        self.assertEqual(category_for_type('MAP_PIECE'), 'map_tile')
        self.assertEqual(category_for_type('CLASS_ICON'), 'class')

    def test_footprint_to_grid(self):
        from sprites.manifest_data import footprint_to_grid
        self.assertEqual(footprint_to_grid('2x2'), (2, 2))
        self.assertEqual(footprint_to_grid(None), (1, 1))
```

(Garantir o import `from django.test import SimpleTestCase` no topo do arquivo de testes.)

- [ ] **Step 3: Rodar p/ confirmar que falha**

Run: `docker compose exec web python manage.py test sprites.tests.ManifestDataTests -v 2`
Expected: FAIL (`ModuleNotFoundError: sprites.manifest_data`).

- [ ] **Step 4: Implementar `manifest_data.py`**

Criar `dd3esheet/sprites/manifest_data.py`:

```python
"""Dados do manifesto Parchment & Ink (496 assets) + config de grupos/specs.

Fonte: design_handoff_dnd_vtt (data/assets.js, app/specs.js). Funções puras,
sem DB — consumidas pelo comando de seed, pela Sprite Library e pela Art Spec.
"""
import functools
import json
import re
from pathlib import Path

from .models import SpriteAsset

_MANIFEST_PATH = Path(__file__).resolve().parent / 'fixtures' / 'sprite_manifest.json'

# tipo do manifesto -> Category do SpriteAsset
TYPE_TO_CATEGORY = {
    'TABLETOP_TOKEN': SpriteAsset.MAP_TOKEN,
    'PROP_TOKEN': SpriteAsset.MAP_TOKEN,
    'BATTLE_MAP': SpriteAsset.MAP_TILE,
    'CITY_OR_WORLD_MAP': SpriteAsset.MAP_TILE,
    'MAP_PIECE': SpriteAsset.MAP_TILE,
    'CLASS_ICON': SpriteAsset.CLASS,
    'PORTRAIT': SpriteAsset.CHARACTER,
    'STATUS_MARKER': SpriteAsset.GENERIC,
}


@functools.lru_cache(maxsize=1)
def _manifest():
    return json.loads(_MANIFEST_PATH.read_text(encoding='utf-8'))


def all_assets():
    """Lista achatada de todos os assets, cada um com a seção de origem."""
    rows = []
    for section in _manifest()['sections']:
        for asset in section['assets']:
            row = dict(asset)
            row.setdefault('section', section['name'])
            rows.append(row)
    return rows


def sections():
    """As seções do manifesto, na ordem (para a tela agrupada)."""
    return _manifest()['sections']


def category_for_type(asset_type):
    return TYPE_TO_CATEGORY.get(asset_type, SpriteAsset.GENERIC)


def footprint_to_grid(footprint):
    """'NxM' -> (N, M); None/sem match -> (1, 1)."""
    if not footprint:
        return (1, 1)
    m = re.match(r'(\d+)x(\d+)', footprint)
    return (int(m.group(1)), int(m.group(2))) if m else (1, 1)
```

> Para as telas D/E, porte também `GROUPS` e `TYPE_SPECS` de `app/specs.js` para este módulo (constantes Python) quando precisar do agrupamento de exibição/acentos/glifos. A fatia E reusa este módulo.

- [ ] **Step 5: Rodar o teste**

Run: `docker compose exec web python manage.py test sprites.tests.ManifestDataTests -v 2`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add dd3esheet/sprites/fixtures/sprite_manifest.json dd3esheet/sprites/manifest_data.py dd3esheet/sprites/tests.py
git commit -m "feat(sprites): dados do manifesto Parchment & Ink (496 assets) + helpers"
```

---

## Task 2: Comando `seed_sprite_library` (TDD)

**Files:**
- Create: `dd3esheet/sprites/management/commands/seed_sprite_library.py`
- Test: `dd3esheet/sprites/tests.py` (adicionar `SeedLibraryTests`)

- [ ] **Step 1: Teste que falha**

Adicionar em `dd3esheet/sprites/tests.py`:

```python
class SeedLibraryTests(TestCase):
    def test_seed_creates_all_placeholders(self):
        from django.core.management import call_command
        call_command('seed_sprite_library')
        self.assertEqual(SpriteAsset.objects.count(), 496)
        # tipo -> categoria
        icon = SpriteAsset.objects.get(Slug='barbarian_class_icon')
        self.assertEqual(icon.Category, SpriteAsset.CLASS)
        token = SpriteAsset.objects.get(Slug='human_fighter_sword_shield')
        self.assertEqual(token.Category, SpriteAsset.MAP_TOKEN)

    def test_seed_is_idempotent(self):
        from django.core.management import call_command
        call_command('seed_sprite_library')
        call_command('seed_sprite_library')
        self.assertEqual(SpriteAsset.objects.count(), 496)

    def test_seed_sets_footprint(self):
        from django.core.management import call_command
        call_command('seed_sprite_library')
        ogre = SpriteAsset.objects.get(Slug='ogre')  # footprint 2x2
        self.assertEqual((ogre.DefaultGridWidth, ogre.DefaultGridHeight), (2, 2))
```

- [ ] **Step 2: Rodar p/ confirmar que falha**

Run: `docker compose exec web python manage.py test sprites.tests.SeedLibraryTests -v 2`
Expected: FAIL (`Unknown command: 'seed_sprite_library'`).

- [ ] **Step 3: Implementar o comando**

Criar `dd3esheet/sprites/management/commands/seed_sprite_library.py`:

```python
from django.core.management.base import BaseCommand

from sprites.manifest_data import all_assets, category_for_type, footprint_to_grid
from sprites.models import SpriteAsset


class Command(BaseCommand):
    help = 'Cria/atualiza placeholders SpriteAsset dos 496 assets do manifesto (idempotente).'

    def handle(self, *args, **options):
        created = updated = 0
        for asset in all_assets():
            gw, gh = footprint_to_grid(asset.get('footprint'))
            name = asset['id'].replace('_', ' ').title()
            obj, was_created = SpriteAsset.objects.update_or_create(
                Slug=asset['id'],
                defaults={
                    'Name': name,
                    'Category': category_for_type(asset['type']),
                    'AltText': asset.get('description', ''),
                    'Visibility': SpriteAsset.PUBLIC,
                    'DefaultGridWidth': gw,
                    'DefaultGridHeight': gh,
                    'IsActive': True,
                },
            )
            created += was_created
            updated += not was_created
        self.stdout.write(self.style.SUCCESS(f'Sprites: {created} criados, {updated} atualizados.'))
```

> Nota: `SpriteAsset.save()` gera `Slug` a partir do `Name` quando vazio; aqui passamos `Slug` explícito no lookup, então o `update_or_create` usa o id do manifesto como chave estável.

- [ ] **Step 4: Rodar o teste**

Run: `docker compose exec web python manage.py test sprites.tests.SeedLibraryTests -v 2`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add dd3esheet/sprites/management/commands/seed_sprite_library.py dd3esheet/sprites/tests.py
git commit -m "feat(sprites): comando seed_sprite_library (496 placeholders, idempotente)"
```

---

## Task 3: View + URL da biblioteca (TDD)

**Files:**
- Modify: `dd3esheet/sprites/views.py`
- Modify: `dd3esheet/sprites/urls.py`
- Create: `dd3esheet/sprites/templates/sprites/library.html`
- Test: `dd3esheet/sprites/tests.py` (adicionar `LibraryViewTests`)

- [ ] **Step 1: Teste que falha**

```python
class LibraryViewTests(TestCase):
    def setUp(self):
        from django.core.management import call_command
        call_command('seed_sprite_library')
        self.user = User.objects.create_user('u', password='x' * 12)
        self.client.force_login(self.user)

    def test_library_page_renders_with_theme(self):
        resp = self.client.get(reverse('sprites:library'))
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn('tt-themed', html)          # tema parchment (fatia A)
        self.assertIn('human_fighter_sword_shield', html)

    def test_library_requires_login(self):
        self.client.logout()
        resp = self.client.get(reverse('sprites:library'))
        self.assertEqual(resp.status_code, 302)   # redireciona p/ login
```

(Garantir imports `User`, `reverse`, `TestCase` no topo dos testes.)

- [ ] **Step 2: Rodar p/ confirmar que falha**

Run: `docker compose exec web python manage.py test sprites.tests.LibraryViewTests -v 2`
Expected: FAIL (`NoReverseMatch: 'library'`).

- [ ] **Step 3: View + URL**

Em `dd3esheet/sprites/views.py`, adicionar:

```python
from django.shortcuts import render

from .manifest_data import sections


@login_required
def library(request):
    assets = SpriteAsset.objects.active().visible_to(request.user).order_by('Category', 'Name')
    return render(request, 'sprites/library.html', {
        'sections': sections(),
        'assets': list(assets),
        'categories': SpriteAsset.CATEGORY_CHOICES,
    })
```

Em `dd3esheet/sprites/urls.py`, adicionar no topo de `urlpatterns`:

```python
    path('', views.library, name='library'),
```

- [ ] **Step 4: Template mínimo (faz o teste passar; refine no Step seguinte)**

Criar `dd3esheet/sprites/templates/sprites/library.html`:

```html
{% extends "main.html" %}
{% load static %}

{% block title %}Biblioteca de Sprites · Codex{% endblock %}
{% block body_class %}sheet-body tt-themed paper-field{% endblock %}

{% block extra_head %}
    <link rel="stylesheet" href="{% static 'css/parchment-theme.css' %}?v={% now 'U' %}">
    <link rel="stylesheet" href="{% static 'css/sprite_library.css' %}?v={% now 'U' %}">
{% endblock %}

{% block content %}
<main class="sl-page" data-screen-label="sprite-library">
    <header class="sl-top">
        <h1>Biblioteca de Sprites</h1>
        <input type="search" id="sl-search" class="sl-search" placeholder="Buscar por id ou descrição…">
    </header>
    <div class="sl-gallery">
        {% for asset in assets %}
            {% include "sprites/partials/_card.html" %}
        {% endfor %}
    </div>
</main>
{% endblock %}

{% block extra_js %}
    <script src="{% static 'js/sprite_library.js' %}?v={% now 'U' %}"></script>
{% endblock %}
```

Criar `dd3esheet/sprites/templates/sprites/partials/_card.html`:

```html
<button class="sl-card" data-id="{{ asset.Slug }}" data-cat="{{ asset.Category }}"
        data-desc="{{ asset.AltText }}" title="{{ asset.Slug }} — {{ asset.AltText }}">
    <span class="sl-slot sl-slot--{{ asset.Category }}">
        {% if asset.original_url %}<img src="{{ asset.original_url }}" alt="{{ asset.display_alt }}">{% endif %}
    </span>
    <span class="sl-id mono">{{ asset.Slug }}</span>
</button>
```

- [ ] **Step 5: Rodar o teste**

Run: `docker compose exec web python manage.py test sprites.tests.LibraryViewTests -v 2`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add dd3esheet/sprites/views.py dd3esheet/sprites/urls.py dd3esheet/sprites/templates/sprites/library.html dd3esheet/sprites/templates/sprites/partials/_card.html dd3esheet/sprites/tests.py
git commit -m "feat(sprites): tela Sprite Library (lista + busca) com tema parchment"
```

---

## Task 4: Filtros, gaveta de detalhe, glifos e estilo

Porta visual de `app/library.css`/`app/library.js`. Os placeholders mostram um **glifo de categoria** dentro de uma forma (círculo p/ tokens, hex p/ map pieces, retângulo p/ maps), conforme a "Card / slot shapes" do README.

**Files:**
- Create: `dd3esheet/sprites/templates/sprites/partials/_glyphs.html` (set SVG portado de `app/specs.js`)
- Create: `dd3esheet/sprites/templates/sprites/partials/_detail.html` (gaveta)
- Create: `dd3esheet/static/css/sprite_library.css`
- Create: `dd3esheet/static/js/sprite_library.js`
- Modify: `dd3esheet/sprites/views.py` (filtros por categoria + chips; opcional `asset_detail`)
- Modify: `dd3esheet/sprites/urls.py` (rota de detalhe se usada)
- Modify: `dd3esheet/templates/main.html` (link "Biblioteca")

- [ ] **Step 1: Glifos + formas**

Portar o set de glifos SVG de `design_handoff_dnd_vtt/app/specs.js` (`glyphRaw`/`glyph`) para `_glyphs.html` (um `{% with %}`/include que escolhe o glifo pela categoria do grupo). Mapear forma por categoria: `map_token`/`class`/`character`/`companion`/`monster`→círculo; `map_tile` (map_pieces)→hex; backgrounds→retângulo 4:3. Espelha "Card / slot shapes" do README (seção 1).

- [ ] **Step 2: Estilo (`sprite_library.css`)**

Portar `app/library.css` consumindo os tokens parchment (fatia A): galeria responsiva (`grid-template-columns: repeat(auto-fill, minmax(...))`), `.sl-slot--circle/-hex/-map`, gaveta lateral 440px sobre scrim, chips de filtro. Sem `:root` próprio — usar `var(--ochre)` etc. (escopados em `.tt-themed`, presente no body).

- [ ] **Step 3: Filtros + busca + gaveta (`sprite_library.js`)**

Porta de `app/library.js` (filtro client-side por id/descrição/categoria; abrir/fechar gaveta de detalhe). Modelo de filtro do README: busca casa `id` OU descrição; chips de categoria estreitam; densidade opcional. A gaveta usa os dados já no DOM (`data-*`) ou um fetch a `sprites:asset_detail`.

- [ ] **Step 4: Link no nav**

Em `dd3esheet/templates/main.html`, adicionar após o link "Mesa" (linha ~35):

```html
        <a class="nav-link {% if request.resolver_match.app_name == 'sprites' %}active{% endif %}"
           href="{% url 'sprites:library' %}">Biblioteca</a>
```

- [ ] **Step 5: Verificação manual + commit**

Subir o app (rodar `seed_sprite_library` se necessário), abrir `/sprites/`: galeria parchment, busca filtra, chips de categoria filtram, clicar num card abre a gaveta com a spec. Confirmar formas (círculo/hex/retângulo) por categoria.

```bash
git add dd3esheet/sprites/templates/sprites/partials/_glyphs.html dd3esheet/sprites/templates/sprites/partials/_detail.html dd3esheet/static/css/sprite_library.css dd3esheet/static/js/sprite_library.js dd3esheet/sprites/views.py dd3esheet/sprites/urls.py dd3esheet/templates/main.html
git commit -m "feat(sprites): filtros, gaveta de detalhe, glifos e estilo da Sprite Library"
```

---

## Task 5: Seed automático + suíte + docs

- [ ] **Step 1: Encadear no seed do projeto (opcional, recomendado)**

Se desejado, chamar `seed_sprite_library` dentro do fluxo de seed do `docker compose up`. O `command` do serviço `web` roda `migrate → seed → runserver` (ver AGENTS.md). Adicionar uma chamada a `call_command('seed_sprite_library')` no comando `seed` (em `character/management/commands/seed.py`) **ou** documentar que se roda à parte. (Decisão de produto — confirmar.)

- [ ] **Step 2: Suíte**

Run: `docker compose exec web python manage.py test sprites -v 2` e `docker compose exec web python manage.py test -v 1`
Expected: PASS.

- [ ] **Step 3: Docs**

Atualizar `docs/architecture.md` (app `sprites`) e `AGENTS.md` (linha do `sprites/`) citando a Sprite Library em `/sprites/` e o comando `seed_sprite_library`. Commit.

```bash
git add docs/architecture.md AGENTS.md dd3esheet/character/management/commands/seed.py
git commit -m "docs/seed: registra a Sprite Library e o seed do manifesto"
```

---

## Self-Review (autor do plano)

**1. Cobertura vs. README "1. Sprite Library":** ingestão dos 496 assets ✅ · navegador agrupado ✅ · busca (id/descrição) ✅ · chips de categoria ✅ · gaveta de detalhe ✅ · formas de slot (círculo/hex/map) ✅ · placeholders por glifo ✅ · id↔arquivo preservado (Slug=id) ✅.
**2. Placeholders:** Python/command/view/teste literais; a porta visual (CSS/JS/glifos, Task 4) referencia `app/library.css`/`.js`/`specs.js` como fonte concreta designada pelo handoff.
**3. Consistência:** `manifest_data` (`all_assets`/`category_for_type`/`footprint_to_grid`/`sections`) é usado igual no comando, na view e nos testes; `Slug=id` é a chave estável em seed e templates; `sprites:library` consistente em urls/nav/testes.

**Dependência:** requer a fatia A (a tela usa `tt-themed` + `parchment-theme.css`). Se A não estiver pronta, o teste `test_library_page_renders_with_theme` falha — execute A antes.
