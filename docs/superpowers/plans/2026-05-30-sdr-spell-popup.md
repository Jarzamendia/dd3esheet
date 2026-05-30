# Magias do SDR no input com tooltip + modal — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar autocomplete SDR (com fallback texto livre), tooltip ao hover e modal ao clicar para nomes de magia no Livro de Magias, Domínios de clérigo e Magias de Invocação dos Aliados.

**Architecture:** Coluna nova `SDRSpellId` (nullable `IntegerField`) em `CharacterSpell` ligada ao DB `sdr` por ID, sem FK cross-DB. Save hook HTMX resolve nome → SDR_Spell e grava o ID. Templates pré-renderizam tooltip + ícone só quando há `SDRSpellId`. Modal usa `<dialog>` nativo + 1 linha de JS (`showModal()`) + endpoint HTMX `character:spell-detail`. CSS puro controla hover.

**Tech Stack:** Django 4.2, django-htmx, SQLite (2 DBs: `default` + `sdr`), HTML5 `<datalist>`, HTML5 `<dialog>`, CSS puro.

**Spec:** `docs/superpowers/specs/2026-05-30-sdr-spell-popup-design.md`

---

## File Structure

**Novos arquivos:**
- `dd3esheet/sdr/lookups.py` — função pura `resolve_spell(name) → Optional[SDR_Spell]`
- `dd3esheet/character/templates/character/partials/spell_detail_dialog.html` — partial do conteúdo do modal
- `dd3esheet/character/templates/character/partials/_spell_tooltip.html` — partial reusável do bloco de hover
- `dd3esheet/character/migrations/000X_characterspell_sdrspellid.py` — migration auto-gerada

**Modificados:**
- `dd3esheet/character/models.py` — adiciona `SDRSpellId` em `CharacterSpell`
- `dd3esheet/character/views.py` — view `spell_detail`, save hook em `_save_spellbook_level`, pré-carga `sdr_lookup` em `_spellbook_level_context`/`_spellbook_context`, `_summon_nature_rows` com `sdr_id`
- `dd3esheet/character/urls.py` — rota `character:spell-detail`
- `dd3esheet/character/spellcasting.py` — `domain_spells` inclui `sdr_id`
- `dd3esheet/character/templates/character/partials/spellbook_level_form.html` — wrap, datalist, tooltip, ícone, contexto
- `dd3esheet/character/templates/character/partials/character_spells.html` — span de domínio com `data-sdr-id`
- `dd3esheet/character/templates/character/companions.html` — span de summon spell com `data-sdr-id`
- `dd3esheet/templates/main.html` — `<dialog id="spell-detail-dialog">` vazio
- `dd3esheet/static/css/character_sheet.css` — estilos `.spell-input-wrap`, `.spell-tooltip`, `.spell-name-link`, `.spell-detail-dialog`
- `dd3esheet/sdr/management/commands/import_spells.py` — usar `resolve_spell` (DRY)
- `dd3esheet/character/tests.py` — testes de save hook, view spell_detail e render
- `dd3esheet/sdr/tests.py` — testes de `resolve_spell`

---

## Tarefas

### Task 1: Função pura `sdr.lookups.resolve_spell`

**Files:**
- Create: `dd3esheet/sdr/lookups.py`
- Test: `dd3esheet/sdr/tests.py` (nova classe `ResolveSpellTests`)

- [ ] **Step 1: Escrever os testes que falham**

Adicionar no fim de `dd3esheet/sdr/tests.py`:

```python
class ResolveSpellTests(TestCase):
    databases = {'sdr', 'default'}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connections['sdr'].cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS spell (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    altname TEXT,
                    school TEXT, subschool TEXT, descriptor TEXT,
                    spellcraft_dc TEXT, level TEXT, components TEXT,
                    casting_time TEXT, range TEXT, target TEXT, area TEXT,
                    effect TEXT, duration TEXT, saving_throw TEXT,
                    spell_resistance TEXT, short_description TEXT,
                    to_develop TEXT, material_components TEXT,
                    arcane_material_components TEXT, focus TEXT,
                    description TEXT, xp_cost TEXT,
                    arcane_focus TEXT, wizard_focus TEXT,
                    verbal_components TEXT, sorcerer_focus TEXT,
                    bard_focus TEXT, cleric_focus TEXT, druid_focus TEXT,
                    full_text TEXT, reference TEXT
                );
            """)

    def setUp(self):
        SDR_Spell.objects.using('sdr').all().delete()
        SDR_Spell(name="Magic Missile", altname="Misseis Magicos",
                  school="Evocation", level="Sor/Wiz 1").save(using='sdr')

    def test_match_by_name_case_insensitive(self):
        from sdr.lookups import resolve_spell
        self.assertEqual(resolve_spell("magic missile").name, "Magic Missile")
        self.assertEqual(resolve_spell("MAGIC MISSILE").name, "Magic Missile")

    def test_match_by_altname_when_name_misses(self):
        from sdr.lookups import resolve_spell
        self.assertEqual(resolve_spell("Misseis Magicos").name, "Magic Missile")

    def test_returns_none_for_empty(self):
        from sdr.lookups import resolve_spell
        self.assertIsNone(resolve_spell(""))
        self.assertIsNone(resolve_spell(None))
        self.assertIsNone(resolve_spell("   "))

    def test_returns_none_for_unknown(self):
        from sdr.lookups import resolve_spell
        self.assertIsNone(resolve_spell("Bola de Fogo Tropical"))

    def test_ambiguity_returns_first_by_id(self):
        from sdr.lookups import resolve_spell
        SDR_Spell(name="Magic Missile", school="X").save(using='sdr')
        result = resolve_spell("Magic Missile")
        self.assertEqual(result.school, "Evocation")  # primeira por id
```

- [ ] **Step 2: Rodar testes para verificar que falham**

Run: `docker compose exec web python manage.py test sdr.tests.ResolveSpellTests -v 2`
Expected: 5 erros do tipo `ModuleNotFoundError: No module named 'sdr.lookups'`.

- [ ] **Step 3: Implementar `resolve_spell`**

Criar `dd3esheet/sdr/lookups.py`:

```python
from typing import Optional
from .models import SDR_Spell


def resolve_spell(name: Optional[str]) -> Optional[SDR_Spell]:
    """Resolve um nome de magia para o registro SDR_Spell correspondente.

    Busca primeiro por `name__iexact`, depois por `altname__iexact`.
    Em caso de empate, retorna a primeira por `id`.
    Retorna `None` para string vazia, None ou nome desconhecido.
    """
    if not name or not name.strip():
        return None
    cleaned = name.strip()
    qs = SDR_Spell.objects.using('sdr')
    match = qs.filter(name__iexact=cleaned).order_by('id').first()
    if match is not None:
        return match
    return qs.filter(altname__iexact=cleaned).order_by('id').first()
```

- [ ] **Step 4: Rodar testes para verificar que passam**

Run: `docker compose exec web python manage.py test sdr.tests.ResolveSpellTests -v 2`
Expected: `Ran 5 tests ... OK`.

- [ ] **Step 5: Commit**

```bash
git add dd3esheet/sdr/lookups.py dd3esheet/sdr/tests.py
git commit -m "feat(sdr): resolve_spell por name/altname com fallback None"
```

---

### Task 2: Refatorar `import_spells` para usar `resolve_spell` (DRY)

**Files:**
- Modify: `dd3esheet/sdr/management/commands/import_spells.py:33-50`

- [ ] **Step 1: Verificar teste existente passa antes da mudança**

Run: `docker compose exec web python manage.py test sdr.tests.SDRSpellTests -v 2`
Expected: `Ran 1 test ... OK`.

- [ ] **Step 2: Substituir busca manual por `resolve_spell`**

Em `dd3esheet/sdr/management/commands/import_spells.py`, no topo:

```python
from sdr.lookups import resolve_spell
```

Substituir as linhas 43-50 (bloco `spell_qs = SDR_Spell.objects.using('sdr').none() ...`) por:

```python
            # Prioriza match por altname (nome original em inglês),
            # cai para name (português) — encapsulado em resolve_spell.
            existing = resolve_spell(altname) or resolve_spell(name)
```

E substituir o bloco `if spell_qs.exists(): spell = spell_qs.first()` (linhas 75-82) por:

```python
            if existing is not None:
                for key, val in data.items():
                    setattr(existing, key, val)
                existing.save(using='sdr')
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'Traduzida magia: {altname or name} -> {name}'))
```

(O `else` que cria spell nova permanece igual; só removemos a variável `spell_qs`.)

- [ ] **Step 3: Rodar teste de import para confirmar que segue passando**

Run: `docker compose exec web python manage.py test sdr.tests.SDRSpellTests -v 2`
Expected: `Ran 1 test ... OK`.

- [ ] **Step 4: Commit**

```bash
git add dd3esheet/sdr/management/commands/import_spells.py
git commit -m "refactor(sdr): import_spells usa resolve_spell para DRY"
```

---

### Task 3: Coluna `SDRSpellId` + migration

**Files:**
- Modify: `dd3esheet/character/models.py:248-256`
- Create: `dd3esheet/character/migrations/000X_characterspell_sdrspellid.py` (auto-gerado)

- [ ] **Step 1: Escrever teste do model**

Adicionar em `dd3esheet/character/tests.py`:

```python
class CharacterSpellSDRLinkTests(TestCase):
    databases = {'sdr', 'default'}

    def test_sdr_spell_id_nullable_by_default(self):
        user = make_user()
        char = make_character(user)
        spell = CharacterSpell.objects.create(Character=char, Name="X", Level=1)
        self.assertIsNone(spell.SDRSpellId)

    def test_sdr_spell_id_stores_integer(self):
        user = make_user()
        char = make_character(user)
        spell = CharacterSpell.objects.create(
            Character=char, Name="Magic Missile", Level=1, SDRSpellId=42,
        )
        spell.refresh_from_db()
        self.assertEqual(spell.SDRSpellId, 42)
```

- [ ] **Step 2: Rodar testes para verificar que falham**

Run: `docker compose exec web python manage.py test character.tests.CharacterSpellSDRLinkTests -v 2`
Expected: `TypeError: CharacterSpell() got unexpected keyword arguments: 'SDRSpellId'` ou erro de coluna inexistente.

- [ ] **Step 3: Adicionar coluna no model**

Em `dd3esheet/character/models.py`, na classe `CharacterSpell` (linhas 248-256), adicionar antes do `def __str__`:

```python
    SDRSpellId = models.IntegerField(null=True, blank=True, db_index=True)
```

Estado final esperado da classe:

```python
class CharacterSpell(models.Model):
    Character = models.ForeignKey(Character, on_delete=models.CASCADE)

    Name      = models.CharField(max_length=200, null=True, blank=True)
    Page      = models.CharField(max_length=200, null=True, blank=True)
    Level     = models.IntegerField(default=0, null=True, blank=True)
    SDRSpellId = models.IntegerField(null=True, blank=True, db_index=True)

    def __str__(self):
        return self.Name
```

- [ ] **Step 4: Gerar e aplicar a migration**

Run: `docker compose exec web python manage.py makemigrations character`
Expected: `Migrations for 'character': 000X_characterspell_sdrspellid.py - Add field SDRSpellId to characterspell`.

Run: `docker compose exec web python manage.py migrate`
Expected: aplica a migration sem erros.

- [ ] **Step 5: Rodar testes para verificar que passam**

Run: `docker compose exec web python manage.py test character.tests.CharacterSpellSDRLinkTests -v 2`
Expected: `Ran 2 tests ... OK`.

- [ ] **Step 6: Commit**

```bash
git add dd3esheet/character/models.py dd3esheet/character/migrations/ dd3esheet/character/tests.py
git commit -m "feat(character): coluna SDRSpellId em CharacterSpell"
```

---

### Task 4: Save hook em `_save_spellbook_level` resolve nome → SDR_Spell

**Files:**
- Modify: `dd3esheet/character/views.py:190-226` (função `_save_spellbook_level`)
- Test: `dd3esheet/character/tests.py`

- [ ] **Step 1: Escrever testes que falham**

Adicionar em `dd3esheet/character/tests.py`. Antes, ler topo do arquivo para confirmar que `from .models import CharacterSpell` está lá. Em seguida:

```python
class SpellbookSDRResolveTests(TestCase):
    databases = {'sdr', 'default'}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connections['sdr'].cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS spell (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL, altname TEXT,
                    school TEXT, subschool TEXT, descriptor TEXT,
                    spellcraft_dc TEXT, level TEXT, components TEXT,
                    casting_time TEXT, range TEXT, target TEXT, area TEXT,
                    effect TEXT, duration TEXT, saving_throw TEXT,
                    spell_resistance TEXT, short_description TEXT,
                    to_develop TEXT, material_components TEXT,
                    arcane_material_components TEXT, focus TEXT,
                    description TEXT, xp_cost TEXT,
                    arcane_focus TEXT, wizard_focus TEXT,
                    verbal_components TEXT, sorcerer_focus TEXT,
                    bard_focus TEXT, cleric_focus TEXT, druid_focus TEXT,
                    full_text TEXT, reference TEXT
                );
            """)

    def setUp(self):
        from sdr.models import SDR_Spell
        SDR_Spell.objects.using('sdr').all().delete()
        self.sdr_mm = SDR_Spell(
            name="Magic Missile", altname="Misseis Magicos",
            school="Evocation", level="Sor/Wiz 1",
            short_description="1 missil mais 1 a cada dois niveis",
        )
        self.sdr_mm.save(using='sdr')
        self.user = make_user()
        self.user.set_password('pw')
        self.user.save()
        self.char = make_character(self.user)
        self.client.login(username=self.user.username, password='pw')

    def _post_level(self, level, rows):
        data = {}
        for i, (name, page) in enumerate(rows, start=1):
            data[f'spellbook_{level}_{i}_Name'] = name
            data[f'spellbook_{level}_{i}_Page'] = page
        return self.client.post(
            reverse('character:spellbook', args=[self.char.pk]),
            data=data,
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET=f'spellbookLevel{level}Form',
        )

    def test_save_resolves_sdr_id_for_known_spell(self):
        self._post_level(1, [("Magic Missile", "12")])
        spell = CharacterSpell.objects.get(Character=self.char, Level=1)
        self.assertEqual(spell.SDRSpellId, self.sdr_mm.id)

    def test_save_resolves_sdr_id_by_altname(self):
        self._post_level(1, [("Misseis Magicos", "")])
        spell = CharacterSpell.objects.get(Character=self.char, Level=1)
        self.assertEqual(spell.SDRSpellId, self.sdr_mm.id)

    def test_save_leaves_sdr_id_none_for_homebrew(self):
        self._post_level(1, [("Bola de Fogo Tropical", "")])
        spell = CharacterSpell.objects.get(Character=self.char, Level=1)
        self.assertIsNone(spell.SDRSpellId)

    def test_save_clears_sdr_id_when_switching_to_homebrew(self):
        self._post_level(1, [("Magic Missile", "")])
        self._post_level(1, [("Bola de Fogo Tropical", "")])
        spell = CharacterSpell.objects.get(Character=self.char, Level=1)
        self.assertIsNone(spell.SDRSpellId)
```

- [ ] **Step 2: Rodar testes para verificar que falham**

Run: `docker compose exec web python manage.py test character.tests.SpellbookSDRResolveTests -v 2`
Expected: 4 falhas — `SDRSpellId` permanece `None` em todos os casos (save hook ainda não setou).

- [ ] **Step 3: Aplicar o save hook**

Em `dd3esheet/character/views.py`, no topo do arquivo, adicionar import:

```python
from sdr.lookups import resolve_spell
```

Em `_save_spellbook_level` (linha 190), modificar o trecho que salva o item. Substituir as linhas 219-224 (criação/atualização do item):

```python
        if item is None:
            item = CharacterSpell(Character=character)
        item.Level = level
        item.Name = name
        item.Page = page
        item.save()
```

por:

```python
        if item is None:
            item = CharacterSpell(Character=character)
        item.Level = level
        item.Name = name
        item.Page = page
        matched = resolve_spell(name)
        item.SDRSpellId = matched.id if matched else None
        item.save()
```

- [ ] **Step 4: Rodar testes para verificar que passam**

Run: `docker compose exec web python manage.py test character.tests.SpellbookSDRResolveTests -v 2`
Expected: `Ran 4 tests ... OK`.

- [ ] **Step 5: Rodar suíte do character para garantir que nada quebrou**

Run: `docker compose exec web python manage.py test character -v 1`
Expected: tudo verde.

- [ ] **Step 6: Commit**

```bash
git add dd3esheet/character/views.py dd3esheet/character/tests.py
git commit -m "feat(character): save hook resolve SDRSpellId no Livro de Magias"
```

---

### Task 5: View `spell_detail` + URL + template do dialog

**Files:**
- Modify: `dd3esheet/character/views.py` (adicionar `spell_detail`)
- Modify: `dd3esheet/character/urls.py` (adicionar rota)
- Create: `dd3esheet/character/templates/character/partials/spell_detail_dialog.html`
- Test: `dd3esheet/character/tests.py`

- [ ] **Step 1: Escrever testes que falham**

Adicionar em `dd3esheet/character/tests.py`:

```python
class SpellDetailViewTests(TestCase):
    databases = {'sdr', 'default'}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # mesma criação da tabela 'spell' usada em SpellbookSDRResolveTests
        with connections['sdr'].cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS spell (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL, altname TEXT,
                    school TEXT, subschool TEXT, descriptor TEXT,
                    spellcraft_dc TEXT, level TEXT, components TEXT,
                    casting_time TEXT, range TEXT, target TEXT, area TEXT,
                    effect TEXT, duration TEXT, saving_throw TEXT,
                    spell_resistance TEXT, short_description TEXT,
                    to_develop TEXT, material_components TEXT,
                    arcane_material_components TEXT, focus TEXT,
                    description TEXT, xp_cost TEXT,
                    arcane_focus TEXT, wizard_focus TEXT,
                    verbal_components TEXT, sorcerer_focus TEXT,
                    bard_focus TEXT, cleric_focus TEXT, druid_focus TEXT,
                    full_text TEXT, reference TEXT
                );
            """)

    def setUp(self):
        from sdr.models import SDR_Spell
        SDR_Spell.objects.using('sdr').all().delete()
        self.spell = SDR_Spell(
            name="Magic Missile",
            full_text="<p>Conjuras misseis magicos.</p>",
            school="Evocation", level="Sor/Wiz 1",
        )
        self.spell.save(using='sdr')
        self.owner = make_user('owner')
        self.owner.set_password('pw'); self.owner.save()
        self.stranger = make_user('stranger')
        self.stranger.set_password('pw'); self.stranger.save()
        self.char = make_character(self.owner)

    def test_owner_gets_dialog_partial(self):
        self.client.login(username='owner', password='pw')
        url = reverse('character:spell-detail', args=[self.char.pk, self.spell.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Magic Missile', resp.content)
        self.assertIn(b'Conjuras misseis magicos', resp.content)

    def test_unknown_sdr_id_returns_404(self):
        self.client.login(username='owner', password='pw')
        url = reverse('character:spell-detail', args=[self.char.pk, 99999])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_stranger_gets_404(self):
        self.client.login(username='stranger', password='pw')
        url = reverse('character:spell-detail', args=[self.char.pk, self.spell.id])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_anonymous_redirected_or_blocked(self):
        url = reverse('character:spell-detail', args=[self.char.pk, self.spell.id])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, (302, 401, 403))
```

- [ ] **Step 2: Rodar testes para verificar que falham**

Run: `docker compose exec web python manage.py test character.tests.SpellDetailViewTests -v 2`
Expected: `NoReverseMatch: 'spell-detail' is not a registered namespace`.

- [ ] **Step 3: Criar o template do dialog**

Criar `dd3esheet/character/templates/character/partials/spell_detail_dialog.html`:

```html
<article class="spell-detail">
    <header class="spell-detail-head">
        <div>
            <h2>{{ spell.name }}</h2>
            {% if spell.altname %}<p class="spell-detail-altname">{{ spell.altname }}</p>{% endif %}
        </div>
        <form method="dialog" class="spell-detail-close-form">
            <button type="submit" class="spell-detail-close" aria-label="Fechar">×</button>
        </form>
    </header>
    <div class="spell-detail-body">
        {% if spell.full_text %}
            {{ spell.full_text|safe }}
        {% else %}
            <p><strong>{{ spell.school }}{% if spell.level %} — Nv {{ spell.level }}{% endif %}</strong></p>
            {% if spell.short_description %}<p>{{ spell.short_description }}</p>{% endif %}
            {% if spell.description %}<div>{{ spell.description|safe }}</div>{% endif %}
        {% endif %}
    </div>
</article>
```

- [ ] **Step 4: Adicionar a view**

Em `dd3esheet/character/views.py`, no topo, garantir import:

```python
from sdr.models import SDR_Spell
```

(Se já não existir.) Adicionar a view no fim do arquivo:

```python
@login_required
def spell_detail(request, pk, sdr_id):
    get_object_or_404(Character, pk=pk, User=request.user)
    spell = get_object_or_404(SDR_Spell.objects.using('sdr'), id=sdr_id)
    return render(request, 'character/partials/spell_detail_dialog.html', {'spell': spell})
```

- [ ] **Step 5: Registrar a URL**

Em `dd3esheet/character/urls.py`, adicionar antes de `create-character`:

```python
    path("character/<int:pk>/spell/<int:sdr_id>/", views.spell_detail, name="spell-detail"),
```

- [ ] **Step 6: Rodar testes para verificar que passam**

Run: `docker compose exec web python manage.py test character.tests.SpellDetailViewTests -v 2`
Expected: `Ran 4 tests ... OK`.

- [ ] **Step 7: Commit**

```bash
git add dd3esheet/character/views.py dd3esheet/character/urls.py \
        dd3esheet/character/templates/character/partials/spell_detail_dialog.html \
        dd3esheet/character/tests.py
git commit -m "feat(character): endpoint spell_detail devolve dialog partial"
```

---

### Task 6: `<dialog>` vazio em main.html

**Files:**
- Modify: `dd3esheet/templates/main.html` (após `{% block content %}{% endblock %}`)

- [ ] **Step 1: Adicionar dialog vazio**

Em `dd3esheet/templates/main.html`, logo após a linha `{% block content %}{% endblock %}` (linha 55):

```html
    <dialog id="spell-detail-dialog" class="spell-detail-dialog"></dialog>
```

- [ ] **Step 2: Rodar a suíte completa para confirmar que nada quebra**

Run: `docker compose exec web python manage.py test -v 1`
Expected: tudo verde (essa mudança é só HTML estrutural sem efeito ativo).

- [ ] **Step 3: Commit**

```bash
git add dd3esheet/templates/main.html
git commit -m "feat(ui): <dialog> global para detalhe de magia"
```

---

### Task 7: CSS — wrap, tooltip e dialog

**Files:**
- Modify: `dd3esheet/static/css/character_sheet.css` (fim do arquivo)

- [ ] **Step 1: Adicionar bloco CSS no fim do arquivo**

Em `dd3esheet/static/css/character_sheet.css`, anexar no fim:

```css
/* ============================================================
   Magia SDR — wrap, tooltip ao hover e dialog ao clicar
   ============================================================ */
.spell-input-wrap {
    position: relative;
    display: flex;
    align-items: center;
    gap: 4px;
    min-width: 0;
}
.spell-input-wrap .sheet-input {
    flex: 1 1 auto;
    min-width: 0;
}
.spell-detail-trigger {
    flex: 0 0 auto;
    background: none;
    border: 1px solid var(--rule-line);
    border-radius: 3px;
    padding: 0 6px;
    font-size: 12px;
    line-height: 22px;
    cursor: pointer;
    color: var(--ink);
}
.spell-detail-trigger:hover { background: var(--header-bg); color: var(--header-fg); }

.spell-name-link[data-sdr-id]:not([data-sdr-id=""]) {
    position: relative;
    cursor: pointer;
    text-decoration: underline dotted;
}

.spell-tooltip {
    display: none;
    position: absolute;
    z-index: 200;
    top: 100%;
    left: 0;
    width: 320px;
    max-width: 90vw;
    margin-top: 4px;
    padding: 10px 12px;
    background: var(--paper-bg, #fff);
    border: 1px solid var(--rule-line, #333);
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.18);
    font-family: var(--font-body);
    font-size: 12px;
    line-height: 1.4;
    color: var(--ink, #111);
    pointer-events: none;
}
.spell-tooltip dl { margin: 0; display: grid; grid-template-columns: auto 1fr; gap: 2px 8px; }
.spell-tooltip dt { font-weight: 700; }
.spell-tooltip dd { margin: 0; }
.spell-tooltip .spell-tooltip-school {
    display: block;
    font-weight: 700;
    margin-bottom: 4px;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.spell-tooltip .spell-tooltip-desc {
    margin-top: 6px;
    font-style: italic;
}
.spell-input-wrap[data-sdr-id]:not([data-sdr-id=""]):hover .spell-tooltip,
.spell-name-link[data-sdr-id]:not([data-sdr-id=""]):hover .spell-tooltip {
    display: block;
}

.spell-detail-dialog {
    width: min(720px, 92vw);
    max-height: 88vh;
    padding: 0;
    border: 1px solid var(--rule-line, #333);
    background: var(--paper-bg, #fff);
    color: var(--ink, #111);
}
.spell-detail-dialog::backdrop { background: rgba(0, 0, 0, 0.5); }
.spell-detail { display: flex; flex-direction: column; max-height: 88vh; }
.spell-detail-head {
    display: flex; align-items: flex-start; justify-content: space-between;
    padding: 12px 16px; border-bottom: 1px solid var(--rule-line, #333);
    background: var(--header-bg, #222); color: var(--header-fg, #fff);
}
.spell-detail-head h2 { margin: 0; font-size: 16px; }
.spell-detail-altname { margin: 2px 0 0; font-size: 11px; opacity: 0.85; }
.spell-detail-close-form { margin: 0; }
.spell-detail-close {
    background: none; border: 0; color: inherit; font-size: 22px;
    line-height: 1; cursor: pointer; padding: 0 6px;
}
.spell-detail-body { padding: 14px 16px; overflow-y: auto; font-size: 13px; line-height: 1.5; }
```

- [ ] **Step 2: Rodar a suíte (CSS é texto inerte)**

Run: `docker compose exec web python manage.py test -v 1`
Expected: tudo verde.

- [ ] **Step 3: Commit**

```bash
git add dd3esheet/static/css/character_sheet.css
git commit -m "feat(ui): CSS de tooltip hover e dialog para magia SDR"
```

---

### Task 8: Partial `_spell_tooltip.html` (reusável)

**Files:**
- Create: `dd3esheet/character/templates/character/partials/_spell_tooltip.html`

- [ ] **Step 1: Criar o partial**

Criar `dd3esheet/character/templates/character/partials/_spell_tooltip.html`:

```html
{% comment %}
Renderiza um <aside class="spell-tooltip"> com a ficha técnica curta.
Espera no contexto:
  - sdr: instância de SDR_Spell (não vazia)
{% endcomment %}
<aside class="spell-tooltip" role="tooltip">
    <span class="spell-tooltip-school">
        {{ sdr.school|default:"" }}{% if sdr.level %} — Nv {{ sdr.level }}{% endif %}
    </span>
    <dl>
        {% if sdr.casting_time %}<dt>Conjuração</dt><dd>{{ sdr.casting_time }}</dd>{% endif %}
        {% if sdr.components %}<dt>Componentes</dt><dd>{{ sdr.components }}</dd>{% endif %}
        {% if sdr.range %}<dt>Alcance</dt><dd>{{ sdr.range }}</dd>{% endif %}
        {% if sdr.target %}<dt>Alvo</dt><dd>{{ sdr.target }}</dd>{% endif %}
        {% if sdr.area %}<dt>Área</dt><dd>{{ sdr.area }}</dd>{% endif %}
        {% if sdr.duration %}<dt>Duração</dt><dd>{{ sdr.duration }}</dd>{% endif %}
        {% if sdr.saving_throw %}<dt>Resistência</dt><dd>{{ sdr.saving_throw }}</dd>{% endif %}
        {% if sdr.spell_resistance %}<dt>RM</dt><dd>{{ sdr.spell_resistance }}</dd>{% endif %}
    </dl>
    {% if sdr.short_description %}
        <p class="spell-tooltip-desc">{{ sdr.short_description }}</p>
    {% endif %}
</aside>
```

- [ ] **Step 2: Commit (mudança isolada, sem teste — só será exercitado pelos próximos)**

```bash
git add dd3esheet/character/templates/character/partials/_spell_tooltip.html
git commit -m "feat(ui): partial _spell_tooltip com ficha técnica curta"
```

---

### Task 9: Pré-carga `sdr_lookup` + wrap/datalist/tooltip/ícone no `spellbook_level_form.html`

**Files:**
- Modify: `dd3esheet/character/views.py` (`_spellbook_level_context`, `_spellbook_context`)
- Modify: `dd3esheet/character/templates/character/partials/spellbook_level_form.html`
- Test: `dd3esheet/character/tests.py`

- [ ] **Step 1: Escrever testes que falham (render)**

Adicionar em `dd3esheet/character/tests.py`:

```python
class SpellbookLevelRenderTests(TestCase):
    databases = {'sdr', 'default'}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connections['sdr'].cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS spell (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL, altname TEXT,
                    school TEXT, subschool TEXT, descriptor TEXT,
                    spellcraft_dc TEXT, level TEXT, components TEXT,
                    casting_time TEXT, range TEXT, target TEXT, area TEXT,
                    effect TEXT, duration TEXT, saving_throw TEXT,
                    spell_resistance TEXT, short_description TEXT,
                    to_develop TEXT, material_components TEXT,
                    arcane_material_components TEXT, focus TEXT,
                    description TEXT, xp_cost TEXT,
                    arcane_focus TEXT, wizard_focus TEXT,
                    verbal_components TEXT, sorcerer_focus TEXT,
                    bard_focus TEXT, cleric_focus TEXT, druid_focus TEXT,
                    full_text TEXT, reference TEXT
                );
            """)

    def setUp(self):
        from sdr.models import SDR_Spell
        SDR_Spell.objects.using('sdr').all().delete()
        self.sdr_mm = SDR_Spell(
            name="Magic Missile", school="Evocation", level="Sor/Wiz 1",
            casting_time="1 ação padrão",
            short_description="1 missil mais 1 a cada 2 niveis",
        )
        self.sdr_mm.save(using='sdr')
        self.user = make_user(); self.user.set_password('pw'); self.user.save()
        self.char = make_character(self.user)
        self.client.login(username=self.user.username, password='pw')

    def test_known_spell_renders_data_sdr_id_and_trigger(self):
        CharacterSpell.objects.create(
            Character=self.char, Name="Magic Missile", Level=1, SDRSpellId=self.sdr_mm.id,
        )
        url = reverse('character:spellbook', args=[self.char.pk])
        resp = self.client.get(url)
        body = resp.content.decode()
        self.assertIn(f'data-sdr-id="{self.sdr_mm.id}"', body)
        self.assertIn('class="spell-detail-trigger"', body)
        self.assertIn('class="spell-tooltip"', body)
        self.assertIn('1 missil mais 1 a cada 2 niveis', body)

    def test_homebrew_spell_renders_without_sdr_attrs(self):
        CharacterSpell.objects.create(
            Character=self.char, Name="Bola Tropical", Level=1, SDRSpellId=None,
        )
        url = reverse('character:spellbook', args=[self.char.pk])
        body = self.client.get(url).content.decode()
        self.assertNotIn('spell-detail-trigger', body)
        # wrap existe, mas sem data-sdr-id (ou com data-sdr-id vazio)
        self.assertNotIn('class="spell-tooltip"', body)

    def test_datalist_is_rendered_once(self):
        url = reverse('character:spellbook', args=[self.char.pk])
        body = self.client.get(url).content.decode()
        self.assertEqual(body.count('id="spell-suggestions"'), 1)
        # Magia do SDR aparece como option
        self.assertIn('value="Magic Missile"', body)
```

- [ ] **Step 2: Rodar testes para verificar que falham**

Run: `docker compose exec web python manage.py test character.tests.SpellbookLevelRenderTests -v 2`
Expected: 3 falhas (assertions sobre `spell-detail-trigger`, `data-sdr-id`, `spell-suggestions`).

- [ ] **Step 3: Pré-carga no contexto**

Em `dd3esheet/character/views.py`, no topo, garantir imports:

```python
from sdr.models import SDR_Spell
```

Modificar `_spellbook_level_context` (linha 275). Estado final:

```python
def _spellbook_level_context(char, level, spellcasting=None):
    if spellcasting is None:
        spellcasting = spellcasting_context(char)
    spells = _spellbook_level_rows(char, level)
    sdr_lookup = _build_sdr_lookup_for_spells(spells)
    return {
        'character': char,
        'spellcasting': spellcasting,
        'spellbook_profile_fields': _SPELLBOOK_PROFILE_FIELDS,
        'spellbook_level': {
            'level': level,
            'target': f'spellbookLevel{level}Form',
            'form_id': f'spellbookLevel{level}Form',
            'spells': spells,
            'count': sum(1 for s in spells if s and (s.Name or s.Page)),
            'sdr_lookup': sdr_lookup,
        },
        'sdr_spell_suggestions': _sdr_spell_suggestions(),
    }
```

(Mantenha quaisquer outras chaves do dict atual; só estamos adicionando `sdr_lookup` dentro de `spellbook_level` e `sdr_spell_suggestions` no top-level. Releia a função atual e adicione sem remover nada existente.)

Adicionar helpers no mesmo arquivo, antes de `_spellbook_level_context`:

```python
def _build_sdr_lookup_for_spells(spells):
    ids = {s.SDRSpellId for s in spells if s and s.SDRSpellId}
    if not ids:
        return {}
    return {
        sdr.id: sdr
        for sdr in SDR_Spell.objects.using('sdr').filter(id__in=ids)
    }


def _sdr_spell_suggestions():
    return list(
        SDR_Spell.objects.using('sdr').only('id', 'name', 'school', 'level').order_by('name')
    )
```

Em `_spellbook_context` (linha 350), garantir que cada `spellbook_levels[i]` também inclua `sdr_lookup` — a list-comp atual chama `_spellbook_level_context`, então só precisamos colher o dict `spellbook_level` já enriquecido. Verifique a list-comp e ajuste se necessário (deve continuar funcionando sem mudança porque pegamos o sub-dict).

Adicionar também `sdr_spell_suggestions` no `_spellbook_context` (uma vez, top-level):

```python
    context['sdr_spell_suggestions'] = _sdr_spell_suggestions()
```

(Cuide para não duplicar em cada nível.)

- [ ] **Step 4: Atualizar template `spellbook_level_form.html`**

Substituir o conteúdo de `dd3esheet/character/templates/character/partials/spellbook_level_form.html` por:

```html
<details class="spellbook-level" {% if spellbook_level.level == 0 %}open{% endif %}>
    <summary class="spellbook-level-summary">
        <span>Magias de nivel {{ spellbook_level.level }}</span>
        <strong>{{ spellbook_level.count }}</strong>
    </summary>
    <form id="{{ spellbook_level.form_id }}"
          class="spellbook-level-form"
          hx-post="{% url 'character:spellbook' character.pk %}"
          hx-target="#{{ spellbook_level.form_id }}"
          hx-swap="outerHTML"
          hx-trigger="change delay:300ms">
        {% csrf_token %}
        <div class="spellbook-level-grid" data-sheet-table="spellbook-level-{{ spellbook_level.level }}">
            <div class="spellbook-head">Livro</div>
            <div class="spellbook-head">Magia</div>
            {% for spell in spellbook_level.spells %}
                <input class="sheet-input spellbook-page-input"
                       name="spellbook_{{ spellbook_level.level }}_{{ forloop.counter }}_Page"
                       value="{{ spell.Page|default:'' }}"
                       data-field="spellbook.Page" data-slot="{{ forloop.counter }}">
                {% with sdr=spellbook_level.sdr_lookup|get_item:spell.SDRSpellId %}
                <span class="spell-input-wrap"
                      data-sdr-id="{% if sdr %}{{ sdr.id }}{% endif %}">
                    <input class="sheet-input spellbook-name-input"
                           list="spell-suggestions"
                           name="spellbook_{{ spellbook_level.level }}_{{ forloop.counter }}_Name"
                           value="{{ spell.Name|default:'' }}"
                           data-field="spellbook.Name" data-slot="{{ forloop.counter }}">
                    {% if sdr %}
                        <button type="button"
                                class="spell-detail-trigger"
                                title="Ver detalhe completo"
                                hx-get="{% url 'character:spell-detail' character.pk sdr.id %}"
                                hx-target="#spell-detail-dialog"
                                hx-swap="innerHTML"
                                onclick="document.getElementById('spell-detail-dialog').showModal()">📖</button>
                        {% include "character/partials/_spell_tooltip.html" %}
                    {% endif %}
                </span>
                {% endwith %}
            {% endfor %}
        </div>
    </form>
</details>

{% if sdr_spell_suggestions %}
<datalist id="spell-suggestions">
    {% for s in sdr_spell_suggestions %}
        <option value="{{ s.name }}">{{ s.school }}{% if s.level %} — Nv {{ s.level }}{% endif %}</option>
    {% endfor %}
</datalist>
{% endif %}
```

- [ ] **Step 5: Criar o template filter `get_item`**

O template usa `spellbook_level.sdr_lookup|get_item:spell.SDRSpellId`. Esse filter não existe nativamente no Django. Verificar primeiro se já existe um filter custom no projeto:

Run: `Grep -n "register.filter" dd3esheet/character/templatetags/ 2>/dev/null || echo "no templatetags"`

Se a pasta `templatetags` não existir, criar:

`dd3esheet/character/templatetags/__init__.py` (vazio).

`dd3esheet/character/templatetags/dict_extras.py`:

```python
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Permite `mydict|get_item:variable` em templates."""
    if not dictionary:
        return None
    return dictionary.get(key)
```

No topo de `spellbook_level_form.html` (linha 1) adicionar:

```
{% load dict_extras %}
```

E também em `spellbook.html` (página inteira) se o partial for renderizado lá direto — verificar e ajustar conforme necessário.

- [ ] **Step 6: Rodar testes para verificar que passam**

Run: `docker compose exec web python manage.py test character.tests.SpellbookLevelRenderTests -v 2`
Expected: `Ran 3 tests ... OK`.

- [ ] **Step 7: Rodar suíte inteira**

Run: `docker compose exec web python manage.py test -v 1`
Expected: tudo verde.

- [ ] **Step 8: Commit**

```bash
git add dd3esheet/character/views.py \
        dd3esheet/character/templates/character/partials/spellbook_level_form.html \
        dd3esheet/character/templatetags/ \
        dd3esheet/character/tests.py
git commit -m "feat(ui): autocomplete SDR + tooltip + trigger no Livro de Magias"
```

---

### Task 10: Domínios de clérigo com `sdr_id` + tooltip/click

**Files:**
- Modify: `dd3esheet/character/spellcasting.py` (função `domain_spells`)
- Modify: `dd3esheet/character/templates/character/partials/character_spells.html` (bloco de domínios, linhas ~31-34 e ~39-42)
- Test: `dd3esheet/character/tests.py`

- [ ] **Step 1: Escrever teste do `domain_spells`**

Adicionar em `dd3esheet/character/tests.py`:

```python
class DomainSpellsResolveTests(TestCase):
    databases = {'sdr', 'default'}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connections['sdr'].cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS spell (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL, altname TEXT, school TEXT,
                    subschool TEXT, descriptor TEXT, spellcraft_dc TEXT,
                    level TEXT, components TEXT, casting_time TEXT,
                    range TEXT, target TEXT, area TEXT, effect TEXT,
                    duration TEXT, saving_throw TEXT, spell_resistance TEXT,
                    short_description TEXT, to_develop TEXT,
                    material_components TEXT, arcane_material_components TEXT,
                    focus TEXT, description TEXT, xp_cost TEXT,
                    arcane_focus TEXT, wizard_focus TEXT, verbal_components TEXT,
                    sorcerer_focus TEXT, bard_focus TEXT, cleric_focus TEXT,
                    druid_focus TEXT, full_text TEXT, reference TEXT
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS domain (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    granted_power TEXT,
                    spell_1 TEXT, spell_2 TEXT, spell_3 TEXT, spell_4 TEXT,
                    spell_5 TEXT, spell_6 TEXT, spell_7 TEXT, spell_8 TEXT, spell_9 TEXT,
                    reference TEXT
                );
            """)

    def test_domain_spells_includes_sdr_id_when_known(self):
        from sdr.models import SDR_Spell, SDR_Domain
        from character.spellcasting import domain_spells
        SDR_Spell.objects.using('sdr').all().delete()
        SDR_Domain.objects.using('sdr').all().delete()
        sdr = SDR_Spell(name="Bless", school="Enchantment", level="Clr 1")
        sdr.save(using='sdr')
        d = SDR_Domain(name="Good", spell_1="Bless")
        d.save(using='sdr')
        rows = domain_spells("Good")
        # Encontra entrada de nível 1 com sdr_id setado
        row1 = next(r for r in rows if r['level'] == 1)
        self.assertEqual(row1['name'], "Bless")
        self.assertEqual(row1['sdr_id'], sdr.id)

    def test_domain_spells_sdr_id_none_when_unknown(self):
        from sdr.models import SDR_Spell, SDR_Domain
        from character.spellcasting import domain_spells
        SDR_Spell.objects.using('sdr').all().delete()
        SDR_Domain.objects.using('sdr').all().delete()
        d = SDR_Domain(name="Custom", spell_1="Homebrew Spell")
        d.save(using='sdr')
        rows = domain_spells("Custom")
        row1 = next(r for r in rows if r['level'] == 1)
        self.assertEqual(row1['name'], "Homebrew Spell")
        self.assertIsNone(row1['sdr_id'])
```

- [ ] **Step 2: Rodar para verificar que falha**

Run: `docker compose exec web python manage.py test character.tests.DomainSpellsResolveTests -v 2`
Expected: `KeyError: 'sdr_id'`.

- [ ] **Step 3: Atualizar `domain_spells`**

Em `dd3esheet/character/spellcasting.py` (linha 105), substituir:

```python
def domain_spells(domain_name):
    if not domain_name:
        return []
    domain = SDR_Domain.objects.using('sdr').filter(name=domain_name).first()
    if not domain:
        return []
    return [
        {'level': level, 'name': getattr(domain, f'spell_{level}') or ''}
        for level in range(1, 10)
    ]
```

por:

```python
def domain_spells(domain_name):
    if not domain_name:
        return []
    domain = SDR_Domain.objects.using('sdr').filter(name=domain_name).first()
    if not domain:
        return []
    from sdr.lookups import resolve_spell
    rows = []
    for level in range(1, 10):
        name = getattr(domain, f'spell_{level}') or ''
        match = resolve_spell(name) if name else None
        rows.append({
            'level': level,
            'name': name,
            'sdr_id': match.id if match else None,
            'sdr': match,
        })
    return rows
```

- [ ] **Step 4: Rodar para verificar que passa**

Run: `docker compose exec web python manage.py test character.tests.DomainSpellsResolveTests -v 2`
Expected: `Ran 2 tests ... OK`.

- [ ] **Step 5: Atualizar template `character_spells.html`**

Em `dd3esheet/character/templates/character/partials/character_spells.html`, no topo (linha 1), adicionar:

```
{% load dict_extras %}
```

Substituir as duas iterações de domínio (linhas 31-34 e 39-42). Estado novo para o primeiro domínio:

```html
{% for spell in spellcasting.domain_1_spells %}
<div data-slot="{{ spell.level }}">
    <span data-derived="domainSpell.Level" data-slot="{{ spell.level }}">{{ spell.level }}</span>
    <strong class="spell-name-link"
            data-sdr-id="{% if spell.sdr_id %}{{ spell.sdr_id }}{% endif %}"
            data-derived="domainSpell.Name" data-slot="{{ spell.level }}"
            {% if spell.sdr_id %}
            hx-get="{% url 'character:spell-detail' character.pk spell.sdr_id %}"
            hx-target="#spell-detail-dialog"
            hx-swap="innerHTML"
            onclick="document.getElementById('spell-detail-dialog').showModal()"
            {% endif %}>
        {{ spell.name|default:"-" }}
    </strong>
    {% if spell.sdr %}
        {% with sdr=spell.sdr %}{% include "character/partials/_spell_tooltip.html" %}{% endwith %}
    {% endif %}
</div>
{% endfor %}
```

Replicar mesma mudança para `spellcasting.domain_2_spells` (segundo bloco).

**Importante:** o `<strong>` é tanto o nome quanto o trigger do modal. Sem botão extra porque é read-only e não há input para focar. CSS `.spell-name-link[data-sdr-id]:not([data-sdr-id=""])` ativa cursor pointer + underline dotted.

- [ ] **Step 6: Rodar suíte inteira**

Run: `docker compose exec web python manage.py test -v 1`
Expected: tudo verde.

- [ ] **Step 7: Commit**

```bash
git add dd3esheet/character/spellcasting.py \
        dd3esheet/character/templates/character/partials/character_spells.html \
        dd3esheet/character/tests.py
git commit -m "feat(ui): domínios de clérigo com tooltip + click no SDR"
```

---

### Task 11: Magias de Invocação dos Aliados com `sdr_id`

**Files:**
- Modify: `dd3esheet/character/views.py` (`_summon_nature_rows`, linhas 397+)
- Modify: `dd3esheet/character/templates/character/companions.html` (linha 103)
- Test: `dd3esheet/character/tests.py`

- [ ] **Step 1: Escrever teste do `_summon_nature_rows`**

Adicionar em `dd3esheet/character/tests.py`:

```python
class SummonNatureRowsResolveTests(TestCase):
    databases = {'sdr', 'default'}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connections['sdr'].cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS spell (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL, altname TEXT, school TEXT,
                    subschool TEXT, descriptor TEXT, spellcraft_dc TEXT,
                    level TEXT, components TEXT, casting_time TEXT,
                    range TEXT, target TEXT, area TEXT, effect TEXT,
                    duration TEXT, saving_throw TEXT, spell_resistance TEXT,
                    short_description TEXT, to_develop TEXT,
                    material_components TEXT, arcane_material_components TEXT,
                    focus TEXT, description TEXT, xp_cost TEXT,
                    arcane_focus TEXT, wizard_focus TEXT, verbal_components TEXT,
                    sorcerer_focus TEXT, bard_focus TEXT, cleric_focus TEXT,
                    druid_focus TEXT, full_text TEXT, reference TEXT
                );
            """)

    def test_summon_rows_have_sdr_id_when_known(self):
        from sdr.models import SDR_Spell
        from character.views import _summon_nature_rows
        SDR_Spell.objects.using('sdr').all().delete()
        sdr = SDR_Spell(
            name="Aliado da Natureza I",
            altname="Summon Nature's Ally I",
            school="Conjuration", level="Drd 1",
        )
        sdr.save(using='sdr')
        rows = _summon_nature_rows()
        row1 = next(r for r in rows if r['level'] == 1)
        self.assertEqual(row1['sdr_id'], sdr.id)

    def test_summon_rows_sdr_id_none_when_unknown(self):
        from sdr.models import SDR_Spell
        from character.views import _summon_nature_rows
        SDR_Spell.objects.using('sdr').all().delete()
        rows = _summon_nature_rows()
        self.assertTrue(all(r['sdr_id'] is None for r in rows))
```

- [ ] **Step 2: Rodar para verificar que falha**

Run: `docker compose exec web python manage.py test character.tests.SummonNatureRowsResolveTests -v 2`
Expected: `KeyError: 'sdr_id'`.

- [ ] **Step 3: Atualizar `_summon_nature_rows`**

Em `dd3esheet/character/views.py` (linha 397). No topo do arquivo, garantir:

```python
from sdr.lookups import resolve_spell
```

Substituir `_summon_nature_rows()` para enriquecer cada row com `sdr_id` e `sdr`:

```python
def _summon_nature_rows():
    raw = [
        {'level': 1, 'spell': 'Aliado da Natureza I',  'quantity': '1 criatura de 1o nivel',          'examples': 'Rato atroz, aguia, macaco, coruja, lobo, vibora pequena'},
        {'level': 2, 'spell': 'Aliado da Natureza II', 'quantity': '1 de 2o, 1d3 de 1o',              'examples': 'Urso negro, crocodilo, texugo atroz, morcego atroz, elemental pequeno'},
        {'level': 3, 'spell': 'Aliado da Natureza III','quantity': '1 de 3o, 1d3 de 2o, 1d4+1 de 1o','examples': 'Gorila, doninha atroz, lobo atroz, leao, thoqqua'},
        {'level': 4, 'spell': 'Aliado da Natureza IV', 'quantity': '1 de 4o, 1d3 de 3o, 1d4+1 menores','examples': 'Urso pardo, aguia gigante, elemental medio, tigre, unicornio'},
        {'level': 5, 'spell': 'Aliado da Natureza V',  'quantity': '1 de 5o, 1d3 de 4o, 1d4+1 menores','examples': 'Urso polar, leao atroz, elemental grande, grifo, rinoceronte'},
        # ... mantenha os demais níveis 6-9 conforme já existem hoje
    ]
    for row in raw:
        sdr = resolve_spell(row['spell'])
        row['sdr_id'] = sdr.id if sdr else None
        row['sdr'] = sdr
    return raw
```

**Atenção:** o snippet acima mostra parte da lista. Leia a versão atual em `dd3esheet/character/views.py:397` e adicione níveis 6-9 do jeito que já estão. Não recorte conteúdo.

- [ ] **Step 4: Rodar para verificar que passa**

Run: `docker compose exec web python manage.py test character.tests.SummonNatureRowsResolveTests -v 2`
Expected: `Ran 2 tests ... OK`.

- [ ] **Step 5: Atualizar template `companions.html`**

Em `dd3esheet/character/templates/character/companions.html`, no topo, adicionar (se ainda não existir):

```
{% load dict_extras %}
```

Substituir a linha 103:

```html
<div class="summon-spell-name" data-field="summonNature.Spell" data-slot="{{ row.level }}">{{ row.spell }}</div>
```

por:

```html
<div class="summon-spell-name" data-field="summonNature.Spell" data-slot="{{ row.level }}">
    <span class="spell-name-link"
          data-sdr-id="{% if row.sdr_id %}{{ row.sdr_id }}{% endif %}"
          {% if row.sdr_id %}
          hx-get="{% url 'character:spell-detail' character.pk row.sdr_id %}"
          hx-target="#spell-detail-dialog"
          hx-swap="innerHTML"
          onclick="document.getElementById('spell-detail-dialog').showModal()"
          {% endif %}>
        {{ row.spell }}
    </span>
    {% if row.sdr %}
        {% with sdr=row.sdr %}{% include "character/partials/_spell_tooltip.html" %}{% endwith %}
    {% endif %}
</div>
```

- [ ] **Step 6: Rodar suíte inteira**

Run: `docker compose exec web python manage.py test -v 1`
Expected: tudo verde.

- [ ] **Step 7: Commit**

```bash
git add dd3esheet/character/views.py \
        dd3esheet/character/templates/character/companions.html \
        dd3esheet/character/tests.py
git commit -m "feat(ui): Magias de Invocação com tooltip + click no SDR"
```

---

### Task 12: Verificação manual via `/run`

**Files:** nenhum (validação visual).

- [ ] **Step 1: Subir a stack**

Run: `docker compose up -d`
Expected: containers `web` e `db` (se houver) sobem; logs do `web` mostram `migrate → seed → runserver`.

- [ ] **Step 2: Logar com usuário seed**

Abrir `http://localhost:8000/`, logar como `jarza` / `P@ssw0rd`. Abrir o personagem **Mago** seedado (que já tem magias preparadas pelo seed).

- [ ] **Step 3: Validar Livro de Magias**

Ir em **Livro de Magias** → expandir nível 1.

Checklist visual:
- [ ] Inputs renderizam normalmente; nenhum erro de layout regrediu.
- [ ] Para magias que casam com SDR (ex: Magic Missile), aparece o ícone **📖** ao lado.
- [ ] **Hover** sobre uma magia com 📖 → tooltip com escola/nível/casting/components/range/save aparece dentro de ~50ms (CSS puro).
- [ ] **Click** no 📖 → `<dialog>` abre no centro com o `full_text` da magia, com fundo escurecido (backdrop).
- [ ] Botão **×** fecha o dialog. ESC também fecha (nativo).
- [ ] Digitar no input mostra sugestões do datalist com nomes do SDR.
- [ ] Escolher uma sugestão dispara o save HTMX e, após o swap, o 📖 e o tooltip aparecem.
- [ ] Digitar um nome custom (homebrew) → sem 📖, sem tooltip; save normal.

- [ ] **Step 4: Validar Domínios de Clérigo**

Logar com `jarza`, ir num personagem clérigo (ou trocar `Class` temporariamente no Mago para `Cleric` via admin se não houver seed clérigo).

Checklist:
- [ ] Spans de domínio mostram nome com underline dotted quando há `data-sdr-id`.
- [ ] Hover mostra tooltip.
- [ ] Click abre o dialog.

- [ ] **Step 5: Validar Aliados / Magias de Invocação**

Ir num personagem druida → **Aliados** → expandir 📜 Magias de Invocação.

Checklist:
- [ ] Cada linha de "Aliado da Natureza N" tem underline dotted se a magia existe no SDR.
- [ ] Hover/click funcionam.

- [ ] **Step 6: Verificar regressão geral**

- [ ] Outras seções da ficha (atributos, AC, saves, skills, equipamentos) editam normalmente.
- [ ] Botões de salvar/HTMX em outras páginas funcionam (Recursos Diários, Reputação, Aliados — Animal/Familiar).
- [ ] Sem erros no console do navegador.
- [ ] Sem `500` nos logs do Docker (`docker compose logs web --tail=100`).

- [ ] **Step 7: Tag de fechamento**

Se tudo passou:

```bash
git log --oneline | head -15
```

Confirmar a sequência de commits da feature. Não há tag formal a aplicar — fim das tarefas.

---

## Estimativa

12 tasks, ~5-10 min cada (a Task 9 é a maior por mexer em template + contexto + tag custom; Task 12 leva ~10-15 min de validação visual). Total estimado: 1.5–2h.

## Riscos conhecidos

- **Datalist com ~1500 opções:** pesado de carregar. Se ficar lento, mitigar passando `only('id', 'name', 'school', 'level')` (já incluso) e considerar lazy-load via HTMX num próximo PR. Não bloqueia este plano.
- **Múltiplos clicks em ícones diferentes antes do dialog fechar:** `showModal()` em dialog já aberto é no-op; HTMX `innerHTML` substitui conteúdo. Comportamento esperado: o último click vence. Aceitável.
- **`onclick`:** introduz JS inline. Já há precedente em `companions.html:73-74`. Se o usuário rejeitar, mover para um único listener delegado em `main.html` (mudança trivial).
- **`spellbook.html` versus partial:** o partial `spellbook_level_form.html` é renderizado tanto pela página inteira quanto pelo retorno HTMX. O `<datalist>` no fim do partial pode acabar duplicado se a página renderizar vários níveis. Considerar mover o datalist para `spellbook.html` (página) num único lugar — durante implementação ajuste conforme a estrutura observada.

## Self-Review (já feito durante a escrita)

**Spec coverage:**
- Modelo `SDRSpellId` → Task 3 ✓
- `resolve_spell` extraído + reuso em `import_spells` → Tasks 1 e 2 ✓
- Save hook → Task 4 ✓
- Endpoint `spell_detail` → Task 5 ✓
- Pré-carga bulk → Task 9 ✓
- Template livro com autocomplete + ícone + tooltip → Task 9 ✓
- Template domínios → Task 10 ✓
- Template summon (Aliados) → Task 11 ✓
- `<dialog>` em main → Task 6 ✓
- CSS → Task 7 ✓
- Partial reutilizável tooltip → Task 8 ✓
- Testes de lookup, save, view, render → Tasks 1, 3, 4, 5, 9, 10, 11 ✓
- Verificação visual → Task 12 ✓

**Placeholders:** scaneei — nenhum "TBD/TODO/preencher depois". As referências a "ajustar conforme estrutura observada" (Task 11 step 3, Task 9 step 3) são reaberturas mínimas porque o conteúdo da função atual é fonte de verdade; o plano dá a instrução precisa de leitura.

**Type/method consistency:**
- `resolve_spell(name)` retorna `Optional[SDR_Spell]` em todas as tasks ✓
- `SDRSpellId` é `IntegerField` em todas as referências ✓
- `sdr_id` (snake_case) usado em dicts de contexto (`domain_spells`, `summon_rows`); `SDRSpellId` (PascalCase) usado no model — consistente com convenção do projeto ✓
- Nome de URL `character:spell-detail` igual em todos os lugares ✓
- IDs HTML: `spell-detail-dialog`, `spell-suggestions` — consistentes ✓
- Classes CSS: `spell-input-wrap`, `spell-tooltip`, `spell-name-link`, `spell-detail-trigger`, `spell-detail-dialog` — consistentes ✓
