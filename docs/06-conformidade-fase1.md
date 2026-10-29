# Conformidade: fluxos principais e requisitos técnicos

Data da análise: 28/10/2026.

Referência: `Fase 1 - Tech Challenge (3).pdf`, páginas 3 e 4, com os detalhamentos funcionais e técnicos das páginas 9 a 11. Escopo: fluxos principais, segurança e qualidade associadas e requisitos técnicos. Não abrange vídeo, PDF de entrega, identificação do grupo ou publicação dos artefatos DDD.

Base examinada: árvore de trabalho local do MEC System, branch `hml`, HEAD `7d241a6e6ed3ffb81a4c231488b3bdabaff0ecee`. Existem alterações locais e arquivos não rastreados; as conclusões incluem esse conteúdo e não representam exclusivamente o commit.

Atualização após a análise: a autorização de OS foi corrigida. Clientes agora consultam somente suas próprias ordens e não podem criar, alterar ou excluir OS. As demais lacunas deste relatório continuam válidas. Os resultados da seção 3 registram a execução original da avaliação.

**Conclusão: conformidade parcial.** A estrutura técnica está implementada em boa parte, mas o fluxo completo de OS ainda não atende ao enunciado. Os principais impedimentos são cálculo automático do orçamento, aprovação/rejeição, regras de transição de status, CRUD de serviços, controle operacional de estoque e tempo médio de execução. A cobertura mínima de 80% não está comprovada.

Critérios de classificação:

- **Atende:** implementação identificada para o requisito; não significa homologação completa em produção.
- **Parcial:** parte do requisito existe, mas há limitações relevantes.
- **Não atende:** implementação necessária não identificada no código examinado.
- **Não comprovado:** faltam medição ou validação operacional suficiente.

## 1. Fluxos principais

### 1.1 Criação da Ordem de Serviço

| Requisito do PDF | Situação | Evidência e avaliação |
| --- | --- | --- |
| Identificar cliente por CPF/CNPJ | Atende por CPF | Existe `GET /users/cpf/{cpf}` e consulta por CPF no repositório. A OS recebe o `client_id` obtido nessa consulta. CNPJ não está implementado; as páginas 9 e 11 dizem CPF **ou** CNPJ, portanto CPF satisfaz essa alternativa. |
| Cadastrar veículo com placa, marca, modelo e ano | Atende | Os DTOs de veículo possuem `license_plate`, `brand`, `model`, `year_manufacture` e `year_model`; há criação e persistência por `/vehicles`. A limitação de formato de placa está tratada na seção técnica. |
| Incluir os serviços solicitados | Parcial | OS e orçamento têm `service_name` e `service_description`, permitindo descrever um serviço. Não há coleção estruturada de serviços nem catálogo ao qual vincular múltiplos serviços solicitados. |
| Incluir peças e insumos necessários | Atende no orçamento associado | `CreateBudgetDTO.tools` recebe itens com identificador e quantidade positiva. A criação verifica se os itens existem; a OS referencia `budget_id`. As peças ficam no orçamento vinculado, sem coleção própria na OS. Isso não comprova controle de consumo de estoque. |
| Gerar orçamento automaticamente com base em serviços e peças | Não atende | `CreateBudgetUseCase` recebe e copia `amount=dto.amount`. Calcula prazo, mas não soma preços das peças e serviços. Criar a OS também não gera orçamento: exige um `budget_id` existente. |
| Enviar/disponibilizar orçamento ao cliente para aprovação | Parcial | Há consulta de orçamento por API autenticada. Não há fluxo de solicitação de aprovação nem envio ao cliente. A consulta não restringe o orçamento ao proprietário. A disponibilização por API pode satisfazer o meio previsto na página 9, mas falta completar a finalidade de aprovação. |
| Registrar aprovação ou rejeição do orçamento | Não atende | Não há estado de decisão, responsável, data ou operação de aprovação/rejeição nos DTOs, entidade e casos de uso de orçamento. Exigência explícita na página 9. |

Evidências: [rotas de usuários](../src/app/modules/users/infrastructure/http/router_users.py), [DTOs de veículo](../src/app/modules/users/application/dtos/vehicle_dto.py), [DTOs de orçamento](../src/app/modules/quotes/application/dtos/budget_dto.py), [criação de orçamento](../src/app/modules/quotes/application/use_cases/create_budget.py), [rotas de orçamento](../src/app/modules/quotes/infrastructure/http/router_budgets.py) e [criação de OS](../src/app/modules/orders/application/use_cases/create_order.py).

### 1.2 Acompanhamento da OS

| Requisito do PDF | Situação | Evidência e avaliação |
| --- | --- | --- |
| Status Recebida, Em diagnóstico, Aguardando aprovação, Em execução, Finalizada e Entregue | Atende | Todos os seis valores estão em `OrderStatus` e são usados nos DTOs e na persistência. |
| Alterar status automaticamente conforme ações no sistema | Não atende | O cliente da API informa `order_status` na criação e na atualização. Não há ações de negócio que produzam automaticamente as transições. |
| Controlar alterações e aplicar regras de transição | Não atende | `UpdateOrderUseCase` atribui os campos recebidos com `setattr`. Não compara estado atual e próximo estado; não exige aprovação para execução. Aceitar somente valores do enum não valida a transição. |
| Permitir consulta pelo cliente via API | Atende | `GET /orders` filtra as ordens pelo cliente autenticado antes da paginação. `GET /orders/{order_id}` retorna 404 para ordens alheias ou inexistentes. Clientes recebem 403 em criação, alteração e exclusão; os papéis internos mantêm acesso operacional. |

Evidências: [enum dos status](../src/app/modules/orders/domain/enums/order_status.py), [atualização da OS](../src/app/modules/orders/application/use_cases/update_order.py), [rotas de OS](../src/app/modules/orders/infrastructure/http/router_orders.py) e [registro das dependências de autenticação](../src/app/main.py).

### 1.3 Gestão administrativa

| Requisito do PDF | Situação | Evidência e avaliação |
| --- | --- | --- |
| CRUD de clientes | Atende | `/users` oferece criação, consulta/listagem, atualização e exclusão. Clientes são usuários com papel `client`; as rotas exigem administrador. |
| CRUD de veículos | Atende | `/vehicles` oferece POST, GET, PATCH e DELETE com casos de uso e persistência. |
| CRUD de serviços | Não atende | Não há entidade de catálogo de serviços nem rotas de CRUD correspondentes. Campos textuais em orçamento e OS não equivalem a um cadastro independente de serviços. |
| CRUD de peças e insumos | Atende como cadastro genérico | `/stock` permite criar, listar, consultar, atualizar e excluir itens com nome, quantidade, preço e lote. Não distingue explicitamente peça de insumo, distinção que o PDF não exige como modelo específico. |
| Controle de estoque | Parcial | Há saldo editável e consulta de disponibilidade na criação do orçamento. Quando falta quantidade, a regra acrescenta prazo de reposição. Não há reserva, baixa ou devolução vinculada à execução da OS; os DTOs de estoque também não proíbem quantidade negativa. |
| Listagem e detalhamento de OS | Atende | Existem `GET /orders` com paginação e `GET /orders/{order_id}`, conectados aos casos de uso e repositório. |
| Monitorar/calcular tempo médio de execução dos serviços | Não atende | Existem duração informada e datas de planejamento. Não foi identificada agregação de tempos reais, cálculo de média nem endpoint correspondente. Notificar atraso ou prazo próximo não atende a esse requisito. |

Evidências: [rotas de usuários](../src/app/modules/users/infrastructure/http/router_users.py), [rotas de veículos](../src/app/modules/users/infrastructure/http/router_vehicles.py), [rotas de estoque](../src/app/modules/quotes/infrastructure/http/router_stock.py), [DTOs de estoque](../src/app/modules/quotes/application/dtos/stock_dto.py), [criação de orçamento](../src/app/modules/quotes/application/use_cases/create_budget.py), [rotas de OS](../src/app/modules/orders/infrastructure/http/router_orders.py) e [entidade OS](../src/app/modules/orders/domain/entities/orders.py).

## 2. Requisitos técnicos, segurança e qualidade

| Requisito do PDF | Situação | Evidência e avaliação |
| --- | --- | --- |
| Back-end monolítico | Atende | Uma aplicação FastAPI reúne `users`, `quotes` e `orders`, compartilhando código e banco. O scheduler usa a mesma imagem; seu processo separado não caracteriza microsserviços. |
| Organização em camadas | Atende | Módulos separados em `domain`, `application` e `infrastructure`, com entidades, casos de uso, portas, HTTP e repositórios. |
| Banco de dados com escolha justificada | Atende | PostgreSQL está configurado; `docs/02-stack.md` justifica a escolha pelas relações do domínio, transações, restrições e uso de JSONB. |
| APIs RESTful | Atende em estrutura | Há recursos HTTP com POST, GET, PATCH e DELETE. Há ajustes de contrato a fazer: por exemplo, o PATCH de OS exige muitos campos em `UpdateOrderDTO`, limitando atualizações parciais. |
| Swagger ou documentação equivalente | Atende | `create_app` habilita `/docs`, `/redoc` e `/openapi.json`. |
| Dockerfile para build | Atende por inspeção | Existe Dockerfile com Python 3.12, instalação a partir do lockfile e execução com usuário não root. Não foi executado um novo build nesta avaliação. |
| Compose para ambiente completo | Atende por inspeção | O arquivo define API, PostgreSQL, scheduler, dependências, healthchecks e volume persistente. A subida completa não foi homologada nesta avaliação. |
| Autenticação JWT para APIs administrativas | Atende à autenticação | JWT protege as rotas de negócio; `/users` também exige administrador. Os testes de segurança verificam login, tokens, expiração/adulteração, rotação e revogação. OS agora restringe consulta por proprietário e escrita a papéis internos. Veículos, estoque e orçamentos ainda exigem apenas autenticação, com autorização a aprimorar. |
| Validação de CPF ou CNPJ | Atende por CPF | A entidade `User` valida formato, repetição e dígitos verificadores de CPF. CNPJ não existe, mas a página 11 admite uma das alternativas. |
| Validação de placa de veículo | Parcial | O DTO aceita o padrão antigo `AAA1234`. A expressão regular rejeita o padrão Mercosul `AAA1A23`. Existe validação, porém a cobertura de formatos é limitada. O PDF não discrimina formatos: esta classificação considera o uso geral da oficina. |
| Testes unitários | Atende | A suíte em `tests/unit` executou com 139 testes aprovados. Inclui também testes de API e de persistência isolada. |
| Testes de integração dos principais fluxos | Parcial | Há testes com TestClient, repositórios e SQLite em `tests/unit`. A pasta `tests/integration` só verifica conexão/sessão PostgreSQL com `SELECT 1`. Não demonstra o fluxo integrado completo de criação de OS, orçamento, aprovação, execução e estoque. Os três testes PostgreSQL falharam por conexão recusada nesta execução. |
| Cobertura mínima de 80% nos domínios críticos | Não comprovado | Não foi encontrado relatório nem configuração de cobertura/limiar em `pyproject.toml`. Passar 139 testes não comprova percentual de cobertura. Não há base para afirmar que o percentual atual seja maior ou menor que 80%. |
| Execução local simples com README explicativo | Parcial | O README explica Compose, ambiente, autenticação e comandos de testes. Porém referencia `app.bootstrap.migrate_user_passwords` e `app.bootstrap.migrate_client_ids`, módulos ausentes na árvore examinada. Esses passos para bancos legados não são reproduzíveis; o caminho com banco novo está documentado, mas não foi validado de ponta a ponta. |
| Transações adequadas nos fluxos principais | Parcial | Há commits nos repositórios, rollback nas dependências HTTP e transação na carga inicial. Não há fluxo transacional completo envolvendo aprovação, estoque e OS, pois essas operações integradas não estão implementadas. Commits por operação isolada não comprovam atomicidade do fluxo inteiro. |

Evidências técnicas: [aplicação](../src/app/main.py), [arquitetura](03-arquitetura.md), [justificativa da stack e banco](02-stack.md), [Dockerfile](../Dockerfile), [Compose](../docker-compose.yml), [entidade de usuário](../src/app/modules/users/domain/entities/user.py), [DTOs de veículo](../src/app/modules/users/application/dtos/vehicle_dto.py), [testes de segurança](../tests/unit/test_security.py), [testes PostgreSQL](../tests/integration/test_database.py), [configuração do projeto](../pyproject.toml), [README operacional](../README.md), [repositório de OS](../src/app/modules/orders/infrastructure/repositories/sqlalchemy_orders_repository.py), [dependências de OS](../src/app/modules/orders/infrastructure/http/dependencies.py) e [carga inicial](../src/app/bootstrap/seed_initial_data.py).

## 3. Validação executada

| Comando | Resultado | Interpretação |
| --- | --- | --- |
| `uv run --no-sync pytest tests/unit -q` | 139 passed; 1 warning; 17,89 s | Os cenários existentes nessa suíte passaram. O aviso é uma depreciação de integração Starlette/httpx. Não equivale à aprovação de requisitos ainda sem testes. |
| `uv run --no-sync pytest tests/integration -q` | 3 failed; 7,84 s | Todos falharam por `ConnectionRefusedError`, WinError 1225. Não foi possível validar o acesso ao PostgreSQL configurado. Essa falha ambiental não comprova defeito nas regras de negócio. |

Não foram executados build/subida do Compose, medição de cobertura ou fluxo real completo com PostgreSQL. A análise distingue existência de código, testes executados e funcionalidades ausentes; não atribui uma nota ou percentual de conformidade, pois o documento não fornece pesos de avaliação.

## 4. Prioridades para atender aos tópicos

1. **Completar orçamento e serviços:** criar CRUD de serviços, permitir itens de serviço no orçamento e calcular o total a partir de preços e quantidades, com regras monetárias definidas.
2. **Completar autorização do orçamento e ciclo da OS:** disponibilizar o orçamento ao cliente correto, registrar aprovação/rejeição e implementar transições válidas e automáticas conforme as ações. Não permitir início da execução sem a aprovação exigida pela regra de negócio.
3. **Integrar estoque e consistência:** definir em que ação ocorre reserva/baixa, impedir saldo inválido, tratar concorrência e garantir transação das operações relacionadas. São meios de completar o controle de estoque; o PDF não impõe uma tecnologia específica para isso.
4. **Restringir acesso por papel e proprietário:** concluído para consulta e escrita de OS. Ainda falta tratar os demais recursos, incluindo a futura decisão do cliente sobre seus orçamentos.
5. **Medir execução real:** registrar início e término efetivos e disponibilizar média por serviço/período, diferenciando estimativa de duração realizada.
6. **Comprovar qualidade:** disponibilizar PostgreSQL de teste, cobrir o fluxo integrado e as falhas com rollback, medir cobertura dos domínios críticos e registrar evidência de pelo menos 80%.
7. **Fechar limitações técnicas:** ampliar placas aceitas, corrigir comandos desatualizados do README e validar build e inicialização em ambiente limpo.

As prioridades 1, 2, 3, 5 e 6 impedem considerar os tópicos integralmente atendidos hoje. As tecnologias e os CRUDs existentes oferecem a base, mas não substituem as regras de negócio exigidas.
