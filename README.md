# MEC System

## 1. Objetivo do projeto

Centralizar o atendimento e a execução de serviços de uma oficina mecânica, reduzindo a dependência de anotações e planilhas dispersas. O MEC System organiza clientes, veículos, estoque, orçamentos e ordens de serviço para facilitar o acompanhamento dos reparos, dos prazos e das aprovações.

## 2. Descrição resumida da solução

O projeto entrega uma API HTTP/JSON com autenticação e controle de acesso por perfil. A equipe da oficina pode administrar cadastros, elaborar orçamentos e conduzir ordens de serviço; clientes autenticados podem consultar e aprovar suas próprias ordens.

O fluxo de uma ordem de serviço é:

```text
recebida → em_diagnostico → aguardando_aprovacao → em_execucao → finalizada → entregue
```

As transições registram histórico e verificam permissões, versão e pré-condições. A aprovação é registrada separadamente do início da execução. Jobs gravam notificações de prazos próximos e atrasos no banco, sem envio de e-mails. A implementação atual é um backend; a interação pode ser feita pelo Swagger ou por clientes HTTP.

## 3. Arquitetura utilizada

A aplicação é um **monólito modular**, organizado em camadas e contratos de persistência. Os módulos compartilham a aplicação FastAPI e o banco PostgreSQL:

| Módulo | Responsabilidades |
| --- | --- |
| `users` | Usuários, endereços e veículos. |
| `quotes` | Orçamentos e estoque. |
| `orders` | Ordens de serviço, workflow, histórico e notificações. |

Cada módulo separa `domain` (entidades e regras), `application` (casos de uso, DTOs e contratos) e `infrastructure` (rotas HTTP, modelos e repositórios). `bootstrap` conecta as implementações e oferece comandos operacionais. `shared/infrastructure` concentra banco, logging e segurança.

```text
Cliente HTTP → FastAPI → Casos de uso → Repositórios → PostgreSQL
                              ↓
                        Regras de domínio

API → ViaCEP (consulta de endereços)
Scheduler → Jobs de notificações → PostgreSQL
```

O Docker Compose executa três serviços: `app`, `postgres` e `scheduler`. API e scheduler usam a mesma imagem; o scheduler roda em processo separado e inicia ciclos a cada 30 segundos, sem sobreposição. O banco usa volume persistente. As requisições utilizam sessões próprias de banco.

Detalhes das camadas e diagramas estão na [documentação de arquitetura](docs/03-arquitetura.md), e os relacionamentos no [modelo de dados](docs/04-modelo-de-dados.md).

## 4. Tecnologias utilizadas

| Tecnologia | Utilização |
| --- | --- |
| Python 3.12+ | Linguagem da API, casos de uso, jobs e scripts; Docker usa 3.12. |
| FastAPI e Pydantic | Rotas HTTP, validação, dependências e contratos da API. |
| Uvicorn | Servidor ASGI da aplicação. |
| PostgreSQL 16 | Persistência relacional; versão utilizada pelo Compose. |
| SQLAlchemy, asyncpg e psycopg | ORM e drivers de acesso ao PostgreSQL. |
| HTTPX | Comunicação HTTP e integração com ViaCEP. |
| PyJWT e pwdlib/Argon2id | Tokens JWT e hash de senhas. |
| pydantic-settings | Carregamento e validação das configurações. |
| pytest e pytest-asyncio | Testes unitários e de integração, incluindo código assíncrono. |
| uv | Gerenciamento do ambiente, dependências e execução de comandos. |
| Docker e Docker Compose | Construção da imagem e execução dos serviços. |
| OpenAPI, Swagger UI e ReDoc | Documentação e exploração da API. |

As dependências estão declaradas em [pyproject.toml](pyproject.toml), com versões resolvidas em [uv.lock](uv.lock).

## 5. Pré-requisitos

**Para executar com Docker:**

- Docker com suporte a containers Linux e Docker Compose v2, com o serviço Docker ativo.
- Acesso à internet para obter imagens/dependências e consultar o ViaCEP na carga inicial.
- Portas 8000 (API) e 5432 (banco) disponíveis, ou portas alternativas no `.env`.

**Para executar localmente:**

- Python 3.12 ou superior e `uv` disponíveis no terminal.
- PostgreSQL disponível, com banco criado e credenciais configuradas.
- Permissão para criar tabelas e, nos testes integrados, criar e remover schemas temporários.
- Acesso ao ViaCEP para cadastrar endereços e executar a carga inicial.

Os comandos abaixo usam PowerShell e devem ser executados na raiz do projeto. Para configuração, copie `.env.example` para `.env`, sem substituir um arquivo já configurado. Defina `POSTGRES_PASSWORD` e um `JWT_SECRET_KEY` aleatório com pelo menos 32 caracteres. Na execução local, configure também `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER` e `POSTGRES_DB`.

## 6. Instruções para execução

### Com Docker Compose

Na primeira configuração:

```powershell
Copy-Item .env.example .env
```

Edite o `.env` conforme os pré-requisitos. Se houver usuários sem `password` em `dados/users.json`, configure `MEC_INITIAL_PASSWORD` com 12 a 128 caracteres. Senhas explícitas nos registros são preservadas.

```powershell
docker compose up -d --build
docker compose logs -f app scheduler
```

A API fica disponível em `http://localhost:8000` após o startup concluir. O processo cria tabelas ausentes, aplica as migrações de notificações e workflow, executa os testes, importa os usuários iniciais e inicia o Uvicorn. Uma falha nessas etapas impede a API de iniciar.

A carga inicial importa somente `dados/users.json`, consulta o ViaCEP e é transacional. O marcador `initial_dados_v1` impede repetir a carga em reinícios; mudanças posteriores no JSON não atualizam registros já importados. Os demais recursos têm importação manual descrita no [guia operacional](docs/06-guia-operacional.md).

`APP_PORT` altera a porta da API no host; `POSTGRES_EXTERNAL_PORT` altera a porta do banco no host. Dentro dos containers, o banco permanece em `postgres:5432`. `TZ` usa `America/Sao_Paulo` por padrão.

Para encerrar, preservando o banco:

```powershell
docker compose down
```

`docker compose down -v` também apaga o volume e seus dados. Após alterar código, repita `docker compose up -d --build`. Alterar credenciais no `.env` não altera usuários de um volume PostgreSQL existente; consulte a sincronização de credenciais no [guia operacional](docs/06-guia-operacional.md).

### Execução local

Com Python, uv, banco e `.env` preparados:

```powershell
uv sync --frozen
```

Para gerar o segredo JWT, copie a saída deste comando para `JWT_SECRET_KEY` no `.env`:

```powershell
uv run python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Prepare o banco e carregue os usuários de demonstração:

```powershell
uv run --env-file .env python -m app.bootstrap.create_tables
uv run --env-file .env python -m app.bootstrap.migrate_notification_type
uv run --env-file .env python -m app.bootstrap.migrate_order_workflow
$env:MEC_DATA_DIR = (Resolve-Path dados).Path
uv run --env-file .env python -m app.bootstrap.seed_initial_data
uv run --env-file .env uvicorn app.main:app --app-dir src --reload
```

A API fica disponível em `http://127.0.0.1:8000`. O comando local do Uvicorn não executa os testes nem inicia o scheduler automaticamente. `create_tables` cria tabelas ausentes; não migra colunas de tabelas existentes. As migrações listadas tratam apenas notificações e workflow, e devem ser executadas com API e jobs parados.

Para executar os jobs uma vez, em outro terminal:

```powershell
uv run --env-file .env python -m app.bootstrap.notify_upcoming_orders
uv run --env-file .env python -m app.bootstrap.notify_overdue_orders
```

Para execução contínua no Windows, cada job aceita `--interval-seconds 30`, em terminais separados. O Compose já mantém o scheduler ativo.

## 7. Instruções para execução dos testes

Com dependências instaladas e `.env` configurado, execute toda a suíte:

```powershell
uv run --env-file .env pytest tests -q
```

Para executar por categoria:

```powershell
uv run --env-file .env pytest tests/unit -q
uv run --env-file .env pytest tests/integration -q
```

Os testes unitários usam substitutos de dependências e, em cenários de segurança, SQLite isolado. A configuração de ambiente ainda é necessária para importar a aplicação. Os testes integrados exigem PostgreSQL acessível; verificam a conexão e o workflow com HTTP, JWT e repositórios reais. Os cenários de workflow criam e removem schemas `test_orders_<uuid>`, exigindo permissão no banco configurado.

Com o serviço `app` em execução, também é possível executar a suíte dentro do container:

```powershell
docker compose exec app python -m pytest tests -q -p no:cacheprovider
```

O startup Docker executa a suíte automaticamente antes de disponibilizar a API. O resultado aparece em `docker compose logs app`.

## 8. Instruções para acesso ao Swagger ou documentação da API

Com a aplicação iniciada e usando a porta padrão:

| Interface | Endereço |
| --- | --- |
| Swagger UI | [http://localhost:8000/docs](http://localhost:8000/docs) |
| ReDoc | [http://localhost:8000/redoc](http://localhost:8000/redoc) |
| Schema OpenAPI | [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json) |

Se alterar `APP_PORT`, ajuste a porta dos endereços. No Swagger, execute `POST /auth/login`, copie o `access_token`, clique em **Authorize** e cole o token para acessar rotas protegidas.

Exemplos de requisições estão em [http/](http/), com instruções em [http/README.md](http/README.md). Os contratos e detalhes de operação também estão no [guia operacional](docs/06-guia-operacional.md).

## 9. Decisão e justificativa do banco de dados escolhido

O banco escolhido é o **PostgreSQL**, na versão 16 do ambiente Docker, por ser **open source e amplamente utilizado no mercado**. Essas características permitem utilizar uma solução consolidada, com uma comunidade ativa e ampla disponibilidade de conhecimento e profissionais.

O modelo relacional, com uso de SQL, atende plenamente às necessidades da proposta: organizar usuários, veículos, orçamentos e ordens de serviço e manter a integridade dos relacionamentos entre esses registros. Chaves primárias e estrangeiras, restrições de unicidade e transações ajudam a garantir a consistência dos dados nas operações da oficina.

Consulte o [modelo de dados](docs/04-modelo-de-dados.md) para os relacionamentos e as limitações de integridade dos campos JSON. O volume `postgres_data` preserva os dados entre recriações dos containers. O SQLite utilizado em testes isolados não substitui o banco da aplicação.

## 10. Usuários, credenciais de demonstração ou procedimento de autenticação

A autenticação usa **CPF com 11 dígitos e senha**. A carga inicial cria os usuários de [dados/users.json](dados/users.json); consulte nesse arquivo o CPF e o perfil da conta desejada. A senha inicial corresponde ao campo `password` do registro ou, quando ausente, ao valor de `MEC_INITIAL_PASSWORD` usado na carga. Alterar o JSON ou essa variável após a carga não redefine senhas existentes.

Para administrar usuários, escolha uma conta com `role=admin`. Não há cadastro público, e o login não cria usuários. Para redefinir a senha de um usuário existente localmente:

```powershell
uv run --env-file .env python -m app.shared.infrastructure.security.set_password --cpf <CPF_DO_USUARIO>
```

No Docker:

```powershell
docker compose exec app python -m app.shared.infrastructure.security.set_password --cpf <CPF_DO_USUARIO>
```

Substitua `<CPF_DO_USUARIO>` pelo CPF real da amostra. O comando solicita e confirma uma senha de 12 a 128 caracteres sem exibi-la, revoga sessões anteriores e preserva o perfil.

Faça login pelo Swagger ou envie:

```http
POST /auth/login
Content-Type: application/json

{"cpf":"<CPF_DO_USUARIO>","password":"<SENHA_CONFIGURADA>"}
```

A resposta contém `access_token` e `refresh_token`. Envie `Authorization: Bearer <access_token>` nas rotas protegidas. Consulte `GET /auth/me` para verificar a identidade autenticada.

| Perfil | Acesso principal |
| --- | --- |
| `admin` | Administração de usuários e ações do workflow. |
| `manager` | Ações do workflow, respeitando transições e pré-condições. |
| `technical` | Ações técnicas nas OS pelas quais é responsável. |
| `financial` | Consulta de OS, sem comandos do workflow. |
| `client` | Consulta e aprovação das próprias OS. |

Veículos, estoque e orçamentos exigem autenticação, mas ainda não possuem restrição por proprietário. As regras completas das ordens estão no [guia operacional](docs/06-guia-operacional.md).

O access token expira em 15 minutos e o refresh em 7 dias por padrão, configuráveis no `.env`. Há uma sessão ativa por usuário: novo login ou refresh invalida o par anterior. `POST /auth/refresh` renova tokens; `POST /auth/logout` encerra a sessão; `POST /auth/change-password` altera a senha e revoga tokens. As senhas são persistidas como hash Argon2id.

## 11. Estrutura dos principais diretórios do projeto

```text
mec-system/
├── dados/                      # JSONs de demonstração e importação
├── docs/                       # Wiki, arquitetura, modelo de dados e guia operacional
├── http/                       # Requisições de exemplo para REST Client
├── scripts/                    # Scripts de suporte operacional
├── src/app/
│   ├── main.py                 # Criação da API, routers e ciclo de vida
│   ├── config.py               # Configurações de ambiente
│   ├── bootstrap/              # Composição, carga inicial, migrações e jobs
│   ├── modules/
│   │   ├── users/              # Usuários, endereços e veículos
│   │   ├── quotes/             # Orçamentos e estoque
│   │   └── orders/             # Ordens, workflow, histórico e notificações
│   └── shared/infrastructure/
│       ├── database/           # Engine, sessões e base SQLAlchemy
│       ├── logging/            # Logger compartilhado
│       └── security/           # Autenticação, autorização e senhas
├── tests/
│   ├── unit/                  # Testes isolados
│   └── integration/           # Testes com PostgreSQL
├── .env.example               # Modelo de configuração
├── docker-compose.yml         # Serviços e volume persistente
├── Dockerfile                 # Imagem da API e do scheduler
├── pyproject.toml             # Metadados, dependências e configuração de testes
├── uv.lock                    # Versões resolvidas das dependências
└── README.md                  # Visão geral e instruções de uso
```

Dentro dos módulos, as pastas `domain/`, `application/` e `infrastructure/` separam as responsabilidades descritas na seção de arquitetura. A [wiki](docs/README.md) reúne a documentação complementar.
