# Arquitetura

## Visao geral

O repositorio contem um projeto Django 4.2. O codigo Django fica dentro de `dd3esheet/`.

Apps:

- `home`: landing page e redirecionamento de usuarios autenticados.
- `character`: fichas de personagem e toda a persistencia editavel.
- `sdr`: referencia D&D 3.5 SRD, read-only.
- `initiative`: rastreador de iniciativa.
- `sprites`: Sprite Library em `/sprites/`, biblioteca central de imagens e bindings para classes, monstros, iniciativa e mapas.
- `tabletop`: mesa virtual / criador de mapas (cenas compartilhadas, miniaturas, névoa). Ver `TABLETOP.md`.

Arquivos centrais:

- `dd3esheet/manage.py`: entrada dos comandos Django.
- `dd3esheet/dd3esheet/settings.py`: settings, apps, middleware, bancos, static.
- `dd3esheet/dd3esheet/urls.py`: roteamento raiz.
- `dd3esheet/templates/main.html`: template base.
- `dd3esheet/static/css/character_sheet.css`: visual principal da ficha.

## Rotas

Roteamento raiz:

- `/admin/`: Django admin.
- `/accounts/`: auth padrao do Django.
- `/`: app `home`.
- `/character/`: app `character`.
- `/sprites/`: app `sprites`.
- `/sdr/`: app `sdr`.
- `/iniciativa/`: app `initiative`.
- `/mesa/`: app `tabletop`.

Rotas principais de `character`:

- `/character/`: lista fichas do usuario logado.
- `/character/create-character/`: cria ficha.
- `/character/character/<pk>`: exibe/edita ficha (pagina principal, dispatcher HTMX).
- `/character/character/<pk>/companions`: pagina de companheiros (animais, familiares, montarias).
- `/character/character/<pk>/daily-resources`: pagina de recursos diarios (slots/usos/recargas) e efeitos ativos.
- `/character/character/<pk>/reputation`: pagina de reputacao/notas de campanha.
- `/character/character/<pk>/spell-slot/<slot_id>/toggle/`: alterna uso de slot de magia.
- `/character/delete-character/<pk>/`: remove ficha.

Rotas principais de `sdr`:

- `/sdr/`
- `/sdr/spells/`
- `/sdr/monsters/`
- `/sdr/classes/`
- `/sdr/domains/`
- `/sdr/equipment/`
- `/sdr/feats/`
- `/sdr/items/`
- `/sdr/powers/`
- `/sdr/skills/`

Rotas principais de `sprites`:

- `/sprites/`: navegador pesquisavel dos 496 placeholders do manifesto Parchment & Ink.
- `/sprites/estilo/`: Art Direction Spec ("livro" parchment) gerada do manifesto — paleta de 14 cores, estilo da casa, regras de output, specs dos 8 tipos de asset, tabela de tamanho/footprint, manifesto completo e checklist de QA, com TOC + scroll-spy.
- `/sprites/search/`: busca JSON para pickers/autocomplete.
- `/sprites/manifest/`: manifesto JSON de imagens em lote, com URL, dimensoes, grid e ancora.
- `/sprites/<slug>/`: partial de detalhe de um asset da biblioteca.

## Rotas principais de tabletop

- `/mesa/`: lista as mesas do usuario logado.
- `/mesa/<slug>/`: visao ao vivo compartilhada (cena ativa); jogadores arrastam suas miniaturas.
- `/mesa/<slug>/fragment`: payload do polling (canvas da cena ativa).
- `/mesa/<slug>/manage`: gerenciar cenas (CRUD de mapas, definir fundo, trocar cena ativa).
- `/mesa/<slug>/map/<mid>/editor`: editor de uma cena (tokens, props, nevoa) — somente o dono.

O acesso publico e por `Slug` aleatorio (igual ao `initiative`); editar exige ser o dono.

## Bancos

O projeto usa dois SQLite databases.

### default

Arquivo:

```text
dd3esheet/db.sqlite3
```

Usado por:

- Django auth.
- `home`.
- `character`.
- `initiative`.
- `sprites`.
- `tabletop`.

O comando `python manage.py migrate` atua nele.

### sdr

Arquivo:

```text
dd3esheet/dnd35.sqlite3
```

Usado pelo app `sdr`.

Regras:

- tratar como read-only;
- models do `sdr` usam `managed = False`;
- toda query SDR deve usar `.using("sdr")`;
- nao migrar nem editar o schema manualmente.

## Templates

`settings.py` inclui `BASE_DIR / "templates"` em `TEMPLATES.DIRS`, alem dos templates por app.

Templates compartilhados:

- `dd3esheet/templates/main.html`
- `dd3esheet/templates/registration/login.html`

Templates de ficha:

- `character/templates/character/character.html`
- `character/templates/character/partials/*.html`

## Static

Arquivos estaticos locais ficam em:

```text
dd3esheet/static/
```

`STATICFILES_DIRS` aponta para `BASE_DIR / "static"`.

Itens importantes:

- `static/css/character_sheet.css`
- `static/htmx.min.js`
