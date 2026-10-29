# 1 — Introdução

[Índice da wiki](README.md) · [Próximo: Stack utilizada](02-stack.md)

## Contexto e motivo da implementação

Uma oficina mecânica de médio porte, especializada na manutenção de veículos, enfrenta dificuldades para expandir seus serviços mantendo qualidade e eficiência. O atendimento, o diagnóstico, a execução dos serviços e a entrega dos veículos dependem de anotações manuais e planilhas dispersas, sem um fluxo integrado de informações.

Essa organização provoca erros na priorização dos atendimentos, falhas no controle de peças e insumos, dificuldade para acompanhar o status dos serviços, perda de histórico de clientes e veículos e ineficiência na elaboração de orçamentos e obtenção de autorizações. À medida que a demanda cresce, a equipe precisa conferir informações em diferentes lugares, aumentando o retrabalho e dificultando a comunicação com o cliente.

Para enfrentar esses problemas, a oficina decidiu investir em um **Sistema Integrado de Atendimento e Execução de Serviços**, o MEC System. O projeto visa atender às demandas mencionadas por meio da centralização dos cadastros, dos orçamentos, do estoque e das ordens de serviço, criando uma base para uma gestão interna eficiente e segura.

A visão do produto inclui permitir que os clientes acompanhem em tempo real o andamento dos serviços e autorizem reparos adicionais por aplicativo. Esses objetivos orientam a evolução do sistema; a implementação atual concentra-se no backend e ainda não entrega toda essa experiência ao cliente.

## Relação entre os problemas e o projeto

| Demanda da oficina | Contribuição da implementação atual | Evolução necessária para o objetivo completo |
| --- | --- | --- |
| Priorizar os atendimentos | Ordens registram status e datas; jobs identificam prazos próximos e atrasos. | Definir critérios e uma fila de priorização; não há algoritmo de prioridade implementado. |
| Controlar peças e insumos | Estoque registra quantidade, preço, lote e prazo de reposição. A criação de orçamento consulta os itens e acrescenta prazo quando a quantidade é insuficiente. | Completar o fluxo de movimentação, reserva e baixa de estoque associado à execução. |
| Acompanhar o serviço | A API permite consultar e atualizar ordens com status de recebimento, diagnóstico, espera de aprovação, execução, finalização e entrega. | Desenvolver a interface do cliente e a atualização em tempo real. |
| Preservar dados de clientes e veículos | Usuários, veículos, orçamentos e ordens possuem registros persistentes e relacionamentos no banco. | Complementar a consulta de histórico e, se necessário, auditoria das alterações; os registros atuais não constituem um histórico completo de eventos. |
| Organizar orçamentos e autorizações | Orçamentos vinculam cliente, técnico e veículo; ordens se vinculam a orçamentos e incluem o status `aguardando_aprovacao`. | Implementar o ato de aprovação/rejeição pelo cliente e o registro de consentimento para reparos adicionais. |
| Garantir gestão segura | Autenticação JWT, hash de senha Argon2 e restrição administrativa nas rotas de usuários. | Aplicar regras de acesso por proprietário para a experiência individual do cliente. |

## Escopo encontrado na varredura

O backend oferece operações de cadastro, consulta, atualização e exclusão para usuários, veículos, estoque, orçamentos e ordens. Integra-se ao ViaCEP para resolução de endereços e possui processos de criação de tabelas, importação de dados e geração periódica de notificações de prazo.

As notificações são registros no banco: os jobs não enviam e-mail, push ou mensagens ao aplicativo. Não há frontend, aplicativo móvel, WebSocket ou SSE no código examinado. A presença de um status de aprovação também não representa, por si só, um fluxo de autorização do cliente.

As rotas de usuários exigem administrador; veículos, estoque, orçamentos e ordens exigem autenticação, sem restrição por proprietário nesses recursos. Essa distinção é relevante para a futura disponibilização de um aplicativo aos clientes.

As principais evidências estão na [composição da API](../src/app/main.py), nos [módulos de negócio](../src/app/modules), no [cálculo de orçamento](../src/app/modules/quotes/application/use_cases/create_budget.py) e nos [jobs de notificação](../src/app/modules/orders/infrastructure/jobs).
