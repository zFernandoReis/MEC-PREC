# 2 — Stack utilizada

[Índice da wiki](README.md) · [Anterior: Introdução](01-introducao.md) · [Próximo: Arquitetura](03-arquitetura.md)

As funções descritas abaixo foram conferidas no código. As justificativas expressam a adequação das escolhas ao contexto da oficina e os critérios deste projeto: praticidade, documentação, presença no mercado e facilidade de manutenção. Não representam um levantamento histórico de decisões ou uma medição de participação de mercado.

## Python

**O que é e qual sua função:** Python é a linguagem utilizada para implementar a API, as regras de negócio, a persistência, os jobs e os scripts. O [pyproject.toml](../pyproject.toml) declara Python `>=3.12`, e a imagem Docker utiliza Python 3.12. A linguagem oferece sintaxe legível e recursos para programação assíncrona, empregados nas operações de banco e HTTP. [Documentação do Python](https://docs.python.org/3/tutorial/).

**Justificativa:** a escolha considera seu uso amplo no mercado, a documentação robusta e o ecossistema de bibliotecas. Esses fatores facilitam a formação da equipe, a manutenção e a evolução das regras de atendimento, sem exigir ferramentas próprias para tarefas comuns de backend.

## SQL e PostgreSQL

**O que são e qual sua função:** SQL é a linguagem de consulta e manipulação de bancos relacionais; PostgreSQL é o sistema gerenciador adotado. Ele armazena usuários, veículos, orçamentos, estoque, ordens e notificações. O Compose utiliza PostgreSQL 16, com volume persistente. Os modelos usam chaves estrangeiras, identificadores únicos e uma coluna JSONB para os itens do orçamento. [Documentação do PostgreSQL 16](https://www.postgresql.org/docs/16/intro-whatis.html).

**Justificativa:** a escolha combina praticidade, documentação extensa e uso consolidado no mercado. O modelo relacional se ajusta às relações entre cliente, veículo, orçamento e ordem, enquanto transações e restrições ajudam a preservar consistência. O JSONB permite armazenar a lista de itens de um orçamento, com as limitações de integridade explicadas no [MER](04-modelo-de-dados.md).

## uv

**O que é e qual sua função:** ferramenta de gestão de projetos, ambientes e dependências Python. Neste projeto, `pyproject.toml` declara dependências e `uv.lock` registra a resolução; o Docker executa `uv sync --frozen --no-editable`. Comandos locais usam `uv run`. [Documentação do uv](https://docs.astral.sh/uv/).

**Justificativa:** centraliza tarefas de preparação e execução, reduz passos manuais e facilita reproduzir as versões resolvidas. A documentação e a integração com o ecossistema Python favorecem a adoção pela equipe. O lockfile controla dependências, mas não substitui a configuração do ambiente e do banco.

## Docker e Docker Compose

**O que são e qual sua função:** Docker empacota a aplicação e seu ambiente em uma imagem; Compose descreve os serviços e suas dependências. O [Dockerfile](../Dockerfile) constrói a imagem compartilhada pela API e pelo scheduler; o [Compose](../docker-compose.yml) define `app`, `scheduler` e `postgres`, incluindo healthchecks e persistência do banco. [Documentação do Docker](https://docs.docker.com/get-started/docker-overview/).

**Justificativa:** a presença no mercado, a documentação e a praticidade operacional tornam a implantação mais previsível. API, banco e jobs podem ser preparados de forma consistente, reduzindo diferenças entre máquinas de desenvolvimento.

## SQLAlchemy

**O que é e qual sua função:** biblioteca de acesso SQL e ORM, responsável por mapear classes para tabelas e construir consultas. Os modelos em `infrastructure/models` descrevem o esquema; os repositórios convertem entidades de domínio em modelos e executam persistência. A configuração compartilhada oferece engine e sessões assíncronas com `asyncpg`. [Documentação oficial](https://www.sqlalchemy.org/).

**Justificativa:** seu uso consolidado, documentação e integração com PostgreSQL reduzem a necessidade de código repetitivo. A separação por repositórios concentra detalhes de persistência, embora recursos específicos como JSONB continuem vinculando parte da solução ao PostgreSQL.

## FastAPI

**O que é e qual sua função:** framework web que organiza rotas HTTP, dependências, validação e documentação OpenAPI. Em `main.py`, reúne os routers, configura o ciclo de vida do cliente HTTP e registra os tratamentos globais de erros. Expõe Swagger em `/docs` e ReDoc em `/redoc`. [Documentação do FastAPI](https://fastapi.tiangolo.com/).

**Justificativa:** a documentação extensa e a integração com tipagem, Pydantic e funções assíncronas simplificam a construção e manutenção da API. A documentação interativa facilita entender e experimentar os contratos consumidos por futuras interfaces.

## Pydantic e pydantic-settings

**O que são e qual sua função:** Pydantic valida e serializa dados a partir de modelos tipados. É usado nos DTOs e schemas para campos obrigatórios, formatos, limites e respostas. `pydantic-settings` carrega e valida a configuração em `config.py` a partir do ambiente e do `.env`. Pydantic é importado pelo código, mas não aparece como dependência direta no `pyproject.toml`; é resolvido pelas dependências do projeto. [Documentação do Pydantic](https://docs.pydantic.dev/latest/).

**Justificativa:** a documentação robusta e a integração com FastAPI permitem definir contratos claros com pouco código repetitivo. A validação na entrada ajuda a identificar problemas antes da execução dos casos de uso; as regras de negócio continuam distribuídas nas entidades e nos casos de uso.

## Demais componentes

| Tecnologia | Função no projeto | Justificativa de adequação |
| --- | --- | --- |
| Uvicorn | Servidor ASGI que executa a aplicação FastAPI. | Integração direta com a stack assíncrona e operação simples. |
| asyncpg | Driver PostgreSQL utilizado pelo engine `postgresql+asyncpg`. | Permite acesso assíncrono ao banco integrado ao SQLAlchemy. |
| psycopg com extra binary | Driver PostgreSQL declarado nas dependências; o engine principal utiliza asyncpg. | Disponibiliza outra opção de acesso PostgreSQL; não deve ser confundido com o driver efetivamente usado pela API. |
| HTTPX | Cliente HTTP assíncrono para o ViaCEP e para rotinas de importação/teste da API. | API consistente para integrações HTTP e suporte a transporte ASGI nos testes e bootstrap. |
| email-validator | Suporte à validação de campos de e-mail utilizados com Pydantic. | Evita implementar manualmente validações de formato. |
| pwdlib com Argon2 | Cria e verifica hashes de senhas. | Utiliza biblioteca especializada para uma responsabilidade de segurança. |
| PyJWT | Emite e valida tokens de autenticação. | Integra autenticação por tokens ao backend sem implementar manualmente o formato JWT. |
| pytest e pytest-asyncio | Executam testes, incluindo funções assíncronas. | Facilitam validar regras, repositórios, rotas e jobs com ferramentas do ecossistema Python. |
| Hatchling | Backend de build configurado para empacotar `src/app`. | Segue o fluxo de empacotamento baseado em `pyproject.toml`. |

Os requisitos mínimos estão no [pyproject.toml](../pyproject.toml); as versões resolvidas estão no [uv.lock](../uv.lock). Os números declarados com `>=` não devem ser tratados como versões exatas instaladas.
