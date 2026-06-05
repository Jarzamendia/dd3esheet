# Separar terreno básico de terreno detalhado

**Data:** 2026-06-05
**Status:** Design aprovado (aguardando revisão do spec)

## Problema

Todos os ~96 "map pieces" de terreno hoje são tratados como um bloco único:

- **Modelo/dados:** todos caem na categoria `SpriteAsset.MAP_TILE`.
- **Biblioteca (app `sprites`):** todos aparecem num único grupo "Map Pieces"
  (dirigido pela seção `MAP PIECES` do manifesto).
- **Editor de Cena (app `tabletop`):** a ferramenta Terreno mostra uma grade
  única e plana com todos os tiles.

Não existe nenhuma noção de "terreno básico" (preenchimentos sólidos, genéricos
e tileáveis que cobrem área) versus "terreno detalhado" (estradas, rios, pontes,
muros, cercas, árvores, bordas, junções — peças com forma/feature). O usuário
precisa dessa separação tanto no editor quanto na biblioteca.

Exemplos citados de terreno **detalhado**: `dirt_road_straight`, `river_segment`
(ambos no manifesto base, descritos como segmentos tileáveis).

## Decisões tomadas (brainstorming)

1. **Classificação:** tag explícita e curada no manifesto (não heurística).
2. **Editor:** apresentar os dois grupos como abas/seções separadas — na prática,
   um segmented control "Básico | Detalhes" no topo do painel da ferramenta
   Terreno.
3. **Sem migração de banco:** seguindo o precedente do campo `subcategory`
   (lido direto do manifesto, sem coluna no modelo), o `terrain_kind` vive
   apenas no manifesto.

## Design

### 1. Classificação — campo `terrain_kind` no manifesto

Adicionar um campo curado a cada entrada de `MAP_PIECE` nos dois manifestos
(`sprite_manifest.json` e `sprite_manifest_tokens_expansion.json`):

```json
"terrain_kind": "base"   // ou "detail"
```

**Regra de curadoria:**

- **`base`** = preenchimento sólido/genérico, tileável, que cobre área
  ("ground / floor / water / grass / mud *tile/patch*"). Você pinta uma cena
  inteira com ele e os tiles encaixam um no outro.
- **`detail`** = qualquer peça com forma/feature: estradas, rios, pontes,
  trilhas, muros, cercas, escadas, portas, poços, árvores, arbustos, rochas,
  bordas/transições (`*_edge`), junções (`*_t_junction`, `*_crossroads`,
  `*_curve`, `*_fork`), perigos (`*_sinkhole`, `lava_*`).

**Classificação inicial proposta — `base`:**

Manifesto base: `dungeon_floor_tile`, `cave_floor_tile`, `deep_water_tile`,
`shallow_water_tile`, `grass_field_tile`.

Expansão: `terrain_village_grass_low_tile`,
`terrain_village_irregular_stone_floor`, `terrain_city_courtyard_stone_tile`,
`terrain_city_flagstone_floor_tile`, `terrain_city_castle_floor_tile`,
`terrain_city_inner_courtyard_tile`, `terrain_swamp_dark_water_tile`,
`terrain_swamp_mud_tile`, `terrain_swamp_dry_ground_tile`,
`terrain_rocky_mountain_ground_tile`.

**Todo o resto = `detail`.**

**Borderline (decisão do usuário na revisão):** `dungeon_rubble_floor`,
`rocky_ground_patch`, `swamp_muck_tile`, `cobblestone_street`,
`terrain_village_mud_patch`. (Proposta padrão: `rocky_ground_patch`,
`swamp_muck_tile`, `cobblestone_street` → `base`; `dungeon_rubble_floor`,
`terrain_village_mud_patch` → `detail`.)

**Tiles enviados pelo usuário** (sem entrada no manifesto): default `base`.

### 2. `manifest_data.py` — helper de lookup

Adicionar:

```python
def terrain_kind_by_slug():
    """{slug: 'base'|'detail'} para todos os map pieces do manifesto."""
```

Construído a partir de `all_assets()`, lendo `asset.get('terrain_kind', 'base')`
para entradas de tipo `MAP_PIECE`. Cacheável (`functools.lru_cache`) como os
outros acessores do módulo.

### 3. Editor de Cena — `scene_editor.js` + `_tile_library_payload`

**Backend (`tabletop/views.py`):** `_tile_library_payload(user)` passa a incluir
`kind` por tile, anexando do `terrain_kind_by_slug()` (default `'base'` para
tiles fora do manifesto):

```python
{'id': s.id, 'name': s.Name, 'url': s.original_url, 'slug': s.Slug,
 'kind': kinds.get(s.Slug, 'base')}
```

**Frontend (`scene_editor.js`, `terrainPanel()`):**

- Novo estado `terrainKind = 'base'`.
- Segmented control "Básico | Detalhes" no topo do painel da ferramenta Terreno
  (espelhando o toggle Pincel/Balde existente). Trocar de aba re-renderiza a
  grade.
- A grade filtra `tileLib` por `t.kind === terrainKind` **e** pelo termo de
  busca.
- `terrainActive` inicial = primeiro tile com `kind === 'base'` (fallback: o
  primeiro tile, se não houver `base`).

A pintura em si (TerrainCell, Pincel/Balde, eyedropper, apagar) **não muda** —
ambos os tipos continuam pintando a mesma camada `S.terrain`.

### 4. Biblioteca — `sprites/views.py` `_library_groups_for_user`

`_library_row` já recebe o `manifest_asset`, então lê `terrain_kind` de graça
(adicionar `'terrain_kind'` ao dict da row).

Em `_library_groups_for_user`, ao processar o grupo cuja chave é `map_pieces`,
**particionar as rows em dois grupos emitidos** conforme `row['terrain_kind']`:

- `map_pieces_base` — rótulo "Terreno Básico"
- `map_pieces_detail` — rótulo "Terreno Detalhado"

Mesma seção de origem (`MAP PIECES`), dois cards de grupo na UI. A lista
`GROUPS` de seções **não muda** (a partição é por asset, não por seção). Glyph
`hex` para ambos; accents podem diferir (`--forest` para básico, `--iron` para
detalhado) — ajuste cosmético.

Templates da biblioteca (`_card.html` / partial de grupo): só precisam suportar
os dois novos cards de grupo e seus empty-states; sem mudança estrutural.

### Fora de escopo

- **Seletor de fundo de cena** (`bg_sprites` em `manage`): continua listando
  todo `MAP_TILE` (inclui battle maps + todos os map pieces). Não é afetado.
- **Modelo `SpriteAsset`:** sem novo campo, sem migração.

## Fluxo de dados

```
manifesto (terrain_kind)
   │
   ├─ manifest_data.terrain_kind_by_slug() ──► tabletop._tile_library_payload (kind)
   │                                              └─► scene_editor.js (filtro Básico/Detalhes)
   │
   └─ manifest_data.all_assets() ──► sprites._library_row (terrain_kind)
                                        └─► _library_groups_for_user (particiona map_pieces)
```

## Testes

- **`sprites` (manifest):** todo `MAP_PIECE` tem `terrain_kind` válido
  (`base`/`detail`); `terrain_kind_by_slug()` retorna o esperado para
  ids conhecidos (`dirt_road_straight` → `detail`, `grass_field_tile` → `base`).
- **`tabletop`:** `_tile_library_payload` inclui `kind`; tile fora do manifesto
  cai em `base`; pelo menos um `base` e um `detail` presentes no payload de seed.
- **`sprites` (biblioteca):** a view emite os grupos `map_pieces_base` e
  `map_pieces_detail` com as contagens corretas e cada tile no grupo certo.

## Arquivos tocados

- `dd3esheet/sprites/fixtures/sprite_manifest.json` — `terrain_kind` nos 26 map pieces
- `dd3esheet/sprites/fixtures/sprite_manifest_tokens_expansion.json` — `terrain_kind` nos 70 map pieces
- `dd3esheet/sprites/manifest_data.py` — helper `terrain_kind_by_slug()`
- `dd3esheet/tabletop/views.py` — `_tile_library_payload` inclui `kind`
- `dd3esheet/static/js/scene_editor.js` — segmented control + filtro de kind
- `dd3esheet/sprites/views.py` — `_library_row` + `_library_groups_for_user` particiona
- templates da biblioteca (`sprites/partials/_card.html` e/ou grupo) — rótulos/empty-state se necessário
- testes em `sprites/tests.py` e `tabletop/tests.py`

**Sem migração de banco.**
