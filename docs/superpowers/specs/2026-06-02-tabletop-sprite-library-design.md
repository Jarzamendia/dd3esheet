# Expansão da biblioteca de sprites da mesa virtual (STYLE.md + seed)

> Spec de design — 2026-06-02. Status: aguardando revisão do usuário.

## Objetivo

Ampliar o brief de arte `STYLE.md` com um conjunto **curado e genérico** de
criaturas, NPCs e mapas do D&D 3.5 que ainda **não** estão no manifesto atual, e
**registrar** esses novos assets em `sprites/seeds.py` como itens de catálogo da
biblioteca — para que apareçam no picker da mesa virtual (`tabletop`) **antes
mesmo** de a arte existir. A geração das imagens em si é um passo separado
("Claude Design"), fora deste escopo.

Direção escolhida com o usuário: **preencher lacunas SRD genéricas** (tom de
sourcebook reutilizável), **não** conteúdo específico da campanha. Volume:
**essencial (~80 entradas)**, com a seção de **Magical Beasts** completa como
destaque (hoje esse *tipo* inteiro do SRD está ausente do manifesto).

## Contexto de arquitetura (verificado no código)

- `STYLE.md` é um **brief autônomo**: cada `id` de asset é o nome do arquivo de
  imagem que o gerador produzirá (`owlbear.png`). Hoje nenhum código referencia
  esses ids.
- `sprites/views.py::search` (`GET /sprites/search/?q=&category=`) lista qualquer
  `SpriteAsset` por `Category` + `Name__icontains`. Assets **sem imagem** também
  aparecem (o app tem fallback SVG por `Kind` na mesa).
- `tabletop/views.py::_sprite_library(user, category)` filtra
  `SpriteAsset.objects.active().visible_to(user).filter(Category=category)`. O
  picker de **tokens** usa `MAP_TOKEN`; o de **fundos** usa `MAP_TILE`.
- `SpriteBinding` só importa para **amarrar** um asset a uma classe/monstro SDR
  específico. Tokens de biblioteca genéricos **não precisam** de binding —
  bastam ser descobertos por categoria/nome.
- `SpriteAsset` tem `DefaultGridWidth/DefaultGridHeight` (pegada padrão do token,
  1–20), `Slug` único, `Visibility` (`PUBLIC`/`OWNER`), `IsActive`.

## Decisão-chave: slug == id do STYLE.md (mapeamento 1:1)

Cada registro de catálogo tem `Slug` **igual** ao `id` do asset no STYLE.md
(`owlbear` → slug `owlbear`). Quando a arte for gerada e enviada, o upload casa
pelo slug. Rejeitada a alternativa de namespacing (`lib-owlbear`): quebraria o
match direto arquivo↔slug.

Categoria por tipo (conforme o picker da mesa):

| Tipo no STYLE.md | Categoria do `SpriteAsset` |
|---|---|
| `TABLETOP_TOKEN` (criaturas, NPCs) | `MAP_TOKEN` |
| `BATTLE_MAP`, `CITY_OR_WORLD_MAP` (mapas) | `MAP_TILE` |

`DefaultGridWidth/Height` vêm da pegada (footprint) do STYLE.md. Fundos
(`MAP_TILE`) não usam pegada (ficam no default 1×1). **Sem bindings.**

Pegada por tamanho D&D 3.5 (regra do próprio STYLE.md): Tiny/Small/Medium → 1×1,
montaria/criatura "longa" → 2×1, Large → 2×2, Huge → 3×3, Gargantuan → 4×4,
Colossal → 6×6.

---

## Parte A — Novas entradas no STYLE.md

Formato idêntico ao existente. Tokens:
`- <id>: TABLETOP_TOKEN, 512x512 transparent PNG, footprint <NxM>, <desc>.`
Mapas de batalha:
`- <id>: BATTLE_MAP, 2048x1536 opaque PNG, 32x24 invisible 64 px cells, <desc>, no grid.`
Mapas de cidade/mundo:
`- <id>: CITY_OR_WORLD_MAP, 2048x1536 opaque PNG, <desc>, no labels.`

**Pontos de inserção:**
- Seções de criaturas/NPCs: **entre** `SWARM AND SUMMONING TOKENS` e
  `PROP TOKENS: DUNGEON, TAVERN, AND TOWN`.
- `ADDITIONAL BATTLE MAPS`: logo após a lista `BATTLE MAPS`, antes de
  `CITY AND WORLD MAPS`.
- `ADDITIONAL CITY AND WORLD MAPS`: após `CITY AND WORLD MAPS`, antes de
  `QUALITY CHECK`.

### MAGICAL BEAST TOKENS (seção nova — maior lacuna)

| id | footprint | descrição curta |
|---|---|---|
| owlbear | 2x2 | bear-owl hybrid with beak and claws |
| griffon | 2x2 | eagle-lion griffon, wings folded circle-safe |
| hippogriff | 2x2 | horse-eagle hippogriff |
| pegasus | 2x2 | winged horse, wings tucked inside circle |
| unicorn | 2x2 | noble horned unicorn |
| worg | 1x1 | large evil wolf, worg |
| winter_wolf | 2x2 | white frost wolf |
| blink_dog | 1x1 | tan teleporting hound |
| displacer_beast | 2x2 | six-legged panther with two tentacles |
| bulette | 3x3 | armored land-shark burrower |
| ankheg | 2x2 | insectoid burrowing beast with mandibles |
| basilisk | 1x1 | eight-legged reptile |
| cockatrice | 1x1 | rooster-lizard cockatrice |
| chimera | 2x2 | lion-goat-dragon three-headed beast |
| manticore | 2x2 | lion body, bat wings, spiked tail |
| hydra_five_head | 3x3 | five-headed reptilian hydra |
| gorgon | 2x2 | iron-plated bull |
| behir | 3x3 | many-legged serpentine beast |
| sea_cat | 2x2 | finned lion-fish predator |
| gynosphinx | 2x2 | winged lion with woman's head |
| phase_spider | 2x2 | large violet phase spider |
| girallon | 2x2 | four-armed white ape |
| choker | 1x1 | small grasping aberrant beast with long arms |
| darkmantle | 1x1 | cave-clinging mantle creature |

### ADDITIONAL ANIMAL AND VERMIN TOKENS

| id | footprint | descrição |
|---|---|---|
| elephant | 3x3 | tusked elephant |
| camel | 2x1 | saddled or wild camel |
| rhinoceros | 2x2 | horned rhinoceros |
| ape | 2x2 | great ape/gorilla |
| dire_badger | 1x1 | oversized dire badger |
| monitor_lizard | 1x1 | large monitor lizard |
| giant_frog | 1x1 | oversized frog |
| giant_ant | 1x1 | soldier giant ant |

### ADDITIONAL UNDEAD TOKENS

| id | footprint | descrição |
|---|---|---|
| spectre | 1x1 | gaunt spectral undead, subtle transparency |
| ghost_apparition | 1x1 | translucent ghost, readable silhouette |
| dread_wraith | 2x2 | large hooded wraith, subtle transparency |
| devourer | 2x2 | gaunt undead with a trapped spirit in its ribcage |
| skeletal_horse | 2x1 | undead skeletal steed |
| zombie_dog | 1x1 | shambling undead hound |

### ADDITIONAL GIANT TOKENS

| id | footprint | descrição |
|---|---|---|
| cloud_giant | 3x3 | regal cloud giant with morningstar |
| storm_giant | 3x3 | violet-skinned storm giant with greatsword |
| cyclops | 3x3 | one-eyed cyclops with club |
| fomorian | 3x3 | misshapen fomorian giant |

### ADDITIONAL OUTSIDER TOKENS

| id | footprint | descrição |
|---|---|---|
| balor | 2x2 | winged flaming demon lord with sword and whip |
| marilith | 2x2 | six-armed serpent-bodied demon |
| vrock | 2x2 | vulture-headed demon |
| hezrou | 2x2 | toad-like demon brute |
| glabrezu | 3x3 | dog-headed pincered demon |
| bone_devil | 2x2 | skeletal scorpion-tailed devil |
| pit_fiend | 2x2 | winged armored arch-devil |
| planetar | 2x2 | green-skinned winged celestial with greatsword |

### ADDITIONAL ABERRATION TOKENS

| id | footprint | descrição |
|---|---|---|
| aboleth | 3x3 | huge fish-like aberration with tentacles |
| roper | 2x2 | stalagmite-shaped predator with tendrils |
| will_o_wisp | 1x1 | floating eerie light orb, subtle glow |
| drider | 2x2 | dark elf torso on a spider body |
| grell | 1x1 | floating brain-shaped aberration with beak and tentacles |

### ADDITIONAL CONSTRUCT TOKENS

| id | footprint | descrição |
|---|---|---|
| clay_golem | 2x2 | crude clay humanoid golem |
| retriever | 3x3 | four-legged spider-like construct |
| animated_object_generic | 1x1 | generic animated object with faint runes |

### ADDITIONAL DRAGON TOKENS

| id | footprint | descrição |
|---|---|---|
| dragon_wyrmling_white | 1x1 | small white dragon wyrmling with icy spines |
| dragon_wyrmling_blue | 1x1 | small blue dragon wyrmling with horn |
| dragon_wyrmling_brass | 1x1 | small brass dragon wyrmling |
| dragon_wyrmling_bronze | 1x1 | small bronze dragon wyrmling |
| dragon_wyrmling_copper | 1x1 | small copper dragon wyrmling |
| dragon_wyrmling_silver | 1x1 | small silver dragon wyrmling |
| dragon_turtle | 3x3 | huge armored dragon turtle |

### ADDITIONAL NPC TOKENS

| id | footprint | descrição |
|---|---|---|
| mayor_burgomaster | 1x1 | town mayor in chain of office |
| town_crier | 1x1 | crier with handbell |
| fisherman | 1x1 | fisher with net and basket |
| hunter_trapper | 1x1 | hunter with bow and pelts |
| gravedigger | 1x1 | gravedigger with shovel |
| jailer | 1x1 | burly jailer with key ring |
| man_at_arms | 1x1 | armored soldier with sword |
| court_wizard | 1x1 | robed advisor mage with staff |

### ADDITIONAL BATTLE MAPS

| id | descrição |
|---|---|
| castle_gatehouse | gatehouse with portcullis, murder holes, guard niches |
| castle_courtyard | enclosed courtyard, walls, well, training posts |
| keep_great_hall | great hall with long tables, hearth, dais |
| catacombs | branching burial niches, narrow halls, small shrine |
| mine_tunnels | mining tunnels, carts, support beams, ore veins |
| goblin_warren | crude cave dens, bone piles, cook fire, tunnels |
| bandit_hideout | hidden camp among rocks, tents, lookout, loot |
| arena_pit | sand fighting pit ringed by stone tiers |

### ADDITIONAL CITY AND WORLD MAPS

| id | descrição |
|---|---|
| dwarven_underground_city | carved stone halls, bridges, forges, vaults |
| elven_forest_city | tree platforms, walkways, glades, streams |
| underdark_region | underground caverns, tunnels, chasms, fungus zones |
| mountain_range_region | peaks, passes, foothills, rivers, mines |
| desert_region | dunes, oasis, rocky mesas, ruins, caravan tracks |

**Total: ~86 entradas.** Cada seção é trimável se algo soar supérfluo na revisão.

---

## Parte B — Registro em `sprites/seeds.py`

Adicionar duas listas de catálogo no nível do módulo e um laço em
`seed_sprites()`. Reutilizar o helper `_asset`, estendido com pegada opcional.

```python
# (slug, nome_pt, grid_w, grid_h) — Slug casa 1:1 com o id do STYLE.md.
TABLETOP_TOKEN_LIBRARY = [
    ('owlbear', 'Urso-coruja', 2, 2),
    # ... todas as criaturas e NPCs da Parte A ...
]

# (slug, nome_pt) — fundos (MAP_TILE) não usam pegada.
TABLETOP_MAP_LIBRARY = [
    ('castle_gatehouse', 'Portão do castelo'),
    # ... todos os mapas da Parte A ...
]
```

`_asset` ganha `grid_w=1, grid_h=1` (defaults preservam as chamadas atuais de
classe/combatente/monstro, que já são 1×1) e passa a setar
`DefaultGridWidth/Height`. Em `seed_sprites()`:

```python
for slug, name, gw, gh in TABLETOP_TOKEN_LIBRARY:
    assets[slug] = _asset(slug, name, SpriteAsset.MAP_TOKEN, gw, gh)
for slug, name in TABLETOP_MAP_LIBRARY:
    assets[slug] = _asset(slug, name, SpriteAsset.MAP_TILE)
```

Propriedades dos registros: `Visibility=PUBLIC`, `IsActive=True`, **sem imagem**
(mantém verde o `test_seed_sprites_does_not_generate_image_files`), **sem
binding**. Idempotente por slug (mesma lógica do `_asset` atual). Roda também em
produção via `seed_all` — são dados de catálogo de referência, sem credenciais.

Nomes em PT seguem o estilo do seed atual (`'Urso Pardo'`, `'Lobo'`); o slug
permanece em inglês (= id do STYLE.md = nome do arquivo gerado).

---

## Parte C — Testes (TDD, regra dura do AGENTS.md)

Novo `TabletopLibrarySeedTests(TestCase)` em `sprites/tests.py`. Teste **antes**
do código:

1. `test_seed_creates_token_and_tile_library`: roda `seed_sprites()`; um token de
   amostra (`owlbear`) tem `Category == MAP_TOKEN` e `DefaultGridWidth/Height ==
   2/2`; um mapa de amostra (`catacombs`) tem `Category == MAP_TILE`. Conta de
   criados = `len(TABLETOP_TOKEN_LIBRARY) + len(TABLETOP_MAP_LIBRARY)`.
2. `test_library_assets_have_no_bindings`: `SpriteBinding` para os slugs de
   biblioteca == 0.
3. `test_library_seed_is_idempotent`: rodar duas vezes não duplica nem muda
   slugs (conta de `SpriteAsset` estável).
4. `test_library_token_discoverable_via_search`: usuário logado; `GET
   /sprites/search/?category=map_token` inclui um token de biblioteca no JSON
   (garante que aparece no picker da mesa).

Os testes existentes de seed devem seguir verdes (sobretudo
`test_seed_sprites_does_not_generate_image_files`).

## Parte D — Docs

Em `docs/seeds.md`, sob "Sprites", um bullet: o seed também registra um
**catálogo de biblioteca da mesa virtual** — placeholders públicos e sem imagem
(`MAP_TOKEN` para criaturas/NPCs, `MAP_TILE` para mapas), com `Slug` = id do
STYLE.md, descobertos no picker por categoria; a arte real é enviada depois.

## Fora de escopo

- Gerar as imagens (passo "Claude Design").
- Conteúdo específico da campanha (Fronteira de Elsir / Red Hand of Doom).
- Criar `SpriteBinding`/variantes para os assets de biblioteca.
- Importador que casa arquivos gerados ↔ slug (futuro; o slug 1:1 já prepara).

## Sequência de implementação

1. Escrever `TabletopLibrarySeedTests` (falhando).
2. `sprites/seeds.py`: listas + `_asset` com pegada + laço em `seed_sprites()`.
3. Rodar `python manage.py test sprites` até verde.
4. Adicionar as seções na `STYLE.md` (Parte A), com ids == slugs do seed.
5. Bullet em `docs/seeds.md`.
6. Suíte completa verde (`python manage.py test`).
