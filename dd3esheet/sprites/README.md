# App: sprites

Este app gerencia os arquivos de imagem (sprites, tokens, retratos, fundos de mapa) utilizados em toda a plataforma. Ele é responsável pelo armazenamento, redimensionamento automático de imagens (geração de variantes) e a vinculação inteligente (bindings) dessas imagens aos elementos do jogo (classes, monstros e fichas).

## Para que serve?

* **Biblioteca de Assets (SpriteAsset):** Cadastra e categoriza imagens em tipos como `classe`, `monstro`, `personagem`, `companheiro`, `mini de mapa`, `tile de mapa`, `item` e `genérico`.
* **Geração de Variantes (SpriteVariant):** Redimensiona imagens enviadas para resoluções específicas adequadas para o front-end (ex: *Thumb 64x64*, *Ícone 96x96*, *Token 128x128*, *Token 256x256*, *Retrato 320x320*, *Retrato 640x640*). Isso melhora o desempenho e economiza banda.
* **Mapeamento de Assets (SpriteBinding):** Associa um asset de sprite a um elemento de regra do jogo. Por exemplo, vincula o token de "Orc" a um ID de monstro no banco de dados SDR (SRD do D&D 3.5), ou um ícone de escudo à classe "Guerreiro".
* **Checksum e Otimização:** Calcula hashes SHA-256 dos arquivos de imagem para evitar duplicações e gerenciar uploads de forma mais robusta.

## Principais Arquivos

* [models.py](models.py): Define `SpriteAsset` (o arquivo original com metadados e âncora), `SpriteVariant` (as imagens redimensionadas) e `SpriteBinding` (a tabela de relacionamento que vincula um asset a uma chave de regras, como um monstro ou classe).
* [services.py](services.py): Centraliza as regras de negócio de processamento de imagem, geração física das variantes de imagem usando bibliotecas de imagem, e métodos de busca/resolução de vínculos (ex: `sprite_for_class`, `sprite_for_monster`).
* [views.py](views.py): Fornece interfaces HTML e endpoints para buscar na biblioteca de sprites, ver detalhes de um asset específico, e expor manifestos das imagens disponíveis.
* [seeds.py](seeds.py): Utilitário para popular o banco de dados com ícones padrão de classe e tokens de monstros iniciais.
* [manifest_data.py](manifest_data.py): Contém os dados estruturados usados para mapeamento inicial dos ícones e assets em lote.
* [urls.py](urls.py): Define rotas de acesso à biblioteca, buscas, detalhes e manifesto de assets.
