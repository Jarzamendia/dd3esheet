# Mesa virtual / criador de mapas (`tabletop`)

Spec viva do recurso de **mesa virtual compartilhada**. Mantenha este arquivo atualizado
conforme o build avança.

## Visão geral

O grupo joga D&D 3.5 à distância e quer uma mesa virtual. O **mestre** cria mapas (visão de
mundo/cidade e mapas de batalha/dungeon), compartilha **um único link** com a mesa e controla
qual cena está "no ar". Os **jogadores**, só com o link (sem login), arrastam suas miniaturas
como numa mesa física. O mestre posiciona inimigos, props decorativos e esconde áreas com
**névoa retangular**. **Não há automação de combate** — é uma mesa visual compartilhada.

O recurso reaproveita o padrão do app `initiative` (dono + slug público + polling HTMX) e a
infraestrutura do app `sprites` (categorias `map_token`/`map_tile`, campos de pegada
`DefaultGridWidth/Height` e âncora `AnchorX/Y`). Imagens são guardadas **sempre** via `sprites`.

## Decisões

1. **Criação do mapa:** híbrido — imagem de fundo + props decorativos por cima (sem editor de tiles).
2. **Controle:** trust-based. Qualquer um com o link move as miniaturas dos jogadores; inimigos e
   props são movidos só pelo mestre.
3. **Link/cenas:** uma "mesa" (link único) com várias cenas; o mestre troca a cena ativa (controle de cena).
4. **Movimento:** arrastar e soltar, com um JS vanilla pequeno (sem framework, sem build step).
5. **Névoa:** regiões retangulares ocultas (não por hexágono).
6. **Grade:** hexagonal (batalha/dungeon) **ou** livre (mundi/cidade), escolhida por mapa.
7. **Sprites:** upload no próprio app (cria `SpriteAsset`) **+** picker da biblioteca via `/sprites/search/`.

Nomenclatura (ajustável): app `tabletop`, URL `/mesa/`, label no nav **Mesa**
(segue o padrão `initiative` → `/iniciativa/`).

## Modelos (`tabletop/models.py`, banco `default`, PascalCase)

### `GameTable` — a mesa compartilhável (espelha `initiative.Encounter`)
| Campo | Tipo | Notas |
|---|---|---|
| `Owner` | FK(User, CASCADE) | o mestre |
| `Name` | Char(120) | default `'Nova Mesa'` |
| `Slug` | SlugField(unique, db_index, blank) | `secrets.token_urlsafe(16)` no `save()` |
| `ActiveMap` | FK('Map', null, blank, SET_NULL, related_name='+') | a cena no ar |
| `UpdatedAt` | auto_now | sinal de versão p/ polling |
| `CreatedAt` | auto_now_add | |

`Meta.ordering = ('-UpdatedAt', 'CreatedAt')`. O link compartilhado é `/mesa/<slug>/`.

### `Map` — uma cena dentro da mesa
| Campo | Tipo | Notas |
|---|---|---|
| `Table` | FK(GameTable, CASCADE) | |
| `Name` | Char(120) | |
| `Order` | PositiveSmallInt | default 0 |
| `GridMode` | Char choices `hex`/`free` | hexagonal vs livre |
| `Background` | FK('sprites.SpriteAsset', null, blank, SET_NULL, related_name='tabletop_backgrounds') | imagem de fundo |
| `WidthPx`, `HeightPx` | PositiveInt | tamanho natural do canvas (da imagem ou default 1600×1200) |
| `GridSize` | PositiveSmallInt | px por hexágono (snap + tamanho-base do token); default 64 |
| `ShowGrid` | Bool | default True |
| `CreatedAt`, `UpdatedAt` | | |

`Meta.ordering = ('Order', 'CreatedAt')`.

Grade hexagonal: orientação **pointy-top**, com linhas horizontais alternadas (`odd-r offset`).
`X`/`Y` continuam sendo coordenadas em px do centro visual. `GridSize` representa a largura visual
do hexágono em px e é usado tanto para desenhar a grade quanto para calcular o centro hexagonal mais
próximo durante o arrasto.

### `Token` — mini / inimigo / NPC / marcador / prop (um modelo só)
| Campo | Tipo | Notas |
|---|---|---|
| `Map` | FK(Map, CASCADE) | |
| `Kind` | Char choices `player`/`enemy`/`npc`/`object` | `object` = prop/marcador; renderiza por baixo |
| `Label` | Char(80, blank) | |
| `SpriteAsset` | FK('sprites.SpriteAsset', null, blank, SET_NULL, related_name='tabletop_tokens') | |
| `X`, `Y` | IntegerField | posição do **centro** em px do mapa |
| `GridWidth`, `GridHeight` | PositiveSmallInt | pegada em hexágonos no envelope ocupado (default do sprite); default 1 |
| `MovableByPlayers` | Bool | default por Kind: player→True, demais→False |
| `Hidden` | Bool | mestre esconde do jogador (emboscada); default False |
| `Order` | PositiveSmallInt | empilhamento |
| `CreatedAt` | | |

`Meta.ordering = ('Order', 'CreatedAt')`.

### `FogRegion` — retângulo oculto
| Campo | Tipo | Notas |
|---|---|---|
| `Map` | FK(Map, CASCADE) | |
| `X`, `Y`, `Width`, `Height` | IntegerField | px do mapa |
| `CreatedAt` | | |

## Funções puras (`tabletop/calculations.py`, `SimpleTestCase`, sem DB)

- `snap_to_grid(x, y, grid_size, grid_mode)` → encaixa no centro do hexágono mais próximo em `hex`; identidade em `free`.
- `hex_dimensions(grid_size)` → retorna largura, altura e espaçamentos da grade pointy-top.
- `nearest_hex_center(x, y, grid_size)` → calcula o centro em px do hexágono mais próximo usando coordenadas axiais/cúbicas.
- `point_in_rect(px, py, rx, ry, rw, rh)` → bool.
- `token_visible_to(token, fog_regions, is_owner)` → bool. Para não-donos, oculta `Hidden=True` e
  tokens cujo **centro** cai em qualquer `FogRegion`. A névoa é aplicada **no servidor**, não só visualmente.

## Integração com `sprites` (reuso, sem alterar o app)

- Fundos: `SpriteAsset.Category = MAP_TILE`. Tokens: `Category = MAP_TOKEN`.
- Upload in-app: view cria `SpriteAsset(Owner=request.user, Category=…, OriginalImage=arquivo)`; o
  `save()` do model já calcula checksum/filesize. Tenta ler dimensões via Pillow (opcional) p/ setar
  `Width/Height` do sprite e `WidthPx/HeightPx` do `Map`; fallback p/ defaults se Pillow ausente.
- **Segurança do upload:** `create_sprite_from_upload` aceita só raster (`png/jpg/jpeg/webp/gif`) e
  recusa SVG/HTML. Como `SpriteAsset.save()` não roda os validadores do FileField, a checagem de
  extensão é feita no serviço — senão um SVG com `<script>`, servido na mesma origem por `/media/`,
  viraria XSS armazenado. (Hardening mais amplo — tirar `svg` do `sprites.IMAGE_EXTENSIONS`, servir
  mídia com `Content-Disposition: attachment`/origem isolada — fica como recomendação fora deste escopo.)
- Picker da biblioteca: reusa `GET /sprites/search/?q=&category=` (`sprites/views.py`, `@login_required`).
- Render do token: helper `attach_sprites_to_tokens(tokens)` análogo a `attach_sprites_to_combatants`
  (`sprites/services.py`), variante `TOKEN_256` com fallback p/ original; fallback SVG por Kind como em
  `initiative/templates/initiative/partials/_combatant_sprite.html`.

## Views & URLs (`tabletop/urls.py`, `app_name='tabletop'`, prefixo `/mesa/`)

Espelham `initiative/views.py`. Helpers `_is_owner`/`_get_owned` (404 se slug não existe, 403 se quem
edita não é dono). Toda mutação faz `table.save()` (bump `UpdatedAt`) e devolve o fragmento ao vivo.

| Rota | View | Acesso |
|---|---|---|
| `''` | `home` (lista minhas mesas) | login_required |
| `'novo'` | `create_table` (POST) | login_required |
| `'<slug>/'` | `table_view` (visão ao vivo compartilhada) | público |
| `'<slug>/fragment'` | `live_fragment` (payload do polling) | público |
| `'<slug>/manage'` | `manage` (CRUD de mapas, troca de cena) | dono |
| `'<slug>/map/add'` · `/<mid>/edit` · `/<mid>/delete` · `/<mid>/activate` | maps CRUD + set_active | dono |
| `'<slug>/token/add'` · `/<tid>/edit` · `/<tid>/delete` | tokens CRUD | dono |
| `'<slug>/token/<tid>/move'` | `move_token` (X,Y) | dono **ou** player (regra trust-based) |
| `'<slug>/fog/add'` · `/<fid>/delete` | fog CRUD | dono |
| `'<slug>/sprite/upload'` | `upload_sprite` (cria SpriteAsset) | dono |

**Regra do `move_token`:** dono move qualquer token; viewer anônimo só move tokens com
`MovableByPlayers=True` **e** que estejam no `Table.ActiveMap`. Mover inimigos ou tokens de cenas
inativas → 403.

## Polling e arrasto

Diferente do `initiative` (só viewers fazem polling), aqui **dono e jogadores** fazem polling da
`live_fragment` (`hx-get … hx-trigger="every 2s"` no container do canvas), porque ambos mutam estado.
**Guarda de arrasto:** `tabletop.js` marca `data-dragging` e um listener `htmx:beforeSwap` chama
`preventDefault()` enquanto há arrasto, evitando que o poll reverta uma mini em movimento; após o drop
+ POST, o próximo poll traz o estado autoritativo.

## Visibilidade no servidor (não vazar posições)

`live_fragment`/`table_view` filtram tokens para não-donos: excluem `Hidden=True` e tokens sob névoa
(via `token_visible_to`). O HTML do jogador **não contém** inimigos sob a névoa.

## Frontend

- `static/css/tabletop.css` — convenção `.tt-` (como `.init-` em `initiative.css`).
- `static/js/tabletop.js` — vanilla, carregado só nas páginas da mesa via `{% block extra_js %}`.
  Arrasto por pointer events de `.tt-token[data-movable]`, snap à grade hexagonal, move otimista + POST,
  guarda de poll; ferramentas do mestre: clicar-para-colocar token, desenhar retângulo de névoa.
- Canvas dimensionado a `Map.WidthPx×HeightPx`; fundo `<img>`; grade hexagonal pointy-top desenhada via
  SVG/CSS background derivado de `GridSize`; névoa e tokens como divs/imgs absolutos. Escala responsiva
  por `transform: scale()`.
- Templates: `tabletop/base_tabletop.html` (extends `templates/main.html`), `table_view.html`,
  `manage.html`, partials `_live_fragment.html`, `_token.html`, `_token_sprite.html`, `_map_card.html`,
  `_fog.html`. Condicional `{% if is_owner %}` separa controles do mestre.

## Plano de testes (TDD, conforme AGENTS.md)

- **Funções puras** (`SimpleTestCase`): `snap_to_grid`, `hex_dimensions`, `nearest_hex_center`,
  `point_in_rect`, `token_visible_to`.
- **Modelos:** geração de slug, defaults (`Token.MovableByPlayers` por Kind), ordenações.
- **Permissões:** dono cria/edita; estranho/anônimo recebem 403 nas edições; view pública 200 por slug.
- **Regra de move:** anônimo move token movível na cena ativa (200, posição muda e encaixa no centro
  de um hexágono); não move inimigo (403); não move token de cena inativa (403).
- **Névoa/ocultos:** `live_fragment` de jogador exclui tokens sob névoa e `Hidden`; dono vê tudo.
- **Troca de cena:** `set_active` muda `ActiveMap`; visão ao vivo reflete a nova cena.
- **HTMX:** endpoints retornam o partial esperado; request não-HTMX cai no fallback de página inteira.
- **Upload de sprite:** cria `SpriteAsset` com categoria/owner corretos; SVG/HTML são recusados (anti-XSS).

## Sequência de build

1. [x] Spec: este `TABLETOP.md`.
2. [x] Scaffold: app `tabletop`, `INSTALLED_APPS`, include `mesa/`, link no nav, `base_tabletop.html`.
3. [x] Modelos + migração (`0001_initial`) + `calculations.py` + testes das puras/defaults.
4. [x] CRUD do mestre (mesas/mapas), upload + picker de sprite, troca de cena + testes.
5. [x] Visão ao vivo + render do canvas + polling + filtro de visibilidade + testes.
6. [x] Tokens & props (CRUD do mestre) + testes.
7. [x] Arrasto (`tabletop.js`) + endpoint `move_token` + testes.
8. [x] Névoa retangular (desenhar/remover) + testes.
9. [x] Polish + docs (`docs/architecture.md`, `AGENTS.md`) + suíte completa (22 testes do app verdes).
10. [ ] Migração da grade `square` para `hex` pointy-top em modelos, cálculos, CSS/JS e testes.

> Itens 1-9 implementados numa única passada; 22 testes do app `tabletop` verdes
> (`python manage.py test tabletop`) na implementação original. A migração hexagonal do item 10 é uma
> mudança posterior desta spec e ainda precisa ser implementada/testada. Nota de UX: para preparar uma cena com inimigos/névoa **antes**
> de revelá-la, use o **editor** da cena (`/mesa/<slug>/map/<mid>/editor`), que é privado do mestre;
> só a cena ativa aparece para os jogadores.

## Verificação

- `python manage.py makemigrations tabletop && python manage.py migrate`.
- `python manage.py test tabletop` e a suíte inteira (os testes existentes devem seguir verdes).
- Manual (`docker-compose up`): criar mesa, subir fundo de batalha e um mundi, colocar tokens
  player+enemy, abrir `/mesa/<slug>/` em janela anônima, confirmar que o mapa de batalha mostra grade
  hexagonal, arrastar o token do jogador e verificar snap no centro de um hexágono (mestre vê em ~2s),
  tentar arrastar o inimigo (bloqueado), desenhar névoa sobre o inimigo (some p/ o jogador), trocar a
  cena ativa (a visão do jogador acompanha).

## Fora de escopo (futuro)

Névoa por hexágono (pintar), grade quadrada, régua/medição de distância, templates de área (AoE),
HP/condições no token (isso fica no `initiative`), links por jogador / controle por conta logada,
sincronização via WebSocket (hoje o polling de 2s basta para uma mesa amigável).
