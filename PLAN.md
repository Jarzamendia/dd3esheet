# PLAN.md — Roadmap para ambiente de testes online

Este plano divide o trabalho em **tasks autocontidas**, cada uma executável por um agente (Sonnet ou Codex) sem precisar de contexto extra além do que está descrito. Tasks com o mesmo `Fase` podem rodar em paralelo entre si.

## Objetivos finais

1. App rodando em servidor público (ambiente de testes), acessível por URL.
2. Configurações de segurança aplicadas (Django checklist de produção).
3. Correções de performance (queries, recalculo, render).
4. Todos os componentes da ficha (edição inline, páginas extras, toggles) funcionando ponta a ponta.

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

# Matriz de paralelismo

| Fase | Tasks paralelas                                                                   |
|------|-----------------------------------------------------------------------------------|
| 0    | T0.1, T0.2 (independentes)                                                        |
| 1    | T1.1 / T1.2 / T1.3 / T1.4 / T1.5 / T1.6 / T1.7* / T1.8 / T1.9 / T1.10 / T1.11 / T1.12 |
| 2    | T2.1 / T2.2 / T2.3                                                                |
| 3    | T3.1 → T3.2                                                                       |

`*` T1.7 depende de T1.6.

# Alocação final por agente

Os prompts prontos para colar em cada agente estão em [`docs/agents-prompts.md`](docs/agents-prompts.md).

| Agente            | Tasks                                                                   |
|-------------------|-------------------------------------------------------------------------|
| **Sonnet** (#1)   | T0.2, T1.1, T1.2, T1.4, T1.6, T1.7, T1.8, T2.1, T2.2, T3.1, T3.2        |
| **Codex** (#2)    | T0.1, T1.3, T1.5, T1.9, T1.10, T1.11, T1.12, T2.3                       |

Justificativa das mudanças vs. campo "Agente" das tasks individuais:

- **T1.1, T1.2, T1.4** todas editam `settings.py` → Sonnet é dono único para evitar conflito de merge.
- **T1.6 + T1.7** editam a mesma função `_recalculate_stats` → mesmo dono (Sonnet).
- **T2.1** casa com T2.2 (trilha de infra/deploy) → Sonnet.
- **T2.3** depende de toda a trilha C (companions, reputação, dispatcher) que é do Codex → Codex.

# Critério de "pronto para colocar online"

Antes de declarar Fase 2 concluída, exigir:
- [ ] `python manage.py check --deploy` zero warnings.
- [ ] Suite de testes 100% verde.
- [ ] `docker compose -f docker-compose.prod.yaml up` sobe e responde em `/healthz`.
- [ ] Login funciona, criar ficha funciona, edição inline persiste, todas as 4 páginas (ficha, companions, recursos, reputação) abrem 200.
- [ ] Sem credenciais hardcoded em settings ou seeds rodando em prod.
- [ ] Static files servidos via WhiteNoise (verificar header `Cache-Control` em GET de CSS/JS).
- [ ] `requirements.txt` em UTF-8 sem dependências mortas.
