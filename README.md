# MEC System

## Ingestão dos arquivos JSON pela API

Com a API em execução, importe os arquivos de `dados/`:

```powershell
uv run python -m app.bootstrap.ingest_json --dry-run
uv run python -m app.bootstrap.ingest_json --base-url http://127.0.0.1:8000
```

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
