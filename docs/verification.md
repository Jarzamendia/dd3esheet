# Verificacao atual

Ultima revisao: 2026-05-28.

## Comandos executados

Todos executados a partir de `dd3esheet/`.

```powershell
docker compose run --rm web python manage.py check
```

Resultado:

```text
System check identified no issues (0 silenced).
```

```powershell
docker compose run --rm web python manage.py makemigrations --check --dry-run
```

Resultado:

```text
No changes detected
```

```powershell
docker compose run --rm web python manage.py test character
```

Resultado:

```text
Found 39 test(s).
System check identified no issues (0 silenced).
Ran 39 tests in 4.772s
OK
```

## Itens conferidos em codigo

- `docker-compose.yaml` roda `migrate`, `seed` e `runserver`.
- `character/management/commands/seed.py` chama `character.seeds.seed_all`.
- `character/seeds.py` cria admin local e duas fichas completas.
- `settings.py` declara bancos `default` e `sdr`.
- `sdr/views.py` e `sdr/filters.py` usam `.using("sdr")`.
- `character/views.py` centraliza o dispatcher HTMX da ficha.
- `character/services.py` cria os siblings iniciais da ficha.
- `static/htmx.min.js` existe.
- `templates/main.html` ainda nao inclui o script HTMX.

