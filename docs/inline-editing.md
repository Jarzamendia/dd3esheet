# Edicao inline HTMX

## Objetivo

A ficha deve ser editavel direto na pagina, sem reload completo.

Cada bloco da ficha e um partial com autosave via HTMX. A view salva os campos recebidos e devolve apenas o partial afetado.

## Fluxo padrao

1. O template renderiza um `<form>` ou container com `hx-post`.
2. `hx-target` aponta para o proprio bloco.
3. `hx-swap="outerHTML"` substitui o bloco inteiro.
4. `hx-trigger="change delay:300ms"` salva apos edicao.
5. `character.views.character` identifica `request.htmx.target`.
6. A view salva, recalcula derivados se necessario e retorna o partial.

Exemplo:

```html
<form id="characterStatsForm"
      hx-post="{% url 'character:character' character.pk %}"
      hx-target="#characterStatsForm"
      hx-swap="outerHTML"
      hx-trigger="change delay:300ms">
```

## Dispatcher da view

A view `character.views.character(request, pk)` centraliza os POSTs HTMX.

Targets tratados:

- `characterIdentityForm`
- `characterForm`
- `characterStatsForm`
- `characterStatusForm`
- `characterArmorForm`
- `characterSavesForm`
- `characterAttackForm`
- `characterSkillsForm`
- `characterWeaponsForm`
- `characterProgressForm` (XP, nivel, campanha)
- `characterEquipmentForm`
- `characterItemsForm`
- `characterMoneyForm`
- `characterFeatsForm`
- `characterSpecialsForm`
- `characterSpellsForm`

Paginas extras da ficha (rotas proprias, fora do dispatcher principal):

- `companions` — companheiros, animais, familiares e montarias.
- `daily-resources` — recursos diarios com maximo/usado/recarga e efeitos ativos.
- `reputation` — reputacao e notas de campanha.

## Helpers da view

`_update_fields_from_post(instance, request, fields, prefix="")`

- le campos do POST;
- converte por tipo do field Django;
- salva se algo mudou.

`_ordered_slots(character, related_name, model, count)`

- busca registros existentes ordenados por `id`;
- completa com `None` ate a quantidade fixa da UI.

`_save_repeating_slots(character, request, model, prefix, fields, count)`

- salva linhas repetidas da UI;
- cria registro novo quando um slot vazio recebe qualquer valor;
- espera names no formato `prefix_<n>_Campo`.

`_sheet_context(char, **extra)`

- monta todos os forms, slots fixos e contexto de magia.

`_recalculate_stats(character)`

- recalcula derivados da ficha depois de edits relevantes.

## Inputs visuais

A classe CSS principal para campos inline e:

```css
.sheet-input
```

Ela remove bordas padrao do navegador e preserva o visual da ficha em papel.

## Blocos ja convertidos

- Identidade.
- Descricao.
- Atributos.
- Progresso (XP, nivel, campanha).
- Saves.
- BAB, resistencia a magia e agarrar.
- Armas e municao.
- PV, dano por contusao e deslocamento.
- CA e reducao de dano.
- Pericias (com slots multiplos para Conhecimento/Oficios/Profissao via `SkillSpecialization`).
- Equipamentos.
- Outros itens.
- Dinheiro e carga.
- Talentos.
- Habilidades especiais.
- Idiomas.
- Magias.

## Campos calculados nao editaveis

Nao transforme estes campos em inputs livres:

- modificadores de atributo;
- modificadores temporarios;
- total de CA;
- CA toque;
- CA surpreso;
- iniciativa;
- total dos saves;
- modificador de habilidade dos saves;
- total de agarrar;
- modificador de forca do agarrar;
- resumo calculado de magias.

## Observacao importante

O arquivo `static/htmx.min.js` existe, mas o template base atual nao inclui o script. Sem isso, os atributos `hx-*` ficam inertes no browser. Ver [Lacunas conhecidas](known-issues.md).

