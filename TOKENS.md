Crie novos assets para o sistema de mapas e tokens, mantendo o mesmo estilo visual dos tokens e mapas já existentes no projeto.

Nesta etapa, não gere imagens, PNGs, artes finais ou arquivos visuais. O objetivo agora é apenas fazer os assets existirem na estrutura do projeto em `/sprites`, com nomes, categorias e metadados suficientes para que as imagens sejam criadas depois.

Quando um asset ainda não tiver imagem, ele deve ser cadastrado como pendente/placeholder, mantendo o caminho esperado em `/sprites` e uma descrição clara do que deverá ser criado futuramente.

O objetivo é expandir a biblioteca de criação de mapas com:

- Items
- Markers & Status
- Terrenos modulares
- Peças de construções
- Cenas prontas editáveis

Todos os assets devem funcionar em mapas top-down para RPG de mesa, com aparência medieval/fantasia, leitura clara em grid e boa integração visual entre si.

# Objetivo principal

Transformar a categoria "City & World Maps" em um conjunto de cenas prontas para edição, usando tokens modulares de terreno, estruturas, itens e marcadores.

As cenas devem ser montáveis e editáveis a partir de peças menores, como terrenos, paredes, portas, árvores, caminhos, objetos e marcadores.

# Cenas prontas

Crie assets suficientes para montar as seguintes cenas:

1. Vilarejo na floresta
- Um pequeno vilarejo medieval em uma clareira.
- Deve incluir casas simples, taverna, prefeitura, estábulo e igreja.
- O vilarejo deve ter ruas de terra batida, áreas de grama, cercas, poço, carroças e vegetação ao redor.

2. Floresta com estrada
- Uma floresta densa atravessada por uma estrada.
- Deve incluir árvores variadas, mato alto, clareiras, troncos caídos, pedras e bifurcações de caminho.

3. Pântano labiríntico
- Um pântano com caminhos estreitos e confusos.
- Deve parecer um labirinto natural, onde apenas um caminho leva até o final.
- Incluir água escura, lama, mato alto, troncos, ilhas secas e áreas perigosas.

4. Fortaleza medieval
- Uma pequena fortaleza com muralhas, torres e um castelo no centro.
- Deve incluir pátio interno, portão, estrada de acesso, chão de pedra, áreas de defesa e construções auxiliares.

# Terrenos necessários

Crie tiles e tokens de terreno compatíveis entre si, preferencialmente modulares e repetíveis.

## Vilarejos medievais simples
- Rua de terra batida
- Grama baixa
- Mato alto
- Chão de pedras irregulares
- Cercas simples
- Trilhas
- Áreas de lama
- Poço
- Pequenos jardins

## Cidades medievais
- Estrada de pedra
- Pátios de pedra
- Fonte
- Calçadas
- Paredes externas de casas
- Pisos internos simples
- Muralhas
- Torres
- Portões
- Elementos de castelo

## Florestas
- Árvores individuais
- Grupos de árvores
- Mato alto
- Clareiras
- Arbustos
- Pedras
- Troncos caídos
- Caminhos de terra
- Bordas de floresta

## Pântanos
- Água escura/alagada
- Lama
- Solo seco de pântano
- Mato alto
- Lagos negros
- Ilhas de terra
- Troncos submersos
- Raízes expostas
- Caminhos estreitos

## Planaltos e regiões rochosas
- Chão de pedra montanhosa
- Pedras soltas
- Penhascos
- Caminhos rochosos
- Plataformas naturais
- Bordas elevadas

# Peças de construções

Crie peças modulares que possam ser combinadas para formar casas, tavernas, igrejas, estábulos, muralhas e castelos.

## Construções simples
- Parede de madeira reta
- Parede de madeira em canto
- Parede de madeira quebrada
- Porta de madeira fechada
- Porta de madeira aberta
- Janela simples
- Telhado de palha
- Telhado de madeira
- Piso de madeira
- Piso de terra batida interno

## Construções de pedra
- Parede de pedra reta
- Parede de pedra em canto
- Parede de pedra danificada
- Porta reforçada
- Portão grande
- Janela arqueada
- Torre circular
- Torre quadrada
- Muralha reta
- Muralha em canto
- Escada de pedra
- Piso de castelo
- Pátio interno

## Peças especiais
- Altar de igreja
- Bancos de igreja
- Balcão de taverna
- Mesas e cadeiras
- Barris
- Caixas
- Feno
- Cochos de estábulo
- Carroça
- Placa de estrada
- Poço
- Fonte

# Items

Crie tokens de itens utilizáveis em mapas, com fundo transparente:

- Baú fechado
- Baú aberto
- Saco de moedas
- Pilha de tesouro
- Espada no chão
- Escudo
- Pergaminho
- Livro antigo
- Chave
- Tocha
- Lanterna
- Barril
- Caixa
- Corda
- Armadilha simples
- Alavanca
- Pedra rúnica
- Cristal mágico
- Poção
- Mesa com comida
- Saco de suprimentos

# Markers & Status

Crie marcadores visuais claros para uso em mapa e combate.

## Marcadores de mapa
- Ponto de interesse
- Entrada
- Saída
- Objetivo
- Perigo
- Tesouro
- NPC importante
- Missão
- Área bloqueada
- Área secreta
- Acampamento
- Armadilha

## Status de personagem ou criatura
- Envenenado
- Atordoado
- Paralisado
- Caído
- Sangrando
- Queimando
- Congelado
- Assustado
- Invisível
- Protegido
- Amaldiçoado
- Abençoado
- Concentrando
- Morto/Inconsciente

# Regras visuais

- Estilo top-down, adequado para VTT/RPG de mesa.
- Fantasia medieval, com aparência coesa entre todos os assets.
- Boa leitura em tamanhos pequenos.
- Assets de terreno devem se encaixar visualmente entre si.
- Tokens de itens, peças e marcadores devem ter fundo transparente.
- Evitar excesso de detalhes que dificultem a leitura no mapa.
- Usar sombras suaves e iluminação consistente.
- Manter proporção compatível com grid quadrado.
- Sempre que possível, criar variações para evitar repetição visual.

# Entregáveis esperados

Para cada asset, fornecer:

- Nome claro e padronizado
- Categoria
- Subcategoria
- Descrição curta
- Tamanho sugerido em tiles/grid
- Caminho esperado dentro de `/sprites`
- Estado inicial como pendente/placeholder, sem imagem gerada nesta etapa
- Versão modular quando for terreno, parede, estrada ou construção
- Variações quando útil

Não criar arquivos PNG reais agora. As imagens finais serão criadas depois, usando os registros e caminhos definidos nesta etapa.

Use nomes em formato consistente, por exemplo:

- terrain_village_dirt_road_straight
- terrain_forest_clearing_small
- building_wood_wall_straight
- item_chest_closed
- marker_danger
- status_poisoned

# Prioridade

Priorize primeiro os assets necessários para montar:

1. Vilarejo na floresta
2. Floresta com estrada
3. Pântano labiríntico
4. Fortaleza medieval

Depois complete os itens, marcadores e status adicionais.
