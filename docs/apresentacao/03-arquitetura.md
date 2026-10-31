# 3 — Arquitetura do projeto

[Índice da wiki](README.md) · [Anterior: Stack](02-stack.md) · [Complemento: MER](04-modelo-de-dados.md)

## Organização arquitetural

O MEC System é um **monólito modular**, organizado por responsabilidades de negócio e por camadas. Os módulos `users`, `quotes` e `orders` compartilham uma aplicação FastAPI, uma base de código e um banco. O scheduler executa separadamente, usando a mesma imagem e os mesmos modelos.

## Estrutura do backend

```text
src/app/
├── main.py
├── config.py
├── bootstrap/
├── modules/
│   ├── users/
│   │   ├── domain/{entities,enums,value_objects}/
│   │   ├── application/{dtos,ports,services,use_cases}/
│   │   └── infrastructure/{clients,http,models,repositories}/
│   ├── quotes/
│   │   ├── domain/entities/
│   │   ├── application/{dtos,ports,use_cases}/
│   │   ├── infrastructure/{http,models,repositories}/
│   │   └── exceptions.py
│   └── orders/
│       ├── domain/{entities,enums}/
│       ├── application/{dtos,ports,use_cases}/
│       └── infrastructure/{http,jobs,models,repositories}/
└── shared/infrastructure/
    ├── database/
    ├── logging/
    └── security/
```

### Camadas e responsabilidades

| Pasta | Função no projeto |
| --- | --- |
| `domain/` | Reúne as estruturas e regras que representam os conceitos centrais da aplicação, separadas dos detalhes de transporte HTTP e 
| `application/` | Organiza as operações oferecidas pelo sistema e coordena a colaboração entre regras, contratos e serviços. |
| `infrastructure/` | Reúne as implementações técnicas que conectam a aplicação ao banco de dados, à interface HTTP e aos serviços externos. |
| `bootstrap/` | conecta implementações e casos de uso em arquivos como `users.py`, `budgets.py` e `orders.py`. Também contém comandos de criação de tabelas, migração de tipos de notificação, importação JSON, carga inicial, inicialização do servidor e execução dos jobs. É o ponto de montagem e operação da aplicação. |
| `shared/` | Construi todas as aplicações que são compartilhadas no servidor entre os modulos, como logger, sessão de banco de dados e autenticação JWT. |
