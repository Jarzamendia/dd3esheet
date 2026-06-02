# Lacunas conhecidas

## HTMX carregado (resolvido em T0.2)

`dd3esheet/templates/main.html` ja carrega `htmx.min.js`, `django_htmx_script`
e o handler de CSRF para POSTs HTMX.

## Calculos: funcoes puras extraidas (resolvido em T1.7)

`character/calculations.py` agora concentra `compute_armor_class`,
`compute_save_total`, `compute_grapple_total` e `compute_skill_row`, alem das
funcoes puras anteriores. `_recalculate_stats` e um orquestrador fino.

## Validacao consistente (resolvido em T1.3)

`_update_fields_from_post` e `_save_repeating_slots` agora aplicam strip/truncate
em strings (respeitando `max_length` do model) e clamp em inteiros (`-999..999`).
Identidade/descricao/stats continuam usando `ModelForm` crispy.

## Compartilhamento ainda nao implementado

Hoje a ficha e acessivel apenas pelo dono.

Quando implementar, usar permissao explicita:

```python
CharacterShare(character, user, can_edit=False)
```

Regra de seguranca:

- dono pode ver/editar;
- usuario compartilhado pode ver;
- estranho recebe 404.

## SDR tests ainda sao limitados

`sdr/tests.py` ainda e minimo.

O app `character` possui testes que exercitam consultas SDR, mas o app `sdr` em si ainda precisa de cobertura propria para listagens e detalhes.

## Campos derivaveis ainda manuais

Checklist da Entrega A do `AGENT2.md`. O objetivo e zerar esta lista.

- `CharacterWeapon.AttackBonus` ainda e digitado manualmente nos cards de arma. Deve ser derivado de `BBA` + mod. de atributo correto (FOR corpo a corpo, DES a distancia) + tamanho + misc.
- `CharacterAttackModifiers.GrapplerBBA` ainda duplica `BBA` como entrada manual, apesar de representar o mesmo componente base do total de agarrar.
- `CharacterStatus.ACDexModifier` ainda usa a Destreza cheia; nao respeita o teto de `MaxDex` da armadura/escudo equipado.
- `CharacterSkill.SkillModifier` ainda ignora penalidade de armadura/escudo nas pericias afetadas por armadura. `Natacao` tambem nao dobra essa penalidade.
- `CharacterStatus.Speed` ainda pode ser digitado manualmente no bloco de combate; deveria ser recalculado a partir do deslocamento da armadura equipada e da categoria de carga.
- `CharacterMagicDayUse.SpellSaveDC` e `CharacterMagicDayUse.BonusSpells` nao sao persistidos. A UI mostra valores calculados em memoria, sem gravar o estado derivado por nivel.

