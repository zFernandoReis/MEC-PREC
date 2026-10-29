# Wiki do MEC System

Documentação do Sistema Integrado de Atendimento e Execução de Serviços de uma oficina mecânica. A descrição da implementação foi conferida no código disponível em 26/10/2026.

## Roteiro de leitura

1. [Introdução](01-introducao.md): contexto, motivação e demandas que orientam o sistema.
2. [Stack utilizada](02-stack.md): função das tecnologias e justificativas das escolhas.
3. [Arquitetura do projeto](03-arquitetura.md): pastas, responsabilidades, conexão entre camadas e diagramas C4 em Mermaid.
   - [Modelo de Entidade-Relacionamento](04-modelo-de-dados.md): complemento da arquitetura com o MER dos modelos SQLAlchemy.
4. [Regras de negócio](05-regras-de-negocio.md): identificação dos registros e regras de criação dos orçamentos.

As funcionalidades planejadas estão identificadas separadamente das que existem no repositório. Os diagramas descrevem a implementação atual, exceto o ator futuro explicitamente indicado no contexto C4.

Para executar a aplicação, consulte o [README operacional](../README.md). Esta wiki é documentação Markdown versionada no repositório; a rota `/docs` da API é a interface Swagger para seus endpoints.

Os blocos `mermaid` precisam de um visualizador com suporte aos diagramas C4 e ER. A sintaxe C4 ainda é classificada como experimental pela [documentação do Mermaid](https://mermaid.js.org/syntax/c4.html).
