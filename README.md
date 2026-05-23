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

Observacao: versoes recentes do Docker Compose exibem um aviso dizendo que `version: '3.8'` no `docker-compose.yaml` e obsoleto. Isso nao impede o app de subir.

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

Ao criar uma ficha em `character.views.createCharacter`, o app cria o `Character` e inicializa varios modelos relacionados, incluindo a lista base de skills.

Convencao importante: os models do app `character` usam nomes em PascalCase, como `Name`, `Strength`, `ACTotal` e `UpdatedAt`. Mantenha esse padrao ao estender modelos existentes.

## HTMX e Partials

A edicao da ficha deve evitar reload de pagina. O padrao esperado e:

1. Renderizar o form com `crispy-forms` dentro de um partial em `character/templates/character/partials/`.
2. Configurar o form com `hx-post`, `hx-target` e `hx-trigger`.
3. A view identificar `request.htmx` e `request.htmx.target`.
4. Salvar o form, recalcular derivados quando houver, e devolver somente o partial atualizado.

O fluxo atual ja existe para:

- `characterForm`, renderizado por `character/partials/character_description.html`.
- `characterStatsForm`, renderizado por `character/partials/character_stats.html`.

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

Recomendacao para novas implementacoes:

- Coloque funcoes puras em `character/calculations.py`.
- Chame essas funcoes na view ou em um servico de aplicacao depois de `form.save()`.
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

Estado atual observado: `python manage.py test` encontra 0 testes. Para novas features e correcoes, adicione testes antes ou junto da implementacao.

Prioridades de teste:

- Funcoes puras de calculo derivado.
- Views HTMX retornando o partial correto.
- Recalculo e persistencia apos salvar forms.
- Permissoes de acesso a ficha.
- Queries do SDR usando `.using("sdr")` quando aplicavel.

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

Pontos importantes para proximas melhorias:

- A listagem de personagens em `character.views.home` usa `Character.objects.all()`; para multiplos usuarios, deve filtrar pelo usuario logado e futuramente por compartilhamentos.
- As views de detalhe, edicao e exclusao usam `Character.objects.get(id=pk)` sem checagem de dono; o comportamento desejado e retornar 404 para quem nao tem acesso.
- Os calculos derivados ainda nao estao centralizados em `character/calculations.py`.
- Os partials HTMX atuais cobrem apenas descricao/dados principais e stats.
- Os arquivos `tests.py` existem, mas ainda nao ha testes implementados.

## Cuidados

- `requirements.txt` esta em UTF-16 LE com BOM. Nao regrave automaticamente como UTF-8 sem confirmar, porque isso pode quebrar o build ou o fluxo esperado de instalacao.
- O arquivo `dnd35.sqlite3` e parte essencial do app SDR. Evite altera-lo manualmente durante desenvolvimento normal.
- O template principal carrega HTMX via CDN em `templates/main.html`, apesar de tambem existir `static/htmx.min.js`.
- Antes de grandes alteracoes, rode:

```bash
python manage.py check
python manage.py test
```
