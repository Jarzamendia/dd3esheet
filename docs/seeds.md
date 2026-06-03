# Seeds e dados de exemplo

## Arquivos

- `character/seeds.py`: builders reutilizaveis.
- `character/management/commands/seed.py`: comando `python manage.py seed`.
- `sprites/seeds.py`: registros e bindings de imagens usados pela ficha, iniciativa e exemplos, sem criar arquivos.
- `sprites/management/commands/seed_sprites.py`: comando `python manage.py seed_sprites`.
- `sprites/management/commands/seed_sprite_library.py`: comando `python manage.py seed_sprite_library`, cria/atualiza os 496 placeholders do manifesto.

## Quando roda

O seed roda automaticamente no `docker compose up`, porque o comando do servico `web` e:

```bash
python manage.py migrate &&
python manage.py seed &&
python manage.py runserver 0.0.0.0:8000
```

Tambem pode ser rodado manualmente:

```bash
python manage.py seed
```

Ou de fora do container:

```powershell
docker compose exec web python manage.py seed
docker compose run --rm web python manage.py seed
```

## Dados criados

Admin local:

- usuario: `jarza`
- senha: `P@ssw0rd`
- email: `jarza@example.com`

Fichas:

- `Borin Escudoferreo`: guerreiro humano nivel 5.
- `Maelis Vorn`: maga elfa nivel 8, especialista em Evocacao.
- `Thalara Verdefolha`: druida humana nivel 9, com companheiro animal, invocacoes ativas, recursos diarios, buffs e reputacao.
- `Kael Rastrolongo`: ranger humano nivel 6, com companheiro animal, recursos diarios, trilhas de reputacao e magias preparadas.

Sprites:

- classes principais usadas nos exemplos (`Fighter`, `Wizard`, `Druid`, `Ranger`);
- tipos de combatente da iniciativa (`player`, `npc`, `enemy`);
- monstros usados em invocacoes/companheiros de exemplo (`Brown Bear`, `Unicorn`, `Wolf`).
- 496 placeholders publicos da Sprite Library, com `Slug` igual ao id snake_case do manifesto e `DefaultGridWidth/Height` derivados do footprint.

O seed de sprites nao gera imagens. Ele prepara os registros, bindings e placeholders; as imagens reais devem ser enviadas depois por upload/admin.

Observacao: no codigo, alguns textos possuem caracteres acentuados. Ao editar arquivos, preserve o encoding e evite regravar arquivos grandes sem necessidade.

## Idempotencia

`seed_all()`:

1. cria/repara o admin;
2. apaga fichas de exemplo anteriores do mesmo dono/nome;
3. recria as fichas completas;
4. cria ou atualiza os sprites e bindings base;
5. cria ou atualiza os 496 placeholders da Sprite Library.

Isso torna seguro rodar o seed varias vezes em desenvolvimento.

## Builders disponiveis

```python
from character.seeds import seed_all, seed_admin
from character.seeds import seed_fighter, seed_wizard, seed_druid, seed_ranger
from character.seeds import ADMIN_USERNAME, ADMIN_PASSWORD
from character.seeds import FIGHTER_NAME, WIZARD_NAME, DRUID_NAME, RANGER_NAME
from sprites.seeds import seed_sprite_library, seed_sprites
```

## Como os derivados sao calculados

Os builders setam fontes de verdade e chamam:

```python
from character.views import _recalculate_stats
```

Assim, mods, CA, saves e agarrar usam o mesmo calculo da edicao inline. `_recalculate_stats` por sua vez usa funcoes puras de `character/calculations.py` (`ability_modifier`, `skill_total`, etc.) para a matematica reaproveitavel em testes.

## Cuidados

- Credenciais fixas sao apenas para ambiente local.
- O seed mexe no banco `default`, nao no banco `sdr`.
- O banco `db.sqlite3` e local e ignorado pelo git.
