# PROMPT.md — Conclusão do trabalho pendente (2 agentes: Sonnet + GPT-5)

Este arquivo contém **prompts prontos para colar** em dois agentes que vão fechar todo o trabalho pendente do `dd3esheet`. Cada prompt é autocontido. Leia primeiro a seção **Regras compartilhadas**.

Trabalho pendente coberto aqui:

1. **Popup SDR de Magias** — Tasks 5–12 do plano `docs/superpowers/plans/2026-05-30-sdr-spell-popup.md` (Tasks 1–4 já feitas).
2. **Fase 4 do `PLAN.md`** — T4.6, T4.7, T4.8 (Invocações / `CharacterSummon`).
3. **Fase 5 do `PLAN.md`** — T5.1 (autosave ao digitar), T5.2/T5.3 (cálculos), T5.4 (persistência de PV).

---

## Regras compartilhadas (valem para os dois agentes)

- **Repo / branch:** trabalhar na branch `feat/sdr-spell-popup`. Não criar branch nova sem combinar. Commits pequenos e atômicos por task/step.
- **Working dir Django:** `dd3esheet/` (subdiretório do repo).
- **Rodar testes (Docker):** o container já roda como `dd3esheet-web-1`. Use:
  ```
  docker exec dd3esheet-web-1 python manage.py test <alvo> -v 2
  ```
  (use `docker exec`, **não** `docker compose exec`). Rode a suíte inteira antes de cada commit final de task: `docker exec dd3esheet-web-1 python manage.py test -v 1`.
- **TDD obrigatório:** escrever o teste que falha → implementar → ver passar. Toda task entrega testes na mesma commit.
- **Convenções do projeto:**
  - **PascalCase** nos campos dos models de `character/` (ex.: `SDRSpellId`, `HitPoints`). Manter.
  - `dnd35.sqlite3` é **read-only**; toda query SDR usa `.using('sdr')`. **Nunca** criar FK cross-DB (`default` ↔ `sdr`); resolver por ID manualmente.
  - Arquivos novos em **UTF-8 sem BOM**.
- **Commits:** **NÃO** adicionar trailer `Co-Authored-By: Claude`. Mensagens em pt-BR seguindo o padrão existente (`feat(...)`, `refactor(...)`).
- **Lixo do Windows:** existe um arquivo órfão `dd3esheet/nul` (nome reservado). **Nunca** dar `git add` nele. Use `git add <paths específicos>` (evite `git add -A`).
- **Coordenação de conflitos:** `character/views.py` é tocado pelos dois — editem **funções distintas** e façam `git pull --rebase` com frequência. Ownership de arquivos com sobreposição está marcado em cada prompt abaixo.
- **Ordem de dependência crítica:** a **Fundação do popup** (Tasks 5, 6, 7, 8) é feita pelo **Sonnet primeiro**. A **Task 11** (GPT-5) depende dela — só começar a Task 11 depois que 5–8 estiverem na branch.

---

## Prompt para o Agente 1 — **Sonnet** (Popup SDR: UI/templates/CSS + autosave frontend)

> Cole tudo abaixo da linha no Sonnet.

---

Você é o Agente 1 (Sonnet). Trabalhe na branch `feat/sdr-spell-popup` do repo `dd3esheet`. Leia a seção "Regras compartilhadas" do `PROMPT.md` antes de começar. Use a sub-skill `superpowers:subagent-driven-development` ou `superpowers:executing-plans`. Faça TDD e commits pequenos, sem trailer `Co-Authored-By`.

**Seu escopo (nesta ordem):**

1. **Fundação do popup SDR — Tasks 5, 6, 7, 8** do plano `docs/superpowers/plans/2026-05-30-sdr-spell-popup.md`. Siga os passos detalhados de cada task no plano (já trazem testes, código e comandos):
   - **Task 5:** view `spell_detail` + URL `character:spell-detail` + partial `spell_detail_dialog.html`.
   - **Task 6:** `<dialog id="spell-detail-dialog">` vazio em `dd3esheet/templates/main.html`.
   - **Task 7:** bloco CSS (`.spell-input-wrap`, `.spell-tooltip`, `.spell-detail-dialog`) em `static/css/character_sheet.css`.
   - **Task 8:** partial reusável `_spell_tooltip.html`.
   > ⚠️ Avise quando 5–8 estiverem commitadas — o Agente 2 depende disso para a Task 11.

2. **Renderização nas telas — Tasks 9 e 10** do mesmo plano:
   - **Task 9:** autocomplete via `<datalist>` + tooltip + ícone 📖 no Livro de Magias (`spellbook_level_form.html`), pré-carga de `sdr_lookup` em `_spellbook_level_context`, e o template tag `get_item` (`character/templatetags/dict_extras.py`).
   - **Task 10:** Domínios de clérigo com tooltip + click em `partials/character_spells.html` (função `domain_spells` em `spellcasting.py`).

3. **Fase 5 — T5.1 (autosave ao digitar), lado frontend.** Detalhes em `PLAN.md` › Fase 5 › T5.1. Você é dono dos **templates de partials editáveis** e do **indicador de salvamento**:
   - Trocar `hx-trigger="change delay:300ms"` por `input changed delay:600ms` + `hx-swap="none"` **apenas nos campos puramente textuais** (nomes, notas, descrições, páginas), preservando foco/cursor.
   - Manter `change` (com swap) nos campos que alteram derivados (atributos, BBA, bônus de armadura, ranks).
   - Indicador "salvando…/salvo ✓" via `htmx:beforeRequest`/`htmx:afterRequest` em `main.html` + CSS.
   - **Coordene com o Agente 2:** ele garante que o dispatcher responde corretamente a saves com `hx-swap="none"` (corpo vazio/204). Combine o contrato antes de mexer.

4. **Task 12 — verificação visual** do plano do popup, via `/run`, **após** o Agente 2 fechar a Task 11. Rode o checklist visual completo (Livro de Magias, Domínios, Aliados, regressão geral).

**Arquivos que você possui:** `templates/main.html`, `static/css/character_sheet.css`, `partials/spell_detail_dialog.html`, `partials/_spell_tooltip.html`, `partials/spellbook_level_form.html`, `partials/character_spells.html`, `character/templatetags/`, e os triggers nos demais partials editáveis. Em `views.py`/`spellcasting.py` edite apenas `spell_detail`, `_spellbook_level_context`/`_spellbook_context` e `domain_spells`.

Ao terminar cada task: suíte inteira verde (`docker exec dd3esheet-web-1 python manage.py test -v 1`) e commit.

---

## Prompt para o Agente 2 — **GPT-5** (Invocações/Summons + cálculos + persistência + autosave backend)

> Cole tudo abaixo da linha no GPT-5.

---

Você é o Agente 2 (GPT-5). Trabalhe na branch `feat/sdr-spell-popup` do repo `dd3esheet`. Leia a seção "Regras compartilhadas" do `PROMPT.md` antes de começar. Faça TDD e commits pequenos, sem trailer `Co-Authored-By`. Lembre: PascalCase nos models, `.using('sdr')` para SDR, sem FK cross-DB, nunca `git add dd3esheet/nul`.

**Seu escopo (sugestão de ordem — itens 1–3 são independentes da Fundação do popup; o item 4 depende dela):**

1. **Invocações — `PLAN.md` Fase 4: T4.6, T4.7, T4.8.** Detalhes completos em `PLAN.md`:
   - **T4.6:** model `CharacterSummon` (PascalCase) + migration (`0008_charactersummon`, confirme o número conforme o estado real das migrations — a última é `0007`), grid de 3 colunas de invocações ativas integrado à página de Aliados (`companions.html`), endpoint HTMX para criar/editar slot.
   - **T4.7:** favoritos ★/☆ (`Highlighted` BooleanField + migration), `toggle_summon_highlight` view + URL, reordenação com destacados no topo.
   - **T4.8:** autopreenchimento via SRD — confirme o nome real do model em `sdr/models.py` (`SdrMonster`/`Monster`), endpoint de busca (`summon_search`) e `create_summon_from_monster`, com `.using('sdr')`.

2. **Cálculos faltantes — Fase 5: T5.2 e T5.3.** Detalhes em `PLAN.md` › Fase 5. Estenda `character/calculations.py` (funções puras) e ligue em `character/views.py::_recalculate_stats` (linhas 488–596) e/ou `spellcasting.py`:
   - **T5.2:** `compute_attack_bonus` (corpo-a-corpo Força / à distância Destreza), `cap_dex_to_armor` (respeitar `MaxDex` da armadura na CA), `armor_check_penalty` nas perícias, `speed_for_load` (deslocamento por carga/armadura).
   - **T5.3:** `compute_spell_save_dc` (10 + nível + mod do atributo-chave) e `bonus_spells_for_ability` (tabela 3.5), persistindo em `CharacterSpellSave`.
   > As puras devem receber primitivos e ter testes `SimpleTestCase` (zero/positivo/negativo). Mantenha persistência atômica com `update_fields`.

3. **Persistência de estado — Fase 5: T5.4.** Detalhes em `PLAN.md`:
   - Passo 1 = **auditoria** (o que é editável na UI mas não persiste, e o que deveria ser rastreado) registrada em `docs/known-issues.md`.
   - Adicionar `CurrentHitPoints`/`TemporaryHitPoints` (e opcional `NonlethalDamage`) em `CharacterStatus` + migration + UI inline com clamp.

4. **Autosave backend — Fase 5: T5.1 (lado servidor).** Garanta que o dispatcher (`views.py::character` e views de sub-página) aceita saves de texto com `hx-swap="none"` e responde corpo vazio/`204` sem re-renderizar o partial. **Combine o contrato com o Agente 1** (ele faz os triggers/indicador no frontend).

5. **Popup — Task 11** do plano `docs/superpowers/plans/2026-05-30-sdr-spell-popup.md`: Magias de Invocação dos Aliados com `sdr_id` + tooltip + click (`_summon_nature_rows` em `views.py`, `companions.html`). **Só começar depois que o Agente 1 commitar as Tasks 5–8** (precisa do endpoint `spell-detail`, do `<dialog>`, do CSS e do partial `_spell_tooltip.html`).
   > Como T4.6 e a Task 11 mexem ambas em `companions.html`, **você é dono desse arquivo** — faça as duas mudanças de forma coerente.

**Arquivos que você possui:** `character/models.py`, `character/migrations/`, `character/calculations.py`, `character/spellcasting.py` (exceto `domain_spells`, do Agente 1), `companions.html`, e em `views.py` as funções de summon/recalc/dispatcher (`_recalculate_stats`, `_summon_nature_rows`, dispatcher, views de summon). `static/css/character_sheet.css` é do Agente 1 — para o grid de summons, **anexe** seu bloco ao fim do arquivo numa seção própria para minimizar conflito.

Ao terminar cada task: suíte inteira verde (`docker exec dd3esheet-web-1 python manage.py test -v 1`) e commit.

---

## Mapa de divisão (resumo)

| Trabalho                                   | Agente 1 (Sonnet)         | Agente 2 (GPT-5)              |
|--------------------------------------------|---------------------------|-------------------------------|
| Popup SDR — Tasks 5,6,7,8 (fundação)       | ✅ (faz primeiro)         | —                             |
| Popup SDR — Tasks 9,10 (Livro/Domínios)    | ✅                        | —                             |
| Popup SDR — Task 11 (Aliados/Invocação)    | —                         | ✅ (após 5–8)                 |
| Popup SDR — Task 12 (verificação visual)   | ✅ (no fim)               | —                             |
| `PLAN.md` T4.6/T4.7/T4.8 (Summons)         | —                         | ✅                            |
| Fase 5 T5.1 autosave — frontend/indicador  | ✅                        | contrato do dispatcher        |
| Fase 5 T5.1 autosave — dispatcher (backend)| triggers/templates        | ✅                            |
| Fase 5 T5.2/T5.3 (cálculos)                | —                         | ✅                            |
| Fase 5 T5.4 (persistência PV)              | —                         | ✅                            |

**Ponto de sincronização único:** Agente 1 entrega Tasks 5–8 → avisa → Agente 2 destrava a Task 11. Tudo o mais roda em paralelo, com rebase frequente em `character/views.py`.
