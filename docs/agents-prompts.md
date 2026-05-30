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

---

# Rodada 2 — Prompts de fechamento

Estado em 2026-05-30: a Rodada 1 fechou 13 tasks (T0.1, T0.2, T1.1, T1.2, T1.4, T1.6, T1.7, T1.8, T1.9, T2.1, T2.2, T3.1, T3.2-parcial). Restam:

- **Codex:** T1.3, T1.5, T1.10 (finalizar), T1.11 (finalizar), T1.12, T2.3.
- **Sonnet:** revisão final de T3.2 (re-rodar `manage.py check --deploy` + suite completa) quando o Codex fechar.

Use os prompts abaixo para esta rodada. Eles assumem `PLAN.md` na raiz como fonte de verdade e que o histórico `git log` mostra os commits anteriores no formato `T<id>: <título>`.

## Agente 2 — Codex (fechamento da trilha de domínio)

```
Você é o Agente 2 (Codex) terminando o trabalho no repositório
dd3esheet (Django 4.2 + HTMX, código em dd3esheet/).

Estado atual: ver "Status atual" no topo de PLAN.md. A Rodada 1
fechou 13 tasks. Você ainda é dono de 6:

  T1.10 (finalizar) — Página Companheiros editável
       Working tree tem migration 0005_charactercompanion.py e
       templates companions.html + partials/companions_form.html
       UNTRACKED. Falta confirmar: model em character/models.py,
       view companions(request, pk) aceitando POST HTMX via
       _save_repeating_slots, teste CompanionsTest. Depois commite
       como "T1.10: Página Companheiros editável".

  T1.11 (finalizar) — Página Reputação editável
       Working tree tem reputation.html UNTRACKED. Falta criar
       os 3 models (CharacterContact, CharacterFaction,
       CharacterContract), migration 0006_reputation_entities,
       view reputation(request, pk) com dispatcher HTMX, teste
       ReputationTest. Commit "T1.11: Página Reputação editável".

  T1.3 — Validação consistente nos helpers POST de character/views.py
       Reforçar _update_fields_from_post e _save_repeating_slots
       com strip + clamp de IntegerField (-999..999) + truncamento
       por max_length. Teste FieldValidationTest. Commit
       "T1.3: validação consistente em helpers POST".

  T1.5 — Otimizar queries em _sheet_context e home
       Trocar os 11+ _ordered_slots por prefetch_related único;
       opcional manager Character.objects.with_full_sheet(pk).
       Teste QueryCountTest com CaptureQueriesContext. Meta:
       render de /character/<pk> em ≤ 15 queries. Commit
       "T1.5: prefetch_related em _sheet_context".

  T1.12 — DispatcherSmokeTest
       Em character/tests.py, classe parametrizada que faz POST
       HTMX para cada um dos 16 targets do dispatcher (ver lista
       em docs/inline-editing.md) e valida status 200 +
       assertTemplateUsed. Commit "T1.12: DispatcherSmokeTest".

  T2.3 — EndToEndSmoke
       TransactionTestCase com databases = {'default','sdr'}.
       Fluxo: registra/loga usuário → cria ficha → POST HTMX em
       characterStatsForm mudando Strength → GET ficha e assertua
       StrengthStatMod recalculado. Pré-requisito: T1.10, T1.11
       e T1.12 fechados. Commit "T2.3: EndToEndSmoke".

Convenções não-negociáveis (reforçar — não mudaram):
- Working dir Django: dd3esheet/.
- Models de character/ usam PascalCase (Name, Strength, ACTotal).
- requirements.txt está em UTF-8 desde T0.1 — pode mexer
  normalmente se uma task pedir.
- dnd35.sqlite3 é read-only. Toda query SDR usa .using('sdr').
- HTMX dispatcher: cada novo POST de seção precisa de target
  único e partial dedicado. Padrão: render do partial com
  _sheet_context(char).
- TDD: teste antes ou junto da implementação. python manage.py
  test verde ao fim de cada task.
- NÃO adicionar trailer Co-Authored-By em commits deste repo.

Ordem sugerida:
1. T1.10 (terminar e commitar — work in progress fica caro)
2. T1.11 (mesmo padrão)
3. T1.3 (independente)
4. T1.5 (independente, mas afeta perf de tudo — rodar QueryCountTest
   depois)
5. T1.12 (cobre o dispatcher inteiro)
6. T2.3 (espera 1-5 estarem mergeadas)

Coordenação com o Sonnet (Agente 1):
- O Sonnet vai esperar você fechar tudo para rodar a revisão final
  de T3.2 (manage.py check --deploy + suite completa + pip-audit).
  Avise quando T2.3 estiver mergeada.

Entregue cada task em commit/PR separado nomeado "T<id>: <título>".
Em cada PR, inclua:
- diff dos arquivos,
- nome e conteúdo da migration criada (se houver),
- saída de python manage.py test (deve estar verde),
- nota sobre qualquer regressão ou bloqueio.

Comece por T1.10 (commitar o que já está no working tree, depois
fechar o que falta).
```

## Agente 1 — Sonnet (revisão final + closure)

```
Você é o Agente 1 (Sonnet) fazendo o fechamento do roadmap em
dd3esheet (Django 4.2 + HTMX, código em dd3esheet/).

Estado atual: ver "Status atual" no topo de PLAN.md. A Rodada 1
fechou T0.2, T1.1, T1.2, T1.4, T1.6, T1.7, T1.8, T2.1, T2.2, T3.1
e a versão parcial de T3.2 (pip-audit em d662521). O Codex está
fechando T1.3, T1.5, T1.10, T1.11, T1.12 e T2.3.

Sua única task aberta:

  T3.2 — Revisão final e checklist de deploy (segunda passada)
       Pré-requisito: Codex avisar que T2.3 mergeou.

       Quando o Codex sinalizar:

       1. git pull --rebase para puxar tudo.
       2. python manage.py check --deploy com DEBUG=False:
            DEBUG=False SECRET_KEY=x ALLOWED_HOSTS=localhost \
            python manage.py check --deploy
          Endereçar TODA warning restante (esperado: zero
          warnings). Se sobrar, abrir patches direcionados,
          NÃO ignorar.
       3. python manage.py test — suite inteira verde,
          incluindo o que o Codex acabou de adicionar
          (DispatcherSmokeTest, EndToEndSmoke,
          CompanionsTest, ReputationTest).
       4. docker compose -f docker-compose.prod.yaml up --build,
          GET / e GET /healthz devem retornar 200.
       5. pip-audit novamente (já rodado em d662521; só
          confirmar que nenhum upgrade do Codex regrediu).
       6. Atualizar o painel de status no topo de PLAN.md
          marcando todas as tasks como ✅ concluída.
       7. Atualizar docs/known-issues.md removendo os itens
          que viraram realidade (companions/reputation
          editáveis, validação consistente, query budget).
       8. Commit final: "T3.2 (final): deploy checklist
          verde, suite completa verde". Sem trailer
          Co-Authored-By.

       Entregável: PR description curto com:
       - número final de queries por render de /character/<pk>,
       - tempo médio do _recalculate_stats,
       - resultado de check --deploy (deve dizer "no issues"),
       - linha do pip-audit,
       - status final de PLAN.md (espera-se 19/19 ✅).

Enquanto espera o Codex (opcional, só se quiser adiantar):
- Releia docs/deployment.md e veja se algo precisa de update
  para refletir T1.10/T1.11 (novas páginas) ou T1.5
  (variáveis de perf).
- Releia docs/known-issues.md e prepare o diff antes do
  fechamento (sem commitar ainda — depende do que o Codex
  entregar).

Convenções:
- Working dir Django: dd3esheet/.
- NÃO adicionar trailer Co-Authored-By em commits.
- Sem mexer em código de domínio do Codex sem coordenação.

Aguarde o Codex sinalizar T2.3 mergeada para iniciar a passada
final.
```

## Como usar (Rodada 2)

1. Cole o **prompt do Codex** primeiro. Ele vai trabalhar as 6 tasks pendentes em sequência.
2. Cole o **prompt do Sonnet** em seguida, em outra sessão. Ele fica em standby até o Codex avisar que T2.3 está mergeada.
3. Quando o Sonnet finalizar T3.2, todas as 19 tasks do PLAN.md devem estar ✅.
