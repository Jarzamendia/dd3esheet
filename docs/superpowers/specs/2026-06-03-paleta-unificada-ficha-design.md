# Paleta unificada: todo o app na paleta da ficha

**Data:** 2026-06-03
**Status:** aprovado (pendente revisão do spec escrito)

## Problema

O app tem duas paletas convivendo:

- **Ficha + SDR** — tokens `:root` em `character_sheet.css` (carregado globalmente em
  `main.html`): papel branco `#fff`, tinta preta `#1a1a1a`, rubrica vermelha `#b51818`,
  headers pretos, fontes Cinzel/EB Garamond. O SDR já consome esses tokens.
- **Mesa + Sprite Library + Art Direction Spec** — paleta quente "Parchment & Ink"
  (`parchment-theme.css`, escopada sob `.tt-themed`, aplicada no `<body>`): creme/ocre/couro.

O objetivo é que **todo o app pareça com a ficha** (consistência visual).

## Decisões (do brainstorming)

1. **Art Direction Spec fica intocada.** `/sprites/estilo/` é um guia de estilo gerado de
   `manifest_data.py` que exibe os swatches da paleta Parchment & Ink dos sprites.
   Recolori-la a tornaria autocontraditória. Recolorimos só **Mesa + Sprite Library**.
2. **Cores da ficha (branco/preto/vermelho), textura preservada.** Adotamos os valores de cor
   da ficha, mas mantemos a leve textura de papel (`--grain`) para não ficar chapado.
3. **Cores funcionais de tipo de token preservadas.** player=azul, enemy=vermelho, npc=cinza,
   object, active=âmbar são marcadores semânticos no mapa, compartilhados com a Iniciativa.
   Recolorimos só o *chrome* (fundos, bordas, texto, headers, botões, links).
4. **Iniciativa incluída no polish:** trocar hardcodes soltos pelos tokens da ficha.

## Estratégia: remapear tokens, não reescrever CSS

`tabletop.css` e `sprite_library.css` consomem variáveis definidas sob `.tt-themed`
(`--ink`, `--paper-0/1/2/3`, `--leather`, `--deep-red`, `--edge-line`, `--edge-strong`,
`--text*`, etc.). Em vez de editar esses arquivos extensos, redefinimos os mesmos tokens
com os valores da ficha numa **nova classe modificadora `.tt-ficha`** aplicada no `<body>`
da Mesa e da Sprite Library. A Art Spec mantém só `.tt-themed`.

## Mudanças

### 1. `dd3esheet/static/css/parchment-theme.css`

Adicionar bloco de override após `.tt-themed`:

```css
.tt-themed.tt-ficha {
  --ink:#1a1a1a; --ink-soft:#585858;
  --parchment:#ffffff;                 /* texto sobre superfície escura → branco */
  --bone:#ececea;
  --paper-0:#ffffff; --paper-1:#fafafa; --paper-2:#f3f3f1; --paper-3:#ececea;
  --edge-line:rgba(0,0,0,.18); --edge-strong:rgba(0,0,0,.40);
  --text:#1a1a1a; --text-soft:#585858; --text-faint:#8a8a8a; --line:#000000;
  --leather:#1a1a1a;                   /* links → tinta */
  --deep-red:#b51818;                  /* link hover / acentos → rubrica da ficha */
}
```

- Suavizar `.tt-themed.tt-ficha.paper-field` para fundo near-white, **mantendo `--grain`**.
- Trocar o seletor do re-skin da nav: `.tt-themed .app-nav` → `.tt-themed:not(.tt-ficha) .app-nav`
  (e as regras filhas correlatas), para que a nav na Mesa/Sprites volte a ser a nav padrão
  do app e o re-skin couro só sobre na Art Spec.

### 2. Templates (body_class)

- `dd3esheet/tabletop/templates/tabletop/base_tabletop.html` → adicionar `tt-ficha`.
- `dd3esheet/sprites/templates/sprites/library.html` → adicionar `tt-ficha`.
- `dd3esheet/sprites/templates/sprites/art_spec.html` → **sem mudança**.

### 3. Auditoria de hardcodes

Varrer `tabletop.css` e `sprite_library.css` por hex/rgba quentes que não passem por
variável; neutralizar os poucos que existirem (tokenizar ou ajustar para tom neutro).
rgba de tinta translúcida (ex.: `rgba(43,38,34,.05)`) pode virar `rgba(0,0,0,.05)`.

### 4. `dd3esheet/static/css/initiative.css`

Trocar hardcodes soltos (`#555` subtítulo, `#bbb` bordas, eventuais `#fff`) pelos tokens
da ficha (`--ink-soft`, `--rule-line`/hair, `--paper-bg`). Manter `--init-*` (cores
semânticas de tipo).

## Testes

Mudança puramente CSS/template — sem lógica, view ou cálculo. A regra de TDD do AGENTS.md
mira cálculos/permissões/views HTMX, nenhum dos quais é tocado. Sem teste unitário aplicável.
Verificação: subir Mesa, Sprite Library, Art Spec (deve continuar Parchment & Ink),
Iniciativa, Ficha e SDR, conferindo consistência visual.

## Fora de escopo

- Reorganizar layout/estrutura das telas (só cor).
- Mudar a paleta dos sprites no manifesto / Art Direction Spec.
- Refatorações não relacionadas em tabletop.css / sprite_library.css.
