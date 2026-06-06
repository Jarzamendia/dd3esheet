# TODO

> Roadmap de melhorias por área do app. Cada item descreve **o que** fazer e,
> quando ajuda, **por quê** ou **como saber que ficou pronto**. Marque os
> checkboxes conforme concluir.

---

## Referência — `/sdr`

Consulta do SRD 3.5 (magias, monstros, classes, etc.). Hoje funciona, mas a
navegação é "lista crua" e o visual não evoca um livro de RPG.

### Geral (todas as páginas de `/sdr`)
- [ ] **Paginação** em todas as listas. Hoje as páginas carregam a tabela inteira;
      adicionar paginação no servidor com o `Paginator` do Django, integrado ao
      `django-filter` já usado nas views de lista, para reduzir o peso e facilitar a
      navegação.
- [ ] **Redesenho com cara de livro de RPG.** Repensar a identidade visual das
      páginas de referência para lembrar um grimório/manual (tipografia, bordas,
      papel), em vez do layout de tabela atual.

- [ ] **Links entre SDR e SPRITES**: Precisamos garantir que os tokens dos monstros do SDR estejam devidamente linkados aos seus sprites.

### `/sdr` (página inicial)
- [ ] **Filtros na home.** Permitir buscar/filtrar a partir da própria página
      inicial, sem precisar entrar em cada categoria.
- [ ] **Imagem-tema por categoria.** Cada caixa (Magias, Monstros, Classes…) recebe
      uma arte temática para diferenciá-las visualmente.

### `/sdr/spells`
- [ ] **Filtro de escola como dropdown** (em vez do controle atual).
- [ ] **Filtrar por nível de magia e por classe.**

### `/sdr/monsters`
- [ ] **Filtros de família e tipo como dropdowns.**
- [ ] **Novos filtros:** nível de desafio (CR) e tamanho.
- [ ] **Imagem-tema por monstro.** Exibir a arte/token de cada monstro na lista e/ou
      na ficha (já temos tokens vinculados via `sprites` → `SpriteBinding`).
- [ ] **Multiplos tipos de imagem**: Além das imagens de Token, monstros também devem ter imagens tematicas (Para mostrar no /sdr)
- [ ] **Casar a arte existente com os monstros do SDR.** A arte já está completa (os
      294 tokens do manifesto têm PNG), mas o casamento `monster_token_casamento.json`
      ainda cobre só **148** monstros — Owlbear, Griffon, Hippogriff, Pegasus, Unicorn,
      Worg, Treant, Dryad, Bulette, golems etc. têm imagem mas continuam sem vínculo,
      então caem no token placeholder no `/sdr`/mesa. Estender o casamento
      (`{nome_SDR: token_slug}`) e re-rodar `seed_monster_tokens`.
- [ ] **Adicionar à mesa/iniciativa direto da ficha do monstro.** O token de monstro já
      linka para a ficha do SRD (ida); oferecer o caminho de volta: botão na ficha para
      criar um token na mesa ou um combatente na iniciativa.

### `/sdr/feats`
- [ ] **Filtro por classe permitida.**
- [ ] **Filtro por livro permitida.**

---

## Iniciativa — `/iniciativa`

- [ ] **Token como imagem.** Permitir anexar uma imagem ao combatente como token
      (hoje há fallback por tipo; falta o upload/seleção de imagem).
- [ ] **Reaproveitar tokens de monstro do SDR.** Conectar o "token como imagem"
      acima aos tokens de monstro já semeados (`SpriteBinding` / `sprite_for_monster`),
      permitindo escolher a arte do SRD em vez de exigir upload manual.
- [ ] **Marcar combatente como morto.** Em vez de remover da lista, mantê-lo visível
      porém riscado e fora da ordem de turnos (não participa, mas continua à vista).

---

## Biblioteca de sprites — `/sprites`

- [ ] **Paginação por tipo.** Separar e paginar os assets por categoria
      (token, tile, item…) para a biblioteca não crescer numa lista única.
- [ ] **Seção de "Tokens avulsos" (genéricos), separada dos tokens do SDR.** Na
      biblioteca e no seletor de tokens da mesa, agrupar à parte os tokens **não**
      vinculados a um monstro do SRD: arte sem linha no SDR (stand-ins IP-safe,
      templates como Lich/Ghost/Vampire Lord) e uploads do mestre. Hoje eles convivem
      na mesma lista dos tokens de monstro do SDR. Critério: a aba/seção "Avulsos"
      lista só assets sem `SpriteBinding` de monstro, e a "SDR" só os vinculados.

---

## Mesa — `/mesa`

Precisa de uma boa evolução de organização e navegação.

### `/mesa` (lista de mesas)
- [ ] **Tags e descrição nas mesas.** Permitir definir tags e um texto descritivo
      por mesa.
- [ ] **Menu lateral de busca/filtro** das mesas (por nome, tag…).

### Dentro de uma mesa
- [ ] **Organizar cenas e mapas numa árvore de pastas** (file tree) com pastas e
      subpastas. Exemplo da estrutura desejada:

      ```
      mesa/
        cenas/
          masmorras/
            1-masmorra-inicial
            2-masmorra-media
        mapas/
          vilarejo
          floresta
      ```

- [ ] **"Ver ao vivo" passa a ser da mesa, não da cena.** O dono escolhe qual cena
      fica visível aos jogadores num dado momento (uma cena ativa por mesa), em vez
      de cada cena ter seu próprio link ao vivo.
- [ ] **Página de controle de cena ativa.** Tela para o mestre alternar qual cena
      está no ar para os jogadores.

---

## Editor de cena

### Melhorias
- [ ] **Limitar a pintura ao tamanho da cena.** Após definir as dimensões da cena,
      não deve ser possível pintar terreno/fora dos limites dela.
- [ ] **Criar cena a partir de um mapa pronto.** A cena nasce com o tamanho exato da
      imagem do mapa, com a grade de hexágonos sobreposta por cima.
- [ ] **Header "Ferramentas"** na seção de itens/paleta, para agrupar os controles.
- [ ] **Camada de arquitetura.** Adicionar uma camada intermediária (acima do
      terreno e abaixo dos tokens) para paredes, portas e afins.

### Correções
- [ ] **Balde bugado.** O preenchimento gera listras diagonais em vez de pintar o
      canvas inteiro; corrigir o algoritmo de flood fill.
- [ ] **Mapas aparecendo como tiles em "Terreno → Detalhes".** Imagens de mapa
      completo não devem figurar na paleta de terreno; servem apenas como imagem de
      fundo ao criar cenas. (relacionado ao fix recente de classificação de tiles)

---

## Cena ao vivo

### Correções
- [ ] **Régua não funciona.**
- [ ] **Marcador não muda de cor.**
- [ ] **Não dá para remover um marcador individual** — só é possível limpar todos.

### Melhorias
- [ ] **Ferramentas de texto e lápis** (anotação livre sobre a cena).
- [ ] **Menu lateral de iniciativa** (acompanhar a ordem de turnos durante a sessão).
- [ ] **Menu lateral de rolagem de dados.**

---

## Infra & manutenção

- [ ] **Padronizar tudo em Python 3.12.** Alinhar o ambiente de dev ao de produção
      (o `Dockerfile` já usa 3.12): recriar o venv local em 3.12, que é a versão
      suportada pelo Django 4.2 — assim a suíte roda sem o problema de render no test
      client visto no 3.14. Não exige atualizar o Django.
