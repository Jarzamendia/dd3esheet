# Prompts para agentes (Sonnet e Codex)

Estes são os prompts prontos para colar em cada agente. Eles assumem que ambos os agentes têm acesso ao repositório e a [`PLAN.md`](../PLAN.md) como fonte de verdade.

A alocação de tasks abaixo é a final — divergente do campo "Agente" das tasks individuais em alguns casos para evitar colisão de merge. Ver "Alocação final por agente" no fim do `PLAN.md` para a justificativa.

---

## Agente 1 — Sonnet (trilha "Infra / Segurança / Deploy")

```
Você é o Agente 1 (Sonnet) trabalhando no repositório dd3esheet
(Django 4.2 + HTMX, ficha de D&D 3.5, código em dd3esheet/).

Leia primeiro: PLAN.md na raiz do repo. Toda a estratégia está lá.
Você é dono das tasks da trilha Infra/Segurança/Deploy:

  T0.2  Carregar HTMX no template base (main.html)
  T1.1  Settings.py via variáveis de ambiente (django-environ + hardening)
  T1.2  Hardening de auth (seed guard, django-axes, login template)
  T1.4  WhiteNoise + STATIC_ROOT + collectstatic
  T1.6  Atomic + bulk_update em _recalculate_stats
  T1.7  Extrair funções puras de _recalculate_stats para calculations.py
  T1.8  Trocar <str:pk> por <int:pk> em character/urls.py
  T2.1  Dockerfile.prod + docker-compose.prod.yaml + Gunicorn
  T2.2  Health check /healthz + logging dictConfig
  T3.1  Criar docs/deployment.md e atualizar docs/README.md
  T3.2  Rodar manage.py check --deploy e pip-audit; relatório final

Coordenação com o Agente 2 (Codex):
- T0.1 (reescrita do requirements.txt em UTF-8) é dele. Antes de começar
  T1.1, T1.2 ou T1.4 você precisa do requirements.txt já em UTF-8 com
  django-environ, whitenoise, django-axes, gunicorn. Comece por T0.2
  enquanto ele faz T0.1 — são independentes.
- T1.5 (queries em _sheet_context) é dele e edita views.py. Você edita
  _recalculate_stats no mesmo arquivo (T1.6/T1.7). Coordenem por
  commit/branch e evitem editar a mesma função simultaneamente.
- T1.3 (validação POST) é dele e mexe nos helpers da view. Idem.

Convenções não-negociáveis:
- Working dir Django: dd3esheet/.
- Models de character/ usam PascalCase (Name, Strength, ACTotal). Mantenha.
- requirements.txt original está em UTF-16 LE BOM. NÃO regrave fora de T0.1.
- dnd35.sqlite3 é read-only. Toda query SDR precisa de .using('sdr').
- TDD: escreva o teste primeiro ou junto da implementação. A suite
  (python manage.py test) tem que ficar verde ao fim de cada task.
- Ao terminar cada task, atualize docs/ ou AGENTS.md se a mudança for
  arquitetural (settings, deploy, novos endpoints).

Ordem sugerida:
1. T0.2 (independente, libera testes E2E do Agente 2).
2. Aguardar Agente 2 sinalizar T0.1 pronto.
3. T1.1 → T1.2 → T1.4 (todos editam settings.py; faça em sequência).
4. T1.8 (URLs, isolado).
5. T1.6 → T1.7 (views.py::_recalculate_stats).
6. T2.1 → T2.2 (deploy).
7. T3.1 → T3.2 (encerramento, depois que tudo da Fase 1 e Fase 2 estiver mergeado).

Entregue cada task em um commit ou PR separado com mensagem
"T<id>: <título>" (ex: "T1.4: WhiteNoise + STATIC_ROOT").
Em cada PR, inclua:
- diff dos arquivos,
- comandos de teste executados e resultado,
- nota sobre qualquer coisa que ficou bloqueada esperando o outro agente.

Pode começar.
```

---

## Agente 2 — Codex GPT 5.5 (trilha "Domínio / Features / Tests")

```
Você é o Agente 2 (Codex) trabalhando no repositório dd3esheet
(Django 4.2 + HTMX, ficha de D&D 3.5, código em dd3esheet/).

Leia primeiro: PLAN.md na raiz do repo. Toda a estratégia está lá.
Você é dono das tasks da trilha Domínio/Features/Tests:

  T0.1  Reescrever dd3esheet/requirements.txt em UTF-8 enxuto
  T1.3  Validação consistente em _update_fields_from_post / _save_repeating_slots
  T1.5  prefetch_related/select_related em _sheet_context e home
  T1.9  Toggle de slot de magia via HTMX (template character_spells.html)
  T1.10 Página "Companheiros" editável (model + migration + view + template)
  T1.11 Página "Reputação" editável (3 models + migration + view + template)
  T1.12 DispatcherSmokeTest cobrindo os 16 targets HTMX
  T2.3  EndToEndSmoke (login → criar ficha → editar → confirmar persistência)

Coordenação com o Agente 1 (Sonnet):
- T0.1 é a primeira coisa que você faz: o Sonnet depende disso para começar
  T1.1/T1.2/T1.4. Sinalize quando terminar.
- T1.6 e T1.7 (refatorar _recalculate_stats em views.py) são dele.
  Você edita _sheet_context e os helpers no mesmo arquivo (T1.3/T1.5).
  Coordene por commit/branch; não editem a mesma função ao mesmo tempo.
- T0.2 (carregar HTMX no main.html) é dele e desbloqueia seus testes E2E
  (T2.3). Não inicie T2.3 antes de T0.2 mergeado.
- T1.8 (URLs <int:pk>) é dele; as suas views devem aceitar pk inteiro
  quando T1.8 entrar.

Convenções não-negociáveis:
- Working dir Django: dd3esheet/.
- requirements.txt está em UTF-16 LE BOM. T0.1 regrava em UTF-8 sem BOM,
  uma dep por linha, ordenado alfabeticamente.
  Dependências mínimas reais: Django==4.2.11, django-htmx==1.17.3,
  django-crispy-forms==2.1, crispy-bootstrap5==2024.2,
  django-bootstrap-v5==1.0.11, django-filter==24.2, sqlparse==0.4.4,
  asgiref==3.8.1, tzdata==2024.1.
  Adicionar para outras tasks: gunicorn==22.0.0, whitenoise==6.6.0,
  django-environ==0.11.2, django-axes==6.5.0.
  Remover tudo o que não é usado (kafka-python via git, google-cloud-*,
  numpy, pythonnet, aiohttp, beautifulsoup4, requests, etc.).
- Models de character/ usam PascalCase (Name, Strength, ACTotal). Mantenha
  ao criar CharacterCompanion, CharacterContact, CharacterFaction,
  CharacterContract.
- Novas migrations devem ser criadas via `makemigrations` dentro do
  container, com nome explícito (`--name`).
- dnd35.sqlite3 é read-only. Toda query SDR precisa de .using('sdr').
- HTMX dispatcher: a view character(request, pk) roteia por
  request.htmx.target. Cada novo POST de seção precisa de um target
  único e de um partial dedicado. Padrão: render(request,
  "character/partials/<nome>.html", _sheet_context(char)).
- TDD: escreva o teste primeiro ou junto da implementação. A suite
  (python manage.py test) precisa ficar verde no fim de cada task.

Ordem sugerida:
1. T0.1 (desbloqueia o Sonnet imediatamente; sinalize pronto).
2. T1.5 (prefetch em _sheet_context — base para tudo que renderiza ficha).
3. T1.3 (validação nos helpers da view, fica encostado em T1.5).
4. T1.9 (toggle de spell slot).
5. T1.10 (Companheiros).
6. T1.11 (Reputação).
7. T1.12 (DispatcherSmokeTest — cobre todas as branches do dispatcher).
8. T2.3 (E2E — só depois que T0.2 mergeou).

Entregue cada task em um commit ou PR separado com mensagem
"T<id>: <título>" (ex: "T1.10: página Companheiros editável").
Em cada PR, inclua:
- diff dos arquivos,
- nome e conteúdo da migration criada (se houver),
- comandos de teste executados e resultado,
- nota sobre qualquer coisa que ficou bloqueada esperando o Sonnet.

Pode começar por T0.1 imediatamente.
```

---

## Como usar

1. Cole o primeiro prompt no Agente 1 (Sonnet) e o segundo no Agente 2 (Codex).
2. O Codex começa por T0.1; o Sonnet começa por T0.2 em paralelo.
3. Quando T0.1 estiver pronto, o Sonnet libera T1.1 → T1.2 → T1.4 (mesmo `settings.py`, em série).
4. Os pontos de coordenação estão explícitos nos prompts: `settings.py` e `views.py` têm dono diferente por função/seção.
