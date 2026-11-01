# Alinha a senha configurada no Compose ao usuário existente, sem apagar dados.
# Execute da raiz do projeto. Exige acesso administrativo local ao container.
$ErrorActionPreference = 'Stop'
@'
\getenv configured_user POSTGRES_USER
\getenv configured_password POSTGRES_PASSWORD
SELECT format('ALTER ROLE %I PASSWORD %L', :'configured_user', :'configured_password') \gexec
'@ | docker compose exec -T postgres sh -c 'exec psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d postgres'
if ($LASTEXITCODE -ne 0) {
    throw 'Não foi possível sincronizar a senha do PostgreSQL.'
}
Write-Host 'Senha sincronizada. Os dados foram preservados.'
