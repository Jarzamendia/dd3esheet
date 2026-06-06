# PLAN-SDR — Monstros, Tokens e Dados do SRD

> Plano de implementação **passo a passo** para garantir que todos os monstros do
> SRD 3.5 existam como dados, tenham um **token** vinculado e apareçam corretamente
> em `/sdr`, com os tokens linkando de volta para a ficha do monstro.
>
> O trabalho é grande: execute **um passo de cada vez**, marque os checkboxes e
> atualize as listas de _Feito / Falta_ ao final de cada sessão. Nunca pule a
> verificação.

---

## 0. Contexto e descobertas (leia antes de começar)

Antes de planejar, o estado atual foi auditado. **Não assuma que está tudo vazio.**

- **Os dados dos monstros já existem no banco.** A tabela `monster` (no banco
  `sdr` → `dnd35.sqlite3`) tem **681 linhas**, com preenchimento ~100% na maioria
  dos campos (`stat_block`, `full_text`, `hit_dice`, etc.). O modelo é
  `sdr.models.SDR_Monster` (`managed = False`, `db_table = 'monster'`).
- **`/sdr` já serve esses dados.** As views `sdr.views.monsters` (lista) e
  `sdr.views.monster` (detalhe em `/sdr/monster/<id>/`, resolvido por `id` inteiro)
  já existem e renderizam o bloco de estatísticas.
- **A pasta `.data/Monsters/*.md` é a referência humana, não a fonte do app.**
  Tem ~179 cabeçalhos `## ` (nível "família"). Cada `## ` mapeia para a coluna
  **`family`** do banco e se expande em **vários** `name` (ex.: `## Angel` →
  `Angel, Astral Deva`, `Angel, Planetar`, `Angel, Solar`). **O banco é um
  superconjunto** da markdown (tem famílias que a markdown nem lista, como
  `Abomination`, `Astral Construct`).
- **O conceito de "token de monstro" já está modelado** em `sprites/`:
  - `SpriteAsset(Category='monster')` — o token em si (imagem é **opcional**).
  - `SpriteBinding(TargetType='sdr_monster', Purpose='monster_token' | 'map_token',
    TargetKey=<id ou nome>)` — o vínculo token ↔ monstro do SRD.
  - Hoje existem **apenas 3** tokens semeados (`seed_sprites()` em
    `sprites/seeds.py`): Wolf, Unicorn e "Brown Bear" (este **não** existe no banco).
- **Lacunas reais de dados** (o que Parte 2 precisa fechar):
  - `special_abilities`: preenchido em **86%** (588/681) → ~93 monstros sem.
  - `attack` e `special_attacks`: 2 linhas vazias cada.
  - Cobertura markdown → banco ainda **não verificada** monstro a monstro.

### Decisões já tomadas (não reabrir sem motivo)

1. **Escopo do token:** um token para **cada uma das 681 linhas** do banco.
2. **Chave do vínculo:** vincular por **id e por nome** (nomes são únicos no banco).
   O id garante o link para `/sdr/monster/<id>/`; o nome mantém paridade com
   `seed_sprites()` e `sprite_for_monster(monster_name=...)`.
3. **Footprint (pegada no mapa):** derivar de `size`:
   `Fine/Diminutive/Tiny/Small/Medium → 1×1`, `Large → 2×2`, `Huge → 3×3`,
   `Gargantuan → 4×4`, `Colossal / Colossal+ → 6×6`.
4. **Propósitos do vínculo:** `MONSTER_TOKEN` **e** `MAP_TOKEN` (igual ao seed atual).
5. **Sem imagens** nesta fase: os `SpriteAsset` nascem sem `OriginalImage`.

### Convenções do repositório

- Modelos `tabletop`/`sprites` usam **PascalCase** nos campos; `sdr` (não-gerenciado)
  usa `snake_case`. Mantenha o padrão do app que está editando.
- Commits e docs em **português**. **Não** adicionar trailer `Co-Authored-By`.
- Toda alteração precisa de **teste** em `sprites/tests.py` ou `sdr/tests.py`.
- Seeders são **idempotentes** (`update_or_create`), seguindo `seed_sprites()`.

---

## 0.1 Inventário de tokens com arte + casamento token↔SDR (auditado 2026-06-05)

> ⚠️ **Correção importante ao contexto da seção 0:** além dos 3 placeholders de
> `seed_sprites()` (Wolf, Unicorn, Brown Bear, **sem imagem**), a biblioteca da Mesa
> já tem **180 tokens de criatura com PNG renderizado** em
> `media/sprites/original/map_token/<id>.png` (catalogados nos manifests
> `sprites/fixtures/sprite_manifest*.json`, tipo `TABLETOP_TOKEN`). O `MEDIA_ROOT`
> real é `dd3esheet/dd3esheet/media/` (BASE_DIR = pasta do `settings.py`).
>
> Esses tokens **ainda não estão vinculados** a `SDR_Monster` — estão na categoria
> `map_token`, não `monster`. O **casamento abaixo** já resolve cada token de arte
> ao `id` do monstro no banco `sdr` (`dnd35.sqlite3`, 681 linhas), pronto para a
> Parte 1.2 anexar a arte ao asset/monstro certo.

### Resumo do casamento

- **180** tokens de criatura têm arte (PNG).
- **163** foram casados a um monstro do SDR → cobrem **148 monstros distintos**
  (vários tokens de variante apontam para a mesma linha-base; ver "muitos→1" abaixo).
- **17** **não têm equivalente** nesta base do SDR (decidir na Parte 1.2/Parte 2).
- O casamento programático completo está em `tmp/token_monster_match.json`
  (`{token_id: {sdr_id, sdr_name, image}}`). Casamento auto por **conjunto de
  palavras** (resolve "Bear, Black" ↔ `black_bear`) + tabela de aliases curada
  para variantes (ex.: `orc_archer`→Orc base, `wolf_companion`→Wolf).

> **muitos→1** (token de papel/variante → mesma linha-base): `393` Goblin ×3
> (skirmisher/archer/shaman); `454` Kobold ×3; `523` Orc ×3; `413` Hobgoblin ×2;
> `390` Gnoll ×2; `361` Drow ×2; `554` Human Warrior Skeleton ×2; `142` Wolf
> (wolf + wolf_companion); `206` Dire Wolf ×2; `87` Bear,Black ×2; `88` Bear,Brown
> ×2; `108` Leopard ×2.

### ✅ Casamento por categoria (`token` → **[id]** Nome no SDR)

**Bestas e alimárias** (32/33)
`wolf`→**[142]** Wolf · `dire_wolf`→**[206]** Dire Wolf · `dog_guard`→**[97]** Dog · `black_bear`→**[87]** Bear, Black · `brown_bear`→**[88]** Bear, Brown · `dire_bear`→**[199]** Dire Bear · `boar`→**[91]** Boar · `dire_boar`→**[200]** Dire Boar · `lion`→**[109]** Lion · `tiger`→**[136]** Tiger · `leopard`→**[108]** Leopard · `rat_swarm`→**[578]** Rat Swarm · `bat_swarm`→**[574]** Bat Swarm · `giant_rat`→**[202]** Dire Rat · `giant_centipede`→**[628]** Monstrous Centipede, Medium · `giant_spider_medium`→**[642]** Monstrous Spider, Medium · `giant_spider_large`→**[643]** Monstrous Spider, Large · `monstrous_scorpion_medium`→**[635]** Monstrous Scorpion, Medium · `monstrous_scorpion_large`→**[636]** Monstrous Scorpion, Large · `giant_wasp`→**[625]** Giant Wasp · `giant_praying_mantis`→**[624]** Giant Praying Mantis · `crocodile`→**[95]** Crocodile · `shark`→**[124]** Shark, Medium · `constrictor_snake`→**[127]** Constrictor Snake · `viper_snake`→**[131]** Snake, Medium Viper · `elephant`→**[101]** Elephant · `camel`→**[92]** Camel · `rhinoceros`→**[123]** Rhinoceros · `ape`→**[83]** Ape · `dire_badger`→**[197]** Dire Badger · `monitor_lizard`→**[111]** Lizard, Monitor · `giant_ant`→**[618]** Giant Ant, Soldier · ⚠️ `giant_frog`

**Mortos-vivos** (16/21)
`skeleton_warrior`→**[554]** Human Warrior Skeleton · `skeleton_archer`→**[554]** Human Warrior Skeleton · `zombie_commoner`→**[610]** Human Commoner Zombie · `ghoul`→**[379]** Ghoul · `ghast`→**[380]** Ghast · `wight`→**[596]** Wight · `shadow_undead`→**[548]** Shadow · `wraith`→**[600]** Wraith · `mummy`→**[502]** Mummy · `vampire_spawn`→**[594]** Vampire Spawn · `allip`→**[430]** Allip · `bodak`→**[151]** Bodak · `mohrg`→**[501]** Mohrg · `spectre`→**[564]** Spectre · `dread_wraith`→**[601]** Dread Wraith · `devourer`→**[189]** Devourer · ⚠️ `vampire_lord` · ⚠️ `lich` · ⚠️ `ghost_apparition` · ⚠️ `skeletal_horse` · ⚠️ `zombie_dog`

**Gigantes e humanoides monstruosos** (15/19)
`ogre`→**[515]** Ogre · `ogre_mage`→**[517]** Ogre Mage · `troll`→**[590]** Troll · `hill_giant`→**[385]** Hill Giant · `stone_giant`→**[386]** Stone Giant · `frost_giant`→**[383]** Frost Giant · `fire_giant`→**[382]** Fire Giant · `ettin`→**[365]** Ettin · `minotaur`→**[500]** Minotaur · `centaur_archer`→**[155]** Centaur · `harpy`→**[408]** Harpy · `gargoyle`→**[374]** Gargoyle · `medusa`→**[487]** Medusa · `cloud_giant`→**[381]** Cloud Giant · `storm_giant`→**[387]** Storm Giant · ⚠️ `yuan_ti_pureblood` · ⚠️ `yuan_ti_abomination` · ⚠️ `cyclops` · ⚠️ `fomorian`

**Aberrações** (12/17)
`chuul`→**[159]** Chuul · `cloaker`→**[160]** Cloaker · `ettercap`→**[364]** Ettercap · `gibbering_mouther`→**[388]** Gibbering Mouther · `grick`→**[401]** Grick · `mimic_chest`→**[499]** Mimic · `otyugh`→**[524]** Otyugh · `rust_monster`→**[541]** Rust Monster · `aboleth`→**[427]** Aboleth · `roper`→**[540]** Roper · `will_o_wisp`→**[597]** Will-O'-Wisp · `drider`→**[331]** Drider · ⚠️ `beholder_like_eye_tyrant` · ⚠️ `carrion_crawler` · ⚠️ `mind_flayer_like_psion` · ⚠️ `umber_hulk` · ⚠️ `grell`

**Dragões** (19/19)
`dragon_wyrmling_red`→**[245]** Red Dragon, Wyrmling · `dragon_wyrmling_black`→**[209]** Black Dragon, Wyrmling · `dragon_wyrmling_green`→**[233]** Green Dragon, Wyrmling · `dragon_wyrmling_white`→**[257]** White Dragon, Wyrmling · `dragon_wyrmling_blue`→**[221]** Blue Dragon, Wyrmling · `dragon_wyrmling_brass`→**[269]** Brass Dragon, Wyrmling · `dragon_wyrmling_bronze`→**[281]** Bronze Dragon, Wyrmling · `dragon_wyrmling_copper`→**[293]** Copper Dragon, Wyrmling · `dragon_wyrmling_silver`→**[317]** Silver Dragon, Wyrmling · `dragon_young_red`→**[247]** Red Dragon, Young · `dragon_young_blue`→**[223]** Blue Dragon, Young · `dragon_young_green`→**[235]** Green Dragon, Young · `dragon_young_black`→**[211]** Black Dragon, Young · `dragon_young_white`→**[259]** White Dragon, Young · `dragon_adult_red`→**[250]** Red Dragon, Adult · `dragon_adult_gold`→**[310]** Gold Dragon, Adult · `wyvern`→**[602]** Wyvern · `pseudodragon`→**[533]** Pseudodragon · `dragon_turtle`→**[329]** Dragon Turtle

**Elementais e outsiders** (27/28)
`air_elemental_medium`→**[337]** Air Elemental, Medium · `air_elemental_large`→**[338]** Air Elemental, Large · `earth_elemental_medium`→**[343]** Earth Elemental, Medium · `earth_elemental_large`→**[344]** Earth Elemental, Large · `fire_elemental_medium`→**[349]** Fire Elemental, Medium · `fire_elemental_large`→**[350]** Fire Elemental, Large · `water_elemental_medium`→**[355]** Water Elemental, Medium · `water_elemental_large`→**[356]** Water Elemental, Large · `celestial_lantern_archon`→**[443]** Lantern Archon · `hound_archon`→**[444]** Hound Archon · `avoral_guardinal`→**[452]** Avoral · `imp_familiar`→**[187]** Imp · `quasit`→**[173]** Quasit · `dretch`→**[168]** Dretch · `hell_hound`→**[410]** Hellhound · `barbed_devil`→**[179]** Barbed Devil · `chain_devil`→**[182]** Chain Devil · `erinyes_archer`→**[183]** Erinyes · `succubus_tempter`→**[175]** Succubus · `balor`→**[166]** Balor · `marilith`→**[171]** Marilith · `vrock`→**[176]** Vrock · `hezrou`→**[170]** Hezrou · `glabrezu`→**[169]** Glabrezu · `bone_devil`→**[181]** Bone Devil · `pit_fiend`→**[188]** Pit Fiend · `planetar`→**[432]** Angel, Planetar · ⚠️ `lemure`

**Humanoides inimigos** (22/23)
`goblin_skirmisher`/`goblin_archer`/`goblin_shaman`→**[393]** Goblin, 1st-Level Warrior · `kobold_spearman`/`kobold_slinger`/`kobold_trapmaker`→**[454]** Kobold, 1st-Level Warrior · `orc_raider`/`orc_archer`/`orc_war_chief`→**[523]** Orc, 1st-Level Warrior · `hobgoblin_soldier`/`hobgoblin_captain`→**[413]** Hobgoblin, 1st-Level Warrior · `bugbear_brute`→**[153]** Bugbear · `gnoll_hunter`/`gnoll_pack_lord`→**[390]** Gnoll · `lizardfolk_warrior`→**[462]** Lizardfolk · `troglodyte_savage`→**[589]** Troglodyte · `sahuagin_raider`→**[542]** Sahuagin · `drow_scout`/`drow_priestess`→**[361]** Drow, 1st-Level Warrior · `duergar_warrior`→**[334]** Duergar, 1st-Level Warrior · `derro_madcap`→**[177]** Derro · `grimlock_cavern_hunter`→**[403]** Grimlock · ⚠️ `kuo_toa_monitor`

**Montarias, companheiros e familiares** (20/20)
`riding_horse`→**[104]** Horse, Light · `warhorse_light`→**[106]** Warhorse, Light · `warhorse_heavy`→**[105]** Warhorse, Heavy · `pony`→**[118]** Pony · `mule_pack`→**[114]** Mule · `riding_dog`→**[98]** Dog, Riding · `hawk_familiar`→**[102]** Hawk · `owl_familiar`→**[117]** Owl · `raven_familiar`→**[122]** Raven · `cat_familiar`→**[93]** Cat · `rat_familiar`→**[121]** Rat · `toad_familiar`→**[137]** Toad · `weasel_familiar`→**[138]** Weasel · `snake_familiar`→**[129]** Snake, Tiny Viper · `wolf_companion`→**[142]** Wolf · `black_bear_companion`→**[87]** Bear, Black · `brown_bear_companion`→**[88]** Bear, Brown · `dire_wolf_companion`→**[206]** Dire Wolf · `eagle_companion`→**[100]** Eagle · `leopard_companion`→**[108]** Leopard

### ⚠️ Tokens com arte SEM equivalente no SDR (17 — decidir na Parte 1.2/2)

- **Stand-ins propositais (IP-safe)** — não terão linha no SRD: `beholder_like_eye_tyrant`, `mind_flayer_like_psion`. → manter como arte avulsa (sem link SRD).
- **Templates do SRD (sem stat-line própria nesta base)**: `lich`, `ghost_apparition` (Ghost é template), `vampire_lord` (só "Vampire Spawn" existe). → decidir se cria linha derivada na Parte 2.
- **Esqueleto/zumbi de animal sem linha**: `skeletal_horse`, `zombie_dog` (existem Wolf Skeleton etc., mas não estes).
- **Criaturas ausentes desta base de 681 linhas**: `giant_frog`, `yuan_ti_pureblood`, `yuan_ti_abomination`, `cyclops`, `fomorian`, `carrion_crawler`, `umber_hulk`, `grell`, `lemure`, `kuo_toa_monitor`. → candidatos a **FALTA** na auditoria da Parte 2.

### ⏳ Catalogados no manifesto, mas SEM imagem ainda (57 — arte pendente)

- **Bestas mágicas** (24): Owlbear, Griffon, Hippogriff, Pegasus, Unicorn, Worg, Winter Wolf, Blink Dog, Displacer Beast, Bulette, Ankheg, Basilisk, Cockatrice, Chimera, Manticore, Hydra (5 cabeças), Gorgon, Behir, Sea Cat, Gynosphinx, Phase Spider, Girallon, Choker, Darkmantle
- **Constructos e gosmas** (15): Animated Armor/Table/Statue/Object, Homunculus, Shield Guardian, Stone/Iron/Flesh/Clay Golem, Retriever, Gelatinous Cube, Gray Ooze, Ochre Jelly, Black Pudding
- **Plantas e fey** (9): Dryad, Pixie, Satyr, Nymph, Treant, Assassin Vine, Shambling Mound, Violet Fungus, Shrieker Fungus
- **Enxames e invocações** (9): Celestial Eagle/Bison, Fiendish Wolf/Giant Spider, Small Fire/Earth summon, Insect/Spider/Centipede Swarm

> Nota: `unicorn` (manifesto, sem imagem) vs. placeholder SVG `monster-unicorn.svg`
> do `seed_sprites()` antigo (id `592` no SDR) são assets distintos; consolidar na
> Parte 1.2.

---

## PARTE 1 — Estrutura (monstros, tokens e dados)

**Objetivo:** ter a "fundação" pronta: confirmar os modelos, criar o seeder de
tokens de todos os monstros e a função que resolve o link token → `/sdr`.
Nenhuma imagem é gerada aqui.

### 1.1 Confirmar a estrutura existente
- [x] Reler `sdr/models.py::SDR_Monster`, `sprites/models.py`
      (`SpriteAsset`, `SpriteBinding`) e `tabletop/models.py::Token`.
- [x] Reler `sprites/services.py::sprite_for_monster` e `sprites/seeds.py`.
- [x] **Nenhuma migração nova** é necessária para Parte 1 (modelos já existem).

### 1.2 Seeder de tokens — `seed_monster_tokens()` ✅ FEITO (2026-06-05)
Arquivo: `sprites/seeds.py::seed_monster_tokens()` + comando
`sprites/management/commands/seed_monster_tokens.py`. Casamento durável em
`sprites/fixtures/monster_token_casamento.json` (`{nome_SDR: token_slug}`, 148 entradas).

Para cada `SDR_Monster.objects.using('sdr')` (id, name, size), `_resolve_monster_asset`
escolhe o asset nesta **ordem de prioridade**:
- [x] **1. Arte do casamento** (`casamento[name]` → `SpriteAsset(Slug=token_slug)`):
      anexa o PNG auditado na seção 0.1. **Tem prioridade** sobre o placeholder
      legado do `seed_sprites` (ex.: Wolf agora usa `wolf.png`, não `monster-wolf.svg`).
- [x] **2. Vínculo já existente** (`SpriteBinding(sdr_monster, str(id)|name,
      MONSTER_TOKEN)`): garante idempotência dos placeholders e preserva binds manuais
      (ex.: Unicorn, sem PNG, mantém `monster-unicorn.svg`).
- [x] **3. Placeholder sem imagem**: `SpriteAsset(Slug='monster-<id>',
      Category='monster', …)` com footprint via `footprint_for_size(size)`.
- [x] **Vincular** os 4 (`update_or_create` em `(TargetType, TargetKey, Purpose)`):
      `(sdr_monster, str(id)|name, MONSTER_TOKEN|MAP_TOKEN)`.
- [x] Comando imprime resumo: `total | criados, reutilizados, vínculos`.
- [x] **Idempotência:** rodar 2× → 0 criados, 681 reutilizados, 2724 vínculos.

### 1.3 Resolver o link token → SRD — `monster_id_for_asset()` ✅ FEITO
Arquivo: `sprites/services.py::monster_id_for_asset()`.
- [x] Dado um `SpriteAsset`, retorna o `id` do monstro via
      `SpriteBinding(sdr_monster, MONSTER_TOKEN)` cuja `TargetKey` é numérica
      (`.isdigit()`) → permite `reverse('sdr:monster', [id])`.
- [x] Retorna `None` quando o asset não for de monstro.

### 1.4 Testes da Parte 1 (`sprites/tests.py`) ✅ 12 testes verdes
- [x] Mapeamento de footprint por `size` (cada faixa + fallback).
- [x] Idempotência do seeder (rodar 2× → contagens iguais, sem asset duplicado).
- [x] Reutiliza asset de arte via casamento; arte **vence** o placeholder legado.
- [x] Cria placeholder sem imagem (footprint pelo size) p/ monstro sem arte.
- [x] Token resolve por `sprite_for_monster(monster_id=...)` **e** `(monster_name=...)`.
- [x] Vincula cada monstro de 4 formas; comando roda e imprime resumo.
- [x] `monster_id_for_asset()` devolve o id correto e `None` p/ asset não-monstro.

### ✅ Critério de pronto da Parte 1
- [x] `python manage.py seed_monster_tokens` → **681 monstros, 2724 vínculos**
      (1ª rodada: 532 placeholders criados + 149 reutilizados; 2ª: 0/681, idempotente).
      Arte anexada a 148 monstros distintos.
- [x] `python manage.py test sprites` → meus 12 testes novos verdes. (10 falhas
      **pré-existentes** em testes de _view_ — 301/login — alheias a esta mudança,
      confirmado por `git stash` na main suja do working tree.)

---

## PARTE 2 — Dados dos monstros com base em `.data/Monsters/`

**Objetivo:** garantir que **todo** monstro da markdown está representado no banco
e **completo**. Como o banco já é um superconjunto, isto é
**verificação de cobertura + backfill de lacunas** — não uma reimportação.

> ⚠️ Esta é a parte "muito trabalho". Faça **um arquivo de letra por vez** (A → Z),
> marque o checkbox da letra e registre os achados na tabela de progresso (2.4).

### 2.1 Ferramenta de auditoria — `audit_monster_coverage` ✅ FEITO (2026-06-06)
Comando: `sdr/management/commands/audit_monster_coverage.py` (ler `--db sdr`).
- [x] Para cada `.data/Monsters/3.5 Monsters - <L>.md`, extrair os cabeçalhos `## `
      (as famílias) e os sub-blocos relevantes.
- [x] Para cada família, achar linhas no banco por `family` (igualdade
      normalizada) **ou** `name` contendo o termo. Classificar em:
      `OK` (≥1 linha), `FALTA` (0 linhas), `REVISAR` (nome ambíguo).
- [x] Reportar também **lacunas de campo** por monstro: `special_abilities`,
      `attack`, `special_attacks` vazios.
- [x] Saída: relatório por letra em `tmp/monster_coverage_<L>.md` + resumo no stdout.
- [x] Teste do comando com um fixture markdown pequeno.

Rodada real em 2026-06-06 após reconciliação A-Z da markdown: 179 famílias
auditadas, 0 `FALTA`, 0 `REVISAR`, 9 famílias justificadas, 0 lacunas de campo
abertas nos monstros cobertos pela markdown e 11 campos vazios justificados.
Checagem do banco completo via `audit_monster_field_gaps` reporta 0 lacunas
abertas e 38 campos vazios justificados.

### 2.2 Reconciliação por letra (loop principal)
Para **cada** arquivo abaixo: rodar a auditoria, revisar o relatório, e para cada
`FALTA`/`REVISAR`/lacuna decidir e aplicar a correção (criar linha que falte a
partir da markdown, ou preencher campo). Registrar tudo na tabela 2.4.

- [x] A · [x] B · [x] C · [x] D · [x] E · [x] F · [x] G · [x] H · [x] I · [x] K
- [x] L · [x] M · [x] N · [x] O · [x] P · [x] R · [x] S · [x] T · [x] U · [x] V
- [x] W · [x] X · [x] Y · [x] Z
- (não existem arquivos **J** nem **Q** — confirmado.)

> Como o banco é **não-gerenciado** (`managed=False`), inserções/edições nesse
> banco vão por script de migração de dados próprio do `sdr` (ver 2.3), **não** por
> migração Django comum.

### 2.3 Backfill de lacunas conhecidas
- [x] `special_abilities` vazio em ~93 monstros: extrair os blocos `#### <Habilidade>
      (Ex/Su/Sp)` da markdown correspondente e preencher. Resolvido por
      `backfill_monster_fields` + justificativas; `audit_monster_field_gaps`
      reporta `0` lacunas abertas (38 justificadas).
- [x] As 2 linhas com `attack` vazio e 2 com `special_attacks` vazio: completar pela
      markdown (ex.: `Ethereal Marauder.special_attacks="-"`); sem lacunas restantes.
- [x] Toda escrita no banco `sdr` é feita por um comando idempotente versionado
      (`sdr/management/commands/backfill_monster_fields.py`) — re-rodável, com
      `--dry-run`.

Backfills aplicados:
- 2026-06-06: `Angel, Planetar` (`id=432`) recebeu
  `special_abilities="Regeneration (Ex)"`; reauditoria da letra A reportou
  `0 FALTA`, `0 REVISAR`, `0` lacunas.
- 2026-06-06: backfill dos devils da letra D: `Barbed Devil` (`id=179`),
  `Bearded Devil` (`id=180`), `Bone Devil` (`id=181`), `Chain Devil` (`id=182`),
  `Hellcat` (`id=184`), `Horned Devil` (`id=185`) e `Ice Devil` (`id=186`)
  receberam `special_abilities` a partir dos cabeçalhos da fonte.
- 2026-06-06: `Ethereal Marauder` (`id=363`) recebeu
  `special_attacks="-"`, corrigindo parse vazio onde a fonte indica ausência de
  ataques especiais.
- 2026-06-06: backfill da letra L: `Lizardfolk.special_abilities`,
  `Weretiger` formas animal/híbrida (`attack`) e `special_abilities` dos
  lycanthropes avançados (`Werewolf Lord` e `Hill Giant Dire Wereboar`).
- 2026-06-06: backfills finais da cobertura markdown: `Ogre, 4th-Level Barbarian`,
  `Pegasus`, esqueletos, `Triton`, `Troglodyte` e zumbis.
- 2026-06-06: backfills fora da cobertura markdown: `Behemoth Eagle`,
  `Hoary Hunter`, `Hoary Steed`, `Sirrush`, `Titan, Elder`, `Crocodile, Giant`,
  `Astral Construct` níveis 1-9, `Blue`, `Crysmal`, `Dromite` e `Psicrystal`.

Campos vazios justificados:
- 2026-06-06: `Bugbear.special_abilities` (`id=153`) permanece vazio porque a
  fonte não traz habilidade especial `Ex/Su/Sp`, apenas seção `Skills`; registrado
  em `sdr/data/monster_field_justifications.json`. Reauditoria da letra B reportou
  `0 FALTA`, `0 REVISAR`, `0` lacunas e `1` justificativa.
- 2026-06-06: `Centaur.special_abilities` (`id=155`) permanece vazio porque a
  fonte não traz habilidade especial `Ex/Su/Sp`; registrado em
  `sdr/data/monster_field_justifications.json`.
- 2026-06-06: `Locathah.special_abilities` permanece vazio porque a fonte não traz
  habilidade especial `Ex/Su/Sp`; registrado em
  `sdr/data/monster_field_justifications.json`.
- 2026-06-06: `Elasmosaurus.special_abilities` (`id=192`) permanece vazio porque
  a fonte não traz habilidade especial `Ex/Su/Sp`; registrado em
  `sdr/data/monster_field_justifications.json`.
- 2026-06-06: `Gnoll`, `Goblin, 1st-Level Warrior`, `Grick`, `Hippogriff` e
  `Hobgoblin, 1st-Level Warrior` permanecem com `special_abilities` vazio porque
  a fonte não traz habilidade especial `Ex/Su/Sp`; registrados em
  `sdr/data/monster_field_justifications.json`.
- 2026-06-06: `Ogre` e `Roc` permanecem com `special_abilities` vazio porque a
  fonte não traz habilidade especial `Ex/Su/Sp`; registrados em
  `sdr/data/monster_field_justifications.json`.
- 2026-06-06: animais/vermes comuns fora da cobertura markdown permanecem com
  `special_abilities` vazio quando `SA=-` e não há habilidade especial tipada;
  registrados em `sdr/data/monster_field_justifications.json`.

Famílias sem linha própria justificadas:
- 2026-06-06: `Celestial Creature` permanece sem linha no banco porque a fonte
  define como template herdado, não como monstro autônomo; registrado em
  `sdr/data/monster_family_justifications.json`. Reauditoria da letra C reportou
  `0 FALTA`, `0 REVISAR`, `0` lacunas, `1` família justificada e `1` campo
  justificado.
- 2026-06-06: `Dragons - Chromatic` e `Dragons - Metallic` permanecem sem linhas
  próprias porque são cabeçalhos agrupadores; os monstros por cor/idade já existem
  em `Dragon, True`. Reauditoria da letra D reportou `0 FALTA`, `0 REVISAR`,
  `0` lacunas, `2` famílias justificadas e `1` campo justificado.
- 2026-06-06: `Fiendish Creature`, `Ghost`, `Half-Celestial`, `Half-Dragon` e
  `Half-Fiend` permanecem sem linhas próprias porque são templates; registrados em
  `sdr/data/monster_family_justifications.json`.
- 2026-06-06: `Lich` permanece sem linha própria porque a fonte define como
  template adquirido; registrado em `sdr/data/monster_family_justifications.json`.

### 2.4 Tabela de progresso da cobertura (preencher durante 2.2)

| Letra | Famílias md | Linhas no banco | FALTA | REVISAR | Lacunas backfill | Status |
|-------|-------------|-----------------|-------|---------|------------------|--------|
| A | 13 | 27 | 0 | 0 | 0 | OK |
| B | 9 | 11 | 0 | 0 | 0 | OK (1 justificada) |
| C | 9 | 8 | 0 | 0 | 0 | OK (1 família e 1 campo justificados) |
| D | 19 | 172 | 0 | 0 | 0 | OK (2 famílias e 1 campo justificados) |
| E | 7 | 31 | 0 | 0 | 0 | OK |
| F | 4 | 8 | 0 | 0 | 0 | OK (1 família justificada) |
| G | 17 | 32 | 0 | 0 | 0 | OK (1 família e 3 campos justificados) |
| H | 12 | 21 | 0 | 0 | 0 | OK (3 famílias e 2 campos justificados) |
| I | 2 | 3 | 0 | 0 | 0 | OK |
| K | 3 | 3 | 0 | 0 | 0 | OK |
| L | 8 | 29 | 0 | 0 | 0 | OK (1 família e 1 campo justificados) |
| M | 9 | 19 | 0 | 0 | 0 | OK |
| N | 5 | 11 | 0 | 0 | 0 | OK |
| O | 7 | 12 | 0 | 0 | 0 | OK (1 campo justificado) |
| P | 7 | 8 | 0 | 0 | 0 | OK |
| R | 7 | 7 | 0 | 0 | 0 | OK (1 campo justificado) |
| S | 17 | 38 | 0 | 0 | 0 | OK |
| T | 9 | 12 | 0 | 0 | 0 | OK |
| U | 1 | 2 | 0 | 0 | 0 | OK |
| V | 3 | 2 | 0 | 0 | 0 | OK |
| W | 6 | 7 | 0 | 0 | 0 | OK |
| X | 2 | 4 | 0 | 0 | 0 | OK |
| Y | 2 | 2 | 0 | 0 | 0 | OK |
| Z | 1 | 8 | 0 | 0 | 0 | OK |

### ✅ Critério de pronto da Parte 2
- [x] `audit_monster_coverage` reporta **0 FALTA** em todas as letras.
- [x] `special_abilities`, `attack`, `special_attacks` sem lacunas (ou justificadas
      como "não existe na fonte").
- [x] `python manage.py test sdr` verde (19 testes; ver nota de ambiente abaixo).

---

## PARTE 3 — `/sdr` atualizado + tokens com link para o SRD

**Objetivo:** confirmar que a página `/sdr` mostra os dados (inclusive os do
backfill) e que **cada token de monstro** tem um link para a ficha do monstro.

### 3.1 Verificar que `/sdr` reflete os dados ✅ FEITO (2026-06-06)
- [x] Conferir `sdr/views.py::monster` e o template `sdr/monster.html`: garantir que
      `special_abilities`, `stat_block` e o fallback `full_text` aparecem. A view já
      monta `text_sections` com "Habilidades Especiais" (`special_abilities`) e
      "Bloco de Estatísticas" (`stat_block`), com `fallback_full_text` quando não há
      conteúdo estruturado.
- [x] Conferir a **lista** `/sdr/monsters/` e o `MonsterFilter`: a view `monsters`
      usa `SDR_Monster.objects.using('sdr')` (todos os 681) e o `MonsterFilter`.
- [x] Verificação automatizada: smoke test `GET /sdr/monster/<id>/` → 200 cobrindo o
      caminho de render (substitui a checagem manual).

### 3.2 Link token → ficha do SRD ✅ FEITO (2026-06-06)
- [x] `tabletop/partials/_token.html` expõe `data-srd-url` quando o token resolve
      para um monstro; o editor JS (`scene_editor.js`) seta `data-srd-url` no token
      do canvas (`updateToken`).
- [x] Link visível **"Ver no SRD ↗"** no detalhe/edição do token: server-side em
      `_token_row.html` e no inspector do editor JS (`renderInspector`).
- [x] `tabletop/services.py::attach_sprites_to_tokens` injeta `token.SrdUrl` em lote
      via `sprites.services.monster_ids_for_assets()` (uma query p/ bindings, sem
      N+1); `serialize_token` expõe `srdUrl`; `_token_library_payload` resolve em
      lote para tokens recém-colocados.
- [x] Token **sem** monstro vinculado (jogador/objeto) fica com `SrdUrl=''` → sem link.

### 3.3 Testes da Parte 3 ✅ 8 testes verdes (`tabletop.tests.MonsterTokenSrdLinkTests`)
- [x] Serviço: token de monstro recebe `SrdUrl == /sdr/monster/<id>/`; `serialize_scene`
      expõe `srdUrl`.
- [x] Token de jogador/objeto (asset não-monstro) não expõe URL.
- [x] Resolução em lote (`assertNumQueries(2)` para N tokens — sem N+1).
- [x] Editor body mostra "Ver no SRD" p/ token de monstro e **não** p/ jogador.
- [x] Smoke test: `GET /sdr/monster/<id>/` de um monstro semeado responde 200.

### ✅ Critério de pronto da Parte 3
- [x] Tokens de monstro mostram link para o SRD; demais tokens não.
- [x] `/sdr` renderiza dados completos (incl. backfill).
- [x] `python manage.py test` (suite inteira) verde — **369 testes OK**.

---

## Nota de ambiente — como rodar os testes (descoberto 2026-06-06)

A suíte só fica verde com **`DEBUG=True`** e em **Python ≤ 3.13** (o deploy usa
3.12; ver `Dockerfile`). As "falhas pré-existentes de view" das sessões anteriores
eram ambientais, não do código:

1. **Python 3.14** (venv local antigo `.venv`) quebra `Context.__copy__` do Django
   4.2 ao renderizar templates no test client. Use Python 3.12/3.13.
2. **`DEBUG=False`** (default sem `.env`) liga `SECURE_SSL_REDIRECT` → todas as
   requisições http do test client viram 301, e o storage de estáticos exige
   manifesto (collectstatic). Os testes de config de produção
   (`character.tests.SettingsHardeningTest`/`StaticFilesTest`) **esperam** esse
   bloco ativo, então a forma correta é rodar a suíte com `DEBUG=True` (não mexer
   no `settings.py`).

Comando usado: `DEBUG=True python manage.py test` (venv Python 3.13).

---

## Rastreamento global — Feito / Falta

### ✅ Feito
- **Casamento token↔SDR** (seção 0.1): 180 tokens com arte, 163 casados → 148
  monstros distintos; fixture `monster_token_casamento.json` (2026-06-05).
- **Parte 1 inteira** — `seed_monster_tokens()` + `monster_id_for_asset()` +
  `footprint_for_size()` + comando + 12 testes verdes; rodado no banco real
  (681 monstros, 2724 vínculos, idempotente) (2026-06-05).
- **Parte 2.1** — comando `audit_monster_coverage` + teste; relatórios A-Z gerados
  em `tmp/monster_coverage_<L>.md` (2026-06-06).
- **Parte 2.2/2.3 letra A** — backfill de `Angel, Planetar.special_abilities`
  aplicado via `backfill_monster_fields`; letra A reaudita sem pendências
  (2026-06-06).
- **Parte 2.2 letra B** — `Bugbear.special_abilities` justificado como vazio pela
  fonte; letra B reaudita sem pendências abertas (2026-06-06).
- **Parte 2.2 letra C** — `Celestial Creature` justificado como template sem linha
  própria e `Centaur.special_abilities` justificado como vazio pela fonte; letra C
  reaudita sem pendências abertas (2026-06-06).
- **Parte 2.2/2.3 letra D** — devils receberam backfill de `special_abilities`;
  agrupadores de dragões e `Elasmosaurus.special_abilities` foram justificados;
  letra D reaudita sem pendências abertas (2026-06-06).
- **Parte 2.2/2.3 letras E-H** — `Ethereal Marauder.special_attacks` recebeu
  backfill; templates de F/G/H e campos sem habilidade especial real foram
  justificados; letras E-H reauditam sem pendências abertas (2026-06-06).
- **Parte 2.2 letras I e K** — relatórios sem `FALTA`, `REVISAR` ou lacunas;
  marcadas como concluídas (2026-06-06).
- **Parte 2.2/2.3 letras L-N** — L recebeu backfills/justificativas; M e N não
  tinham pendências; letras L-N reauditam sem pendências abertas (2026-06-06).
- **Parte 2.2/2.3 letras O-Z** — cobertura markdown concluída: `0 FALTA`,
  `0 REVISAR` e `0` lacunas abertas nos relatórios A-Z (2026-06-06).
- **Parte 2.3 banco completo** — `audit_monster_field_gaps` reporta `0` lacunas
  abertas e `38` justificadas; `backfill_monster_fields` segue idempotente
  (2026-06-06).
- **Parte 3 inteira** — `/sdr` confirmado (view monta `special_abilities`/`stat_block`
  + fallback `full_text`); link token→SRD via `attach_sprites_to_tokens` (batch,
  `monster_ids_for_assets`), `serialize_token.srdUrl`, `_token.html` (`data-srd-url`),
  `_token_row.html` + inspector JS ("Ver no SRD ↗"); 8 testes novos verdes; suíte
  inteira **369 OK** (2026-06-06).
- **Ambiente de teste** — descoberto que a suíte exige `DEBUG=True` e Python ≤3.13;
  as "falhas pré-existentes" eram ambientais (ver "Nota de ambiente"). Sem mudança
  de `settings.py` (2026-06-06).

### ⏳ Falta
- Nada pendente no escopo do PLAN-SDR. **Partes 1, 2 e 3 concluídas.**
  - Itens opcionais futuros (fora do plano): os 17 tokens "sem equivalente" da
    seção 0.1 seguem como arte avulsa por decisão (stand-ins IP-safe e templates);
    e os 57 tokens catalogados sem PNG aguardam arte.

### Ordem de execução recomendada
1. Parte 1 inteira (base + tokens) → permite testar links já na Parte 3.
2. Parte 2.1 (ferramenta de auditoria) — destrava todo o resto da Parte 2.
3. Parte 2.2/2.3 letra a letra (sessões curtas, commit por letra).
4. Parte 3 por último, quando dados e tokens já existem.

> A cada sessão: rode os testes do app tocado, atualize os checkboxes e a tabela
> 2.4, e mova itens de _Falta_ para _Feito_.
