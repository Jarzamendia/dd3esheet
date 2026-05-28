# Playbook para agentes

## Antes de alterar

1. Leia `docs/README.md`.
2. Leia o documento especifico da area.
3. Verifique o estado atual do codigo.
4. Rode ou adicione testes conforme o risco.

## Principios do produto

- Parecer ficha de papel.
- Nao reinventar a UX da ficha oficial sem motivo.
- Editar fonte de verdade.
- Calcular derivados no backend.
- Salvar via HTMX sem reload.
- Manter `sdr` read-only.

## Regras de edicao da ficha

Ao adicionar um bloco editavel:

1. Crie/ajuste partial em `character/templates/character/partials/`.
2. Use `hx-post`, `hx-target`, `hx-swap="outerHTML"` e target unico.
3. Trate `request.htmx.target` em `character.views.character`.
4. Salve fonte de verdade.
5. Recalcule derivados no backend.
6. Retorne o partial atualizado.
7. Adicione teste HTMX.

## Models

Para novos dados da ficha:

- prefira novo model irmao de `Character`;
- use FK para listas e OneToOne para blocos unicos;
- mantenha PascalCase nos fields do app `character`;
- nao coloque secoes inteiras como colunas novas em `Character`.

## SDR

Toda query:

```python
.using("sdr")
```

Nao rode migrations contra `sdr`.

## Seeds

Se alterar fields obrigatorios ou a estrutura da ficha:

- atualize `_bootstrap_character_siblings`;
- atualize `character/seeds.py`;
- atualize testes relacionados.

## CSS e UI

O visual principal fica em:

```text
dd3esheet/static/css/character_sheet.css
```

Para campos editaveis inline, use `.sheet-input`.

Evite transformar a ficha em dashboard. A prioridade e densidade, linhas, blocos e leitura de ficha em papel.

## Encoding e arquivos sensiveis

- `requirements.txt` esta em UTF-16 LE com BOM.
- Nao regrave `requirements.txt` como UTF-8 sem confirmar.
- Evite editar `dnd35.sqlite3`.
- `db.sqlite3` e local e ignorado pelo git.

## Checklist antes de finalizar

```bash
python manage.py check
python manage.py test character
python manage.py makemigrations --check --dry-run
```

Se nao rodar algum comando, documente o motivo na resposta final.

