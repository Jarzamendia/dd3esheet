# Design — Mesa virtual: Editor de Cena (substituição fiel ao handoff)

> Data: 2026-06-04 · Status: aprovado, pronto para planejar a implementação.

## Contexto

O pacote `design_handoff_editor_de_cena/` é uma referência de design hi-fi (protótipo
React/Babel) de um **Editor de Cena** para mestre de RPG: um editor de mapas
hexagonais com dois modos — **Editor** (mestre prepara a cena) e **Cena ao vivo /
LiveStage** (vista imersiva read-only para jogadores, com régua, cone, ping e
marcadores). Grid de hexágonos pointy-top, coordenadas axiais `(q, r)`, escala
1 hex = 1,5 m. UI em pt-BR.

O app `tabletop` (`/mesa/`) **já existe** com Django + HTMX + JS vanilla,
renderização server-side e modelos `GameTable`, `Map`, `Token`, `FogRegion`,
`TerrainCell`. A matemática de hex já vive em `calculations.py` (pointy-top axial,
compatível com o `hex.js` do handoff). Há um editor parcial (toolstrip, canvas
overlay, camadas, inspector) e uma visão ao vivo com polling de 2s.

Este handoff **substitui** o editor atual por uma versão de fidelidade muito maior.
Decisão de produto: substituição fiel, evoluindo os modelos.

## Decisões confirmadas com o usuário

1. **Escopo:** substituir o editor de cena (e a visão ao vivo) para bater fielmente
   com o handoff, evoluindo os modelos do `tabletop`.
2. **Persistência:** **cliente + autosave**. O editor mantém o estado da cena em JS,
   renderiza no canvas, undo/redo em memória, e salva em lote via endpoint JSON com
   debounce. A visão ao vivo lê do banco por polling.
3. **Multiplayer preservado (tudo):** visão ao vivo pública + polling; tokens
   movíveis por jogadores (`MovableByPlayers`); tokens ocultos (`Hidden`); múltiplas
   cenas por mesa + `ActiveMap`.
4. **Token model:** adicionar `Faction`/`HP`/`MaxHP`/`Size`/`Conditions`; **manter
   `Kind` apenas para marcar `object` (prop sem HP/condições)**. Migração deriva
   `Faction` do `Kind` atual.
5. **Tema:** implementar **todo o layout/interações do handoff**, porém **remapeando
   as cores para a paleta Parchment & Ink (clara)** já existente — não o ember/gold
   escuro. Mantém a identidade visual atual da Mesa.
6. **Execução:** plano completo (writing-plans) cobrindo todas as fases; execução
   fase a fase com checkpoints de revisão.

## Arquitetura geral

### Editor — cliente-autoritativo

A view Django do editor renderiza um **shell**: o HTML do chrome (topbar, header,
rails, status) + a cena serializada num `<script type="application/json">`
(terreno, névoa, tokens, grade, nome da cena) + a biblioteca de sprites (tokens e
texturas de terreno, com URLs). Um módulo `tabletop_editor.js` **reescrito** detém
todo o estado da cena em JS:

- **Canvas 2D** desenha terreno (cor sólida / textura via `createPattern`), grade
  hex, névoa, prévia de pincel, régua/cone — com câmera `{x,y,zoom}`,
  `devicePixelRatio` e `ctx.setTransform(dpr*zoom,0,0,dpr*zoom,dpr*cam.x,dpr*cam.y)`,
  conforme o handoff.
- **Overlay DOM** renderiza tokens (disco + anel da facção + barra de vida + ícones
  de condição + nome) posicionados em coordenadas de tela; trata hover, seleção,
  arraste com snap, quickbar e menu de contexto.
- **Undo/redo em memória**: pilha de ≤80 snapshots `{terrain, fog, tokens}`.

Conversão mundo→tela: `telaX = mundoX * zoom + cam.x`. Limites de zoom editor
0.18–3.

### Hex math — cliente espelha o servidor

`calculations.py` já cobre `nearest_hex_center`, `axial_to_pixel`, `_cube_round`.
Criar `static/js/hex.js` espelhando 1:1 essas funções **mais** os auxiliares do
handoff ainda ausentes: `disk(center, radius)` (pincel: 0→1hex, 1→7, 2→19, 3→37),
`line(a, b)` (interpola traço p/ não deixar buracos), `pixelToAxial` (com cube
round). Portar `disk`/`line`/distância também para Python (`calculations.py`) para
o flood-fill/validação no servidor e para testes paralelos.

### Cena ao vivo — mesmo renderer, read-only

`table_view` (`/mesa/<slug>/`) é reconstruída como o `LiveStage`: o **mesmo renderer
de canvas** em modo read-only — névoa **opaca** (jogadores não veem através),
**vinheta** atmosférica, tokens dentro da névoa **ocultados** (não renderizados).
Semeada por JSON do servidor e atualizada pelo polling de 2s já existente (o
fragmento de polling passa a devolver **JSON da cena** → re-render no cliente).
Arraste de token por jogador continua via endpoint `move_token` por ação
(preserva multiplayer). Utilidades (régua/cone/ping/marcador, tela cheia) são
client-only e efêmeras (não persistem).

## Mudanças de modelo + migração

### Token

Campos novos:

| Campo | Tipo | Notas |
|---|---|---|
| `Faction` | CharField | `party` / `ally` / `neutral` / `enemy`, default `enemy` |
| `HP` | IntegerField | default 0 |
| `MaxHP` | IntegerField | default 0 |
| `Size` | CharField | `sm` / `md` / `lg` / `xl`, default `md` (escalas 0.74/1/1.6/2.3) |
| `Conditions` | JSONField | lista de ids (ex.: `['blessed']`), default `list` |

`Kind` **permanece**, mas seu único papel passa a ser distinguir `object` (prop sem
HP/condições/facção na UI). Migração de dados: deriva `Faction` do `Kind`
(`player→party`, `enemy→enemy`, `npc→neutral`, `object→neutral`). `MovableByPlayers`,
`Hidden`, `Rotation`, `GridWidth/GridHeight` (pegada de prop) seguem inalterados.
`default_movable_for_kind` continua: criaturas `party` nascem movíveis quando
`Kind=player`.

### Terreno (paleta fixa)

Novo módulo `tabletop/terrains.py` com a paleta fixa de 9 terrenos (id, label, tipo):
6 cor sólida — `stone #d8d4ca`, `grass #54692f`, `dirt #6a4d31`, `water #2b5266`,
`sand #bda468`, `rock #363139` — e 3 textura — `dungeon`, `cobble`, `woods` —
referenciando sprites `MAP_TILE` semeados por slug conhecido. Espelhar a paleta em
JS para o canvas.

`TerrainCell` ganha `Terrain = CharField` (chave da paleta); o FK `SpriteAsset`
**permanece nullable** para texturas customizadas (fallback: se houver `SpriteAsset`,
o cliente usa a URL como pattern; senão usa cor/textura da paleta pela chave).
Migração: cells existentes recebem uma chave default (`stone`) ou, se tiverem
`SpriteAsset` de tile conhecido, a chave correspondente.

> Nota: as **cores de terreno** são semânticas (grama=verde, água=azul) e **não**
> são remapeadas para a paleta de chrome Parchment — representam o terreno real.

### Névoa (por-hex)

Novo modelo `FogCell(Map, Q, R)` espelhando `TerrainCell` (unique por Map+Q+R).
`token_visible_to` passa a ocultar um token cujo hex esteja em `FogCell` (além de
`Hidden`). O `FogRegion` retangular é **aposentado** do fluxo (deixado de usar; sua
remoção/migração é tratada na fase de modelo). Persistência de névoa entra no
autosave em lote, como o terreno.

## Persistência (autosave)

Endpoint transacional **`POST /mesa/<slug>/map/<mid>/scene/save`** que aceita JSON
da cena e, numa transação:

- substitui as `TerrainCell` do mapa pelo conjunto enviado (`q,r,terrain`);
- substitui as `FogCell` do mapa pelo conjunto enviado (`q,r`);
- faz upsert/delete dos `Token` (posição, facção, hp/maxhp, size, conditions,
  label, rotation, hidden, movable, sprite, kind);
- atualiza `Map` (grade `cols/rows` via `GridSize`/dimensões, `Name`, `ShowGrid`);
- bompe `table.UpdatedAt` (sinal de versão p/ polling).

Cliente faz autosave **debounced (~800ms)** após edições; mostra estado
"salvando…/salvo". Só o dono pode salvar (`_get_owned`). Tamanho de payload
limitado (validar nº de cells/tokens). **Mover token por jogador** mantém o
endpoint `move_token` por ação (não passa pelo autosave do editor).

> Concorrência: o editor é de uso do mestre (um autor). Autosave é
> "last-write-wins" para a cena inteira do mapa; não há merge multi-editor.

## Tema — remapeamento Parchment

Reutiliza `parchment-theme.css` (tokens escopados em `.tt-themed`). O editor adota
o **layout e as interações** do handoff, mapeando os papéis de cor do handoff para
tokens Parchment:

| Papel no handoff | Valor handoff | → Parchment |
|---|---|---|
| `--ember` (primário/brasa) | `#cf6a3c` | `--ochre #c8923a` |
| `--ember-bright` | `#e8845a` | `--muted-gold #b58a36` |
| `--gold` (floreio) | `#c6a24e` | `--muted-gold #b58a36` |
| superfícies `bg-0..bg-4` (escuras) | `#0c0c0e…#322f37` | rampa `--paper-0..3` + `--bone` |
| `--line`/`--line-strong` | brancos translúcidos | `--edge-line`/`--edge-strong` |
| `--text`/`--dim`/`--faint` | claros sobre escuro | `--text`/`--text-soft`/`--text-faint` |
| facção party | `#4f86bd` | `--steel-blue #3f6079` |
| facção ally | `#5aa06b` | `--forest #4f6b3a` |
| facção neutral | `#c6a24e` | `--ochre #c8923a` |
| facção enemy | `#c23b34` | `--deep-red #8a2f28` |
| seleção/ativo | ember | `--ochre` |

Condições (6): mapear cada cor para o acento Parchment mais próximo
(envenenado→forest, atordoado→muted-gold, caído→iron, abençoado→ochre,
amedrontado→dull-violet, protegido→steel-blue). Tipografia mantém Cinzel (display) +
a fonte de corpo do tema; o handoff pede Manrope, mas usamos a stack Parchment já
carregada (sem nova fonte).

## UI — estrutura (layout do handoff, cores Parchment)

- **Topbar global (50px):** marca + nav (decorativa, item "Mesa" ativo) + usuário.
- **Editor — header de cena (56px):** migalha "EDITOR" + nome da cena + lápis
  (renomear) · à direita: undo/redo, controle de zoom `[−] 92% [+]`, "Ajustar",
  "Cenas", botão primário "Ver ao vivo".
- **Editor — corpo (3 colunas `296px 1fr 290px`):**
  - **Rail esq.:** `ToolDock` (Selecionar V, Terreno B, Token T, Névoa F, Régua R,
    Apagar E) + painel contextual por ferramenta — `TerrainPanel` (Pincel/Balde,
    paleta 9, chips de tamanho, conta-gotas Alt+clique), `TokenPanel` (busca + grid
    de assets da biblioteca, drag/clique-para-pegar), `FogPanel` (Revelar/Ocultar,
    tamanho, Revelar tudo/Cobrir tudo), `SimplePanel` (select/erase/measure).
  - **Centro (`stage-wrap`):** fundo xadrez + `<canvas>` + overlay DOM de tokens +
    barra de status (34px: ferramenta, coord sob cursor, dicas, contagens).
  - **Rail dir.:** `SceneSizePanel` (presets Pequena/Média/Grande/Enorme + steppers,
    limites cols 8–80 / rows 6–60), `LayersPanel` (Terreno/Tokens/Névoa/Grade:
    visibilidade + trava; barra ativa; "Limpar terreno"), `InspectorPanel` (ficha do
    token: avatar+nome inline, facção 4 botões, PV stepper+barra, tamanho P/M/G/GG,
    6 condições toggláveis), `TokenListPanel` (lista com facções + mini barra de
    vida + clique p/ selecionar).
- **Token no mapa (overlay):** disco com imagem/placeholder, anel da facção, barra
  de vida, ≤3 ícones de condição, nome (em hover/seleção/zoom>0.78), anel duplo
  ocre quando selecionado, **quickbar** flutuante (−1 PV / valor / +1 PV / duplicar
  / remover).
- **Menu de contexto (botão direito):** Duplicar (Ctrl+D), Facção (4 swatches),
  Remover (Del).
- **LiveStage:** header próprio (badge "● Ao vivo" pulsante, nome, zoom, Ajustar,
  Tela cheia, Gerenciar cenas, "Editar esta cena"); palco com vinheta + névoa
  opaca; dock vertical de utilidades à esquerda (Mover, Régua, Cone, Ping,
  Marcador) + paleta de 7 cores + Limpar tudo.

## Interações

- **Câmera:** pan (botão meio/direito, Espaço+arraste, ou `select` arrastando o
  fundo); zoom na roda centrado no cursor (`preventDefault`), botões ±1.2×;
  "Ajustar" (tecla `0`) reenquadra; reenquadra ao trocar tamanho da cena.
- **Pintura de terreno:** mousedown empurra undo; pinta disco de raio=brush ao longo
  do traço (`line` interpola). Balde = flood-fill 6-vizinhos limitado a 6000 hexes.
  Apagar = pinta `stone`. Alt+clique = conta-gotas.
- **Névoa:** mesma mecânica; revelar remove do set, ocultar adiciona.
- **Tokens:** colocar (drag do asset ou pegar+clicar no hex); mover (arraste, snap ao
  hex, undo no 1º movimento); selecionar (clique), nudge com setas, duplicar (Ctrl+D),
  remover (Del). Edição de ficha imediata; edições estruturais empurram undo
  (digitação contínua de nome/PV usa flag de skip).
- **Undo/Redo:** Ctrl+Z / Ctrl+Y (ou Ctrl+Shift+Z), ≤80 snapshots.
- **Atalhos:** `V/B/T/F/R/E` ferramenta; `Espaço` pan; `0` ajustar; setas mover;
  `Del` remover; `Esc` limpar seleção/medição/menu; `Ctrl+Z/Y/D`. Ignorados quando o
  foco está em input/textarea.
- **Régua/cone:** arrasta de hex a hex; mostra `N hex · M m` (M = N×1.5); cone 60°
  (`CONE_HALF=π/6`) no live.
- **Ping:** anéis 14→96px em 1.4s; **marcadores:** pins coloridos toggláveis.

## Fases de implementação (sequenciais, cada uma verificável)

1. **Tema/shell:** tokens de cor (remapeamento Parchment), topbar, header de cena,
   layout 3-col, status bar — sem comportamento ainda.
2. **Modelo + migração:** `Token` (Faction/HP/MaxHP/Size/Conditions), `FogCell`,
   `TerrainCell.Terrain`, paleta `terrains.py`, seed das 3 texturas; ajustar
   `token_visible_to`; testes de modelo/migração/serialização.
3. **Canvas core:** `hex.js`, renderer de terreno+grade+câmera (pan/zoom), seed por
   JSON. É o núcleo.
4. **Overlay DOM de tokens:** render, seleção, arraste com snap, quickbar.
5. **Ferramentas de terreno + undo/redo:** pincel, balde (flood-fill), apagar,
   conta-gotas, tamanhos de pincel.
6. **Névoa por-hex:** pincel revelar/ocultar, revelar/cobrir tudo.
7. **Rails:** ToolDock, TerrainPanel, TokenPanel, FogPanel, SceneSizePanel,
   LayersPanel, InspectorPanel, TokenListPanel.
8. **Persistência/autosave:** endpoint `scene/save` + carga inicial + estado
   salvando/salvo; testes de view/permissão.
9. **LiveStage:** renderer read-only (névoa opaca, vinheta, tokens ocultos),
   integração com polling (JSON), arraste de jogador, utilidades (régua/cone/ping/
   marcador), tela cheia.
10. **Atalhos + menu de contexto.**
11. **Testes finais + limpeza:** cobertura de cálculos/permissões/roteamento HTMX;
    garantir os testes existentes verdes; remover código morto (`FogRegion`,
    editor antigo).

## Testes

Conforme AGENTS.md, TDD cobre **cálculos, permissões e roteamento HTMX**:

- `hex.js`/`calculations.py`: `distance`, `disk`, `line`, `pixelToAxial` (paridade
  Python↔JS onde aplicável).
- Modelo/serialização: derivação `Kind→Faction` na migração; `token_visible_to` com
  `FogCell`; round-trip do payload de `scene/save`.
- Views/permissão: `scene/save` exige dono; `move_token` por jogador respeita
  `MovableByPlayers` + cena ativa; polling devolve JSON correto.
- Manter verdes os testes existentes do `tabletop`.

## Fora de escopo

- Multi-editor concorrente / merge de cena (autosave é last-write-wins do mestre).
- Persistência de pings/marcadores/medições do LiveStage (efêmeros).
- Nova fonte Manrope (usa a stack Parchment).
- Pipeline de mídia novo para assets (usa o app `sprites` atual).
```

