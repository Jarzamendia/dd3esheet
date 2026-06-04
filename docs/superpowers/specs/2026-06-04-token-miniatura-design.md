# Token da mesa: tratamento de "miniatura" com anel por tipo

**Data:** 2026-06-04
**Status:** aprovado (pendente revisão do spec escrito)

## Problema

Agora que tokens podem ter imagem (`SpriteVariant.TOKEN_256`, via
`tabletop/services.py::attach_sprites_to_tokens`), o token não se adapta bem a ela.
Hoje o `.tt-token` é um disco com **fundo colorido por tipo** + anel **branco** de 2px;
a `<img>` com `object-fit:cover` **preenche 100% do disco e esconde a cor do tipo** →
não dá pra distinguir aliado/inimigo com foto, e a imagem fica "chapada" (adesivo), sem
volume de miniatura.

## Decisões (do brainstorming)

1. **Anel da cor do tipo** visível ao redor da imagem (jogador=azul, inimigo=vermelho,
   npc=cinza, objeto=marrom).
2. **Visual de miniatura** (moldura/base com sombra + leve vinheta/volume).
3. **Encaixe `cover`** centralizado (preenche o disco; padrão de VTT).
4. Não priorizado agora: retrabalho de seleção/rótulo (só preservar o que existe).

## Estratégia

Mudança **só de CSS** em `dd3esheet/static/css/tabletop.css`. A classe de tipo
(`tt-token--player/enemy/npc/object`) já está no `.tt-token` (ver
`tabletop/partials/_token.html`), então não há mudança de template/JS/servidor.
`SpriteWidth/Height` já existem se forem necessários, mas não são para este tratamento.

## Mudanças (`dd3esheet/static/css/tabletop.css`, bloco `--- tokens ---`)

- **Variável de cor por tipo:** cada `.tt-token--*` define `--tok` (= `--tt-player`,
  `--tt-enemy`, `--tt-npc`, `--tt-object`). `.tt-token` usa `background: var(--tok)` como
  hoje (aparece quando não há imagem).
- **Anel + base via `box-shadow` em camadas** no `.tt-token` (não consome a área da
  imagem): anel `--tok` (~3px) + fio escuro fino (contraste sobre o mapa) + sombra
  projetada (base da mini). Substitui o `box-shadow` branco atual.
- **Volume de miniatura:** `.tt-token::after` (`position:absolute; inset:0;
  border-radius:inherit; pointer-events:none`) com vinheta inferior (`inset` shadow) +
  brilho superior sutil (radial-gradient claro). Fica **por cima da imagem** e também dá
  profundidade ao disco com glifo (sem imagem). Opacidades baixas (discreto).
- **Encaixe:** `.tt-token__img` mantém `object-fit:cover` (sem mudança).
- **Objeto:** mantém `border-radius:12%`; anel e `::after` herdam a forma (`inherit`).
- **Estados preservados:** `.is-dragging` (anel ocre), `.is-selected` (outline ocre),
  `.is-hidden` (opacidade + tracejado) e `.tt-token__label` continuam por cima.

## Casos de borda

- **Sem imagem:** disco colorido + glifo + o mesmo anel/volume → consistente.
- **Rotação (facing):** o `::after` gira junto (filho do token); brilho girando é
  aceitável (não vale contra-rotacionar — YAGNI).
- **Editor:** os tokens do editor usam o mesmo `.tt-token`/partial, então herdam o
  tratamento (desejável, consistência). `tabletop_editor.js` não é tocado.

## Testes

CSS puro de apresentação — sem view/modelo/cálculo alterado; nenhuma regra de TDD do
AGENTS.md (cálculos/permissões/views HTMX) se aplica. Verificação visual com Playwright:
injetar uma imagem de teste em um token e conferir encaixe `cover`, anel da cor do tipo,
sombra de base e vinheta; conferir também um token sem imagem (glifo) e um objeto.

## Fora de escopo

- Mudar de variante de sprite / pipeline de imagens.
- Retrabalho de rótulo/seleção/HUD do token.
- Mudanças no editor além da herança do estilo do `.tt-token`.
