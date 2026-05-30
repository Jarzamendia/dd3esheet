# Lacunas conhecidas

## HTMX carregado (resolvido em T0.2)

`dd3esheet/templates/main.html` ja carrega `htmx.min.js`, `django_htmx_script`
e o handler de CSRF para POSTs HTMX.

## Calculos: funcoes puras extraidas (resolvido em T1.7)

`character/calculations.py` agora concentra `compute_armor_class`,
`compute_save_total`, `compute_grapple_total` e `compute_skill_row`, alem das
funcoes puras anteriores. `_recalculate_stats` e um orquestrador fino.

## Validacao desigual entre blocos

Identidade, descricao e stats usam `ModelForm`.

Outros blocos usam helpers diretos de POST:

- equipamentos;
- itens;
- talentos;
- habilidades;
- magias;
- dinheiro;
- pericias.

Impacto:

- menos validacao explicita;
- conversao simples para `IntegerField` e `BooleanField`;
- valores textuais aceitam quase tudo.

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

