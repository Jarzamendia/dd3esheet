# 🎲 DD3ESheet — Ansible (OCI Server)

## ⚙️ Configuração inicial

```bash
# 1. Editar IP do servidor e variáveis
vim inventory/hosts.ini
vim group_vars/oci_servers.yml

# 2. Instalar coleções (já feito automaticamente via Docker)
# Caso precise atualizar manualmente:
.\ansible.ps1 ansible-galaxy collection install -r requirements.yml
```

**Variáveis obrigatórias** em `group_vars/oci_servers.yml`:

| Variável | Exemplo |
|----------|---------|
| `ansible_host` | `150.230.x.x` |
| `django_secret_key` | Gerar com `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `app_domain` | `meuapp.com` |
| `ssl_email` | `admin@meuapp.com` |

---

## 🚀 Deploy

```bash
# Deploy completo (primeira vez)
.\ansible.ps1 ansible-playbook deploy.yml

# Deploy rápido (sync + build docker + restart)
.\ansible.ps1 ansible-playbook deploy.yml --tags "deploy"

# Apenas sincronizar arquivos (muito rápido, não reinicia o app)
.\ansible.ps1 ansible-playbook sync.yml

# Dry-run
.\ansible.ps1 ansible-playbook deploy.yml --check --diff
```

**Tags:** `update`, `firewall`, `docker`, `nginx`, `sync`, `app`, `deploy` (sync+app), `full` (tudo)

---

## 🔐 SSL (Let's Encrypt)

```bash
# Testar com staging primeiro (sem rate limit)
.\ansible.ps1 ansible-playbook ssl.yml -e "ssl_environment=staging"

# Certificado real
.\ansible.ps1 ansible-playbook ssl.yml -e "ssl_environment=production"
```

> Requer: Nginx instalado, DNS apontando para o servidor, portas 80/443 abertas.

---

## 💾 Backup SQLite

```bash
# Backup do banco principal
.\ansible.ps1 ansible-playbook backup.yml

# Incluir base de referência D&D 3.5
.\ansible.ps1 ansible-playbook backup.yml -e "backup_dnd35=true"
```

Backups salvos em `.devops/backups/<timestamp>/` (git ignored).
