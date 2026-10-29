# 4 — Regras de negócio

[Índice da wiki](README.md) · [Arquitetura](03-arquitetura.md) · [Modelo de dados](04-modelo-de-dados.md)

## 4.1 — Identificadores inteiros para uso na operação

Os identificadores de usuários, veículos, orçamentos e ordens de serviço são números inteiros únicos dentro de suas respectivas tabelas. Essa escolha atende à rotina de pessoas não técnicas: atendentes, técnicos e responsáveis pela oficina precisam localizar, informar e conferir registros durante o atendimento.

Referências como **orçamento 125** ou **ordem de serviço 348** são simples de ler, digitar e comunicar verbalmente. Isso facilita buscar um atendimento, anotar uma referência e conversar com o cliente ou com outro profissional, reduzindo a dificuldade de manipular identificadores longos. A decisão considera, portanto, a facilidade de uso na operação, além da identificação técnica dos dados.

| Registro | Identificador inteiro | Exemplo de referência |
| --- | --- | --- |
| Usuário | `users.id` | Usuário 42 |
| Veículo | `vehicles.vehicle_id` | Veículo 87 |
| Orçamento | `budgets.budget_id` | Orçamento 125 |
| Ordem de serviço | `orders.order_id` | Ordem 348 |

O banco gera esses identificadores com `Identity`, e a chave primária garante que não se repitam na mesma tabela. O usuário informa o ID de um registro existente ao vinculá-lo a outro, mas não escolhe o ID do novo orçamento: ele é atribuído durante a persistência.

A unicidade é por tipo de registro: pode existir um usuário 42 e um orçamento 42, pois são tabelas diferentes. A numeração também pode ter intervalos após exclusões ou transações desfeitas; não representa a quantidade de registros nem uma sequência obrigatoriamente contínua.

Os modelos mantêm ainda um `system_id` UUID único, como identificador adicional do sistema. A escolha de números simples para a operação não elimina esse identificador. Nem todas as chaves do projeto são inteiras: estoque usa `tool_id` textual e notificações usam `notification_id` UUID, conforme o [MER](04-modelo-de-dados.md).

## 4.2 — Criação de orçamentos (`budgets`)

O orçamento registra o serviço proposto, seu valor, o cliente, o veículo, o técnico e os itens necessários. A principal regra de criação ajusta a duração estimada considerando **disponibilidade do técnico** e **necessidade de reposição de estoque**. O objetivo é incorporar esses fatores ao prazo informado para o serviço.

O fluxo é executado por `CreateBudgetUseCase`, chamado pela rota autenticada `POST /budgets`.

### Dados de entrada

O cadastro recebe `client_id`, `vehicle_id`, `technical_id`, nome e disponibilidade do técnico, nome do serviço, valor (`amount`) e duração base em horas e dias. A descrição do serviço e a lista `tools` são opcionais.

Quando a lista é enviada, cada item deve conter `tool_id`, `tool_name` e uma quantidade inteira maior que zero. Os campos de identificação e nome do item aceitam de 1 a 100 caracteres. O DTO exige `vehicle_id` positivo e rejeita campos extras não previstos.

Os vínculos com cliente, técnico e veículo são obrigatórios no modelo, e as chaves estrangeiras verificam a existência dos registros ao persistir. Essa verificação não equivale a conferir o papel do usuário ou se o veículo pertence ao cliente: o caso de uso de criação não executa essas verificações adicionais.

### Consulta e consolidação dos itens

Antes de salvar, o sistema soma as quantidades dos itens que tenham o mesmo `tool_id`. Se um item aparecer duas vezes, com quantidades 2 e 3, a necessidade total considerada será 5.

Essa consolidação é usada na verificação de disponibilidade. A lista gravada no orçamento preserva as entradas recebidas, serializadas em JSONB; não é substituída pela lista consolidada.

| Situação | Regra aplicada |
| --- | --- |
| `tools` ausente, nulo ou lista vazia | Não consulta estoque nem acrescenta prazo de reposição. |
| Um `tool_id` não existe no estoque | Interrompe com `StockNotFoundError`, sem salvar o orçamento. |
| Quantidade disponível maior ou igual à quantidade total solicitada | Não acrescenta prazo para esse item. |
| Quantidade disponível menor que a quantidade total solicitada | Permite criar o orçamento, acrescentando o prazo de reposição cadastrado para esse item. |

Cada item distinto com quantidade insuficiente contribui **uma única vez** com `replacement_time_hours` e `replacement_time_days`. O prazo não é multiplicado pela quantidade faltante nem pelo número de aparições do item. Se vários itens distintos estiverem em falta, seus prazos são somados; o cálculo não utiliza apenas o maior prazo.

Essa é uma regra de estimativa: a consulta não reserva nem baixa itens do estoque e não garante disponibilidade futura.

### Disponibilidade do técnico

A disponibilidade é recebida no campo `technical_disponibility`. Quando seu valor é verdadeiro, a duração base é mantida nessa etapa. Quando é falso, o sistema acrescenta **24 horas e 1 dia**.

O acréscimo é fixo. A criação do orçamento não consulta uma agenda do técnico nem calcula o primeiro horário livre; utiliza a disponibilidade informada no cadastro.

### Cálculo do prazo final

```text
horas finais = horas base
             + (24, se o técnico estiver indisponível; 0, caso contrário)
             + soma dos prazos em horas dos itens distintos com estoque insuficiente

dias finais = dias base
            + (1, se o técnico estiver indisponível; 0, caso contrário)
            + soma dos prazos em dias dos itens distintos com estoque insuficiente
```

As duas unidades são calculadas separadamente a partir dos valores recebidos. O caso de uso não converte automaticamente horas em dias, não verifica equivalência entre esses campos e não considera calendário de dias úteis.

Por exemplo, considere um serviço com duração base de 48 horas e 2 dias, técnico indisponível e os seguintes itens:

| Item | Quantidade necessária | Quantidade disponível | Reposição cadastrada | Acréscimo |
| --- | --- | --- | --- | --- |
| A | 5, somando duas entradas de 2 e 3 | 4 | 24 horas / 1 dia | 24 horas / 1 dia, uma vez |
| B | 1 | 1 | 48 horas / 2 dias | Nenhum |
| C | 2 | 0 | 48 horas / 2 dias | 48 horas / 2 dias, uma vez |

O prazo final será **144 horas** (`48 + 24 + 24 + 48`) e **6 dias** (`2 + 1 + 1 + 2`). O item B não altera o prazo porque a quantidade disponível atende ao solicitado.

### Valor e persistência

O valor `amount` é informado na entrada e preservado. A criação não calcula automaticamente o preço a partir do estoque, da mão de obra ou do prazo, nem acrescenta cobrança pela indisponibilidade do técnico ou reposição.

Depois de verificar os itens e calcular as durações, o caso de uso cria a entidade `Budget` e solicita sua gravação. O repositório SQLAlchemy persiste o modelo, obtém o `budget_id` inteiro gerado pelo banco e preenche as datas de criação e atualização. Em sucesso, a rota retorna HTTP 201 com o orçamento criado.

Criar um orçamento não abre automaticamente uma ordem de serviço e não registra aprovação do cliente. Esses eventos não fazem parte desse caso de uso.

### Limites das validações atuais

O DTO valida tipos, a quantidade positiva dos itens e as restrições explicitadas acima. Entretanto, não define limites positivos para `amount`, `duration_service_hours` ou `duration_service_days`, e a entidade `Budget` não acrescenta essa validação. Portanto, não se deve documentar a rejeição desses valores negativos como uma regra já implementada.

As regras desta seção descrevem especificamente a **criação**. Não pressupõem que a atualização do orçamento repita as mesmas consultas ou recalcule os acréscimos.

## Referências no código

- [Caso de uso de criação](../src/app/modules/quotes/application/use_cases/create_budget.py): estoque, disponibilidade e cálculo de duração.
- [DTOs de orçamento](../src/app/modules/quotes/application/dtos/budget_dto.py) e [entidade Budget](../src/app/modules/quotes/domain/entities/budget.py): contrato de entrada e dados de domínio.
- [Modelo BudgetModel](../src/app/modules/quotes/infrastructure/models/budgets_model.py) e [repositório](../src/app/modules/quotes/infrastructure/repositories/sqlalchemy_budget_repository.py): identificadores, relacionamentos e persistência.
- [Rotas de orçamento](../src/app/modules/quotes/infrastructure/http/router_budgets.py): entrada HTTP e resposta de criação.
- [Testes das regras de estoque](../tests/unit/test_budget_stock_validation.py): itens repetidos, quantidade insuficiente, item inexistente, ausência de itens e soma de prazos.
