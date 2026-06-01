# AGENT1.md — Sonnet: Popup SDR de Magias (end-to-end) + Autosave universal

Você é o **Agente 1 (Sonnet)**. Trabalhe **isolado em worktree própria**. Seu escopo são duas entregas completas: (A) o **popup de magias com dados do SDR** e (B) **autosave em todos os campos editáveis** da ficha. O Agente 2 cuida de cálculos/invocações/persistência em outra worktree; vocês não compartilham branch — o coordenador faz o merge no fim.

## 0. Setup (uma vez)

```bash
# A partir da raiz do repo (C:\Users\Jarzamendia\git\github\dd3esheet):
git worktree add ../dd3esheet-agent1 -b feat/agent1-popup-autosave feat/sdr-spell-popup
cd ../dd3esheet-agent1
```

Confirme que o container de testes está de pé: `docker ps` deve listar `dd3esheet-web-1`.

## Regras (obrigatórias)

- **TDD:** escreva o teste que falha → implemente → veja passar. Testes na mesma commit da implementação.
- **Testes:** `docker exec dd3esheet-web-1 python manage.py test <alvo> -v 2`. Suite inteira antes de cada commit: `docker exec dd3esheet-web-1 python manage.py test -v 1`.
- **Commits pequenos**, pt-BR (`feat(...)`), **sem** trailer `Co-Authored-By`. Commite só na sua branch.
- **PascalCase** em campos de model; SDR sempre `.using('sdr')`; **sem FK cross-DB**. Arquivos novos UTF-8 sem BOM.
- **Nunca** `git add dd3esheet/nul`. Use `git add <paths específicos>`.
- Você **não** cria migrations (isso é do Agente 2). Se algum teste seu precisar de coluna nova, é sinal de que está fora do escopo — pare e sinalize.

---

# Entrega A — Popup de magias com dados do SDR (Tasks 5–12)

O passo a passo completo (com testes, snippets de código e comandos prontos) está em **`docs/superpowers/plans/2026-05-30-sdr-spell-popup.md`**. As Tasks 1–4 já estão feitas. Execute **Tasks 5 a 12 na ordem**. Resumo do que cada uma entrega e onde mexe:

### Task 5 — Endpoint `spell_detail` + dialog partial
- `character/views.py`: view `spell_detail(request, pk, sdr_id)` (`@login_required`, valida dono via `get_object_or_404(Character, pk=pk, User=request.user)`, busca `SDR_Spell.objects.using('sdr')`).
- `character/urls.py`: rota `name="spell-detail"`.
- Novo `character/templates/character/partials/spell_detail_dialog.html`.
- Testes: dono recebe 200 com conteúdo; `sdr_id` inexistente → 404; estranho → 404; anônimo → 302/401/403.

### Task 6 — `<dialog>` global vazio
- `dd3esheet/templates/main.html`: `<dialog id="spell-detail-dialog" class="spell-detail-dialog"></dialog>` após o bloco de conteúdo.

### Task 7 — CSS de tooltip e dialog
- `static/css/character_sheet.css` (anexar no fim): `.spell-input-wrap`, `.spell-detail-trigger`, `.spell-name-link`, `.spell-tooltip` (hover via CSS puro), `.spell-detail-dialog` + `::backdrop`.
  > **Atenção de merge:** o Agente 2 também anexa CSS (grid de summons) ao fim deste arquivo, em seção própria. Mantenha suas regras agrupadas num bloco com cabeçalho de comentário claro para facilitar a resolução.

### Task 8 — Partial reusável `_spell_tooltip.html`
- Novo `character/templates/character/partials/_spell_tooltip.html` (ficha técnica curta: escola/nível/conjuração/componentes/alcance/duração/save/RM + descrição).

### Task 9 — Autocomplete + tooltip + ícone no Livro de Magias
- `character/views.py`: helpers `_build_sdr_lookup_for_spells` e `_sdr_spell_suggestions`; enriquecer `_spellbook_level_context`/`_spellbook_context` com `sdr_lookup` (por nível) e `sdr_spell_suggestions` (uma vez).
- `character/templatetags/dict_extras.py`: filter `get_item` (criar `__init__.py` na pasta `templatetags` se não existir).
- `partials/spellbook_level_form.html`: `<datalist id="spell-suggestions">`, `.spell-input-wrap` com `data-sdr-id`, botão 📖 (`hx-get` para `spell-detail`, `hx-target="#spell-detail-dialog"`, `onclick="…showModal()"`) e `{% include "_spell_tooltip.html" %}` só quando há `sdr`.
- Testes: magia conhecida renderiza `data-sdr-id`, `spell-detail-trigger` e `spell-tooltip`; homebrew não; datalist renderiza uma vez.

### Task 10 — Domínios de clérigo com tooltip + click
- `character/spellcasting.py`: `domain_spells` passa a devolver `{'level', 'name', 'sdr_id', 'sdr'}` (usa `resolve_spell`).
- `partials/character_spells.html`: `<strong class="spell-name-link" data-sdr-id=…>` como nome + gatilho do modal; inclui tooltip quando há `sdr`.
- Testes: `sdr_id` setado p/ magia conhecida; `None` p/ desconhecida.

### Task 11 — Magias de Invocação (Aliados)
- `character/views.py`: `_summon_nature_rows()` enriquece cada linha com `sdr_id`/`sdr` (via `resolve_spell`).
- `character/templates/character/companions.html`: span clicável + tooltip na coluna de magia de invocação.
  > **Atenção de merge:** o Agente 2 reestrutura `companions.html` (grid de summons, T4.6). Faça sua mudança o mais localizada possível (apenas a célula da magia de invocação) para o merge ser trivial.

### Task 12 — Verificação visual (`/run`)
- Suba a stack, logue com o usuário seed e percorra o checklist visual completo do plano (Livro de Magias, Domínios, Aliados, regressão geral, sem 500 nos logs).

**Commit final da Entrega A:** suite inteira verde.

---

# Entrega B — Autosave em **todos** os campos editáveis

## Problema atual
Todo form editável usa `hx-trigger="change delay:300ms"` + `hx-swap="outerHTML"`. `change` só dispara no **blur**, então a ficha **não salva enquanto se digita**. E como o submit troca o form inteiro (`outerHTML`), disparar em cada tecla destruiria o input em foco (perde cursor/seleção).

## Objetivo
Salvar **enquanto o usuário digita**, em **todos** os campos editáveis (ficha principal e sub-páginas: identidade, descrição, stats, combate, armadura, perícias, armas, equipamento, itens, dinheiro, talentos, especiais, magias, progresso, companions/animal/familiar, reputação contatos/facções/contratos, recursos diários, livro de magias), sem perder foco, mantendo o recálculo de campos derivados.

## Abordagem (recomendada — pode ajustar se descobrir algo melhor durante a implementação)

1. **Separar "persistir" de "re-renderizar".**
   - **Campos textuais puros** (nomes, notas, descrições, páginas, especialização de perícia, etc.): `hx-trigger="input changed delay:500ms"` + `hx-swap="none"`. O servidor persiste e responde **corpo vazio / `204`**; o input mantém foco e cursor.
   - **Campos que alteram derivados** (atributos, BBA, bônus/penalidades de armadura, `Ranks`/`MiscModifier` de perícia, base de saves): manter `change` (com swap) para recalcular e re-renderizar ao sair do campo. Opcionalmente também `input changed delay:700ms` com `hx-swap="none"` para persistir o valor durante a digitação, deixando o recálculo visual para o blur.
2. **Dispatcher (backend).** Garanta que `views.py::character` e as views de sub-página (`companions`, `reputation`, `daily_resources`, `spellbook`) aceitam o POST de autosave e, quando o cliente pede `hx-swap="none"`, persistem e retornam `HttpResponse(status=204)` (ou corpo vazio) **sem** montar o partial. Não quebre o caminho atual (com swap) usado pelos campos derivados.
   > Este é o único ponto de `views.py` que você toca além das funções da Entrega A. O Agente 2 também edita `views.py` (em outras funções) — mantenha sua mudança isolada num ramo claro do dispatcher.
3. **Indicador de estado.** Em `main.html` + CSS, um indicador discreto "salvando… / salvo ✓ / erro" alimentado por `htmx:beforeRequest` / `htmx:afterRequest` / `htmx:responseError` (listener global, como o de CSRF já existente).
4. **CSRF:** o handler `htmx:configRequest` já injeta o token (T0.2); confirme que segue funcionando para os novos requests.

## Cobertura — não deixar nenhum campo de fora
Faça um inventário: liste todos os partials com `hx-trigger` e classifique cada input como "texto puro" ou "afeta derivado". Garanta que **todo** input editável passou a salvar ao digitar (texto) ou ao menos no `change` com persistência durante a digitação (derivados). Registre o inventário no corpo da PR/branch.

## Testes
- `character/tests.py::AutosaveOnInputTest`: POST simulando trigger de `input` (header `HX-Request`, sem swap) persiste o campo e responde 200/204 sem re-renderizar o input.
- `AutosaveCoverageTest`: para cada target editável, um POST de autosave persiste o valor (parametrizado, no espírito do `DispatcherSmokeTest` existente).
- Regressão: campos derivados continuam recalculando no `change` (suite existente verde).
- Smoke manual (`/run`): digitar em "Nome"/"Notas" salva sozinho após ~0,5 s sem perder o cursor; o indicador pisca "salvo ✓".

**Commit final da Entrega B:** suite inteira verde.

---

## Critério de aceite (Agent 1)
- [ ] Popup SDR funcionando nas 3 telas (Livro de Magias, Domínios, Aliados): autocomplete, tooltip ao hover, modal ao clicar; homebrew sem ícone; fallback texto livre preservado.
- [ ] Autosave ao digitar em **todos** os campos editáveis, sem perder foco; derivados recalculam no blur; indicador de salvamento visível.
- [ ] Cobertura de testes nova verde + suite inteira verde.
- [ ] Branch `feat/agent1-popup-autosave` pronta para merge; sem `dd3esheet/nul` commitado.

Ao terminar, avise o coordenador que a branch está pronta para merge.
