# App: home

O app `home` e a porta de entrada publica do projeto. Ele decide o que acontece
quando alguem acessa a raiz da aplicacao e expoe um endpoint simples de saude
para infraestrutura.

## Para que serve

- Renderiza a landing page para visitantes nao autenticados.
- Redireciona usuarios autenticados da raiz (`/`) para `character:home`.
- Expoe `/healthz`, que responde `{"ok": true}` para checks de disponibilidade.

## Arquivos principais

- `views.py`: contem a view `home` e o health check `health`.
- `urls.py`: registra as rotas `/` e `/healthz`.
- `templates/home/landing.html`: pagina inicial publica.
- `tests.py`: cobre o comportamento de entrada e saude do app.

## Rotas

- `GET /`: landing page ou redirecionamento para fichas quando autenticado.
- `GET /healthz`: health check usado por deploy, monitoramento ou load balancer.

## Observacoes

Este app nao possui modelos de dominio. Alteracoes aqui devem ser tratadas como
mudancas de navegacao global, porque a raiz do site e o ponto de entrada comum
para usuarios e infraestrutura.
