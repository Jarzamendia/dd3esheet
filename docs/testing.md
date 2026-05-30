# Testes e qualidade

## Comandos

Dentro do container:

```bash
python manage.py check
python manage.py test
python manage.py test character
python manage.py test home
python manage.py test sdr
python manage.py makemigrations --check --dry-run
```

De fora do container:

```powershell
docker compose run --rm web python manage.py check
docker compose run --rm web python manage.py test character
docker compose run --rm web python manage.py makemigrations --check --dry-run
```

## Estado esperado

Antes de entregar mudancas de codigo:

- `python manage.py check` sem erros;
- testes relevantes passando;
- `makemigrations --check --dry-run` sem migrations pendentes.

## Onde ficam os testes

- `character/tests.py`: principal suite do projeto (atualmente 67 testes).
- `home/tests.py`: landing e redirect.
- `sdr/tests.py`: ainda minimo.

## O que testar

Obrigatorio para mudancas nao triviais:

- calculos derivados;
- views HTMX;
- permissoes;
- saves de forms/partials;
- queries SDR com `.using("sdr")`;
- seeds quando alterar dados de exemplo.

## Padroes atuais

`character/tests.py` cobre:

- criacao de ficha;
- bootstrap dos models irmaos;
- acesso por dono e 404 para nao dono;
- identidade via HTMX;
- render da ficha;
- layout de armas, equipamentos e paginas;
- calculos de conjuracao;
- render de dominios e slots;
- toggle de slot de magia;
- conjuracao custom para qualquer classe;
- choices de SDR;
- validacoes de constantes.

## Testes com SDR

Use `TransactionTestCase` quando precisar tocar os dois bancos:

```python
class MyTests(TransactionTestCase):
    databases = ("default", "sdr")
```

Crie tabelas minimas no banco de teste `sdr` se o teste depender de dados especificos.

## Migracoes

O app `character` tem 4 migrations versionadas:

- `0001_initial`: base consolidada da ficha.
- `0002_characterprogress`: `CharacterProgress` (XP e nome da campanha).
- `0003_daily_resources`: `CharacterDailyNotes`, `CharacterDailyResource`, `CharacterActiveEffect`.
- `0004_skill_specialization_and_key_ability`: adiciona `SkillSpecialization` a `CharacterSkill` e amplia `SkillAbility`.

Ao adicionar campos:

1. altere model;
2. rode `makemigrations`;
3. revise a migration;
4. rode testes;
5. nao edite o banco `sdr` via migrations.

