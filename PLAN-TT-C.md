# Mesa Virtual — Scene Creator rico (Fatia C) — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) ou superpowers:executing-plans. Steps usam checkbox (`- [ ]`).

**Goal:** Elevar o **editor privado da cena** (`/mesa/<slug>/map/<mid>/editor`) ao nível do "Scene Creator" do handoff: pan/zoom, paleta com drag-and-drop, seleção + rotação, pintura de terreno, régua métrica e camadas — mantendo a persistência no servidor e o compartilhamento ao vivo do `tabletop`.

**Architecture:** O handoff (`design_handoff_dnd_vtt/scene/scene.js`) é um editor **single-user em localStorage**; aqui o estado mora no **banco** e é compartilhado via polling. Então portamos as **interações** do handoff, mas a persistência vira endpoints HTMX/JSON do `tabletop`. Pan/zoom/camadas/régua são **estado de view client-side** (não persistem). Rotação e terreno **persistem** (novo campo + novo model). A fatia depende de A (tema) e B (grade hex + matemática).

**Tech Stack:** Django 4.2 (1 campo novo + 1 model novo + migração + endpoints), JS vanilla (engine de canvas/transform), `tabletop.css`, testes `python manage.py test tabletop`. Docker.

**Spec de origem:** `design_handoff_dnd_vtt/README.md` (seções "Interactions & Behavior" e "State Management") + `scene/scene.js` (spec comportamental precisa, citado por faixa de linhas).

---

## ⚠️ Decisões assumidas — REVISAR antes de executar

Esta fatia não passou por brainstorming dedicado. As decisões abaixo foram tomadas para caber no padrão do `tabletop`; confirme/ajuste antes de rodar as tasks:

1. **Pan/zoom, camadas (visibilidade/lock) e régua são client-side** (estado de edição do mestre), **não persistem** no banco. Justificativa: são auxílios de edição; persistir multiplicaria schema e tráfego de polling sem ganho para o jogador.
2. **Rotação persiste** (novo `Token.Rotation`, graus 0–345). Aparece na visão ao vivo.
3. **Terreno persiste** num model novo `TerrainCell(Map, Q, R, SpriteAsset)` (por hexágono, coords axiais da fatia B). Pintura em arrasto **acumula no cliente e faz 1 POST em lote** no `pointerup` (não um POST por célula).
4. **Névoa continua retangular** (`FogRegion`), como hoje. O `TABLETOP.md` lista "névoa por hexágono (pintar)" como **fora de escopo/futuro**; portanto a fatia C **não** troca a névoa para pincel hexagonal. (Se você quiser o pincel de névoa por célula do handoff, é uma decisão de produto a confirmar — adiciona um model/endpoint análogo ao terreno.)
5. **Drag-and-drop da paleta** cria tokens a partir de `SpriteAsset` da biblioteca (categoria `MAP_TOKEN`); "fundos" (categoria `MAP_TILE`) continuam definidos na tela `manage` (não no drop). Terreno usa sprites `MAP_TILE` também, mas via a ferramenta "pintar".
6. **Sem build step / sem framework** (regra do projeto): a engine é um arquivo JS vanilla novo (`tabletop_editor.js`), carregado **só** na página do editor.

Se qualquer item acima mudar, pare e reabra como brainstorming desta fatia.

---

## Estrutura de arquivos

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `dd3esheet/tabletop/models.py` | **Modificar** | `Token.Rotation` (PositiveSmallInt, default 0). Novo model `TerrainCell`. |
| `dd3esheet/tabletop/migrations/0004_terrain_rotation.py` | **Criar** | Campo `Rotation` + tabela `TerrainCell`. |
| `dd3esheet/tabletop/views.py` | **Modificar** | `add_token` aceita `X`,`Y` (drop); `move_token`/`edit_token` aceitam `Rotation`; novos `paint_terrain`/`clear_terrain`. `_canvas_context` injeta terreno. |
| `dd3esheet/tabletop/urls.py` | **Modificar** | Rotas `terrain/paint`, `terrain/clear`. |
| `dd3esheet/tabletop/templates/tabletop/editor.html` | **Modificar** | Estrutura 3 colunas (paleta · palco · camadas/inspector) + barra de status. |
| `dd3esheet/tabletop/templates/tabletop/partials/_editor_body.html` | **Modificar** | Render da paleta drag-drop + painel de camadas/inspector. |
| `dd3esheet/tabletop/templates/tabletop/partials/_canvas.html` | **Modificar** | Render das células de terreno (sob tokens). |
| `dd3esheet/static/js/tabletop_editor.js` | **Criar** | Engine: pan/zoom (transform), ferramentas, paleta, seleção/rotação, pintura (batch), régua, camadas. Espelha `scene.js`. |
| `dd3esheet/static/css/tabletop.css` | **Modificar** | Layout do editor (grid 3 colunas), tiles de paleta, inspector, barra de status, classes de ferramenta. |
| `dd3esheet/tabletop/tests.py` | **Modificar** | Testes dos endpoints novos (drop com X/Y, rotação, paint/clear terreno, permissões, render). |

---

## Task 1: Model — `Token.Rotation` + `TerrainCell` (TDD)

**Files:**
- Modify: `dd3esheet/tabletop/models.py`
- Create: `dd3esheet/tabletop/migrations/0004_terrain_rotation.py`
- Test: `dd3esheet/tabletop/tests.py` (adicionar `TerrainModelTests`)

- [ ] **Step 1: Teste que falha**

Adicionar ao final de `dd3esheet/tabletop/tests.py`:

```python
class TerrainModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('gmC', password='x' * 12)
        self.table = GameTable.objects.create(Owner=self.owner, Name='Mesa C')
        self.map = Map.objects.create(Table=self.table, Name='Cena')

    def test_token_rotation_defaults_zero(self):
        tok = Token.objects.create(Map=self.map, Kind=Token.ENEMY)
        self.assertEqual(tok.Rotation, 0)

    def test_terrain_cell_unique_per_axial(self):
        from tabletop.models import TerrainCell
        TerrainCell.objects.create(Map=self.map, Q=1, R=-2)
        with self.assertRaises(Exception):
            TerrainCell.objects.create(Map=self.map, Q=1, R=-2)
```

- [ ] **Step 2: Rodar p/ confirmar que falha**

Run: `docker compose exec web python manage.py test tabletop.tests.TerrainModelTests -v 2`
Expected: FAIL (`Token` sem `Rotation` / sem model `TerrainCell`).

- [ ] **Step 3: Implementar no `models.py`**

Em `dd3esheet/tabletop/models.py`, dentro da classe `Token`, adicionar após o campo `Order` (linha ~97):

```python
    Rotation = models.PositiveSmallIntegerField(default=0)  # graus 0-345
```

E adicionar, ao final do arquivo, o novo model:

```python
class TerrainCell(models.Model):
    """Uma célula de terreno pintada num hexágono (coords axiais, fatia B)."""

    Map = models.ForeignKey(Map, on_delete=models.CASCADE)
    Q = models.IntegerField()
    R = models.IntegerField()
    SpriteAsset = models.ForeignKey(
        'sprites.SpriteAsset', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='tabletop_terrain',
    )
    CreatedAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('CreatedAt',)
        constraints = [
            models.UniqueConstraint(fields=('Map', 'Q', 'R'), name='unique_terrain_cell_per_map'),
        ]

    def __str__(self):
        return f'Terrain {self.Q},{self.R}'
```

- [ ] **Step 4: Gerar e aplicar a migração**

Run:
```bash
docker compose exec web python manage.py makemigrations tabletop --name terrain_rotation
docker compose exec web python manage.py migrate tabletop
```
Expected: cria `0004_terrain_rotation.py` e aplica sem erro.

- [ ] **Step 5: Rodar o teste**

Run: `docker compose exec web python manage.py test tabletop.tests.TerrainModelTests -v 2`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add dd3esheet/tabletop/models.py dd3esheet/tabletop/migrations/0004_terrain_rotation.py dd3esheet/tabletop/tests.py
git commit -m "feat(mesa): Token.Rotation + model TerrainCell"
```

---

## Task 2: Endpoints — drop com posição, rotação, pintura de terreno (TDD)

**Files:**
- Modify: `dd3esheet/tabletop/views.py`
- Modify: `dd3esheet/tabletop/urls.py`
- Test: `dd3esheet/tabletop/tests.py` (adicionar `EditorEndpointTests`)

- [ ] **Step 1: Testes que falham**

Adicionar ao final de `dd3esheet/tabletop/tests.py`:

```python
class EditorEndpointTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('gmE', password='x' * 12)
        self.table = GameTable.objects.create(Owner=self.owner, Name='Mesa E')
        self.map = Map.objects.create(Table=self.table, Name='Cena', GridMode=Map.HEX)
        self.table.ActiveMap = self.map
        self.table.save()
        self.client.force_login(self.owner)

    def test_add_token_with_position_snaps_to_hex(self):
        url = reverse('tabletop:add-token', args=[self.table.Slug])
        resp = self.client.post(url, {'MapId': self.map.id, 'Kind': 'enemy', 'X': 120, 'Y': 90})
        self.assertEqual(resp.status_code, 200)
        tok = Token.objects.filter(Map=self.map).latest('id')
        from tabletop.calculations import nearest_hex_center
        self.assertEqual((tok.X, tok.Y), nearest_hex_center(120, 90, self.map.GridSize))

    def test_edit_token_sets_rotation(self):
        tok = Token.objects.create(Map=self.map, Kind=Token.ENEMY)
        url = reverse('tabletop:edit-token', args=[self.table.Slug, tok.id])
        self.client.post(url, {'Rotation': 90})
        tok.refresh_from_db()
        self.assertEqual(tok.Rotation, 90)

    def test_paint_terrain_creates_cells(self):
        url = reverse('tabletop:paint-terrain', args=[self.table.Slug, self.map.id])
        resp = self.client.post(url, {'cells': '1,-2;0,0;3,1'})
        self.assertEqual(resp.status_code, 200)
        from tabletop.models import TerrainCell
        self.assertEqual(TerrainCell.objects.filter(Map=self.map).count(), 3)

    def test_paint_terrain_is_idempotent_on_repeat(self):
        url = reverse('tabletop:paint-terrain', args=[self.table.Slug, self.map.id])
        self.client.post(url, {'cells': '1,1'})
        self.client.post(url, {'cells': '1,1'})
        from tabletop.models import TerrainCell
        self.assertEqual(TerrainCell.objects.filter(Map=self.map, Q=1, R=1).count(), 1)

    def test_paint_terrain_forbidden_for_stranger(self):
        self.client.logout()
        stranger = User.objects.create_user('x', password='x' * 12)
        self.client.force_login(stranger)
        url = reverse('tabletop:paint-terrain', args=[self.table.Slug, self.map.id])
        self.assertEqual(self.client.post(url, {'cells': '1,1'}).status_code, 403)
```

- [ ] **Step 2: Rodar p/ confirmar que falham**

Run: `docker compose exec web python manage.py test tabletop.tests.EditorEndpointTests -v 2`
Expected: FAIL (`NoReverseMatch` p/ `paint-terrain`; X/Y ignorados; sem `Rotation`).

- [ ] **Step 3: Rotas novas**

Em `dd3esheet/tabletop/urls.py`, adicionar dentro de `urlpatterns` (após a linha do `add-fog`):

```python
    path('<slug:slug>/map/<int:mid>/terrain/paint', views.paint_terrain, name='paint-terrain'),
    path('<slug:slug>/map/<int:mid>/terrain/clear', views.clear_terrain, name='clear-terrain'),
```

- [ ] **Step 4: Implementar nas views**

Em `dd3esheet/tabletop/views.py`:

(a) No `add_token` (linha ~226), trocar o cálculo de `X`/`Y` para honrar posição opcional do drop, encaixando no hex:

```python
    x = _int_or(request.POST.get('X'))
    y = _int_or(request.POST.get('Y'))
    if x is None or y is None:
        x, y = m.WidthPx // 2, m.HeightPx // 2
    else:
        x, y = snap_to_grid(x, y, m.GridSize, m.GridMode)
    Token.objects.create(
        Map=m,
        Kind=kind,
        Label=request.POST.get('Label', '').strip(),
        SpriteAsset=_resolve_sprite(request, 'Sprite', SpriteAsset.MAP_TOKEN),
        X=x,
        Y=y,
        GridWidth=_int_or(request.POST.get('GridWidth'), 1) or 1,
        GridHeight=_int_or(request.POST.get('GridHeight'), 1) or 1,
        MovableByPlayers=movable,
        Order=m.token_set.count(),
    )
```

(b) No `edit_token` (linha ~243), adicionar antes de `token.save()`:

```python
    if 'Rotation' in request.POST:
        token.Rotation = (_int_or(request.POST['Rotation'], token.Rotation) or 0) % 360
```

(c) Adicionar os endpoints de terreno (após `delete_fog`):

```python
def _parse_cells(raw):
    """'q,r;q,r;...' -> lista de tuplas (q, r) inteiras, deduplicadas em ordem."""
    seen, out = set(), []
    for part in (raw or '').split(';'):
        bits = part.split(',')
        if len(bits) != 2:
            continue
        q, r = _int_or(bits[0]), _int_or(bits[1])
        if q is None or r is None or (q, r) in seen:
            continue
        seen.add((q, r))
        out.append((q, r))
    return out


@require_POST
def paint_terrain(request, slug, mid):
    table = _get_owned(request, slug)
    m = get_object_or_404(Map, id=mid, Table=table)
    sprite = _resolve_sprite(request, 'Sprite', SpriteAsset.MAP_TILE)
    for q, r in _parse_cells(request.POST.get('cells')):
        TerrainCell.objects.update_or_create(Map=m, Q=q, R=r, defaults={'SpriteAsset': sprite})
    table.save()
    return _render_editor_body(request, table, m)


@require_POST
def clear_terrain(request, slug, mid):
    table = _get_owned(request, slug)
    m = get_object_or_404(Map, id=mid, Table=table)
    cells = _parse_cells(request.POST.get('cells'))
    if cells:
        for q, r in cells:
            TerrainCell.objects.filter(Map=m, Q=q, R=r).delete()
    else:
        TerrainCell.objects.filter(Map=m).delete()  # "limpar tudo"
    table.save()
    return _render_editor_body(request, table, m)
```

(d) No topo, ampliar o import de models (linha 9):

```python
from .models import FogRegion, GameTable, Map, TerrainCell, Token
```

(e) Em `_canvas_context` (linha ~66), injetar o terreno com centro em px (usa a matemática hex da fatia B):

```python
def _canvas_context(table, m, is_owner):
    """Tokens filtrados por visibilidade + terreno (centros px) + sprites resolvidos."""
    from .calculations import nearest_hex_center
    fogs = list(m.fogregion_set.all()) if m else []
    tokens = []
    terrain = []
    if m:
        candidates = list(m.token_set.select_related('SpriteAsset').all())
        tokens = [t for t in candidates if token_visible_to(t, fogs, is_owner)]
        attach_sprites_to_tokens(tokens)
        for t in tokens:
            t.PxWidth = t.GridWidth * m.GridSize
            t.PxHeight = t.GridHeight * m.GridSize
        if m.GridMode == m.HEX:
            for cell in m.terraincell_set.select_related('SpriteAsset').all():
                # centro do hex (q,r) em px = nearest_hex_center no próprio centro
                from .calculations import hex_dimensions
                d = hex_dimensions(m.GridSize)
                import math
                cx = round(math.sqrt(3) * d['radius'] * (cell.Q + cell.R / 2))
                cy = round(1.5 * d['radius'] * cell.R)
                cell.Cx, cell.Cy = cx, cy
                terrain.append(cell)
    return {
        'table': table, 'map': m, 'tokens': tokens, 'fogs': fogs,
        'terrain': terrain, 'is_owner': is_owner, 'slug': table.Slug,
    }
```

> Simplificação: extraia o cálculo `axial→pixel` para uma função pura `axial_to_pixel(q, r, grid_size)` em `calculations.py` e use-a aqui e no teste, evitando o `import math` inline. (Recomendado durante a implementação; mantém a regra "cálculo em função pura".)

- [ ] **Step 5: Rodar os testes**

Run: `docker compose exec web python manage.py test tabletop.tests.EditorEndpointTests -v 2`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add dd3esheet/tabletop/views.py dd3esheet/tabletop/urls.py dd3esheet/tabletop/tests.py
git commit -m "feat(mesa): endpoints de drop posicionado, rotacao e pintura de terreno"
```

---

## Task 3: Render de terreno + rotação no canvas

**Files:**
- Modify: `dd3esheet/tabletop/templates/tabletop/partials/_canvas.html`
- Modify: `dd3esheet/tabletop/templates/tabletop/partials/_token.html` (aplicar rotação)
- Modify: `dd3esheet/static/css/tabletop.css`

- [ ] **Step 1: Render das células de terreno (sob os tokens)**

Em `_canvas.html`, logo após o `<img class="tt-canvas__bg">`/grade e **antes** do loop de fog, adicionar:

```html
    {% for cell in terrain %}
    <div class="tt-terrain" style="left:{{ cell.Cx }}px; top:{{ cell.Cy }}px; width:{{ map.GridSize }}px; height:{{ map.GridSize }}px;">
        {% if cell.SpriteAsset %}<img src="{{ cell.SpriteAsset.original_url }}" alt="" draggable="false">{% endif %}
    </div>
    {% endfor %}
```

- [ ] **Step 2: Aplicar rotação ao token**

Abrir `dd3esheet/tabletop/templates/tabletop/partials/_token.html` e, no atributo `style` do `.tt-token`, somar a rotação ao transform (o token usa `translate(-50%,-50%)`; acrescentar `rotate`). Exemplo do estilo inline: garantir `transform: translate(-50%,-50%) rotate({{ t.Rotation|default:0 }}deg);` no elemento `.tt-token`. (Conferir o markup atual do arquivo e ajustar só o `transform`.)

- [ ] **Step 3: Estilo do terreno**

Em `tabletop.css`, adicionar na seção do canvas:

```css
.tt-terrain {
    position: absolute;
    transform: translate(-50%, -50%);
    clip-path: polygon(50% 0, 100% 25%, 100% 75%, 50% 100%, 0 75%, 0 25%);
    background: color-mix(in oklab, var(--leather) 22%, var(--paper-1));
    pointer-events: none;
    z-index: 0;
}
.tt-terrain img { width: 100%; height: 100%; object-fit: cover; }
```

- [ ] **Step 4: Verificação manual + commit**

Subir o app; via shell, pintar células (ou aguardar a Task 4 para pintar pela UI) e confirmar que o terreno aparece sob os tokens e que tokens com `Rotation` giram.

```bash
git add dd3esheet/tabletop/templates/tabletop/partials/_canvas.html dd3esheet/tabletop/templates/tabletop/partials/_token.html dd3esheet/static/css/tabletop.css
git commit -m "feat(mesa): render de terreno hexagonal e rotacao de tokens"
```

---

## Task 4: Engine do editor (`tabletop_editor.js`) — pan/zoom, ferramentas, paleta, seleção/rotação, pintura, régua, camadas

Esta é a maior parte e é **client-side**. Porte as interações de `design_handoff_dnd_vtt/scene/scene.js` adaptando a persistência para os endpoints HTMX/JSON do `tabletop`. O handoff é o **spec comportamental preciso**; abaixo o mapeamento exato.

**Files:**
- Create: `dd3esheet/static/js/tabletop_editor.js`
- Modify: `dd3esheet/tabletop/templates/tabletop/editor.html` (layout 3 colunas + status bar; carregar o JS via `{% block extra_js %}` adicional)
- Modify: `dd3esheet/tabletop/templates/tabletop/partials/_editor_body.html` (paleta drag-drop + camadas/inspector)
- Modify: `dd3esheet/static/css/tabletop.css` (layout/inspector/tiles/statusbar)

**Mapeamento handoff → mesa (contratos):**

| Comportamento | Fonte no handoff (`scene.js`) | Adaptação no `tabletop_editor.js` |
|---|---|---|
| `CELL=72`, `1 hex = 1,5 m`, `fmtM` | linhas 9-10, 48 | Usar `GridSize` do mapa (data-attr) como unidade; `M_PER_CELL=1.5`. |
| Pan/zoom (`screenToWorld`, wheel, `startPan`, `zoomBy`, `fitView`) | 89-91, 446-486, 594-614 | Idêntico, sobre um wrapper `.tt-world` com `transform: translate()+scale()` dentro do `.tt-stage`. **Não persiste.** |
| Hex axial↔pixel + `cellAt`/`snapPoint` | 92-122 | **Reusar a matemática da fatia B** (mesmas fórmulas com `R=GridSize/√3`). |
| Ferramentas (select/place/paint/measure) + atalhos V/P/B/M | 419-425, 711-727 | Igual. (Sem "fog" por célula — ver Decisão 4; o botão de névoa retangular existente permanece.) |
| Paleta com tabs + busca + tiles arrastáveis | 30-45, 373-413 | Render server-side a partir de `token_sprites`/`tile_sprites` (já vêm no contexto do editor); `dragstart` carrega o `SpriteId`. |
| Drop no palco | 488-493 | `htmx.ajax('POST', add-token, {values:{MapId, SpriteId, Kind, X, Y}})`. |
| Selecionar/mover/rotacionar objeto | 316-368 | Mover já existe (`tabletop.js`). Rotação: handle gira e no `pointerup` faz `htmx.ajax('POST', edit-token, {values:{Rotation}})`. |
| Pintura de terreno (acumula em arrasto) | 426-436, 455, 467 | Acumular `Set` de `"q,r"` no arrasto; no `pointerup` 1 POST `paint-terrain` com `cells="q,r;q,r;..."` (+ `SpriteId` da peça ativa). "Limpar terreno" → `clear-terrain` sem `cells`. |
| Régua | 211, 235-240, 469, 574-581 | Idêntico; desenha numa `<canvas>` overlay e escreve em `#tt-meas`/status bar. **Não persiste.** |
| Camadas (visibilidade/lock + contagens) | 498-522 | Toggle de classes CSS que escondem `.tt-terrain`/`.tt-token[...]`; lock impede iniciar arrasto. **Não persiste.** |
| Barra de status (hint/coord/zoom) | 583-589 | Igual. |

- [ ] **Step 1: Layout do editor (template)**

Reescrever `editor.html` e `_editor_body.html` para a grade de 3 colunas (paleta `286px` · palco `1fr` · direita `256px`) + barra de status, espelhando a descrição "Layout" do handoff README (seção Scene Creator). Carregar o JS:

```html
{% block extra_js %}
    {{ block.super }}
    <script src="{% static 'js/tabletop_editor.js' %}?v={% now 'U' %}"></script>
{% endblock %}
```

(O `_editor_body.html` deve expor: `#tt-stage` > `#tt-world` > `#tt-live` (canvas atual), as tabs/grid da paleta a partir de `token_sprites`+`tile_sprites`, os botões de ferramenta com `data-tool`, o `#tt-layers`, o `#tt-inspector` e a status bar com `#sb-hint`/`#sb-coord`/`#zoom-pct`/`#tt-meas`.) Para `tile_sprites`, ampliar `_render_editor_body` na view para incluir `_sprite_library(request.user, SpriteAsset.MAP_TILE)`.

- [ ] **Step 2: Implementar a engine**

Criar `dd3esheet/static/js/tabletop_editor.js` portando `scene.js` conforme a tabela acima. Pontos obrigatórios: ler `GridSize`/`GridMode` dos data-attrs do `.tt-canvas`; usar `htmx.ajax` para todas as mutações (drop, rotação, paint, clear) com `target:'#tt-editor', swap:'innerHTML'`; respeitar a **guarda de arrasto** já existente em `tabletop.js` (não conflitar — a engine do editor cuida de pan/zoom/ferramentas; o arrasto de token continua em `tabletop.js`).

- [ ] **Step 3: Estilos**

Em `tabletop.css`, adicionar o layout 3-colunas (`.tt-editor-grid` vira grid de 3 faixas no editor), os tiles de paleta (`.tt-ptile`, formas `circle`/`hex`/`sq`), o inspector (`.tt-inspector`), a barra de status (`.tt-statusbar`) e as classes de ferramenta (`.tool-select/place/paint/measure`, `.panning`). Consumir os tokens parchment da fatia A.

- [ ] **Step 4: Verificação manual (roteiro do handoff)**

Subir o app, abrir o editor de uma cena hex:
- arrastar um tile da paleta pro palco → cria token no hex sob o cursor;
- selecionar, girar pelo handle → persiste rotação (confirmar no poll da visão ao vivo);
- ferramenta "pintar", escolher peça de terreno, arrastar → terreno aparece (1 POST no soltar);
- "limpar terreno" remove tudo;
- régua mede em metros e hexes;
- pan (espaço/arrastar vazio) e zoom (roda) funcionam;
- camadas escondem/travam terreno e tokens.

- [ ] **Step 5: Commit**

```bash
git add dd3esheet/static/js/tabletop_editor.js dd3esheet/tabletop/templates/tabletop/editor.html dd3esheet/tabletop/templates/tabletop/partials/_editor_body.html dd3esheet/static/css/tabletop.css dd3esheet/tabletop/views.py
git commit -m "feat(mesa): Scene Creator rico (pan/zoom, paleta drag-drop, rotacao, terreno, regua, camadas)"
```

---

## Task 5: Suíte + docs

- [ ] **Step 1: Rodar a suíte**

Run: `docker compose exec web python manage.py test tabletop -v 2` e `docker compose exec web python manage.py test -v 1`
Expected: PASS.

- [ ] **Step 2: Atualizar `TABLETOP.md`**

Acrescentar uma subseção "Editor (Scene Creator)" descrevendo: ferramentas, que pan/zoom/camadas/régua são client-side, e que terreno (`TerrainCell`) e rotação (`Token.Rotation`) persistem; névoa segue retangular. Commit.

```bash
git add TABLETOP.md
git commit -m "docs: documenta o editor rico (fatia C) no TABLETOP.md"
```

---

## Self-Review (autor do plano)

**1. Cobertura vs. README "Interactions & Behavior":** pan/zoom ✅ · ferramentas select/place/paint/measure ✅ · drag-drop da paleta ✅ · seleção/rotação ✅ · pintura de terreno ✅ · régua ✅ · camadas ✅. **Névoa por célula: deliberadamente fora** (Decisão 4, alinhada ao "fora de escopo" do TABLETOP.md). Save/load/autosave do handoff: **não se aplica** (persistência é o banco, não localStorage) — registrado como adaptação.
**2. Placeholders:** o código Django/SQL/teste é literal; a engine JS (Task 4) referencia `scene.js` por faixa de linhas com contratos explícitos (data-attrs, payloads HTMX) — é a fonte concreta designada pelo handoff, não um "TODO".
**3. Consistência:** `TerrainCell(Map,Q,R,SpriteAsset)`, `Token.Rotation`, rotas `paint-terrain`/`clear-terrain`, `_parse_cells`, e o formato `cells="q,r;q,r"` aparecem idênticos em models, views, urls, testes e contrato JS. A matemática hex é reusada da fatia B (não reimplementada).

**Aviso de escopo:** esta é a fatia mais pesada e a única com model novo + engine JS extensa. Recomenda-se executá-la em sub-tasks (Tasks 1→5) com revisão entre cada uma, e revisar as "Decisões assumidas" antes de começar.
