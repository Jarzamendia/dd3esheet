# PLAN.md — Roadmap do trabalho restante (ambiente de testes online + MVP de jogo)

> Atualizado 2026-06-01. Este arquivo lista **só o que falta**. O detalhamento executável de cada parte está dividido em dois prompts autocontidos:
> - [`AGENT1.md`](AGENT1.md) — **Sonnet**: Popup SDR de Magias (end-to-end) + Autosave em todos os campos editáveis.
> - [`AGENT2.md`](AGENT2.md) — **GPT-5** (trabalho mais complexo): Cálculos automáticos completos + Invocações (`CharacterSummon` + autocomplete SRD) + Persistência de estado de jogo.
>
> Os dois agentes trabalham em **worktrees e branches separadas**; o merge final é feito pelo coordenador (ver "Fluxo de worktrees e merge" no fim).

## Já concluído (não revisitar)

- **Fases 0–3** (deploy/segurança/performance/componentes): 19 tasks, `check --deploy` zero warnings, WhiteNoise, `/healthz`, axes, suite verde. Detalhe histórico no `git log`.
- **Fase 4 — Sprints A/B/C** (UX): T4.1 largura 1280px (`a3e89a3`), T4.2 "Aliados" (`8e71fd2`), T4.3 redesign do nome (`634909e`), T4.4 accordion (`be6b5ab`), T4.5 sub-página Livro de Magias (`e45a15d`).
- **Popup SDR — Tasks 1–4**: `resolve_spell` (`0cd7479`), `import_spells` DRY (`845c94d`), coluna `CharacterSpell.SDRSpellId` + migration `0007` (`ab2ee16`), save hook (`d1d637c`).

---

## O que falta (3 entregas)

### 1. Popup com dados do SDR  → **AGENT1**
Autocomplete (datalist), tooltip ao hover e modal ao clicar para nomes de magia no **Livro de Magias**, **Domínios de clérigo** e **Magias de Invocação**. Tasks 5–12 do plano detalhado [`docs/superpowers/plans/2026-05-30-sdr-spell-popup.md`].

### 2. Autosave em **todos** os campos editáveis  → **AGENT1**
Hoje os forms usam `hx-trigger="change delay:300ms"` (só salva no blur) + `hx-swap="outerHTML"` (recria o form a cada submit). Falta salvar **enquanto o usuário digita**, sem perder foco, em todos os campos editáveis da ficha e sub-páginas.

### 3. Cálculo automático em **todos** os campos deriváveis  → **AGENT2**
`_recalculate_stats` hoje deriva mods de atributo, limites de perícia, CA (total/toque/surpresa), Iniciativa, saves, Agarrar, perícias e carga. Falta: ataque corpo-a-corpo/à distância, cap de `MaxDex` da armadura na CA, penalidade de armadura nas perícias, deslocamento por carga/armadura, CD de magia e magias bônus. Inclui auditoria para não deixar nenhum campo derivável manual.

### 4. Invocações + persistência de estado  → **AGENT2**
- `CharacterSummon` (model + grid 3 colunas + favoritos ★ + autocomplete via SRD `SdrMonster`) — T4.6/T4.7/T4.8.
- Persistência de PV atual/temporário e dano (hoje só `TotalHitPoints`) — T5.4.

---

## Convenções (valem para os dois agentes)

- **Working dir Django:** `dd3esheet/`.
- **Testes (Docker):** `docker exec dd3esheet-web-1 python manage.py test <alvo> -v 2` (use `docker exec`, não `docker compose exec`). Suite inteira antes de cada commit: `docker exec dd3esheet-web-1 python manage.py test -v 1`.
- **TDD obrigatório**, teste falhando antes de implementar; testes na mesma commit.
- **PascalCase** nos campos de models de `character/`. `dnd35.sqlite3` é **read-only**; SDR sempre via `.using('sdr')`; **sem FK cross-DB** (resolver por ID).
- Arquivos novos em **UTF-8 sem BOM**.
- **Commits sem** trailer `Co-Authored-By`. Mensagens pt-BR (`feat(...)`, `refactor(...)`).
- **Nunca** `git add dd3esheet/nul` (arquivo órfão de nome reservado no Windows). Use paths específicos.

---

## Fluxo de worktrees e merge

Base das duas worktrees: HEAD atual de `feat/sdr-spell-popup` (`0fa9f4a` — já contém popup Tasks 1–4 e os planos).

```bash
# Coordenador (uma vez), a partir da raiz do repo:
git worktree add ../dd3esheet-agent1 -b feat/agent1-popup-autosave feat/sdr-spell-popup
git worktree add ../dd3esheet-agent2 -b feat/agent2-calc-summons   feat/sdr-spell-popup
```

- **AGENT1** trabalha em `../dd3esheet-agent1` (branch `feat/agent1-popup-autosave`), seguindo `AGENT1.md`.
- **AGENT2** trabalha em `../dd3esheet-agent2` (branch `feat/agent2-calc-summons`), seguindo `AGENT2.md`.
- Cada um commita só na sua branch; suite verde antes de cada commit.

**Merge final (coordenador):** integrar em `feat/sdr-spell-popup`, na ordem **AGENT2 → AGENT1** (modelos/migrations/cálculos primeiro, UI depois):

```bash
git switch feat/sdr-spell-popup
git merge --no-ff feat/agent2-calc-summons
git merge --no-ff feat/agent1-popup-autosave
docker exec dd3esheet-web-1 python manage.py migrate
docker exec dd3esheet-web-1 python manage.py test -v 1
git worktree remove ../dd3esheet-agent1 && git worktree remove ../dd3esheet-agent2
```

**Hotspots de conflito esperados no merge** (o coordenador resolve):
- `character/views.py` — AGENT1 ajusta o dispatcher (autosave/no-swap) e edita `spell_detail`/`_spellbook_*context`/`domain_spells`; AGENT2 edita `_recalculate_stats`/`_summon_nature_rows`/views de summon. São funções distintas → conflito textual resolúvel.
- `character/templates/character/companions.html` — AGENT1 (Task 11: span de magia clicável) e AGENT2 (T4.6: grid de summons) tocam o arquivo. Combinar as duas mudanças no merge.
- `character/migrations/` — AGENT2 cria `0008+`. AGENT1 não cria migrations. Sem conflito de numeração se AGENT1 não gerar migration.

Critérios de aceite finais em `AGENT1.md` e `AGENT2.md`.
