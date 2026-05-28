# D&D 3.5 eSheet

Ficha virtual de D&D 3.5 feita em Django. A ideia do produto e manter a experiencia proxima da ficha em papel, mas com automacao de app: o jogador edita os valores que sao fonte de verdade e o sistema deve persistir os valores derivados recalculados.

## Stack

- Python 3.12
- Django 4.2
- SQLite
- Docker Compose
- django-htmx
- django-crispy-forms com bootstrap5
- django-filter

O codigo Django fica em `dd3esheet/`. Os comandos abaixo assumem que voce esta na raiz do app Django:

```powershell
cd dd3esheet
```

## Rodando o Ambiente

Subir o container web:

```powershell
docker compose up --build
```

Ou em background:

```powershell
docker compose up -d
```

O app fica em:

- App: `http://localhost:8000/`
- Admin: `http://localhost:8000/admin/`

Entrar no container:

```powershell
docker compose exec web bash
```

Rodar comandos Django de fora do container:

```powershell
docker compose exec web python manage.py check
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py test
```

Rodar comandos Django de dentro do container:

```bash
python manage.py check
python manage.py migrate
python manage.py createsuperuser
python manage.py test
```

Observacao: o `command` do servico `web` roda `migrate` -> `seed` -> `runserver` a cada `up`, entao o banco ja sobe migrado e com a conta admin (`jarza` / `P@ssw0rd`) e as fichas de exemplo prontas (ver "Seeds"). O `seed` e idempotente, entao subir varias vezes e seguro.

## Estrutura do Projeto

Apps principais:

- `home/`: pagina inicial em `/`.
- `character/`: fichas dos personagens em `/character/`.
- `sdr/`: dados de referencia do SRD D&D 3.5 em `/sdr/`.

Arquivos importantes:

- `dd3esheet/manage.py`: entrada dos comandos Django.
- `dd3esheet/dd3esheet/settings.py`: configuracao Django, apps instalados e bancos.
- `dd3esheet/dd3esheet/urls.py`: inclui as rotas de `home`, `character` e `sdr`.
- `dd3esheet/templates/`: templates compartilhados.
- `dd3esheet/static/`: arquivos estaticos locais.

## Bancos de Dados

O projeto usa dois bancos SQLite configurados em `settings.py`.

### default

Arquivo: `dd3esheet/db.sqlite3`

Usado para:

- Django auth.
- App `home`.
- App `character`.

O comando normal de migracao atua neste banco:

```bash
python manage.py migrate
```

### sdr

Arquivo: `dd3esheet/dnd35.sqlite3`

Usado para os dados de referencia do D&D 3.5. Os models em `sdr/models.py` usam `managed = False` e apontam para tabelas existentes, como `spell`, `monster`, `feat`, `equipment`, `skill`, etc.

Toda query SDR precisa usar explicitamente o banco `sdr`:

```python
SDR_Spell.objects.using("sdr").order_by("name")
```

Sem `.using("sdr")`, a query tenta bater no banco `default` e pode retornar vazio ou falhar conforme a tabela.

Para regenerar models a partir do banco SDR:

```bash
python manage.py inspectdb --database sdr
```

Nao rode migracoes tentando criar ou alterar as tabelas do banco `sdr`. Ele e uma base de referencia externa/read-only.

## Fluxo da Ficha

`Character` e o modelo principal da ficha e possui `ForeignKey(User)`. Os demais dados da ficha ficam em modelos irmaos ligados por `OneToOneField` ou `ForeignKey`, por exemplo:

- `CharacterStats`
- `CharacterStatus`
- `CharacterSavingThrows`
- `CharacterAttackModifiers`
- `CharacterSkill`
- `CharacterWeapon`
- `CharacterArmor`
- `CharacterShield`
- `CharacterFeat`
- `CharacterSpell`
- `CharacterMoney`

Ao criar uma ficha em `character.views.createCharacter`, o app cria o `Character` e chama `character.services._bootstrap_character_siblings`, que inicializa os modelos `OneToOne` (stats, status, saves, ataque, dinheiro, conjuracao, etc.) e a lista base de 35 skills.

Convencao importante: os models do app `character` usam nomes em PascalCase, como `Name`, `Strength`, `ACTotal` e `UpdatedAt`. Mantenha esse padrao ao estender modelos existentes.

## HTMX e Partials

A edicao da ficha deve evitar reload de pagina. O padrao esperado e:

1. Renderizar o form com `crispy-forms` dentro de um partial em `character/templates/character/partials/`.
2. Configurar o form com `hx-post`, `hx-target` e `hx-trigger`.
3. A view identificar `request.htmx` e `request.htmx.target`.
4. Salvar o form, recalcular derivados quando houver, e devolver somente o partial atualizado.

A ficha inteira ja e editavel inline. A view `character.views.character(request, pk)` funciona como um dispatcher unico: um encadeamento de `if request.htmx.target == '...'` cobre identidade, descricao, stats, status, CA/armadura, saves, ataque/grapple, skills, armas, equipamento, itens, dinheiro, talentos, especiais e magias. Apenas identidade/descricao/stats usam `ModelForm` crispy; as demais secoes leem o POST direto via helpers (`_update_fields_from_post`, `_save_repeating_slots`, `_ordered_slots`) e recalculam derivados com `_recalculate_stats`.

Exemplo do padrao nos forms:

```python
self.helper.attrs = {
    "hx-post": reverse_lazy("character:character", kwargs={"pk": self.instance.id}),
    "hx-target": "#characterStatsForm",
    "hx-trigger": "change",
}
```

Ao adicionar uma nova area editavel da ficha, crie um partial com target unico e trate esse target na view.

## Calculos Derivados

Valores derivados devem ser calculados no backend e persistidos, nao digitados manualmente nem calculados no template.

Exemplos de regras esperadas:

- Modificador de atributo: `(stat - 10) // 2`.
- AC total: `10 + armor + shield + dex_mod + size_mod + natural_armor + deflection + misc`.
- Saves: `base + ability_mod + magic + misc + temporary`.
- Skill total: `ranks + ability_mod + misc`, com tratamento para skills treinadas quando aplicavel.

Onde os calculos vivem hoje:

- O recalculo dos derivados da ficha esta em `character.views._recalculate_stats(character)` (mods, AC, saves, iniciativa, grapple — muta os siblings e salva num so fluxo).
- A matematica de conjuracao esta em `character/spellcasting.py` como funcoes puras (`spell_save_dc`, `bonus_spells_for_level`, `ability_modifier`, `numeric_slot_count`).

Recomendacao para novas implementacoes:

- Prefira funcoes puras e testaveis; chame-as no fluxo de save (view ou servico) depois de gravar a fonte de verdade.
- Persista os campos derivados no mesmo fluxo que salvou a fonte de verdade.
- Cubra as funcoes com testes unitarios usando `SimpleTestCase`.

## Testes

Comandos:

```bash
python manage.py test
python manage.py test character
python manage.py test sdr
python manage.py test home
```

De fora do container:

```powershell
docker compose exec web python manage.py test
```

Estado atual: `character/tests.py` ja tem uma suite ampla (criacao de ficha, permissoes de dono/404, edicao HTMX por target, calculos de conjuracao, render de dominios/slots, e queries SDR via `.using("sdr")`). Testes que tocam o SDR usam `TransactionTestCase` com `databases = ('default', 'sdr')` e criam as tabelas de referencia no banco de teste via cursor cru (ver `setup_sdr_class_table`). Para novas features e correcoes, estenda essa suite (escreva o teste antes ou junto da implementacao).

Prioridades de teste:

- Funcoes puras de calculo derivado.
- Views HTMX retornando o partial correto.
- Recalculo e persistencia apos salvar forms.
- Permissoes de acesso a ficha.
- Queries do SDR usando `.using("sdr")` quando aplicavel.

## Seeds (Dados de Exemplo)

`character/seeds.py` popula o banco com dados de exemplo prontos para uso e teste:

- Uma conta admin (superusuario): `jarza` / `P@ssw0rd`.
- Uma ficha completa de Guerreiro humano nivel 5 (`Borin Escudoférreo`).
- Uma ficha completa de Mago elfo nivel 8 especialista em Evocacao (`Maelis Vorn`), com livro de magias e slots preparados.

Roda automaticamente no `docker compose up` (o `command` do servico `web` faz `migrate` -> `seed` -> `runserver`). Para rodar manualmente (afeta o banco `default`, que e `.gitignore`d):

```bash
python manage.py seed
```

```powershell
docker compose exec web python manage.py seed
```

Os mesmos builders sao importaveis e usados pelos testes (`character.tests.SeedTests`), garantindo que o app e os testes compartilhem os mesmos dados:

```python
from character.seeds import seed_all, seed_admin, seed_fighter, seed_wizard
```

Detalhes:

- E idempotente: rodar de novo recria as fichas de exemplo e redefine a senha do admin.
- Os derivados (mods, CA, saves, grapple) sao calculados via `views._recalculate_stats`, o mesmo recalculo da edicao inline — nao sao numeros chumbados a mao.
- A conta admin usa credenciais fixas e conhecidas: use apenas em ambiente local/de teste.

## Desenvolvimento de Features

Ao adicionar campos da ficha:

- Prefira um novo model relacionado a `Character` quando o dado pertencer a uma nova area da ficha.
- Evite inflar `Character` com colunas de secoes especificas.
- Adicione `ModelForm` proprio quando a area for editavel.
- Adicione partial HTMX proprio.
- Recalcule derivados no backend.
- Adicione ou atualize testes.

Ao trabalhar no app `sdr`:

- Trate os models como read-only.
- Use `django-filter` para filtros de listagem.
- Sempre use `.using("sdr")` nas queries.
- Nao altere `sdr/models.py` manualmente se a fonte real for o banco; prefira `inspectdb --database sdr`.

## Lacunas Conhecidas

Ja resolvido (estava aqui antes): todas as views exigem login e usam `get_object_or_404(Character, pk=pk, User=request.user)` (nao-dono recebe 404); `home` filtra por usuario; a ficha inteira ja e editavel via HTMX; e ha suite de testes.

Pontos importantes para proximas melhorias:

- Compartilhamento entre usuarios (`CharacterShare`) ainda nao implementado — hoje so o dono ve/edita.
- O HTMX nao esta carregado em nenhum template: `static/htmx.min.js` esta versionado e o `django_htmx` esta instalado (app + middleware em `settings.py`), mas nem `templates/main.html` nem `character.html` incluem o `<script>` do HTMX. A edicao inline so funciona apos wirar esse script.
- As secoes que leem o POST direto (tudo menos identidade/descricao/stats) nao passam por validacao de `ModelForm`; validacao explicita so existe na identidade (ex: alignment).

## Cuidados

- `requirements.txt` esta em UTF-16 LE com BOM. Nao regrave automaticamente como UTF-8 sem confirmar, porque isso pode quebrar o build ou o fluxo esperado de instalacao.
- O arquivo `dnd35.sqlite3` e parte essencial do app SDR. Evite altera-lo manualmente durante desenvolvimento normal.
- `static/htmx.min.js` esta versionado e o `django_htmx` esta ativo, mas nenhum template inclui o `<script>` do HTMX hoje (ver Lacunas Conhecidas).
- Antes de grandes alteracoes, rode:

```bash
python manage.py check
python manage.py test
```
