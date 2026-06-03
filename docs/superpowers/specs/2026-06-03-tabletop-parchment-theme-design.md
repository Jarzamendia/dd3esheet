# Design — Mesa virtual: tema "Parchment & Ink" (fatia A)

> Data: 2026-06-03 · Status: aprovado, pronto para planejar a implementação.

## Contexto

O `design_handoff_dnd_vtt/` define um design language completo ("Parchment & Ink")
e três telas (Sprite Library, Art Direction Spec, Scene Creator). O `TABLETOP.md`
descreve a mesa virtual (`/mesa/`) já implementada (itens 1–9) com visual próprio
e grade quadrada. O handoff é grande demais para um único spec, então foi
**decomposto em 5 fatias**, cada uma com seu próprio ciclo spec → plano →
implementação.

### Sequência acordada das fatias (A → B → C → D → E)

| Fatia | Escopo | Depende de |
|---|---|---|
| **A** | Tema Parchment & Ink (tokens compartilhados + restyle imersivo do `/mesa/`) | — |
| **B** | Migração da grade quadrada → hexagonal pointy-top (item 10 do TABLETOP.md): models, `calculations.py`, CSS/JS, leituras métricas (1,5 m/célula) | A |
| **C** | Scene Creator: pan/zoom, camadas, pintura de terreno, pincel de névoa, régua, rotação, paleta drag-drop, autosave | A, B |
| **D** | Sprite Library: navegador do manifesto de 496 assets sobre o app `sprites` | A |
| **E** | Art Direction Spec: "art bible" gerada a partir do manifesto | A, D |

**Este documento cobre apenas a fatia A.** As demais viram specs próprios depois.

## Objetivo da fatia A

Portar o design language Parchment & Ink (`theme.css`) para o projeto e revestir
todas as telas do `/mesa/` de forma **imersiva** (incluindo nav e rodapé enquanto
o usuário está na mesa), sem tocar no resto do app. É um restyle **puramente
visual**: nenhuma mudança de comportamento, rotas, models ou estrutura de markup
além de classes/atributos necessários para o estilo. A grade continua **quadrada**
nesta fatia (hexágono é a fatia B).

## Decisões (confirmadas com o usuário)

1. **Alcance:** `/mesa/` imersivo — o tema reveste também nav e rodapé via uma
   classe no `body`, dando um quadro parchment completo e sem costura, distinto do
   restante do app. Fichas/SDR/iniciativa ficam inalterados.
2. **Tokens compartilhados:** vivem num CSS dedicado reusável por A/D/E, **escopados
   sob `.tt-themed`** (não em `:root` nu) para não colidir com as variáveis do
   `character_sheet.css`.
3. **Fontes:** Cinzel + EB Garamond já carregam globalmente no `main.html`; Spectral
   + JetBrains Mono entram via `<link>` escopado no `extra_head` do
   `base_tabletop.html` (CDN Google Fonts, igual ao padrão atual do projeto).

## Arquitetura de CSS

Três camadas com fronteiras claras:

- **`static/css/parchment-theme.css`** *(novo, compartilhado)* — porta de
  `theme.css`: todos os design tokens (cores ink/paper, família da paleta, rampa de
  superfícies, texto, tipografia, escala de espaçamento, raios, sombras, grain) +
  as primitivas reutilizáveis (`.paper-field`, `.btn`, `.eyebrow`, `.rule`, `.mono`,
  `.swatch`, scrollbars no tom parchment). Os tokens são declarados sob a classe
  **`.tt-themed`** em vez de `:root`. As fatias D e E carregam este mesmo arquivo.
- **`static/css/tabletop.css`** *(reformulado)* — consome os tokens parchment;
  substitui a paleta `--tt-*` viva pelos acentos derivados da paleta; reveste
  topbar, botões, cards, formulários e o chrome do canvas.
- **Fontes:** um `<link>` extra escopado para Spectral + JetBrains Mono no
  `extra_head` do `base_tabletop.html`.

### Tokens portados (cópia exata do handoff)

Valores exatos de `design_handoff_dnd_vtt/theme.css` — copiar sem alterar:

- **Ink/paper:** `--ink #2b2622` · `--ink-soft #493628` · `--parchment #efe6d2` ·
  `--bone #d6c6aa`.
- **Família da paleta:** `--ochre #c8923a` · `--leather #7a4f2a` · `--forest #4f6b3a`
  · `--iron #6b6f73` · `--deep-red #8a2f28` · `--steel-blue #3f6079` ·
  `--muted-gold #b58a36` · `--arcane-teal #2f6f6a` · `--royal-blue #314f7c` ·
  `--dull-violet #5d4978`.
- **Superfícies:** `--paper-0 #f4ecd9` · `--paper-1 #efe6d2` · `--paper-2 #e6d9bd` ·
  `--paper-3 #ddcca9` · `--edge-line #cdbb96` · `--edge-strong #b29b6f`.
- **Texto:** `--text #2b2622` · `--text-soft #5a4a37` · `--text-faint #8a7857` ·
  `--line #2b2622`.
- **Tipografia:** `--font-display 'Cinzel'` · `--font-body 'EB Garamond'` ·
  `--font-alt 'Spectral'` · `--font-mono 'JetBrains Mono'`.
- **Espaçamento:** `--sp-1 4px` … `--sp-8 64px`. **Raio:** `--radius 3px` ·
  `--radius-lg 5px`. **Sombras:** `--shadow-1/-2/-inset`. **Grain:** data-URI SVG
  fractalNoise como em `theme.css`.

## O quadro imersivo

- `main.html` ganha um `{% block body_class %}sheet-body{% endblock %}` no `<body>`.
- `base_tabletop.html` sobrescreve para `sheet-body tt-themed paper-field`.
- Essa classe (a) ativa os tokens parchment escopados e (b) permite que
  `parchment-theme.css` re-estilize a **nav e o rodapé compartilhados apenas
  enquanto em páginas da mesa** (seletores `.tt-themed .app-nav`, `.tt-themed
  .app-footer`), sem afetar as outras telas.

## Mapeamento Kind → acento da paleta

Substitui os tokens `--tt-*` vivos. Alimenta os fallbacks de sprite
(`_token_sprite.html`) e os estados de cena ativa/seleção.

| Kind do token | Atual | Acento parchment |
|---|---|---|
| player | `#1f5fb0` | `--steel-blue #3f6079` |
| enemy | `#a32020` | `--deep-red #8a2f28` |
| npc | `#5a5a5a` | `--iron #6b6f73` |
| object | `#6a7d2e` | `--leather #7a4f2a` |
| active/seleção | `#d9a441` | `--ochre #c8923a` |

## Escopo do restyle

As cinco superfícies da mesa recebem o tratamento parchment, preservando a
estrutura de markup:

- `home` (lista de mesas), `manage` (CRUD de mapas), `editor` (preparo privado da
  cena), `table_view` (visão ao vivo compartilhada) e as partials (`_token`,
  `_fog`, `_map_card`, `_canvas`, `_token_sprite`).
- Botões `.tt-btn` adotam o estilo inked `.btn`; painéis usam a rampa de papel
  (`--paper-0/1/2`); réguas hairline `--edge-line`; canvas sobre o parchment field.

## Testes

Mudança é só CSS/template. Pelo AGENTS.md, TDD cobre cálculos/permissões/roteamento
HTMX — nada disso muda aqui. Guarda mínima:

- Teste afirmando que páginas da mesa renderizam a classe `tt-themed` no body e
  linkam `parchment-theme.css` (impede o tema sumir em silêncio).
- Os 22 testes existentes do app `tabletop` seguem verdes.

## Fora de escopo (desta fatia)

Grade hexagonal e leituras métricas (fatia B); pan/zoom, camadas, terreno, régua,
rotação, autosave (fatia C); telas Sprite Library e Art Spec (D/E); re-tema global
do app; ingestão do manifesto de 496 assets.
