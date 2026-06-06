# App: sdr

O app `sdr` e a referencia de regras de D&D 3.5. Ele disponibiliza consultas,
filtros e paginas de detalhe para magias, monstros, classes, dominios,
equipamentos, talentos, itens magicos, poderes psionicos e pericias.

## Para que serve

- Expoe uma interface navegavel para dados do SRD/SDR.
- Filtra registros por campos relevantes usando `django-filter`.
- Renderiza paginas de detalhe com linhas resumidas, blocos de texto e fallback
  para `full_text` quando nao ha conteudo estruturado.
- Serve como fonte de dados para outros apps, especialmente `character`
  (magias, classes e invocacoes) e `tabletop`/`sprites` (links para monstros).

## Arquivos principais

- `models.py`: mapeia tabelas do banco SDR, como `spell`, `monster`, `class`,
  `equipment`, `feat`, `item`, `power` e `skill`.
- `views.py`: monta home, listas filtradas e paginas de detalhe.
- `filters.py`: define os `FilterSet` usados nas listas.
- `lookups.py`: contem utilitarios de resolucao, como `resolve_spell`.
- `management/commands/`: comandos de importacao, traducao e auditoria de dados.
- `data/`: dados auxiliares usados por importacoes/auditorias.

## Rotas

- `GET /sdr/`: home da referencia.
- `GET /sdr/spells/` e `GET /sdr/spell/<pk>/`: lista e detalhe de magias.
- `GET /sdr/monsters/` e `GET /sdr/monster/<pk>/`: lista e detalhe de monstros.
- `GET /sdr/classes/` e `GET /sdr/class/<pk>/`: lista e detalhe de classes.
- `GET /sdr/domains/` e `GET /sdr/domain/<pk>/`: lista e detalhe de dominios.
- `GET /sdr/equipment/` e `GET /sdr/equipment/<pk>/`: equipamentos.
- `GET /sdr/feats/`, `/items/`, `/powers/` e `/skills/`: demais categorias.

## Dependencias e cuidados

- Os modelos usam `managed = False`; o Django nao deve criar nem alterar essas
  tabelas via migrations normais.
- As queries usam `.using("sdr")`, apontando para `dnd35.sqlite3` em `settings.py`.
- Ao adicionar campos ou modelos, confirme primeiro a estrutura real do banco SDR.
- `resolve_spell` faz correspondencia por `name` e depois por `altname`; mudar
  essa regra afeta o spellbook em `character`.
