# Setup e comandos

## Requisitos

- Docker
- Docker Compose v2 (`docker compose`)

O projeto foi preparado para rodar dentro de container. Os comandos Django devem ser executados a partir da pasta `dd3esheet/`.

```powershell
cd dd3esheet
```

## Subir o app

Build + start:

```powershell
docker compose up --build
```

Start sem rebuild:

```powershell
docker compose up
```

Start em background:

```powershell
docker compose up -d
```

URLs:

- App: `http://localhost:8000/`
- Admin: `http://localhost:8000/admin/`

## O que o compose faz

O servico `web` executa este fluxo automaticamente:

```bash
python manage.py migrate &&
python manage.py seed &&
python manage.py runserver 0.0.0.0:8000
```

Consequencias:

- o banco `default` e migrado no `up`;
- o seed roda a cada `up`;
- as fichas de exemplo sao recriadas;
- a senha do admin local e redefinida.

O seed e idempotente para o uso local esperado.

## Entrar no container

```powershell
docker compose exec web bash
```

Dentro do container:

```bash
python manage.py check
python manage.py migrate
python manage.py seed
python manage.py createsuperuser
python manage.py test
python manage.py test character
```

## Rodar comandos sem shell interativo

Com o container rodando:

```powershell
docker compose exec web python manage.py check
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed
docker compose exec web python manage.py test character
```

Sem depender de container ja rodando:

```powershell
docker compose run --rm web python manage.py check
docker compose run --rm web python manage.py test character
docker compose run --rm web python manage.py makemigrations --check --dry-run
```

## Credenciais locais do seed

O seed cria um superusuario local:

- Usuario: `jarza`
- Senha: `P@ssw0rd`

Use apenas em ambiente local/de teste.

## Arquivos de ambiente

- `dd3esheet/Dockerfile`: imagem Python 3.12, instala `requirements.txt`.
- `dd3esheet/docker-compose.yaml`: servico `web`, porta `8000:8000`, volume `./:/usr/src/app/`.
- `dd3esheet/requirements.txt`: arquivo em UTF-16 LE com BOM. Nao regravar como UTF-8 sem confirmar.

