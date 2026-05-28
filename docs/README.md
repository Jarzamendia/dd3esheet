# Base de conhecimento do projeto

Esta pasta e a referencia principal para humanos e agentes trabalharem no projeto.

Leia nesta ordem quando estiver entrando no codigo:

1. [Setup e comandos](setup-and-commands.md)
2. [Arquitetura](architecture.md)
3. [Dominio da ficha de personagem](character-domain.md)
4. [Edicao inline HTMX](inline-editing.md)
5. [Seeds e dados de exemplo](seeds.md)
6. [SRD / banco de referencia](sdr-reference.md)
7. [Testes e qualidade](testing.md)
8. [Verificacao atual](verification.md)
9. [Playbook para agentes](agent-playbook.md)
10. [Lacunas conhecidas](known-issues.md)

## Produto

O projeto e uma ficha virtual de D&D 3.5 em Django.

A direcao do produto e clara:

- parecer uma ficha de papel de D&D 3.5;
- permitir edicao direta dos campos da ficha;
- salvar sem reload de pagina;
- calcular derivados no backend;
- suportar varias fichas por usuario;
- manter o SRD como referencia read-only separada.

## Estado verificado

Revisado em 2026-05-28:

- Django app em `dd3esheet/`.
- Docker Compose sobe `web` em `localhost:8000`.
- O comando do container executa `migrate`, `seed` e `runserver`.
- Banco `default`: `db.sqlite3`, local e ignorado pelo git.
- Banco `sdr`: `dnd35.sqlite3`, versionado e tratado como read-only.
- App `character` possui apenas uma migration inicial consolidada.
- `character/seeds.py` e `manage.py seed` existem e populam admin + fichas de exemplo.
- A ficha possui partials HTMX e muitos campos ja foram convertidos para inputs reais.
- `static/htmx.min.js` existe, mas o template base atual nao inclui o script. Ver [Lacunas conhecidas](known-issues.md).

## Ultima verificacao

Ver [Verificacao atual](verification.md).
