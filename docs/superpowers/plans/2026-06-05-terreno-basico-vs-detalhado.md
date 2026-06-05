# Terreno Básico vs Detalhado — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Separar os "map pieces" de terreno em **básico** (preenchimentos sólidos tileáveis) e **detalhado** (estradas, rios, bordas, estruturas) tanto no Editor de Cena quanto na biblioteca de sprites.

**Architecture:** Tag curada `terrain_kind` ("base"/"detail") em cada `MAP_PIECE` dos dois manifestos JSON. Um helper em `manifest_data.py` expõe `{slug: kind}`. O editor (`_tile_library_payload` → `scene_editor.js`) ganha um segmented control que filtra por kind; a biblioteca (`_library_groups_for_user`) particiona o grupo "Map Pieces" em dois grupos. Sem migração de banco.

**Tech Stack:** Django 4.2, fixtures JSON, JS vanilla (sem build), testes via `python manage.py test`.

**Convenções de execução:**
- Todos os comandos `python manage.py test ...` rodam a partir do diretório `dd3esheet/` (onde está `manage.py`), com o venv `dd3esheet/.venv` ativo.
- Não há infraestrutura de testes JS no repo (sem `package.json`); a Task 4 (scene_editor.js) é verificada manualmente conforme descrito.

---

## File Structure

- `dd3esheet/sprites/fixtures/sprite_manifest.json` — +`terrain_kind` em 26 map pieces (modificado)
- `dd3esheet/sprites/fixtures/sprite_manifest_tokens_expansion.json` — +`terrain_kind` em 70 map pieces (modificado)
- `scripts/tag_terrain_kind.py` — script único de tagueamento idempotente (criado)
- `dd3esheet/sprites/manifest_data.py` — helper `terrain_kind_by_slug()` (modificado)
- `dd3esheet/tabletop/views.py` — `_tile_library_payload` inclui `kind` (modificado)
- `dd3esheet/static/js/scene_editor.js` — segmented control Básico/Detalhes + filtro (modificado)
- `dd3esheet/sprites/views.py` — `_library_row` lê `terrain_kind`; `_library_groups_for_user` particiona `map_pieces` (modificado)
- `dd3esheet/sprites/tests.py`, `dd3esheet/tabletop/tests.py` — testes (modificados)

---

## Task 1: Taguear `terrain_kind` nos manifestos

**Files:**
- Create: `scripts/tag_terrain_kind.py`
- Modify: `dd3esheet/sprites/fixtures/sprite_manifest.json`
- Modify: `dd3esheet/sprites/fixtures/sprite_manifest_tokens_expansion.json`
- Test: `dd3esheet/sprites/tests.py`

- [ ] **Step 1: Escrever o teste de integridade dos dados (falha)**

Adicionar ao final de `dd3esheet/sprites/tests.py`:

```python
from django.test import SimpleTestCase

from .manifest_data import all_assets


class TerrainKindManifestTests(SimpleTestCase):
    def _map_pieces(self):
        return [a for a in all_assets() if a.get('type') == 'MAP_PIECE']

    def test_every_map_piece_has_valid_terrain_kind(self):
        missing = [a['id'] for a in self._map_pieces()
                   if a.get('terrain_kind') not in ('base', 'detail')]
        self.assertEqual(missing, [], f'map pieces sem terrain_kind valido: {missing}')

    def test_known_base_and_detail_examples(self):
        kinds = {a['id']: a.get('terrain_kind') for a in self._map_pieces()}
        self.assertEqual(kinds.get('grass_field_tile'), 'base')
        self.assertEqual(kinds.get('dungeon_floor_tile'), 'base')
        self.assertEqual(kinds.get('terrain_swamp_mud_tile'), 'base')
        self.assertEqual(kinds.get('dirt_road_straight'), 'detail')
        self.assertEqual(kinds.get('river_segment'), 'detail')
        self.assertEqual(kinds.get('terrain_village_fence_gate'), 'detail')
```

- [ ] **Step 2: Rodar e verificar que falha**

Run: `python manage.py test sprites.tests.TerrainKindManifestTests`
Expected: FAIL — `terrain_kind` ausente (None ∉ {'base','detail'}).

- [ ] **Step 3: Escrever o script de tagueamento**

Criar `scripts/tag_terrain_kind.py`:

```python
"""Tagueia `terrain_kind` em todos os MAP_PIECE dos manifestos de sprites.

Idempotente: rode quantas vezes quiser. Slugs em BASE_SLUGS viram 'base';
qualquer outro MAP_PIECE vira 'detail'.
"""
import json
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent.parent / 'dd3esheet' / 'sprites' / 'fixtures'
MANIFESTS = [
    FIXTURES / 'sprite_manifest.json',
    FIXTURES / 'sprite_manifest_tokens_expansion.json',
]

BASE_SLUGS = {
    # manifesto base
    'dungeon_floor_tile', 'cave_floor_tile', 'deep_water_tile',
    'shallow_water_tile', 'grass_field_tile', 'rocky_ground_patch',
    'swamp_muck_tile', 'cobblestone_street',
    # expansao
    'terrain_village_grass_low_tile', 'terrain_village_irregular_stone_floor',
    'terrain_city_courtyard_stone_tile', 'terrain_city_flagstone_floor_tile',
    'terrain_city_castle_floor_tile', 'terrain_city_inner_courtyard_tile',
    'terrain_swamp_dark_water_tile', 'terrain_swamp_mud_tile',
    'terrain_swamp_dry_ground_tile', 'terrain_rocky_mountain_ground_tile',
}


def tag(path):
    data = json.loads(path.read_text(encoding='utf-8'))
    changed = 0
    for section in data.get('sections', []):
        for asset in section.get('assets', []):
            if asset.get('type') != 'MAP_PIECE':
                continue
            kind = 'base' if asset['id'] in BASE_SLUGS else 'detail'
            if asset.get('terrain_kind') != kind:
                asset['terrain_kind'] = kind
                changed += 1
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    return changed


if __name__ == '__main__':
    for manifest in MANIFESTS:
        n = tag(manifest)
        print(f'{manifest.name}: {n} map pieces atualizados')
```

> Nota: `indent=1` espelha a indentação existente do `sprite_manifest.json`. Revise o diff antes de commitar para confirmar que só foram adicionadas linhas `terrain_kind` (e não houve reformatação massiva). Se o diff ficar ruidoso, ajuste `indent`/separators até o diff ficar limpo.

- [ ] **Step 4: Rodar o script**

Run (da raiz do repo): `python scripts/tag_terrain_kind.py`
Expected: imprime `sprite_manifest.json: 26 map pieces atualizados` e `sprite_manifest_tokens_expansion.json: 70 map pieces atualizados`.

- [ ] **Step 5: Conferir o diff**

Run: `git diff --stat dd3esheet/sprites/fixtures/`
Expected: apenas os dois manifestos alterados; inspecione `git diff` para confirmar que as mudanças são só inserções de `"terrain_kind": ...`.

- [ ] **Step 6: Rodar o teste e verificar que passa**

Run: `python manage.py test sprites.tests.TerrainKindManifestTests`
Expected: PASS (2 testes).

- [ ] **Step 7: Commit**

```bash
git add scripts/tag_terrain_kind.py dd3esheet/sprites/fixtures/sprite_manifest.json dd3esheet/sprites/fixtures/sprite_manifest_tokens_expansion.json dd3esheet/sprites/tests.py
git commit -m "feat(sprites): tag terrain_kind (base/detail) nos map pieces"
```

---

## Task 2: Helper `terrain_kind_by_slug()` em `manifest_data.py`

**Files:**
- Modify: `dd3esheet/sprites/manifest_data.py`
- Test: `dd3esheet/sprites/tests.py`

- [ ] **Step 1: Escrever o teste (falha)**

Adicionar à classe `TerrainKindManifestTests` em `dd3esheet/sprites/tests.py`:

```python
    def test_terrain_kind_by_slug_helper(self):
        from .manifest_data import terrain_kind_by_slug
        mapping = terrain_kind_by_slug()
        self.assertEqual(mapping['grass_field_tile'], 'base')
        self.assertEqual(mapping['dirt_road_straight'], 'detail')
        # so map pieces entram no mapa
        self.assertNotIn('barbarian_class_icon', mapping)
        # cobre todos os map pieces
        ids = {a['id'] for a in self._map_pieces()}
        self.assertEqual(set(mapping), ids)
```

- [ ] **Step 2: Rodar e verificar que falha**

Run: `python manage.py test sprites.tests.TerrainKindManifestTests.test_terrain_kind_by_slug_helper`
Expected: FAIL — `ImportError: cannot import name 'terrain_kind_by_slug'`.

- [ ] **Step 3: Implementar o helper**

Em `dd3esheet/sprites/manifest_data.py`, depois de `def all_assets():` (perto da linha 231), adicionar:

```python
@functools.lru_cache(maxsize=1)
def terrain_kind_by_slug():
    """{slug: 'base'|'detail'} para todos os map pieces do manifesto."""
    return {
        asset['id']: asset.get('terrain_kind', 'detail')
        for asset in all_assets()
        if asset.get('type') == 'MAP_PIECE'
    }
```

(`functools` já está importado no topo do módulo.)

- [ ] **Step 4: Rodar o teste e verificar que passa**

Run: `python manage.py test sprites.tests.TerrainKindManifestTests`
Expected: PASS (3 testes).

- [ ] **Step 5: Commit**

```bash
git add dd3esheet/sprites/manifest_data.py dd3esheet/sprites/tests.py
git commit -m "feat(sprites): helper terrain_kind_by_slug()"
```

---

## Task 3: `_tile_library_payload` inclui `kind` (tabletop)

**Files:**
- Modify: `dd3esheet/tabletop/views.py:83-88`
- Test: `dd3esheet/tabletop/tests.py`

- [ ] **Step 1: Escrever o teste (falha)**

Localize o teste existente `test_tile_library_lists_map_tiles_only` em `dd3esheet/tabletop/tests.py` (linha ~480) para reusar o padrão de setup. Adicionar um novo teste na mesma classe:

```python
    def test_tile_library_payload_includes_kind(self):
        from .views import _tile_library_payload
        from sprites.models import SpriteAsset
        # tiles de seed do manifesto
        SpriteAsset.objects.update_or_create(
            Slug='grass_field_tile',
            defaults={'Name': 'Grass Field Tile', 'Category': SpriteAsset.MAP_TILE,
                      'Visibility': SpriteAsset.PUBLIC, 'IsActive': True})
        SpriteAsset.objects.update_or_create(
            Slug='dirt_road_straight',
            defaults={'Name': 'Dirt Road Straight', 'Category': SpriteAsset.MAP_TILE,
                      'Visibility': SpriteAsset.PUBLIC, 'IsActive': True})
        # tile fora do manifesto -> default 'base'
        SpriteAsset.objects.create(
            Slug='custom-uploaded-tile', Name='Custom', Category=SpriteAsset.MAP_TILE,
            Visibility=SpriteAsset.PUBLIC, IsActive=True)

        payload = _tile_library_payload(self.owner)
        kinds = {t['slug']: t['kind'] for t in payload}
        self.assertEqual(kinds['grass_field_tile'], 'base')
        self.assertEqual(kinds['dirt_road_straight'], 'detail')
        self.assertEqual(kinds['custom-uploaded-tile'], 'base')
```

> Nota: confirme o nome do atributo de usuário no setup da classe (`self.owner` vs outro). Se a classe usa outro nome, ajuste. O teste `test_tile_library_lists_map_tiles_only` existente mostra o padrão correto.

- [ ] **Step 2: Rodar e verificar que falha**

Run: `python manage.py test tabletop.tests` (filtre pelo método se preferir)
Expected: FAIL — `KeyError: 'kind'`.

- [ ] **Step 3: Implementar**

Em `dd3esheet/tabletop/views.py`, substituir `_tile_library_payload` (linhas 83-88) por:

```python
def _tile_library_payload(user):
    """Tiles de terreno da biblioteca (MAP_TILE) para a paleta do editor."""
    from sprites.manifest_data import terrain_kind_by_slug
    kinds = terrain_kind_by_slug()
    return [
        {'id': s.id, 'name': s.Name, 'url': s.original_url, 'slug': s.Slug,
         'kind': kinds.get(s.Slug, 'base')}
        for s in _sprite_library(user, SpriteAsset.MAP_TILE)
    ]
```

> Se já houver um import de `sprites.manifest_data` no topo de `views.py`, mova `terrain_kind_by_slug` para lá em vez do import local. Verifique os imports existentes no topo do arquivo.

- [ ] **Step 4: Rodar o teste e verificar que passa**

Run: `python manage.py test tabletop.tests`
Expected: PASS (incluindo o teste existente `test_tile_library_lists_map_tiles_only`).

- [ ] **Step 5: Commit**

```bash
git add dd3esheet/tabletop/views.py dd3esheet/tabletop/tests.py
git commit -m "feat(mesa): _tile_library_payload inclui kind do terreno"
```

---

## Task 4: Segmented control Básico/Detalhes no editor (`scene_editor.js`)

**Files:**
- Modify: `dd3esheet/static/js/scene_editor.js` (estado perto da linha 59; `terrainPanel()` linhas 385-419)

Sem testes automatizados (sem infra JS). Verificação manual ao final.

- [ ] **Step 1: Adicionar estado `terrainKind`**

Em `dd3esheet/static/js/scene_editor.js`, perto da linha 59 onde está:

```js
  let terrainActive = tileLib.length ? tileLib[0].id : null;
  let terrainMode = 'brush';
```

Substituir por:

```js
  const firstBase = (tileLib.find(t => t.kind === 'base') || tileLib[0] || {}).id || null;
  let terrainActive = firstBase;
  let terrainMode = 'brush';
  let terrainKind = 'base';
```

- [ ] **Step 2: Adicionar o segmented control de kind e filtrar a grade**

Em `terrainPanel()` (a partir da linha 388, dentro do `if (tool === 'terrain') {`), logo após o bloco que monta o segmented control de `['brush', 'fill']` e faz `wrap.appendChild(seg);` (linha 395), inserir um segundo segmented control:

```js
      const kseg = el('div', 'sc-seg');
      [['base', 'Básico'], ['detail', 'Detalhes']].forEach(([k, label]) => {
        const b = el('button', terrainKind === k ? 'is-active' : '', label);
        b.addEventListener('click', () => { terrainKind = k; renderPanel(); });
        kseg.appendChild(b);
      });
      wrap.appendChild(kseg);
```

Depois, na função interna `fill(term)` (linha 400), trocar a linha do filtro:

```js
        const matches = tileLib.filter(t => !term || (t.name || '').toLowerCase().includes(term));
```

por:

```js
        const matches = tileLib.filter(t =>
          (t.kind || 'base') === terrainKind &&
          (!term || (t.name || '').toLowerCase().includes(term)));
```

> Resultado: a grade da ferramenta Terreno mostra só tiles do kind ativo; trocar Básico/Detalhes re-renderiza o painel inteiro (o segmented control reflete o estado via `is-active`). O conta-gotas (`eyedrop`) e a pintura não mudam. A classe `.sc-seg` já existe e é reutilizada — sem CSS novo.

- [ ] **Step 3: Verificação manual**

1. Da pasta `dd3esheet/`: `python manage.py runserver`.
2. Garanta que a biblioteca foi semeada: `python manage.py seed_sprite_library` (se ainda não rodou nesta base).
3. Abra uma cena no Editor de Cena (`/mesa/<slug>/map/<id>/editor`), selecione a ferramenta **Terreno**.
4. Confirme: dois segmented controls (Pincel/Balde e Básico/Detalhes). Em **Básico** aparecem só preenchimentos (grass, floor, water tiles); em **Detalhes** aparecem estradas/rios/cercas/árvores.
5. A busca continua filtrando dentro do kind ativo. Pintar e o conta-gotas (Alt+clique) seguem funcionando.

- [ ] **Step 4: Commit**

```bash
git add dd3esheet/static/js/scene_editor.js
git commit -m "feat(mesa): abas Basico/Detalhes na ferramenta Terreno do editor"
```

---

## Task 5: Particionar "Map Pieces" na biblioteca (`sprites/views.py`)

**Files:**
- Modify: `dd3esheet/sprites/views.py:62-100` (`_library_row`), `:103-128` (`_library_groups_for_user`)
- Test: `dd3esheet/sprites/tests.py`

- [ ] **Step 1: Escrever o teste (falha)**

Adicionar uma nova classe a `dd3esheet/sprites/tests.py`:

```python
from django.test import TestCase
from .models import SpriteAsset
from .views import _library_groups_for_user


class LibraryTerrainSplitTests(TestCase):
    def setUp(self):
        for slug, name in [('grass_field_tile', 'Grass Field Tile'),
                           ('dungeon_floor_tile', 'Dungeon Floor Tile'),
                           ('dirt_road_straight', 'Dirt Road Straight'),
                           ('river_segment', 'River Segment')]:
            SpriteAsset.objects.update_or_create(
                Slug=slug,
                defaults={'Name': name, 'Category': SpriteAsset.MAP_TILE,
                          'Visibility': SpriteAsset.PUBLIC, 'IsActive': True})

    def test_map_pieces_split_into_base_and_detail_groups(self):
        groups = {g['key']: g for g in _library_groups_for_user(None)}
        self.assertNotIn('map_pieces', groups)
        self.assertIn('map_pieces_base', groups)
        self.assertIn('map_pieces_detail', groups)

        base_slugs = {r['id'] for r in groups['map_pieces_base']['assets']}
        detail_slugs = {r['id'] for r in groups['map_pieces_detail']['assets']}
        self.assertIn('grass_field_tile', base_slugs)
        self.assertIn('dungeon_floor_tile', base_slugs)
        self.assertIn('dirt_road_straight', detail_slugs)
        self.assertIn('river_segment', detail_slugs)
        self.assertEqual(base_slugs & detail_slugs, set())
        self.assertEqual(groups['map_pieces_base']['visible_count'], len(base_slugs))
```

- [ ] **Step 2: Rodar e verificar que falha**

Run: `python manage.py test sprites.tests.LibraryTerrainSplitTests`
Expected: FAIL — `'map_pieces_base'` ausente (ainda existe só `map_pieces`).

- [ ] **Step 3: `_library_row` expõe `terrain_kind`**

Em `dd3esheet/sprites/views.py`, dentro do dict retornado por `_library_row` (perto da linha 86, junto de `'modular'`), adicionar:

```python
        'terrain_kind': manifest_asset.get('terrain_kind', ''),
```

- [ ] **Step 4: Particionar em `_library_groups_for_user`**

Substituir o corpo do loop em `_library_groups_for_user` (linhas 116-127) por:

```python
    groups = []
    for group in section_groups():
        rows = []
        for manifest_asset in group['assets']:
            asset = visible_assets.get(manifest_asset['id'])
            if asset:
                rows.append(_library_row(asset, manifest_asset, group))
        if group['key'] == 'map_pieces':
            groups.extend(_split_map_pieces(group, rows))
        else:
            groups.append({
                **group,
                'assets': rows,
                'visible_count': len(rows),
                'grid_class': _grid_class(group['key']),
            })
    return groups
```

E adicionar, logo acima de `def _library_groups_for_user(user):` (linha 103), o helper:

```python
def _split_map_pieces(group, rows):
    """Quebra o grupo 'Map Pieces' em Terreno Básico e Terreno Detalhado."""
    base_assets = [a for a in group['assets'] if a.get('terrain_kind') == 'base']
    parts = [
        ('map_pieces_base', 'Terreno Básico', '--forest', base_assets,
         [r for r in rows if r['terrain_kind'] == 'base']),
        ('map_pieces_detail', 'Terreno Detalhado', '--iron',
         [a for a in group['assets'] if a.get('terrain_kind') != 'base'],
         [r for r in rows if r['terrain_kind'] != 'base']),
    ]
    out = []
    for key, label, accent, manifest_assets, part_rows in parts:
        out.append({
            **group,
            'key': key,
            'label': label,
            'accent': accent,
            'assets': part_rows,
            'count': len(manifest_assets),
            'visible_count': len(part_rows),
            'grid_class': _grid_class('map_pieces'),
        })
    return out
```

> Notas: o template `library.html` itera `groups` genericamente (usa `key`, `label`, `accent`, `glyph`, `count`, `visible_count`, `grid_class`), então dois grupos bem-formados bastam — sem mudança de template. O `glyph` vem herdado via `**group` (continua `hex`). `count` é o total da seção naquele kind; `visible_count` é o que o usuário enxerga.

- [ ] **Step 5: Rodar o teste e verificar que passa**

Run: `python manage.py test sprites.tests.LibraryTerrainSplitTests`
Expected: PASS.

- [ ] **Step 6: Verificação manual rápida da biblioteca**

Abrir a biblioteca de sprites no navegador e confirmar dois cards de grupo ("Terreno Básico" e "Terreno Detalhado") com a navegação lateral e contagens corretas, no lugar do antigo "Map Pieces".

- [ ] **Step 7: Commit**

```bash
git add dd3esheet/sprites/views.py dd3esheet/sprites/tests.py
git commit -m "feat(sprites): biblioteca separa Terreno Basico de Detalhado"
```

---

## Task 6: Suíte completa verde

**Files:** nenhum (validação)

- [ ] **Step 1: Rodar a suíte dos dois apps**

Run: `python manage.py test sprites tabletop`
Expected: PASS, sem regressões (incluir o número de testes no relato).

- [ ] **Step 2: Rodar a suíte inteira (sanidade)**

Run: `python manage.py test`
Expected: PASS — todos os testes verdes.

---

## Self-Review (preenchido pelo autor do plano)

**Cobertura do spec:**
- §1 Classificação `terrain_kind` no manifesto → Task 1.
- §2 helper `terrain_kind_by_slug()` → Task 2.
- §3 Editor (`_tile_library_payload` kind + segmented control) → Tasks 3 e 4.
- §4 Biblioteca (partição `map_pieces`) → Task 5.
- §Testes → Tasks 1,2,3,5 + suíte na Task 6.
- §Fora de escopo (bg_sprites, sem migração) → respeitado (nenhuma task toca `manage`/modelo).

**Consistência de tipos/nomes:** `terrain_kind` (manifesto/rows), `kind` (payload do editor e `t.kind` no JS), `terrain_kind_by_slug()`, grupos `map_pieces_base`/`map_pieces_detail`, helper `_split_map_pieces`. Usados de forma consistente entre tasks.

**Borderline resolvidos (aprovados):** `rocky_ground_patch`, `swamp_muck_tile`, `cobblestone_street` → base; `dungeon_rubble_floor`, `terrain_village_mud_patch` → detail (este último não está em BASE_SLUGS, logo cai em detail automaticamente).
