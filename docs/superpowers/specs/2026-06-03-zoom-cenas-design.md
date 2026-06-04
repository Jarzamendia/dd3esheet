# Controle de zoom nas cenas compartilhadas

**Data:** 2026-06-03
**Status:** aprovado (pendente revisão do spec escrito)

## Problema

A cena compartilhada (`tabletop/table_view.html`) não tem zoom. O `#tt-live.tt-stage`
faz polling HTMX a cada 2s trocando o `innerHTML` pelo `_canvas.html` (um `.tt-canvas`
de tamanho fixo em px), com rolagem nativa. O **editor** (`tabletop_editor.js`) já tem
pan/zoom completo, mas a cena que jogadores veem não.

## Decisões (do brainstorming)

1. **Interação como o editor:** botões `−/+/Ajustar`, zoom na roda do mouse (no ponto do
   cursor), arrastar o fundo para pan. Touch: botões + arrastar-com-um-dedo.
2. **Zoom individual, só no cliente:** cada espectador dá zoom/pan na própria tela; não
   sincroniza nem persiste. **Zero mudança em servidor/modelo.**
3. **Câmera compartilhada (mestre controla o que todos veem) fica fora de escopo.**
4. **Pinça de dois dedos fica fora de escopo** (o editor também não tem).

## Estratégia

Reaproveitar o padrão de `transform` do editor, mas **isolado no `tabletop.js`** e ativado
só quando existe `#tt-live` (não existe na página do editor → sem interferência).
**`tabletop_editor.js` não é tocado.**

`tabletop.js` é carregado em todas as páginas da mesa (`base_tabletop.html`); o editor soma
`tabletop_editor.js`. O editor usa `#tt-stage`; a cena usa `#tt-live`. Guardar tudo em
`#tt-live` mantém os dois sistemas separados.

## Mudanças

### 1. `tabletop/templates/tabletop/table_view.html`

- Adicionar cluster de zoom na `tt-topbar` (visível a dono e espectador), reusando
  `.tt-btn` + `data-zoom` ("out"/"in"/"fit") e um `<span>` com a % (id estável):
  `[ − ] 100% [ + ] [ Ajustar ]`.
- Só renderizar o cluster quando há cena (`{% if map %}`).
- Adicionar o modificador `tt-stage--live` ao `#tt-live`.

### 2. `static/js/tabletop.js`

Módulo de pan/zoom auto-contido, ativo só com `#tt-live` presente:

- Estado de módulo `view = { scale:1, panX:0, panY:0 }` — **persiste entre os swaps** do
  polling.
- `applyTransform(canvas)`: seta `transform: translate(panX,panY) scale(scale)` +
  `transform-origin:0 0` no `.tt-canvas`; atualiza o readout `%`.
- `screenToWorld(ev)` via rect do `#tt-live` + `panX/panY/scale` (espelha o editor).
- `zoomBy(mult, ev)`: zoom no cursor; clamp `scale` em 0.2–3.
- `fitView()`: fit + centraliza pela largura/altura do canvas (espelha `fitView` do editor).
- Handlers, todos guardados em `#tt-live`:
  - `wheel` → `zoomBy` (preventDefault, `passive:false`).
  - `click` em `[data-zoom]` → in/out/fit.
  - `pointerdown` no fundo (não-token) → `startPan` (arrastar move); em token do dono →
    arrasto existente.
  - `htmx:afterSwap` do `#tt-live` → reaplicar `applyTransform` no canvas novo (estender o
    hook que já redesenha a grade hex).
  - `htmx:beforeSwap` → suprimir swap durante o pan (estender a guarda que já existe pro
    arrasto de token, via flag `panning`).
- **Arrasto de token sob zoom:** `canvasPoint` passa a dividir o delta pela `scale`
  (`(ev.clientX - rect.left)/scale`), para o token cair na célula certa em qualquer zoom.
  Único ponto de lógica existente alterado.

### 3. `static/css/tabletop.css`

- `.tt-stage--live`: viewport recortado — `overflow:hidden`, altura definida (~78vh),
  `cursor` de pan; `.tt-stage--live.panning { cursor: grabbing; }`.
- `.tt-canvas` na cena: `transform-origin:0 0` (ou setado via JS).
- Estilizar o cluster de zoom se necessário (reusa `.tt-btn`/`.tt-zoom`).

## Casos de borda

- **Cena vazia** (sem `map`): cluster não renderiza; JS no-op se não houver `.tt-canvas`
  dimensionado.
- **Clamp de zoom:** 0.2×–3× (igual ao editor).
- **Swap durante pan:** suprimido via flag; ao soltar, polling volta e reaplica transform.
- **Página do editor / home:** sem `#tt-live` → handlers inativos.

## Testes

Mudança puramente cliente (JS/CSS/template); a view `live-fragment` e os modelos não mudam.
Pela regra de TDD do AGENTS.md (cálculos/permissões/views HTMX), não há teste de servidor
aplicável. Verificação visual com Playwright (cena com zoom in/out/fit, pan, e arrasto de
token do dono sob zoom landing na célula certa).

## Fora de escopo

- Câmera sincronizada pelo mestre / persistência de estado de câmera.
- Pinça de dois dedos.
- Zoom no editor (já existe).
- Refatorar o pan/zoom do editor para um módulo compartilhado (manter local; baixo risco).
