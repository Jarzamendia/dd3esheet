# AGENT2.md — GPT-5: Cálculos automáticos + Invocações (SDR) + Persistência de estado

Você é o **Agente 2 (GPT-5)** e cuida do trabalho de **domínio mais complexo**: derivar automaticamente todos os números da ficha, criar o sistema de **Invocações** (`CharacterSummon`) com autocomplete via SRD, e **persistir o estado de jogo** que hoje se perde. Trabalhe **isolado em worktree própria**. O Agente 1 cuida do popup/autosave em outra worktree; vocês não compartilham branch — o coordenador faz o merge no fim.

## 0. Setup (uma vez)

```bash
# A partir da raiz do repo (C:\Users\Jarzamendia\git\github\dd3esheet):
git worktree add ../dd3esheet-agent2 -b feat/agent2-calc-summons feat/sdr-spell-popup
cd ../dd3esheet-agent2
```

Ligue o Docker Desktop antes de testar.

## Regras (obrigatórias)

- **TDD:** teste que falha → implementa → passa. Testes na mesma commit.
- **Testes (container isolado desta worktree):** rode a partir de `../dd3esheet-agent2/dd3esheet` com nome de projeto próprio para não colidir com a outra worktree. `run --rm` não publica a porta 8000 (sem conflito):
  ```bash
  cd ../dd3esheet-agent2/dd3esheet   # raiz onde está o docker-compose.yaml
  docker compose -p agent2 run --rm --build web python manage.py test <alvo> -v 2
  ```
  Suite inteira antes de cada commit (omita `--build` após a 1ª vez):
  ```bash
  docker compose -p agent2 run --rm web python manage.py test -v 1
  ```
  Após criar migrations, aplique no banco da sua worktree:
  ```bash
  docker compose -p agent2 run --rm web python manage.py makemigrations character
  docker compose -p agent2 run --rm web python manage.py migrate
  ```
  > **Não** use `docker exec dd3esheet-web-1 …`: aquele container monta a pasta do coordenador, não a sua worktree.
- **Funções de cálculo são puras** (recebem primitivos, não models), moram em `character/calculations.py`, e ganham `SimpleTestCase` com casos zero/positivo/negativo. A view só orquestra: lê fontes de verdade, chama puras, persiste atômico com `update_fields`.
- **PascalCase** em campos de model; SDR sempre `.using('sdr')`; **sem FK cross-DB** (resolver por ID com `.using('sdr')`). Arquivos novos UTF-8 sem BOM.
- **Commits pequenos**, pt-BR (`feat(...)`/`refactor(...)`), **sem** trailer `Co-Authored-By`. Commite só na sua branch.
- **Nunca** `git add dd3esheet/nul`. Use paths específicos.
- **Migrations:** a última existente é `0007`. Numere a partir de `0008`. Você é o único que cria migrations.

## Mapa do que já existe (fonte de verdade)

- `character/calculations.py` — puras já prontas: `ability_modifier`, `skill_graduation_limits`, `skill_total`, `compute_armor_class`, `compute_save_total`, `compute_grapple_total`, `compute_skill_row`, `load_limits_for_strength`, `parse_bonus`, `parse_weight`, `total_carried_weight`, `equipment_armor_class_bonuses`.
- `character/views.py::_recalculate_stats` (linhas ~488–596) — orquestrador atual: deriva mods de atributo, limites de perícia, CA (total/toque/surpresa, mas usando **Des cheio**, sem cap), Iniciativa=Des, saves totais, **só Agarrar** entre os ataques, perícias e carga/peso. Chamado em todos os saves HTMX.
- Models relevantes: `CharacterStats`, `CharacterStatus` (`TotalHitPoints`, `Speed`), `CharacterAttackModifiers` (`BBA`, Grappler*), `CharacterArmor` (`ACBonus`, `MaxDex`, `CheckPenalty`, `Speed`, `Weigth`), `CharacterSpellSave` (`SpellSaveDC`, `BonusSpells`), `CharacterSkill`.

---

# Entrega A — Cálculo automático em **todos** os campos deriváveis

## A0 — Auditoria primeiro
Varra `_recalculate_stats`, os models e os partials e **liste todo campo que é digitado à mão mas é derivável** das regras de D&D 3.5. Registre a lista em `docs/known-issues.md` (seção "Campos deriváveis ainda manuais"). Use-a como checklist de cobertura — o critério é "nenhum campo derivável fica manual".

## A1 — Ataques (corpo-a-corpo e à distância)
Hoje só Agarrar é derivado. Adicione em `calculations.py`:
```python
def compute_attack_bonus(*, bba, ability_mod, size_mod, misc):
    return to_int(bba) + to_int(ability_mod) + to_int(size_mod) + to_int(misc)
```
- Corpo-a-corpo usa mod de **Força**; à distância usa mod de **Destreza**; ambos somam `size_mod` e `misc`.
- Persistir no destino correto (campo de ataque base em `CharacterAttackModifiers` e/ou por arma em `CharacterWeapon.AttackBonus`, conforme a UI consumir — verifique o template). Atualize `_recalculate_stats`.
- Testes: `SimpleTestCase` para a pura; teste de view confirmando persistência do total melee/ranged.

## A2 — Cap de Destreza pela armadura na CA
Hoje `status.ACDexModifier = stats.DexterityStatMod` (Des cheio). Adicione:
```python
def cap_dex_to_armor(dex_mod, max_dex):
    # max_dex vazio/None = sem limite
    ...
```
- Pegue o menor `MaxDex` entre as armaduras/escudos equipados (parse via `parse_bonus`); aplique como teto ao mod de Des usado na CA (e na CA de toque).
- Atualize `_recalculate_stats` antes de chamar `compute_armor_class`.
- Teste: armadura `MaxDex 2` + Des +4 → CA usa +2.

## A3 — Penalidade de armadura nas perícias
- Some as `CheckPenalty` de armadura + escudo equipados (parse via `parse_bonus`, são negativas).
- Aplique às perícias afetadas por armadura (baseadas em Força/Destreza — defina o conjunto conforme 3.5; Natação conta dobrado). Estenda `skill_total`/`compute_skill_row` ou adicione uma pura `armor_check_penalty_for_skill(skill_name, total_penalty)`.
- Teste: perícia de Destreza com penalidade −4 reflete no `SkillModifier`.

## A4 — Deslocamento por carga e armadura
```python
def speed_for_load(base_speed, load_category, armor_speed): ...
```
- Determine a categoria de carga (leve/média/pesada) comparando `TotalWCarried` com os limites já calculados.
- Carga média/pesada **ou** armadura pesada reduzem o deslocamento (30→20, 20→15, etc., regra padrão 3.5). `armor_speed` da armadura equipada tem prioridade quando preenchido.
- Persistir em `CharacterStatus.Speed`. Teste para 30 e 20 ft com carga leve/pesada.

## A5 — CD de magia e magias bônus
```python
def compute_spell_save_dc(spell_level, casting_ability_mod):
    return 10 + to_int(spell_level) + to_int(casting_ability_mod)

def bonus_spells_for_ability(ability_score, spell_level):
    # tabela padrão 3.5: mod >= spell_level necessário; bônus = (mod - spell_level)//4 + 1
    ...
```
- Ligue em `character/spellcasting.py` e/ou `_recalculate_stats`, persistindo em `CharacterSpellSave` por nível (`SpellSaveDC`, `BonusSpells`). O atributo-chave de conjuração vem da classe (já há leitura de `class_table` do SDR em `spellcasting.py` — reutilize).
- Testes `SimpleTestCase`: CD e bônus para FOR/DES/etc. baixos e altos (incl. caso "sem magias bônus").

**Commit da Entrega A:** suite inteira verde; auditoria registrada em `docs/known-issues.md`.

---

# Entrega B — Invocações (`CharacterSummon`): T4.6 + T4.7 + T4.8

## B1 (T4.6) — Model + grid de 3 colunas
Model em `character/models.py` (PascalCase):
```python
class CharacterSummon(models.Model):
    Character = models.ForeignKey(Character, on_delete=models.CASCADE)
    Name = models.CharField(max_length=200, blank=True)
    SpellOrigin = models.CharField(max_length=100, blank=True)   # "SNA III", "SM IV"
    Level = models.IntegerField(default=0)
    HitPointsMax = models.IntegerField(default=0)
    HitPointsCurrent = models.IntegerField(default=0)
    ArmorClass = models.IntegerField(default=0)
    AttackBonus = models.CharField(max_length=200, blank=True)
    Damage = models.CharField(max_length=200, blank=True)
    SpecialAbility = models.CharField(max_length=500, blank=True)
    RoundsTotal = models.IntegerField(default=0)
    RoundsRemaining = models.IntegerField(default=0)
    SdrMonsterName = models.CharField(max_length=200, blank=True)  # gancho p/ B3
    CreatedAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-RoundsRemaining', 'CreatedAt')
```
- Migration `0008_charactersummon`.
- Integrar à view `companions(request, pk)`: seção "Invocações Ativas" com grid `repeat(3, 1fr)` de cards (`companions.html`). Endpoint HTMX para criar/editar slot (padrão `_save_repeating_slots`).
- CSS do grid: **anexe ao fim de `static/css/character_sheet.css`** numa seção própria com cabeçalho de comentário (o Agente 1 também anexa CSS aí — minimize sobreposição).
  > **Atenção de merge:** `companions.html` também recebe uma mudança pequena do Agente 1 (Task 11: span de magia de invocação clicável). Mantenha o grid de summons numa seção separada do template para o merge ser simples.
- Testes: `CharacterSummonModelTest` (persiste + ordering `-RoundsRemaining`); `SummonsGridTest` (POST cria 3 → GET renderiza 3 cards).

## B2 (T4.7) — Favoritos ★
- Migration `0009_summon_highlighted`: `Highlighted = BooleanField(default=False)`; `Meta.ordering = ('-Highlighted', '-RoundsRemaining', 'CreatedAt')`.
- View `toggle_summon_highlight(request, pk, summon_id)` (valida dono; `summon.Highlighted = not ...; save(update_fields=['Highlighted'])`; devolve **o partial do grid**, não a página).
- URL `name="toggle-summon-highlight"`. Botão ★/☆ no card com `hx-post` + `hx-target="#summons-grid"`.
- Teste `SummonHighlightToggleTest`: flip + destacado no topo + não-dono 404.

## B3 (T4.8) — Autopreenchimento via SRD
- Confirme o nome real do model em `sdr/models.py` (provável `SdrMonster`/`Monster`) e os campos (hp, ac, attacks, special abilities).
- `summon_search(request)`: `q = GET['q'].strip()`; `len(q) < 2` → `HttpResponse('')`; senão `SdrMonster.objects.using('sdr').filter(name__icontains=q).order_by('name')[:10]` → partial de resultados. URL `name="summon-search"`.
- `create_summon_from_monster(request, pk, monster_id)`: lê o monstro `.using('sdr')`, mapeia para um novo `CharacterSummon` (HP, CA, ataque, dano, habilidade; `SdrMonsterName = monster.name`), devolve o grid atualizado.
- UI: busca com `hx-trigger="keyup changed delay:300ms"` + dropdown de resultados.
- Testes (`TransactionTestCase`, `databases = {'default','sdr'}`): `q=wolf` → ≥1 hit; criar a partir de `monster_id` preenche os campos e persiste `SdrMonsterName`; `len(q)<2` e `q` inexistente → vazio sem 500.

**Commit da Entrega B:** suite inteira verde.

---

# Entrega C — Persistência de estado de jogo (T5.4)

Hoje `CharacterStatus.TotalHitPoints` guarda o total, mas **não há PV atual/temporário nem registro de dano** — o estado de combate se perde entre sessões.

- Migration `0010_status_hitpoints`: adicionar `CurrentHitPoints`, `TemporaryHitPoints` (e opcional `NonlethalDamage`) a `CharacterStatus`.
- UI inline (HTMX) para PV atual/temporário no bloco de combate, com **clamp** (`0 ≤ atual ≤ total`; dano não-letal ≥ 0). Persistência via dispatcher.
- (Opcional, se sobrar tempo) seção simples de **condições/efeitos** persistida.
- Teste `HitPointTrackingTest`: POST altera PV atual; clamp respeitado; persiste no GET.

**Commit da Entrega C:** suite inteira verde.

---

## Critério de aceite (Agent 2)
- [ ] Auditoria de campos deriváveis registrada; ataque melee/ranged, cap de Des por armadura, penalidade de armadura nas perícias, deslocamento por carga, CD de magia e magias bônus **todos derivados automaticamente** e persistidos.
- [ ] `CharacterSummon` completo: grid de 3 colunas, favoritos ★ funcionando, autocomplete SRD preenchendo estatísticas.
- [ ] PV atual/temporário (e dano) persistidos e editáveis com clamp.
- [ ] Funções de cálculo são puras com testes `SimpleTestCase`; suite inteira verde; migrations `0008+` aplicam limpo.
- [ ] Branch `feat/agent2-calc-summons` pronta para merge; sem `dd3esheet/nul` commitado.

Ao terminar, avise o coordenador que a branch está pronta para merge.
