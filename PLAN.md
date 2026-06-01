# PLAN.md — Roadmap para ambiente de testes online

Este plano divide o trabalho em **tasks autocontidas**, cada uma executável por um agente (Sonnet ou Codex) sem precisar de contexto extra além do que está descrito. Tasks com o mesmo `Fase` podem rodar em paralelo entre si.

## Objetivos finais

1. App rodando em servidor público (ambiente de testes), acessível por URL.
2. Configurações de segurança aplicadas (Django checklist de produção).
3. Correções de performance (queries, recalculo, render).
4. Todos os componentes da ficha (edição inline, páginas extras, toggles) funcionando ponta a ponta.

## Status atual (2026-06-01) — Fases 0–3 concluídas; Fase 4 em andamento (T4.1–T4.5 ✅, T4.6–T4.8 pendentes)

Legenda: ✅ concluída · ⬜ não iniciada

| Fase | Task  | Status | Commit / Notas                                                        |
|------|-------|--------|-----------------------------------------------------------------------|
| 0    | T0.1  | ✅     | `fe3d0c7` — requirements UTF-8 enxuto                                 |
| 0    | T0.2  | ✅     | `02cf28c` — HTMX no template base                                     |
| 1A   | T1.1  | ✅     | `fd4862a` — django-environ + hardening                                |
| 1A   | T1.2  | ✅     | `8fecf01` — seed guard + django-axes + login                          |
| 1A   | T1.3  | ✅     | `3b876f6` — validação consistente nos helpers POST                    |
| 1A   | T1.4  | ✅     | `b07c2b5` — WhiteNoise + STATIC_ROOT                                  |
| 1B   | T1.5  | ✅     | `96b7821` — prefetch_related em `_sheet_context` e home               |
| 1B   | T1.6  | ✅     | `bf7e796` — atomic + bulk_update                                      |
| 1B   | T1.7  | ✅     | `d8d4319` — funções puras em calculations.py                          |
| 1C   | T1.8  | ✅     | `02cf28c` — `<int:pk>` nas URLs                                       |
| 1C   | T1.9  | ✅     | `02c34e5` — toggle de spell slot                                      |
| 1C   | T1.10 | ✅     | `9aa488f` — página Companheiros editável (migration 0005)             |
| 1C   | T1.11 | ✅     | `8264230` — página Reputação editável (Contact/Faction/Contract)      |
| 1C   | T1.12 | ✅     | `3b59a16` — DispatcherSmokeTest (16 targets)                          |
| 2    | T2.1  | ✅     | `7811bf2` — Dockerfile.prod + compose.prod                            |
| 2    | T2.2  | ✅     | `7811bf2` — `/healthz` + logging                                      |
| 2    | T2.3  | ✅     | `f960945` — EndToEndSmoke                                             |
| 3    | T3.1  | ✅     | `11c9e4c` — docs/deployment.md                                        |
| 3    | T3.2  | ✅     | T3.2 (final) — check --deploy zero issues, 107 testes verdes, pip-audit limpo |
| 4    | T4.1  | ✅     | `a3e89a3` — largura unificada 1280px nas sub-páginas                  |
| 4    | T4.2  | ✅     | `8e71fd2` — renomear "Companheiros" → "Aliados" na UI (URL preservada) |
| 4    | T4.3  | ✅     | `634909e` — redesign do bloco Nome do Aliado/Familiar                 |
| 4    | T4.4  | ✅     | `be6b5ab` — stack vertical + accordion Animal/Familiar                |
| 4    | T4.5  | ✅     | `e45a15d` — sub-página "Livro de Magias" + enxugar `character_spells.html` |
| 4    | T4.6  | ⬜     | Modelo `CharacterSummon` + grid de 3 colunas de invocações ativas     |
| 4    | T4.7  | ⬜     | Sistema de favoritos (★) em invocações                                |
| 4    | T4.8  | ⬜     | Autopreenchimento de Summon via SRD (`SdrMonster`)                    |

**Fases 0–3 concluídas (19 tasks). Fase 4 (backlog de UX/feature de [`NEW.md`](NEW.md)) traz 8 novas tasks.**

## Visão geral em fases

```
Fase 0 (sequencial, bloqueante) → desbloqueia tudo
  T0.1  Reescrever requirements.txt (UTF-8 enxuto)
  T0.2  Carregar HTMX no template base

Fase 1 (paralela)             ← depende de T0.1 e T0.2
  Trilha A — Segurança          (T1.1, T1.2, T1.3, T1.4)
  Trilha B — Performance        (T1.5, T1.6, T1.7)
  Trilha C — Componentes        (T1.8, T1.9, T1.10, T1.11, T1.12)

Fase 2 (paralela)             ← depende de Fase 1
  T2.1  Deploy (Dockerfile prod + WSGI + docker-compose.prod)
  T2.2  Health check + observabilidade básica
  T2.3  Testes de smoke E2E (login → criar ficha → editar → ver salvo)

Fase 3 (sequencial)           ← depende de Fase 2
  T3.1  Documentação de deploy e variáveis de ambiente
  T3.2  Code review final e checagem da Django deployment checklist

Fase 4 (backlog UX/feature — NEW.md)
  Sprint A — Layout/Visuais     (T4.1, T4.2, T4.3)
  Sprint B — Empilhar Aliados    (T4.4 — depende de T4.3)
  Sprint C — Livro de Magias     (T4.5)
  Sprint D — Summons             (T4.6 → T4.7, T4.8)
```

---

## Convenções para agentes

- **Working dir Django:** `dd3esheet/` (subdiretório do repo). Comandos `python manage.py ...` rodam dentro do container ou do venv local apontado para esse diretório.
- **Convenção PascalCase** nos models de `character/` (não Django padrão, mas convenção do projeto). Mantenha.
- **`dnd35.sqlite3` é read-only**; toda query SDR usa `.using('sdr')`.
- **`requirements.txt` original está em UTF-16 LE com BOM** — só pode ser regravado conforme T0.1.
- **TDD:** todo agente deve escrever/atualizar testes na mesma PR. `python manage.py test` precisa passar verde no fim de cada task.
- **Documentação:** ao terminar, atualizar `docs/` ou `AGENTS.md` quando a task mudar algo arquitetural relevante.
- **Encoding dos arquivos novos:** UTF-8 sem BOM, exceto onde explicitamente dito o contrário.

---

# Fase 0 — Pré-requisitos sequenciais

## T0.1 — Reescrever `requirements.txt` em UTF-8 enxuto

**Status:** ✅ concluída (`fe3d0c7`)
**Tipo:** segurança/build
**Pré-requisitos:** nenhum
**Pode paralelizar com:** T0.2 (independentes)
**Agente:** Codex ou Sonnet

### Contexto
`dd3esheet/requirements.txt` está em UTF-16 LE com BOM e contém ~30 dependências, várias **não usadas** pelo projeto (kafka-python via git, google-cloud-*, numpy, pythonnet, aiohttp). Isso aumenta tempo de build do Docker, superfície de ataque e risco de incompatibilidades em deploy.

### Objetivo
Substituir por um `requirements.txt` UTF-8 contendo só as dependências reais do projeto e suas pinagens.

### Passos
1. Rodar `pipdeptree` (ou inspeção manual via `grep -r "^import\|^from " dd3esheet/`) para confirmar o conjunto mínimo. As dependências reais usadas no código são:
   - `Django==4.2.11`
   - `django-htmx==1.17.3`
   - `django-crispy-forms==2.1`
   - `crispy-bootstrap5==2024.2`
   - `django-bootstrap-v5==1.0.11`
   - `django-filter==24.2`
   - `sqlparse==0.4.4`
   - `asgiref==3.8.1`
   - `tzdata==2024.1`
2. Acrescentar as dependências de produção/segurança que outras tasks vão exigir:
   - `gunicorn==22.0.0` (T2.1)
   - `whitenoise==6.6.0` (T1.4)
   - `django-environ==0.11.2` (T1.1)
3. Escrever o arquivo em **UTF-8 sem BOM**, uma dependência por linha, ordenado alfabeticamente.
4. Reconstruir a imagem Docker para validar:
   ```
   docker compose build --no-cache
   docker compose run --rm web python manage.py check
   ```

### Entregáveis
- `dd3esheet/requirements.txt` regravado em UTF-8.

### Testes
- `docker compose build` completa sem erro.
- `docker compose run --rm web python manage.py check` retorna `System check identified no issues`.
- `docker compose run --rm web python manage.py test` continua verde.

---

## T0.2 — Carregar HTMX no template base

**Status:** ✅ concluída (`02cf28c`)
**Tipo:** componente
**Pré-requisitos:** nenhum
**Pode paralelizar com:** T0.1
**Agente:** Sonnet

### Contexto
`dd3esheet/static/htmx.min.js` existe e `django_htmx` está instalado/middleware ativo, mas **nenhum template carrega o script**. Sem isso, todos os atributos `hx-*` ficam inertes — a ficha vira read-only no browser apesar do backend estar pronto. Esse é o bloqueador #1 para "componentes funcionarem".

### Objetivo
Carregar HTMX em `dd3esheet/templates/main.html` e adicionar CSRF para POSTs HTMX.

### Passos
1. Editar `dd3esheet/templates/main.html`. Antes de `{% block extra_js %}{% endblock %}`, adicionar:
   ```html
   <script src="{% static 'htmx.min.js' %}"></script>
   {% load django_htmx %}
   {% django_htmx_script %}
   ```
2. Garantir que requests HTMX enviam o token CSRF. Acrescentar ao mesmo bloco:
   ```html
   <script>
     document.body.addEventListener('htmx:configRequest', (event) => {
       const token = document.querySelector('[name=csrfmiddlewaretoken]');
       if (token) event.detail.headers['X-CSRFToken'] = token.value;
     });
   </script>
   ```
3. Conferir manualmente que cada partial editável tem um `{% csrf_token %}` dentro do `<form>` ou `<input type="hidden" name="csrfmiddlewaretoken" ...>` disponível na página.

### Entregáveis
- `dd3esheet/templates/main.html` editado.
- Se faltar `csrf_token` em algum partial, adicionar.

### Testes
- Novo teste `character/tests.py::HtmxLoadedTest`:
  - GET `/character/<pk>` autenticado → resposta contém `htmx.min.js`.
  - Resposta contém o evento `htmx:configRequest` ou `django_htmx_script` renderizado.
- Teste manual obrigatório: subir o app, editar um atributo (ex: Strength) e validar que o valor persiste sem reload (use DevTools → Network para confirmar POST).

---

# Fase 1 — Trabalho paralelo (3 trilhas)

## Trilha A — Segurança

### T1.1 — Settings de produção via variáveis de ambiente

**Status:** ✅ concluída (`fd4862a`)
**Pré-requisitos:** T0.1 (precisa de `django-environ`)
**Pode paralelizar com:** T1.2, T1.3, T1.4, T1.5, T1.6, T1.7, T1.8…T1.12
**Agente:** Sonnet (dono único de `settings.py` em T1.1/T1.2/T1.4)

#### Contexto
`dd3esheet/dd3esheet/settings.py` tem `DEBUG=True`, `SECRET_KEY` hardcoded, `ALLOWED_HOSTS=[]`, sem `CSRF_TRUSTED_ORIGINS`. Estado claramente de desenvolvimento.

#### Objetivo
Refatorar `settings.py` para ler do ambiente, com defaults seguros para produção e overrides para dev.

#### Passos
1. Acrescentar no topo de `settings.py`:
   ```python
   import environ
   env = environ.Env(
       DEBUG=(bool, False),
       SECRET_KEY=(str, ''),
       ALLOWED_HOSTS=(list, []),
       CSRF_TRUSTED_ORIGINS=(list, []),
   )
   environ.Env.read_env(BASE_DIR / '.env')
   ```
2. Substituir os literais:
   ```python
   SECRET_KEY = env('SECRET_KEY')
   DEBUG = env('DEBUG')
   ALLOWED_HOSTS = env('ALLOWED_HOSTS')
   CSRF_TRUSTED_ORIGINS = env('CSRF_TRUSTED_ORIGINS')
   ```
3. Adicionar bloco de segurança (aplicado **apenas quando `DEBUG=False`**):
   ```python
   if not DEBUG:
       SECURE_SSL_REDIRECT = True
       SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
       SECURE_HSTS_INCLUDE_SUBDOMAINS = True
       SECURE_HSTS_PRELOAD = True
       SECURE_CONTENT_TYPE_NOSNIFF = True
       SECURE_BROWSER_XSS_FILTER = True
       SECURE_REFERRER_POLICY = 'same-origin'
       SESSION_COOKIE_SECURE = True
       CSRF_COOKIE_SECURE = True
       SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
       X_FRAME_OPTIONS = 'DENY'
   ```
4. Criar `dd3esheet/.env.example` com:
   ```
   SECRET_KEY=changeme-generate-with-django-utils
   DEBUG=False
   ALLOWED_HOSTS=localhost,127.0.0.1
   CSRF_TRUSTED_ORIGINS=https://localhost
   ```
5. Adicionar `.env` em `.gitignore` se ainda não estiver.
6. Ajustar `docker-compose.yaml` (mantém DEBUG=True para local) e preparar gancho para `docker-compose.prod.yaml` (criado em T2.1).

#### Entregáveis
- `dd3esheet/dd3esheet/settings.py` refatorado.
- `dd3esheet/.env.example`.
- `.gitignore` atualizado.

#### Testes
- `python manage.py check --deploy` quando `DEBUG=False` deve ter **zero** issues de severidade ≥ warning.
- Teste unitário `character/tests.py::SettingsHardeningTest` que importa o módulo settings com `DEBUG=False` via monkey-patch e assertua que `SECURE_HSTS_SECONDS > 0` e `SESSION_COOKIE_SECURE is True`.

---

### T1.2 — Endurecer auth e permissões

**Status:** ✅ concluída (`8fecf01`)
**Pré-requisitos:** T0.1
**Pode paralelizar com:** T1.1, T1.3, T1.4 etc.
**Agente:** Sonnet

#### Contexto
Hoje:
- `LOGIN_URL = '/accounts/login/'` mas o template de login padrão do Django é feio e não tem proteção contra brute force.
- `character.views` já usa `@login_required` e `get_object_or_404(Character, pk=pk, User=request.user)`.
- Seed cria admin `jarza/P@ssw0rd` automático no `docker compose up`.

#### Objetivo
- Garantir que o seed **não** crie o admin com senha fraca em produção.
- Adicionar rate limit básico ao login.
- Aumentar requisitos de senha.

#### Passos
1. Em `character/management/commands/seed.py` (ou onde estiver a chamada `seed_all`), envolver a criação do admin com:
   ```python
   if settings.DEBUG or env('SEED_ADMIN', default=False):
       seed_admin()
   ```
2. Em `AUTH_PASSWORD_VALIDATORS` aumentar `MinimumLengthValidator` para `min_length: 12`.
3. Adicionar `django-axes==6.5.0` em `requirements.txt` (coordenar com T0.1 se ainda em curso). Configurar:
   ```python
   INSTALLED_APPS += ['axes']
   MIDDLEWARE = ['axes.middleware.AxesMiddleware'] + MIDDLEWARE
   AXES_FAILURE_LIMIT = 5
   AXES_COOLOFF_TIME = 1  # hora
   AUTHENTICATION_BACKENDS = ['axes.backends.AxesStandaloneBackend', 'django.contrib.auth.backends.ModelBackend']
   ```
4. Criar `templates/registration/login.html` minimamente estilizado consistente com o resto da UI.

#### Entregáveis
- `character/management/commands/seed.py` editado.
- `settings.py` editado (validadores + axes).
- `templates/registration/login.html`.
- Migration `axes` aplicada via `migrate`.

#### Testes
- `character/tests.py::SeedAdminGuardTest`:
  - Com `DEBUG=False` e env sem `SEED_ADMIN`, `seed_all()` não cria o admin.
  - Com `DEBUG=True`, cria normalmente.
- `character/tests.py::LoginBruteForceTest`:
  - 5 logins falhos consecutivos → 6º recebe 403 (cooloff axes).

---

### T1.3 — Validação consistente em todos os blocos da ficha

**Status:** ⬜ não iniciada
**Pré-requisitos:** T0.2 (HTMX precisa estar carregado para testes E2E)
**Pode paralelizar com:** T1.1, T1.2, T1.4…T1.12
**Agente:** Codex

#### Contexto
Em `character/views.py::character` só `characterIdentityForm`, `characterForm` e `characterStatsForm` usam `ModelForm` crispy. Todo o resto (skills, weapons, equipment, items, money, feats, abilities, languages, spells, progress) chama `_update_fields_from_post` / `_save_repeating_slots`, que aceitam **qualquer string**, sem clean_*.

#### Objetivo
Adicionar uma camada fina de validação para os campos que recebem `IntegerField` (já são coercidos para int, mas sem bound), `BooleanField` (já ok) e campos textuais sensíveis (limites de tamanho, strip de espaços, escape de HTML).

#### Passos
1. Em `character/views.py::_update_fields_from_post`, antes do `setattr`:
   - Strings: `.strip()[:model_field.max_length or 200]`.
   - IntegerFields: validar range `(-999, 999)` para todos os campos da ficha. Reusar `_to_int` mas com clamp.
2. Para `_save_repeating_slots`, validar comprimento textual via `model._meta.get_field(field).max_length`.
3. Não introduzir crispy/ModelForm para tudo — manter os helpers, mas com defesa.

#### Entregáveis
- `character/views.py` com helpers reforçados.

#### Testes
- `character/tests.py::FieldValidationTest`:
  - POST com valor numérico fora do range é clampado, não 500.
  - POST com string acima do `max_length` é truncada.
  - POST com HTML injectado em campo de texto é preservado como string (não autoescaped no banco, mas autoescape no template já cuida no render).

---

### T1.4 — Static files de produção (WhiteNoise + collectstatic)

**Status:** ✅ concluída (`b07c2b5`)
**Pré-requisitos:** T0.1 (precisa de `whitenoise`)
**Pode paralelizar com:** outras de Fase 1
**Agente:** Sonnet

#### Contexto
Não existe `STATIC_ROOT`, então `collectstatic` não roda. Em produção, o `runserver` é proibido e precisamos servir static via WhiteNoise dentro do Gunicorn.

#### Objetivo
Configurar WhiteNoise e `STATIC_ROOT`. Executar `collectstatic` no boot do container de produção.

#### Passos
1. `settings.py`:
   ```python
   STATIC_ROOT = BASE_DIR / 'staticfiles'
   STORAGES = {
       'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
       'staticfiles': {
           'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
       },
   }
   ```
2. `MIDDLEWARE` (após `SecurityMiddleware`, antes do resto):
   ```python
   'whitenoise.middleware.WhiteNoiseMiddleware',
   ```
3. Adicionar `staticfiles/` em `.gitignore`.
4. Verificar que `static/css/character_sheet.css` e `static/htmx.min.js` aparecem em `staticfiles/` após `collectstatic`.

#### Entregáveis
- `settings.py` editado.
- `.gitignore` atualizado.

#### Testes
- `docker compose run --rm web python manage.py collectstatic --noinput` completa.
- `character/tests.py::StaticFilesTest`:
  - WhiteNoiseMiddleware está em `MIDDLEWARE`.
  - `STATIC_ROOT` é configurado e é dentro de `BASE_DIR`.

---

## Trilha B — Performance

### T1.5 — Reduzir queries em `_sheet_context` e `home`

**Status:** ⬜ não iniciada
**Pré-requisitos:** nenhum
**Pode paralelizar com:** outras de Fase 1
**Agente:** Codex

#### Contexto
`character.views._sheet_context(char)` chama 11+ querysets `_ordered_slots(...)` mais `characterskill_set.all()`, `spellcasting_context(char)` (que toca `sdr`) e `CharacterProgress.objects.get_or_create`. Cada render da ficha hoje dispara ~30+ queries.

`home(request)` já usa `select_related` mas não `prefetch_related` para os slots na listagem (caso a `home.html` consuma).

#### Objetivo
Cortar pelo menos 50% das queries por render.

#### Passos
1. Em `_sheet_context`, substituir os 11 `_ordered_slots(...)` por **uma única** chamada que carrega tudo via `prefetch_related`:
   ```python
   char = Character.objects.select_related(
       'characterstats', 'characterstatus', 'charactersavingthrows',
       'characterattackmodifiers', 'characterskillgraduation',
       'characterotheritemobs', 'charactermoney', 'characterspellcasting',
   ).prefetch_related(
       'characterweapon_set', 'characterprotectionitem_set',
       'characterotheritem_set', 'characterfeat_set', 'ability_set',
       'characterlanguages_set', 'characterspellslot_set',
       'characterspell_set', 'characterskill_set',
   ).get(pk=char.pk)
   ```
   Ou expor isso via um manager method `Character.objects.with_full_sheet(pk)`.
2. Cachear `spellcasting_context(char)` por request (são leituras do SDR `class_table` constantes para o mesmo char). Usar `functools.lru_cache` em funções puras puras (não no `_sheet_context` em si).
3. Em `home`, adicionar `prefetch_related` para o que `home.html` consumir (auditar template para saber).

#### Entregáveis
- `character/views.py` editado.
- Opcional: manager method em `character/models.py`.

#### Testes
- `character/tests.py::QueryCountTest`:
  - Render de `/character/<pk>` autenticado consome `≤ N` queries (definir N pela medida pós-refactor + margem; meta < 15).
  - Use `django.test.utils.CaptureQueriesContext`.
- Suite existente continua verde.

---

### T1.6 — Otimizar `_recalculate_stats` (transação única + update_fields)

**Status:** ✅ concluída (`bf7e796`)
**Pré-requisitos:** nenhum
**Pode paralelizar com:** outras de Fase 1
**Agente:** Sonnet

#### Contexto
`character/views.py::_recalculate_stats(character)` faz ~6 `.save()` separados e itera skills com `.save(update_fields=...)` por linha. Cada autosave HTMX chama essa função.

#### Objetivo
- Empacotar em `transaction.atomic`.
- Trocar `instance.save()` por `instance.save(update_fields=[...])` em todos os siblings.
- Skills: usar `bulk_update`.

#### Passos
1. Anotar `from django.db import transaction`.
2. Envolver corpo de `_recalculate_stats` em `with transaction.atomic():`.
3. Para `stats`, `graduation`, `status`, `saves`, `attack`, `encumbrance`: declarar a lista exata de campos alterados e passar em `update_fields=`.
4. Para o loop de skills:
   ```python
   skills = list(CharacterSkill.objects.filter(Character=character))
   for skill in skills:
       skill.SkillAbility = ...
       skill.AbilityModifier = ...
       skill.SkillModifier = ...
   CharacterSkill.objects.bulk_update(skills, ['SkillAbility', 'AbilityModifier', 'SkillModifier'])
   ```

#### Entregáveis
- `character/views.py::_recalculate_stats` refatorado.

#### Testes
- Suite existente continua verde (especialmente `RecalculateStatsTest` se já houver).
- `character/tests.py::RecalculateQueryBudget`:
  - `_recalculate_stats(char)` faz ≤ 10 queries (defina o número pós-refactor, margem +2).

---

### T1.7 — Mover `_recalculate_stats` para `calculations.py` (funções puras + 1 persistência)

**Status:** ✅ concluída (`d8d4319`)
**Pré-requisitos:** T1.6
**Pode paralelizar com:** outras (exceto T1.6)
**Agente:** Sonnet (mesmo dono de T1.6, mesma função `_recalculate_stats`)

#### Contexto
Doc em `docs/known-issues.md` já lista isso como melhoria. As regras de CA, saves, iniciativa e grapple ainda vivem na view; só os pedaços de matemática mais primitivos foram para `calculations.py`.

#### Objetivo
- Extrair funções puras `compute_armor_class(...)`, `compute_save_totals(...)`, `compute_grapple_total(...)`, `compute_skill_row(...)`, `compute_encumbrance(...)` para `character/calculations.py`.
- `_recalculate_stats` vira orquestrador fino: lê fontes de verdade, chama puras, persiste.

#### Passos
1. Para cada bloco no `_recalculate_stats`, criar uma função pura recebendo primitivos (não models). Ex:
   ```python
   def compute_armor_class(*, armor_bonus, shield_bonus, dex_mod, size_mod,
                            natural_armor, deflection, misc):
       total = 10 + armor_bonus + shield_bonus + dex_mod + size_mod + natural_armor + deflection + misc
       touch = 10 + dex_mod + size_mod + deflection + misc
       flat_footed = 10 + armor_bonus + shield_bonus + size_mod + natural_armor + deflection + misc
       return total, touch, flat_footed
   ```
2. Em `views.py::_recalculate_stats`, importar e chamar; manter persistência atômica conforme T1.6.

#### Entregáveis
- `character/calculations.py` com novas funções puras.
- `character/views.py::_recalculate_stats` reduzido a orquestração.
- Doc `docs/character-domain.md` e `docs/known-issues.md` atualizados.

#### Testes
- `character/tests.py::PureCalculationsTest` com `SimpleTestCase` cobrindo cada nova função pura com pelo menos 3 casos (zero, positivo, negativo).
- Suite existente continua verde.

---

## Trilha C — Componentes da ficha

### T1.8 — Fix `<str:pk>` → `<int:pk>` em todas as URLs de character

**Status:** ✅ concluída (`02cf28c`)
**Pré-requisitos:** nenhum
**Pode paralelizar com:** outras
**Agente:** Sonnet

#### Contexto
Em `character/urls.py`, as rotas usam `<str:pk>` mesmo sendo IDs numéricos. Isso aceita inputs malformados que viram 404 mais tarde no `get_object_or_404`, é menos eficiente e quebra inferência de URL.

#### Passos
1. Em `character/urls.py`, trocar todos os `<str:pk>` por `<int:pk>`.
2. Conferir templates / testes que referenciam URLs continuam funcionando (Django's reverse aceita int).

#### Entregáveis
- `character/urls.py` editado.

#### Testes
- Suite existente verde.
- `character/tests.py::UrlPkIntTest`: GET `/character/abc` retorna 404 (validação URL); GET `/character/<pk>` numérico autenticado retorna 200.

---

### T1.9 — Toggle de slot de magia funcionando inline

**Status:** ✅ concluída (`02c34e5`)
**Pré-requisitos:** T0.2
**Pode paralelizar com:** outras
**Agente:** Codex

#### Contexto
Existe `views.toggleSpellSlot(request, pk, slot_id)` que retorna o partial inteiro de magias, mas é preciso confirmar que o template `character_spells.html` realmente tem um `hx-post` no checkbox/botão de cada slot.

#### Objetivo
Validar / corrigir o markup para que clicar num slot use HTMX, sem reload, e atualize só o partial.

#### Passos
1. Ler `character/templates/character/partials/character_spells.html`.
2. Para cada slot, garantir um `<button>` ou `<form>` com:
   ```html
   hx-post="{% url 'character:toggle-spell-slot' character.pk slot.id %}"
   hx-target="#characterSpellsForm"
   hx-swap="outerHTML"
   ```
3. O botão precisa estar fora do `<form>` principal de magias (ou usar `hx-include` correto).

#### Entregáveis
- `character/templates/character/partials/character_spells.html` ajustado.

#### Testes
- `character/tests.py::SpellSlotToggleTest`:
  - POST HTMX para `toggle-spell-slot` flipa `IsUsed`.
  - Retorna 200 e o partial.
  - GET subsequente confirma o estado persistido.

---

### T1.10 — Página "Companheiros" editável

**Status:** 🟡 em progresso — migration `0005_charactercompanion.py`, `companions.html` e `companions_form.html` existem no working tree mas ainda não foram commitados; falta confirmar view + testes
**Pré-requisitos:** nenhum
**Pode paralelizar com:** outras
**Agente:** Codex

#### Contexto
`character.views.companions(request, pk)` hoje só renderiza dados estáticos (listagem de aliados-da-natureza por nível) — não persiste nada. Precisa virar uma área de ficha com slots para companheiros animais, familiares, montarias.

#### Objetivo
Criar um sibling model `CharacterCompanion` (FK para Character) e fazer a página `companions.html` salvar via HTMX.

#### Passos
1. Criar model:
   ```python
   class CharacterCompanion(models.Model):
       Character = models.ForeignKey(Character, on_delete=models.CASCADE)
       Type = models.CharField(max_length=200, blank=True)   # 'animal', 'familiar', 'mount', ...
       Name = models.CharField(max_length=200, blank=True)
       Species = models.CharField(max_length=200, blank=True)
       HitPoints = models.IntegerField(default=0)
       ArmorClass = models.IntegerField(default=0)
       Speed = models.CharField(max_length=50, blank=True)
       Skills = models.TextField(blank=True)
       Feats = models.TextField(blank=True)
       SpecialAbilities = models.TextField(blank=True)
       Notes = models.TextField(blank=True)
   ```
2. Migration `0005_charactercompanion`.
3. View `companions(request, pk)`:
   - GET → render com 4 slots de `CharacterCompanion`.
   - POST HTMX → salvar via `_save_repeating_slots`.
4. Template `companions.html` com `<form hx-post hx-target>` em volta dos slots.

#### Entregáveis
- `character/models.py` editado.
- `character/migrations/0005_charactercompanion.py`.
- `character/views.py` editado.
- `character/templates/character/companions.html` editado.

#### Testes
- `character/tests.py::CompanionsTest`:
  - Criar/editar 2 companions via POST HTMX.
  - GET refletindo os dados salvos.
  - Slots vazios não criam linhas.

---

### T1.11 — Página "Reputação" editável

**Status:** 🟡 em progresso — `reputation.html` existe no working tree, mas ainda não há migration para `CharacterContact/Faction/Contract` e nada foi commitado
**Pré-requisitos:** nenhum
**Pode paralelizar com:** outras
**Agente:** Codex

#### Contexto
Igual ao T1.10: `reputation.html` é puramente estática hoje (`contact_slots = range(1,17)` etc., só para layout).

#### Objetivo
Criar models `CharacterContact`, `CharacterFaction`, `CharacterContract` e persistir via HTMX.

#### Passos
1. Models:
   ```python
   class CharacterContact(models.Model):
       Character = models.ForeignKey(Character, on_delete=models.CASCADE)
       Name = models.CharField(max_length=200, blank=True)
       Description = models.CharField(max_length=500, blank=True)
       Reliability = models.IntegerField(default=0)

   class CharacterFaction(models.Model):
       Character = models.ForeignKey(Character, on_delete=models.CASCADE)
       Name = models.CharField(max_length=200, blank=True)
       Standing = models.IntegerField(default=0)
       Notes = models.CharField(max_length=500, blank=True)

   class CharacterContract(models.Model):
       Character = models.ForeignKey(Character, on_delete=models.CASCADE)
       Title = models.CharField(max_length=200, blank=True)
       Patron = models.CharField(max_length=200, blank=True)
       Reward = models.CharField(max_length=200, blank=True)
       Status = models.CharField(max_length=50, blank=True)
   ```
2. Migration `0006_reputation_entities`.
3. View `reputation(request, pk)` aceita POST HTMX e dispatcha por `request.htmx.target`.

#### Entregáveis
- Models + migration + view + template editados.

#### Testes
- `character/tests.py::ReputationTest`:
  - POST HTMX para cada uma das 3 seções persiste.
  - Render mostra os valores salvos.

---

### T1.12 — Smoke tests cobrindo todos os targets do dispatcher

**Status:** ⬜ não iniciada
**Pré-requisitos:** T0.2
**Pode paralelizar com:** outras
**Agente:** Codex

#### Contexto
`character.views.character(request, pk)` tem 16 branches HTMX. Hoje os testes cobrem alguns (identity, stats), mas não a matriz inteira.

#### Objetivo
Garantir que cada `target` em `_HTMX_TARGETS = [...]` responde 200 e devolve o partial certo.

#### Passos
1. Em `character/tests.py`, criar `DispatcherSmokeTest` parametrizado:
   ```python
   TARGETS = {
       'characterIdentityForm': 'character/partials/character_identity.html',
       'characterForm': 'character/partials/character_description.html',
       'characterStatsForm': 'character/partials/character_stats.html',
       'characterStatusForm': 'character/partials/character_combat.html',
       'characterArmorForm': 'character/partials/character_combat.html',
       'characterSavesForm': 'character/partials/character_stats.html',
       'characterAttackForm': 'character/partials/character_stats.html',
       'characterSkillsForm': 'character/partials/character_skills.html',
       'characterWeaponsForm': 'character/partials/character_weapon_card.html',
       'characterProgressForm': 'character/partials/character_progress.html',
       'characterEquipmentForm': 'character/partials/character_armor.html',
       'characterItemsForm': 'character/partials/character_items.html',
       'characterMoneyForm': 'character/partials/character_money.html',
       'characterFeatsForm': 'character/partials/character_feats.html',
       'characterSpecialsForm': 'character/partials/character_specials.html',
       'characterSpellsForm': 'character/partials/character_spells.html',
   }
   ```
2. Para cada target: POST mínimo com header `HX-Request: true` e `HX-Target: <target>`. Validar status 200 e template renderizado (`assertTemplateUsed`).

#### Entregáveis
- `character/tests.py::DispatcherSmokeTest`.

#### Testes
- A própria task entrega os testes.
- Suite completa verde.

---

# Fase 2 — Deploy e observabilidade

## T2.1 — Dockerfile e docker-compose de produção

**Status:** ✅ concluída (`7811bf2`)
**Pré-requisitos:** T0.1, T1.1, T1.4
**Pode paralelizar com:** T2.2, T2.3
**Agente:** Sonnet (continuidade da trilha de infra/deploy)

### Contexto
Hoje só existe `docker-compose.yaml` que roda `runserver` em modo dev. Produção precisa de Gunicorn, multistage build (opcional), e configuração separada.

### Passos
1. Criar `dd3esheet/Dockerfile.prod`:
   ```dockerfile
   FROM python:3.12-slim
   ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   COPY . .
   RUN python manage.py collectstatic --noinput
   EXPOSE 8000
   CMD ["gunicorn", "dd3esheet.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-"]
   ```
2. Criar `dd3esheet/docker-compose.prod.yaml`:
   ```yaml
   services:
     web:
       build:
         context: .
         dockerfile: Dockerfile.prod
       env_file:
         - .env
       command: >
         sh -c "python manage.py migrate &&
                gunicorn dd3esheet.wsgi:application --bind 0.0.0.0:8000 --workers 3 --access-logfile -"
       ports:
         - "8000:8000"
       restart: unless-stopped
   ```
3. Garantir que `.env` é lido (T1.1).
4. Verificar que `migrate` roda no boot mas `seed` **não** (admin com senha fixa é proibido em prod).

### Entregáveis
- `Dockerfile.prod`, `docker-compose.prod.yaml`.

### Testes
- `docker compose -f docker-compose.prod.yaml build` completa.
- Subir local com `.env` apontando `DEBUG=False` e testar GET `/` retorna 200.

---

## T2.2 — Healthcheck + logging estruturado

**Status:** ✅ concluída (`7811bf2`)
**Pré-requisitos:** T1.1
**Pode paralelizar com:** T2.1, T2.3
**Agente:** Sonnet

### Passos
1. Criar `home/views.py::health(request)` retornando `JsonResponse({'ok': True})` (no DB hit) e `home/urls.py` mapeando `/healthz`.
2. Configurar `LOGGING` em `settings.py` com `json` handler (stdout) — sem dependência externa, usar `logging.config.dictConfig`.
3. Adicionar healthcheck no `docker-compose.prod.yaml`:
   ```yaml
   healthcheck:
     test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
     interval: 30s
     timeout: 3s
     retries: 3
   ```

### Entregáveis
- `home/views.py`, `home/urls.py`, `settings.py`, `docker-compose.prod.yaml`.

### Testes
- `home/tests.py::HealthCheckTest`: GET `/healthz` retorna 200 sem auth.

---

## T2.3 — Smoke test E2E (login → criar ficha → editar → ver salvo)

**Status:** ⬜ não iniciada
**Pré-requisitos:** T0.2, todas as tasks da trilha C
**Pode paralelizar com:** T2.1, T2.2
**Agente:** Codex (continuidade da trilha C, conhece os fluxos das telas)

### Passos
1. `character/tests.py::EndToEndSmoke` (TransactionTestCase com `databases = {'default', 'sdr'}`):
   - registra/loga usuário,
   - cria ficha via POST,
   - faz POST HTMX em `characterStatsForm` mudando `Strength`,
   - GET `/character/<pk>/` e assertua que `StrengthStatMod` foi recalculado.

### Entregáveis
- Suite E2E em `character/tests.py`.

### Testes
- Próprio entregável.

---

# Fase 3 — Encerramento

## T3.1 — Documentação de deploy e variáveis de ambiente

**Status:** ✅ concluída (`11c9e4c`)
**Pré-requisitos:** T2.1, T2.2
**Agente:** Sonnet

### Passos
1. Acrescentar em `docs/` um arquivo `deployment.md`:
   - Como gerar `SECRET_KEY` (`python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`).
   - Variáveis obrigatórias em `.env`.
   - Sequência: `docker compose -f docker-compose.prod.yaml up -d --build`.
   - Como verificar healthcheck e logs.
   - Aviso explícito: nunca rodar seed/admin em prod sem flag.
2. Atualizar `docs/README.md` para apontar para `deployment.md`.
3. Atualizar `docs/known-issues.md` removendo o item de HTMX-não-carregado (resolvido em T0.2).

### Entregáveis
- `docs/deployment.md`.
- `docs/README.md`, `docs/known-issues.md` atualizados.

### Testes
- N/A (doc).

---

## T3.2 — Code review + Django deployment checklist

**Status:** ✅* parcial (`d662521` — `pip-audit` rodado). Refazer quando T1.3, T1.5, T1.10, T1.11, T1.12 e T2.3 fecharem para validar `check --deploy` zero warnings com o app inteiro.
**Pré-requisitos:** todas as outras
**Agente:** Sonnet (ou Code Review especializado)

### Passos
1. Rodar `python manage.py check --deploy` com `DEBUG=False` e endereçar **toda** warning restante.
2. Rodar a suite completa: `python manage.py test`.
3. Rodar smoke manual no container de produção localmente.
4. Verificar que `.env` não está commitado.
5. Conferir que requirements não trouxe deps com CVE conhecidas (`pip-audit`).

### Entregáveis
- Relatório curto (PR description) listando: deploy checklist passou; cobertura final de testes; queries por render de ficha; tempo médio do recalculate.

### Testes
- Suite verde.
- `pip-audit` sem alertas críticos.

---

# Fase 4 — Backlog de UX/Feature (NEW.md)

Fonte: [`NEW.md`](NEW.md). Esta fase **não** é pré-requisito para o critério "pronto para colocar online" (Fases 0–3 já cumprem isso); são melhorias incrementais de UX, layout e features de combate/conjuração. Cada task continua autocontida e exige TDD.

## Sprint A — Layout e Visuais (baixo risco, totalmente paralelo)

### T4.1 — Padronizar `max-width` das sub-páginas em 1280px

**Status:** ✅ concluída (`a3e89a3`)
**Tipo:** UI/CSS
**Pré-requisitos:** nenhum
**Pode paralelizar com:** T4.2, T4.3, T4.5, T4.6
**Agente:** Sonnet ou Codex (trivial)

#### Contexto
`character.html` usa `.sheet` com `max-width: 1280px`. As sub-páginas (`companions.html`, `daily_resources.html`, `reputation.html`) usam `.companions-sheet` / `.sheet-utility`, ambas em 1180px. Resultado: encolhimento horizontal de 100px ao trocar de aba.

#### Passos
1. Em `dd3esheet/static/css/character_sheet.css`, ajustar:
   ```css
   .companions-sheet,
   .sheet-utility {
       max-width: 1280px;
   }
   ```
2. Conferir visualmente que grids internos seguem responsivos (sem barras horizontais).

#### Entregáveis
- `character_sheet.css` editado.

#### Testes
- `character/tests.py::SubPageWidthTest`: GET de `/character/<pk>/companions/`, `/daily-resources/`, `/reputation/` autenticado → `assertContains` da classe alvo (`companions-sheet` ou `sheet-utility`).
- Smoke manual: navegar entre abas e confirmar ausência de "soluço" horizontal.

---

### T4.2 — Renomear "Companheiros" → "Aliados" na interface (URL preservada)

**Status:** ✅ concluída (`8e71fd2`)
**Tipo:** UI/i18n
**Pré-requisitos:** nenhum
**Pode paralelizar com:** T4.1, T4.3, T4.5, T4.6
**Agente:** Sonnet

#### Contexto
"Companheiros" ambíguo em PT — confunde com colegas de mesa. A página gerencia animal companion, familiar, montaria e asseclas. Renomear só os rótulos exibidos; **manter** rota `/companions/`, nome de view, nome de URL Django (`character:companions`) e nomes de model.

#### Passos
1. `grep` por "Companheiros" em `dd3esheet/character/templates/` e `dd3esheet/templates/`.
2. Trocar para **"Aliados"** (ou "Aliados & Acompanhantes" onde houver espaço) em:
   - `<h1>` de `companions.html` ("Aliados do Personagem").
   - Itens de navegação superior em `character.html`, `daily_resources.html`, `reputation.html`.
   - `<title>` da página.
3. **Não** alterar: `character/urls.py`, `views.companions`, model `CharacterCompanion`, paths de partials.

#### Entregáveis
- Templates editados.

#### Testes
- `character/tests.py::AlliesRenameTest`:
  - GET `/character/<pk>/companions/` → `assertContains('Aliados')`, `assertNotContains('Companheiros')` no `<h1>` e nav.
  - `reverse('character:companions', kwargs={'pk': c.pk})` continua resolvendo para `/character/<pk>/companions/`.

---

### T4.3 — Redesign do bloco "Nome" do Aliado/Familiar (linha 100%, tipografia premium)

**Status:** ✅ concluída (`634909e`)
**Tipo:** UI/UX
**Pré-requisitos:** nenhum
**Pode paralelizar com:** T4.1, T4.2, T4.5, T4.6
**Agente:** Sonnet

#### Contexto
O campo `Name` do animal/familiar está dentro de um grid de duas colunas, espremido. NEW.md pede que ele ocupe linha inteira, com fonte Cinzel/EB Garamond e linha tracejada elegante. Abaixo dele, atributos rápidos (PV, CA, deslocamento, iniciativa, RM) em barra horizontal.

#### Passos
1. Em `companions.html` (ou em partial dedicado se existir), envolver o `<input name="...Name">` num bloco `.companion-name-line` com a etiqueta acima/abaixo e largura 100%.
2. Em `character_sheet.css`, adicionar:
   ```css
   .companion-name-line input {
       width: 100%;
       border: none;
       border-bottom: 2px dashed var(--ink-light, #2b1d10);
       font-family: 'Cinzel', serif;
       font-size: 1.5rem;
       font-weight: 700;
       text-transform: uppercase;
       letter-spacing: 0.05em;
       background: transparent;
   }
   .companion-name-line .subtitle {
       font-family: 'EB Garamond', serif;
       font-style: italic;
       font-size: 0.9rem;
   }
   .companion-quickstats {
       display: grid;
       grid-template-columns: repeat(5, 1fr);
       gap: 0.5rem;
       margin-top: 0.5rem;
   }
   ```
3. Conferir se Cinzel/EB Garamond já estão carregadas em `templates/main.html`; se não, adicionar `<link>` do Google Fonts.

#### Entregáveis
- `companions.html` editado.
- `character_sheet.css` editado.
- Possivelmente `templates/main.html` editado (Google Fonts).

#### Testes
- `character/tests.py::CompanionNameLineTest`: GET `/character/<pk>/companions/` autenticado → `assertContains('companion-name-line')` e `assertContains('companion-quickstats')`.
- Smoke visual: subir local e validar tipografia.

---

## Sprint B — Empilhar Aliados (médio risco)

### T4.4 — Stack vertical + toggle colapsável Animal/Familiar

**Status:** ✅ concluída (`be6b5ab`)
**Tipo:** UI/UX
**Pré-requisitos:** T4.3 (mesmo template — evita conflito)
**Pode paralelizar com:** T4.1, T4.2, T4.5, T4.6, T4.7, T4.8
**Agente:** Sonnet (continuidade de T4.3)

#### Contexto
Hoje Animal Companion e Familiar ficam lado a lado. Raros personagens têm os dois. NEW.md pede stack vertical com toggle (accordion). Quando o `Name` da seção é vazio, inicia colapsada com botão `+ Cadastrar`.

#### Passos
1. Em `companions.html`, reestruturar o container das duas seções:
   ```html
   <section class="companion-section" data-section="animal"
            {% if not animal.Name %}data-collapsed="true"{% endif %}>
     <header class="companion-section-header" onclick="toggleCompanionSection('animal')">
       <span>🐾 Companheiro Animal</span>
       <span class="chevron">▾</span>
     </header>
     <div class="companion-section-body">...</div>
   </section>
   <section class="companion-section" data-section="familiar"
            {% if not familiar.Name %}data-collapsed="true"{% endif %}>
     ...
   </section>
   ```
2. CSS: `.companion-section[data-collapsed="true"] .companion-section-body { display: none; }`.
3. JS vanilla mínimo num `<script>` em `companions.html` (ou em `static/js/companions.js`):
   ```js
   function toggleCompanionSection(section) {
     const el = document.querySelector(`.companion-section[data-section="${section}"]`);
     const collapsed = el.getAttribute('data-collapsed') === 'true';
     el.setAttribute('data-collapsed', collapsed ? 'false' : 'true');
   }
   ```
4. Para seção colapsada, mostrar botão `+ Cadastrar Companheiro Animal` que expande ao clicar.

#### Entregáveis
- `companions.html` reestruturado.
- `character_sheet.css` editado.
- JS inline ou em `static/js/companions.js`.

#### Testes
- `character/tests.py::CompanionCollapseTest`:
  - Ficha sem nome de animal/familiar → resposta contém `data-collapsed="true"` em ambas seções.
  - Ficha com nome preenchido → `data-collapsed="false"` (ou ausente).
- Smoke manual: clicar no header expande/colapsa sem reload.

---

## Sprint C — Livro de Magias (alto impacto)

### T4.5 — Sub-página `/spellbook/` + simplificação de `character_spells.html`

**Status:** ✅ concluída (`e45a15d`)
**Tipo:** componente/feature
**Pré-requisitos:** nenhum
**Pode paralelizar com:** T4.1–T4.4, T4.6
**Agente:** Codex (trilha de domínio/HTMX)

#### Contexto
`character_spells.html` hoje carrega: Resumo de conjuração + grid de slots diários (0–9) + tabela de 20 Slots Preparados + tabela de 36 Magias Conhecidas. As duas últimas alongam demais a ficha base. NEW.md pede mover essas tabelas para `/character/<pk>/spellbook/`, mantendo na base só Resumo + Grid de Slots + link para a nova página.

#### Objetivo
1. Criar view `spellbook(request, pk)` análoga a `companions`/`reputation`.
2. Movimentar tabelas para o novo template, agrupadas por Círculo (0 a 9) com accordion/abas.
3. Adicionar link "📖 Abrir Livro de Magias" no `character_spells.html`.
4. Edição HTMX no spellbook segue o padrão do dispatcher de `character` ou view local.

#### Passos
1. Adicionar em `character/urls.py`:
   ```python
   path('<int:pk>/spellbook/', views.spellbook, name='spellbook'),
   ```
2. Em `character/views.py`, criar `spellbook(request, pk)`:
   - Reusar `_sheet_context(char)` (ou subset) para resumo + slots.
   - Agrupar `CharacterSpell` por `SpellLevel` (0..9).
   - GET → render `character/spellbook.html`.
   - POST HTMX (preparar/desmarcar, editar magia conhecida) → atualizar partial do círculo afetado.
3. Criar `character/templates/character/spellbook.html` com header de slots + sections por nível.
4. Em `character/templates/character/partials/character_spells.html`:
   - **Remover** os dois blocos `<table>` grandes (Slots Preparados, Conhecidas/Grimório).
   - Manter Resumo e Grid de Slots.
   - Acrescentar `<a class="btn btn-arcane" href="{% url 'character:spellbook' character.pk %}">📖 Abrir Livro de Magias</a>`.
5. Adicionar item de menu/aba em `character.html`, `companions.html`, `daily_resources.html`, `reputation.html` apontando para o spellbook (consistência com as outras sub-páginas).

#### Entregáveis
- `character/urls.py` editado.
- `character/views.py` — nova view.
- `character/templates/character/spellbook.html` (novo).
- `character/templates/character/partials/character_spells.html` enxugado.
- Navegação atualizada nas 4 telas.

#### Testes
- `character/tests.py::SpellbookPageTest`:
  - GET `/character/<pk>/spellbook/` autenticado → 200, contém grupos por círculo (0 a 9).
  - Não-dono → 404.
  - Ficha de mago do seed (`Maelis Vorn`) → encontra as magias preparadas no círculo correto.
- `character/tests.py::CharacterSpellsLeanTest`:
  - GET `/character/<pk>/` → `assertNotContains` das tabelas removidas (texto característico) e `assertContains('Abrir Livro de Magias')`.
- Suite existente continua verde.

---

## Sprint D — Invocações de combate

### T4.6 — Modelo `CharacterSummon` + grid de 3 colunas de invocações ativas

**Status:** ⬜ não iniciada
**Tipo:** componente/feature
**Pré-requisitos:** nenhum
**Pode paralelizar com:** T4.1–T4.5
**Agente:** Codex

#### Contexto
Hoje não há model persistente de invocações. NEW.md pede grid de cards (3 por linha) na mesma página de Aliados (ou nova), com ataques rápidos, contador de rodadas e habilidades especiais.

#### Objetivo
Criar `CharacterSummon` (FK Character), migration, e renderizar grid 3 colunas na página de Aliados.

#### Passos
1. Em `character/models.py`, adicionar (PascalCase, padrão do projeto):
   ```python
   class CharacterSummon(models.Model):
       Character = models.ForeignKey(Character, on_delete=models.CASCADE)
       Name = models.CharField(max_length=200, blank=True)
       SpellOrigin = models.CharField(max_length=100, blank=True)   # "SNA III", "SM IV"
       Level = models.IntegerField(default=0)
       HitPointsMax = models.IntegerField(default=0)
       HitPointsCurrent = models.IntegerField(default=0)
       ArmorClass = models.IntegerField(default=0)
       AttackBonus = models.CharField(max_length=200, blank=True)
       Damage = models.CharField(max_length=200, blank=True)
       SpecialAbility = models.CharField(max_length=500, blank=True)
       RoundsTotal = models.IntegerField(default=0)
       RoundsRemaining = models.IntegerField(default=0)
       SdrMonsterName = models.CharField(max_length=200, blank=True)  # gancho p/ T4.8
       CreatedAt = models.DateTimeField(auto_now_add=True)

       class Meta:
           ordering = ('-RoundsRemaining', 'CreatedAt')
   ```
2. Migration `0007_charactersummon` (numerar conforme estado real do app).
3. View: integrar à `companions(request, pk)` (mesma página de Aliados) — adicionar seção "Invocações Ativas".
4. Template — grid:
   ```html
   <section class="summons-grid">
     {% for s in summons %}
       <article class="summon-card">
         <header>{{ s.Name }} <span>[{{ s.SpellOrigin }}]</span></header>
         <div class="row">PV: {{ s.HitPointsCurrent }} / {{ s.HitPointsMax }} · CA: {{ s.ArmorClass }}</div>
         <div class="row">⏳ {{ s.RoundsRemaining }}/{{ s.RoundsTotal }} rodadas</div>
         <div class="row">Atq: {{ s.AttackBonus }} ({{ s.Damage }})</div>
         <div class="row hability">{{ s.SpecialAbility }}</div>
       </article>
     {% endfor %}
   </section>
   ```
   ```css
   .summons-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }
   ```
5. Endpoint HTMX para criar/editar slot de Summon — pode seguir padrão `_save_repeating_slots`.

#### Entregáveis
- `models.py`, nova migration, `views.py`, `companions.html`, CSS.

#### Testes
- `character/tests.py::CharacterSummonModelTest` (SimpleTestCase com banco): persiste + ordering `-RoundsRemaining`.
- `character/tests.py::SummonsGridTest`: POST cria 3 summons; GET renderiza 3 cards no grid.

---

### T4.7 — Sistema de favoritos (★) em `CharacterSummon`

**Status:** ⬜ não iniciada
**Tipo:** componente/feature
**Pré-requisitos:** T4.6
**Pode paralelizar com:** T4.8 (campos independentes; coordenar migration)
**Agente:** Codex

#### Contexto
NEW.md pede botão ★/☆ que fixa um summon no topo do grid (`hx-post` instantâneo).

#### Passos
1. Migration `0008_summon_highlighted`:
   ```python
   Highlighted = models.BooleanField(default=False)
   ```
   Ajustar `Meta.ordering = ('-Highlighted', '-RoundsRemaining', 'CreatedAt')`.
2. View `toggle_summon_highlight(request, pk, summon_id)`:
   - Validar `summon.Character.pk == pk` e dono.
   - `summon.Highlighted = not summon.Highlighted; summon.save(update_fields=['Highlighted'])`.
   - Retornar o partial do grid (não a página inteira).
3. URL `path('<int:pk>/summon/<int:summon_id>/toggle-highlight/', views.toggle_summon_highlight, name='toggle-summon-highlight')`.
4. Botão no card:
   ```html
   <button hx-post="{% url 'character:toggle-summon-highlight' character.pk s.pk %}"
           hx-target="#summons-grid" hx-swap="outerHTML">
     {% if s.Highlighted %}★{% else %}☆{% endif %}
   </button>
   ```

#### Entregáveis
- Migration, view, URL, partial.

#### Testes
- `character/tests.py::SummonHighlightToggleTest`: POST HTMX flipa `Highlighted`, ordering coloca destacado no topo, não-dono → 404.

---

### T4.8 — Autopreenchimento de Summon via SRD (`SdrMonster`)

**Status:** ⬜ não iniciada
**Tipo:** integração SDR
**Pré-requisitos:** T4.6
**Pode paralelizar com:** T4.7
**Agente:** Codex

#### Contexto
NEW.md: formulário "Adicionar Invocação" com autocomplete que busca em `sdr.models.SdrMonster` (com `.using('sdr')`) e pré-preenche HP/CA/ataques/habilidades. Jogador só ajusta `RoundsRemaining` e `HitPointsCurrent`.

#### Passos
1. Confirmar o nome real do model em `sdr/models.py` (ex.: `Monster`/`SdrMonster`). Listar campos disponíveis (hp, ac, attacks, special_abilities).
2. Endpoint `path('summon/search/', views.summon_search, name='summon-search')` retornando JSON ou partial HTMX com lista de 10 hits para `q=...`:
   ```python
   def summon_search(request):
       q = request.GET.get('q', '').strip()
       if len(q) < 2:
           return HttpResponse('')
       hits = SdrMonster.objects.using('sdr').filter(name__icontains=q).order_by('name')[:10]
       return render(request, 'character/partials/summon_search_results.html', {'hits': hits})
   ```
3. Endpoint `create_summon_from_monster(request, pk, monster_id)`:
   - Lê `SdrMonster.objects.using('sdr').get(id=monster_id)`.
   - Mapeia campos para um novo `CharacterSummon` (HP, CA, ataque, dano, habilidade especial; `SdrMonsterName = monster.name`).
   - Volta o grid atualizado.
4. UI: campo de busca + dropdown de resultados (HTMX `hx-trigger="keyup changed delay:300ms"`).

#### Entregáveis
- Views, URLs, partial de resultados de busca, partial do form de criação.

#### Testes
- `character/tests.py::SummonSrdIntegrationTest` (`TransactionTestCase` com `databases = {'default', 'sdr'}`):
  - Buscar `q=wolf` retorna ≥1 resultado (usar `setup_sdr_class_table` ou similar para seed).
  - Criar summon a partir de monster_id preenche os campos esperados e persiste `SdrMonsterName`.
  - Buscas com `len(q) < 2` retornam vazio (não explode no DB).
- `q` malformado ou inexistente retorna vazio sem 500.

---

# Feature paralela — Popup SDR de Magias (branch `feat/sdr-spell-popup`)

Em paralelo à Fase 4, está em curso a feature de **autocomplete SDR + tooltip (hover) + modal (click)** para nomes de magia no Livro de Magias, Domínios de clérigo e Magias de Invocação. Plano detalhado e autocontido (12 tasks TDD) em [`docs/superpowers/plans/2026-05-30-sdr-spell-popup.md`].

| Task | Descrição                                                        | Status |
|------|-----------------------------------------------------------------|--------|
| 1    | `sdr.lookups.resolve_spell` (name/altname → SDR_Spell)          | ✅ `0cd7479` |
| 2    | `import_spells` usa `resolve_spell` (DRY)                       | ✅ `845c94d` |
| 3    | Coluna `CharacterSpell.SDRSpellId` + migration `0007`          | ✅ `ab2ee16` |
| 4    | Save hook resolve `SDRSpellId` no Livro de Magias              | ✅ `d1d637c` |
| 5    | View `spell_detail` + URL + partial `spell_detail_dialog.html` | ⬜ |
| 6    | `<dialog>` vazio em `main.html`                                 | ⬜ |
| 7    | CSS `.spell-input-wrap` / `.spell-tooltip` / `.spell-detail-dialog` | ⬜ |
| 8    | Partial reusável `_spell_tooltip.html`                         | ⬜ |
| 9    | Autocomplete (datalist) + tooltip + ícone no Livro de Magias   | ⬜ |
| 10   | Domínios de clérigo com tooltip + click                        | ⬜ |
| 11   | Magias de Invocação (Aliados) com tooltip + click             | ⬜ |
| 12   | Verificação visual manual (`/run`)                             | ⬜ |

---

# Fase 5 — Fechamento de MVP (cálculos, persistência, autosave ao digitar)

Estas tasks fecham o que falta para a ficha funcionar como **MVP de jogo real**: derivar automaticamente os números que hoje são digitados à mão, persistir o estado que hoje se perde, e salvar enquanto o usuário digita (não só no blur). Cada task é autocontida e exige TDD. Fonte de verdade do estado atual: `character/calculations.py` (puras já existentes) e `character/views.py::_recalculate_stats` (linhas 488–596).

## Sprint E — Autosave conforme o usuário escreve

### T5.1 — Salvar ao digitar (input) sem perder foco

**Status:** ⬜ não iniciada
**Tipo:** UX/HTMX (frontend + dispatcher)
**Pré-requisitos:** nenhum
**Agente:** ver alocação

#### Contexto
Todos os forms da ficha usam hoje `hx-trigger="change delay:300ms"` + `hx-swap="outerHTML"`. O evento `change` só dispara no **blur** (sair do campo), então a ficha **não salva enquanto o usuário digita**. Trocar ingenuamente para `keyup`/`input` quebra a UX: o `hx-swap="outerHTML"` substitui o form inteiro a cada tecla e o input perde foco/cursor.

#### Objetivo
Salvar texto enquanto o usuário digita, **sem** destruir o campo em foco, mantendo o recálculo de campos derivados.

#### Passos (abordagem recomendada — confirmar na implementação)
1. **Separar persistência de re-render.** Para campos puramente textuais (nomes, notas, descrições, páginas), disparar `hx-trigger="input changed delay:600ms"` com `hx-swap="none"` (servidor persiste e devolve `204 No Content` ou corpo vazio) — o input mantém foco e cursor.
2. **Manter `change` (com swap) para campos que alteram derivados** (atributos, BBA, bônus de armadura, ranks de perícia): ao sair do campo, recalcula e troca o partial. Opcionalmente, empurrar só os campos derivados via **OOB swap** (`hx-swap-oob`) para não tocar o input ativo.
3. Adicionar um **indicador de estado** discreto ("salvando…/salvo ✓") via `htmx:beforeRequest`/`htmx:afterRequest`.
4. Garantir que o dispatcher (`views.py::character` e as views de sub-página) aceitam POST sem header de swap e respondem corretamente quando `hx-swap="none"`.

#### Entregáveis
- Templates de partials editáveis com triggers ajustados.
- `views.py` (dispatcher) suportando resposta sem swap para saves de texto.
- Indicador de salvamento em `main.html`/CSS.

#### Testes
- `character/tests.py::AutosaveOnInputTest`: POST com `HX-Trigger` de `input` persiste o campo e responde 200/204 sem re-renderizar o input ativo.
- Regressão: saves por `change` (derivados) continuam recalculando (suite existente verde).
- Smoke manual (`/run`): digitar em "Nome"/"Notas" salva sozinho após ~0,6 s sem perder o cursor.

---

## Sprint F — Cálculos faltantes

### T5.2 — Derivar ataques, cap de Des da armadura, deslocamento e penalidades

**Status:** ⬜ não iniciada
**Tipo:** domínio/cálculo
**Pré-requisitos:** nenhum (estende `calculations.py` + `_recalculate_stats`)
**Agente:** ver alocação

#### Contexto
Hoje só **Agarrar** é derivado entre os ataques; `_recalculate_stats` não calcula ataque corpo-a-corpo/à distância, ignora o `MaxDex` da armadura na CA (usa o mod de Des cheio), não aplica penalidade de armadura nem ajusta deslocamento por carga/armadura.

#### Objetivo
Adicionar funções puras em `calculations.py` e ligá-las no `_recalculate_stats`:
1. `compute_attack_bonus(*, bba, ability_mod, size_mod, misc)` → corpo-a-corpo (Força) e à distância (Destreza).
2. `cap_dex_to_armor(dex_mod, max_dex)` → limita o mod de Des aplicado à CA pelo `MaxDex` da armadura equipada (parse via `parse_bonus`).
3. `armor_check_penalty(...)` → soma penalidades de armadura/escudo e aplica às perícias afetadas por armadura (Força/Destreza).
4. `speed_for_load(base_speed, load_category, armor_speed)` → deslocamento ajustado por carga média/pesada e armadura.

#### Entregáveis
- `character/calculations.py` com as novas funções puras.
- `character/views.py::_recalculate_stats` chamando-as e persistindo (`update_fields`).
- `docs/character-domain.md` atualizado.

#### Testes
- `character/tests.py::PureCombatCalcsTest` (`SimpleTestCase`): cada função pura com casos zero/positivo/negativo.
- `RecalcAppliesArmorCapTest`: armadura com `MaxDex 2` + Des +4 → CA usa +2.
- Suite existente verde.

---

### T5.3 — Conjuração: Ca (DC) de magia e magias bônus por atributo

**Status:** ⬜ não iniciada
**Tipo:** domínio/cálculo (integra SDR `class_table`)
**Pré-requisitos:** nenhum
**Agente:** ver alocação

#### Contexto
`CharacterSpellSave.SpellSaveDC` e `BonusSpells` existem como campos mas ficam em `0` (manuais). A CD de uma magia é `10 + nível da magia + mod do atributo-chave`; magias bônus saem de uma tabela por atributo.

#### Objetivo
1. `compute_spell_save_dc(spell_level, casting_ability_mod)` puro.
2. `bonus_spells_for_ability(ability_score, spell_level)` puro (tabela padrão 3.5).
3. Ligar no contexto de conjuração (`spellcasting.py`) e/ou `_recalculate_stats`, persistindo por nível.

#### Entregáveis
- `character/calculations.py` + `character/spellcasting.py` editados.

#### Testes
- `character/tests.py::SpellDcAndBonusTest` (`SimpleTestCase`): CD e bônus para FOR/DES baixos e altos.

---

## Sprint G — Persistência faltante

### T5.4 — Auditoria + persistência de estado de jogo (HP atual, dano, condições)

**Status:** ⬜ não iniciada
**Tipo:** modelo/persistência
**Pré-requisitos:** nenhum
**Agente:** ver alocação

#### Contexto
`CharacterStatus.TotalHitPoints` guarda o total, mas **não há PV atual/temporário nem registro de dano** — o estado de combate se perde. Pode haver outros campos hoje só derivados/estáticos que deveriam persistir.

#### Objetivo
1. **Passo 1 (auditoria):** varrer models + templates editáveis e listar o que é editável na UI mas não persiste, e o que deveria ser rastreado e não é. Registrar em `docs/known-issues.md`.
2. Adicionar campos `CurrentHitPoints`, `TemporaryHitPoints` (e opcional `NonlethalDamage`) em `CharacterStatus` + migration.
3. UI inline (HTMX) para PV atual/temporário com clamp (`0 ≤ atual ≤ total`).
4. (Opcional MVP) seção simples de **condições/efeitos** persistida.

#### Entregáveis
- Auditoria em `docs/known-issues.md`.
- `models.py` + migration + view/partial de PV.

#### Testes
- `character/tests.py::HitPointTrackingTest`: POST altera PV atual; clamp respeitado; persiste no GET.

---

# Critério de "MVP de jogo pronto" (Fase 5)

- [ ] Ficha salva enquanto se digita (texto), sem perder foco; derivados recalculam no blur (T5.1).
- [ ] Ataque corpo-a-corpo/à distância, cap de Des por armadura, penalidade de armadura e deslocamento por carga derivados automaticamente (T5.2).
- [ ] CD de magia e magias bônus calculados (T5.3).
- [ ] PV atual/temporário (e dano) persistidos e editáveis (T5.4).
- [ ] Suite de testes verde com a nova cobertura.

---

# Matriz de paralelismo

| Fase | Tasks paralelas                                                                   |
|------|-----------------------------------------------------------------------------------|
| 0    | T0.1, T0.2 (independentes)                                                        |
| 1    | T1.1 / T1.2 / T1.3 / T1.4 / T1.5 / T1.6 / T1.7* / T1.8 / T1.9 / T1.10 / T1.11 / T1.12 |
| 2    | T2.1 / T2.2 / T2.3                                                                |
| 3    | T3.1 → T3.2                                                                       |
| 4    | T4.1 / T4.2 / T4.3 → T4.4 / T4.5 / T4.6 → T4.7, T4.8                              |

`*` T1.7 depende de T1.6. T4.4 depende de T4.3 (mesmo arquivo). T4.7 e T4.8 dependem de T4.6 (model criado).

# Alocação final por agente

Os prompts prontos para colar em cada agente estão em [`docs/agents-prompts.md`](docs/agents-prompts.md).

| Agente            | Tasks Fases 0–3                                                         | Tasks Fase 4                          |
|-------------------|-------------------------------------------------------------------------|---------------------------------------|
| **Sonnet** (#1)   | T0.2, T1.1, T1.2, T1.4, T1.6, T1.7, T1.8, T2.1, T2.2, T3.1, T3.2        | T4.1, T4.2, T4.3, T4.4                |
| **Codex** (#2)    | T0.1, T1.3, T1.5, T1.9, T1.10, T1.11, T1.12, T2.3                       | T4.5, T4.6, T4.7, T4.8                |

Justificativa Fase 4:
- **T4.1–T4.4** são UI/CSS/template; T4.3 e T4.4 mexem no mesmo arquivo (`companions.html`) → mesmo dono (Sonnet) para evitar conflito.
- **T4.5** (Livro de Magias) é feature com nova view/template e edição HTMX em série de partials → Codex (trilha de domínio + HTMX, já cobre T1.9 e T1.10/T1.11).
- **T4.6–T4.8** dependem de novo model + integração SDR; cadeia coerente com T2.3/T1.5 → Codex.

Justificativa das mudanças vs. campo "Agente" das tasks individuais:

- **T1.1, T1.2, T1.4** todas editam `settings.py` → Sonnet é dono único para evitar conflito de merge.
- **T1.6 + T1.7** editam a mesma função `_recalculate_stats` → mesmo dono (Sonnet).
- **T2.1** casa com T2.2 (trilha de infra/deploy) → Sonnet.
- **T2.3** depende de toda a trilha C (companions, reputação, dispatcher) que é do Codex → Codex.

# Critério de "pronto para colocar online"

Antes de declarar Fase 2 concluída, exigir:
- [x] `python manage.py check --deploy` zero warnings.
- [x] Suite de testes 100% verde.
- [x] `docker compose -f docker-compose.prod.yaml up` sobe e responde em `/healthz`.
- [x] Login funciona, criar ficha funciona, edição inline persiste, todas as 4 páginas (ficha, companions, recursos, reputação) abrem 200.
- [x] Sem credenciais hardcoded em settings ou seeds rodando em prod.
- [x] Static files servidos via WhiteNoise (verificar header `Cache-Control` em GET de CSS/JS).
- [x] `requirements.txt` em UTF-8 sem dependências mortas.

# Critério de "Fase 4 concluída" (UX/Feature)

- [x] Largura unificada 1280px nas 3 sub-páginas (T4.1).
- [x] Aba/menu mostra "Aliados" em toda a navegação (T4.2).
- [x] Página de Aliados com nome em destaque, layout empilhado e accordion (T4.3 + T4.4).
- [x] `/character/<pk>/spellbook/` no ar; `character_spells.html` enxugado (T4.5).
- [ ] Grid de invocações renderiza, fixar (★) funciona, autocomplete SRD preenche estatísticas (T4.6 + T4.7 + T4.8).
- [ ] Suite de testes continua verde com a nova cobertura.
