# App: home

Este app serve como a porta de entrada principal da aplicação **dd3esheet**. Ele gerencia a página de aterrissagem (landing page) para usuários não autenticados e fornece endpoints utilitários como verificação de saúde (health check).

## Para que serve?

* **Landing Page:** Apresenta o projeto para usuários que ainda não estão logados.
* **Redirecionamento Inteligente:** Se um usuário já estiver autenticado e acessar a raiz da aplicação, ele é redirecionado automaticamente para a página de gerenciamento de fichas de personagens (`character:home`).
* **Verificação de Saúde (Health Check):** Fornece o endpoint `/healthz` que retorna o estado da aplicação (`{'ok': True}`), comumente utilizado em monitoramento de infraestrutura e pipelines de deploy.

## Principais Arquivos

* [views.py](views.py): Contém a lógica de redirecionamento/renderização da landing page e a view simples do health check.
* [urls.py](urls.py): Define as rotas principais do app (`/` e `/healthz`).
* `templates/home/landing.html`: O template HTML renderizado para usuários não autenticados na página inicial.
* [tests.py](tests.py): Testes automatizados para garantir que o redirecionamento e a view de saúde estejam funcionando corretamente.
