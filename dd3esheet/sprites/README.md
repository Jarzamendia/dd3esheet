# App: sprites

O app `sprites` centraliza os assets visuais usados pelo projeto: tokens,
retratos, icones de classe, tiles de mapa, marcadores e variantes de imagem.
Ele e uma camada compartilhada por `character`, `initiative` e `tabletop`.

## Para que serve

- Mantem a biblioteca de imagens em `SpriteAsset`, com categoria, visibilidade,
  dono, dimensoes, checksum, ancoragem e tamanho padrao de grade.
- Gera e consulta variantes em `SpriteVariant`, como thumb, icone, token e
  retrato, usando o original como fallback quando a variante nao existe.
- Relaciona sprites a conceitos do jogo em `SpriteBinding`, como classe,
  monstro do SDR, tipo de combatente, especie de companheiro e uso no mapa.
- Expoe endpoints para biblioteca, busca, manifesto JSON e especificacao de
  estilo da arte.

## Arquivos principais

- `models.py`: define `SpriteAsset`, `SpriteVariant` e `SpriteBinding`.
- `services.py`: resolve sprites por classe/monstro, escolhe variantes,
  anexa imagens a combatentes e gera variantes quando Pillow esta disponivel.
- `views.py`: renderiza a biblioteca, detalhe de asset, especificacao de arte e
  endpoints JSON de busca/manifesto.
- `manifest_data.py`: descreve o catalogo esperado de assets, grupos, tipos,
  tamanhos e regras visuais.
- `seeds.py` e `management/commands/`: populam assets e bindings padrao.

## Rotas

- `GET /sprites/`: biblioteca de sprites do usuario autenticado.
- `GET /sprites/search/`: busca JSON filtrada por nome, slug, alt text e categoria.
- `GET /sprites/manifest/`: manifesto JSON para um conjunto de ids.
- `GET /sprites/estilo/`: especificacao visual do catalogo.
- `GET /sprites/<slug>/`: detalhe parcial de um asset.

## Dependencias e cuidados

- Arquivos enviados ficam em `MEDIA_ROOT`, normalmente em `sprites/original/`
  e `sprites/variants/`.
- `SpriteAsset.visible_to(user)` aplica permissao: assets publicos ou do dono.
- `generate_variant` depende de Pillow, mas o app continua funcional sem ele.
- `SpriteAsset.save()` calcula checksum quando ha arquivo original.
- Bindings sao usados em outros apps; mudar chaves, categorias ou propositos
  pode quebrar tokens de iniciativa, mesa e sugestoes da ficha.
