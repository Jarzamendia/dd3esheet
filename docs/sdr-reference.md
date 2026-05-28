# SRD / banco de referencia

## Objetivo

O app `sdr` expoe dados de referencia D&D 3.5.

Ele e usado para consulta e tambem alimenta partes da ficha, como escolhas de classe e tabelas de conjuracao.

## Banco

Arquivo:

```text
dd3esheet/dnd35.sqlite3
```

Alias Django:

```python
"sdr"
```

## Models

Os models ficam em:

```text
dd3esheet/sdr/models.py
```

Eles usam `managed = False` e tabelas explicitas.

Regra:

```python
SDR_Spell.objects.using("sdr")
```

Sempre use `.using("sdr")`.

Sem isso, o Django tenta consultar o banco `default`.

## Views e filtros

`sdr/views.py` cria listagens e detalhes.

Listagens usam `django-filter`:

- `SpellsFilter`
- `MonsterFilter`
- `ClassFilter`
- `DomainFilter`
- `EquipmentFilter`
- `FeatFilter`
- `ItemFilter`
- `PowerFilter`
- `SkillFilter`

Os filtros tambem definem querysets padrao com `.using("sdr")`.

## Categorias expostas

- Spells.
- Monsters.
- Classes.
- Domains.
- Equipment.
- Feats.
- Items.
- Powers.
- Skills.

## Uso pela ficha

`character.services.sdr_class_choices()` busca classes no banco `sdr` para o select de classe.

`character.spellcasting` usa:

- `SDR_ClassTable` para slots por nivel;
- `SDR_Domain` para magias de dominio.

## Regenerar models

Se o schema do banco SRD mudar, gere models a partir do banco:

```bash
python manage.py inspectdb --database sdr
```

Nao escreva os fields manualmente sem comparar com o schema real.

## Testes

Testes que precisam tocar `sdr` devem declarar:

```python
databases = ("default", "sdr")
```

Em `character/tests.py`, o helper `setup_sdr_class_table()` cria tabelas minimas no banco de teste `sdr` para exercitar classes, class table e dominios.

