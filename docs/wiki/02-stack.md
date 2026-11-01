# 2 — Stack utilizada

[Índice da wiki](README.md) · [Anterior: Introdução](01-introducao.md) · [Próximo: Arquitetura](03-arquitetura.md)

## Python

**O que é e qual sua função:** Python é a linguagem utilizada para implementar a API, as regras de negócio, a persistência, os jobs e os scripts. O [pyproject.toml](../pyproject.toml) declara Python `>=3.12`, e a imagem Docker utiliza Python 3.12. A linguagem oferece sintaxe legível e recursos para programação assíncrona, empregados nas operações de banco e HTTP. [Documentação do Python](https://docs.python.org/3/tutorial/).

**Justificativa:** a escolha considera seu uso amplo no mercado, a documentação robusta e o ecossistema de bibliotecas. Esses fatores facilitam a formação da equipe, a manutenção e a evolução das regras de atendimento, sem exigir ferramentas próprias para tarefas comuns de backend.

## SQL e PostgreSQL

**O que são e qual sua função:** SQL é a linguagem de consulta e manipulação de bancos relacionais; PostgreSQL é o sistema gerenciador adotado. Ele armazena usuários, veículos, orçamentos, estoque, ordens e notificações. O Compose utiliza PostgreSQL 16, com volume persistente. Os modelos usam chaves estrangeiras, identificadores únicos e uma coluna JSONB para os itens do orçamento. [Documentação do PostgreSQL 16](https://www.postgresql.org/docs/16/intro-whatis.html).

**Justificativa:** o PostgreSQL foi escolhido por ser open source e amplamente utilizado no mercado. Seu modelo relacional, com uso de SQL, atende plenamente à proposta de organizar usuários, veículos, orçamentos e ordens de serviço. Chaves primárias e estrangeiras, restrições de unicidade e transações ajudam a manter a integridade dos relacionamentos e a consistência dos dados. As limitações de integridade dos campos JSON estão explicadas no [MER](04-modelo-de-dados.md).

## FastAPI

**O que é e qual sua função:** framework web que organiza rotas HTTP, dependências, validação e documentação OpenAPI. Em `main.py`, reúne os routers, configura o ciclo de vida do cliente HTTP e registra os tratamentos globais de erros. Expõe Swagger em `/docs` e ReDoc em `/redoc`. [Documentação do FastAPI](https://fastapi.tiangolo.com/).

**Justificativa:** a documentação extensa e a integração com tipagem, Pydantic e funções assíncronas simplificam a construção e manutenção da API. A documentação interativa facilita entender e experimentar os contratos consumidos por futuras interfaces.
