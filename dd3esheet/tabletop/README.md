# App: tabletop

O app `tabletop` implementa a mesa virtual: mesas compartilhaveis, cenas/mapas,
tokens, terreno em hex, nevoa de guerra e autosave de cena. Ele usa a biblioteca
de sprites como fonte de tiles, fundos e miniaturas.

## Para que serve

- Cria mesas (`GameTable`) pertencentes a um mestre e acessiveis por slug publico.
- Organiza cenas em `Map`, com mapa ativo para a visao ao vivo.
- Gerencia tokens em `Token`, com posicao, faccao, HP, tamanho, condicoes,
  rotacao, visibilidade e permissao de movimento por jogadores.
- Mantem terreno pintado em `TerrainCell` e nevoa em `FogCell`/`FogRegion`.
- Serializa a cena inteira para JSON e aplica autosave transacional.
- Permite uploads de imagens raster e cria `SpriteAsset` privado para o dono.

## Arquivos principais

- `models.py`: define mesas, mapas, tokens, terreno e nevoa.
- `views.py`: contem home, gerenciamento de mapas, editor, visao ao vivo,
  uploads, tokens, terreno, nevoa e endpoint de autosave.
- `serializers.py`: contrato JSON da cena, serializacao e aplicacao do payload.
- `calculations.py`: calculos puros de grade hexagonal, conversao axial/pixel,
  distancia, linha, disco e snap.
- `services.py`: resolve sprites de tokens e cria sprites a partir de upload.
- `urls.py`: rotas de mesa, editor, cena, tokens, mapas, terreno e nevoa.

## Rotas

- `GET /mesa/`: lista mesas do usuario autenticado.
- `POST /mesa/novo`: cria uma mesa.
- `GET /mesa/<slug>/`: visao ao vivo publica da mesa ativa.
- `GET /mesa/<slug>/fragment`: JSON da cena ativa para polling.
- `GET /mesa/<slug>/manage`: gerenciamento da mesa pelo dono.
- `GET /mesa/<slug>/map/<mid>/editor`: editor da cena.
- `POST /mesa/<slug>/map/<mid>/scene/save`: autosave JSON da cena inteira.
- `POST /mesa/<slug>/map/...`: cria, edita, ativa, remove mapas, pinta terreno
  e altera nevoa.
- `POST /mesa/<slug>/token/...`: cria, edita, move e remove tokens.

## Dependencias e cuidados

- O link da mesa e publico, mas edicao de mapas e tokens do mestre usa `_get_owned`.
- Jogadores anonimos so podem mover tokens `MovableByPlayers` na cena ativa.
- O contrato em `serializers.py` e usado tanto pelo editor quanto pela visao ao
  vivo; alteracoes precisam ser coordenadas com o JavaScript/templates.
- Uploads aceitam apenas formatos raster (`png`, `jpg`, `jpeg`, `webp`, `gif`)
  para evitar SVG/HTML servido por `/media/` com risco de XSS armazenado.
- `apply_scene_payload` usa estrategia last-write-wins e limites de seguranca:
  `MAX_CELLS` e `MAX_TOKENS`.
