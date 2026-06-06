# App: initiative

O app `initiative` implementa um rastreador de combate compartilhavel. O mestre
cria encontros, adiciona combatentes, controla turnos, dano acumulado e efeitos;
os jogadores podem acompanhar a board por um link publico com slug.

## Para que serve

- Mantem encontros em `Encounter`, pertencentes a um usuario dono.
- Mantem combatentes em `Combatant`, ordenados por iniciativa.
- Controla round e combatente ativo.
- Permite adicionar, editar, causar/remover dano e apagar combatentes.
- Resolve sprites de combatentes usando o app `sprites`.
- Renderiza uma board publica, enquanto acoes de edicao exigem ser dono.

## Arquivos principais

- `models.py`: define `Encounter` e `Combatant`.
- `views.py`: contem home do mestre, criacao de encontro, board publica,
  fragments e acoes POST de edicao.
- `urls.py`: registra as rotas de encontro, combatentes e turnos.
- `admin.py`: configuracao administrativa dos modelos.
- `tests.py`: cobertura do comportamento do app.

## Rotas

- `GET /iniciativa/`: lista encontros do usuario autenticado.
- `POST /iniciativa/novo`: cria um encontro.
- `GET /iniciativa/<slug>/`: board publica do encontro.
- `GET /iniciativa/<slug>/fragment`: partial da board para atualizacao.
- `POST /iniciativa/<slug>/combatente/add`: adiciona combatente.
- `POST /iniciativa/<slug>/combatente/<cid>/edit`: edita combatente.
- `POST /iniciativa/<slug>/combatente/<cid>/damage`: altera dano acumulado.
- `POST /iniciativa/<slug>/combatente/<cid>/delete`: remove combatente.
- `POST /iniciativa/<slug>/turn/next`: avanca turno.
- `POST /iniciativa/<slug>/turn/reset`: reinicia turno e round.

## Dependencias e cuidados

- Slugs sao gerados por `secrets.token_urlsafe(16)` e usados como link publico.
- `board` e `board_fragment` sao publicos; a edicao usa `_get_owned`, que aplica
  404 para inexistente e 403 para nao dono.
- `DamageTaken` e dano acumulado, nao pontos de vida atuais.
- `attach_sprites_to_combatants` adiciona atributos dinamicos usados pelos
  templates; ao alterar sprites, teste a board com e sem `SpriteAsset`.
