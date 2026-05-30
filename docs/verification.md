# Verificacao atual

Ultima revisao: 2026-05-30.

## Estrutura atual do codigo

- App `character` agora possui 4 migrations: `0001_initial`, `0002_characterprogress`, `0003_daily_resources`, `0004_skill_specialization_and_key_ability`.
- `character/calculations.py` concentra funcoes puras (modificador de atributo, totais de pericia, limites de carga, parsing de bonus, recursos diarios).
- Novos models: `CharacterProgress`, `CharacterDailyNotes`, `CharacterDailyResource`, `CharacterActiveEffect`.
- Novas rotas: `/character/<pk>/companions`, `/character/<pk>/daily-resources`, `/character/<pk>/reputation`.
- Novos templates de pagina: `companions.html`, `daily_resources.html`, `reputation.html`, partial `character_progress.html`.

## Comandos sugeridos

Todos executados a partir de `dd3esheet/`.

```powershell
docker compose run --rm web python manage.py check
docker compose run --rm web python manage.py makemigrations --check --dry-run
docker compose run --rm web python manage.py test character
```

A suite de `character` esta em ~67 testes (ver `character/tests.py`).

## Itens conferidos em codigo

- `docker-compose.yaml` roda `migrate`, `seed` e `runserver`.
- `character/management/commands/seed.py` chama `character.seeds.seed_all`.
- `character/seeds.py` cria admin local e duas fichas completas.
- `settings.py` declara bancos `default` e `sdr`.
- `sdr/views.py` e `sdr/filters.py` usam `.using("sdr")`.
- `character/views.py` centraliza o dispatcher HTMX da ficha e expoe as paginas extras (companions, daily-resources, reputation).
- `character/services.py` cria os siblings iniciais da ficha (incluindo `CharacterProgress` e `CharacterDailyNotes`) e gerencia slots expansiveis de pericia.
- `character/calculations.py` reune as regras puras de calculo derivado.
- `static/htmx.min.js` existe.
- `templates/main.html` ainda nao inclui o script HTMX (ver [Lacunas conhecidas](known-issues.md)).
