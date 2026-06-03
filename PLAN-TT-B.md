# Mesa Virtual — Grade Hexagonal pointy-top (Fatia B) — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans para implementar task-a-task. Steps usam checkbox (`- [ ]`).

**Goal:** Migrar a grade da mesa de quadrada (`square`) para **hexagonal pointy-top (odd-r)** em models, cálculos puros, JS de arrasto, render do canvas e testes, com leituras coerentes (1 hex = 1,5 m). Corresponde ao **item 10 do `TABLETOP.md`**.

**Architecture:** `GridMode` passa a ser `hex`/`free` (substitui `square`). A matemática hexagonal vive em funções puras testáveis (`tabletop/calculations.py`), espelhando o algoritmo axial/cube-round do handoff (`design_handoff_dnd_vtt/scene/scene.js`). `GridSize` = **largura visual do hexágono em px** (flat-to-flat horizontal); o raio é derivado `R = GridSize/√3`. O snap encaixa no centro do hexágono mais próximo. A grade é desenhada por um pequeno overlay `<canvas>` via JS (espelha `drawGrid` do handoff).

**Tech Stack:** Django 4.2 (models + migração de dados), Python puro (`math`), JS vanilla, `python manage.py test tabletop`. Roda no Docker (`docker compose exec web ...`).

**Depende de:** Fatia A (tema). Não bloqueia, mas assume o `tabletop.css`/`base_tabletop.html` já no estado da fatia A.

**Spec de origem:** `docs/superpowers/specs/2026-06-03-tabletop-parchment-theme-design.md` (tabela de fatias) + `TABLETOP.md` item 10 + `design_handoff_dnd_vtt/README.md` ("Geometry constants").

---

## Contexto e contratos

- **Constantes geométricas (do handoff, README "Geometry constants"):** pointy-top, axial↔pixel com cube-rounding. No handoff `HEXR=46` é o circumraio. Aqui o model guarda `GridSize` (largura visual, default 64), então **derivamos `R = GridSize / √3`**.
  - `axial→pixel`: `x = √3·R·(q + r/2)`, `y = 1.5·R·r`.
  - `pixel→axial`: `q = (√3/3·x − 1/3·y)/R`, `r = (2/3·y)/R`, depois cube-round.
- **`GridSize` = largura flat-to-flat** ⇒ `width = √3·R = GridSize`; `height = 2R`; espaçamento de coluna = `GridSize`; espaçamento de linha = `1.5R`.
- **Onde já se usa:** `tabletop/views.py::move_token` já chama `snap_to_grid(x, y, GridSize, GridMode)` (linha ~285) — só a função muda. `_clean_grid` (views.py linha ~32) valida o set de modos.
- **Migração de dados:** mapas existentes com `GridMode='square'` viram `'hex'`.

## Estrutura de arquivos

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `dd3esheet/tabletop/calculations.py` | **Modificar** | Adicionar `hex_dimensions`, `nearest_hex_center`, `_cube_round`; reescrever `snap_to_grid` (hex em vez de square). |
| `dd3esheet/tabletop/models.py:39-43` | **Modificar** | `GRID_CHOICES`: `square`→`hex`; default `HEX`. |
| `dd3esheet/tabletop/migrations/0003_square_to_hex.py` | **Criar** | Migração de schema (default) + dados (`square`→`hex`). |
| `dd3esheet/tabletop/views.py:32-33` | **Modificar** | `_clean_grid`: set válido `{HEX, FREE}`. |
| `dd3esheet/static/js/tabletop.js:13-16` | **Modificar** | `snap()` passa a encaixar no hexágono; adicionar `drawHexGrid()` e wire em load/afterSwap. |
| `dd3esheet/tabletop/templates/tabletop/partials/_canvas.html:15` | **Modificar** | Trocar o `<div class="tt-canvas__grid">` (square) por um `<canvas class="tt-canvas__hexgrid">` quando `GridMode=='hex'`. |
| `dd3esheet/static/css/tabletop.css` | **Modificar** | `.tt-canvas--square`→`.tt-canvas--hex`; estilo do overlay de grade hex. |
| `dd3esheet/tabletop/tests.py` | **Modificar** | Reescrever os testes de snap (hex) + testes de `hex_dimensions`/`nearest_hex_center`; teste da migração. |

---

## Task 1: Funções puras de hexágono (TDD)

**Files:**
- Test: `dd3esheet/tabletop/tests.py` (substituir a classe `CalcTests`)
- Modify: `dd3esheet/tabletop/calculations.py`

- [ ] **Step 1: Reescrever os testes puros**

Em `dd3esheet/tabletop/tests.py`: trocar o import da linha 10
```python
from .calculations import point_in_rect, snap_to_grid, token_visible_to
```
por
```python
from .calculations import (
    hex_dimensions, nearest_hex_center, point_in_rect, snap_to_grid, token_visible_to,
)
import math
```
E **substituir toda a classe `CalcTests`** (linhas ~33-54) por:

```python
class CalcTests(SimpleTestCase):
    def test_hex_dimensions_pointy_top(self):
        d = hex_dimensions(64)
        # R = 64/sqrt(3); largura flat-to-flat = GridSize
        self.assertAlmostEqual(d['radius'], 64 / math.sqrt(3), places=3)
        self.assertAlmostEqual(d['width'], 64, places=3)
        self.assertAlmostEqual(d['height'], 2 * 64 / math.sqrt(3), places=3)
        self.assertAlmostEqual(d['col_spacing'], 64, places=3)
        self.assertAlmostEqual(d['row_spacing'], 1.5 * 64 / math.sqrt(3), places=3)

    def test_nearest_hex_center_origin(self):
        # Perto da origem encaixa no centro do hex (0,0) = (0,0).
        self.assertEqual(nearest_hex_center(3, -2, 64), (0, 0))

    def test_nearest_hex_center_is_idempotent_on_a_center(self):
        # O centro de um hex deve mapear para ele mesmo.
        cx, cy = nearest_hex_center(120, 90, 64)
        self.assertEqual(nearest_hex_center(cx, cy, 64), (cx, cy))

    def test_snap_hex_returns_a_hex_center(self):
        # snap em modo hex == nearest_hex_center
        self.assertEqual(snap_to_grid(120, 90, 64, 'hex'), nearest_hex_center(120, 90, 64))

    def test_snap_free_is_identity(self):
        self.assertEqual(snap_to_grid(123, 77, 64, 'free'), (123, 77))

    def test_snap_without_size_is_identity(self):
        self.assertEqual(snap_to_grid(123, 77, 0, 'hex'), (123, 77))

    def test_point_in_rect(self):
        self.assertTrue(point_in_rect(50, 50, 0, 0, 100, 100))
        self.assertFalse(point_in_rect(150, 50, 0, 0, 100, 100))

    def test_visibility_owner_sees_everything(self):
        self.assertTrue(token_visible_to(_Tok(50, 50, hidden=True), [_Fog(0, 0, 100, 100)], True))

    def test_visibility_player_hidden_and_under_fog(self):
        self.assertFalse(token_visible_to(_Tok(10, 10, hidden=True), [], False))
        self.assertFalse(token_visible_to(_Tok(50, 50), [_Fog(0, 0, 100, 100)], False))
        self.assertTrue(token_visible_to(_Tok(500, 500), [_Fog(0, 0, 100, 100)], False))
```

- [ ] **Step 2: Rodar os testes p/ confirmar que falham**

Run: `docker compose exec web python manage.py test tabletop.tests.CalcTests -v 2`
Expected: FAIL — `ImportError`/`cannot import name 'hex_dimensions'`.

- [ ] **Step 3: Implementar as funções puras**

Substituir **toda** a função `snap_to_grid` em `dd3esheet/tabletop/calculations.py` (linhas 4-15) e adicionar as novas funções. O topo do arquivo passa a ser:

```python
"""Funções puras da mesa virtual — sem DB, testáveis com `SimpleTestCase`."""

import math


def hex_dimensions(grid_size):
    """Dimensões de um hexágono pointy-top cuja largura flat-to-flat = `grid_size`.

    `R = grid_size / √3` (circumraio). Retorna largura/altura do envelope e os
    espaçamentos de coluna (mesma linha) e de linha da grade odd-r.
    """
    size = float(grid_size)
    r = size / math.sqrt(3)
    return {
        'radius': r,
        'width': math.sqrt(3) * r,   # == grid_size
        'height': 2 * r,
        'col_spacing': math.sqrt(3) * r,
        'row_spacing': 1.5 * r,
    }


def _cube_round(q, r):
    """Arredonda coordenadas axiais fracionárias ao hexágono inteiro mais próximo."""
    x, z = q, r
    y = -x - z
    rx, ry, rz = round(x), round(y), round(z)
    dx, dy, dz = abs(rx - x), abs(ry - y), abs(rz - z)
    if dx > dy and dx > dz:
        rx = -ry - rz
    elif dy > dz:
        ry = -rx - rz
    else:
        rz = -rx - ry
    return rx, rz


def nearest_hex_center(x, y, grid_size):
    """Centro (px, inteiro) do hexágono pointy-top mais próximo de (x, y)."""
    r = float(grid_size) / math.sqrt(3)
    # pixel -> axial
    q = (math.sqrt(3) / 3 * x - 1.0 / 3 * y) / r
    rr = (2.0 / 3 * y) / r
    q, rr = _cube_round(q, rr)
    # axial -> pixel
    cx = math.sqrt(3) * r * (q + rr / 2)
    cy = 1.5 * r * rr
    return (round(cx), round(cy))


def snap_to_grid(x, y, grid_size, grid_mode):
    """Encaixa (x, y) no centro do hexágono mais próximo em modo 'hex'.

    Em modo 'free' (ou `grid_size` inválido) devolve as coordenadas inalteradas.
    Coordenadas são o centro do token em px do mapa.
    """
    if grid_mode == 'hex' and grid_size and grid_size > 0:
        return nearest_hex_center(x, y, grid_size)
    return (int(x), int(y))
```

(As funções `point_in_rect` e `token_visible_to` ficam como estão, logo abaixo.)

- [ ] **Step 4: Rodar os testes p/ confirmar que passam**

Run: `docker compose exec web python manage.py test tabletop.tests.CalcTests -v 2`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add dd3esheet/tabletop/calculations.py dd3esheet/tabletop/tests.py
git commit -m "feat(mesa): matematica de grade hexagonal pointy-top (funcoes puras)"
```

---

## Task 2: Model + migração square→hex

**Files:**
- Modify: `dd3esheet/tabletop/models.py:39-51`
- Modify: `dd3esheet/tabletop/views.py:32-33`
- Create: `dd3esheet/tabletop/migrations/0003_square_to_hex.py`
- Test: `dd3esheet/tabletop/tests.py` (adicionar `GridMigrationTests`)

- [ ] **Step 1: Atualizar o model `Map`**

Em `dd3esheet/tabletop/models.py`, substituir o bloco de choices/constantes (linhas 39-51) por:

```python
    HEX, FREE = 'hex', 'free'
    GRID_CHOICES = [
        (HEX, 'Hexagonal'),
        (FREE, 'Livre'),
    ]

    DEFAULT_WIDTH = 1600
    DEFAULT_HEIGHT = 1200

    Table = models.ForeignKey(GameTable, on_delete=models.CASCADE)
    Name = models.CharField(max_length=120, default='Novo Mapa')
    Order = models.PositiveSmallIntegerField(default=0)
    GridMode = models.CharField(max_length=8, choices=GRID_CHOICES, default=HEX)
```

(O campo `Background` e os demais seguem inalterados logo abaixo.)

- [ ] **Step 2: Atualizar `_clean_grid` na view**

Em `dd3esheet/tabletop/views.py`, substituir (linhas 32-33):

```python
def _clean_grid(value):
    return value if value in {Map.SQUARE, Map.FREE} else Map.SQUARE
```

por:

```python
def _clean_grid(value):
    return value if value in {Map.HEX, Map.FREE} else Map.HEX
```

- [ ] **Step 3: Criar a migração (schema + dados)**

Confirmar o número da última migração:
Run: `docker compose exec web ls dd3esheet/tabletop/migrations`
(Assume-se `0002_*` como última; se houver outra, ajustar `dependencies` abaixo.)

Criar `dd3esheet/tabletop/migrations/0003_square_to_hex.py`:

```python
from django.db import migrations, models


def square_to_hex(apps, schema_editor):
    Map = apps.get_model('tabletop', 'Map')
    Map.objects.filter(GridMode='square').update(GridMode='hex')


def hex_to_square(apps, schema_editor):
    Map = apps.get_model('tabletop', 'Map')
    Map.objects.filter(GridMode='hex').update(GridMode='square')


class Migration(migrations.Migration):

    dependencies = [
        ('tabletop', '0002_combatant_spriteasset'),
    ]

    operations = [
        migrations.AlterField(
            model_name='map',
            name='GridMode',
            field=models.CharField(
                max_length=8, default='hex',
                choices=[('hex', 'Hexagonal'), ('free', 'Livre')],
            ),
        ),
        migrations.RunPython(square_to_hex, hex_to_square),
    ]
```

> Nota: o nome do arquivo `0002_combatant_spriteasset` aparece no `git status` inicial; se o `ls` mostrar outra última migração do app `tabletop`, usar esse nome em `dependencies`.

- [ ] **Step 4: Teste da migração de dados + default**

Adicionar ao final de `dd3esheet/tabletop/tests.py`:

```python
class GridMigrationTests(TestCase):
    def test_new_map_defaults_to_hex(self):
        owner = User.objects.create_user('gm2', password='x' * 12)
        table = GameTable.objects.create(Owner=owner, Name='Mesa')
        m = Map.objects.create(Table=table, Name='Cena')
        self.assertEqual(m.GridMode, Map.HEX)
```

- [ ] **Step 5: Aplicar a migração e rodar os testes**

Run:
```bash
docker compose exec web python manage.py migrate tabletop
docker compose exec web python manage.py test tabletop.tests.GridMigrationTests -v 2
```
Expected: migração aplica sem erro; teste PASS.

- [ ] **Step 6: Commit**

```bash
git add dd3esheet/tabletop/models.py dd3esheet/tabletop/views.py dd3esheet/tabletop/migrations/0003_square_to_hex.py dd3esheet/tabletop/tests.py
git commit -m "feat(mesa): GridMode hex/free + migracao square->hex"
```

---

## Task 3: Snap hexagonal no JS de arrasto

**Files:**
- Modify: `dd3esheet/static/js/tabletop.js:13-16`

- [ ] **Step 1: Substituir a função `snap` por hex**

Em `dd3esheet/static/js/tabletop.js`, substituir (linhas 13-16):

```javascript
    function snap(x, y, mode, size) {
        if (mode !== 'square' || !size) return [Math.round(x), Math.round(y)];
        return [Math.floor(x / size) * size + (size >> 1), Math.floor(y / size) * size + (size >> 1)];
    }
```

por (espelha `nearest_hex_center` do backend; `R = size/√3`):

```javascript
    var SQ3 = Math.sqrt(3);
    function cubeRound(q, r) {
        var x = q, z = r, y = -x - z;
        var rx = Math.round(x), ry = Math.round(y), rz = Math.round(z);
        var dx = Math.abs(rx - x), dy = Math.abs(ry - y), dz = Math.abs(rz - z);
        if (dx > dy && dx > dz) rx = -ry - rz; else if (dy > dz) ry = -rx - rz; else rz = -rx - ry;
        return [rx, rz];
    }
    function snap(x, y, mode, size) {
        if (mode !== 'hex' || !size) return [Math.round(x), Math.round(y)];
        var R = size / SQ3;
        var a = cubeRound((SQ3 / 3 * x - 1 / 3 * y) / R, (2 / 3 * y) / R);
        var cx = SQ3 * R * (a[0] + a[1] / 2), cy = 1.5 * R * a[1];
        return [Math.round(cx), Math.round(cy)];
    }
```

- [ ] **Step 2: Verificar manualmente o arrasto**

Subir o app, abrir uma cena em modo hex, arrastar um token e soltar: deve encaixar no **centro de um hexágono** (não numa célula quadrada). O próximo poll (≤2s) confirma a posição vinda do servidor (que usa a mesma matemática — devem coincidir).

- [ ] **Step 3: Commit**

```bash
git add dd3esheet/static/js/tabletop.js
git commit -m "feat(mesa): snap hexagonal no arrasto de tokens (JS)"
```

---

## Task 4: Desenho da grade hexagonal no canvas

A grade quadrada era um `<div>` com `repeating-linear-gradient`. Para hexágonos, desenhamos com um overlay `<canvas>` via JS (espelha `drawGrid` hex do handoff, `scene.js:194-209`).

**Files:**
- Modify: `dd3esheet/tabletop/templates/tabletop/partials/_canvas.html:15`
- Modify: `dd3esheet/static/css/tabletop.css` (regra `.tt-canvas__grid` → `.tt-canvas__hexgrid`)
- Modify: `dd3esheet/static/js/tabletop.js` (adicionar `drawHexGrid` + wiring)

- [ ] **Step 1: Trocar o overlay no `_canvas.html`**

Em `dd3esheet/tabletop/templates/tabletop/partials/_canvas.html`, substituir a linha 15:

```html
    {% if map.ShowGrid and map.GridMode == 'square' %}<div class="tt-canvas__grid"></div>{% endif %}
```

por:

```html
    {% if map.ShowGrid and map.GridMode == 'hex' %}<canvas class="tt-canvas__hexgrid" data-hexgrid width="{{ map.WidthPx }}" height="{{ map.HeightPx }}"></canvas>{% endif %}
```

- [ ] **Step 2: Estilo do overlay no `tabletop.css`**

Em `dd3esheet/static/css/tabletop.css`, substituir a regra `.tt-canvas__grid { ... }` inteira (o bloco `repeating-linear-gradient`) por:

```css
.tt-canvas__hexgrid {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
}
```

- [ ] **Step 3: Desenhar a grade hex no JS**

Em `dd3esheet/static/js/tabletop.js`, adicionar antes do `})();` final:

```javascript
    function drawHexGrid(cv) {
        var size = parseInt(cv.parentElement.dataset.gridSize, 10) || 64;
        var R = size / SQ3, w = cv.width, h = cv.height;
        var g = cv.getContext('2d');
        g.clearRect(0, 0, w, h);
        g.strokeStyle = 'rgba(43,38,34,0.28)';
        g.lineWidth = 1;
        var rTop = -1, rBot = Math.ceil(h / (1.5 * R)) + 1;
        for (var r = rTop; r <= rBot; r++) {
            var qLeft = Math.floor((-(R * SQ3)) / (R * SQ3) - r / 2) - 1;
            var qRight = Math.ceil((w / (R * SQ3)) - r / 2) + 1;
            for (var q = qLeft; q <= qRight; q++) {
                var cx = SQ3 * R * (q + r / 2), cy = 1.5 * R * r;
                g.beginPath();
                for (var i = 0; i < 6; i++) {
                    var a = Math.PI / 180 * (60 * i - 30);
                    var px = cx + R * Math.cos(a), py = cy + R * Math.sin(a);
                    if (i === 0) g.moveTo(px, py); else g.lineTo(px, py);
                }
                g.closePath();
                g.stroke();
            }
        }
    }
    function drawAllHexGrids() {
        document.querySelectorAll('canvas[data-hexgrid]').forEach(drawHexGrid);
    }
    document.body.addEventListener('htmx:afterSwap', drawAllHexGrids);
    if (document.readyState !== 'loading') drawAllHexGrids();
    else document.addEventListener('DOMContentLoaded', drawAllHexGrids);
```

- [ ] **Step 4: Verificação manual**

Subir o app, abrir `/mesa/<slug>/` numa cena hex: deve aparecer a malha de hexágonos pointy-top sobre o fundo, alinhada ao snap do arrasto. Após cada poll (swap do `#tt-live`), a grade é redesenhada.

- [ ] **Step 5: Commit**

```bash
git add dd3esheet/tabletop/templates/tabletop/partials/_canvas.html dd3esheet/static/css/tabletop.css dd3esheet/static/js/tabletop.js
git commit -m "feat(mesa): desenha grade hexagonal pointy-top no canvas"
```

---

## Task 5: Suíte completa + docs

- [ ] **Step 1: Rodar a suíte do app e a geral**

Run:
```bash
docker compose exec web python manage.py test tabletop -v 2
docker compose exec web python manage.py test -v 1
```
Expected: PASS em ambos (todos os testes do `tabletop` + suíte geral).

- [ ] **Step 2: Marcar o item 10 no `TABLETOP.md`**

Em `TABLETOP.md`, na "Sequência de build", trocar:
```markdown
10. [ ] Migração da grade `square` para `hex` pointy-top em modelos, cálculos, CSS/JS e testes.
```
por:
```markdown
10. [x] Migração da grade `square` para `hex` pointy-top em modelos, cálculos, CSS/JS e testes.
```

- [ ] **Step 3: Commit**

```bash
git add TABLETOP.md
git commit -m "docs: marca item 10 (grade hexagonal) como concluido"
```

---

## Self-Review (autor do plano)

**1. Cobertura:** `GridMode` hex/free (Task 2) · `snap_to_grid` hex + `hex_dimensions` + `nearest_hex_center` (Task 1) · JS snap hex (Task 3) · render da grade hex (Task 4) · migração de dados (Task 2) · leitura métrica: 1 hex = 1,5 m é convenção exposta na UI da fatia C (régua); na fatia B a malha/encaixe hexagonal é o entregável. ✅
**2. Placeholders:** nenhum; todo código (Python/JS/HTML/CSS/migração/teste) é literal.
**3. Consistência:** a mesma matemática (`R = GridSize/√3`, axial↔pixel, cube-round) aparece idêntica no backend (`calculations.py`, Task 1) e no JS (`snap`/`drawHexGrid`, Tasks 3-4). `Map.HEX`/`Map.FREE` usados em models, view (`_clean_grid`), migração e teste batem.

**Observação:** se a última migração do app não for `0002_combatant_spriteasset`, ajustar `dependencies` da migração 0003 (Task 2 Step 3 já alerta e manda conferir via `ls`).
