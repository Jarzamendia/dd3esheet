$imageName = "dd3esheet-ansible"

# Verificar se a imagem já existe, se não, builda
$imageExists = docker images -q $imageName
if (-not $imageExists) {
    Write-Host "Construindo a imagem Docker do Ansible..." -ForegroundColor Cyan
    docker build -t $imageName .
}

if ($args.Count -eq 0) {
    Write-Host "Uso: .\ansible.ps1 <comando> [argumentos]"
    Write-Host "Exemplo: .\ansible.ps1 ansible-playbook deploy.yml"
    exit 1
}

# Prepara os argumentos com aspas se tiverem espaços
$safeArgs = $args | ForEach-Object { if ($_ -match '\s') { "`"$_`"" } else { $_ } }
$argsString = $safeArgs -join ' '

# Resolve a raiz do repositório (uma pasta acima do .devops)
$repoRoot = Split-Path -Path $PWD -Parent

# Executa o container mapeando a raiz e entrando na pasta .devops
docker run --rm -i `
  -e "ANSIBLE_CONFIG=/workspace/.devops/ansible.cfg" `
  -v "${repoRoot}:/workspace" `
  -w "/workspace/.devops" `
  -v "${HOME}/.ssh:/tmp_ssh:ro" `
  --entrypoint sh `
  $imageName -c "mkdir -p /root/.ssh && cp /tmp_ssh/id_* /root/.ssh/ 2>/dev/null; chmod 600 /root/.ssh/id_* 2>/dev/null; exec $argsString"
