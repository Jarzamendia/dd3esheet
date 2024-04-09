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
