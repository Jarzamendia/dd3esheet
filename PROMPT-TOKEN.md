# Prompt para Criar Proximos Tokens

Crie os tokens da categoria **<NOME DA CATEGORIA>** da Sprite Library.

Escopo:
- Use as secoes do manifesto em `dd3esheet/sprites/fixtures/sprite_manifest.json` vinculadas a essa categoria em `dd3esheet/sprites/manifest_data.py`.
- Processe somente os assets dessa categoria.
- Nao inclua categorias vizinhas, mesmo que parecam relacionadas.
- Se houver algum slug ambiguo, pare e pergunte antes de gerar.

Objetivo:
- Para cada slug da categoria, gerar um token PNG transparente em:
  `dd3esheet/media/sprites/original/map_token/<slug>.png`
- Salvar tambem a fonte em:
  `dd3esheet/media/sprites/original/map_token/<slug>-source.png`
- Manter o PNG final em `512x512`.
- Atualizar `dd3esheet/db.sqlite3` em `SpriteAsset`:
  `OriginalImage = sprites/original/map_token/<slug>.png`,
  `Width = 512`,
  `Height = 512`.
- Preservar `DefaultGridWidth` e `DefaultGridHeight` ja definidos no banco/manifesto.

Direcao visual:
- Siga o mesmo padrao de qualidade dos lotes ja criados: Undead, Beasts & Vermin, Giants & Monstrous e Dragons.
- Use ilustracao fantasy bestiary pintada, estilo parchment-and-ink, com boa leitura em tamanho pequeno.
- Gere corpo inteiro, centralizado, sem base, sem sombra projetada, sem token ring e sem texto.
- Use composicao three-quarter top-down ou top-down quando fizer sentido para tabletop.
- Mantenha armas, asas, caudas, tentaculos e membros dentro do canvas.
- Para criaturas grandes, use pose compacta/circle-safe quando necessario.
- Para slugs com footprint grande, deixe a criatura ocupar bem o quadro.
- Para slugs `1x1`, mantenha a silhueta compacta e legivel.

Transparencia:
- Use o fluxo built-in `image_gen` com fundo chroma-key plano.
- Use `#00ff00` por padrao.
- Use `#ff00ff` quando o sujeito tiver verde, folhagem, veneno, reptil, planta, lodo ou qualquer parte que possa confundir com o chroma verde.
- O fundo da fonte deve ser uma cor solida uniforme, sem gradiente, sombra, textura, plano de chao ou reflexo.
- Depois remova o chroma localmente e gere PNG final com alpha.

Validacao obrigatoria:
- Confirmar programaticamente, para cada slug:
  - arquivo `<slug>.png` existe;
  - arquivo `<slug>-source.png` existe;
  - dimensao final `512x512`;
  - alpha final tem faixa `0-255`;
  - `SpriteAsset.OriginalImage`, `Width` e `Height` foram atualizados;
  - `DefaultGridWidth` e `DefaultGridHeight` permanecem corretos.
- Montar e abrir uma folha de contato em xadrez para revisar halo de chroma, enquadramento e qualidade visual.
- Se algum token ficar ruim, pequeno demais, cortado, com pose errada ou com halo aparente, refazer esse slug antes de finalizar.

Nao mexer:
- Nao alterar CSS, JS, templates ou renderizacao do tabletop.
- Nao alterar manifesto, seeds ou views a menos que seja estritamente necessario e explicitamente solicitado.
- Nao reverter mudancas existentes no worktree.

Resposta final esperada:
- Informar quantos tokens foram criados.
- Listar os slugs gerados.
- Confirmar paths salvos, DB atualizado e validacao.
- Avisar se algum teste Django nao foi rodado e por que.
