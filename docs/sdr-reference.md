# SRD / banco de referencia

## Objetivo

O app `sdr` expoe dados de referencia D&D 3.5.

Ele e usado para consulta e tambem alimenta partes da ficha, como escolhas de classe e tabelas de conjuracao.

## Banco

Arquivo:

```text
dd3esheet/dnd35.sqlite3
```

Alias Django:

```python
"sdr"
```

## Models

Os models ficam em:

```text
dd3esheet/sdr/models.py
```

Eles usam `managed = False` e tabelas explicitas.

Regra:

```python
SDR_Spell.objects.using("sdr")
```

Sempre use `.using("sdr")`.

Sem isso, o Django tenta consultar o banco `default`.

## Views e filtros

`sdr/views.py` cria listagens e detalhes.

Listagens usam `django-filter`:

- `SpellsFilter`
- `MonsterFilter`
- `ClassFilter`
- `DomainFilter`
- `EquipmentFilter`
- `FeatFilter`
- `ItemFilter`
- `PowerFilter`
- `SkillFilter`

Os filtros tambem definem querysets padrao com `.using("sdr")`.

## Categorias expostas

- Spells.
- Monsters.
- Classes.
- Domains.
- Equipment.
- Feats.
- Items.
- Powers.
- Skills.

## Uso pela ficha

`character.services.sdr_class_choices()` busca classes no banco `sdr` para o select de classe.

`character.spellcasting` usa:

- `SDR_ClassTable` para slots por nivel;
- `SDR_Domain` para magias de dominio.

## Regenerar models

Se o schema do banco SRD mudar, gere models a partir do banco:

```bash
python manage.py inspectdb --database sdr
```

Nao escreva os fields manualmente sem comparar com o schema real.

## Testes

Testes que precisam tocar `sdr` devem declarar:

```python
databases = {"default", "sdr"}
```

Em `character/tests.py`, o helper `setup_sdr_class_table()` cria tabelas mínimas no banco de teste `sdr` para exercitar classes, class table e domínios. Em `sdr/tests.py`, criamos a tabela `feat` dinamicamente no `setUpClass` para testar comandos de importação contra models com `managed = False`.

---

## 📖 Melhoria do SDR em Português: Gestão de Talentos (Feats)

O banco de dados de referência do D&D 3.5 (`dnd35.sqlite3`) originalmente possui os talentos cadastrados no idioma inglês. Para melhorar a experiência em português do jogador brasileiro, implementamos uma arquitetura robusta de **importação e tradução** extensível.

### O que já foi implementado e está pronto:

1. **Arquivo de Dados Inicial (`sdr/data/feats_pt.json`):**
   Contém os 15 talentos mais populares e essenciais do *Livro do Jogador 3.5* em português com traduções ricas e completas de pré-requisitos, benefícios, seções normais e notas especiais. Dentre eles:
   * *Ataque Poderoso* (Power Attack)
   * *Iniciativa Aprimorada* (Improved Initiative)
   * *Esquiva* (Dodge)
   * *Foco em Arma* (Weapon Focus)
   * *Sucesso Decisivo Aprimorado* (Improved Critical)
   * *Combate com Duas Armas* (Two-Weapon Fighting)
   * *Tiro Certeiro* (Point-Blank Shot)
   * *Tiro Rápido* (Rapid Shot)
   * *Foco em Magia* (Spell Focus)
   * *Vontade de Ferro*, *Reflexos Rápidos* e *Grande Fortitude* (Saves)
   * *Robustez* (Toughness)
   * *Escrever Pergaminho* e *Preparar Poção* (Criação de Itens)

2. **Comando Customizado do Django Admin (`import_feats`):**
   Um comando administrativo robusto e idempotente para sincronizar os talentos traduzidos para a base do SDR.
   * **Comando:** `python manage.py import_feats`
   * Ele analisa cada item do arquivo JSON. Se o talento já existir, atualiza os campos com o conteúdo traduzido de forma segura. Se não existir, ele cria o registro.

3. **Suite de Testes Unitários (`sdr/tests.py`):**
   Um caso de teste completo rodando sob `databases = {'sdr', 'default'}` que cria a tabela temporária na base de testes (contornando o fato de ser `managed = False`) e valida se a criação e a atualização via comando são executadas de forma livre de bugs.

### Como adicionar facilmente outros talentos ao SDR:

Para expandir a biblioteca de talentos traduzidos para incluir outros livros (como *Livro do Monstro*, *Guia do Mestre*, *Codex Divino* ou suplementos específicos), siga este processo simples:

1. Abra o arquivo [feats_pt.json](file:///C:/Users/Jarzamendia/git/github/dd3esheet/dd3esheet/sdr/data/feats_pt.json).
2. Adicione uma nova entrada seguindo o esquema JSON:
   ```json
   {
     "name": "Nome do Talento em Portugues",
     "type": "Tipo (ex: General, Fighter, Metamagic, Item Creation)",
     "multiple": "Yes ou No",
     "stack": "Yes ou No",
     "choice": "Opcao de escolha se houver (ex: Arma, Escola de Magia)",
     "prerequisite": "Pre-requisitos do talento",
     "benefit": "Descricao resumida do beneficio",
     "normal": "Descricao do comportamento normal sem o talento",
     "special": "Notas especiais e condicoes adicionais",
     "full_text": "Texto em HTML completo formatado",
     "reference": "Nome do Livro de Origem (ex: Guia do Mestre 3.5 (PT))"
   }
   ```
3. Se estiver rodando o ambiente local no Docker, execute o comando de importação:
   ```bash
   docker compose exec web python manage.py import_feats
   ```
4. Pronto! O talento estará disponível imediatamente para busca no SDR e para ser associado aos personagens de forma integrada e traduzida.

---

## 🔮 Melhoria do SDR em Português: Gestão de Magias (Spells)

Seguindo o mesmo conceito de tradução extensível, implementamos a **importação e tradução de magias** (spells) do *Livro do Jogador 3.5* diretamente para a tabela `spell` da base de referência do SDR.

### Recursos prontos no sistema:

1. **Biblioteca de Magias Iniciais (`sdr/data/spells_pt.json`):**
   Contém magias clássicas e amplamente usadas no D&D 3.5 em português:
   * *Mísseis Mágicos* (Magic Missile)
   * *Bola de Fogo* (Fireball)
   * *Curar Ferimentos Leves* (Cure Light Wounds)
   * *Escudo da Fé* (Shield of Faith)
   * *Bênção* (Bless)
   * *Sono* (Sleep)
   * *Ataque Certeiro* (True Strike)

2. **Comando Administrativo Inteligente (`import_spells`):**
   * **Comando:** `python manage.py import_spells`
   * **Tradução In-Place:** O comando busca as magias existentes pelos seus nomes correspondentes em inglês (ex: `Magic Missile`) e **traduz o registro existente** in-place, alterando o título para português e salvando o nome original no campo `altname`. Isso mantém a integridade do banco e evita a duplicação de dados!

3. **Testes Unitários de Cobertura (`sdr/tests.py`):**
   * Classe `SDRSpellTests` que valida dinamicamente o parser de magias e a tradução in-place de registros fictícios em inglês sem duplicidade.

### Como adicionar facilmente outras magias ao SDR:

Para expandir a biblioteca de magias em português:

1. Abra o arquivo [spells_pt.json](file:///C:/Users/Jarzamendia/git/github/dd3esheet/dd3esheet/sdr/data/spells_pt.json).
2. Adicione uma nova magia seguindo o esquema JSON:
   ```json
   {
     "name": "Nome da Magia em Portugues",
     "altname": "Nome da Magia original em Ingles (obrigatorio para traducao in-place)",
     "school": "Escola (ex: Evocation, Conjuration, Abjuration)",
     "level": "Nivel (ex: Sor/Wiz 1, Clr 1)",
     "components": "Componentes (ex: V, S, M, F)",
     "casting_time": "Tempo de conjuracao (ex: 1 acao padrao)",
     "range": "Alcance (ex: Medio, Pessoal, Toque)",
     "target": "Alvo ou efeito se aplicavel",
     "area": "Area se aplicavel",
     "duration": "Duracao",
     "saving_throw": "Teste de resistencia",
     "spell_resistance": "Resistencia a magia (Sim ou Nao)",
     "short_description": "Breve descricao de combate",
     "description": "Descricao completa das regras da magia",
     "reference": "Livro de Origem (ex: Livro do Jogador 3.5 (PT))"
   }
   ```
3. No ambiente Docker, execute:
   ```bash
   docker compose exec web python manage.py import_spells
   ```
4. As magias traduzidas estarão prontas imediatamente para uso na nova sub-página de Grimório/Livro de Magias!

