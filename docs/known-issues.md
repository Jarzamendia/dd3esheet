# Lacunas conhecidas

## HTMX nao esta carregado no template base

Existe o arquivo:

```text
dd3esheet/static/htmx.min.js
```

`django_htmx` tambem esta instalado e o middleware esta ativo.

Porem, o template base atual `dd3esheet/templates/main.html` nao inclui:

```html
<script src="{% static 'htmx.min.js' %}"></script>
```

Impacto:

- os atributos `hx-*` renderizam no HTML;
- sem o script, o browser nao executa o autosave HTMX;
- a edicao inline fica visualmente presente, mas nao faz POST automatico.

## Calculos ainda dentro da view

`_recalculate_stats` fica em `character/views.py`.

Melhoria recomendada:

- mover regras de calculo para `character/calculations.py`;
- deixar a view apenas orquestrar request, forms e render;
- cobrir funcoes puras com testes unitarios.

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

