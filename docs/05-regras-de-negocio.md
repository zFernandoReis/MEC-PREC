# 4 — Regras de negócio

[Índice da wiki](README.md) · [Arquitetura](03-arquitetura.md)

## Disponibilidade do técnico

**Exemplo:** serviço com duração base de **48 horas e 2 dias**, com todos os itens disponíveis em estoque.

| Disponibilidade informada | Acréscimo | Prazo final |
| --- | --- | --- |
| Técnico disponível (`technical_disponibility = true`) | Nenhum | **48 horas e 2 dias** |
| Técnico indisponível (`technical_disponibility = false`) | 24 horas e 1 dia | **72 horas e 3 dias** |

O acréscimo é fixo e usa a disponibilidade informada no orçamento, sem consultar a agenda do técnico.

## Cálculo do prazo final

**Prazo final = duração base + acréscimo do técnico + prazos de reposição dos itens com estoque insuficiente.**

### Exemplo 1 — Técnico disponível e estoque suficiente

| Componente | Horas | Dias |
| --- | --- | --- |
| Duração base | 48 | 2 |
| Acréscimo do técnico | 0 | 0 |
| Reposição de itens | 0 | 0 |
| **Prazo final** | **48** | **2** |

### Exemplo 2 — Quantidade em estoque menor que a exigida no orçamento

Um orçamento para troca de velas exige **4 velas de ignição do mesmo modelo**, mas o estoque possui apenas **2 unidades**. O técnico está disponível. Neste exemplo, a duração base informada é de **24 horas e 1 dia**, e o prazo de reposição cadastrado para a peça é de **48 horas e 2 dias**.

| Peça | Quantidade exigida no orçamento | Quantidade em estoque | Quantidade faltante |
| --- | --- | --- | --- |
| Vela de ignição | 4 | 2 | **2** |

Como **2 em estoque < 4 exigidas**, o sistema identifica estoque insuficiente e acrescenta o prazo de reposição dessa peça ao serviço.

| Componente | Horas | Dias |
| --- | --- | --- |
| Duração base | 24 | 1 |
| Acréscimo do técnico | 0 | 0 |
| Reposição das velas | 48 | 2 |
| **Prazo final** | **72** | **3** |

**Resultado:** o orçamento é criado com prazo de **72 horas** (`24 + 48`) e **3 dias** (`1 + 2`).

O prazo de reposição entra **uma única vez para esse modelo de peça**: as 2 velas faltantes não multiplicam as 48 horas por 2. A criação do orçamento não reserva nem retira as 2 unidades existentes do estoque.

### Exemplo 3 — Peça sem unidades em estoque

Uma troca de bomba d'água precisa de **1 peça**, mas a quantidade em estoque é **zero**. A peça está cadastrada com prazo de reposição de **48 horas e 2 dias**. O técnico está disponível e a duração base do serviço é de **24 horas e 1 dia**.

| Componente | Horas | Dias |
| --- | --- | --- |
| Duração base do serviço | 24 | 1 |
| Acréscimo do técnico disponível | 0 | 0 |
| Reposição da bomba d'água | 48 | 2 |
| **Prazo final** | **72** | **3** |

O orçamento pode ser criado mesmo sem a peça disponível. O sistema acrescenta o prazo de reposição ao prazo do serviço. Esse cálculo não realiza a compra nem reserva a peça.

**Peça sem estoque é diferente de peça não cadastrada:** se o identificador da peça não existir no cadastro de estoque, a criação do orçamento é interrompida.

### Exemplo 4 — Técnico indisponível e vários itens em falta

Duração base: **48 horas e 2 dias**. Técnico indisponível: **mais 24 horas e 1 dia**.

| Item | Quantidade necessária | Quantidade em estoque | Prazo de reposição cadastrado | Acréscimo ao prazo |
| --- | --- | --- | --- | --- |
| A | 5, somando duas entradas de 2 e 3 | 4 | 24 horas e 1 dia | 24 horas e 1 dia, uma vez |
| B | 1 | 1 | 48 horas e 2 dias | Nenhum |
| C | 2 | 0 | 48 horas e 2 dias | 48 horas e 2 dias, uma vez |

| Cálculo | Resultado |
| --- | --- |
| Horas: 48 da base + 24 do técnico + 24 do item A + 48 do item C | **144 horas** |
| Dias: 2 da base + 1 do técnico + 1 do item A + 2 do item C | **6 dias** |

O item B não acrescenta prazo. As entradas repetidas do item A têm suas quantidades somadas antes da comparação com o estoque. Os prazos de reposição de A e C são somados, sem multiplicação pela quantidade faltante.

Horas e dias são calculados separadamente com os valores informados. Não há conversão automática entre essas unidades nem cálculo de dias úteis.
