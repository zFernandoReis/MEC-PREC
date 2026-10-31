# 4 — Regras de negócio

[Índice da wiki](README.md) · [Arquitetura](03-arquitetura.md)

## Disponibilidade do técnico

| Situação informada no orçamento | Efeito no prazo |
| --- | --- |
| Técnico disponível | Mantém a duração base. |
| Técnico indisponível | Acrescenta **24 horas e 1 dia**, sem consultar a agenda. |

## Cálculo do prazo final

**Prazo final = duração base + acréscimo do técnico + reposição das peças com estoque insuficiente.**

| Exemplo | Duração base | Acréscimos | Prazo final |
| --- | --- | --- | --- |
| Técnico disponível e estoque suficiente | 48 horas / 2 dias | Nenhum | **48 horas / 2 dias** |
| Técnico indisponível e estoque suficiente | 48 horas / 2 dias | Técnico: 24 horas / 1 dia | **72 horas / 3 dias** |
| Orçamento exige **4 velas**, mas há **2 em estoque**; técnico disponível | 24 horas / 1 dia | Reposição das 2 velas faltantes: 48 horas / 2 dias | **72 horas / 3 dias** |
| Orçamento exige **1 bomba d'água**, mas o estoque está **zerado**; técnico disponível | 24 horas / 1 dia | Reposição: 48 horas / 2 dias | **72 horas / 3 dias** |
| Técnico indisponível e duas peças distintas com estoque insuficiente | 48 horas / 2 dias | Técnico: 24 horas / 1 dia; peça A: 24 horas / 1 dia; peça C: 48 horas / 2 dias | **144 horas / 6 dias** |

## Regras do cálculo

- Quantidades repetidas da mesma peça são somadas antes da comparação com o estoque.
- Cada peça distinta com saldo insuficiente acrescenta seu prazo de reposição **uma única vez**, independentemente da quantidade faltante. Os prazos das peças distintas são somados.
- Estoque insuficiente ou zerado permite criar o orçamento com prazo adicional. **Peça não cadastrada interrompe a criação.**
- Criar o orçamento não compra, reserva ou retira peças do estoque.
- Horas e dias são calculados separadamente, sem conversão automática nem calendário de dias úteis.
