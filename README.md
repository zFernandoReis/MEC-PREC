# MEC System

## Docker Compose

Copie `.env.example` para `.env`, defina `POSTGRES_PASSWORD` e um
`JWT_SECRET_KEY` aleatório de pelo menos 32 caracteres, e execute:

```powershell
docker compose up -d --build
```

O Compose inicia três serviços:

- `postgres`: PostgreSQL 16 com volume persistente `postgres_data`, publicado
  em `localhost:5432`. Use as credenciais `POSTGRES_USER`, `POSTGRES_PASSWORD`
  e `POSTGRES_DB` do `.env`. `POSTGRES_EXTERNAL_PORT` altera a porta no host;
  a comunicação entre containers continua em `postgres:5432`.
- `app`: API em `http://localhost:8000/docs`. Espera o banco ficar saudável,
  cria tabelas ausentes e aplica a migração de `notification_type` antes de
  executar todos os testes em `tests` (unitários e integração), mostrando o
  resultado no log. Após aprovação, importa `dados` e inicia o Uvicorn.
  Falha na preparação, testes ou carga impede a API de iniciar.
- `scheduler`: espera a API ficar saudável, executa os dois jobs imediatamente
  e repete a cada 30 segundos, em um único processo e sem sobrepor ciclos.
  Cada job usa sua própria sessão; falha em um não impede a execução do outro.

O intervalo é contado a partir do início de cada ciclo. Se um ciclo ultrapassar
30 segundos, o próximo começa quando ele terminar. Não há reposição dos ciclos
perdidos enquanto os containers estiverem parados. O scheduler roda enquanto
seu container estiver ativo; a dependência da API é verificada na inicialização.

O agendamento fica em `src/app/bootstrap/notification_scheduler.py`, na função
`run`: `delay = max(0, 30 - (loop.time() - started))`. Os 30 segundos definem
o intervalo entre os inícios dos ciclos. O serviço `scheduler` do
`docker-compose.yml` inicia esse módulo.

Os serviços usam `restart: unless-stopped`: voltam após reiniciar o Docker,
desde que não tenham sido parados manualmente. O Docker precisa estar ativo
no servidor. A API e o scheduler usam a mesma imagem, com dependências de
instaladas a partir de `uv.lock`, incluindo pytest para a validação de startup.
Os arquivos de `tests` e `dados` são incluídos na imagem; o `.env` não é copiado.

A carga inicial segue `users`, `stock`, `vehicles`, `budgets`, remapeando as
relações para os IDs gerados. Usa as mesmas rotas e regras da aplicação em uma
instância interna, sem abrir uma porta HTTP. Consulta o ViaCEP, portanto a
primeira inicialização precisa de acesso à internet. As senhas vêm dos JSONs;
para registros sem senha, configure `MEC_INITIAL_PASSWORD` no `.env`.
Nenhuma senha é registrada no log.
Na carga automática, itens de orçamento sem `tool_id` são associados por
`tool_name` a uma entrada única de `stock.json`, usando o ID gerado na carga.
Nomes ausentes ou ambíguos impedem a importação. O importador HTTP manual
continua exigindo `tool_id` explícito.

Toda a carga ocorre em uma transação. Em falha, os dados da tentativa são
revertidos. Ao concluir, grava `initial_dados_v1` em `bootstrap_ingestions`,
no mesmo banco. Nos próximos reinícios executa os testes novamente e pula a
carga já concluída. Alterações posteriores nos JSONs não são reimportadas
automaticamente. Registros existentes que conflitem com os arquivos fazem a
carga falhar, sem sobrescrevê-los. Os testes atuais de integração verificam a
conexão PostgreSQL; novos testes que alterem dados devem usar banco isolado.
O healthcheck concede até cinco minutos de preparação antes de contabilizar
falhas, para acomodar os testes e as consultas de CEP.

`TZ` define a data local dos jobs (padrão: `America/Sao_Paulo`). Configure
`APP_PORT`, `NOTIFICATION_DAYS_BEFORE` e `NOTIFICATION_BATCH_SIZE` no `.env`
se necessário. Dentro dos containers, o banco sempre é `postgres:5432`.
O volume criado é um banco separado do PostgreSQL instalado no host.
As credenciais `POSTGRES_*` inicializam o volume na primeira execução;
alterá-las no `.env` não altera usuários de um volume já existente.
Se alterar `POSTGRES_PASSWORD` com o volume já inicializado, recrie o container
do banco para receber o novo ambiente e sincronize a senha sem apagar dados:

```powershell
docker compose up -d postgres
powershell -ExecutionPolicy Bypass -File scripts/sync_postgres_credentials.ps1
docker compose up -d --wait --wait-timeout 600
```

O script exige acesso administrativo local ao container e mantém o usuário
`POSTGRES_USER` existente. O healthcheck agora executa uma consulta autenticada:
senha incorreta ou banco ausente impedem a inicialização da API. A mensagem
`password authentication failed` é uma falha de conexão ao iniciar, mesmo
quando a construção da imagem terminou com sucesso.
O bootstrap não executa migrações de outros esquemas legados.

Para acompanhar e encerrar:

```powershell
docker compose logs -f app scheduler
docker compose down
```

`down` preserva o banco. `docker compose down -v` remove o volume e todos
os dados. Após alterar o código, execute novamente `up -d --build`.

## Job de notificações de prazo

Crie as tabelas com `uv run python -m app.bootstrap.create_tables` e execute:

```powershell
uv run python -m app.bootstrap.notify_upcoming_orders
```

O job consulta `orders` em lotes de 100 e cria registros em `notifications`
para ordens com `service_date_end` entre `date.today()` e os próximos 3 dias,
incluindo os dois limites. Usa a data local do processo; configure o servidor
com o fuso horário desejado. Ignora prazos nulos, vencidos e ordens finalizadas
ou entregues. O nome do cliente vem de `users`; os demais dados são copiados
da ordem. Uma ordem com o mesmo prazo e tipo já notificado não gera outro aviso.
Se o prazo mudar, pode gerar uma nova notificação para a nova data.

Para manter um processo independente verificando a cada hora:

```powershell
uv run python -m app.bootstrap.notify_upcoming_orders --days-before 3 --interval-seconds 3600
```

Sem `--interval-seconds`, executa uma vez e encerra, permitindo agendamento
externo. `--days-before 0` verifica apenas os prazos de hoje e `--batch-size`
ajusta o tamanho dos lotes. Cada lote é confirmado em uma transação; em falha,
o lote atual é revertido e os anteriores são preservados. Em modo contínuo,
registra o erro e tenta novamente no próximo intervalo. No PostgreSQL, bloqueia
as ordens do lote com `FOR UPDATE SKIP LOCKED` para coordenar instâncias deste
job. Não cria rotas HTTP nem envia e-mails.

## Job de notificações de atraso

O segundo job cria notificações do tipo `overdue` quando
`service_date_end < date.today()` e `order_status == em_execucao`.
Prazos de hoje, futuros ou nulos e os demais status são ignorados.
O aviso de atraso é independente do aviso `upcoming`: uma ordem pode receber
ambos, mas cada tipo é criado apenas uma vez por ordem e data de término.
Alterar o prazo permite um novo aviso quando a nova data estiver vencida.

Para banco existente, antes de executar qualquer um dos dois jobs atualizados:

```powershell
uv run python -m app.bootstrap.migrate_notification_type
```

A migração pode ser repetida e classifica os avisos existentes como `upcoming`.
Para banco novo, use `app.bootstrap.create_tables`.

Execução única:

```powershell
uv run python -m app.bootstrap.notify_overdue_orders
```

Execução contínua, a cada hora:

```powershell
uv run python -m app.bootstrap.notify_overdue_orders --interval-seconds 3600
```

Também aceita `--batch-size` (padrão: 100) e usa a data local do processo.
Segue as mesmas regras de transação, rollback e repetição em falha do job de
prazo próximo. Execute os jobs como processos independentes da API.

## Autenticação JWT

A implementação fica em `src/app/shared/infrastructure/security`, integrada ao
usuário existente em `modules/users`. O login usa **CPF com 11 dígitos e senha**,
pois o CPF já é único e o e-mail atualmente permite duplicidade. Nenhum usuário
é criado pelo login. O cadastro em `POST /users` exige `password` (12 a 128
caracteres) e calcula o hash Argon2id antes de salvar em `users.password_hash`.
O modelo `User` contém apenas o hash, omitido no repr e nos DTOs de resposta.
`users.token_version` permite revogar as sessões. Não há tabela separada de senhas.

### Preparação

1. Execute `uv sync` e configure as variáveis de banco no `.env` (veja `.env.example`).
2. Gere um segredo com `uv run python -c "import secrets; print(secrets.token_urlsafe(48))"`
   e salve o resultado em `JWT_SECRET_KEY` no `.env`. Use o mesmo segredo em todas
   as instâncias; são exigidos pelo menos 32 caracteres. Sem configuração, a
   emissão/validação de tokens retorna 503, sem usar uma chave padrão.
3. Execute `uv run --env-file .env python -m app.bootstrap.create_tables`.
   Para banco **já existente**, pare a API e execute também:

   ```powershell
   uv run --env-file .env python -m app.bootstrap.migrate_user_passwords
   ```

   Essa migração adiciona `password_hash` e `token_version` à tabela `users`.
   Caso exista a antiga `user_credentials`, transfere os hashes e versões antes
   de removê-la. Preserva hashes já definidos em `users` e pode ser repetida.
   Registros legados sem senha continuam com hash nulo e não podem fazer login.
   `create_tables` sozinho não altera colunas de uma tabela já existente.
4. Para usuários antigos sem senha, ou para redefinição administrativa:

   ```powershell
   uv run --env-file .env python -m app.shared.infrastructure.security.set_password --cpf 52998224725
   ```

   O comando solicita a senha e a confirmação sem exibi-las nem recebê-las em
   argumentos. Exige de 12 a 128 caracteres e também permite redefinição
   administrativa, revogando as sessões anteriores. Ele não altera o papel do
   usuário. Para administrar usuários pela API, use uma conta já cadastrada
   com `role=admin`. Não há cadastro público nem redefinição pública por CPF.
5. Inicie a API com `uv run uvicorn app.main:app --app-dir src --reload`.

### Rotas

| Método | Rota | Corpo JSON / comportamento |
| --- | --- | --- |
| POST | `/auth/login` | `{"cpf":"52998224725","password":"sua-senha-segura"}`; retorna access e refresh token |
| POST | `/auth/refresh` | `{"refresh_token":"..."}`; consome o refresh e emite um novo par |
| GET | `/auth/me` | Retorna o usuário do access token atual |
| POST | `/auth/change-password` | `{"current_password":"...","new_password":"..."}`; exige access token e senha atual; retorna 204 |
| POST | `/auth/logout` | Exige access token; revoga a sessão e retorna 204 |

Envie `Authorization: Bearer <access_token>` nas rotas protegidas. No Swagger,
use **Authorize** e cole o access token retornado pelo login.
Todas as rotas de usuários exigem administrador, inclusive criação e mudança
de papel. As rotas de veículos, estoque e orçamentos exigem usuário autenticado;
esses três recursos ainda não têm restrição por proprietário.

Nas ordens de serviço, usuários com papel `client` podem apenas consultar suas
próprias OS. `GET /orders` filtra pelo ID do usuário autenticado antes de aplicar
a paginação; parâmetros enviados pelo cliente não alteram esse proprietário.
`GET /orders/{order_id}` retorna 404 tanto para uma OS alheia quanto inexistente.
POST, PATCH e DELETE de ordens retornam 403 para clientes, inclusive nas próprias
OS. Os papéis internos `admin`, `manager`, `technical` e `financial` mantêm acesso
à consulta de todas as ordens e às operações de criação, alteração e exclusão.
Sem autenticação, as rotas de ordens retornam 401.

### CRUD de ordens de serviço

| Método | Rota | Resultado |
| --- | --- | --- |
| POST | `/orders` | Cria uma OS (201) |
| GET | `/orders?offset=0&limit=100` | Lista OS com paginação e escopo do usuário |
| GET | `/orders/{order_id}` | Consulta uma OS (200) |
| PATCH | `/orders/{order_id}` | Atualiza somente os campos enviados (200) |
| DELETE | `/orders/{order_id}` | Exclui uma OS, sem corpo de resposta (204) |

O PATCH aceita, por exemplo, `{"service_name":"Alinhamento"}`. Campos omitidos
mantêm seu valor. `service_description` e `duration_service_days` aceitam `null`
para limpar o campo; os demais campos não aceitam `null` explícito. Identificadores
gerados pelo sistema não podem ser alterados no corpo da requisição. Consulta,
atualização e exclusão de OS inexistente retornam 404. Conflitos de integridade
do banco retornam 409. As restrições de autorização descritas acima se aplicam
a todas essas operações. Exemplos executáveis estão em [http/orders.http](http/orders.http).

Exemplo no PowerShell (a senha fica oculta durante a digitação):

```powershell
$credential = Get-Credential -UserName "52998224725" -Message "Login MEC: CPF e senha"
$body = @{ cpf = $credential.UserName; password = $credential.GetNetworkCredential().Password } | ConvertTo-Json
$tokens = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/auth/login -ContentType application/json -Body $body
$headers = @{ Authorization = "Bearer $($tokens.access_token)" }
Invoke-RestMethod -Uri http://127.0.0.1:8000/auth/me -Headers $headers
```

O access token expira em 15 minutos e o refresh em 7 dias, configuráveis com
`JWT_ACCESS_TOKEN_MINUTES` (1–60) e `JWT_REFRESH_TOKEN_DAYS` (1–30).
Os tokens usam HS256, issuer (`JWT_ISSUER`), audience (`JWT_AUDIENCE`), subject,
expiração, tipo, identificador aleatório e versão de sessão. A validação
consulta o usuário e a credencial persistidos, permitindo revogação imediata.
Access e refresh não são intercambiáveis.

Há **uma sessão ativa por usuário**: novo login e refresh invalidam o par
anterior; o refresh só pode ser consumido uma vez, inclusive em concorrência.
Logout e mudança/redefinição de senha invalidam todos os tokens anteriores.
Após mudar a senha, faça login novamente. Credenciais incorretas e tokens
inválidos retornam 401; falta de permissão retorna 403; entrada inválida retorna
422. Respostas de validação de autenticação não repetem senhas/tokens recebidos.
Use HTTPS fora do ambiente local. A API não implementa entrega de e-mails de
recuperação nem limitação de tentativas; configure esta última no gateway de
produção. Referência das bibliotecas:
[FastAPI: JWT e Argon2](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/).

Execute `uv run pytest tests/unit/test_security.py -q` para validar o fluxo com
os repositórios reais em SQLite isolado, sem consultar o PostgreSQL configurado.

## Ingestão dos arquivos JSON pela API

Com a API em execução, importe os arquivos de `dados/`:

```powershell
uv run python -m app.bootstrap.ingest_json --dry-run
$env:MEC_ACCESS_TOKEN = $tokens.access_token # obtido no login de um administrador
uv run python -m app.bootstrap.ingest_json --base-url http://127.0.0.1:8000
```

Os usuários importados também precisam de `password`. Para os arquivos de
amostra, que não contêm senhas, defina `MEC_INITIAL_PASSWORD` com uma senha de
12 a 128 caracteres antes da validação/importação. Ela será aplicada apenas a
registros sem o campo `password`; senhas explícitas são preservadas. Use esse
recurso para amostras locais. A senha é enviada no corpo HTTP e transformada
em hash pela API; não é impressa nos logs nem gravada nos JSONs pelo script.

O script valida todos os arquivos selecionados antes do primeiro envio e faz
um POST por registro: `users.json` → `/users`, `stock.json` → `/stock`,
`vehicles.json` → `/vehicles` e `budgets.json` → `/budgets`, nessa ordem.
Não acessa o banco diretamente. Aceita `--data-dir`, `--timeout` e seleção:

```powershell
uv run python -m app.bootstrap.ingest_json --resources users
uv run python -m app.bootstrap.ingest_json --data-dir ./dados --resources stock vehicles
```

Quando usuários e veículos são importados juntos, `owner_id`, `technical_id`
e `client_id` nos arquivos representam a posição do usuário em `users.json`,
começando em 1. O script substitui essas referências pelos IDs retornados pela
API. Da mesma forma, se veículos e orçamentos forem selecionados juntos,
`vehicle_id` representa a posição em `vehicles.json` e é substituído pelo ID
criado. Quando o arquivo referenciado não é selecionado, informe os IDs reais
já existentes no banco. A ordem dos arquivos não deve ser alterada sem ajustar
essas referências.

Os arquivos devem seguir os DTOs de criação da API. Nos dados de exemplo,
os CPFs fictícios possuem dígitos verificadores calculados para passar pela
validação de domínio da API.
Os 50 endereços da amostra usam 25 CEPs distintos de 24 UFs, cobrindo as
cinco regiões do Brasil, confirmados no ViaCEP em 21/10/2026. Cada CEP aparece
em dois usuários; número e complemento foram preservados como dados fictícios.
`duration_service_days` e `replacement_time_days` foram arredondados para cima
para representar dias inteiros; os valores exatos em horas foram preservados.
`engine_capacity` está em cm³ inteiros (por exemplo, 1,6 L → 1600 cm³).
Os tipos `carro`, `suv` e `picape` foram classificados como `car`, conforme
o enum atual, e `gasolina` foi convertido em `gasoline`. Os demais combustíveis
aceitos são `ethanol`, `flex`, `diesel`, `electric` e `hybrid`.
Nos orçamentos de exemplo, `vehicle_id` distribui os serviços entre os veículos
do respectivo cliente, seguindo a ordem de `vehicles.json` e reiniciando a
distribuição quando os veículos desse cliente se esgotam.
O script não arredonda nem inventa relações entre dados durante a ingestão.
O `--dry-run` valida o formato local, sem consultar o servidor; regras de
domínio, CEP, conflitos e referências no banco são verificadas pela API.

Em erro de validação, nenhum registro é enviado. Em erro HTTP, o script para
e sai com código 1; os POSTs anteriores permanecem gravados. Não há repetição
automática nem deduplicação: confira a API antes de executar novamente,
especialmente após timeout, pois o último POST pode ter sido persistido.

## Logging compartilhado

Use o mesmo objeto em todos os módulos:

```python
from app.shared.infrastructure.logging import logger

logger.debug("Processando item de estoque: tool_id=%s", tool_id)
```

A saída inclui data/hora, nível, nome do arquivo, método/função, número da
linha da chamada e o comentário informado. O contexto é capturado automaticamente.
Também estão disponíveis `info`, `warning`, `error`, `critical` e `exception`
(este último inclui o traceback quando usado dentro de um `except`).

A API configura o console em `create_app`. O nível padrão da aplicação é
`DEBUG`; configure `LOG_LEVEL=INFO` no `.env` para ocultar os detalhes de
depuração. Os níveis aceitos são `DEBUG`, `INFO`, `WARNING`, `ERROR` e `CRITICAL`.
Os casos de uso de usuários, orçamentos e estoque registram as etapas de
processamento, resultados e registros não encontrados. Também há logs nas
rotas, repositórios, resolução de dependências e consultas ao ViaCEP.
As mensagens usam identificadores e contagens, sem incluir CPF, e-mail,
endereço ou DTOs completos.

Em scripts independentes, chame
`configure_logging()` antes de registrar mensagens; use
`configure_logging("DEBUG")` para habilitar mensagens de depuração.

## API de usuários

Execute `uv run uvicorn app.main:app --app-dir src --reload`.
A documentação Swagger UI fica em `http://127.0.0.1:8000/docs`.
O ReDoc fica em `http://127.0.0.1:8000/redoc` e o schema OpenAPI em
`http://127.0.0.1:8000/openapi.json`.
Essas rotas são habilitadas explicitamente em `create_app`, inclusive ao
executar sem `--reload`. O comando `uv build` apenas gera o pacote;
para acessar o Swagger, inicie o servidor com o comando acima.

| Método | Rota | Resultado |
| --- | --- | --- |
| POST | `/users` | Cria usuário (201) |
| GET | `/users?offset=0&limit=100` | Lista usuários com paginação |
| GET | `/users/{user_id}` | Consulta usuário |
| PATCH | `/users/{user_id}` | Atualiza campos enviados |
| DELETE | `/users/{user_id}` | Exclui usuário (204) |

O `id` público é um inteiro positivo gerado sequencialmente pelo banco:
use, por exemplo, `/users/1` para consultar, atualizar ou excluir.
O `system_id` é um UUID gerado pelo sistema, retornado na criação e atualização,
mas omitido nas respostas de consulta e listagem;
nenhum dos dois deve ser enviado no corpo de criação ou atualização.
Sequências podem ter intervalos após exclusões ou transações desfeitas.
`create_at` e `update_at` são datas de persistência; o ORM atualiza
`update_at` quando emite uma alteração SQL. No PostgreSQL, as colunas
armazenam datas com fuso horário.

### Migração do ID antigo

Para uma tabela `cliente` existente com chave UUID, pare a aplicação e execute:

```powershell
uv run --env-file .env python -m app.bootstrap.migrate_client_ids
```

A migração preserva os UUIDs na coluna `system_id`, cria a chave inteira
com identity e adiciona as datas. Os registros antigos recebem o horário
da migração nas duas datas, pois não havia histórico anterior.
A operação é transacional e pode ser repetida. Caso existam foreign keys
para `cliente`, ela interrompe sem alterar os dados: essas relações precisam
ser migradas junto com a chave. Depois, reinicie a aplicação.
Para um banco novo, use `create_tables`; ele não migra tabelas existentes.

Exemplo de criação:

```json
{
  "primary_name": "Fernando",
  "secondary_name": "Silva",
  "cpf": "52998224725",
  "email": "fernando@example.com",
  "password": "uma-senha-segura-123",
  "role": "client",
  "address": {"cep": "01001000", "number": "10", "complement": "Sala 1"}
}
```

O bootstrap em `app.bootstrap.users` conecta os casos de uso ao ViaCEP.
O cliente HTTP é aberto e fechado pelo lifespan da aplicação.
As rotas ficam em `modules/users/infrastructure/http`.

### Configuração de persistência

A aplicação usa `SQLAlchemyUserRepository` por padrão, com uma sessão
PostgreSQL por requisição. Configure as variáveis `POSTGRES_*` no `.env`
e crie a tabela com `uv run --env-file .env python -m app.bootstrap.create_tables`.
Para conectar outra implementação, crie a aplicação com
`create_app(user_repository=repository)` ou substitua a dependência
`get_user_repository`.
O contrato está em `application/ports/user_repository.py`.
Não compartilhe uma sessão SQLAlchemy entre requisições concorrentes.

Usuários inexistentes retornam 404, entradas inválidas retornam 422 e
falhas HTTP do serviço de CEP retornam 502. Conflitos de integridade,
como CPF duplicado, retornam 409.

Execute os testes isolados com
`uv run pytest tests/unit/test_users_router.py -q`.
Eles usam um repositório de teste e respostas simuladas do ViaCEP.
