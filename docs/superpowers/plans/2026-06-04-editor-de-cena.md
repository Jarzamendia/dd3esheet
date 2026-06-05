# Editor de Cena — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Substituir o editor de cena da Mesa (`/mesa/`) por uma versão fiel ao `design_handoff_editor_de_cena/` — editor hexagonal client-autoritativo com canvas, rails ricos, inspector, undo/redo e autosave; LiveStage imersivo read-only — reusando os modelos do app `tabletop` (evoluídos) e remapeando as cores do handoff para a paleta Parchment & Ink clara.

**Architecture:** A view do editor entrega um shell + a cena serializada em JSON; um módulo JS detém todo o estado, renderiza terreno/grade/névoa em `<canvas>` e tokens como overlay DOM, e persiste em lote (autosave debounced) por um endpoint transacional `scene/save`. A visão ao vivo usa o mesmo renderer em modo read-only, semeada por JSON e atualizada por polling. Matemática de hex vive em `calculations.py` (Python) e num espelho `hex.js` (cliente).

**Tech Stack:** Django 4.2 + HTMX + JS vanilla (ES modules-free, padrão do projeto: scripts globais), Canvas 2D, JSONField (sqlite/postgres), Pillow opcional. Testes: `django.test` (`SimpleTestCase`/`TestCase`).

**Convenções do projeto (ler antes):**
- Campos de model em PascalCase (ex.: `Faction`, `MaxHP`). Sem trailer `Co-Authored-By` nos commits (preferência do repo).
- TDD cobre **cálculos, serialização, permissões e roteamento HTMX** (AGENTS.md). Canvas/CSS/DOM não são unit-testados — verificação é manual via passos descritos.
- Rodar testes: `python manage.py test tabletop` a partir de `dd3esheet/` (onde fica `manage.py`). Confirmar o cwd no início.
- Tema: tokens Parchment em `static/css/parchment-theme.css` escopados em `.tt-themed`; chrome da mesa em `static/css/tabletop.css`. Páginas da mesa já têm `body.tt-themed tt-ficha paper-field`.
- Branch de trabalho: `feat/editor-de-cena` (já criada).

**Mapa de arquivos (criar / modificar):**

| Arquivo | Papel |
|---|---|
| `dd3esheet/tabletop/calculations.py` | +`hex_disk`, `hex_line`, `hex_distance`, `pixel_to_axial` |
| `dd3esheet/tabletop/terrains.py` | **novo** — paleta fixa de 9 terrenos (id/label/tipo/cor/slug) |
| `dd3esheet/tabletop/models.py` | `Token` (+Faction/HP/MaxHP/Size/Conditions); `TerrainCell` (+Terrain); **novo** `FogCell` |
| `dd3esheet/tabletop/migrations/0004_*.py` | schema + data migration (Kind→Faction, fog→fogcell, terrain key) |
| `dd3esheet/tabletop/serializers.py` | **novo** — `serialize_scene(map)`, `serialize_token`, `apply_scene_payload` |
| `dd3esheet/tabletop/views.py` | view `editor` (shell+JSON), `scene_save`, `live_fragment`→JSON, ajustes |
| `dd3esheet/tabletop/urls.py` | +`scene/save` |
| `dd3esheet/tabletop/calculations.py` (token_visible_to) | usar FogCell |
| `static/js/hex.js` | **novo** — espelho JS do hex math |
| `static/js/scene_state.js` | **novo** — estado da cena + undo/redo |
| `static/js/scene_canvas.js` | **novo** — renderer canvas (terreno/grade/névoa/câmera/régua) |
| `static/js/scene_editor.js` | **novo** — orquestra editor: ferramentas, rails, tokens DOM, autosave (substitui `tabletop_editor.js`) |
| `static/js/scene_live.js` | **novo** — LiveStage (read-only + utilidades) |
| `static/css/scene_editor.css` | **novo** — layout/components do handoff, cores via tokens Parchment |
| `tabletop/templates/tabletop/editor.html` | shell do editor (3 colunas, rails, `<script>` JSON) |
| `tabletop/templates/tabletop/partials/_rail_*.html` | parciais dos rails |
| `tabletop/templates/tabletop/table_view.html` | LiveStage |
| `dd3esheet/tabletop/tests.py` | testes de cada fase testável |

---

## Fase 1 — Hex math: portar `disk`, `line`, `distance`, `pixel_to_axial`

Base testável para pincel/flood-fill/régua, com paridade Python↔JS.

### Task 1.1: `hex_distance` (Python)

**Files:**
- Modify: `dd3esheet/tabletop/calculations.py`
- Test: `dd3esheet/tabletop/tests.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar em `tests.py`, dentro de `CalcTests`:

```python
    def test_hex_distance_axial(self):
        from .calculations import hex_distance
        self.assertEqual(hex_distance(0, 0, 0, 0), 0)
        self.assertEqual(hex_distance(0, 0, 3, 0), 3)
        self.assertEqual(hex_distance(0, 0, 0, 3), 3)
        # axial (2,-1) dista 2 da origem
        self.assertEqual(hex_distance(0, 0, 2, -1), 2)
        # simetria
        self.assertEqual(hex_distance(2, -1, 0, 0), 2)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python manage.py test tabletop.tests.CalcTests.test_hex_distance_axial`
Expected: FAIL com `ImportError: cannot import name 'hex_distance'`.

- [ ] **Step 3: Implementar**

Adicionar em `calculations.py`:

```python
def hex_distance(q1, r1, q2, r2):
    """Distância em hexes entre duas coordenadas axiais pointy-top."""
    dq = q1 - q2
    dr = r1 - r2
    return (abs(dq) + abs(dr) + abs(dq + dr)) // 2
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python manage.py test tabletop.tests.CalcTests.test_hex_distance_axial`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add dd3esheet/tabletop/calculations.py dd3esheet/tabletop/tests.py
git commit -m "feat(mesa): hex_distance axial em calculations"
```

### Task 1.2: `hex_disk` (Python)

**Files:** Modify `calculations.py`; Test `tests.py`.

- [ ] **Step 1: Teste que falha**

```python
    def test_hex_disk_radii(self):
        from .calculations import hex_disk
        self.assertEqual(len(hex_disk(0, 0, 0)), 1)   # só o centro
        self.assertEqual(len(hex_disk(0, 0, 1)), 7)
        self.assertEqual(len(hex_disk(0, 0, 2)), 19)
        self.assertEqual(len(hex_disk(0, 0, 3)), 37)
        # centro incluído
        self.assertIn((0, 0), hex_disk(0, 0, 1))
```

- [ ] **Step 2: Ver falhar**

Run: `python manage.py test tabletop.tests.CalcTests.test_hex_disk_radii`
Expected: FAIL (ImportError).

- [ ] **Step 3: Implementar**

```python
def hex_disk(q, r, radius):
    """Todos os hexes axiais a distância <= radius do centro (q, r)."""
    cells = []
    for dq in range(-radius, radius + 1):
        lo = max(-radius, -dq - radius)
        hi = min(radius, -dq + radius)
        for dr in range(lo, hi + 1):
            cells.append((q + dq, r + dr))
    return cells
```

- [ ] **Step 4: Ver passar** — `... test_hex_disk_radii` → PASS.
- [ ] **Step 5: Commit** — `git commit -am "feat(mesa): hex_disk (pincel) em calculations"`

### Task 1.3: `hex_line` (Python)

**Files:** Modify `calculations.py`; Test `tests.py`.

- [ ] **Step 1: Teste que falha**

```python
    def test_hex_line_no_gaps(self):
        from .calculations import hex_line, hex_distance
        line = hex_line(0, 0, 3, 0)
        self.assertEqual(line[0], (0, 0))
        self.assertEqual(line[-1], (3, 0))
        self.assertEqual(len(line), 4)  # distância 3 => 4 hexes inclusivos
        # passos diagonais não pulam hexes
        diag = hex_line(0, 0, 2, -1)
        self.assertEqual(len(diag), hex_distance(0, 0, 2, -1) + 1)
```

- [ ] **Step 2: Ver falhar** — FAIL (ImportError).
- [ ] **Step 3: Implementar**

```python
def _cube_lerp(a, b, t):
    return a + (b - a) * t


def hex_line(q1, r1, q2, r2):
    """Linha de hexes (inclusiva) de (q1,r1) a (q2,r2) via interpolação cúbica."""
    n = hex_distance(q1, r1, q2, r2)
    if n == 0:
        return [(q1, r1)]
    x1, z1 = q1, r1
    x2, z2 = q2, r2
    results = []
    for i in range(n + 1):
        t = i / n
        x = _cube_lerp(x1, x2, t)
        z = _cube_lerp(z1, z2, t)
        results.append(_cube_round(x, z))
    # dedup preservando ordem
    seen, out = set(), []
    for cell in results:
        if cell not in seen:
            seen.add(cell)
            out.append(cell)
    return out
```

- [ ] **Step 4: Ver passar** — PASS.
- [ ] **Step 5: Commit** — `git commit -am "feat(mesa): hex_line interpolada em calculations"`

### Task 1.4: `pixel_to_axial` (Python)

**Files:** Modify `calculations.py`; Test `tests.py`.

- [ ] **Step 1: Teste que falha**

```python
    def test_pixel_to_axial_roundtrip(self):
        from .calculations import pixel_to_axial, axial_to_pixel
        for q, r in [(0, 0), (3, -2), (-1, 4), (5, 5)]:
            x, y = axial_to_pixel(q, r, 64)
            self.assertEqual(pixel_to_axial(x, y, 64), (q, r))
```

- [ ] **Step 2: Ver falhar** — FAIL (ImportError).
- [ ] **Step 3: Implementar**

```python
def pixel_to_axial(x, y, grid_size):
    """Converte px de mundo para coordenada axial inteira (cube round)."""
    radius = float(grid_size) / math.sqrt(3)
    q = (math.sqrt(3) / 3 * x - 1.0 / 3 * y) / radius
    r = (2.0 / 3 * y) / radius
    return _cube_round(q, r)
```

- [ ] **Step 4: Ver passar** — PASS.
- [ ] **Step 5: Commit** — `git commit -am "feat(mesa): pixel_to_axial em calculations"`

### Task 1.5: Espelho `hex.js` (cliente)

**Files:** Create `dd3esheet/static/js/hex.js`. Sem teste unitário JS (não há runner JS no projeto); paridade garantida pelos testes Python e verificação manual via console no navegador.

- [ ] **Step 1: Criar o módulo**

```js
// hex.js — espelho de tabletop/calculations.py (pointy-top axial).
// Exposto em window.Hex para os outros scripts da mesa.
(function (global) {
  const SQRT3 = Math.sqrt(3);

  function cubeRound(q, r) {
    let x = q, z = r, y = -q - r;
    let rx = Math.round(x), ry = Math.round(y), rz = Math.round(z);
    const dx = Math.abs(rx - x), dy = Math.abs(ry - y), dz = Math.abs(rz - z);
    if (dx > dy && dx > dz) rx = -ry - rz;
    else if (dy > dz) ry = -rx - rz;
    else rz = -rx - ry;
    return [rx, rz];
  }
  function axialToPixel(q, r, size) {
    const radius = size / SQRT3;
    return [Math.round(SQRT3 * radius * (q + r / 2)), Math.round(1.5 * radius * r)];
  }
  function pixelToAxial(x, y, size) {
    const radius = size / SQRT3;
    const q = (SQRT3 / 3 * x - 1 / 3 * y) / radius;
    const r = (2 / 3 * y) / radius;
    return cubeRound(q, r);
  }
  function distance(q1, r1, q2, r2) {
    const dq = q1 - q2, dr = r1 - r2;
    return (Math.abs(dq) + Math.abs(dr) + Math.abs(dq + dr)) / 2;
  }
  function disk(q, r, radius) {
    const out = [];
    for (let dq = -radius; dq <= radius; dq++) {
      const lo = Math.max(-radius, -dq - radius);
      const hi = Math.min(radius, -dq + radius);
      for (let dr = lo; dr <= hi; dr++) out.push([q + dq, r + dr]);
    }
    return out;
  }
  function line(q1, r1, q2, r2) {
    const n = distance(q1, r1, q2, r2);
    if (n === 0) return [[q1, r1]];
    const out = [], seen = new Set();
    for (let i = 0; i <= n; i++) {
      const t = i / n;
      const [rq, rr] = cubeRound(q1 + (q2 - q1) * t, r1 + (r2 - r1) * t);
      const key = rq + ',' + rr;
      if (!seen.has(key)) { seen.add(key); out.push([rq, rr]); }
    }
    return out;
  }
  global.Hex = { SQRT3, cubeRound, axialToPixel, pixelToAxial, distance, disk, line, key: (q, r) => q + ',' + r };
})(window);
```

- [ ] **Step 2: Verificação manual** — servir o app; numa página da mesa abrir o console e rodar:

```js
Hex.disk(0,0,1).length === 7 && JSON.stringify(Hex.axialToPixel(3,-2,64))
```
Expected: `7`-length confirmado e o par de pixels igual ao retornado por `axial_to_pixel(3,-2,64)` no shell Python.

- [ ] **Step 3: Commit** — `git add dd3esheet/static/js/hex.js && git commit -m "feat(mesa): hex.js (espelho cliente do hex math)"`

---

## Fase 2 — Modelo + migração + paleta de terreno

### Task 2.1: Paleta de terreno `terrains.py`

**Files:** Create `dd3esheet/tabletop/terrains.py`; Test `tests.py`.

- [ ] **Step 1: Teste que falha**

```python
class TerrainPaletteTests(SimpleTestCase):
    def test_palette_has_nine_unique_keys(self):
        from .terrains import TERRAINS, TERRAIN_KEYS, DEFAULT_TERRAIN
        self.assertEqual(len(TERRAINS), 9)
        self.assertEqual(len(set(TERRAIN_KEYS)), 9)
        self.assertEqual(DEFAULT_TERRAIN, 'stone')
        self.assertIn('water', TERRAIN_KEYS)

    def test_solid_terrains_have_color_textured_have_slug(self):
        from .terrains import TERRAINS
        by_id = {t['id']: t for t in TERRAINS}
        self.assertEqual(by_id['water']['kind'], 'color')
        self.assertTrue(by_id['water']['color'].startswith('#'))
        self.assertEqual(by_id['dungeon']['kind'], 'texture')
        self.assertTrue(by_id['dungeon']['slug'])
```

- [ ] **Step 2: Ver falhar** — FAIL (ImportError).
- [ ] **Step 3: Implementar `terrains.py`**

```python
"""Paleta fixa de terrenos da Mesa (espelhada em scene_canvas.js).

`color` para fundos sólidos; `texture` referencia um SpriteAsset MAP_TILE pelo
Slug conhecido (semeado pelo seed_sprite_library). As cores são semânticas
(grama=verde, água=azul) e NÃO seguem o chrome Parchment.
"""

TERRAINS = [
    {'id': 'stone',   'label': 'Pedra',     'kind': 'color',   'color': '#d8d4ca'},
    {'id': 'dungeon', 'label': 'Masmorra',  'kind': 'texture', 'slug': 'terrain-dungeon', 'color': '#3a3340'},
    {'id': 'cobble',  'label': 'Calçada',   'kind': 'texture', 'slug': 'terrain-cobblestone', 'color': '#6d6660'},
    {'id': 'woods',   'label': 'Floresta',  'kind': 'texture', 'slug': 'terrain-woods', 'color': '#3f5230'},
    {'id': 'grass',   'label': 'Grama',     'kind': 'color',   'color': '#54692f'},
    {'id': 'dirt',    'label': 'Terra',     'kind': 'color',   'color': '#6a4d31'},
    {'id': 'water',   'label': 'Água',      'kind': 'color',   'color': '#2b5266'},
    {'id': 'sand',    'label': 'Areia',     'kind': 'color',   'color': '#bda468'},
    {'id': 'rock',    'label': 'Rocha',     'kind': 'color',   'color': '#363139'},
]

TERRAIN_KEYS = [t['id'] for t in TERRAINS]
DEFAULT_TERRAIN = 'stone'
TEXTURE_SLUGS = {t['slug']: t['id'] for t in TERRAINS if t['kind'] == 'texture'}


def is_valid_terrain(key):
    return key in TERRAIN_KEYS
```

- [ ] **Step 4: Ver passar** — `python manage.py test tabletop.tests.TerrainPaletteTests` → PASS.
- [ ] **Step 5: Commit** — `git add ... && git commit -m "feat(mesa): paleta fixa de terrenos (terrains.py)"`

### Task 2.2: Campos novos no `Token` + `FogCell` + `TerrainCell.Terrain`

**Files:** Modify `dd3esheet/tabletop/models.py`; Test `tests.py`.

- [ ] **Step 1: Teste que falha**

```python
class SceneModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('m', password='x')
        self.table = GameTable.objects.create(Owner=self.user, Name='T')
        self.map = Map.objects.create(Table=self.table, Name='C')

    def test_token_scene_fields_defaults(self):
        t = Token.objects.create(Map=self.map)
        self.assertEqual(t.Faction, Token.ENEMY_FACTION)
        self.assertEqual(t.Size, 'md')
        self.assertEqual(t.HP, 0)
        self.assertEqual(t.MaxHP, 0)
        self.assertEqual(t.Conditions, [])

    def test_fogcell_unique_per_map(self):
        from .models import FogCell
        FogCell.objects.create(Map=self.map, Q=1, R=2)
        with self.assertRaises(Exception):
            FogCell.objects.create(Map=self.map, Q=1, R=2)

    def test_terraincell_terrain_key(self):
        from .models import TerrainCell
        c = TerrainCell.objects.create(Map=self.map, Q=0, R=0, Terrain='grass')
        self.assertEqual(c.Terrain, 'grass')
```

- [ ] **Step 2: Ver falhar** — FAIL (campo/modelo inexistente).
- [ ] **Step 3: Implementar nos models**

Em `Token`, adicionar constantes e campos (após `KIND_CHOICES`):

```python
    PARTY, ALLY, NEUTRAL, ENEMY_FACTION = 'party', 'ally', 'neutral', 'enemy'
    FACTION_CHOICES = [
        (PARTY, 'Grupo'), (ALLY, 'Aliado'), (NEUTRAL, 'Neutro'), (ENEMY_FACTION, 'Inimigo'),
    ]
    SIZE_CHOICES = [('sm', 'Pequeno'), ('md', 'Médio'), ('lg', 'Grande'), ('xl', 'Enorme')]
```

E os campos (após `Kind`):

```python
    Faction = models.CharField(max_length=8, choices=FACTION_CHOICES, default=ENEMY_FACTION)
    HP = models.IntegerField(default=0)
    MaxHP = models.IntegerField(default=0)
    Size = models.CharField(max_length=2, choices=SIZE_CHOICES, default='md')
    Conditions = models.JSONField(default=list, blank=True)
```

Adicionar mapeamento de migração no model (usado pela data migration e por views):

```python
    KIND_TO_FACTION = {PLAYER: PARTY, ENEMY: ENEMY_FACTION, NPC: NEUTRAL, OBJECT: NEUTRAL}
```

Adicionar `TerrainCell.Terrain` (após `SpriteAsset`):

```python
    Terrain = models.CharField(max_length=16, default='stone')
```

Novo modelo `FogCell` no fim de `models.py`:

```python
class FogCell(models.Model):
    """Hex coberto por névoa (coords axiais). Substitui o FogRegion retangular."""

    Map = models.ForeignKey(Map, on_delete=models.CASCADE)
    Q = models.IntegerField()
    R = models.IntegerField()
    CreatedAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('CreatedAt',)
        constraints = [
            models.UniqueConstraint(fields=('Map', 'Q', 'R'), name='unique_fog_cell_per_map'),
        ]

    def __str__(self):
        return f'Fog {self.Q},{self.R}'
```

- [ ] **Step 4: Gerar migração de schema**

Run: `python manage.py makemigrations tabletop`
Expected: cria `0004_token_faction_fogcell_terrain.py` (ou nome similar) com AddField/CreateModel.

- [ ] **Step 5: Ver passar** — `python manage.py test tabletop.tests.SceneModelTests` → PASS.
- [ ] **Step 6: Commit** — `git add dd3esheet/tabletop/models.py dd3esheet/tabletop/migrations/0004_*.py dd3esheet/tabletop/tests.py && git commit -m "feat(mesa): Token faction/hp/size/conditions, FogCell, TerrainCell.Terrain"`

### Task 2.3: Data migration — Kind→Faction, FogRegion→FogCell, terrain default

**Files:** Create `dd3esheet/tabletop/migrations/0005_backfill_scene_data.py`; Test `tests.py`.

- [ ] **Step 1: Teste que falha** (testa a função pura de derivação, não a migração em si)

```python
class FactionDerivationTests(SimpleTestCase):
    def test_kind_to_faction_mapping(self):
        from .models import Token
        self.assertEqual(Token.KIND_TO_FACTION[Token.PLAYER], Token.PARTY)
        self.assertEqual(Token.KIND_TO_FACTION[Token.ENEMY], Token.ENEMY_FACTION)
        self.assertEqual(Token.KIND_TO_FACTION[Token.NPC], Token.NEUTRAL)
        self.assertEqual(Token.KIND_TO_FACTION[Token.OBJECT], Token.NEUTRAL)
```

- [ ] **Step 2: Ver falhar/passar** — `KIND_TO_FACTION` já existe (Task 2.2), então este teste passa direto; serve de guarda. Run: `python manage.py test tabletop.tests.FactionDerivationTests` → PASS.

- [ ] **Step 3: Escrever a data migration**

`0005_backfill_scene_data.py`:

```python
from django.db import migrations


def backfill(apps, schema_editor):
    Token = apps.get_model('tabletop', 'Token')
    FogRegion = apps.get_model('tabletop', 'FogRegion')
    FogCell = apps.get_model('tabletop', 'FogCell')
    TerrainCell = apps.get_model('tabletop', 'TerrainCell')
    kind_to_faction = {'player': 'party', 'enemy': 'enemy', 'npc': 'neutral', 'object': 'neutral'}

    for token in Token.objects.all():
        token.Faction = kind_to_faction.get(token.Kind, 'enemy')
        token.save(update_fields=['Faction'])

    # terreno sem chave -> 'stone'
    TerrainCell.objects.filter(Terrain='').update(Terrain='stone')

    # FogRegion (retângulos, px) -> não há conversão fiel para hexes sem o GridSize;
    # política: não migrar geometria; apenas garante que nenhuma cena fica "presa".
    # FogCell começa vazio; o mestre re-pinta névoa no novo editor.
    _ = (FogRegion, FogCell)


class Migration(migrations.Migration):
    dependencies = [('tabletop', '0004_token_faction_fogcell_terrain')]
    operations = [migrations.RunPython(backfill, migrations.RunPython.noop)]
```

> Nota de produto: névoa retangular antiga **não** é convertida (sem grade não há mapeamento fiel). Documentar em `docs/seeds.md`/known-issues que cenas pré-existentes perdem a névoa e precisam ser repintadas.

- [ ] **Step 4: Aplicar e validar**

Run: `python manage.py migrate tabletop`
Expected: aplica 0004 e 0005 sem erro.
Run: `python manage.py test tabletop` (suite inteira) — Expected: PASS (ajustar testes que usavam `Kind` se quebrarem).

- [ ] **Step 5: Commit** — `git add dd3esheet/tabletop/migrations/0005_*.py dd3esheet/tabletop/tests.py && git commit -m "feat(mesa): data migration Kind->Faction + terreno default"`

### Task 2.4: `token_visible_to` usa `FogCell`

**Files:** Modify `dd3esheet/tabletop/calculations.py`; Test `tests.py`.

- [ ] **Step 1: Teste que falha**

```python
class FogVisibilityTests(SimpleTestCase):
    def test_token_hidden_when_its_hex_is_fogged(self):
        from .calculations import token_hex_visible
        # token no hex (2,1); névoa cobre {(2,1)} => invisível p/ jogador
        self.assertFalse(token_hex_visible(2, 1, {(2, 1)}, is_owner=False))
        self.assertTrue(token_hex_visible(2, 1, {(0, 0)}, is_owner=False))
        self.assertTrue(token_hex_visible(2, 1, {(2, 1)}, is_owner=True))  # dono vê tudo
```

- [ ] **Step 2: Ver falhar** — FAIL (ImportError).
- [ ] **Step 3: Implementar** — adicionar em `calculations.py`:

```python
def token_hex_visible(q, r, fog_keys, is_owner):
    """Token (no hex q,r) visível? Dono vê tudo; jogador não vê hex em névoa."""
    if is_owner:
        return True
    return (q, r) not in fog_keys
```

> `token_visible_to` (px/Hidden) permanece para compat; a view passa a calcular o hex do token via `pixel_to_axial` e usar `token_hex_visible`. A integração entra na Fase 8 (serialização/views).

- [ ] **Step 4: Ver passar** — `python manage.py test tabletop.tests.FogVisibilityTests` → PASS.
- [ ] **Step 5: Commit** — `git commit -am "feat(mesa): visibilidade de token por hex de névoa (FogCell)"`

---

## Fase 3 — Serialização da cena (JSON contract)

Contrato único usado pelo shell do editor, pelo polling do live e pelo `scene/save`.

### Task 3.1: `serialize_scene` / `serialize_token`

**Files:** Create `dd3esheet/tabletop/serializers.py`; Test `tests.py`.

- [ ] **Step 1: Teste que falha**

```python
class SceneSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('m', password='x')
        self.table = GameTable.objects.create(Owner=self.user, Name='T')
        self.map = Map.objects.create(Table=self.table, Name='C', GridSize=64)

    def test_serialize_scene_shape(self):
        from .serializers import serialize_scene
        from .models import TerrainCell, FogCell
        Token.objects.create(Map=self.map, Label='Lúmen', Faction='party', HP=18, MaxHP=24,
                             Size='md', Conditions=['blessed'], X=0, Y=0)
        TerrainCell.objects.create(Map=self.map, Q=1, R=0, Terrain='grass')
        FogCell.objects.create(Map=self.map, Q=2, R=2)
        data = serialize_scene(self.map, is_owner=True)
        self.assertEqual(data['grid']['size'], 64)
        self.assertEqual(data['terrain'], [{'q': 1, 'r': 0, 'terrain': 'grass'}])
        self.assertEqual(data['fog'], [{'q': 2, 'r': 2}])
        tok = data['tokens'][0]
        self.assertEqual(tok['faction'], 'party')
        self.assertEqual(tok['hp'], 18)
        self.assertEqual(tok['conditions'], ['blessed'])
        self.assertIn('q', tok)  # hex derivado da posição px

    def test_live_serialize_hides_fogged_and_hidden(self):
        from .serializers import serialize_scene
        from .models import FogCell
        # token escondido não aparece p/ jogador
        Token.objects.create(Map=self.map, Hidden=True, X=0, Y=0)
        data = serialize_scene(self.map, is_owner=False)
        self.assertEqual(data['tokens'], [])
```

- [ ] **Step 2: Ver falhar** — FAIL (ImportError).
- [ ] **Step 3: Implementar `serializers.py`**

```python
"""Contrato JSON da cena: usado pelo shell do editor, pelo polling do live e
pelo endpoint scene/save (round-trip)."""
from .calculations import axial_to_pixel, pixel_to_axial
from .services import attach_sprites_to_tokens


def serialize_token(token, grid_size):
    q, r = pixel_to_axial(token.X, token.Y, grid_size) if grid_size else (0, 0)
    return {
        'id': token.id,
        'assetId': token.SpriteAsset_id,
        'spriteUrl': getattr(token, 'SpriteUrl', '') or '',
        'name': token.Label,
        'kind': token.Kind,
        'faction': token.Faction,
        'q': q, 'r': r,
        'hp': token.HP, 'maxHp': token.MaxHP,
        'conditions': token.Conditions or [],
        'size': token.Size,
        'rotation': token.Rotation,
        'hidden': token.Hidden,
        'movable': token.MovableByPlayers,
    }


def serialize_scene(m, is_owner):
    if m is None:
        return None
    grid_size = m.GridSize
    fog = list(m.fogcell_set.all())
    fog_keys = {(c.Q, c.R) for c in fog}

    tokens_qs = list(m.token_set.select_related('SpriteAsset').all())
    attach_sprites_to_tokens(tokens_qs)
    tokens = []
    for t in tokens_qs:
        q, r = pixel_to_axial(t.X, t.Y, grid_size) if grid_size else (0, 0)
        if not is_owner and (t.Hidden or (q, r) in fog_keys):
            continue
        tokens.append(serialize_token(t, grid_size))

    terrain = [{'q': c.Q, 'r': c.R, 'terrain': c.Terrain}
               for c in m.terraincell_set.all()]

    return {
        'mapId': m.id,
        'name': m.Name,
        'grid': {'size': grid_size, 'cols': _cols(m), 'rows': _rows(m), 'showGrid': m.ShowGrid},
        'background': m.Background.original_url if (m.Background and m.Background.original_url) else '',
        'terrain': terrain,
        'fog': [{'q': c.Q, 'r': c.R} for c in fog] if is_owner else [{'q': c.Q, 'r': c.R} for c in fog],
        'isOwner': is_owner,
    } | {'tokens': tokens}


def _cols(m):
    return max(8, round(m.WidthPx / m.GridSize)) if m.GridSize else 30


def _rows(m):
    return max(6, round(m.HeightPx / m.GridSize)) if m.GridSize else 22
```

> No live, `fog` é enviado (o renderer usa para desenhar névoa opaca); tokens em névoa já foram filtrados acima. Para o jogador, a presença das células de névoa é pública (ele vê a névoa), o que é o comportamento desejado.

- [ ] **Step 4: Ver passar** — `python manage.py test tabletop.tests.SceneSerializerTests` → PASS.
- [ ] **Step 5: Commit** — `git add dd3esheet/tabletop/serializers.py dd3esheet/tabletop/tests.py && git commit -m "feat(mesa): serialize_scene (contrato JSON da cena)"`

### Task 3.2: `apply_scene_payload` (round-trip do autosave)

**Files:** Modify `dd3esheet/tabletop/serializers.py`; Test `tests.py`.

- [ ] **Step 1: Teste que falha**

```python
class ApplyScenePayloadTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('m', password='x')
        self.table = GameTable.objects.create(Owner=self.user, Name='T')
        self.map = Map.objects.create(Table=self.table, Name='C', GridSize=64)

    def test_apply_replaces_terrain_and_fog_and_upserts_tokens(self):
        from .serializers import apply_scene_payload
        from .models import TerrainCell, FogCell
        payload = {
            'name': 'Cripta',
            'grid': {'cols': 30, 'rows': 22},
            'terrain': [{'q': 0, 'r': 0, 'terrain': 'grass'}, {'q': 1, 'r': 0, 'terrain': 'water'}],
            'fog': [{'q': 5, 'r': 5}],
            'tokens': [{'tempId': 'n1', 'name': 'Orc', 'faction': 'enemy', 'q': 2, 'r': 1,
                        'hp': 10, 'maxHp': 12, 'size': 'md', 'conditions': [], 'kind': 'enemy'}],
        }
        apply_scene_payload(self.map, payload)
        self.map.refresh_from_db()
        self.assertEqual(self.map.Name, 'Cripta')
        self.assertEqual(TerrainCell.objects.filter(Map=self.map).count(), 2)
        self.assertEqual(FogCell.objects.filter(Map=self.map).count(), 1)
        self.assertEqual(Token.objects.filter(Map=self.map, Label='Orc').count(), 1)

    def test_apply_deletes_tokens_absent_from_payload(self):
        from .serializers import apply_scene_payload
        existing = Token.objects.create(Map=self.map, Label='Some')
        apply_scene_payload(self.map, {'tokens': [], 'terrain': [], 'fog': []})
        self.assertFalse(Token.objects.filter(id=existing.id).exists())
```

- [ ] **Step 2: Ver falhar** — FAIL (ImportError).
- [ ] **Step 3: Implementar** — adicionar em `serializers.py`:

```python
from django.db import transaction
from .calculations import axial_to_pixel, snap_to_grid
from .models import FogCell, TerrainCell, Token
from .terrains import is_valid_terrain, DEFAULT_TERRAIN

_VALID_FACTIONS = {Token.PARTY, Token.ALLY, Token.NEUTRAL, Token.ENEMY_FACTION}
_VALID_SIZES = {'sm', 'md', 'lg', 'xl'}
MAX_CELLS = 6000
MAX_TOKENS = 400


def _clean_conditions(value):
    return [c for c in (value or []) if isinstance(c, str)][:6]


@transaction.atomic
def apply_scene_payload(m, payload):
    """Aplica a cena inteira (last-write-wins do mestre)."""
    if 'name' in payload and isinstance(payload['name'], str) and payload['name'].strip():
        m.Name = payload['name'].strip()[:120]
    grid = payload.get('grid') or {}
    # cols/rows -> dimensões px (mantém GridSize atual)
    cols = _clamp(grid.get('cols'), 8, 80)
    rows = _clamp(grid.get('rows'), 6, 60)
    if cols and rows and m.GridSize:
        m.WidthPx = cols * m.GridSize
        m.HeightPx = rows * m.GridSize
    m.save()

    # terreno: replace
    TerrainCell.objects.filter(Map=m).delete()
    cells = []
    for c in (payload.get('terrain') or [])[:MAX_CELLS]:
        key = c.get('terrain')
        if not is_valid_terrain(key):
            key = DEFAULT_TERRAIN
        cells.append(TerrainCell(Map=m, Q=int(c['q']), R=int(c['r']), Terrain=key))
    TerrainCell.objects.bulk_create(cells, ignore_conflicts=True)

    # névoa: replace
    FogCell.objects.filter(Map=m).delete()
    fog = [FogCell(Map=m, Q=int(c['q']), R=int(c['r'])) for c in (payload.get('fog') or [])[:MAX_CELLS]]
    FogCell.objects.bulk_create(fog, ignore_conflicts=True)

    # tokens: upsert por id; deleta os ausentes
    incoming = (payload.get('tokens') or [])[:MAX_TOKENS]
    keep_ids = set()
    for i, td in enumerate(incoming):
        keep_ids |= _upsert_token(m, td, order=i)
    Token.objects.filter(Map=m).exclude(id__in=keep_ids).delete()


def _upsert_token(m, td, order):
    q, r = int(td.get('q', 0)), int(td.get('r', 0))
    x, y = axial_to_pixel(q, r, m.GridSize) if m.GridSize else (0, 0)
    faction = td.get('faction') if td.get('faction') in _VALID_FACTIONS else Token.ENEMY_FACTION
    size = td.get('size') if td.get('size') in _VALID_SIZES else 'md'
    fields = dict(
        Label=(td.get('name') or '')[:80],
        Kind=td.get('kind') if td.get('kind') in {'player', 'enemy', 'npc', 'object'} else 'enemy',
        Faction=faction, Size=size,
        HP=int(td.get('hp', 0)), MaxHP=int(td.get('maxHp', 0)),
        Conditions=_clean_conditions(td.get('conditions')),
        Rotation=(int(td.get('rotation', 0)) % 360),
        Hidden=bool(td.get('hidden', False)),
        MovableByPlayers=bool(td.get('movable', False)),
        X=x, Y=y, Order=order,
    )
    sprite_id = td.get('assetId')
    if sprite_id:
        fields['SpriteAsset_id'] = sprite_id
    tid = td.get('id')
    if tid:
        updated = Token.objects.filter(Map=m, id=tid).update(**fields)
        if updated:
            return {tid}
    created = Token.objects.create(Map=m, **fields)
    return {created.id}


def _clamp(v, lo, hi):
    try:
        return max(lo, min(hi, int(v)))
    except (TypeError, ValueError):
        return None
```

- [ ] **Step 4: Ver passar** — `python manage.py test tabletop.tests.ApplyScenePayloadTests` → PASS.
- [ ] **Step 5: Commit** — `git commit -am "feat(mesa): apply_scene_payload (round-trip do autosave)"`

---

## Fase 4 — Endpoints: `scene/save`, editor shell, live JSON

### Task 4.1: View `scene_save` + rota

**Files:** Modify `dd3esheet/tabletop/views.py`, `urls.py`; Test `tests.py`.

- [ ] **Step 1: Teste que falha**

```python
class SceneSaveViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('m', password='x')
        self.other = User.objects.create_user('o', password='x')
        self.table = GameTable.objects.create(Owner=self.user, Name='T')
        self.map = Map.objects.create(Table=self.table, Name='C', GridSize=64)

    def test_owner_can_save_scene(self):
        self.client.force_login(self.user)
        url = reverse('tabletop:scene-save', args=[self.table.Slug, self.map.id])
        resp = self.client.post(url, data={'scene': '{"terrain":[{"q":0,"r":0,"terrain":"grass"}],"fog":[],"tokens":[]}'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.map.terraincell_set.count(), 1)

    def test_non_owner_forbidden(self):
        self.client.force_login(self.other)
        url = reverse('tabletop:scene-save', args=[self.table.Slug, self.map.id])
        resp = self.client.post(url, data={'scene': '{"terrain":[],"fog":[],"tokens":[]}'})
        self.assertEqual(resp.status_code, 403)
```

- [ ] **Step 2: Ver falhar** — FAIL (rota inexistente → `NoReverseMatch`).
- [ ] **Step 3: Implementar**

Em `urls.py`, adicionar:

```python
    path('<slug:slug>/map/<int:mid>/scene/save', views.scene_save, name='scene-save'),
```

Em `views.py`, importar e adicionar a view:

```python
import json
from django.http import JsonResponse
from .serializers import apply_scene_payload, serialize_scene


@require_POST
def scene_save(request, slug, mid):
    table = _get_owned(request, slug)  # 403 se não for dono
    m = get_object_or_404(Map, id=mid, Table=table)
    try:
        payload = json.loads(request.POST.get('scene') or request.body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'json'}, status=400)
    apply_scene_payload(m, payload)
    table.save()  # bumpa UpdatedAt (versão p/ polling)
    return JsonResponse({'ok': True, 'savedAt': table.UpdatedAt.isoformat()})
```

- [ ] **Step 4: Ver passar** — `python manage.py test tabletop.tests.SceneSaveViewTests` → PASS.
- [ ] **Step 5: Commit** — `git add dd3esheet/tabletop/views.py dd3esheet/tabletop/urls.py dd3esheet/tabletop/tests.py && git commit -m "feat(mesa): endpoint scene/save (autosave transacional)"`

### Task 4.2: View `editor` entrega shell + JSON; `live_fragment` vira JSON

**Files:** Modify `dd3esheet/tabletop/views.py`; Test `tests.py`.

- [ ] **Step 1: Teste que falha**

```python
class EditorShellTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('m', password='x')
        self.table = GameTable.objects.create(Owner=self.user, Name='T')
        self.map = Map.objects.create(Table=self.table, Name='C', GridSize=64)
        self.table.ActiveMap = self.map
        self.table.save()

    def test_editor_embeds_scene_json(self):
        self.client.force_login(self.user)
        resp = self.client.get(reverse('tabletop:editor', args=[self.table.Slug, self.map.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'id="tt-scene-data"')
        self.assertContains(resp, 'data-rich-editor="2"')

    def test_live_fragment_returns_json(self):
        resp = self.client.get(reverse('tabletop:live-fragment', args=[self.table.Slug]))
        self.assertEqual(resp['Content-Type'], 'application/json')
        import json as _j
        body = _j.loads(resp.content)
        self.assertIn('tokens', body)
        self.assertIn('terrain', body)
```

- [ ] **Step 2: Ver falhar** — FAIL.
- [ ] **Step 3: Implementar** — substituir `editor` e `live_fragment` em `views.py`:

```python
def editor(request, slug, mid):
    table = _get_owned(request, slug)
    m = get_object_or_404(Map, id=mid, Table=table)
    scene = serialize_scene(m, is_owner=True)
    return render(request, 'tabletop/editor.html', {
        'table': table, 'map': m, 'slug': table.Slug,
        'scene_json': json.dumps(scene),
        'token_sprites': _sprite_library(request.user, TOKEN_LIBRARY_CATEGORIES),
        'terrains_json': json.dumps(_terrain_palette_payload(request.user)),
        'scene_save_url': reverse('tabletop:scene-save', args=[table.Slug, m.id]),
    })


def live_fragment(request, slug):
    table = get_object_or_404(GameTable, Slug=slug)
    is_owner = _is_owner(request, table)
    scene = serialize_scene(table.ActiveMap, is_owner)
    return JsonResponse(scene if scene is not None else {'empty': True})
```

Adicionar helper `_terrain_palette_payload` (resolve URLs das texturas):

```python
from .terrains import TERRAINS

def _terrain_palette_payload(user):
    slug_to_url = {}
    texture_slugs = [t['slug'] for t in TERRAINS if t.get('kind') == 'texture']
    if texture_slugs:
        for asset in SpriteAsset.objects.active().visible_to(user).filter(Slug__in=texture_slugs):
            slug_to_url[asset.Slug] = asset.original_url
    out = []
    for t in TERRAINS:
        entry = dict(t)
        if t.get('kind') == 'texture':
            entry['url'] = slug_to_url.get(t['slug'], '')
        out.append(entry)
    return out
```

> `reverse` precisa ser importado em `views.py` (`from django.urls import reverse`).

- [ ] **Step 4: Ver passar** — `python manage.py test tabletop.tests.EditorShellTests` → PASS (após o template ter `id="tt-scene-data"` e `data-rich-editor="2"`, criados na Fase 5; até lá, escrever um `editor.html` mínimo que renderize esses marcadores).
- [ ] **Step 5: Commit** — `git commit -am "feat(mesa): editor entrega shell+JSON; live_fragment em JSON"`

> **Nota de ordenação:** o `assertContains` da Step 1 exige o template da Fase 5. Implementar primeiro o `editor.html` mínimo (Task 5.1) e depois fechar esta task — ou aceitar que 4.2 e 5.1 são um par e commitar juntos. O executor deve fazer 5.1 antes de validar 4.2.

---

## Fase 5 — Shell do editor (tema + layout 3 colunas)

CSS/HTML; verificação manual. Cores via tokens Parchment (`.tt-themed`).

### Task 5.1: `editor.html` — shell com rails e `<script>` JSON

**Files:** Rewrite `tabletop/templates/tabletop/editor.html`; create partials `_rail_left.html`, `_rail_right.html`.

- [ ] **Step 1: Escrever `editor.html`**

Estrutura (resumo — preencher com os elementos abaixo):

```django
{% extends "tabletop/base_tabletop.html" %}
{% load static %}
{% block title %}{{ map.Name }} — Editor — {{ table.Name }}{% endblock %}
{% block extra_head %}{{ block.super }}
  <link rel="stylesheet" href="{% static 'css/scene_editor.css' %}?v={% now 'U' %}">
{% endblock %}
{% block content %}
<main class="sc-editor" data-screen-label="tabletop"
      data-rich-editor="2"
      data-scene-save-url="{{ scene_save_url }}"
      data-live-url="{% url 'tabletop:table' table.Slug %}"
      data-scenes-url="{% url 'tabletop:manage' table.Slug %}">
  {% csrf_token %}
  <header class="sc-header">
    <div class="sc-header__left">
      <span class="sc-eyebrow">EDITOR</span>
      <h1 class="sc-scene-name" id="sc-scene-name">{{ map.Name }}</h1>
      <button class="sc-iconbtn" id="sc-rename" aria-label="Renomear">✎</button>
    </div>
    <div class="sc-header__right">
      <div class="sc-undo"><button id="sc-undo" disabled>↺</button><button id="sc-redo" disabled>↻</button></div>
      <div class="sc-zoomctl"><button data-zoom="out">−</button><span id="sc-zoom">100%</span><button data-zoom="in">+</button></div>
      <button class="sc-btn" data-zoom="fit">Ajustar</button>
      <a class="sc-btn" href="{% url 'tabletop:manage' table.Slug %}">Cenas</a>
      <a class="sc-btn sc-btn--primary" href="{% url 'tabletop:table' table.Slug %}">Ver ao vivo</a>
      <span class="sc-savestate" id="sc-savestate" aria-live="polite"></span>
    </div>
  </header>
  <div class="sc-body">
    {% include "tabletop/partials/_rail_left.html" %}
    <section class="sc-stage" id="sc-stage">
      <canvas id="sc-canvas"></canvas>
      <div class="sc-tokens" id="sc-tokens"></div>
      <div class="sc-status">
        <span id="sc-status-tool">Selecionar</span>
        <span id="sc-status-coord">q0 r0</span>
        <span id="sc-status-meas"></span>
        <span id="sc-status-counts"></span>
      </div>
    </section>
    {% include "tabletop/partials/_rail_right.html" %}
  </div>
  <script id="tt-scene-data" type="application/json">{{ scene_json|safe }}</script>
  <script id="tt-terrain-data" type="application/json">{{ terrains_json|safe }}</script>
  <script id="tt-tokenlib-data" type="application/json">[{% for s in token_sprites %}{"id":{{ s.id }},"name":"{{ s.Name|escapejs }}","url":"{{ s.original_url }}"}{% if not forloop.last %},{% endif %}{% endfor %}]</script>
</main>
{% endblock %}
{% block extra_js %}
  <script src="{% static 'js/hex.js' %}?v={% now 'U' %}"></script>
  <script src="{% static 'js/scene_state.js' %}?v={% now 'U' %}"></script>
  <script src="{% static 'js/scene_canvas.js' %}?v={% now 'U' %}"></script>
  <script src="{% static 'js/scene_editor.js' %}?v={% now 'U' %}"></script>
{% endblock %}
```

- [ ] **Step 2: Escrever `_rail_left.html`** — ToolDock (6 botões `data-tool`) + container `#sc-panel` que o JS preenche por ferramenta. Tokens: render do `tt-tokenlib-data` é feito no JS; aqui só o invólucro.

```django
<aside class="sc-rail sc-rail--left">
  <div class="sc-tooldock" role="toolbar" aria-label="Ferramentas">
    <button class="sc-tool is-active" data-tool="select"><span>Selecionar</span><kbd>V</kbd></button>
    <button class="sc-tool" data-tool="terrain"><span>Terreno</span><kbd>B</kbd></button>
    <button class="sc-tool" data-tool="token"><span>Token</span><kbd>T</kbd></button>
    <button class="sc-tool" data-tool="fog"><span>Névoa</span><kbd>F</kbd></button>
    <button class="sc-tool" data-tool="measure"><span>Régua</span><kbd>R</kbd></button>
    <button class="sc-tool" data-tool="erase"><span>Apagar</span><kbd>E</kbd></button>
  </div>
  <div class="sc-panel" id="sc-panel"></div>
</aside>
```

- [ ] **Step 3: Escrever `_rail_right.html`** — invólucros de SceneSize / Layers / Inspector / TokenList que o JS preenche:

```django
<aside class="sc-rail sc-rail--right">
  <section class="sc-panel-box" id="sc-scenesize"></section>
  <section class="sc-panel-box" id="sc-layers"></section>
  <section class="sc-panel-box" id="sc-inspector"></section>
  <section class="sc-panel-box" id="sc-tokenlist"></section>
</aside>
```

- [ ] **Step 4: Verificar 4.2 + render** — Run: `python manage.py test tabletop.tests.EditorShellTests` → PASS. Abrir o editor no navegador: deve mostrar header + 3 colunas + canvas vazio (sem JS de render ainda, ok).
- [ ] **Step 5: Commit** — `git add tabletop/templates/tabletop/editor.html tabletop/templates/tabletop/partials/_rail_*.html dd3esheet/tabletop/tests.py && git commit -m "feat(mesa): shell do editor (3 colunas, rails, JSON embutido)"`

### Task 5.2: `scene_editor.css` — tokens do handoff via Parchment

**Files:** Create `dd3esheet/static/css/scene_editor.css`.

- [ ] **Step 1: Declarar o mapa de cores** — no topo do arquivo, escopado em `.sc-editor` (que herda `.tt-themed`):

```css
/* scene_editor.css — layout do design_handoff_editor_de_cena, cores remapeadas
   para a paleta Parchment & Ink (tokens de parchment-theme.css). */
.sc-editor {
  --sc-ember: var(--ochre);
  --sc-ember-bright: var(--muted-gold);
  --sc-gold: var(--muted-gold);
  --sc-surface-0: var(--paper-0);
  --sc-surface-1: var(--paper-1);
  --sc-surface-2: var(--paper-2);
  --sc-surface-3: var(--paper-3);
  --sc-line: var(--edge-line);
  --sc-line-strong: var(--edge-strong);
  --sc-text: var(--text);
  --sc-dim: var(--text-soft);
  --sc-faint: var(--text-faint);
  --sc-party: var(--steel-blue);
  --sc-ally: var(--forest);
  --sc-neutral: var(--ochre);
  --sc-enemy: var(--deep-red);
  --sc-rail-l: 296px;
  --sc-rail-r: 290px;
  --sc-header-h: 56px;
  --sc-status-h: 34px;
}
```

- [ ] **Step 2: Layout** — `.sc-editor` em coluna (header + body); `.sc-body` grid `var(--sc-rail-l) 1fr var(--sc-rail-r)`; `.sc-stage` relativa com `#sc-canvas` absoluto preenchendo, `.sc-tokens` overlay absoluto (pointer-events nos filhos), `.sc-status` rodapé fixo. Fundo xadrez do stage: `repeating-conic-gradient` em tiles de 26px usando `--paper-1`/`--paper-2`.
- [ ] **Step 3: Componentes** — portar de `design_reference/styles.css` os blocos `.sc-tooldock/.sc-tool`, `.sc-panel`, swatches de terreno, chips de pincel, inspector, token list, quickbar, context menu — **trocando** cada `var(--ember)`/`--bg-*`/`--line` pelos `--sc-*` acima. Manter raios (`--r-sm 5px` etc.), sombras e tipografia (Cinzel display; headers de painel maiúsculos `letter-spacing:.16em`).
- [ ] **Step 4: Verificação manual** — recarregar o editor: chrome com aparência Parchment (papel claro, acentos ocre), 3 colunas alinhadas, tooldock e painéis estilizados.
- [ ] **Step 5: Commit** — `git add dd3esheet/static/css/scene_editor.css && git commit -m "style(mesa): scene_editor.css (layout handoff, cores Parchment)"`

---

## Fase 6 — Estado da cena + undo/redo (`scene_state.js`)

Sem runner JS; verificação por console + comportamento. Lógica isolada e testável manualmente.

### Task 6.1: `scene_state.js`

**Files:** Create `dd3esheet/static/js/scene_state.js`.

- [ ] **Step 1: Implementar o store**

```js
// scene_state.js — estado da cena + undo/redo. window.SceneState.
(function (global) {
  const MAX_UNDO = 80;

  function fromJSON(data) {
    const terrain = new Map();
    (data.terrain || []).forEach(c => terrain.set(Hex.key(c.q, c.r), c.terrain));
    const fog = new Set((data.fog || []).map(c => Hex.key(c.q, c.r)));
    const tokens = (data.tokens || []).map(t => Object.assign({}, t));
    return { name: data.name || '', grid: Object.assign({ size: 64, cols: 30, rows: 22, showGrid: true }, data.grid || {}), terrain, fog, tokens, background: data.background || '' };
  }

  function snapshot(s) {
    return { terrain: new Map(s.terrain), fog: new Set(s.fog), tokens: s.tokens.map(t => Object.assign({}, t)) };
  }

  function create(data, onChange) {
    const s = fromJSON(data);
    const undo = [], redo = [];
    function push() { undo.push(snapshot(s)); if (undo.length > MAX_UNDO) undo.shift(); redo.length = 0; }
    function restore(snap) { s.terrain = new Map(snap.terrain); s.fog = new Set(snap.fog); s.tokens = snap.tokens.map(t => Object.assign({}, t)); }
    return {
      s,
      pushUndo: push,
      undo() { if (!undo.length) return false; redo.push(snapshot(s)); restore(undo.pop()); onChange('undo'); return true; },
      redo() { if (!redo.length) return false; undo.push(snapshot(s)); restore(redo.pop()); onChange('redo'); return true; },
      canUndo: () => undo.length > 0,
      canRedo: () => redo.length > 0,
      toPayload() {
        return {
          name: s.name, grid: { cols: s.grid.cols, rows: s.grid.rows, showGrid: s.grid.showGrid },
          terrain: [...s.terrain].map(([k, v]) => { const [q, r] = k.split(',').map(Number); return { q, r, terrain: v }; }),
          fog: [...s.fog].map(k => { const [q, r] = k.split(',').map(Number); return { q, r }; }),
          tokens: s.tokens.map(t => ({ id: t.id, tempId: t.tempId, assetId: t.assetId, name: t.name, kind: t.kind, faction: t.faction, q: t.q, r: t.r, hp: t.hp, maxHp: t.maxHp, size: t.size, conditions: t.conditions, rotation: t.rotation, hidden: t.hidden, movable: t.movable })),
        };
      },
    };
  }
  global.SceneState = { create, fromJSON, snapshot };
})(window);
```

- [ ] **Step 2: Verificação manual** — console: `const st = SceneState.create({terrain:[{q:0,r:0,terrain:'grass'}],fog:[],tokens:[]}, ()=>{}); st.s.terrain.size===1 && st.toPayload().terrain[0].terrain==='grass'` → `true`.
- [ ] **Step 3: Commit** — `git add dd3esheet/static/js/scene_state.js && git commit -m "feat(mesa): scene_state.js (estado + undo/redo)"`

---

## Fase 7 — Renderer canvas (`scene_canvas.js`): terreno, grade, câmera

### Task 7.1: Câmera + grade + terreno + névoa

**Files:** Create `dd3esheet/static/js/scene_canvas.js`.

- [ ] **Step 1: Implementar o renderer** — API: `SceneCanvas.create(canvas, state, opts)` → `{ draw(), screenToWorld(x,y), worldToScreen(x,y), cam, fit(), setHover(q,r), setBrushPreview(cells), setRuler(a,b) }`. Pontos-chave:
  - `HEX = state.grid.size` (circunraio em mundo via `size/√3`, como `calculations.py`).
  - `ctx.setTransform(dpr*zoom, 0, 0, dpr*zoom, dpr*cam.x, dpr*cam.y)`; respeitar `devicePixelRatio`.
  - Terreno: para cada `[key,terrain]` em `state.terrain`, `Hex.axialToPixel`, desenhar polígono hex; `kind==='color'` → `fillStyle` da paleta; `kind==='texture'` → `createPattern` da imagem (carregada de `opts.terrainPalette[id].url`, com cache de `Image`), com fallback para `color` enquanto carrega.
  - Grade: linhas hex finas em `--sc-line` quando `state.grid.showGrid` e camada grid visível.
  - Névoa (editor): preencher hexes de `state.fog` com `rgba` semi-transparente (no live: opaco — parâmetro `opts.fogOpaque`).
  - Prévia de pincel: contorno ocre nos `hoverCells`.
  - Régua/cone: linha + label `N hex · M m` (M=N×1.5).
- [ ] **Step 2: Câmera/eventos** — pan (botão meio/direito/Espaço/`select`+fundo), zoom na roda centrado no cursor (`passive:false`, `preventDefault`), limites 0.18–3, botões ±1.2×, `fit()` reenquadra cols×rows. Expor `draw()` para redraw sob demanda (sem RAF loop salvo durante drag).
- [ ] **Step 3: Verificação manual** — abrir editor: terreno semeado aparece nos hexes corretos, grade visível, pan/zoom suaves, "Ajustar" reenquadra. Conferir alinhamento com `axial_to_pixel` (um token e seu terreno coincidem).
- [ ] **Step 4: Commit** — `git add dd3esheet/static/js/scene_canvas.js && git commit -m "feat(mesa): scene_canvas.js (render terreno/grade/névoa + câmera)"`

---

## Fase 8 — Orquestrador do editor (`scene_editor.js`): tokens DOM, ferramentas, rails, autosave

> Arquivo grande; dividido em tasks por responsabilidade. Todas no mesmo módulo `scene_editor.js` (IIFE; lê `#tt-scene-data`, `#tt-terrain-data`, `#tt-tokenlib-data`, instancia `SceneState` + `SceneCanvas`).

### Task 8.1: Bootstrap + overlay de tokens (render/seleção/arraste)

**Files:** Create `dd3esheet/static/js/scene_editor.js`.

- [ ] **Step 1: Bootstrap** — ao `DOMContentLoaded`, se existe `[data-rich-editor="2"]`: parse dos 3 JSONs; `state = SceneState.create(scene, onChange)`; `canvas = SceneCanvas.create(...)`; primeira `fit()` + `draw()` + `renderTokens()`.
- [ ] **Step 2: `renderTokens()`** — para cada token, criar/atualizar um `.sc-token` posicionado por `worldToScreen(axialToPixel(q,r))`; diâmetro = `grid.size * sizeScale[size]` (`sm .74, md 1, lg 1.6, xl 2.3`); anel da cor `--sc-{faction}`; barra de vida (verde>60% / âmbar>30% / vermelho); ≤3 ícones de condição; nome (em hover/seleção/zoom>0.78); imagem do sprite (`spriteUrl`) ou placeholder. Reposicionar no `draw()` (callback da câmera).
- [ ] **Step 3: Seleção + arraste (ferramenta select)** — clique seleciona (`selectedId`), mostra anel duplo ocre + **quickbar** (−1 PV / valor / +1 PV / duplicar / remover); arrastar move o token (snap ao hex no soltar via `pixelToAxial`), `pushUndo()` no 1º movimento; arraste no fundo faz pan.
- [ ] **Step 4: Verificação manual** — tokens semeados aparecem com anel/vida/nome; selecionar mostra quickbar; arrastar reposiciona e dá snap; pan no fundo funciona.
- [ ] **Step 5: Commit** — `git commit -am "feat(mesa): overlay DOM de tokens (render/seleção/arraste)"`

### Task 8.2: ToolDock + troca de painel + ferramenta de terreno

- [ ] **Step 1: ToolDock** — clique nos `.sc-tool` troca `tool` (e classe `is-active`); atalhos `V/B/T/F/R/E` (ignorar quando foco em input/textarea); `#sc-panel` re-renderiza o painel contextual.
- [ ] **Step 2: TerrainPanel** — alternador Pincel/Balde; paleta 3-col das 9 cores/texturas (de `#tt-terrain-data`); chips de tamanho de pincel (0–3 → 1/7/19/37). Pintar: mousedown empurra undo, pinta `Hex.disk(center, brush)` ao longo de `Hex.line` do traço; balde = flood-fill 6-vizinhos ≤6000; Apagar (ferramenta erase ou terreno) pinta `stone`; Alt+clique = conta-gotas (copia terreno sob o cursor). Cada pincelada atualiza `state.terrain` + `canvas.draw()` + agenda autosave.
- [ ] **Step 3: Verificação manual** — pintar grama com pincel raio 1 cobre 7 hexes; balde preenche região; conta-gotas troca o terreno ativo; apagar volta p/ pedra.
- [ ] **Step 4: Commit** — `git commit -am "feat(mesa): tooldock + pintura de terreno (pincel/balde/contagotas)"`

### Task 8.3: TokenPanel + FogPanel + SimplePanel

- [ ] **Step 1: TokenPanel** — busca + grid 2-col dos assets (`#tt-tokenlib-data`); arrastar asset p/ o mapa cria token no hex (faction default `enemy`, size `md`, hp/maxhp 0); ou clicar para "pegar" e clicar no hex. `pushUndo()` ao criar.
- [ ] **Step 2: FogPanel** — toggle Revelar/Ocultar; tamanho de pincel; "Revelar tudo" (limpa `state.fog`) / "Cobrir tudo" (todas as células cols×rows). Pincel de névoa = mesma mecânica de disco/linha; revelar remove do Set, ocultar adiciona. Autosave agendado.
- [ ] **Step 3: SimplePanel** — para `select`/`erase`/`measure`: ícone + título + instrução curta.
- [ ] **Step 4: Verificação manual** — arrastar asset cria token; pincel de névoa oculta/revela; "Cobrir tudo"/"Revelar tudo" funcionam.
- [ ] **Step 5: Commit** — `git commit -am "feat(mesa): painéis de token, névoa e simples"`

### Task 8.4: Rail direito — SceneSize, Layers, Inspector, TokenList

- [ ] **Step 1: SceneSizePanel** — presets (Pequena 16×12, Média 30×22, Grande 44×32, Enorme 60×44) + steppers cols/rows (limites 8–80 / 6–60); ao mudar, atualiza `state.grid`, `canvas.fit()`, autosave.
- [ ] **Step 2: LayersPanel** — 4 camadas (Terreno/Tokens/Névoa/Grade) com olho (visível) e cadeado (trava — só Terreno/Tokens); camada ativa destacada; "Limpar terreno" (empurra undo, esvazia `state.terrain`). Visibilidade afeta `canvas.draw()`/`renderTokens()`.
- [ ] **Step 3: InspectorPanel** — ficha do token selecionado: avatar+anel; nome inline (editável); facção (4 botões); PV (stepper −/input/+ + barra colorida); tamanho (P/M/G/GG); 6 condições toggláveis. Edições mutam o token + `renderTokens()` + autosave; mudanças estruturais (facção/tamanho/condição) empurram undo; digitação contínua de nome/PV usa flag skip (1 undo por edição). Vazio → "Nada selecionado".
- [ ] **Step 4: TokenListPanel** — lista de todos os tokens (legenda de facções + mini barra de vida); clique seleciona e centraliza.
- [ ] **Step 5: Verificação manual** — trocar preset reenquadra; ocultar camada de tokens some com eles; inspector edita PV/facção/tamanho/condições e reflete no mapa; lista seleciona.
- [ ] **Step 6: Commit** — `git commit -am "feat(mesa): rail direito (scenesize/layers/inspector/tokenlist)"`

### Task 8.5: Autosave (debounced) + estado salvando/salvo + undo/redo UI

- [ ] **Step 1: Autosave** — função `scheduleSave()` com debounce ~800ms: `fetch(scene_save_url, {method:'POST', headers:{'X-CSRFToken':csrf}, body: new URLSearchParams({scene: JSON.stringify(state.toPayload())})})`. Atualiza `#sc-savestate` ("salvando…" → "salvo HH:MM"); em erro, "falha ao salvar" + reespera. Após salvar, mapear `tempId`→`id` da resposta (a resposta pode devolver os ids; se não, recarregar ids no próximo serialize — política simples: resposta `{ok:true}` e os tokens novos recebem id no próximo full save via re-serialize do servidor não ocorre — então `scene_save` deve devolver o mapeamento). **Ajuste no servidor:** `scene_save` retorna `{'ok':True,'tokens':[{'tempId':..,'id':..}]}`; `apply_scene_payload` precisa propagar tempId→id (estender `_upsert_token` para coletar pares). Atualizar Task 3.2/4.1 conforme — ver Step 2.
- [ ] **Step 2: Propagar tempId→id** — modificar `apply_scene_payload` para retornar `id_map` (`{tempId: new_id}`) e `scene_save` para incluí-lo na resposta; o cliente aplica `state.tokens` (seta `id`, limpa `tempId`). (Adicionar teste em `ApplyScenePayloadTests`: criar token com `tempId` retorna mapa com id real.)
- [ ] **Step 3: Undo/Redo UI** — botões `#sc-undo`/`#sc-redo` chamam `store.undo()/redo()`, `disabled` conforme `canUndo/canRedo`; `Ctrl+Z`/`Ctrl+Y`/`Ctrl+Shift+Z`. Cada undo/redo redesenha e agenda autosave.
- [ ] **Step 4: Verificação manual** — pintar e esperar: "salvo"; recarregar a página mantém o terreno (persistiu); Ctrl+Z desfaz; criar token, autosave, recarregar → token tem id estável.
- [ ] **Step 5: Commit** — `git commit -am "feat(mesa): autosave debounced + tempId->id + undo/redo UI"`

---

## Fase 9 — LiveStage (`scene_live.js`) + `table_view.html`

### Task 9.1: Render read-only + polling JSON

**Files:** Rewrite `tabletop/templates/tabletop/table_view.html`; create `dd3esheet/static/js/scene_live.js`.

- [ ] **Step 1: `table_view.html`** — header próprio (badge "● Ao vivo" pulsante, nome, zoom, Ajustar, Tela cheia, e p/ dono: Gerenciar cenas + "Editar esta cena"); palco com `#sc-canvas` + `.sc-tokens` + dock vertical de utilidades à esquerda (Mover/Régua/Cone/Ping/Marcador + 7 cores + Limpar tudo). Embutir `scene_json` inicial (de `serialize_scene(ActiveMap, is_owner)`) num `<script id="tt-scene-data">`. Adicionar `data-live-fragment-url="{% url 'tabletop:live-fragment' table.Slug %}"`, `data-move-url-base`, `data-can-edit`. CSS reusa `scene_editor.css` (mesmos `--sc-*`).
- [ ] **Step 2: View `table_view`** — passar `scene_json = json.dumps(serialize_scene(table.ActiveMap, is_owner))`.
- [ ] **Step 3: `scene_live.js`** — instanciar `SceneState` (read-only) + `SceneCanvas` com `opts.fogOpaque=true` + vinheta (sombra interna via overlay CSS); tokens em névoa já não vêm no JSON. Polling: `setInterval` 2s → `fetch(live-fragment)` → se mudou, recriar state e `draw()`+`renderTokens()`. **Player move:** se `data-can-edit` ou token `movable`, arrastar a própria mini → `POST move_token` (X/Y em px do `axialToPixel`), depois re-render no próximo polling.
- [ ] **Step 4: Verificação manual** — abrir `/mesa/<slug>/` como dono e numa janela anônima: névoa opaca, tokens em névoa somem p/ anônimo; arrastar token movível persiste e aparece na outra janela em ≤2s.
- [ ] **Step 5: Commit** — `git add tabletop/templates/tabletop/table_view.html dd3esheet/static/js/scene_live.js dd3esheet/tabletop/views.py && git commit -m "feat(mesa): LiveStage read-only + polling JSON + move de jogador"`

### Task 9.2: Utilidades do LiveStage (régua/cone/ping/marcador/tela cheia)

**Files:** Modify `dd3esheet/static/js/scene_live.js`.

- [ ] **Step 1: Régua/Cone** — Mover (default/pan); Régua arrasta hex→hex mostrando `N hex · M m`; Cone 60° (`CONE_HALF=Math.PI/6`) com distância. Efêmeros (só desenho no canvas overlay).
- [ ] **Step 2: Ping/Marcador** — Ping: clique emite anéis 14→96px em 1.4s (`@keyframes`), some sozinho; Marcador: pin colorido toggável (clica coloca, clica remove); paleta de 7 cores; "Limpar tudo" remove pings/marcadores. **Não persistem** (locais à sessão do cliente).
- [ ] **Step 3: Tela cheia** — botão usa Fullscreen API no `.sc-stage`.
- [ ] **Step 4: Verificação manual** — régua mede 1 hex = 1,5 m; cone abre 60°; ping anima e some; marcador alterna; tela cheia entra/sai.
- [ ] **Step 5: Commit** — `git commit -am "feat(mesa): utilidades do LiveStage (régua/cone/ping/marcador/tela cheia)"`

---

## Fase 10 — Atalhos globais + menu de contexto

### Task 10.1: Menu de contexto do token

**Files:** Modify `dd3esheet/static/js/scene_editor.js`; CSS em `scene_editor.css`.

- [ ] **Step 1: Implementar** — botão direito num token abre popover: Duplicar (Ctrl+D), separador, "Facção" com 4 swatches, separador, Remover (Del, em vermelho). Fora-do-clique/Esc fecha. Ações mutam state + autosave + undo.
- [ ] **Step 2: Atalhos restantes** — setas movem o token selecionado 1 hex; `Del/Backspace` remove; `Esc` limpa seleção/medição/menu; `Ctrl+D` duplica; `0` ajusta. Garantir que inputs/textareas não disparam atalhos.
- [ ] **Step 3: Verificação manual** — botão direito mostra menu; trocar facção pelo menu; setas/Del/Ctrl+D/Esc funcionam.
- [ ] **Step 4: Commit** — `git commit -am "feat(mesa): menu de contexto do token + atalhos de teclado"`

---

## Fase 11 — Limpeza, seed das texturas, testes finais

### Task 11.1: Seed das 3 texturas de terreno

**Files:** Modify `dd3esheet/sprites/seeds.py` (ou `seed_sprite_library.py`); verificar slugs `terrain-dungeon/terrain-cobblestone/terrain-woods`.

- [ ] **Step 1: Garantir os assets** — assegurar que o seed cria `SpriteAsset` MAP_TILE com `Slug` exatamente `terrain-dungeon`, `terrain-cobblestone`, `terrain-woods`, apontando às imagens de `design_reference/assets/terrain/` copiadas para `media`/fixtures do projeto. Se já existirem com outro slug, adicionar binding/alias ou ajustar `terrains.py`.
- [ ] **Step 2: Teste**

```python
class TerrainSeedTests(TestCase):
    def test_texture_slugs_resolve_or_palette_falls_back(self):
        from .views import _terrain_palette_payload  # tabletop.views
        # sem assets semeados, texturas vêm com url vazia mas mantêm 'color' de fallback
        payload = _terrain_palette_payload(None)
        dungeon = next(t for t in payload if t['id'] == 'dungeon')
        self.assertIn('url', dungeon)
        self.assertTrue(dungeon['color'])
```

- [ ] **Step 3: Ver passar** — `python manage.py test tabletop.tests.TerrainSeedTests` → PASS.
- [ ] **Step 4: Commit** — `git commit -am "feat(mesa): seed/slug das texturas de terreno + fallback"`

### Task 11.2: Remover código morto do editor antigo

**Files:** Delete `dd3esheet/static/js/tabletop_editor.js`; remover de `views.py`/`urls.py` o que ficou órfão (`add_token`/`edit_token`/`paint_terrain`/`clear_terrain`/`add_fog`/`delete_fog` se não mais usados; **manter** `move_token`). Remover `FogRegion` do fluxo (manter o model até uma migração de remoção separada, ou removê-lo se nenhum dado em produção depende — decisão: manter o model, parar de usar).

- [ ] **Step 1: Buscar referências** — `grep -rn "tabletop_editor.js\|paint_terrain\|FogRegion\|_editor_body" dd3esheet/` e remover usos órfãos; ajustar/excluir partials `_editor_body.html`, `_canvas.html` (se o live não usa mais), `_fog.html`, `_token.html`, `_token_row.html`, `_token_sprite.html` conforme o que sobrou.
- [ ] **Step 2: Rodar a suíte** — `python manage.py test tabletop` → Expected: PASS (corrigir/atualizar testes que exercitavam endpoints removidos; remover os que testavam comportamento aposentado).
- [ ] **Step 3: Verificação manual** — editor e live continuam funcionando após a limpeza.
- [ ] **Step 4: Commit** — `git commit -am "chore(mesa): remover editor antigo e código morto"`

### Task 11.3: Suíte completa + docs

- [ ] **Step 1: Rodar tudo** — `python manage.py test` (projeto inteiro) → Expected: PASS. Rodar também `python manage.py makemigrations --check --dry-run` → sem migrações pendentes.
- [ ] **Step 2: Atualizar docs** — `docs/known-issues.md`: névoa retangular antiga não migra (repintar). `docs/architecture.md`/`seeds.md`: novo contrato JSON da cena, autosave, FogCell, paleta de terreno.
- [ ] **Step 3: Commit** — `git commit -am "docs(mesa): editor de cena (contrato, autosave, limitações de migração)"`

---

## Self-review (cobertura do spec)

- Tema Parchment remap → Task 5.2 (mapa `--sc-*`). ✅
- Cliente-autoritativo + autosave → Fases 6–8 + Task 4.1/8.5. ✅
- Multiplayer (live público + polling, movable, hidden, múltiplas cenas) → Task 9.1 (polling/move), serializer filtra hidden/fog (3.1), `manage`/ActiveMap intactos. ✅
- Token Faction/HP/Size/Conditions + Kind p/ object → Task 2.2/2.3. ✅
- FogCell por-hex + visibilidade → Task 2.2/2.4/3.1. ✅
- Paleta de terreno (cor/textura) → Task 2.1/4.2/7.1/11.1. ✅
- Canvas (terreno/grade/névoa/câmera/régua) → Fase 7. ✅
- Rails completos (tooldock/terrain/token/fog/scenesize/layers/inspector/tokenlist) → Task 5.1/8.2–8.4. ✅
- LiveStage (névoa opaca/vinheta/utilidades/tela cheia) → Fase 9. ✅
- Atalhos + menu de contexto → Fase 10. ✅
- Testes (cálculos/serialização/permissões/roteamento) → Tasks 1.x, 2.x, 3.x, 4.x. ✅

**Riscos/ordem:** Task 4.2 depende do template 5.1 (nota incluída). Autosave de tokens precisa do tempId→id (Task 8.5 Step 2 estende 3.2/4.1 — fazer junto). Paridade Python↔JS do hex math é verificada por inspeção (sem runner JS).
