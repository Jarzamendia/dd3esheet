# AGENTS.md

Guia para agentes de codificação (Claude Code, Codex, Copilot, etc.) trabalhando neste repositório.

## Project

D&D 3.5 character sheet web app. Django 4.2 + django-htmx + Bootstrap 5 + django-filter. Python 3.12. Source lives under `dd3esheet/` (project root contains README and TODO; the Django project itself is in the `dd3esheet/` subdirectory).

## Running

Everything runs in Docker. From the `dd3esheet/` directory:

```
docker-compose up                    # starts web on localhost:8000
docker-compose exec web bash         # shell into the container
```

Inside the container (the commands the README assumes):

```
python manage.py makemigrations
python manage.py migrate             # ONLY migrates the 'default' DB (see Databases)
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
python manage.py test <app>          # e.g. python manage.py test character
```

Admin is at `localhost:8000/admin`.

## Architecture

Three Django apps, mounted in `dd3esheet/urls.py`:

- `home/` — landing page (`/`).
- `character/` — user-owned character sheets (`/character/`). All character data lives here: `Character` plus a constellation of `OneToOneField`/`ForeignKey` siblings (`CharacterStats`, `CharacterStatus`, `CharacterSavingThrows`, `CharacterAttackModifiers`, `CharacterSkill`, `CharacterWeapon`, `CharacterArmor`, `CharacterShield`, `CharacterFeat`, `CharacterSpell`, `CharacterMoney`, etc.). New character-related fields generally mean a new sibling model keyed back to `Character`, not adding columns to `Character` itself.
- `sdr/` — read-only D&D 3.5 SRD reference data (`/sdr/`): spells, monsters, classes, feats, equipment, items, powers, skills, domains. Browsing and filtering only.

### Two databases

`settings.py` defines two SQLite DBs:

- `default` (`db.sqlite3`) — Django auth + everything in the `character` and `home` apps. This is what `migrate` writes to.
- `sdr` (`dnd35.sqlite3`) — the SRD reference data, **pre-existing and externally maintained**. All `sdr/models.py` models use `managed = False` with explicit `db_table = '...'`. Never run migrations against this database, and never edit `sdr/` models without matching the existing schema.

Because there is no default router, **every SDR query must use `.using('sdr')`** (see `sdr/views.py` for the pattern: `SDR_Spell.objects.using('sdr')...`). Forgetting this hits `default` and silently returns nothing.

The README documents regenerating `sdr/models.py` from the SRD DB via `python manage.py inspectdb --database sdr` — use this rather than hand-writing model fields if the SRD schema changes.

### Templates

`TEMPLATES.DIRS` includes the top-level `templates/` directory in addition to per-app `templates/`. Shared base templates live at the top level; app-specific templates under `<app>/templates/<app>/`.

### Filtering pattern

List views use `django-filter` `FilterSet` classes (see `sdr/filters.py`) with `icontains` lookups. The view passes the bound filter into the template; templates render `{{ filtered_X.form }}` plus iterate `filtered_X.qs`.

## Conventions

- Field names on `character` models use PascalCase (`Name`, `Strength`, `ACTotal`) — unusual for Django, but consistent across the app. Match the existing style when extending these models.
- `requirements.txt` is UTF-16 encoded (BOM + null bytes between chars). Don't rewrite it as UTF-8 without confirming — `pip install` handles it as-is inside the container, and tooling that re-encodes it has broken the Docker build before.
