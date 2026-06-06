# App: character

O app `character` implementa a ficha de personagem de D&D 3.5. Ele guarda os
dados da ficha, calcula valores derivados, organiza magias, recursos diarios,
companheiros, invocacoes, reputacao e integra referencias do SDR e sprites.

## Para que serve

- Cria, lista, edita e remove fichas pertencentes ao usuario autenticado.
- Mantem blocos da ficha em modelos separados: atributos, status, resistencia,
  ataque, pericias, equipamentos, dinheiro, magias, recursos, buffs e progresso.
- Recalcula valores derivados como modificadores de atributo, CA, testes de
  resistencia, ataque, agarrar, carga e CDs de magia.
- Usa HTMX para autosave e renderizacao parcial de secoes da ficha.
- Consulta o app `sdr` para magias e monstros usados em spellbook e invocacoes.
- Consulta o app `sprites` para icones/retratos por classe e imagens de apoio.

## Arquivos principais

- `models.py`: define `Character` e todos os modelos relacionados da ficha.
- `views.py`: contem as telas e endpoints HTMX de ficha, spellbook, buffs,
  recursos diarios, companheiros, invocacoes e reputacao.
- `calculations.py`: regras puras de calculo para atributos, pericias,
  equipamentos, saves, ataque e carga.
- `spellcasting.py`: contexto de conjuracao por classe e niveis de magia.
- `services.py`: bootstrap dos modelos filhos da ficha e slots de pericia
  expansivel.
- `constants.py`: listas, presets e labels usados pela ficha.
- `forms.py`: formularios de criacao e edicao basica.
- `seeds.py` e `management/commands/seed.py`: criam dados iniciais/padroes.
- `templatetags/dict_extras.py`: helpers de template.

## Rotas

- `GET /character/`: lista de fichas do usuario.
- `GET|POST /character/character/<pk>`: ficha principal e autosaves HTMX.
- `GET|POST /character/character/<pk>/spellbook`: grimorio e slots de magia.
- `GET|POST /character/character/<pk>/daily-resources`: recursos diarios e efeitos.
- `GET|POST /character/character/<pk>/companions`: companheiros e invocacoes.
- `GET|POST /character/character/<pk>/reputation`: contatos, faccoes e contratos.
- `POST /character/character/<pk>/buffs/...`: adiciona, alterna e remove buffs.
- `GET|POST /character/create-character/`: cria nova ficha.
- `GET|POST /character/delete-character/<pk>/`: remove ficha.

## Dependencias e cuidados

- Todas as views principais usam `login_required` e filtram por `User`, evitando
  acesso a fichas de outro usuario.
- Ao criar uma ficha, `_bootstrap_character_siblings` deve ser chamado para
  criar os registros `OneToOne` esperados pelas telas.
- Varias secoes dependem de nomes de targets HTMX; ao renomear templates,
  formularios ou ids, revise os branches em `views.character`.
- A integracao com `sdr` usa o banco configurado como `sdr` em `settings.py`.
- Campos e nomes seguem a convencao atual em PascalCase. Mudar isso exige
  cuidado com templates, migrations e formularios.
