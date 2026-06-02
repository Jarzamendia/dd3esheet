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

---

# Rodada 3 — Fase 4 (backlog UX/Feature)

Origem: [`NEW.md`](../NEW.md). As Fases 0–3 já estão fechadas; esta rodada cobre as 8 tasks novas T4.1–T4.8 do `PLAN.md`. Ambos os agentes podem começar em paralelo desde o primeiro minuto: T4.1 e T4.5 são totalmente independentes.

## Agente 1 — Sonnet (Fase 4 / Sprint A + B — UI/CSS dos Aliados)

```
Você é o Agente 1 (Sonnet) trabalhando no repositório dd3esheet
(Django 4.2 + HTMX, ficha de D&D 3.5, código em dd3esheet/).

Estado atual: ver "Status atual" no topo de PLAN.md. As Fases 0–3
estão 100% concluídas. A Fase 4 (backlog de UX/Feature, fonte
NEW.md) tem 8 tasks pendentes. Você é dono de 4:

  T4.1  Padronizar max-width das sub-páginas em 1280px
        Editar dd3esheet/static/css/character_sheet.css:
        igualar .companions-sheet e .sheet-utility a
        max-width: 1280px (hoje estão em 1180px).
        Teste SubPageWidthTest: assertContains de classe
        nas 3 sub-páginas (companions, daily-resources,
        reputation). Commit "T4.1: largura unificada 1280px".

  T4.2  Renomear "Companheiros" → "Aliados" na UI
        Mudar SÓ os rótulos visíveis (h1, nav, <title>) em
        companions.html, character.html, daily_resources.html,
        reputation.html. NÃO mexer em urls.py, view companions,
        model CharacterCompanion, paths de partials.
        Teste AlliesRenameTest. Commit "T4.2: renomear
        Companheiros para Aliados na UI".

  T4.3  Redesign do bloco Nome do Aliado/Familiar
        Em companions.html, envolver o input Name em
        .companion-name-line ocupando 100% de largura.
        CSS em character_sheet.css: Cinzel/Bold/uppercase
        para o input, EB Garamond itálico para subtítulo,
        linha tracejada. Adicionar .companion-quickstats
        em grid de 5 colunas (PV, CA, Desloc, Inic, RM).
        Conferir se Cinzel e EB Garamond estão carregadas
        em templates/main.html; se não, adicionar Google
        Fonts. Teste CompanionNameLineTest.
        Commit "T4.3: redesign do bloco Nome do Aliado".

  T4.4  Stack vertical + accordion Animal/Familiar
        Pré-requisito: T4.3 mergeada (mesmo arquivo).
        Em companions.html, reorganizar Animal Companion e
        Familiar em fluxo vertical (não lado a lado). Cada
        seção em <section.companion-section> com header
        clicável (🐾 Companheiro Animal / 🧙‍♂️ Familiar) e
        atributo data-collapsed iniciando "true" se o Name
        estiver vazio. CSS:
          .companion-section[data-collapsed="true"]
            .companion-section-body { display: none; }
        JS vanilla mínimo toggleCompanionSection(section).
        Teste CompanionCollapseTest (data-collapsed conforme
        Name preenchido ou não). Commit "T4.4: stack vertical
        e accordion para Animal/Familiar".

Convenções não-negociáveis:
- Working dir Django: dd3esheet/.
- Models de character/ usam PascalCase. Não tocar nos models
  nestas tasks (são puramente UI).
- dnd35.sqlite3 é read-only. Toda query SDR usa .using('sdr').
- TDD: teste antes ou junto. python manage.py test verde ao
  fim de cada task.
- NÃO adicionar trailer Co-Authored-By em commits.

Ordem sugerida:
1. T4.1 (CSS trivial, isolado).
2. T4.2 (rename de UI, isolado).
3. T4.3 (redesign do Name; cria classes que T4.4 vai herdar).
4. T4.4 (depende de T4.3 — mesmo arquivo).

Coordenação com o Codex (Agente 2):
- Codex está nas tasks T4.5–T4.8 (Livro de Magias + Summons).
  Ele edita companions.html para adicionar a seção
  "Invocações Ativas" (T4.6), então sincronize por commit
  para evitar conflito no mesmo arquivo.
- Codex também adiciona link de aba para o Livro de Magias
  (T4.5) nas 4 sub-páginas, podendo colidir com T4.2.
  Quem mergear depois faz rebase manual.

Entregue cada task em commit/PR separado nomeado
"T<id>: <título>". Em cada PR inclua:
- diff dos arquivos,
- comandos de teste executados (saída de manage.py test),
- nota se algum item da Fase 4 mudou de premissa.

Pode começar por T4.1.
```

## Agente 2 — Codex (Fase 4 / Sprint C + D — Livro de Magias + Summons)

```
Você é o Agente 2 (Codex) trabalhando no repositório dd3esheet
(Django 4.2 + HTMX, ficha de D&D 3.5, código em dd3esheet/).

Estado atual: ver "Status atual" no topo de PLAN.md. As Fases 0–3
estão 100% concluídas. A Fase 4 (backlog UX/Feature, fonte
NEW.md) tem 8 tasks; você é dono de 4:

  T4.5  Sub-página "Livro de Magias" + enxugar character_spells.html
        Criar view spellbook(request, pk) em character/views.py
        análoga a companions/reputation. Adicionar URL
        path('<int:pk>/spellbook/', views.spellbook,
             name='spellbook') em character/urls.py.
        Novo template character/templates/character/spellbook.html
        com header de slots (reusar partial) + magias agrupadas
        por SpellLevel (0..9) em accordion/abas.
        Em character_spells.html: REMOVER as duas <table>
        grandes (Slots Preparados de 20 linhas, Conhecidas/
        Grimório de 36 linhas), manter Resumo + Grid de Slots
        Diários, acrescentar
          <a class="btn btn-arcane"
             href="{% url 'character:spellbook' character.pk %}">
             📖 Abrir Livro de Magias
          </a>.
        Adicionar item de aba "Livro de Magias" em character.html,
        companions.html, daily_resources.html, reputation.html.
        Edição HTMX no spellbook segue o padrão do dispatcher
        (target único por seção, partial dedicado).
        Testes SpellbookPageTest + CharacterSpellsLeanTest.
        Validar com a ficha do seed Maelis Vorn (mago nv 8).
        Commit "T4.5: sub-página Livro de Magias".

  T4.6  Modelo CharacterSummon + grid 3 colunas
        Criar model em character/models.py (PascalCase):
        CharacterSummon(Character FK, Name, SpellOrigin, Level,
        HitPointsMax, HitPointsCurrent, ArmorClass, AttackBonus,
        Damage, SpecialAbility, RoundsTotal, RoundsRemaining,
        SdrMonsterName, CreatedAt; Meta.ordering=
        ('-RoundsRemaining','CreatedAt')).
        Migration NUMERADA conforme estado real (provavelmente
        0007_charactersummon — confirme com showmigrations).
        Integrar à view companions(request, pk): adicionar
        seção "Invocações Ativas" em companions.html com
        .summons-grid em grid de 3 colunas. Endpoint HTMX de
        criar/editar slot segue padrão _save_repeating_slots.
        Testes CharacterSummonModelTest + SummonsGridTest.
        Commit "T4.6: CharacterSummon e grid de invocações".

  T4.7  Sistema de favoritos (★)
        Pré-requisito: T4.6 mergeada.
        Migration: adicionar Highlighted = BooleanField(
        default=False) em CharacterSummon. Atualizar
        Meta.ordering = ('-Highlighted','-RoundsRemaining',
        'CreatedAt').
        View toggle_summon_highlight(request, pk, summon_id)
        validando dono via get_object_or_404, fazendo flip
        com save(update_fields=['Highlighted']) e retornando
        o partial do grid. URL toggle-summon-highlight.
        Botão ★/☆ no card com hx-post / hx-target="#summons-grid".
        Teste SummonHighlightToggleTest (flip + ordering +
        não-dono 404). Commit "T4.7: favoritos em invocações".

  T4.8  Autopreenchimento de Summon via SRD
        Pré-requisito: T4.6 mergeada (T4.7 pode rodar em
        paralelo — campos independentes).
        Confirmar nome real do model SDR em sdr/models.py
        (provavelmente Monster ou SdrMonster) e seus campos
        (name, hp, ac, attacks, special_abilities).
        Endpoint summon_search(request) GET ?q=...:
          q = request.GET.get('q','').strip()
          if len(q) < 2: return HttpResponse('')
          hits = SdrMonster.objects.using('sdr')
                  .filter(name__icontains=q)
                  .order_by('name')[:10]
          → render partial character/partials/summon_search_results.html
        Endpoint create_summon_from_monster(request, pk, monster_id)
        cria CharacterSummon com campos mapeados do
        SdrMonster, gravando SdrMonsterName=monster.name.
        UI: input com hx-trigger="keyup changed delay:300ms"
        e hx-get="{% url 'character:summon-search' %}";
        cada hit no dropdown com hx-post para criar.
        Teste SummonSrdIntegrationTest (TransactionTestCase
        com databases={'default','sdr'}, usar
        setup_sdr_class_table-style para popular tabela de
        teste). Casos: q='wolf' retorna ≥1; q='' retorna
        vazio; create_summon_from_monster persiste os
        campos esperados. Commit "T4.8: autopreencher
        Summon via SRD".

Convenções não-negociáveis:
- Working dir Django: dd3esheet/.
- Models de character/ usam PascalCase (Name, Strength,
  ACTotal). Mantenha em CharacterSummon.
- requirements.txt está em UTF-8 desde T0.1.
- dnd35.sqlite3 é read-only. Toda query SDR usa .using('sdr').
- HTMX dispatcher: cada novo POST de seção precisa de target
  único e partial dedicado. Padrão: render do partial com
  _sheet_context(char) ou subset coerente.
- Novas migrations via `makemigrations character --name <nome>`
  dentro do container.
- TDD: teste antes ou junto. python manage.py test verde ao
  fim de cada task.
- NÃO adicionar trailer Co-Authored-By em commits.

Ordem sugerida:
1. T4.5 (isolado, alto impacto — pode mergear cedo).
2. T4.6 (cria base para T4.7 e T4.8).
3. T4.7 e T4.8 em paralelo (campos independentes; cuidar
   da numeração de migrations sequencial).

Coordenação com o Sonnet (Agente 1):
- Sonnet está em T4.1–T4.4 (CSS + companions.html). Você edita
  companions.html em T4.6 para adicionar a seção "Invocações
  Ativas". Sincronize por commit/branch para evitar conflito.
- Em T4.5 você adiciona item de aba "Livro de Magias" em 4
  templates. Pode colidir com T4.2 do Sonnet (rename de
  Companheiros → Aliados). Quem mergear depois faz rebase
  manual — mudanças são pontuais.

Entregue cada task em commit/PR separado nomeado
"T<id>: <título>". Em cada PR inclua:
- diff dos arquivos,
- nome e conteúdo da migration criada (se houver),
- saída de python manage.py test,
- nota sobre regressão ou bloqueio.

Pode começar por T4.5.
```

## Como usar (Rodada 3)

1. Abra duas sessões CLI separadas na raiz do repo.
2. Cole o **prompt do Sonnet** numa, o **do Codex** noutra.
3. Ambos podem começar imediatamente em paralelo — T4.1 e T4.5 não compartilham arquivo.
4. Pontos de coordenação para sincronizar via commit/branch:
   - `companions.html` (T4.4 do Sonnet vs T4.6 do Codex);
   - itens de aba de nav nos 4 templates (T4.2 do Sonnet vs T4.5 do Codex).
5. Quando os 8 commits "T4.x: ..." estiverem em `main`, marcar o painel de status do `PLAN.md` como 27/27 ✅ e encerrar a Fase 4.
