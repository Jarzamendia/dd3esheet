# Plano: Gerenciador de Iniciativas (`/iniciativa`)

## Contexto

O projeto hoje só tem fichas de personagem (solo-owned) e a referência SDR. Falta uma
ferramenta de **mesa**: um rastreador de combate compartilhado onde o mestre adiciona
jogadores, NPCs e inimigos com suas iniciativas e, durante a luta, mantém ordem de turnos,
dano acumulado, efeitos e anotações. Os jogadores precisam **ver o mesmo estado em tempo real**.

Como o stack é Django puro WSGI (sem Channels/websockets), a sincronização é por
**polling HTMX** (`hx-trigger="every Ns"`) — primeiro caso de polling do projeto.

Decisões confirmadas com o usuário:
- **Combatentes:** só entradas manuais (independentes das fichas de personagem).
- **Acesso:** cada encontro tem um **slug aleatório não-adivinhável**; quem tem o link
  **visualiza sem precisar de login**. O slug funciona como URL-capability.
- **Edição:** **somente o dono (mestre)** edita. Jogadores só visualizam.
- **Sprites:** **ícones SVG dedicados** por tipo (jogador / NPC / inimigo), coloridos.
- **Dano:** o valor central é o **total de dano acumulado que o combatente levou** (contador
  que sobe, com clamp em `>= 0`), não uma barra de HP restante.

A divisão "mestre edita / jogadores fazem polling de uma board read-only" elimina o conflito
de polling sobrescrever o foco de um input sendo digitado: a região com polling é read-only.

## Arquitetura

Novo app Django **`initiative`** (espelha a estrutura do app `sdr`). Models no DB `default`.
Segue AGENTS.md: HTMX + partials, cálculos derivados no backend, campos PascalCase, **TDD**.

### Models (`initiative/models.py`)
- **`Encounter`**: `Owner` (FK User, o mestre), `Name`, `Slug` (token aleatório único,
  `secrets.token_urlsafe(16)` gerado no `save()`), `Round` (default 1), `ActiveCombatant`
  (FK nullable), `UpdatedAt`/`CreatedAt`.
- **`Combatant`**: `Encounter` (FK), `Name`, `Kind` (player/npc/enemy), `Initiative`,
  `DamageTaken` (métrica principal — dano acumulado), `ArmorClass` (opcional), `Effects`,
  `Notes`, `CreatedAt`. `Meta.ordering = ('-Initiative', 'CreatedAt')`.

### Rotas (`initiative/urls.py`, `app_name='initiative'`, incluído sob `iniciativa/`)
| Rota | View | Auth |
|------|------|------|
| `/iniciativa/` | `home` — lista encontros + criar | login |
| `novo` (POST) | `create_encounter` → redirect board | login |
| `<slug>/` | `board` — página do rastreador | público (via slug) |
| `<slug>/fragment` | `board_fragment` — partial p/ polling | público |
| `<slug>/combatente/add` (POST) | `add_combatant` | dono |
| `<slug>/combatente/<cid>/edit` (POST) | `edit_combatant` | dono |
| `<slug>/combatente/<cid>/damage` (POST) | `apply_damage` (delta ±) | dono |
| `<slug>/combatente/<cid>/delete` (POST) | `delete_combatant` | dono |
| `<slug>/turn/next` (POST) | `next_turn` | dono |
| `<slug>/turn/reset` (POST) | `reset_turn` | dono |

### Templates / CSS
- `base_initiative.html` (extends `main.html`), `home.html`, `board.html`.
- `partials/`: `_board_fragment.html`, `_combatant_row.html`, `_combatant_sprite.html`
  (SVG inline por tipo, `currentColor`), `_add_combatant_form.html`.
- `static/css/initiative.css` reusa tokens de `character_sheet.css`; cores por tipo,
  destaque do combatente ativo, contador grande do dano acumulado (`.init-damage`).

### Polling
- **Jogadores (não-donos):** board com `hx-trigger="every 3s"` GET no `fragment`, read-only.
- **Mestre (dono):** sem polling; cada POST devolve a board atualizada.

### Segurança
- Slug = `secrets.token_urlsafe(16)` (~22 chars) ⇒ URL-capability não-adivinhável.
- GET de `board`/`fragment` público por design; POST de edição valida `request.user == Owner`
  (403 caso contrário, redirect p/ login se anônimo).

### Registro
- `INSTALLED_APPS += 'initiative.apps.InitiativeConfig'`; `path('iniciativa/', include(...))`;
  link "Iniciativa" no nav de `templates/main.html`.

## Testes (TDD — `python manage.py test initiative`)
1. `create_encounter` exige login, gera slug único, redireciona p/ board.
2. GET `board`/`fragment` anônimo com slug válido → 200, sem controles de edição.
3. GET com slug inválido → 404.
4. POST de edição por não-dono/anônimo → 403/redirect, nada persistido.
5. `add_combatant` cria e ordena por Initiative.
6. `apply_damage` acumula em `DamageTaken`; clamp `>= 0`; board mostra dano total.
7. `edit_combatant` salva Effects/Notes/campos.
8. `next_turn` avança `ActiveCombatant` e incrementa `Round` ao dar a volta; `reset_turn` reseta.
9. `delete_combatant` remove e reposiciona o ponteiro se era o ativo.
10. Render do sprite muda conforme `Kind`.

## Verificação end-to-end
```bash
docker-compose exec web python manage.py makemigrations initiative
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py test initiative
```
Manual: logar (`jarza`/`P@ssw0rd`), criar encontro em `/iniciativa/`, adicionar combatentes
dos 3 tipos, aplicar dano/efeitos/anotações, avançar turnos; abrir o link compartilhável em
janela anônima e confirmar atualização automática (~3s) e ausência de controles de edição.
