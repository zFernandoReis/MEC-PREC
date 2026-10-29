# Requisições HTTP

Arquivos para a extensão **REST Client do VS Code**, separados por domínio:

| Arquivo | Rotas |
| --- | --- |
| [auth.http](auth.http) | Login, usuário autenticado, refresh, alteração de senha e logout |
| [users.http](users.http) | Criar, listar, consultar por ID/CPF, atualizar e excluir usuários |
| [vehicles.http](vehicles.http) | Criar, listar, consultar, atualizar e excluir veículos |
| [stock.http](stock.http) | Criar, listar, consultar, atualizar e excluir estoque |
| [budgets.http](budgets.http) | Criar, listar, consultar, atualizar e excluir orçamentos |
| [orders.http](orders.http) | Criar, listar, consultar, atualizar e excluir ordens |

## Como executar

1. Inicie a API e ajuste `@baseUrl` em cada arquivo se a porta não for 8000.
2. Disponibilize `MEC_HTTP_CPF` (11 dígitos) e `MEC_HTTP_PASSWORD` no ambiente do editor antes de abri-lo. Para testar alteração de senha, defina também `MEC_HTTP_NEW_PASSWORD` (12 a 128 caracteres). Essas são variáveis do cliente HTTP; o `.env` da API não as fornece automaticamente ao editor. Use uma conta já cadastrada; usuários exigem papel `admin`.
3. Execute **Send Request** no bloco **Login** do arquivo. A variável `@token` referencia `access_token` da resposta nomeada `login`.
4. Ajuste as variáveis de IDs relacionados e os dados de exemplo; execute individualmente as requisições desejadas.

Existe apenas uma sessão ativa por usuário: o login em outro arquivo invalida o token anterior. Ao voltar a um arquivo, execute seu login novamente. Refresh, logout e alteração de senha também invalidam tokens anteriores. Em `auth.http`, o refresh disponibiliza `@renewedToken` e `@renewedRefreshToken`; o refresh original não pode ser reutilizado.

## Dados e dependências

Os exemplos de usuários, veículos, estoque e ordens capturam o ID da respectiva criação. Execute o POST antes das consultas por ID, PATCH ou DELETE, ou substitua a variável por um ID existente. Os exemplos podem gerar conflitos se forem repetidos com o mesmo CPF ou placa. O cadastro de usuário consulta o ViaCEP.

Para um fluxo completo, crie usuários (cliente e técnico), estoque, veículo, orçamento e ordem, nessa sequência. Copie os IDs entre os arquivos; confira também nomes e e-mails. O técnico pode ser cadastrado usando `role: "technical"`. O proprietário do veículo deve corresponder ao cliente usado no orçamento e na ordem.

O POST de orçamento retorna `system_id`, mas não `budget_id`. Execute a listagem, localize o registro pelo `system_id` retornado e copie seu `budget_id` para a variável antes de consultar, atualizar, excluir ou criar uma ordem.

Os PATCH de orçamento e ordem exigem os campos completos mostrados nos exemplos, conforme os DTOs atuais. O POST de ordem calcula as datas e a duração em dias no servidor.

As exclusões estão no final de cada arquivo e removem dados reais do ambiente apontado por `@baseUrl`. Execute-as individualmente quando desejar limpar os registros; relações existentes podem impedir a exclusão. Alteração de senha e logout são cenários independentes: siga os comentários de `auth.http`.

Notificações são criadas pelos jobs e não possuem rotas HTTP registradas na aplicação.
