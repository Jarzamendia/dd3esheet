# Deployment

## Pré-requisitos

- Docker e Docker Compose instalados no servidor.
- Arquivo `.env` criado a partir de `.env.example` (veja abaixo).

## Configurar o `.env`

```bash
cp dd3esheet/.env.example dd3esheet/.env
```

Edite `.env` com os valores reais:

```
SECRET_KEY=<gerar conforme abaixo>
DEBUG=False
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com
CSRF_TRUSTED_ORIGINS=https://seu-dominio.com,https://www.seu-dominio.com
```

### Gerar SECRET_KEY

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Ou dentro do container:

```bash
docker compose -f dd3esheet/docker-compose.prod.yaml run --rm web \
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Subir em produção

A partir de `dd3esheet/`:

```bash
docker compose -f docker-compose.prod.yaml up -d --build
```

Isso:
1. Constrói a imagem com `python:3.12-slim`.
2. Executa `collectstatic` no build (WhiteNoise serve os arquivos).
3. Executa `python manage.py migrate` no boot do container.
4. Inicia Gunicorn com 3 workers na porta 8000.

## Verificar healthcheck e logs

```bash
# Verificar se o container está healthy
docker compose -f docker-compose.prod.yaml ps

# Ver logs em tempo real
docker compose -f docker-compose.prod.yaml logs -f web

# Testar healthcheck manualmente
curl http://localhost:8000/healthz
# Resposta esperada: {"ok": true}
```

O `docker-compose.prod.yaml` configura o healthcheck automaticamente:
- Testa `GET /healthz` a cada 30 segundos.
- Timeout de 3 segundos, 3 retentativas.

## Variáveis de ambiente obrigatórias

| Variável               | Descrição                                              |
|------------------------|--------------------------------------------------------|
| `SECRET_KEY`           | Chave secreta Django (nunca commitar)                  |
| `DEBUG`                | `False` em produção                                    |
| `ALLOWED_HOSTS`        | Hostnames permitidos, separados por vírgula            |
| `CSRF_TRUSTED_ORIGINS` | Origins HTTPS confiáveis, separados por vírgula        |

## Opcional

| Variável      | Descrição                                                          |
|---------------|--------------------------------------------------------------------|
| `SEED_ADMIN`  | `true` para criar a conta admin de exemplo (nunca em produção!)    |

## Aviso: seed em produção

**Nunca** execute `python manage.py seed` em produção sem `SEED_ADMIN=true` explícito.
O seed cria a conta `jarza/P@ssw0rd` — credenciais fixas e conhecidas, inadequadas
para servidores públicos.

Se precisar criar um superusuário em produção:

```bash
docker compose -f docker-compose.prod.yaml exec web python manage.py createsuperuser
```

## Static files

Os arquivos estáticos são servidos pelo **WhiteNoise** diretamente do Gunicorn,
sem nginx intermediário. O header `Cache-Control` é configurado automaticamente
pelo `CompressedManifestStaticFilesStorage`.

Para verificar:

```bash
curl -I http://localhost:8000/static/htmx.min.<hash>.js
# Deve conter: Cache-Control: max-age=...
```
