# D&D 3.5 eSheet

## Requiriments
Python: 3.12.2

### Rodando o ambiente
- docker-compose up
- docker-compose exec web bash

Depois de entrar no container:

- python manage.py makemigrations
- python manage.py migrate

Para criar um super user:
- python manage.py createsuperuser

### Acessando o ambiente admin
- Acessar localhost:8000/admin



## Criando models a partir de uma tabela pronta.

Depois de criar a tabela no settings.py, rode o seguinte comando:

```
python manage.py inspectdb --database sdr
```